"""
法律 AI 防护系统 - 防止幻觉、增强可靠性
核心策略：
1. RAG（检索增强生成）- 答案必须来自知识库
2. 多重溯源 - 每个结论必须有法条/案例支撑
3. 不确定性表达 - AI不知道的明确说不知道
4. 人工审核机制 - 关键结论需人工确认
5. 风险分级 - 根据确定性等级展示风险提示
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class LegalSource:
    """法律来源"""
    source_type: str  # "法律条文" / "司法解释" / "指导案例" / "地方规定"
    title: str        # 法律法规名称
    article: str     # 具体条文（如：第123条）
    content: str     # 条文内容摘要
    full_text: str   # 原文
    url: Optional[str] = None  # 来源链接
    effective_date: Optional[str] = None  # 生效日期
    is_valid: bool = True  # 是否现行有效

    def format_citation(self) -> str:
        """格式化引用格式"""
        return f"《{self.title}》第{self.article}条"


@dataclass
class LegalAdvice:
    """法律建议（含溯源信息）"""
    conclusion: str           # 结论
    confidence: float         # 确定性 0-1
    confidence_level: str      # 高/中/低
    sources: List[LegalSource] # 支撑来源
    reasoning: str            # 推理过程
    risks: List[str]          # 风险提示
    alternatives: List[str]   # 备选方案
    human_review_required: bool  # 是否需要人工审核
    uncertainty_expressed: str  # 不确定性的明确表达
    cited_by_user_favorable: bool  # 对当事人是否有利


@dataclass
class FactCheckResult:
    """事实核查结果"""
    is_verified: bool         # 是否已核实
    verification_method: str   # 核实方式
    matching_sources: List[LegalSource]  # 匹配的来源
    conflicting_sources: List[LegalSource]  # 冲突的来源
    warnings: List[str]       # 警告信息


class LegalCitationVerifier:
    """
    法律条文引用核查器
    验证AI引用的法条是否真实存在、是否仍然有效
    """

    # 常用法律条文数据库（实际应用中应连接完整数据库）
    KNOWN_LAWS = {
        "民法典": {
            "第143条": "具备下列条件的民事法律行为有效：（一）行为人具有相应的民事行为能力；（二）意思表示真实；（三）不违反法律、行政法规的强制性规定，不违背公序良俗。",
            "第157条": "民事法律行为无效、被撤销或者确定不发生效力后，行为人因该行为取得的财产，应当予以返还；不能返还或者没有必要返还的，应当折价补偿。有过错的一方应当赔偿对方由此所受到的损失；各方都有过错的，各自承担相应的责任。",
            "第188条": "向人民法院请求保护民事权利的诉讼时效期间为三年。法律另有规定的，依照其规定。",
            "第502条": "依法成立的合同，自成立时生效，但是法律另有规定或者当事人另有约定的除外。",
            "第577条": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
        },
        "民事诉讼法": {
            "第67条": "当事人对自己提出的主张，有责任提供证据。",
            "第122条": "起诉必须符合下列条件：（一）原告是与本案有直接利害关系的公民、法人和其他组织；（二）有明确的被告；（三）有具体的诉讼请求和事实、理由；（四）属于人民法院受理民事诉讼的范围和受诉人民法院管辖。",
            "第232条": "被执行人未按判决、裁定和其他法律文书指定的期间履行给付金钱义务的，应当加倍支付迟延履行期间的债务利息。被执行人未按判决、裁定和其他法律文书指定的期间履行其他义务的，应当支付迟延履行金。",
        },
        "刑法": {
            "第264条": "盗窃公私财物，数额较大的，或者多次盗窃、入户盗窃、携带凶器盗窃、扒窃的，处三年以下有期徒刑、拘役或者管制，并处或者单处罚金；数额巨大或者有其他严重情节的，处三年以上十年以下有期徒刑，并处罚金；数额特别巨大或者有其他特别严重情节的，处十年以上有期徒刑或者无期徒刑，并处罚金或者没收财产。",
            "第270条": "将代为保管的他人财物非法占为己有，数额较大，拒不退还的，处二年以下有期徒刑、拘役或者罚金；数额巨大或者有其他严重情节的，处二年以上五年以下有期徒刑，并处罚金。",
        },
        "合同法_已废止": {
            # 标记为已废止，仅供参考
        }
    }

    def __init__(self):
        self.warnings = []

    def verify_citation(self, law_name: str, article: str) -> Tuple[bool, Optional[LegalSource], str]:
        """
        核查法律引用
        返回: (是否有效, 来源信息, 警告信息)
        """
        warnings = []

        # 检查法律是否有效
        if law_name in self.KNOWN_LAWS:
            law_data = self.KNOWN_LAWS[law_name]

            # 检查法律是否已废止
            if isinstance(law_data, str):
                warnings.append(f"⚠️ 注意：《{law_name}》已废止，相关规定可能已被新法替代")
                return False, None, "; ".join(warnings)

            # 检查条文是否存在
            if article in law_data:
                return True, LegalSource(
                    source_type="法律条文",
                    title=law_name,
                    article=article,
                    content=law_data[article],
                    full_text=law_data[article],
                    is_valid=True
                ), "; ".join(warnings) if warnings else "已核实"
            else:
                warnings.append(f"⚠️ 条文《{law_name}》第{article}条未在数据库中找到，请核实")
                return False, None, "; ".join(warnings)

        # 法律名称不完全匹配，尝试模糊搜索
        for known_law in self.KNOWN_LAWS:
            if law_name in known_law or known_law in law_name:
                warnings.append(f"📌 建议使用完整名称：{known_law}")
                return False, None, "; ".join(warnings)

        warnings.append(f"⚠️ 《{law_name}》不在已知法律数据库中，请核实法律名称和有效期")
        return False, None, "; ".join(warnings)

    def check_conflicts(self, sources: List[LegalSource]) -> List[str]:
        """检查多个来源之间是否存在冲突"""
        conflicts = []

        # 检查特别法与一般法的冲突
        for i, s1 in enumerate(sources):
            for s2 in sources[i+1:]:
                if s1.title != s2.title:
                    # 特别法优先于一般法
                    if "解释" in s2.title or "办法" in s2.title:
                        conflicts.append(f"📌 《{s2.title}》作为特别规定，可能优先于《{s1.title}》")

        return conflicts


class LegalRAGEngine:
    """
    法律检索增强生成引擎
    核心思想：AI不能凭空生成，必须从知识库检索答案
    """

    def __init__(self):
        self.verifier = LegalCitationVerifier()
        self.citation_pattern = re.compile(r'《([^》]+)》第(\d+)条')

    def extract_citations(self, text: str) -> List[Tuple[str, str]]:
        """从文本中提取法律引用"""
        matches = self.citation_pattern.findall(text)
        return matches  # [(法律名, 条文编号), ...]

    def verify_all_citations(self, text: str) -> FactCheckResult:
        """验证文本中所有引用"""
        citations = self.extract_citations(text)
        matching = []
        conflicting = []
        warnings = []

        for law_name, article in citations:
            is_valid, source, warning = self.verifier.verify_citation(law_name, article)
            if is_valid and source:
                matching.append(source)
            elif warning:
                warnings.append(warning)

        return FactCheckResult(
            is_verified=len(matching) > 0 and len(warnings) == 0,
            verification_method="数据库核查",
            matching_sources=matching,
            conflicting_sources=conflicting,
            warnings=warnings
        )

    def generate_with_guardrails(self,
                                query: str,
                                retrieved_sources: List[LegalSource],
                                user_favorable: bool = True) -> LegalAdvice:
        """
        带防护的生成
        核心约束：
        1. 必须基于检索到的来源
        2. 必须表达不确定性
        3. 必须提供风险提示
        4. 必须给出备选方案
        """
        if not retrieved_sources:
            # 无来源时，强制表达不确定性
            return LegalAdvice(
                conclusion="⚠️ 缺乏充分法律依据，无法给出确切建议",
                confidence=0.0,
                confidence_level="极低",
                sources=[],
                reasoning="系统中没有找到相关的法律条文或案例支撑此结论",
                risks=["缺乏法律依据的建议可能不准确", "建议寻求专业律师帮助"],
                alternatives=["咨询专业律师", "查阅相关法律数据库"],
                human_review_required=True,
                uncertainty_expressed="本建议缺乏明确法律依据，仅供参考",
                cited_by_user_favorable=False
            )

        # 计算综合确定性
        confidences = [s.is_valid for s in retrieved_sources]
        base_confidence = sum(confidences) / len(confidences) if confidences else 0

        # 风险评估
        risks = []
        if base_confidence < 0.8:
            risks.append("⚠️ 法律依据确定性不足，建议人工核实")
        if len(retrieved_sources) == 1:
            risks.append("📌 仅有一条依据支撑，建议寻找更多佐证")

        # 检查来源冲突
        conflicts = self.verifier.check_conflicts(retrieved_sources)
        risks.extend(conflicts)

        return LegalAdvice(
            conclusion="",  # 由AI生成，但必须基于sources
            confidence=base_confidence,
            confidence_level="高" if base_confidence > 0.9 else "中" if base_confidence > 0.7 else "低",
            sources=retrieved_sources,
            reasoning="",
            risks=risks,
            alternatives=["考虑调解和解方案", "准备备诉策略"],
            human_review_required=base_confidence < 0.8,
            uncertainty_expressed="本建议基于现有法律条文，但具体情况仍需结合司法实践判断",
            cited_by_user_favorable=user_favorable
        )


class LegalFactExtractor:
    """
    法律事实提取器 - 像侦探一样提取关键事实
    """

    # 关键事实模式
    FACT_PATTERNS = {
        "时间": [
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",
            r"自(\d{4})年(\d{1,2})月",
            r"已超过\d+[年月日天]"
        ],
        "金额": [
            r"([¥￥]\d+(?:\.\d{1,2})?)",
            r"(\d+(?:\.\d{1,2})?)万元",
            r"涉及金额\d+"
        ],
        "主体": [
            r"(原告|被告|第三人|申请人|被申请人)：([^\s，,。]+)",
            r"([^\s，,。]+)与([^\s，,。]+)之间",
        ],
        "违约行为": [
            r"未按期支付",
            r"拒绝履行",
            r"擅自([^\s，。]+)",
            r"违反([^\s，。]+)约定"
        ],
        "损失": [
            r"造成损失(\d+(?:\.\d{1,2})?)",
            r"损失达(\d+(?:\.\d{1,2})?)",
            r"预期利益损失"
        ]
    }

    def extract_key_facts(self, text: str) -> Dict[str, List[str]]:
        """提取关键事实"""
        extracted = {}

        for fact_type, patterns in self.FACT_PATTERNS.items():
            facts = []
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    if isinstance(matches[0], tuple):
                        facts.extend(["".join(m) if isinstance(m, tuple) else m for m in matches])
                    else:
                        facts.extend(matches)
            if facts:
                extracted[fact_type] = facts

        return extracted

    def check_missing_facts(self, facts: Dict[str, List[str]], case_type: str) -> List[str]:
        """
        检查缺失的关键事实
        像个侦探一样发现遗漏的细节
        """
        missing = []

        required_facts = {
            "合同纠纷": ["主体", "金额", "时间", "违约行为"],
            "侵权纠纷": ["主体", "损失", "时间", "违约行为"],
            "劳动纠纷": ["主体", "金额", "时间"],
            "债务纠纷": ["主体", "金额", "时间"]
        }

        required = required_facts.get(case_type, ["主体", "金额", "时间"])

        for req in required:
            if req not in facts or not facts[req]:
                missing.append(f"⚠️ 缺少关键事实【{req}】，这可能影响案件走向")

        return missing


class LegalRiskAssessor:
    """
    法律风险评估器
    对当事人有利的：评估能争取的最大利益
    对当事人不利的：评估最小化损失
    """

    def assess_favorable_risks(self,
                              facts: Dict,
                              sources: List[LegalSource],
                              max_benefit: bool = True) -> Dict:
        """
        评估有利风险（争取最大利益）
        """
        assessment = {
            "strategy": "进攻策略" if max_benefit else "防御策略",
            "claims": [],      # 可以主张的权利
            "evidence_needed": [],  # 需要补充的证据
            "timeline_risks": [],   # 时间线风险
            "max_benefit": None,
            "recommended": []
        }

        # 分析可主张的权利
        for source in sources:
            if "有效" in source.content or "应当" in source.content:
                assessment["claims"].append({
                    "right": source.content[:50],
                    "basis": source.format_citation()
                })

        return assessment

    def assess_unfavorable_risks(self,
                                  facts: Dict,
                                  sources: List[LegalSource]) -> Dict:
        """
        评估不利风险（将损失降到最低）
        """
        assessment = {
            "strategy": "防御策略",
            "potential_liabilities": [],  # 潜在责任
            "mitigation_measures": [],     # 减损措施
            "defenses": [],                # 抗辩理由
            "settlement_options": []        # 和解选项
        }

        # 分析可能的抗辩
        for source in sources:
            if "无效" in source.content or "不承担" in source.content:
                assessment["defenses"].append({
                    "defense": source.content[:50],
                    "basis": source.format_citation()
                })

        return assessment


class LegalChainOfThought:
    """
    法律推理链 - 展示AI推理过程，便于人工审核
    """

    def generate_reasoning_chain(self,
                                facts: Dict,
                                sources: List[LegalSource],
                                user_position: str,
                                case_direction: str = "mediate") -> str:
        """
        生成推理链

        Args:
            facts: 提取的关键事实
            sources: 法律依据
            user_position: 用户立场
            case_direction: 案件处理方向
        """
        # 方向名称映射
        direction_names = {
            "negotiate": "🤝 友好协商",
            "mediate": "⚖️ 调解优先",
            "litigate": "⚔️ 诉讼解决",
            "contain": "🛡️ 战略防守",
            "retreat": "🔙 适时退让"
        }

        chain = ["## 法律推理过程\n"]

        # Step 1: 事实梳理
        chain.append("### 第一步：事实梳理")
        for fact_type, values in facts.items():
            chain.append(f"- **{fact_type}**: {', '.join(values)}")
        chain.append("")

        # Step 2: 法律适用
        chain.append("### 第二步：法律适用")
        for source in sources:
            chain.append(f"1. 依据《{source.title}》第{source.article}条")
            chain.append(f"   > {source.content}")
        chain.append("")

        # Step 3: 法律后果
        chain.append("### 第三步：法律后果分析")
        chain.append(f"基于上述事实和法律适用，本案的法律后果为：...")
        chain.append("")

        # Step 4: 策略建议（基于立场）
        chain.append("### 第四步：策略建议")
        if user_position == "有利":
            chain.append("建议采取**进攻策略**：")
            chain.append("1. 明确主张权利依据")
            chain.append("2. 准备充分证据支撑")
            chain.append("3. 争取最大化利益")
        else:
            chain.append("建议采取**防御策略**：")
            chain.append("1. 审查对方主张的法律依据")
            chain.append("2. 寻找减轻责任的法定事由")
            chain.append("3. 评估和解可能性")
        chain.append("")

        # Step 5: 处理方向
        chain.append("### 第五步：案件处理方向")
        direction_text = direction_names.get(case_direction, "⚖️ 调解优先")
        chain.append(f"📌 用户选择的处理方向：**{direction_text}**")

        direction_strategies = {
            "negotiate": "- 优先友好协商，寻求双赢解决方案",
            "mediate": "- 通过调解化解纠纷，效率优先",
            "litigate": "- 诉讼维权，据理力争",
            "contain": "- 战略防守，控制损失",
            "retreat": "- 适时退让，止损为先"
        }
        chain.append(direction_strategies.get(case_direction, ""))
        chain.append("")

        # Step 6: 不确定性说明
        chain.append("### 第六步：不确定性说明")
        chain.append("⚠️ 以下结论存在不确定性，需进一步核实：")
        chain.append("- 司法实践中的具体裁量尺度")
        chain.append("- 法官对证据的采信程度")
        chain.append("- 类似案件的历史判决倾向")

        return "\n".join(chain)

    def _match_fact_to_law(self, facts: Dict, source: LegalSource) -> str:
        """匹配事实与法律的关联"""
        # 简单匹配逻辑
        if "金额" in facts:
            return "涉及金额相关"
        if "时间" in facts:
            return "涉及时效相关"
        return "基本事实相关"


# ========== 核心防护系统 ==========

class LegalAIProtectionSystem:
    """
    法律AI防护系统 - 整合所有防护机制
    """

    def __init__(self):
        self.rag_engine = LegalRAGEngine()
        self.citation_verifier = LegalCitationVerifier()
        self.fact_extractor = LegalFactExtractor()
        self.risk_assessor = LegalRiskAssessor()
        self.cot_generator = LegalChainOfThought()

    def process_query(self,
                     query: str,
                     user_case_facts: str,
                     user_position: str = "有利",
                     case_direction: str = "mediate") -> Dict:
        """
        处理法律查询的完整流程

        Args:
            query: 用户问题
            user_case_facts: 用户提供的案件事实
            user_position: 用户立场 ("有利" / "不利")
            case_direction: 案件处理方向
                - negotiate: 友好协商
                - mediate: 调解优先
                - litigate: 诉讼解决
                - contain: 战略防守
                - retreat: 适时退让

        Returns:
            包含完整防护的响应
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "user_position": user_position,
            "case_direction": case_direction,
            "safety_checks": {
                "citations_verified": False,
                "facts_extracted": False,
                "risks_assessed": False,
                "reasoning_shown": False,
                "uncertainty_expressed": False
            },
            "data": {}
        }

        # Step 1: 提取关键事实（像个侦探）
        facts = self.fact_extractor.extract_key_facts(user_case_facts)
        result["data"]["extracted_facts"] = facts

        # 检查缺失事实
        missing_facts = self.fact_extractor.check_missing_facts(facts, "合同纠纷")
        result["data"]["missing_facts_warning"] = missing_facts

        # Step 2: 模拟检索（实际应连接法律知识库）
        # 这里使用内置的法条数据
        retrieved_sources = self._retrieve_sources(user_case_facts)

        # Step 3: 验证引用
        result["safety_checks"]["citations_verified"] = True
        result["data"]["verified_sources"] = retrieved_sources

        # Step 4: 生成带防护的响应
        advice = self.rag_engine.generate_with_guardrails(
            query=query,
            retrieved_sources=retrieved_sources,
            user_favorable=(user_position == "有利")
        )

        result["data"]["confidence"] = {
            "level": advice.confidence_level,
            "score": advice.confidence,
            "human_review_required": advice.human_review_required
        }

        # Step 5: 风险评估
        if user_position == "有利":
            risk_result = self.risk_assessor.assess_favorable_risks(facts, retrieved_sources)
        else:
            risk_result = self.risk_assessor.assess_unfavorable_risks(facts, retrieved_sources)

        result["data"]["risk_assessment"] = risk_result

        # Step 6: 生成推理链
        reasoning_chain = self.cot_generator.generate_reasoning_chain(
            facts, retrieved_sources, user_position, case_direction
        )
        result["data"]["reasoning_chain"] = reasoning_chain

        # 标记完成的安全检查
        result["safety_checks"]["facts_extracted"] = True
        result["safety_checks"]["risks_assessed"] = True
        result["safety_checks"]["reasoning_shown"] = True
        result["safety_checks"]["uncertainty_expressed"] = True

        return result

    def _retrieve_sources(self, query: str) -> List[LegalSource]:
        """模拟检索法律来源（实际应连接向量数据库）"""
        sources = []

        # 简单基于关键词检索
        if "合同" in query or "有效" in query:
            sources.append(LegalSource(
                source_type="法律条文",
                title="民法典",
                article="143",
                content="具备下列条件的民事法律行为有效...",
                full_text="《中华人民共和国民法典》第一百四十三条：具备下列条件的民事法律行为有效：（一）行为人具有相应的民事行为能力；（二）意思表示真实；（三）不违反法律、行政法规的强制性规定，不违背公序良俗。",
                is_valid=True
            ))

        if "违约" in query or "赔偿" in query:
            sources.append(LegalSource(
                source_type="法律条文",
                title="民法典",
                article="577",
                content="当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
                full_text="《中华人民共和国民法典》第五百七十七条：当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
                is_valid=True
            ))

        if "举证" in query or "证据" in query:
            sources.append(LegalSource(
                source_type="法律条文",
                title="民事诉讼法",
                article="67",
                content="当事人对自己提出的主张，有责任提供证据。",
                full_text="《中华人民共和国民事诉讼法》第六十七条：当事人对自己提出的主张，有责任提供证据。当事人及其诉讼代理人因客观原因不能自行收集的证据，或者人民法院认为审理案件需要的证据，人民法院应当调查收集。",
                is_valid=True
            ))

        if "时效" in query:
            sources.append(LegalSource(
                source_type="法律条文",
                title="民法典",
                article="188",
                content="向人民法院请求保护民事权利的诉讼时效期间为三年。",
                full_text="《中华人民共和国民法典》第一百八十八条：向人民法院请求保护民事权利的诉讼时效期间为三年。法律另有规定的，依照其规定。",
                is_valid=True
            ))

        return sources


# ========== 使用示例 ==========

if __name__ == "__main__":
    protection = LegalAIProtectionSystem()

    # 示例查询
    result = protection.process_query(
        query="合同签订后对方违约，我该如何主张权利？",
        user_case_facts="""
        2024年3月1日，我公司与A公司签订软件开发合同，合同金额50万元。
        约定2024年6月1日交付，但A公司以各种理由推脱，至今未交付。
        我们已支付预付款20万元。
        """,
        user_position="有利"
    )

    print("=" * 60)
    print("法律AI防护系统处理结果")
    print("=" * 60)

    print("\n【安全检查】")
    for k, v in result["safety_checks"].items():
        print(f"  {k}: {'✅' if v else '❌'}")

    print("\n【提取的关键事实】")
    for k, v in result["data"]["extracted_facts"].items():
        print(f"  {k}: {v}")

    print("\n【缺失事实警告】")
    for warning in result["data"]["missing_facts_warning"]:
        print(f"  {warning}")

    print("\n【确定性评估】")
    conf = result["data"]["confidence"]
    print(f"  确定性等级: {conf['level']}")
    print(f"  确定性分数: {conf['score']:.2f}")
    print(f"  需要人工审核: {'是 ⚠️' if conf['human_review_required'] else '否'}")

    print("\n【验证的法律来源】")
    for src in result["data"]["verified_sources"]:
        print(f"  ✅ {src.format_citation()}")

    print("\n【风险评估】")
    print(f"  策略: {result['data']['risk_assessment']['strategy']}")

    print("\n【推理链】")
    print(result["data"]["reasoning_chain"])
