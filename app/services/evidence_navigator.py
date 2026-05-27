"""
主动式证据引导系统
================
核心理念：用户不是律师，系统应该像资深律师一样主动发现证据缺口，
         引导用户补充信息，持续优化案件准备度。

设计原则：
1. 主动性：系统主动发现问题，不等用户问
2. 可视化：直观的证据图谱，一看就懂
3. 引导性：像问诊一样系统化收集信息
4. 递进性：先抓重点，后补细节
5. 实用性：每个缺口都有具体行动建议
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class EvidenceGapSeverity(Enum):
    """证据缺口严重程度"""
    CRITICAL = "critical"    # 🔴 致命缺失 - 必须补齐
    IMPORTANT = "important"  # 🟡 重要缺失 - 建议补齐
    OPTIONAL = "optional"   # 🟢 可选补充 - 有则更好


class ProofDirection(Enum):
    """证明方向"""
    PLAINTIFF = "原告"       # 对原告有利
    DEFENDANT = "被告"       # 对被告有利
    NEUTRAL = "中立"         # 双方都可用


@dataclass
class EvidenceItem:
    """证据项"""
    id: str
    name: str                      # 证据名称
    description: str               # 证据描述
    evidence_type: str              # 证据类型
    custody: str                    # 举证方
    status: str = "未提交"           # 未提交/已提交/已质证
    
    # 证明力分析
    proves: List[str] = field(default_factory=list)    # 能证明什么
    strength: float = 0.5          # 证明力 0-1
    strength_factors: List[str] = field(default_factory=list)  # 影响证明力的因素
    
    # 关联分析
    related_facts: List[str] = field(default_factory=list)  # 关联的事实
    conflicts_with: List[str] = field(default_factory=list)  # 与哪些证据矛盾
    
    # 补充建议
    enhancement_suggestions: List[str] = field(default_factory=list)  # 增强建议


@dataclass
class EvidenceGap:
    """证据缺口"""
    gap_id: str
    missing_type: str               # 缺失的证据类型
    proves_fact: str               # 影响证明的事实
    
    severity: EvidenceGapSeverity
    importance: str                 # 高/中/低
    
    # 影响分析
    affects_claims: List[str] = field(default_factory=list)  # 影响哪些诉请
    risk_description: str = ""      # 风险描述
    
    # 补强方案
    how_to_obtain: List[str] = field(default_factory=list)   # 如何获取
    alternative_evidence: List[str] = field(default_factory=list)  # 替代证据
    feasibility: str = "中"         # 可行性
    estimated_cost: str = ""        # 预估成本
    estimated_time: str = ""       # 预估时间
    
    # 引导问题
    discovery_questions: List[str] = field(default_factory=list)  # 发现缺口的问题
    verification_questions: List[str] = field(default_factory=list)  # 确认缺口的问题


@dataclass
class CaseDiagnosis:
    """案件诊断报告"""
    case_id: int
    
    # 整体评分
    overall_score: float = 0.0      # 0-100
    readiness_level: str = ""       # 准备度等级
    
    # 证据分析
    submitted_evidence: List[EvidenceItem] = field(default_factory=list)
    evidence_gaps: List[EvidenceGap] = field(default_factory=list)
    
    # 可视化数据
    evidence_type_distribution: Dict[str, int] = field(default_factory=dict)
    proof_chain_completeness: float = 0.0  # 证明链完整度
    
    # 诉讼建议
    critical_findings: List[str] = field(default_factory=list)  # 关键发现
    immediate_actions: List[str] = field(default_factory=list)  # 立即行动
    
    # 诊断时间
    diagnosed_at: datetime = field(default_factory=datetime.now)


@dataclass
class GuideQuestion:
    """引导性问题"""
    question_id: str
    category: str                   # 问题类别：基础/证据/金额/时间/对方
    
    question: str                   # 问题文本
    help_text: str = ""             # 帮助说明
    
    # 选项配置
    options: Optional[List[Dict]] = None  # 选项列表
    input_type: str = "choice"      # choice/text/number/date
    
    # 关联性
    triggers: List[str] = field(default_factory=list)  # 触发哪些后续问题
    required_for: List[str] = field(default_factory=list)  # 影响哪些分析
    
    # 回答后的行动
    next_questions: List[str] = field(default_factory=list)  # 回答后触发的问题
    
    answered: bool = False
    answer: Any = None


class EvidenceNavigator:
    """
    证据导航系统 - 主动引导用户补全证据
    
    像资深律师一样：
    1. 先看有什么 → 现有证据分析
    2. 再看缺什么 → 缺口识别
    3. 最后告诉怎么补 → 行动建议
    """
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
        
        # 案件诊断缓存
        self.diagnosis_cache: Dict[int, CaseDiagnosis] = {}
        
        # 问答历史
        self.question_history: Dict[int, List[GuideQuestion]] = {}
    
    # ==================== 核心功能 ====================
    
    def diagnose_case(self, case_info: Dict, evidence_list: List[Dict]) -> CaseDiagnosis:
        """
        诊断案件 - 像体检一样全面检查
        """
        diagnosis = CaseDiagnosis(case_id=case_info.get("id", 0))
        
        # 1. 分析现有证据
        diagnosis.submitted_evidence = self._analyze_evidence(evidence_list)
        
        # 2. 识别证据缺口
        diagnosis.evidence_gaps = self._identify_gaps(
            case_info, 
            diagnosis.submitted_evidence
        )
        
        # 3. 计算评分
        diagnosis.overall_score = self._calculate_readiness_score(
            diagnosis.submitted_evidence,
            diagnosis.evidence_gaps
        )
        
        # 4. 生成可视化数据
        diagnosis.proof_chain_completeness = self._calculate_proof_chain(
            diagnosis.submitted_evidence,
            diagnosis.evidence_gaps
        )
        
        diagnosis.evidence_type_distribution = self._get_type_distribution(
            diagnosis.submitted_evidence
        )
        
        # 5. 关键发现
        diagnosis.critical_findings = self._generate_critical_findings(
            diagnosis.submitted_evidence,
            diagnosis.evidence_gaps
        )
        
        # 6. 立即行动
        diagnosis.immediate_actions = self._generate_actions(
            diagnosis.evidence_gaps
        )
        
        return diagnosis
    
    def _analyze_evidence(self, evidence_list: List[Dict]) -> List[EvidenceItem]:
        """分析已有证据"""
        items = []
        
        for i, ev in enumerate(evidence_list):
            item = EvidenceItem(
                id=ev.get("id", f"ev_{i}"),
                name=ev.get("name", f"证据{i+1}"),
                description=ev.get("description", ""),
                evidence_type=ev.get("type", "未知"),
                custody=ev.get("custody", "原告"),
                status=ev.get("status", "已提交"),
                proves=ev.get("proves", []),
                strength=ev.get("strength", 0.5)
            )
            items.append(item)
        
        return items
    
    def _identify_gaps(
        self, 
        case_info: Dict, 
        submitted_evidence: List[EvidenceItem]
    ) -> List[EvidenceGap]:
        """识别证据缺口 - 这是核心智能"""
        
        # 基于案件类型和诉请识别缺口
        case_type = case_info.get("case_type", "")
        claims = case_info.get("claims", [])
        
        gaps = []
        gap_counter = 1
        
        # 根据证据类型分布判断缺口
        type_counts = self._get_type_distribution(submitted_evidence)
        
        # 1. 检查基础证据类型是否齐全
        required_types = self._get_required_types(case_type)
        
        for req_type in required_types:
            if req_type not in type_counts or type_counts[req_type] == 0:
                gap = self._create_gap_for_missing_type(
                    req_type, case_type, claims, gap_counter
                )
                gaps.append(gap)
                gap_counter += 1
        
        # 2. 检查诉请对应证据
        for claim in claims:
            has_support = any(
                claim in ev.proves 
                for ev in submitted_evidence
            )
            if not has_support:
                gap = self._create_gap_for_claim(claim, gap_counter)
                gaps.append(gap)
                gap_counter += 1
        
        # 3. 检查关键事实证据
        key_facts = self._identify_key_facts(case_info)
        for fact in key_facts:
            has_support = any(
                fact in ev.proves 
                for ev in submitted_evidence
            )
            if not has_support:
                gap = self._create_gap_for_fact(fact, gap_counter)
                gaps.append(gap)
                gap_counter += 1
        
        return gaps
    
    def _get_required_types(self, case_type: str) -> List[str]:
        """根据案件类型获取必需证据类型"""
        type_requirements = {
            "合同纠纷": ["书面证据", "转账凭证", "沟通记录"],
            "侵权纠纷": ["侵权证据", "损害证据", "因果关系证据"],
            "劳动纠纷": ["劳动合同", "工资证据", "解除证据"],
            "债务纠纷": ["借条凭证", "转账记录", "催款证据"]
        }
        return type_requirements.get(case_type, ["书面证据", "转账凭证"])
    
    def _create_gap_for_missing_type(
        self, 
        missing_type: str, 
        case_type: str,
        claims: List[str],
        gap_id: int
    ) -> EvidenceGap:
        """为缺失的证据类型创建缺口"""
        
        # 获取补强建议
        obtaining_tips = self._get_obtaining_tips(missing_type)
        
        gap = EvidenceGap(
            gap_id=f"gap_{gap_id}",
            missing_type=missing_type,
            proves_fact=self._get_proof_purpose(missing_type),
            severity=self._assess_severity(missing_type, case_type),
            importance="高" if self._is_critical_type(missing_type) else "中",
            affects_claims=claims,
            risk_description=f"缺少{missing_type}可能导致关键事实无法证明",
            how_to_obtain=obtaining_tips["how"],
            alternative_evidence=obtaining_tips["alternatives"],
            feasibility=obtaining_tips["feasibility"],
            discovery_questions=self._get_discovery_questions(missing_type)
        )
        
        return gap
    
    def _create_gap_for_claim(self, claim: str, gap_id: int) -> EvidenceGap:
        """为诉请创建缺口"""
        return EvidenceGap(
            gap_id=f"gap_{gap_id}",
            missing_type=f"支持'{claim}'的证据",
            proves_fact=claim,
            severity=EvidenceGapSeverity.CRITICAL,
            importance="高",
            affects_claims=[claim],
            risk_description=f"诉请'{claim}'缺乏证据支持",
            how_to_obtain=[f"收集能证明{claim}的直接证据"],
            verification_questions=[f"有没有证据能直接证明{claim}？"]
        )
    
    def _create_gap_for_fact(self, fact: str, gap_id: int) -> EvidenceGap:
        """为关键事实创建缺口"""
        return EvidenceGap(
            gap_id=f"gap_{gap_id}",
            missing_type=f"证明'{fact}'的证据",
            proves_fact=fact,
            severity=EvidenceGapSeverity.IMPORTANT,
            importance="中",
            how_to_obtain=[f"寻找了解'{fact}'的知情人"],
            verification_questions=[f"谁可以证明{fact}？"]
        )
    
    def _get_obtaining_tips(self, evidence_type: str) -> Dict:
        """获取获取特定证据类型的建议"""
        tips_map = {
            "书面证据": {
                "how": ["联系合同相对方获取", "调取工商档案", "申请政府信息公开"],
                "alternatives": ["微信聊天记录", "录音证据", "邮件往来"],
                "feasibility": "中高"
            },
            "转账凭证": {
                "how": ["前往银行打印流水", "打印支付宝/微信账单", "申请法院调查令"],
                "alternatives": ["截图+公证", "对方自认"],
                "feasibility": "高"
            },
            "侵权证据": {
                "how": ["现场公证", "鉴定机构鉴定", "申请法院勘验"],
                "alternatives": ["录音录像", "证人证言"],
                "feasibility": "中高"
            },
            "沟通记录": {
                "how": ["打印微信/QQ记录", "导出邮件", "公证通话录音"],
                "alternatives": ["书面确认函", "对方承认函"],
                "feasibility": "高"
            }
        }
        return tips_map.get(evidence_type, {
            "how": ["寻找了解情况的知情人"],
            "alternatives": ["收集间接证据形成证据链"],
            "feasibility": "中"
        })
    
    def _get_proof_purpose(self, evidence_type: str) -> str:
        """获取证据类型的证明目的"""
        purposes = {
            "书面证据": "证明合同关系及具体约定",
            "转账凭证": "证明款项支付情况",
            "沟通记录": "证明双方沟通过程和事实确认",
            "侵权证据": "证明侵权行为的存在",
            "损害证据": "证明损失的具体金额和范围",
            "劳动合同": "证明劳动关系和权利义务",
            "工资证据": "证明工资标准和发放情况"
        }
        return purposes.get(evidence_type, f"证明案件相关事实")
    
    def _assess_severity(self, evidence_type: str, case_type: str) -> EvidenceGapSeverity:
        """评估缺失证据的严重程度"""
        critical_types = ["书面证据", "转账凭证", "侵权证据"]
        if evidence_type in critical_types:
            return EvidenceGapSeverity.CRITICAL
        return EvidenceGapSeverity.IMPORTANT
    
    def _is_critical_type(self, evidence_type: str) -> bool:
        """判断是否为关键证据类型"""
        return evidence_type in ["书面证据", "转账凭证", "侵权证据", "损害证据"]
    
    def _identify_key_facts(self, case_info: Dict) -> List[str]:
        """识别关键待证事实"""
        facts = []
        
        if case_info.get("description"):
            facts.append("案件基本事实")
        if case_info.get("cause"):
            facts.append(f"案由：{case_info['cause']}")
        if case_info.get("claim_amount"):
            facts.append(f"金额：{case_info['claim_amount']}")
        
        return facts
    
    def _calculate_readiness_score(
        self, 
        evidence: List[EvidenceItem],
        gaps: List[EvidenceGap]
    ) -> float:
        """计算案件准备度评分"""
        if not evidence:
            return 20.0  # 无证据
        
        # 基础分
        base_score = len(evidence) * 5
        
        # 证据强度分
        strength_score = sum(e.strength for e in evidence) * 20
        
        # 缺口扣分
        gap_penalty = sum(
            15 if g.severity == EvidenceGapSeverity.CRITICAL else 8
            for g in gaps
        )
        
        score = base_score + strength_score - gap_penalty
        return min(100, max(0, score))
    
    def _calculate_proof_chain(
        self,
        evidence: List[EvidenceItem],
        gaps: List[EvidenceGap]
    ) -> float:
        """计算证明链完整度"""
        if not evidence:
            return 0.0
        
        # 统计已证明的事实
        proven_facts = set()
        for e in evidence:
            proven_facts.update(e.proves)
        
        # 统计需要证明的事实
        required_facts = set()
        for g in gaps:
            required_facts.add(g.proves_fact)
        
        # 计算完整度
        total = len(proven_facts) + len(required_facts)
        if total == 0:
            return 0.0
        
        return len(proven_facts) / total
    
    def _get_type_distribution(self, evidence: List[EvidenceItem]) -> Dict[str, int]:
        """获取证据类型分布"""
        dist = {}
        for e in evidence:
            t = e.evidence_type
            dist[t] = dist.get(t, 0) + 1
        return dist
    
    def _generate_critical_findings(
        self,
        evidence: List[EvidenceItem],
        gaps: List[EvidenceGap]
    ) -> List[str]:
        """生成关键发现"""
        findings = []
        
        # 分析证据强度
        weak_evidence = [e for e in evidence if e.strength < 0.5]
        if weak_evidence:
            findings.append(f"⚠️ 有 {len(weak_evidence)} 份证据证明力较弱，需要补强")
        
        # 分析关键缺口
        critical_gaps = [g for g in gaps if g.severity == EvidenceGapSeverity.CRITICAL]
        if critical_gaps:
            findings.append(f"🔴 存在 {len(critical_gaps)} 个致命证据缺口，必须补齐")
        
        # 分析证据类型
        type_counts = self._get_type_distribution(evidence)
        if "书面证据" not in type_counts:
            findings.append("🔴 缺少书面证据，合同关系难以证明")
        
        return findings
    
    def _generate_actions(self, gaps: List[EvidenceGap]) -> List[str]:
        """生成立即行动建议"""
        actions = []
        
        # 按严重程度排序
        sorted_gaps = sorted(
            gaps, 
            key=lambda x: (
                0 if x.severity == EvidenceGapSeverity.CRITICAL else 1,
                0 if x.importance == "高" else 1
            )
        )
        
        for i, gap in enumerate(sorted_gaps[:3], 1):
            if gap.severity == EvidenceGapSeverity.CRITICAL:
                actions.append(f"{i}. 【紧急】{gap.missing_type}：{gap.how_to_obtain[0] if gap.how_to_obtain else '请尽快收集'}")
            else:
                actions.append(f"{i}. {gap.missing_type}：{gap.how_to_obtain[0] if gap.how_to_obtain else '建议收集'}")
        
        return actions
    
    # ==================== 引导问答系统 ====================
    
    def generate_guidance_questions(
        self, 
        case_info: Dict, 
        diagnosis: CaseDiagnosis
    ) -> List[GuideQuestion]:
        """
        生成引导性问题 - 像律师问诊一样
        """
        questions = []
        
        # 1. 基础事实问题
        if not case_info.get("description"):
            questions.append(GuideQuestion(
                question_id="basic_1",
                category="基础",
                question="请简要描述发生了什么事件？比如：什么时间、什么地点、发生了什么？",
                help_text="尽量详细描述事件经过，包括具体日期、金额等关键信息",
                input_type="text",
                triggers=["事件类型", "涉及金额"]
            ))
        
        # 2. 金额问题
        if not case_info.get("claim_amount") and diagnosis.overall_score < 60:
            questions.append(GuideQuestion(
                question_id="amount_1",
                category="金额",
                question="涉及的具体金额是多少？（包括已付款项、损失金额、期望赔偿等）",
                help_text="如果有多种金额，可以分段说明",
                input_type="number",
                triggers=["金额证明"]
            ))
        
        # 3. 证据缺口相关问题
        critical_gaps = [
            g for g in diagnosis.evidence_gaps 
            if g.severity == EvidenceGapSeverity.CRITICAL
        ]
        
        for gap in critical_gaps[:2]:  # 最多问2个关键问题
            q = self._create_gap_question(gap)
            if q:
                questions.append(q)
        
        # 4. 对方情况问题
        questions.append(GuideQuestion(
            question_id="opponent_1",
            category="对方",
            question="对方是否有承认过相关事实？（如在微信、邮件中确认）",
            help_text="对方的承认可以作为有力证据",
            options=[
                {"value": "yes", "label": "有，对方承认过", "follow_up": "opponent_yes"},
                {"value": "no", "label": "没有明确承认", "follow_up": "opponent_no"},
                {"value": "unknown", "label": "不确定", "follow_up": "opponent_unknown"}
            ],
            input_type="choice"
        ))
        
        # 5. 知情人的问题
        questions.append(GuideQuestion(
            question_id="witness_1",
            category="证人",
            question="有没有其他人了解这个事件？（如同事、朋友、目击者等）",
            help_text="知情人可以作证或提供线索",
            options=[
                {"value": "yes", "label": "有，请说明"},
                {"value": "maybe", "label": "可能有，但不确定"},
                {"value": "no", "label": "没有"}
            ],
            input_type="choice"
        ))
        
        return questions
    
    def _create_gap_question(self, gap: EvidenceGap) -> Optional[GuideQuestion]:
        """为证据缺口创建引导性问题"""
        
        if gap.missing_type == "书面证据":
            return GuideQuestion(
                question_id=f"gap_{gap.gap_id}",
                category="证据",
                question="有没有签订过什么合同、协议、或者书面约定？",
                help_text="可以是电子合同、纸质合同、微信/邮件中的约定",
                options=[
                    {"value": "signed", "label": "有签订过"},
                    {"value": "partial", "label": "部分有，部分口头"},
                    {"value": "verbal", "label": "都是口头约定"},
                    {"value": "none", "label": "没有书面约定"}
                ],
                input_type="choice"
            )
        
        elif gap.missing_type == "转账凭证":
            return GuideQuestion(
                question_id=f"gap_{gap.gap_id}",
                category="证据",
                question="付款是通过什么方式进行的？银行转账、微信、支付宝还是现金？",
                help_text="转账和电子支付都有记录可查",
                options=[
                    {"value": "bank", "label": "银行转账"},
                    {"value": "alipay", "label": "支付宝"},
                    {"value": "wechat", "label": "微信转账"},
                    {"value": "cash", "label": "现金"},
                    {"value": "mixed", "label": "多种方式"}
                ],
                input_type="choice"
            )
        
        elif gap.missing_type == "沟通记录":
            return GuideQuestion(
                question_id=f"gap_{gap.gap_id}",
                category="证据",
                question="双方沟通过程有没有保留聊天记录？包括微信、短信、邮件等",
                help_text="沟通记录可以证明双方的意思表示和事实确认",
                options=[
                    {"value": "yes_wechat", "label": "有微信聊天记录"},
                    {"value": "yes_email", "label": "有邮件往来"},
                    {"value": "yes_sms", "label": "有短信"},
                    {"value": "yes_call", "label": "有通话录音"},
                    {"value": "no", "label": "没有保留"}
                ],
                input_type="choice"
            )
        
        return None
    
    def _get_discovery_questions(self, evidence_type: str) -> List[str]:
        """获取发现特定证据的引导问题"""
        questions = {
            "书面证据": [
                "有没有签过合同或协议？",
                "有没有书面确认函或对账单？"
            ],
            "转账凭证": [
                "付款是怎么付的？",
                "有没有银行流水或支付记录？"
            ],
            "沟通记录": [
                "有没有保留聊天记录？",
                "有没有通话录音？"
            ]
        }
        return questions.get(evidence_type, ["有没有相关的证据？"])
    
    # ==================== 可视化数据 ====================
    
    def get_evidence_graph_data(self, diagnosis: CaseDiagnosis) -> Dict:
        """
        获取证据图谱可视化数据
        """
        # 节点数据
        nodes = []
        
        # 证据节点
        for ev in diagnosis.submitted_evidence:
            nodes.append({
                "id": ev.id,
                "name": ev.name,
                "type": "evidence",
                "category": ev.evidence_type,
                "status": ev.status,
                "strength": ev.strength,
                "color": self._get_strength_color(ev.strength)
            })
        
        # 缺口节点
        for gap in diagnosis.evidence_gaps:
            nodes.append({
                "id": gap.gap_id,
                "name": f"缺少: {gap.missing_type}",
                "type": "gap",
                "severity": gap.severity.value,
                "color": self._get_severity_color(gap.severity)
            })
        
        # 边数据（关系）
        edges = []
        
        # 证据到事实的边
        for ev in diagnosis.submitted_evidence:
            for fact in ev.proves:
                edges.append({
                    "source": ev.id,
                    "target": fact,
                    "type": "proves"
                })
        
        # 缺口到诉请的边
        for gap in diagnosis.evidence_gaps:
            for claim in gap.affects_claims:
                edges.append({
                    "source": gap.gap_id,
                    "target": claim,
                    "type": "affects"
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_evidence": len(diagnosis.submitted_evidence),
                "total_gaps": len(diagnosis.evidence_gaps),
                "critical_gaps": len([g for g in diagnosis.evidence_gaps if g.severity == EvidenceGapSeverity.CRITICAL]),
                "proof_completeness": diagnosis.proof_chain_completeness
            }
        }
    
    def _get_strength_color(self, strength: float) -> str:
        """根据证据强度返回颜色"""
        if strength >= 0.8:
            return "#22c55e"  # 绿色
        elif strength >= 0.5:
            return "#f59e0b"  # 黄色
        else:
            return "#ef4444"  # 红色
    
    def _get_severity_color(self, severity: EvidenceGapSeverity) -> str:
        """根据严重程度返回颜色"""
        colors = {
            EvidenceGapSeverity.CRITICAL: "#ef4444",   # 红色
            EvidenceGapSeverity.IMPORTANT: "#f59e0b",  # 黄色
            EvidenceGapSeverity.OPTIONAL: "#22c55e"     # 绿色
        }
        return colors.get(severity, "#94a3b8")
    
    # ==================== 交互式补充 ====================
    
    def process_answer(
        self, 
        case_id: int,
        question_id: str, 
        answer: Any,
        current_diagnosis: CaseDiagnosis
    ) -> Dict:
        """
        处理用户回答，更新诊断和建议
        """
        result = {
            "question_id": question_id,
            "answer_received": answer,
            "diagnosis_updated": False,
            "new_gaps_identified": [],
            "gaps_resolved": [],
            "new_questions": [],
            "suggestions": []
        }
        
        # 根据回答分析是否解决了某些缺口
        if "yes" in str(answer).lower() or "有" in str(answer):
            # 可能有新证据
            result["suggestions"].append("很好！请尽快上传相关证据")
        
        elif "no" in str(answer).lower() or "没有" in str(answer):
            # 确认缺口存在，给出替代方案
            result["suggestions"].append("没有直接证据也没关系，可以考虑以下替代方案：")
            result["suggestions"].extend([
                "1. 寻找间接证据形成证据链",
                "2. 申请法院调查取证",
                "3. 申请证人出庭作证"
            ])
        
        # 检查是否需要进一步追问
        if question_id.startswith("gap_"):
            gap_id = question_id
            # 可能需要提供获取建议
            gap = next((g for g in current_diagnosis.evidence_gaps if g.gap_id == gap_id), None)
            if gap and gap.alternative_evidence:
                result["suggestions"].append("替代证据建议：" + "、".join(gap.alternative_evidence))
        
        return result


# 全局实例
evidence_navigator = EvidenceNavigator()
