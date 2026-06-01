"""
证据上下文注入器
在每次AI输出前注入证据上下文，确保回答与证据紧密结合
"""
import json
import re
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.evidence import EvidenceItem, EvidenceRelationship
from app.models.case import Case
from app.db.database import SessionLocal


class EvidenceContextInjector:
    """
    证据上下文注入器
    拦截所有AI调用，注入证据信息，确保回答包含证据引用和缺口提示
    """

    # 需要注入证据的关键词
    EVIDENCE_RELEVANT_KEYWORDS = [
        '事实', '证明', '证据', '依据', '材料',
        '主张', '违约', '责任', '金额', '时间',
        '约定', '承诺', '交付', '支付', '签订'
    ]

    # 证据类型中文名映射
    EVIDENCE_TYPE_NAMES = {
        'CONTRACT': '合同协议',
        'CORRESPONDENCE': '函件沟通',
        'PAYMENT': '支付凭证',
        'IDENTITY': '身份证明',
        'AUDIO_VIDEO': '视听资料',
        'TESTIMONY': '证人证言',
        'EXPERT': '鉴定意见',
        'DOCUMENT': '书证',
        'MATERIAL': '物证',
        'OTHER': '其他'
    }

    def __init__(self, evidence_service=None):
        self.evidence_service = evidence_service
        self.db = SessionLocal()

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    def inject_context(
        self,
        prompt: str,
        case_id: int,
        context_type: str = 'general'
    ) -> str:
        """
        注入证据上下文

        Args:
            prompt: 原始提示词
            case_id: 案件ID
            context_type: 上下文类型 (general/analysis/strategy/question)

        Returns:
            增强后的提示词
        """
        db = self._get_db()
        try:
            # 1. 提取查询意图
            entities = self._extract_query_entities(prompt)

            # 2. 检索相关证据
            relevant_evidence = self._retrieve_relevant_evidence(
                db, case_id, entities, context_type
            )

            # 3. 分析证据覆盖
            coverage = self._analyze_coverage(
                entities, relevant_evidence
            )

            # 4. 生成缺口提示
            gap_suggestions = self._generate_gap_suggestions(
                coverage, context_type
            )

            # 5. 构建增强提示词
            enhanced_prompt = self._build_enhanced_prompt(
                prompt,
                relevant_evidence,
                gap_suggestions,
                context_type
            )

            return enhanced_prompt

        finally:
            db.close()

    def _extract_query_entities(self, prompt: str) -> dict:
        """提取查询中的关键实体"""
        entities = {
            'keywords': [],
            'dates': [],
            'amounts': [],
            'parties': [],
            'query_text': prompt
        }

        # 提取关键词
        words = re.findall(r'[\u4e00-\u9fa5]{2,5}', prompt)
        for w in words:
            if len(w) >= 2:
                entities['keywords'].append(w)

        # 提取日期
        date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        dates = re.findall(date_pattern, prompt)
        entities['dates'] = [f"{d[0]}年{d[1]}月{d[2]}日" for d in dates]

        # 提取金额
        money_pattern = r'[\d,]+[万千佰亿万]?[元]?'
        amounts = re.findall(money_pattern, prompt)
        entities['amounts'] = amounts[:5]

        # 提取当事人
        party_patterns = [
            r'([\u4e00-\u9fa5]{2,6})说',
            r'([\u4e00-\u9fa5]{2,6})称',
            r'甲方[：:]?([\u4e00-\u9fa5]{2,4})',
            r'乙方[：:]?([\u4e00-\u9fa5]{2,4})',
            r'([\u4e00-\u9fa5]{2,6})(?:公司|厂|店|企业)'
        ]

        for pattern in party_patterns:
            matches = re.findall(pattern, prompt)
            entities['parties'].extend(matches[:2])

        return entities

    def _retrieve_relevant_evidence(
        self,
        db: Session,
        case_id: int,
        entities: dict,
        context_type: str
    ) -> dict:
        """
        多维度证据检索
        """
        results = {
            'exact_match': [],
            'keyword_match': [],
            'semantic_match': [],
            'date_match': [],
            'amount_match': []
        }

        # 1. 获取所有证据
        all_evidence = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id,
            EvidenceItem.is_current == True
        ).all()

        if not all_evidence:
            return results

        # 2. 关键词匹配
        for ev in all_evidence:
            content = ((ev.extracted_content or '') + (ev.raw_content or '') +
                      ' '.join(ev.keywords or []) + ' '.join([e.get('value', '') for e in (ev.entity_tags or [])]))

            # 检查关键词匹配
            match_score = 0
            for kw in entities.get('keywords', []):
                if kw in content:
                    match_score += 1

            if match_score > 0:
                ev_info = self._evidence_to_dict(ev)
                ev_info['match_score'] = match_score
                ev_info['match_reasons'] = [kw for kw in entities.get('keywords', []) if kw in content]
                results['keyword_match'].append(ev_info)

        # 3. 日期匹配
        for date in entities.get('dates', []):
            for ev in all_evidence:
                content = (ev.extracted_content or '') + (ev.raw_content or '')
                if date in content:
                    ev_info = self._evidence_to_dict(ev)
                    ev_info['match_reason'] = f'包含日期: {date}'
                    results['date_match'].append(ev_info)

        # 4. 金额匹配
        for amount in entities.get('amounts', []):
            for ev in all_evidence:
                content = (ev.extracted_content or '') + (ev.raw_content or '')
                if amount in content:
                    ev_info = self._evidence_to_dict(ev)
                    ev_info['match_reason'] = f'包含金额: {amount}'
                    results['amount_match'].append(ev_info)

        # 5. 按匹配度排序
        for key in results:
            if key != 'exact_match':
                results[key].sort(key=lambda x: x.get('match_score', 0), reverse=True)

        # 6. 去重合并
        seen_ids = set()
        merged = []
        for key in ['exact_match', 'keyword_match', 'date_match', 'amount_match', 'semantic_match']:
            for ev in results[key]:
                if ev['id'] not in seen_ids:
                    seen_ids.add(ev['id'])
                    merged.append(ev)

        results['all_relevant'] = merged  # 返回全部相关证据，无数量限制

        return results

    def _evidence_to_dict(self, ev: EvidenceItem) -> dict:
        """
        将证据转换为字典 - 法律应用专用：证据完整性优先

        重要原则：使用完整内容而非摘要截断版本。
        """
        type_info = EvidenceItem.get_type_display(ev.evidence_type)
        # 优先使用完整提取内容，而非截断的摘要
        full_content = ev.extracted_content or ev.raw_content or ev.summary or ''
        return {
            'id': ev.id,
            'type': ev.evidence_type,
            'type_name': type_info.get('name', ''),
            'icon': type_info.get('icon', '📎'),
            'summary': full_content,  # 法律应用：使用完整内容
            'credibility': ev.credibility_score,
            'source_party': ev.source_party,
            'proves_facts': [f.get('fact', '') for f in (ev.proves_facts or [])],
            'keywords': ev.keywords or []
        }

    def _analyze_coverage(
        self,
        entities: dict,
        evidence: dict
    ) -> dict:
        """
        分析证据覆盖情况
        """
        coverage = {
            'covered': [],
            'partial': [],
            'uncovered': [],
            'gap_points': [],
            'coverage_score': 0
        }

        relevant = evidence.get('all_relevant', [])

        # 检查关键词覆盖
        key_concepts = [
            '合同', '协议', '违约', '付款', '交付',
            '金额', '日期', '期限', '责任', '义务'
        ]

        covered_concepts = []
        for concept in key_concepts:
            for ev in relevant:
                content = (ev.get('summary', '') + ' ' + ' '.join(ev.get('keywords', []))).lower()
                if concept in content:
                    covered_concepts.append(concept)
                    break

        coverage['covered'] = covered_concepts
        coverage['uncovered'] = [c for c in key_concepts if c not in covered_concepts]

        # 计算覆盖率
        if key_concepts:
            coverage['coverage_score'] = len(covered_concepts) / len(key_concepts) * 100

        # 生成缺口点
        for concept in coverage['uncovered']:
            gap_map = {
                '合同': {'name': '合同文件', 'icon': '📄', 'suggestion': '建议补充合同或协议文件'},
                '协议': {'name': '协议文件', 'icon': '📄', 'suggestion': '建议补充书面协议'},
                '违约': {'name': '违约证据', 'icon': '⚠️', 'suggestion': '建议补充违约事实的证据'},
                '付款': {'name': '付款凭证', 'icon': '💰', 'suggestion': '建议补充付款记录或收据'},
                '交付': {'name': '交付证明', 'icon': '📦', 'suggestion': '建议补充交付凭证'},
                '金额': {'name': '金额证明', 'icon': '💵', 'suggestion': '建议提供具体金额的书面证据'},
                '日期': {'name': '时间证明', 'icon': '📅', 'suggestion': '建议提供关键时间节点的证据'},
                '期限': {'name': '期限约定', 'icon': '⏰', 'suggestion': '建议补充履行期限的约定'},
                '责任': {'name': '责任依据', 'icon': '⚖️', 'suggestion': '建议补充责任约定的证据'},
                '义务': {'name': '义务约定', 'icon': '📋', 'suggestion': '建议补充义务约定的证据'}
            }
            gap_info = gap_map.get(concept, {'name': concept, 'icon': '❓', 'suggestion': f'建议补充{concept}相关证据'})
            coverage['gap_points'].append({
                'concept': concept,
                'name': gap_info['name'],
                'icon': gap_info['icon'],
                'suggestion': gap_info['suggestion'],
                'priority': 'high' if concept in ['合同', '违约', '付款'] else 'medium'
            })

        return coverage

    def _generate_gap_suggestions(
        self,
        coverage: dict,
        context_type: str
    ) -> str:
        """
        生成简洁的缺口提示
        """
        suggestions = []

        # 无证据情况
        if coverage.get('coverage_score', 0) == 0 and not coverage.get('gap_points'):
            return ""

        # 未覆盖要点
        high_priority_gaps = [g for g in coverage.get('gap_points', []) if g.get('priority') == 'high']

        if high_priority_gaps:
            suggestions.append("**📋 建议补充证据**：\n")
            for gap in high_priority_gaps[:3]:
                suggestions.append(f"- {gap['icon']} {gap['name']}：{gap['suggestion']}")

        return "\n".join(suggestions)

    def _build_enhanced_prompt(
        self,
        prompt: str,
        evidence: dict,
        suggestions: str,
        context_type: str
    ) -> str:
        """
        构建增强后的提示词
        """
        enhanced = prompt

        # 添加证据上下文
        relevant = evidence.get('all_relevant', [])
        if relevant:
            evidence_context = self._format_evidence_context(relevant)
            enhanced += f"\n\n## 📎 相关证据\n{evidence_context}"

        # 添加缺口提示
        if suggestions:
            enhanced += f"\n\n## 💡 证据补充建议\n{suggestions}\n\n请在回答时引用相关证据编号（如[合同]、[发票]等），对于证据不足的部分请明确说明「待证据证实」。"

        # 添加回答要求
        enhanced += "\n\n## 📝 回答要求\n"
        enhanced += "1. 引用证据时请使用证据类型标注，如：[合同]、[发票]、[函件]\n"
        enhanced += "2. 对于没有证据支撑的主张，明确说明「待证据证实」或「建议补充XXX证据」\n"
        enhanced += "3. 主动提示可能需要的证据类型\n"

        return enhanced

    def _format_evidence_context(self, evidence: list) -> str:
        """
        格式化证据上下文 - 法律应用专用：证据完整性优先

        重要原则：
        - 保留全部相关证据，不限制数量
        - 使用完整内容，不截断任何字符
        - 证据中的每一个字符都可能包含关键法律信息
        """
        if not evidence:
            return "暂无相关证据"

        lines = []
        for i, ev in enumerate(evidence, 1):
            icon = ev.get('icon', '📎')
            ev_type = ev.get('type_name', '证据')
            # 法律应用：使用完整内容，不截断
            full_content = ev.get('summary', '')
            credibility = ev.get('credibility', 0)
            proves = ev.get('proves_facts', [])

            lines.append(f"{i}. {icon} **[{ev_type}]** 证据{i} (证明力参考: {credibility:.0f}%)")
            lines.append(f"   {full_content}")
            if proves:
                lines.append(f"   证明：{', '.join(proves)}")
            lines.append("")

        return "\n".join(lines)

    # ==================== 便捷方法 ====================

    def inject_for_analysis(
        self,
        prompt: str,
        case_id: int,
        analysis_type: str = 'general'
    ) -> str:
        """为分析注入证据上下文"""
        return self.inject_context(prompt, case_id, f'analysis_{analysis_type}')

    def inject_for_question(
        self,
        question: str,
        case_id: int
    ) -> str:
        """为问答注入证据上下文"""
        return self.inject_context(question, case_id, 'question')

    def inject_for_strategy(
        self,
        prompt: str,
        case_id: int
    ) -> str:
        """为策略建议注入证据上下文"""
        return self.inject_context(prompt, case_id, 'strategy')


class StreamingEvidenceInjector:
    """
    流式输出的证据注入
    在每个段落输出前注入相关证据
    """

    # 需要注入证据的段落类型
    EVIDENCE_RELEVANT_SECTIONS = {
        'fact_analysis': ['事实', '经过', '分析'],
        'evidence_evaluation': ['证据', '证明力', '质证'],
        'risk_warning': ['风险', '不利', '弱点'],
        'strategy': ['建议', '策略', '应对']
    }

    def __init__(self, evidence_service=None):
        self.evidence_service = evidence_service
        self.context_injector = EvidenceContextInjector(evidence_service)

    def needs_evidence_injection(self, section_type: str) -> bool:
        """判断段落类型是否需要注入证据"""
        for keywords in self.EVIDENCE_RELEVANT_SECTIONS.values():
            if any(kw in section_type for kw in keywords):
                return True
        return False

    def inject_for_streaming(
        self,
        section_type: str,
        section_content: str,
        case_id: int,
        entities: dict = None
    ) -> str:
        """
        为流式输出注入证据
        """
        if not self.needs_evidence_injection(section_type):
            return section_content

        # 检索相关证据
        db = SessionLocal()
        try:
            if entities:
                evidence = self.context_injector._retrieve_relevant_evidence(
                    db, case_id, entities, 'streaming'
                )
            else:
                evidence = {'all_relevant': []}

            # 生成证据提示
            hint = self._generate_streaming_hint(
                section_type, evidence.get('all_relevant', [])
            )

            if hint:
                return section_content + "\n\n" + hint

            return section_content
        finally:
            db.close()

    def _generate_streaming_hint(
        self,
        section_type: str,
        evidence: list
    ) -> str:
        """生成流式输出的证据提示"""
        if not evidence:
            return ""

        hints = ["**📎 相关证据支撑**：\n"]

        for ev in evidence:
            icon = ev.get('icon', '📎')
            ev_type = ev.get('type_name', '')
            # 法律应用：使用完整内容，不截断
            full_content = ev.get('summary', '')
            hints.append(f"- {icon} [{ev_type}] {full_content}")

        # 识别缺口
        gaps = self._identify_gaps_from_section(section_type, evidence)
        if gaps:
            hints.append("\n**💡 建议补充**：")
            for gap in gaps[:2]:
                hints.append(f"- {gap}")

        return "\n".join(hints)

    def _identify_gaps_from_section(
        self,
        section_type: str,
        evidence: list
    ) -> list:
        """从段落内容识别证据缺口"""
        gaps = []

        # 检查内容中的关键概念
        covered_types = {ev.get('type') for ev in evidence}

        required_map = {
            'fact_analysis': ['CONTRACT', 'DOCUMENT', 'CORRESPONDENCE'],
            'evidence_evaluation': ['CONTRACT', 'PAYMENT', 'CORRESPONDENCE'],
            'risk_warning': ['CONTRACT', 'CORRESPONDENCE'],
            'strategy': ['CONTRACT', 'EVIDENCE_ADVICE']
        }

        required = required_map.get(section_type, [])

        for req_type in required:
            if req_type not in covered_types:
                type_name = EvidenceContextInjector.EVIDENCE_TYPE_NAMES.get(req_type, '证据')
                gaps.append(f"补充{type_name}以增强论证")

        return gaps[:2]


# 单例
evidence_context_injector = EvidenceContextInjector()
streaming_evidence_injector = StreamingEvidenceInjector()
