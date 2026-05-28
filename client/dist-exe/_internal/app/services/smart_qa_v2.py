"""
智能问答系统 V2
支持：意图识别、澄清机制、多轮对话、证据缺口检测
"""
import os
import json
import uuid
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

# 获取当前日期
CURRENT_DATE = datetime.now().strftime('%Y年%m月%d日')
CURRENT_YEAR = datetime.now().year

from app.models.conversation import (
    ConversationSession, ConversationMessage, ClarificationRecord,
    QuestionAnalysis, ConversationType, ConversationStatus,
    ClarificationStatus, QuestionIntent, ClarificationDimension
)
from app.models.evidence import EvidenceItem
from app.models.case import Case
from app.db.database import SessionLocal
from app.services.evidence_v2 import EvidenceServiceV2


class SmartQAServiceV2:
    """
    智能问答系统 V2
    渐进式理解 + 主动澄清 + 证据引导
    """

    # 意图分类体系
    INTENT_TAXONOMY = {
        'FACT_QUERY': {
            'name': '事实查询',
            'keywords': ['什么时候', '谁', '多少', '哪个', '什么是', '有无', '是否', '哪方'],
            'required_clarity': 0.7,
            'icon': '🔍',
            'color': '#1890ff'
        },
        'LEGAL_ADVICE': {
            'name': '法律建议',
            'keywords': ['能否', '应该', '可以', '是否合法', '规定', '应当', '需要'],
            'required_clarity': 0.6,
            'icon': '⚖️',
            'color': '#52c41a'
        },
        'EVIDENCE_ADVICE': {
            'name': '证据建议',
            'keywords': ['需要什么证据', '证据', '证明', '材料', '提供什么', '举证'],
            'required_clarity': 0.5,
            'icon': '📎',
            'color': '#faad14'
        },
        'STRATEGY_ADVICE': {
            'name': '策略建议',
            'keywords': ['策略', '怎么起诉', '如何应对', '下一步', '怎么办', '如何处理'],
            'required_clarity': 0.6,
            'icon': '🎯',
            'color': '#722ed1'
        },
        'DOCUMENT_GENERATION': {
            'name': '文书生成',
            'keywords': ['写', '起草', '生成', '诉状', '合同', '协议', '函件'],
            'required_clarity': 0.6,
            'icon': '📝',
            'color': '#eb2f96'
        },
        'RISK_ASSESSMENT': {
            'name': '风险评估',
            'keywords': ['风险', '胜诉', '可能', '后果', '利弊', '会不会输', '有无风险'],
            'required_clarity': 0.5,
            'icon': '⚠️',
            'color': '#f5222d'
        },
        'CASE_STATUS': {
            'name': '案件状态',
            'keywords': ['现在', '当前', '进度', '状态', '阶段', '进行到哪'],
            'required_clarity': 0.8,
            'icon': '📋',
            'color': '#13c2c2'
        }
    }

    # 澄清维度系统
    CLARIFICATION_DIMENSIONS = {
        'WHO': {
            'name': '当事人',
            'description': '涉及哪些人',
            'icon': '👤',
            'questions': [
                '请问您说的"甲方"是指哪一方？',
                '对方当事人是谁？',
                '是否有代理人？代理人的身份是？',
                '涉及哪些相关方？'
            ]
        },
        'WHEN': {
            'name': '时间',
            'description': '关键时间节点',
            'icon': '📅',
            'questions': [
                '这件事是什么时候发生的？',
                '具体的日期是哪天？',
                '是否已超过诉讼时效？',
                '合同约定的履行期限是？'
            ]
        },
        'WHAT': {
            'name': '事实',
            'description': '具体发生了什么',
            'icon': '❓',
            'questions': [
                '能详细描述一下具体情况吗？',
                '具体金额或数量是？',
                '对方的具体行为是什么？',
                '具体涉及什么内容？'
            ]
        },
        'WHERE': {
            'name': '地点',
            'description': '地点和管辖',
            'icon': '📍',
            'questions': [
                '合同签订地点是？',
                '合同履行地点在哪里？',
                '是否涉及专属管辖？',
                '事情发生在哪个地点？'
            ]
        },
        'WHY': {
            'name': '目的',
            'description': '动机和目的',
            'icon': '🎯',
            'questions': [
                '您的主要诉求是什么？',
                '您希望通过什么方式解决？',
                '对方这样做的原因是什么？',
                '您的预期目标是什么？'
            ]
        },
        'HOW': {
            'name': '过程',
            'description': '事情经过',
            'icon': '📋',
            'questions': [
                '事情经过是怎样的？',
                '双方如何沟通的？',
                '是否有过协商？结果如何？',
                '具体是怎么发生的？'
            ]
        },
        'EVIDENCE': {
            'name': '证据',
            'description': '有哪些证据材料',
            'icon': '📎',
            'questions': [
                '您有哪些证据材料？',
                '是否有书面协议或合同？',
                '是否有聊天记录或邮件？',
                '是否有付款记录或收据？'
            ]
        }
    }

    # 清晰度阈值 - 降低以提高响应性
    CLARITY_THRESHOLD_HIGH = 0.7   # 清晰：直接回答
    CLARITY_THRESHOLD_MEDIUM = 0.35  # 半清晰：部分回答 + 澄清 (降低阈值)
    CLARITY_THRESHOLD_LOW = 0.0     # 模糊：引导澄清

    def __init__(self, llm_service=None):
        self.llm = llm_service
        self.evidence_service = EvidenceServiceV2()
        self.db = SessionLocal()

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    # ==================== 主入口 ====================

    def ask(
        self,
        question: str,
        case_id: int,
        session_id: str = None,
        user_context: dict = None
    ) -> dict:
        """
        智能问答入口

        Args:
            question: 用户问题
            case_id: 案件ID
            session_id: 会话ID（可选，用于多轮对话）
            user_context: 用户上下文（可选）

        Returns:
            回答结果
        """
        db = self._get_db()
        try:
            # 1. 获取或创建会话
            session = self._get_or_create_session(db, session_id, case_id, question)

            # 2. 保存用户消息
            user_message = self._save_message(
                db, session.id, 'user', question, message_type='text'
            )

            # 3. 问题分析
            analysis = self._analyze_question(db, session.id, question, case_id)

            # 4. 清晰度评估
            clarity = self._assess_clarity(question, analysis, case_id)

            # 5. 根据清晰度决策
            if clarity['clarity_score'] >= self.CLARITY_THRESHOLD_HIGH:
                # 清晰问题：直接回答
                result = self._generate_direct_answer(
                    db, session, question, analysis, clarity, case_id
                )
            elif clarity['clarity_score'] >= self.CLARITY_THRESHOLD_MEDIUM:
                # 半清晰：部分回答 + 澄清
                result = self._generate_partial_answer(
                    db, session, question, analysis, clarity, case_id
                )
            else:
                # 模糊问题：引导澄清
                result = self._generate_clarification_guidance(
                    db, session, question, analysis, clarity, case_id
                )

            # 6. 保存AI回复
            self._save_message(
                db, session.id, 'assistant',
                result.get('answer', ''),
                message_type=result.get('type', 'answer')
            )

            # 7. 更新会话
            session.message_count += 1
            session.last_message_at = datetime.utcnow()
            session.overall_clarity = clarity['clarity_score']
            db.commit()

            result['session_id'] = session.id
            result['analysis'] = analysis.to_dict() if analysis else None

            return result

        except Exception as e:
            db.rollback()
            return {
                'status': 'error',
                'message': str(e),
                'type': 'error'
            }
        finally:
            db.close()

    # ==================== 会话管理 ====================

    def _get_or_create_session(
        self,
        db: Session,
        session_id: str,
        case_id: int,
        question: str
    ) -> ConversationSession:
        """获取或创建会话"""
        if session_id:
            session = db.query(ConversationSession).filter(
                ConversationSession.id == session_id
            ).first()
            if session:
                return session

        # 创建新会话
        intent = self._classify_intent_sync(question)
        session = ConversationSession(
            id=str(uuid.uuid4()),
            case_id=case_id,
            session_type=ConversationType.QA.value,
            title=question[:50] + '...' if len(question) > 50 else question,
            primary_intent=intent,
            status=ConversationStatus.ACTIVE.value
        )
        db.add(session)
        db.flush()
        return session

    def _save_message(
        self,
        db: Session,
        session_id: str,
        role: str,
        content: str,
        message_type: str = 'text',
        metadata: dict = None
    ) -> ConversationMessage:
        """保存消息"""
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            entities=metadata or {}
        )
        db.add(message)
        return message

    # ==================== 问题分析 ====================

    def _analyze_question(
        self,
        db: Session,
        session_id: str,
        question: str,
        case_id: int
    ) -> QuestionAnalysis:
        """分析问题"""
        # 意图识别
        intent = self._classify_intent_sync(question)

        # 实体提取
        entities = self._extract_entities_sync(question, case_id)

        # 创建分析记录
        analysis = QuestionAnalysis(
            id=str(uuid.uuid4()),
            session_id=session_id,
            original_question=question,
            question_hash=str(hash(question)),
            intent=intent,
            intent_confidence=0.8,
            entities=entities,
            clarification_needed=False
        )
        db.add(analysis)
        db.flush()

        return analysis

    def _classify_intent_sync(self, question: str) -> str:
        """同步意图分类"""
        question_lower = question.lower()

        for intent_type, config in self.INTENT_TAXONOMY.items():
            for keyword in config['keywords']:
                if keyword in question_lower:
                    return intent_type

        return QuestionIntent.FACT_QUERY.value

    def _extract_entities_sync(self, question: str, case_id: int) -> dict:
        """同步实体提取"""
        entities = {
            'parties': [],
            'dates': [],
            'amounts': [],
            'documents': [],
            'locations': []
        }

        # 提取日期
        date_pattern = r'(\d{4})[年\-\/](\d{1,2})[月\-\/](\d{1,2})[日]?'
        dates = re.findall(date_pattern, question)
        entities['dates'] = [f"{d[0]}年{d[1]}月{d[2]}日" for d in dates]

        # 提取金额
        money_pattern = r'[\d,]+[万千佰亿万]?[元]?'
        amounts = re.findall(money_pattern, question)
        entities['amounts'] = amounts[:5]

        # 提取当事人（需要结合案件信息）
        # 简化实现
        party_pattern = r'([\u4e00-\u9fa5]{2,4})(?:说|称|认|主张|表示)'
        parties = re.findall(party_pattern, question)
        entities['parties'] = parties[:3]

        return entities

    # ==================== 清晰度评估 ====================

    def _assess_clarity(
        self,
        question: str,
        analysis: QuestionAnalysis,
        case_id: int
    ) -> dict:
        """
        多维度清晰度评估
        """
        dimension_scores = {}

        # 1. 问题长度评估
        if len(question) < 10:
            dimension_scores['length'] = 0.2
        elif len(question) < 30:
            dimension_scores['length'] = 0.5
        elif len(question) < 100:
            dimension_scores['length'] = 0.8
        else:
            dimension_scores['length'] = 1.0

        # 2. 意图清晰度
        intent_config = self.INTENT_TAXONOMY.get(analysis.intent, {})
        required_clarity = intent_config.get('required_clarity', 0.6)
        dimension_scores['intent'] = required_clarity

        # 3. 实体完整度
        entities = analysis.entities or {}
        entity_count = sum(len(v) for v in entities.values())
        if entity_count == 0:
            dimension_scores['entities'] = 0.3
        elif entity_count < 3:
            dimension_scores['entities'] = 0.6
        else:
            dimension_scores['entities'] = 0.9

        # 4. 问题类型判断
        has_question_words = any(kw in question for kw in ['吗', '是否', '有没有', '如何', '怎么'])
        dimension_scores['question_clarity'] = 0.8 if has_question_words else 0.5

        # 5. 上下文关联度（检查是否引用了案件信息）
        db = self._get_db()
        try:
            case = db.query(Case).filter(Case.id == case_id).first()
            if case:
                case_text = f"{case.title} {case.description or ''}"
                question_words = set(re.findall(r'[\u4e00-\u9fa5]+', question))
                case_words = set(re.findall(r'[\u4e00-\u9fa5]+', case_text))
                overlap = len(question_words & case_words)
                dimension_scores['context'] = min(1.0, overlap / 10)
            else:
                dimension_scores['context'] = 0.5
        finally:
            db.close()

        # 综合评分
        weights = {
            'length': 0.15,
            'intent': 0.25,
            'entities': 0.25,
            'question_clarity': 0.15,
            'context': 0.20
        }

        clarity_score = sum(
            dimension_scores[k] * weights[k]
            for k in weights
        )

        # 识别需要澄清的维度
        clarification_dims = []
        for dim, score in dimension_scores.items():
            if score < 0.6:
                if dim == 'entities':
                    clarification_dims.append('WHAT')
                elif dim == 'context':
                    clarification_dims.append('EVIDENCE')

        return {
            'clarity_score': clarity_score,
            'dimension_scores': dimension_scores,
            'clarification_dimensions': clarification_dims,
            'threshold_high': self.CLARITY_THRESHOLD_HIGH,
            'threshold_medium': self.CLARITY_THRESHOLD_MEDIUM
        }

    # ==================== 回答生成 ====================

    def _generate_direct_answer(
        self,
        db: Session,
        session: ConversationSession,
        question: str,
        analysis: QuestionAnalysis,
        clarity: dict,
        case_id: int
    ) -> dict:
        """清晰问题：直接完整回答"""
        # 构建上下文
        context = self._build_answer_context(db, question, case_id, analysis)

        # 生成回答
        answer = self._generate_answer_content(question, context, case_id)

        # 分析证据缺口
        evidence_gaps = self._analyze_evidence_gaps(
            db, question, case_id, analysis
        )

        # 更新会话
        session.final_answer = answer  # 完整答案，不截断
        session.answer_type = 'DIRECT'
        session.confidence = clarity['clarity_score']
        session.evidence_gaps = [g['suggestion'] for g in evidence_gaps.get('gaps', [])]

        return {
            'status': 'success',
            'type': 'direct_answer',
            'answer': answer,
            'intent': analysis.intent,
            'confidence': clarity['clarity_score'],
            'evidence_gaps': evidence_gaps.get('gaps', []),
            'suggestions': evidence_gaps.get('suggestions', [])
        }

    def _generate_partial_answer(
        self,
        db: Session,
        session: ConversationSession,
        question: str,
        analysis: QuestionAnalysis,
        clarity: dict,
        case_id: int
    ) -> dict:
        """半清晰问题：部分回答 + 引导澄清"""
        # 生成部分回答
        partial_context = self._build_answer_context(
            db, question, case_id, analysis, partial=True
        )
        partial_answer = self._generate_answer_content(
            question, partial_context, case_id, partial=True
        )

        # 生成澄清问题
        clarifying_questions = self._generate_clarifying_questions(
            question, clarity, analysis, case_id
        )

        # 创建澄清记录
        for cq in clarifying_questions[:2]:
            clarification = ClarificationRecord(
                id=str(uuid.uuid4()),
                session_id=session.id,
                original_question=question,
                dimension=cq.get('dimension'),
                priority=cq.get('priority', 'normal'),
                reason=cq.get('reason'),
                clarifying_questions=[{'question': cq['question'], 'reason': cq.get('reason', '')}],
                selected_question=cq['question'],
                status=ClarificationStatus.PENDING.value
            )
            db.add(clarification)
            session.clarification_count += 1

        # 更新会话
        session.answer_type = 'PARTIAL'
        session.confidence = clarity['clarity_score']

        guidance = self._format_clarification_guidance(clarifying_questions)

        return {
            'status': 'success',
            'type': 'partial_answer',
            'answer': partial_answer + "\n\n" + guidance,
            'intent': analysis.intent,
            'confidence': clarity['clarity_score'],
            'clarifying_questions': clarifying_questions,
            'partial_answer': partial_answer
        }

    def _generate_clarification_guidance(
        self,
        db: Session,
        session: ConversationSession,
        question: str,
        analysis: QuestionAnalysis,
        clarity: dict,
        case_id: int
    ) -> dict:
        """模糊问题：系统性引导澄清"""
        # 生成澄清问题
        clarifying_questions = self._generate_clarifying_questions(
            question, clarity, analysis, case_id, comprehensive=True
        )

        # 创建澄清记录
        for cq in clarifying_questions:
            clarification = ClarificationRecord(
                id=str(uuid.uuid4()),
                session_id=session.id,
                original_question=question,
                dimension=cq.get('dimension'),
                priority=cq.get('priority', 'normal'),
                reason=cq.get('reason'),
                clarifying_questions=[{'question': q['question'], 'reason': q.get('reason', '')}
                                     for q in cq.get('questions', [cq])],
                selected_question=cq.get('question') or cq.get('questions', [{}])[0].get('question'),
                status=ClarificationStatus.PENDING.value
            )
            db.add(clarification)
            session.clarification_count += 1

        # 更新会话
        session.clarification_needed = True
        session.clarification_dimensions = clarity.get('clarification_dimensions', [])

        guidance = self._format_clarification_guidance(clarifying_questions)

        return {
            'status': 'success',
            'type': 'clarification_needed',
            'answer': guidance,
            'intent': analysis.intent,
            'confidence': clarity['clarity_score'],
            'clarifying_questions': clarifying_questions,
            'clarification_dimensions': clarity.get('clarification_dimensions', []),
            'dimension_scores': clarity.get('dimension_scores', {})
        }

    # ==================== 上下文构建 ====================

    def _build_answer_context(
        self,
        db: Session,
        question: str,
        case_id: int,
        analysis: QuestionAnalysis,
        partial: bool = False
    ) -> dict:
        """构建回答上下文"""
        context = {
            'case_info': '',
            'evidence': [],
            'related_laws': [],
            'similar_cases': []
        }

        # 获取案件信息
        case = db.query(Case).filter(Case.id == case_id).first()
        if case:
            context['case_info'] = f"""
案件标题：{case.title}
案由：{case.cause or '未指定'}
案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}
案件描述：{case.description or '未填写'}
"""

        # 获取相关证据
        evidence_list = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id,
            EvidenceItem.is_current == True
        ).limit(10).all()

        for ev in evidence_list:
            content = ev.extracted_content or ev.raw_content or ev.summary or ''
            if content:
                ev_type = EvidenceItem.get_type_display(ev.evidence_type)
                context['evidence'].append({
                    'id': ev.id,
                    'type': ev.evidence_type,
                    'type_name': ev_type.get('name', ''),
                    'summary': content,  # 法律应用：使用完整内容
                    'credibility': ev.credibility_score
                })

        return context

    def _generate_answer_content(
        self,
        question: str,
        context: dict,
        case_id: int,
        partial: bool = False
    ) -> str:
        """生成回答内容"""
        # 如果有LLM服务，使用它
        if self.llm:
            prompt = f"""
用户问题：{question}

案件信息：
{context.get('case_info', '')}

相关证据：
{self._format_evidence_context(context.get('evidence', []))}

请回答用户问题，要求：
1. 结论先行
2. 法律依据明确
3. 事实分析透彻
4. 如涉及证据，请引用证据编号
5. 主动提示需要补充的证据（如有）
"""
            return self.llm.chat([
                {"role": "system", "content": f"""你是一位专业的法律AI助手。

【当前日期信息】
- 当前日期：{CURRENT_DATE}
- 当前年份：{CURRENT_YEAR}年
在分析时效问题、期限计算时，请务必使用上述当前日期。

请回答用户问题，要求：
1. 结论先行
2. 法律依据明确
3. 事实分析透彻
4. 如涉及证据，请引用证据编号
5. 主动提示需要补充的证据（如有）"""},
                {"role": "user", "content": prompt}
            ])

        # 无LLM时的简单回复
        return self._generate_simple_answer(question, context)

    def _generate_simple_answer(self, question: str, context: dict) -> str:
        """生成简单回答（无LLM时）"""
        parts = []

        parts.append("## 回答\n")
        parts.append(f"您的问题是：{question}\n")

        if context.get('case_info'):
            parts.append("\n### 相关案件信息\n")
            parts.append(context['case_info'][:50000])

        if context.get('evidence'):
            parts.append("\n### 相关证据\n")
            for ev in context['evidence']:  # 显示全部相关证据，无数量限制
                parts.append(f"- [{ev['type_name']}] {ev['summary']}...\n")

        parts.append("\n---\n")
        parts.append("💡 **提示**：为了给您更准确的法律建议，建议补充以下信息：\n")
        parts.append("- 具体的日期和时间\n")
        parts.append("- 涉及的金额\n")
        parts.append("- 相关证据材料\n")

        return "".join(parts)

    def _format_evidence_context(self, evidence: list) -> str:
        """格式化证据上下文"""
        if not evidence:
            return "暂无相关证据"

        lines = []
        # 法律应用：保留全部相关证据，不限制数量
        for i, ev in enumerate(evidence, 1):
            lines.append(f"{i}. [{ev.get('type_name', '证据')}] 证据{i}")
            # 法律应用：使用完整内容，不截断
            lines.append(f"   内容：{ev.get('summary', '')}")
            lines.append(f"   信度：{ev.get('credibility', 0):.0f}%\n")

        return "\n".join(lines)

    # ==================== 澄清问题生成 ====================

    def _generate_clarifying_questions(
        self,
        question: str,
        clarity: dict,
        analysis: QuestionAnalysis,
        case_id: int,
        comprehensive: bool = False
    ) -> list:
        """生成澄清问题"""
        questions = []
        dims = clarity.get('clarification_dimensions', [])

        # 根据维度生成问题
        for dim in dims:
            dim_config = self.CLARIFICATION_DIMENSIONS.get(dim)
            if not dim_config:
                continue

            # 选择最合适的问题
            selected_q = self._select_best_question(
                dim_config['questions'], question, dim
            )

            questions.append({
                'dimension': dim,
                'dimension_name': dim_config['name'],
                'dimension_icon': dim_config['icon'],
                'question': selected_q,
                'priority': self._get_dimension_priority(dim, analysis.intent),
                'reason': f'需要明确{dim_config["description"]}以便准确分析'
            })

        # 如果维度为空，生成通用问题
        if not questions:
            questions.append({
                'dimension': 'WHAT',
                'dimension_name': '事实细节',
                'dimension_icon': '❓',
                'question': '能详细描述一下具体情况吗？',
                'priority': 'high',
                'reason': '需要了解更多事实细节'
            })

        # 按优先级排序
        priority_order = {'critical': 0, 'high': 1, 'important': 2, 'normal': 3}
        questions.sort(key=lambda x: priority_order.get(x.get('priority', 'normal'), 3))

        return questions[:3]  # 最多返回3个问题

    def _select_best_question(self, base_questions: list, original: str, dim: str) -> str:
        """选择最合适的问题"""
        # 简单实现：返回第一个
        if base_questions:
            return base_questions[0]
        return f'请提供更多关于"{dim}"的信息'

    def _get_dimension_priority(self, dimension: str, intent: str) -> str:
        """根据意图确定维度优先级"""
        priority_map = {
            'FACT_QUERY': {'WHAT': 'high', 'WHEN': 'high', 'WHO': 'medium', 'EVIDENCE': 'medium'},
            'LEGAL_ADVICE': {'EVIDENCE': 'high', 'WHAT': 'high', 'HOW': 'medium', 'WHY': 'low'},
            'STRATEGY_ADVICE': {'WHAT': 'high', 'WHY': 'medium', 'EVIDENCE': 'high'},
            'RISK_ASSESSMENT': {'EVIDENCE': 'high', 'WHAT': 'medium', 'HOW': 'medium'},
            'EVIDENCE_ADVICE': {'EVIDENCE': 'high', 'WHAT': 'medium'}
        }

        return priority_map.get(intent, {}).get(dimension, 'normal')

    def _format_clarification_guidance(self, questions: list) -> str:
        """格式化澄清引导"""
        parts = []

        parts.append("\n---\n")
        parts.append("## 💬 为了更准确地帮助您，请补充以下信息\n")
        parts.append("（选择最方便的回答即可）\n\n")

        for i, q in enumerate(questions[:3], 1):
            icon = q.get('dimension_icon', '❓')
            dim_name = q.get('dimension_name', '')
            question = q.get('question', '')
            priority = q.get('priority', 'normal')

            priority_tag = ''
            if priority == 'high':
                priority_tag = ' ⚡'
            elif priority == 'critical':
                priority_tag = ' 🔴'

            parts.append(f"{i}. {icon} **{dim_name}**{priority_tag}\n")
            parts.append(f"   {question}\n\n")

        parts.append("---\n")
        parts.append("💡 **小提示**：如果您不确定如何回答某个问题，也可以告诉我您知道的大致情况，")
        parts.append("我会根据您提供的信息进行分析，并指出需要进一步确认的地方。\n")

        return "".join(parts)

    # ==================== 证据缺口分析 ====================

    def _analyze_evidence_gaps(
        self,
        db: Session,
        question: str,
        case_id: int,
        analysis: QuestionAnalysis
    ) -> dict:
        """分析证据缺口"""
        # 获取案件证据
        evidence_list = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id,
            EvidenceItem.is_current == True
        ).all()

        existing_types = set(e.evidence_type for e in evidence_list)

        gaps = []
        suggestions = []

        # 根据意图判断需要的证据类型
        intent_requirements = {
            'FACT_QUERY': ['CONTRACT', 'CORRESPONDENCE', 'DOCUMENT'],
            'LEGAL_ADVICE': ['CONTRACT', 'CORRESPONDENCE', 'PAYMENT'],
            'EVIDENCE_ADVICE': [],
            'STRATEGY_ADVICE': ['CONTRACT', 'CORRESPONDENCE', 'PAYMENT', 'DOCUMENT'],
            'RISK_ASSESSMENT': ['CONTRACT', 'CORRESPONDENCE', 'PAYMENT', 'DOCUMENT']
        }

        required_types = intent_requirements.get(analysis.intent, [])

        for req_type in required_types:
            if req_type not in existing_types:
                type_info = EvidenceItem.get_type_display(req_type)
                gaps.append({
                    'type': req_type,
                    'name': type_info.get('name', req_type),
                    'icon': type_info.get('icon', '📎'),
                    'suggestion': f'建议补充{type_info.get("name", "相关")}证据以支撑分析'
                })
                suggestions.append(f"补充{type_info.get('name', '证据')}：{type_info.get('name', '证据')}可以证明关键事实")

        return {
            'gaps': gaps[:5],
            'suggestions': suggestions[:5],
            'coverage_score': max(0, 100 - len(gaps) * 20)
        }

    # ==================== 会话管理接口 ====================

    def get_session(self, session_id: str) -> dict:
        """获取会话详情"""
        db = self._get_db()
        try:
            session = db.query(ConversationSession).filter(
                ConversationSession.id == session_id
            ).first()

            if not session:
                return None

            # 获取消息
            messages = db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session_id
            ).order_by(ConversationMessage.created_at).all()

            # 获取澄清记录
            clarifications = db.query(ClarificationRecord).filter(
                ClarificationRecord.session_id == session_id
            ).all()

            return {
                'session': session.to_dict(),
                'messages': [m.to_dict() for m in messages],
                'clarifications': [c.to_dict() for c in clarifications]
            }
        finally:
            db.close()

    def resolve_clarification(
        self,
        session_id: str,
        clarification_id: str,
        answer: str
    ) -> dict:
        """处理澄清回答"""
        db = self._get_db()
        try:
            clarification = db.query(ClarificationRecord).filter(
                ClarificationRecord.id == clarification_id,
                ClarificationRecord.session_id == session_id
            ).first()

            if not clarification:
                return {'status': 'error', 'message': '澄清记录不存在'}

            # 更新澄清状态
            clarification.user_answer = answer
            clarification.status = ClarificationStatus.RESOLVED.value
            clarification.resolved_at = datetime.utcnow()
            clarification.impact_on_clarity = 0.3  # 假设澄清提升了30%清晰度

            db.commit()

            # 继续回答原问题
            session = db.query(ConversationSession).filter(
                ConversationSession.id == session_id
            ).first()

            # 使用澄清后的上下文重新生成回答
            return {
                'status': 'success',
                'clarification': clarification.to_dict(),
                'message': '已记录您的回答，正在生成更准确的分析...'
            }
        except Exception as e:
            db.rollback()
            return {'status': 'error', 'message': str(e)}
        finally:
            db.close()

    def get_conversation_history(self, case_id: int, limit: int = 20) -> list:
        """获取对话历史"""
        db = self._get_db()
        try:
            sessions = db.query(ConversationSession).filter(
                ConversationSession.case_id == case_id
            ).order_by(ConversationSession.updated_at.desc()).limit(limit).all()

            return [s.to_dict() for s in sessions]
        finally:
            db.close()


# 单例
smart_qa_service_v2 = SmartQAServiceV2()
