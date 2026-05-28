"""
案件画像系统 - 持续追踪与智能补全
================================
核心理念：
1. 每次交互都更新案件画像，AI越来越"懂"这个案件
2. 像资深律师一样记住所有细节，形成完整认知
3. 主动识别遗漏信息，在对话中自然引导补充
4. 证据和对话都是资产，持续积累形成知识图谱
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib
import re


class ProfileCompleteness(Enum):
    """画像完整度"""
    SPARSE = "稀疏"        # 信息很少
    BASIC = "基本"         # 基础信息有
    DETAILED = "详细"      # 有较多细节
    COMPREHENSIVE = "完整"  # 信息完整


class KnowledgeType(Enum):
    """知识类型"""
    FACT = "fact"          # 事实陈述
    EVIDENCE = "evidence"  # 证据信息
    CLAIM = "claim"        # 诉辩主张
    LEGAL = "legal"        # 法律认知
    RELATION = "relation"   # 关系推理


@dataclass
class KnowledgeAtom:
    """知识原子 - 最小的知识单元"""
    atom_id: str
    content: str                       # 知识内容
    knowledge_type: KnowledgeType       # 知识类型
    
    # 来源追踪
    source: str                        # 来源：对话/文档/分析
    source_id: str                      # 来源ID：对话ID或文档ID
    extracted_at: datetime = field(default_factory=datetime.now)
    
    # 置信度
    confidence: float = 1.0            # 置信度 0-1
    verified: bool = False             # 是否经过验证
    
    # 关联
    related_atoms: List[str] = field(default_factory=list)  # 关联的知识原子
    contradicts: List[str] = field(default_factory=list)    # 矛盾的知识
    supports: List[str] = field(default_factory=list)       # 支持的知识
    
    # 元数据
    keywords: List[str] = field(default_factory=list)
    entity_tags: List[str] = field(default_factory=list)   # 实体标签：人/钱/时间/行为
    
    def to_dict(self) -> dict:
        return {
            "atom_id": self.atom_id,
            "content": self.content,
            "type": self.knowledge_type.value,
            "source": self.source,
            "confidence": self.confidence,
            "verified": self.verified,
            "keywords": self.keywords,
            "entity_tags": self.entity_tags,
            "extracted_at": self.extracted_at.isoformat()
        }


@dataclass
class ConversationTurn:
    """对话回合"""
    turn_id: str
    turn_number: int
    
    # 用户输入
    user_input: str
    input_type: str  # question/evidence/answer/upload
    
    # 系统输出
    system_response: str
    
    # 提取的知识
    extracted_knowledge: List[str] = field(default_factory=list)  # 知识原子ID
    
    # 识别到的缺口
    identified_gaps: List[str] = field(default_factory=list)  # 证据缺口ID
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    
    # 质量评估
    user_satisfaction: Optional[float] = None
    follow_up_needed: bool = False


@dataclass
class CaseProfile:
    """案件画像"""
    case_id: int
    
    # 基础信息
    basic_info: Dict = field(default_factory=dict)  # 从案件表提取
    
    # 知识图谱
    knowledge_base: List[KnowledgeAtom] = field(default_factory=list)
    
    # 对话历史
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    
    # 证据库
    evidence_ids: List[int] = field(default_factory=list)  # 关联的文档ID
    
    # 证据缺口追踪
    tracked_gaps: Dict[str, Dict] = field(default_factory=dict)  # gap_id -> 状态
    
    # 画像评分
    completeness: ProfileCompleteness = ProfileCompleteness.SPARSE
    completeness_score: float = 0.0  # 0-100
    
    # 关键里程碑
    key_milestones: List[Dict] = field(default_factory=list)
    
    # 更新时间
    last_updated: datetime = field(default_factory=datetime.now)
    version: int = 1


class CaseProfileEngine:
    """
    案件画像引擎 - 持续学习和智能补全
    
    核心能力：
    1. 知识抽取：从对话和文档中自动抽取知识
    2. 缺口追踪：识别并追踪需要补充的信息
    3. 画像更新：每次交互都更新画像
    4. 智能建议：基于画像生成下一步建议
    """
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
        
        # 案件画像缓存
        self.profiles: Dict[int, CaseProfile] = {}
        
        # 知识原子索引
        self.atom_index: Dict[str, KnowledgeAtom] = {}
    
    # ==================== 核心功能 ====================
    
    def get_or_create_profile(self, case_id: int, basic_info: Dict) -> CaseProfile:
        """获取或创建案件画像"""
        if case_id not in self.profiles:
            self.profiles[case_id] = CaseProfile(
                case_id=case_id,
                basic_info=basic_info,
                last_updated=datetime.now()
            )
        
        profile = self.profiles[case_id]
        
        # 更新基础信息
        if basic_info:
            profile.basic_info.update(basic_info)
        
        # 更新画像评分
        profile.completeness_score = self._calculate_completeness(profile)
        profile.completeness = self._get_completeness_level(profile.completeness_score)
        
        return profile
    
    def process_interaction(
        self,
        case_id: int,
        user_input: str,
        input_type: str,
        system_response: str,
        basic_info: Optional[Dict] = None
    ) -> Dict:
        """
        处理每次交互，自动更新画像
        
        这是核心方法，每次用户对话都应该调用它
        """
        # 获取/创建画像
        profile = self.get_or_create_profile(case_id, basic_info or {})
        
        # 1. 从用户输入中抽取知识
        extracted_atoms = self._extract_knowledge(user_input, input_type, profile)
        
        # 2. 添加到知识库
        for atom in extracted_atoms:
            profile.knowledge_base.append(atom)
            self.atom_index[atom.atom_id] = atom
        
        # 3. 创建对话回合
        turn = ConversationTurn(
            turn_id=self._generate_id(),
            turn_number=len(profile.conversation_history) + 1,
            user_input=user_input,
            input_type=input_type,
            system_response=system_response,
            extracted_knowledge=[a.atom_id for a in extracted_atoms]
        )
        profile.conversation_history.append(turn)
        
        # 4. 识别新的证据缺口
        new_gaps = self._identify_gaps_from_input(user_input, profile)
        
        # 5. 更新追踪的缺口
        for gap_id, gap_info in new_gaps.items():
            if gap_id not in profile.tracked_gaps:
                profile.tracked_gaps[gap_id] = {
                    "status": "identified",
                    "identified_at": datetime.now().isoformat(),
                    "resolved": False,
                    "resolution": None,
                    "resolution_at": None
                }
        
        # 6. 更新画像评分
        profile.completeness_score = self._calculate_completeness(profile)
        profile.completeness = self._get_completeness_level(profile.completeness_score)
        profile.last_updated = datetime.now()
        profile.version += 1
        
        # 7. 生成建议
        suggestions = self._generate_suggestions(profile, new_gaps)
        
        return {
            "profile_updated": True,
            "knowledge_extracted": len(extracted_atoms),
            "gaps_identified": len(new_gaps),
            "new_suggestions": suggestions,
            "completeness": {
                "score": profile.completeness_score,
                "level": profile.completeness.value
            }
        }
    
    # ==================== 知识抽取 ====================
    
    def _extract_knowledge(
        self, 
        text: str, 
        input_type: str,
        profile: CaseProfile
    ) -> List[KnowledgeAtom]:
        """从输入中抽取知识原子"""
        atoms = []
        
        # 实体识别
        entities = self._extract_entities(text)
        
        # 根据输入类型决定抽取策略
        if input_type == "evidence":
            # 证据类型输入 - 抽取事实和证据信息
            atoms.append(KnowledgeAtom(
                atom_id=self._generate_id(),
                content=self._summarize_evidence(text),
                knowledge_type=KnowledgeType.EVIDENCE,
                source="user_input",
                source_id=input_type,
                entity_tags=["evidence"],
                keywords=self._extract_keywords(text)
            ))
        
        elif input_type == "answer":
            # 回答类型输入 - 抽取确认的事实
            atoms.append(KnowledgeAtom(
                atom_id=self._generate_id(),
                content=text,
                knowledge_type=KnowledgeType.FACT,
                source="conversation",
                source_id=input_type,
                entity_tags=entities,
                keywords=self._extract_keywords(text)
            ))
        
        elif input_type == "question":
            # 问题类型输入 - 标记为待解决
            pass  # 问题不直接产生知识
        
        # 通用事实抽取
        facts = self._extract_stated_facts(text)
        for fact in facts:
            atom = KnowledgeAtom(
                atom_id=self._generate_id(),
                content=fact,
                knowledge_type=KnowledgeType.FACT,
                source="user_input",
                source_id=input_type,
                entity_tags=self._extract_entities(fact),
                keywords=self._extract_keywords(fact)
            )
            atoms.append(atom)
        
        return atoms
    
    def _extract_entities(self, text: str) -> List[str]:
        """提取实体标签"""
        entities = []
        
        # 金额识别
        import re
        money_pattern = r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:元|万|千|块)'
        money_matches = re.findall(money_pattern, text)
        if money_matches:
            entities.append("money")
        
        # 日期识别
        date_pattern = r'(\d{4}[年\-/]\d{1,2}[月\-/]\d{1,2}日?)'
        date_matches = re.findall(date_pattern, text)
        if date_matches:
            entities.append("date")
        
        # 人名（简化版）
        names = ["原告", "被告", "甲方", "乙方", "当事人", "公司", "我", "他"]
        if any(name in text for name in names):
            entities.append("person")
        
        # 行为词
        action_words = ["签订", "付款", "违约", "侵权", "欠款", "转账", "交付"]
        for word in action_words:
            if word in text:
                entities.append("action")
        
        return entities
    
    def _extract_stated_facts(self, text: str) -> List[str]:
        """提取陈述的事实"""
        facts = []
        
        # 提取"XXX的"类型的陈述
        patterns = [
            r'([^，。,]+)签订了([^，。,]+)',
            r'([^，。,]+)支付了([^，。,]+)',
            r'([^，。,]+)欠了([^，。,]+)',
            r'([^，。,]+)转账([^，。,]+)',
            r'在([^，。,]+)[,，]?([^，。,]+)发生了'
        ]
        
        import re
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    facts.append(' '.join(match))
                else:
                    facts.append(match)
        
        return facts[:5]  # 限制数量
    
    def _summarize_evidence(self, text: str) -> str:
        """总结证据内容"""
        # 简化处理，实际可以调用LLM
        if len(text) > 50000:
            return text[:50000] + "..."
        return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简化版关键词提取
        keywords = []
        important_words = [
            "合同", "协议", "转账", "付款", "违约", "侵权", "赔偿",
            "微信", "录音", "邮件", "发票", "收据", "银行", "现金",
            "口头", "书面", "承诺", "承认", "否认", "争议"
        ]
        
        for word in important_words:
            if word in text:
                keywords.append(word)
        
        return keywords[:10]  # 最多10个
    
    # ==================== 缺口追踪 ====================
    
    def _identify_gaps_from_input(
        self, 
        user_input: str, 
        profile: CaseProfile
    ) -> Dict[str, Dict]:
        """从用户输入中识别证据缺口"""
        gaps = {}
        
        # 检查是否提到缺失的证据类型
        gap_keywords = {
            "转账凭证": ["转账", "付款", "银行", "汇款"],
            "书面证据": ["合同", "协议", "书面", "签字", "盖章"],
            "沟通记录": ["微信", "短信", "邮件", "通话", "聊天"],
            "证人": ["证人", "知情人", "目击", "在场"]
        }
        
        # 检查已有关于这些话题的证据
        evidence_keywords = set()
        for atom in profile.knowledge_base:
            if atom.knowledge_type == KnowledgeType.EVIDENCE:
                evidence_keywords.update(atom.keywords)
        
        for gap_type, keywords in gap_keywords.items():
            has_evidence = any(kw in evidence_keywords for kw in keywords)
            
            if not has_evidence:
                # 检查是否在当前输入中确认了没有
                if "没有" in user_input or "没" in user_input:
                    gaps[f"gap_{gap_type}"] = {
                        "type": gap_type,
                        "status": "confirmed_missing",
                        "severity": "high" if gap_type in ["转账凭证", "书面证据"] else "medium"
                    }
        
        return gaps
    
    def resolve_gap(self, case_id: int, gap_id: str, resolution: str):
        """标记缺口已解决"""
        if case_id in self.profiles:
            profile = self.profiles[case_id]
            if gap_id in profile.tracked_gaps:
                profile.tracked_gaps[gap_id]["resolved"] = True
                profile.tracked_gaps[gap_id]["resolution"] = resolution
                profile.tracked_gaps[gap_id]["resolution_at"] = datetime.now().isoformat()
    
    # ==================== 画像评估 ====================
    
    def _calculate_completeness(self, profile: CaseProfile) -> float:
        """计算画像完整度"""
        score = 0.0
        
        # 1. 基础信息 (30分)
        basic_fields = ["title", "case_type", "plaintiff", "defendant", "cause", "claim_amount"]
        basic_filled = sum(1 for f in basic_fields if profile.basic_info.get(f))
        score += (basic_filled / len(basic_fields)) * 30
        
        # 2. 知识原子 (30分)
        knowledge_score = min(len(profile.knowledge_base) / 10, 1.0) * 30
        
        # 3. 对话历史 (20分)
        conversation_score = min(len(profile.conversation_history) / 5, 1.0) * 20
        
        # 4. 证据数量 (20分)
        evidence_score = min(len(profile.evidence_ids) / 5, 1.0) * 20
        
        return round(score, 1)
    
    def _get_completeness_level(self, score: float) -> ProfileCompleteness:
        """根据评分获取完整度等级"""
        if score >= 80:
            return ProfileCompleteness.COMPREHENSIVE
        elif score >= 60:
            return ProfileCompleteness.DETAILED
        elif score >= 30:
            return ProfileCompleteness.BASIC
        else:
            return ProfileCompleteness.SPARSE
    
    # ==================== 智能建议 ====================
    
    def _generate_suggestions(
        self, 
        profile: CaseProfile,
        new_gaps: Dict
    ) -> List[Dict]:
        """生成下一步建议"""
        suggestions = []
        
        # 1. 基于缺口的建议
        for gap_id, gap_info in new_gaps.items():
            if gap_info.get("status") == "confirmed_missing":
                gap_type = gap_info.get("type", "")
                suggestions.append({
                    "type": "evidence_gap",
                    "priority": "high",
                    "message": f"发现缺少 {gap_type}",
                    "action": self._get_gap_action(gap_type)
                })
        
        # 2. 基于完整度的建议
        if profile.completeness == ProfileCompleteness.SPARSE:
            suggestions.append({
                "type": "completeness",
                "priority": "high",
                "message": "案件信息太少，需要补充更多细节",
                "action": "请详细描述案件经过"
            })
        elif profile.completeness == ProfileCompleteness.BASIC:
            suggestions.append({
                "type": "completeness",
                "priority": "medium",
                "message": "案件基本信息已完善",
                "action": "建议上传相关证据材料"
            })
        
        # 3. 基于知识的建议
        if len(profile.knowledge_base) > 5:
            suggestions.append({
                "type": "analysis",
                "priority": "low",
                "message": "已积累足够信息",
                "action": "可以生成详细的案件分析报告"
            })
        
        return suggestions
    
    def _get_gap_action(self, gap_type: str) -> str:
        """获取缺口对应的行动建议"""
        actions = {
            "转账凭证": "请前往银行打印流水账单",
            "书面证据": "请提供合同原件或复印件",
            "沟通记录": "请导出微信聊天记录或邮件",
            "证人": "请提供知情人的联系方式"
        }
        return actions.get(gap_type, "请补充相关材料")
    
    # ==================== 画像查询 ====================
    
    def get_profile_summary(self, case_id: int) -> Dict:
        """获取画像摘要"""
        if case_id not in self.profiles:
            return {"error": "画像不存在"}
        
        profile = self.profiles[case_id]
        
        # 统计各类型知识
        type_counts = {}
        for atom in profile.knowledge_base:
            t = atom.knowledge_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # 统计缺口
        unresolved_gaps = [
            {"id": k, **v} for k, v in profile.tracked_gaps.items()
            if not v.get("resolved", False)
        ]
        
        return {
            "case_id": case_id,
            "completeness": {
                "score": profile.completeness_score,
                "level": profile.completeness.value
            },
            "knowledge_stats": {
                "total": len(profile.knowledge_base),
                "by_type": type_counts
            },
            "conversation_count": len(profile.conversation_history),
            "evidence_count": len(profile.evidence_ids),
            "unresolved_gaps": unresolved_gaps,
            "last_updated": profile.last_updated.isoformat()
        }
    
    def query_knowledge(
        self, 
        case_id: int, 
        query: str,
        knowledge_type: Optional[str] = None
    ) -> List[Dict]:
        """查询知识库"""
        if case_id not in self.profiles:
            return []
        
        profile = self.profiles[case_id]
        query_lower = query.lower()
        
        results = []
        for atom in profile.knowledge_base:
            # 类型过滤
            if knowledge_type and atom.knowledge_type.value != knowledge_type:
                continue
            
            # 关键词匹配
            if (query_lower in atom.content.lower() or
                any(query_lower in kw.lower() for kw in atom.keywords)):
                results.append(atom.to_dict())
        
        return results
    
    # ==================== 工具方法 ====================
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())[:8]


# 全局实例
profile_engine = CaseProfileEngine()
