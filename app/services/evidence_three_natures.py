"""
证据三性深度分析服务（biz-5）
对证据的真实性、合法性、关联性进行结构化深度分析

参考法规：
- 《民事诉讼法》第66条（证据种类）
- 《最高人民法院关于民事诉讼证据的若干规定》(2019修订)
- 《最高人民法院关于适用〈中华人民共和国民事诉讼法〉的解释》第90-108条
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class EvidenceAuthenticity(str, Enum):
    """真实性评估"""
    CONFIRMED = "confirmed"           # 已确认真实
    LIKELY_AUTHENTIC = "likely_authentic"  # 基本真实
    UNCERTAIN = "uncertain"            # 无法确定
    LIKELY_FORGED = "likely_forged"    # 可能伪造
    FORGED = "forged"                 # 确认伪造


class EvidenceLegality(str, Enum):
    """合法性评估"""
    VALID = "valid"                   # 完全合法
    MINOR_DEFECT = "minor_defect"     # 轻微瑕疵（可补正）
    SERIOUS_DEFECT = "serious_defect" # 重大瑕疵（影响效力）
    ILLEGAL = "illegal"               # 违法取得（应排除）
    UNABLE_TO_DETERMINE = "unable"   # 无法判断


class EvidenceRelevance(str, Enum):
    """关联性评估"""
    DIRECT_RELEVANT = "direct"         # 直接相关
    INDIRECT_RELEVANT = "indirect"     # 间接相关
    MARGINALLY_RELEVANT = "marginal"  # 边缘相关
    NOT_RELEVANT = "not_relevant"     # 不相关
    UNCLEAR = "unclear"               # 关联性不明


@dataclass
class ThreeNaturesAnalysis:
    """
    证据三性分析结果
    
    真实性（Authenticity）：证据是否为真的，有无伪造、变造
    合法性（Legality）：证据的取得方式是否合法，是否有瑕疵
    关联性（Relevance）：证据与待证事实之间的关系
    """
    evidence_id: str
    evidence_name: str
    case_id: int
    
    # 真实性分析
    authenticity: EvidenceAuthenticity
    authenticity_score: float  # 0-100
    authenticity_analysis: str
    
    # 合法性分析
    legality: EvidenceLegality
    legality_score: float  # 0-100
    legality_analysis: str
    legality_basis: str  # 法律依据
    
    # 关联性分析
    relevance: EvidenceRelevance
    relevance_score: float  # 0-100
    relevance_analysis: str

    authenticity_factors: List[Dict] = field(default_factory=list)
    # 真实性判断因素
    authenticity_factors_detail: Dict = field(default_factory=dict)
    defect_type: Optional[str] = None  # 瑕疵类型
    defect_remedy: Optional[str] = None  # 补正方式
    proves_facts: List[str] = field(default_factory=list)  # 能证明的事实
    disputed_facts: List[str] = field(default_factory=list)  # 有争议的事实
    
    # 综合评估
    overall_score: float = 0.0  # 综合证明力 0-100
    overall_assessment: str = ""
    key_strengths: List[str] = field(default_factory=list)
    key_weaknesses: List[str] = field(default_factory=list)
    
    # 风险提示
    challenges: List[Dict] = field(default_factory=list)  # 对方可能的质疑
    challenge_responses: List[Dict] = field(default_factory=list)  # 应对策略
    reinforcement_suggestions: List[str] = field(default_factory=list)  # 补强建议
    
    # 元数据
    analyzed_at: datetime = field(default_factory=datetime.now)
    analysis_version: str = "2.0"
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        result = asdict(self)
        # 枚举值转字符串
        result['authenticity'] = self.authenticity.value
        result['legality'] = self.legality.value
        result['relevance'] = self.relevance.value
        return result


class EvidenceThreeNaturesService:
    """
    证据三性深度分析服务
    
    提供：
    1. 结构化三性分析（真实性/合法性/关联性）
    2. AI辅助深度分析
    3. 补强建议生成
    4. 对方质疑预判与应对
    """
    
    # 真实性分析判断规则
    AUTHENTICITY_RULES = {
        "document": {
            "positive_factors": [
                "有原始签章/签名",
                "有第三方认证（如公证）",
                "与其他可靠证据相互印证",
                "形式符合行业惯例",
                "内容逻辑自洽，无矛盾"
            ],
            "negative_factors": [
                "无法提供原件",
                "存在明显涂改痕迹",
                "内容前后矛盾",
                "与其他证据相互矛盾",
                "形式不符合惯例",
                "缺乏必要签章",
                "纸张/墨迹/打印方式与声称的时间不符"
            ],
            "legal_basis": [
                "《民事诉讼法》第66条：证据必须查证属实，才能作为认定事实的根据",
                "《民诉证据规定》第87条：审判人员对单一证据可以从下列方面进行审核认定：（一）证据是否为原件..."
            ]
        },
        "audio_video": {
            "positive_factors": [
                "原始载体完整",
                "未经剪辑/编辑",
                "有鉴定意见支持",
                "录音录像环境清晰",
                "与案件事实存在逻辑联系"
            ],
            "negative_factors": [
                "无法确认原始载体",
                "存在剪辑/合成嫌疑",
                "画质/音质极差无法辨识",
                "偷拍偷录（侵犯隐私）"
            ],
            "legal_basis": [
                "《民诉证据规定》第90条：以档案或者材料、证物识别或者书面陈述形式存在，或者以当事人或者第三人视听资料传输形式存在..."
            ]
        },
        "testimony": {
            "positive_factors": [
                "证人出庭作证",
                "与案件其他证据印证",
                "内容具体明确",
                "证人了解案件事实",
                "证言稳定一致"
            ],
            "negative_factors": [
                "证人未出庭",
                "证言模糊不确定",
                "与案件其他证据矛盾",
                "存在利害关系",
                "传闻证据（未亲身经历）"
            ],
            "legal_basis": [
                "《民事诉讼法》第73条：经人民法院通知，证人应当出庭作证",
                "《民诉证据规定》第97条：证人作证应当使用文明语言"
            ]
        },
        "expert": {
            "positive_factors": [
                "有资质的鉴定机构出具",
                "鉴定程序合法合规",
                "鉴定结论依据充分",
                "鉴定人出庭接受质询",
                "与其他证据相互印证"
            ],
            "negative_factors": [
                "鉴定机构无资质",
                "鉴定程序违法",
                "鉴定依据不足",
                "鉴定结论存在矛盾",
                "对方提出有效质疑"
            ],
            "legal_basis": [
                "《民事诉讼法》第79条：当事人可以就查明事实的专门性问题向人民法院申请鉴定",
                "《民诉证据规定》第36条：对鉴定意见的审查"
            ]
        }
    }
    
    # 合法性判断规则
    LEGALITY_RULES = {
        "defect_types": {
            "minor": {
                "examples": [
                    "证据形式略有瑕疵（如复印件未注明与原件一致）",
                    "签名略有模糊",
                    "证明文件略有迟延"
                ],
                "remedy": "补充说明或提供原件即可补正"
            },
            "serious": {
                "examples": [
                    "未经公证的域外证据",
                    "未按期提交的证据（有正当理由）",
                    "证据来源不明"
                ],
                "remedy": "需要额外证明材料或说明"
            },
            "illegal": {
                "examples": [
                    "通过侵犯隐私权方式取得的录音",
                    "通过非法侵入住宅取得的证据",
                    "通过盗窃方式取得的文件",
                    "严重侵害他人合法权益取得的证据"
                ],
                "remedy": "原则上应予排除，但严重侵害他人合法权益的情形除外"
            }
        }
    }
    
    # 关联性判断
    RELEVANCE_RULES = {
        "direct_facts": [
            "直接证明争议的合同关系存在",
            "直接证明违约行为的发生",
            "直接证明损害结果",
            "直接证明因果关系"
        ],
        "indirect_facts": [
            "间接证明当事人之间的关系",
            "间接证明经济状况",
            "间接证明交易习惯",
            "间接补强直接证据"
        ],
        "not_relevant": [
            "与案件争议焦点完全无关",
            "只能证明一般性事实",
            "只能证明当事人身份信息",
            "属于法院已知的事实"
        ]
    }
    
    def __init__(self):
        self.authenticity_rules = self.AUTHENTICITY_RULES
        self.legality_rules = self.LEGALITY_RULES
        self.relevance_rules = self.RELEVANCE_RULES
    
    def analyze_three_natures(self,
                             evidence_data: Dict,
                             case_facts: Optional[str] = None,
                             llm_analysis: bool = False) -> ThreeNaturesAnalysis:
        """
        综合分析证据三性
        
        Args:
            evidence_data: 证据数据，至少包含 id, name, type, content
            case_facts: 案件事实描述（用于关联性分析）
            llm_analysis: 是否使用LLM进行深度分析
            
        Returns:
            ThreeNaturesAnalysis 结构化分析结果
        """
        evidence_id = evidence_data.get("id", "")
        evidence_name = evidence_data.get("name", evidence_data.get("original_filename", ""))
        case_id = evidence_data.get("case_id", 0)
        evidence_type = evidence_data.get("evidence_type", "DOCUMENT")
        
        # 1. 真实性分析
        auth_result = self._analyze_authenticity(evidence_data)
        
        # 2. 合法性分析
        leg_result = self._analyze_legality(evidence_data)
        
        # 3. 关联性分析
        rel_result = self._analyze_relevance(evidence_data, case_facts)
        
        # 4. 综合评估
        overall_score, overall_text = self._calculate_overall_score(
            auth_result, leg_result, rel_result
        )
        
        # 5. 风险提示
        challenges = self._generate_challenges(evidence_data, auth_result, leg_result, rel_result)
        challenge_responses = self._generate_responses(challenges, evidence_data)
        reinforcement = self._generate_reinforcement(
            evidence_data, auth_result, leg_result, rel_result
        )
        
        return ThreeNaturesAnalysis(
            evidence_id=evidence_id,
            evidence_name=evidence_name,
            case_id=case_id,
            authenticity=auth_result["status"],
            authenticity_score=auth_result["score"],
            authenticity_analysis=auth_result["analysis"],
            authenticity_factors=auth_result.get("factors", []),
            authenticity_factors_detail=auth_result.get("detail", {}),
            legality=leg_result["status"],
            legality_score=leg_result["score"],
            legality_analysis=leg_result["analysis"],
            legality_basis=leg_result.get("basis", ""),
            defect_type=leg_result.get("defect_type"),
            defect_remedy=leg_result.get("remedy"),
            relevance=rel_result["status"],
            relevance_score=rel_result["score"],
            relevance_analysis=rel_result["analysis"],
            proves_facts=rel_result.get("proves_facts", []),
            disputed_facts=rel_result.get("disputed_facts", []),
            overall_score=overall_score,
            overall_assessment=overall_text,
            key_strengths=self._extract_strengths(auth_result, leg_result, rel_result),
            key_weaknesses=self._extract_weaknesses(auth_result, leg_result, rel_result),
            challenges=challenges,
            challenge_responses=challenge_responses,
            reinforcement_suggestions=reinforcement
        )
    
    def _analyze_authenticity(self, evidence: Dict) -> Dict:
        """
        分析证据真实性
        
        判断因素：
        1. 是否有原件
        2. 是否经过鉴定
        3. 是否公证
        4. 来源是否清晰
        5. 内容是否自洽
        6. 与其他证据是否矛盾
        """
        result = {
            "status": EvidenceAuthenticity.UNCERTAIN,
            "score": 50.0,
            "analysis": "",
            "factors": [],
            "detail": {}
        }
        
        positive = []
        negative = []
        evidence_type = evidence.get("evidence_type", "DOCUMENT")
        
        # 获取对应类型的判断规则
        type_key = self._map_evidence_type_to_rule(evidence_type)
        rules = self.authenticity_rules.get(type_key, self.authenticity_rules["document"])
        
        # 检查各种因素
        if evidence.get("file_path") and not evidence.get("is_copy"):
            positive.append("有原始文件载体")
        
        if evidence.get("credibility_score", 0) >= 80:
            positive.append(f"系统证明力参考较高({evidence['credibility_score']})")
        elif evidence.get("credibility_score", 0) <= 30:
            negative.append(f"系统证明力参考较低({evidence['credibility_score']})")
        
        # 公证证据 - 法律应用：检查所有内容字段
        raw_content = evidence.get("raw_content", "")
        extracted_content = evidence.get("extracted_content", "")
        summary = evidence.get("summary", "")
        all_content = raw_content + extracted_content + summary
        if "公证" in summary or "公证" in raw_content or "公证" in extracted_content:
            positive.append("涉及公证程序")
        
        # 形式真实性
        if evidence.get("authenticity_score", 0) > 0:
            if evidence["authenticity_score"] >= 80:
                positive.append(f"形式真实性评分高({evidence['authenticity_score']})")
            elif evidence["authenticity_score"] <= 30:
                negative.append(f"形式真实性评分低({evidence['authenticity_score']})")
        
        # 来源可靠性
        source_party = evidence.get("source_party", "")
        if source_party == "己方":
            positive.append("己方提供的证据，来源可靠")
        elif source_party == "法院":
            positive.append("法院调取的证据，来源权威")
        elif source_party == "对方":
            negative.append("对方提供，需警惕真实性风险")
        
        # 内容一致性
        if evidence.get("consistency_score", 0) > 0:
            if evidence["consistency_score"] >= 80:
                positive.append("内容一致性高")
            elif evidence["consistency_score"] <= 30:
                negative.append("内容一致性低，可能存在矛盾")
        
        # 综合判断
        score = 50.0
        for p in positive:
            score += 5
        for n in negative:
            score -= 8
        
        score = max(0, min(100, score))
        
        if score >= 80:
            status = EvidenceAuthenticity.CONFIRMED if score >= 90 else EvidenceAuthenticity.LIKELY_AUTHENTIC
        elif score >= 60:
            status = EvidenceAuthenticity.LIKELY_AUTHENTIC
        elif score >= 40:
            status = EvidenceAuthenticity.UNCERTAIN
        else:
            status = EvidenceAuthenticity.LIKELY_FORGED
        
        # 生成分析文本
        analysis_parts = []
        if positive:
            analysis_parts.append(f"【支持真实的因素】：{'；'.join(positive)}")
        if negative:
            analysis_parts.append(f"【质疑真实的因素】：{'；'.join(negative)}")
        if not analysis_parts:
            analysis_parts.append("无法确定真实性，需要进一步核实")
        
        result.update({
            "status": status,
            "score": score,
            "analysis": "；".join(analysis_parts),
            "factors": [{"type": "positive", "items": positive}, {"type": "negative", "items": negative}],
            "detail": {"positive": positive, "negative": negative}
        })
        
        return result
    
    def _analyze_legality(self, evidence: Dict) -> Dict:
        """
        分析证据合法性
        
        判断因素：
        1. 取得方式是否合法
        2. 是否严重侵害他人权益
        3. 是否经过法定程序
        4. 形式是否符合法定要求
        """
        result = {
            "status": EvidenceLegality.VALID,
            "score": 100.0,
            "analysis": "",
            "basis": "",
            "defect_type": None,
            "remedy": None
        }
        
        defects = []
        legal_basis = []
        
        # 检查取得方式
        collection_method = evidence.get("collection_method", "正常")
        if "偷拍" in collection_method or "偷录" in collection_method:
            defects.append({
                "type": "serious",
                "description": "偷拍偷录可能侵犯隐私权",
                "detail": "根据《民法典》第1033条，除非法律另有规定，否则不得处理他人的私密信息"
            })
        
        # 检查形式瑕疵
        if not evidence.get("has_original") and not evidence.get("notarized"):
            defects.append({
                "type": "minor",
                "description": "无法提供原件，存在形式瑕疵",
                "detail": "根据《民诉证据规定》，无法提供原件的，应当说明理由"
            })
        
        # 检查是否公证
        if evidence.get("notarized"):
            legal_basis.append("已经过公证程序，证据取得合法有效")
        
        # 检查鉴定
        if evidence.get("has_expert_report"):
            legal_basis.append("有鉴定意见支持，符合法定证据形式")
        
        # 判断合法性等级
        has_serious = any(d["type"] == "serious" for d in defects)
        has_minor = any(d["type"] == "minor" for d in defects)
        
        if has_serious:
            status = EvidenceLegality.SERIOUS_DEFECT
            score = 20.0
            analysis = f"证据存在重大合法性瑕疵：{defects[0]['description']}"
            remedy = defects[0].get("detail", "")
        elif has_minor:
            status = EvidenceLegality.MINOR_DEFECT
            score = 70.0
            analysis = f"证据存在轻微形式瑕疵：{defects[0]['description']}，可补充说明或提供原件补正"
            remedy = "补充说明或提供原件"
        else:
            status = EvidenceLegality.VALID
            score = 100.0
            analysis = "证据取得方式合法，形式符合法定要求"
            remedy = None
        
        result.update({
            "status": status,
            "score": score,
            "analysis": analysis,
            "basis": "；".join(legal_basis) if legal_basis else "《民事诉讼法》第66条、第68条",
            "defect_type": defects[0]["type"] if defects else None,
            "remedy": remedy
        })
        
        return result
    
    def _analyze_relevance(self, evidence: Dict, case_facts: Optional[str] = None) -> Dict:
        """
        分析证据关联性
        
        判断因素：
        1. 与待证事实的直接/间接关系
        2. 能否证明案件的重要事实
        3. 是否属于争议焦点相关
        """
        result = {
            "status": EvidenceRelevance.INDIRECT_RELEVANT,
            "score": 60.0,
            "analysis": "",
            "proves_facts": [],
            "disputed_facts": []
        }
        
        evidence_type = evidence.get("evidence_type", "")
        # 法律应用：优先使用完整内容，不使用截断摘要
        raw_content = evidence.get("raw_content", "")
        extracted_content = evidence.get("extracted_content", "")
        summary = evidence.get("summary", "")
        # 合并所有内容以确保完整性
        content = raw_content or extracted_content or summary or ""
        proves_facts = evidence.get("proves_facts", [])
        
        # 基于证据类型和内容判断关联性
        if evidence_type == "CONTRACT":
            if any(kw in content for kw in ["合同", "协议", "约定", "双方"]):
                result["status"] = EvidenceRelevance.DIRECT_RELEVANT
                result["score"] = 90.0
                result["proves_facts"] = ["合同关系存在", "合同内容", "双方权利义务"]
                result["analysis"] = "合同类证据直接证明核心法律关系，属于关键证据"
            else:
                result["status"] = EvidenceRelevance.INDIRECT_RELEVANT
                result["score"] = 50.0
                result["analysis"] = "合同类证据，但内容关联性有待进一步核实"
        
        elif evidence_type == "PAYMENT":
            if any(kw in content for kw in ["支付", "转账", "汇款", "收据", "发票"]):
                result["status"] = EvidenceRelevance.DIRECT_RELEVANT
                result["score"] = 85.0
                result["proves_facts"] = ["付款事实", "履行行为"]
                result["analysis"] = "支付凭证直接证明合同履行情况"
        
        elif evidence_type == "CORRESPONDENCE":
            if any(kw in content for kw in ["催告", "通知", "确认", "往来"]):
                result["status"] = EvidenceRelevance.INDIRECT_RELEVANT
                result["score"] = 60.0
                result["proves_facts"] = ["双方沟通过程", "履行意愿"]
                result["analysis"] = "函件证据间接证明相关事实，需要结合其他证据"
        
        elif evidence_type == "TESTIMONY":
            result["status"] = EvidenceRelevance.INDIRECT_RELEVANT
            result["score"] = 50.0
            result["proves_facts"] = proves_facts if proves_facts else ["证人陈述事实"]
            result["analysis"] = "证人证言属于间接证据，需要其他证据补强"
        
        elif proves_facts:
            result["status"] = EvidenceRelevance.INDIRECT_RELEVANT
            result["score"] = 65.0
            result["proves_facts"] = proves_facts
            result["analysis"] = f"能证明多个案件事实"
        
        else:
            result["status"] = EvidenceRelevance.UNCLEAR
            result["score"] = 40.0
            result["analysis"] = "无法确定与案件的关联性"
        
        return result
    
    def _calculate_overall_score(self, auth: Dict, leg: Dict, rel: Dict) -> tuple:
        """计算综合证明力评分"""
        # 加权计算：真实性40% + 合法性30% + 关联性30%
        auth_score = auth.get("score", 50)
        leg_score = leg.get("score", 100)
        rel_score = rel.get("score", 50)
        
        overall = auth_score * 0.4 + leg_score * 0.3 + rel_score * 0.3
        
        if overall >= 85:
            text = "证据证明力强，建议作为核心证据使用"
        elif overall >= 70:
            text = "证据证明力较强，建议作为主要证据"
        elif overall >= 50:
            text = "证据证明力一般，需要补强"
        elif overall >= 30:
            text = "证据存在明显缺陷，需要谨慎使用"
        else:
            text = "证据证明力不足，建议放弃或寻求替代证据"
        
        return overall, text
    
    def _extract_strengths(self, auth: Dict, leg: Dict, rel: Dict) -> List[str]:
        strengths = []
        if auth.get("score", 0) >= 70:
            strengths.append("真实性有保障")
        if leg.get("score", 0) >= 80:
            strengths.append("取得方式合法")
        if rel.get("score", 0) >= 70:
            strengths.append("与案件事实高度关联")
        return strengths
    
    def _extract_weaknesses(self, auth: Dict, leg: Dict, rel: Dict) -> List[str]:
        weaknesses = []
        if auth.get("score", 0) < 50:
            weaknesses.append("真实性存疑")
        if leg.get("score", 0) < 70:
            defect = leg.get("defect_type", "瑕疵")
            weaknesses.append(f"合法性存在{defect}问题")
        if rel.get("score", 0) < 50:
            weaknesses.append("关联性不强")
        return weaknesses
    
    def _generate_challenges(self, evidence: Dict, auth: Dict, 
                             leg: Dict, rel: Dict) -> List[Dict]:
        """预判对方可能的质疑"""
        challenges = []
        
        # 真实性挑战
        if auth.get("score", 100) < 80:
            challenges.append({
                "type": "authenticity",
                "challenge": "该证据的真实性无法确认",
                "severity": "high" if auth.get("score", 0) < 50 else "medium",
                "suggested_response": "可申请鉴定或提供原件予以反驳"
            })
        
        # 合法性挑战
        if leg.get("score", 100) < 100:
            challenges.append({
                "type": "legality",
                "challenge": f"该证据存在{leg.get('defect_type', '')}问题",
                "severity": "high" if leg.get("score", 0) < 50 else "medium",
                "suggested_response": leg.get("remedy", "提供补充说明")
            })
        
        # 关联性挑战
        if rel.get("score", 100) < 60:
            challenges.append({
                "type": "relevance",
                "challenge": "该证据与案件争议焦点无关",
                "severity": "medium",
                "suggested_response": "说明证据与案件事实的关联性"
            })
        
        return challenges
    
    def _generate_responses(self, challenges: List[Dict], 
                           evidence: Dict) -> List[Dict]:
        """生成应对策略"""
        responses = []
        
        for challenge in challenges:
            if challenge["type"] == "authenticity":
                responses.append({
                    "challenge_type": "真实性质疑",
                    "response": "该证据系原件/有鉴定意见支持/有其他证据印证",
                    "legal_basis": "《民诉证据规定》第87条"
                })
            elif challenge["type"] == "legality":
                responses.append({
                    "challenge_type": "合法性质疑",
                    "response": f"该证据的{evidence.get('evidence_type', '')}取得方式合法{challenge.get('suggested_response', '')}",
                    "legal_basis": "《民事诉讼法》第68条"
                })
            elif challenge["type"] == "relevance":
                responses.append({
                    "challenge_type": "关联性质疑",
                    "response": "该证据能证明案件的相关事实，与争议焦点具有关联",
                    "legal_basis": "《民诉证据规定》第85条"
                })
        
        return responses
    
    def _generate_reinforcement(self, evidence: Dict, auth: Dict,
                                leg: Dict, rel: Dict) -> List[str]:
        """生成补强建议"""
        suggestions = []
        
        if auth.get("score", 100) < 80:
            suggestions.append("建议提供证据原件或申请鉴定以增强真实性")
        
        if leg.get("score", 100) < 100:
            defect = leg.get("defect_type", "瑕疵")
            suggestions.append(f"建议补充说明或提供证据来源以消除{defect}问题")
        
        if rel.get("score", 100) < 70:
            suggestions.append("建议收集更多直接证明案件事实的证据进行补强")
        
        # 基于证据类型的通用建议
        evidence_type = evidence.get("evidence_type", "")
        if evidence_type == "TESTIMONY":
            suggestions.append("建议申请证人出庭接受质询")
        elif evidence_type == "AUDIO_VIDEO":
            suggestions.append("建议提供原始载体并进行鉴定")
        
        return suggestions if suggestions else ["证据三性良好，可直接使用"]
    
    def _map_evidence_type_to_rule(self, evidence_type: str) -> str:
        """将证据类型映射到判断规则"""
        mapping = {
            "CONTRACT": "document",
            "DOCUMENT": "document",
            "CORRESPONDENCE": "document",
            "PAYMENT": "document",
            "AUDIO_VIDEO": "audio_video",
            "TESTIMONY": "testimony",
            "EXPERT": "expert"
        }
        return mapping.get(evidence_type, "document")
    
    def batch_analyze(self, evidence_list: List[Dict],
                      case_facts: Optional[str] = None) -> List[ThreeNaturesAnalysis]:
        """
        批量分析多个证据
        
        Args:
            evidence_list: 证据数据列表
            case_facts: 案件事实描述
            
        Returns:
            分析结果列表
        """
        results = []
        for evidence in evidence_list:
            try:
                result = self.analyze_three_natures(evidence, case_facts)
                results.append(result)
            except Exception as e:
                # 如果单个分析失败，记录错误但不中断
                results.append(None)
        
        return [r for r in results if r is not None]


# 全局实例
evidence_three_natures_service = EvidenceThreeNaturesService()
