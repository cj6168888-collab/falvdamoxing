"""
增强版证据图谱系统 - 证据链构建与智能分析
==========================================
核心特性：
1. 证据知识图谱 - 每个证据作为节点，关联事实和关系
2. 信度分析 - 评估每份证据的可信度
3. 关键词索引 - 精准检索证据
4. 去重机制 - 内容哈希避免重复存储
5. 证据图谱可视化 - 直观展示证据关系
6. 智能补全引导 - 主动发现证据缺口

设计理念：
- 用户不是律师，系统应该主动引导
- 证据是资产，持续积累形成知识图谱
- 像资深律师一样分析证据
"""

import hashlib
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class EvidenceStrength(Enum):
    """证据证明力等级"""
    STRONG = "strong"           # 证明力强
    MEDIUM = "medium"          # 证明力中等
    WEAK = "weak"              # 证明力弱
    UNKNOWN = "unknown"        # 待评估


class EvidenceStatus(Enum):
    """证据状态"""
    PENDING = "pending"         # 待分析
    ANALYZED = "analyzed"       # 已分析
    VERIFIED = "verified"       # 已核实
    QUESTIONABLE = "questionable"  # 存疑


@dataclass
class EvidenceNode:
    """
    证据节点 - 知识图谱中的核心节点
    
    包含证据的完整信息和AI分析结果
    """
    # 基本信息
    node_id: str                    # 节点唯一ID
    evidence_id: int                # 数据库证据ID
    
    # 证据内容
    name: str                       # 证据名称
    evidence_type: str               # 证据类型
    content: str                    # 证据内容摘要
    content_full: str = ""          # 完整内容（如有）
    source: str = ""                # 证据来源
    
    # 证明信息
    proves_facts: List[str] = field(default_factory=list)  # 能证明的事实
    custody: str = ""               # 举证方
    uploaded_at: str = ""           # 上传时间
    
    # AI分析结果
    strength: EvidenceStrength = EvidenceStrength.UNKNOWN  # 证明力
    strength_score: float = 0.5     # 证明力评分 0-1
    strength_factors: List[str] = field(default_factory=list)  # 影响证明力的因素
    
    # 关联分析
    related_evidence: List[str] = field(default_factory=list)  # 相关证据ID
    contradicts_evidence: List[str] = field(default_factory=list)  # 矛盾证据ID
    supports_evidence: List[str] = field(default_factory=list)  # 支持证据ID
    
    # 关键词索引（用于精准检索）
    keywords: List[str] = field(default_factory=list)
    entity_tags: List[str] = field(default_factory=list)  # 实体标签：人/钱/时间/行为
    
    # 去重哈希
    content_hash: str = ""         # 内容哈希，用于去重
    keyword_hash: str = ""          # 关键词哈希
    
    # 分析状态
    status: EvidenceStatus = EvidenceStatus.PENDING
    analyzed_at: Optional[str] = None
    
    # 原始数据引用
    original_doc_id: Optional[int] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.content_hash:
            self.content_hash = self._generate_hash()
        if not self.keyword_hash:
            self.keyword_hash = self._generate_keyword_hash()
    
    def _generate_hash(self) -> str:
        """生成内容哈希用于去重 - 法律应用：使用完整内容"""
        content = f"{self.name}|{self.content}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_keyword_hash(self) -> str:
        """生成关键词哈希"""
        keywords = "|".join(sorted(self.keywords))
        return hashlib.md5(keywords.encode()).hexdigest()[:16]


@dataclass
class FactNode:
    """
    事实节点 - 案件中的关键事实
    
    与证据节点形成证明关系
    """
    fact_id: str
    description: str              # 事实描述
    fact_type: str              # 事实类型：时间/金额/行为/关系
    importance: str = "medium"  # 重要性：high/medium/low
    proven: bool = False         # 是否已被证明
    evidence_ids: List[str] = field(default_factory=list)  # 支持此事实的证据ID
    
    # AI分析
    analysis_summary: str = ""


@dataclass
class EvidenceGap:
    """
    证据缺口 - 需要补充的证据
    
    系统主动发现的证据缺失
    """
    gap_id: str
    missing_type: str            # 缺失的证据类型
    proves_fact: str            # 影响证明的事实
    importance: str              # 重要性：high/medium/low
    
    # 影响分析
    affects_claims: List[str] = field(default_factory=list)
    risk_description: str = ""
    
    # 补全方案
    how_to_obtain: List[str] = field(default_factory=list)
    alternative_evidence: List[str] = field(default_factory=list)
    feasibility: str = "medium"  # 可行性：high/medium/low
    estimated_cost: str = ""
    estimated_time: str = ""
    
    # 引导问题
    discovery_questions: List[str] = field(default_factory=list)
    
    # 状态
    status: str = "identified"  # identified/discovered/resolved
    discovered_at: str = ""


@dataclass
class EvidenceGraph:
    """
    证据图谱 - 整个案件的证据网络
    
    包含：
    - 证据节点
    - 事实节点
    - 证据缺口
    - 关系边
    """
    case_id: int
    case_type: str = ""
    
    # 节点存储
    evidence_nodes: Dict[str, EvidenceNode] = field(default_factory=dict)
    fact_nodes: Dict[str, FactNode] = field(default_factory=dict)
    evidence_gaps: Dict[str, EvidenceGap] = field(default_factory=dict)
    
    # 索引（加速查询）
    keyword_index: Dict[str, Set[str]] = field(default_factory=dict)  # 关键词 -> 证据ID
    type_index: Dict[str, Set[str]] = field(default_factory=dict)      # 类型 -> 证据ID
    hash_index: Dict[str, str] = field(default_factory=dict)           # 哈希 -> 证据ID
    
    # 统计
    total_evidence: int = 0
    analyzed_evidence: int = 0
    total_gaps: int = 0
    resolved_gaps: int = 0
    
    # 元数据
    created_at: str = ""
    updated_at: str = ""
    version: int = 1
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "case_id": self.case_id,
            "case_type": self.case_type,
            "evidence_nodes": {k: self._node_to_dict(v) for k, v in self.evidence_nodes.items()},
            "fact_nodes": {k: self._fact_to_dict(v) for k, v in self.fact_nodes.items()},
            "evidence_gaps": {k: self._gap_to_dict(v) for k, v in self.evidence_gaps.items()},
            "stats": {
                "total_evidence": self.total_evidence,
                "analyzed_evidence": self.analyzed_evidence,
                "total_gaps": self.total_gaps,
                "resolved_gaps": self.resolved_gaps
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def _node_to_dict(self, node: EvidenceNode) -> dict:
        return {
            "node_id": node.node_id,
            "name": node.name,
            "evidence_type": node.evidence_type,
            "strength": node.strength.value,
            "strength_score": node.strength_score,
            "proves_facts": node.proves_facts,
            "keywords": node.keywords,
            "content_hash": node.content_hash
        }
    
    def _fact_to_dict(self, fact: FactNode) -> dict:
        return {
            "fact_id": fact.fact_id,
            "description": fact.description,
            "fact_type": fact.fact_type,
            "importance": fact.importance,
            "proven": fact.proven,
            "evidence_count": len(fact.evidence_ids)
        }
    
    def _gap_to_dict(self, gap: EvidenceGap) -> dict:
        return {
            "gap_id": gap.gap_id,
            "missing_type": gap.missing_type,
            "proves_fact": gap.proves_fact,
            "importance": gap.importance,
            "how_to_obtain": gap.how_to_obtain,
            "status": gap.status
        }


class EvidenceGraphBuilder:
    """
    证据图谱构建器
    
    核心功能：
    1. 添加证据并分析
    2. 构建证据关系
    3. 发现证据缺口
    4. 去重检测
    """
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
        self.graphs: Dict[int, EvidenceGraph] = {}  # case_id -> graph
    
    def get_or_create_graph(self, case_id: int, case_type: str = "") -> EvidenceGraph:
        """获取或创建证据图谱"""
        if case_id not in self.graphs:
            self.graphs[case_id] = EvidenceGraph(
                case_id=case_id,
                case_type=case_type,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        return self.graphs[case_id]
    
    def add_evidence(
        self, 
        case_id: int,
        evidence_id: int,
        name: str,
        evidence_type: str,
        content: str,
        source: str = "",
        custody: str = "",
        uploaded_at: str = ""
    ) -> Dict:
        """
        添加证据到图谱
        
        自动处理：
        - 去重检测
        - 关键词提取
        - 信度分析
        - 关系构建
        """
        graph = self.get_or_create_graph(case_id)
        
        # 创建证据节点
        node = EvidenceNode(
            node_id=f"ev_{evidence_id}",
            evidence_id=evidence_id,
            name=name,
            evidence_type=evidence_type,
            # 法律应用：保留完整内容
            content=content,
            content_full=content,
            source=source,
            custody=custody,
            uploaded_at=uploaded_at or datetime.now().isoformat()
        )
        
        # 检查去重
        if node.content_hash in graph.hash_index:
            return {
                "status": "duplicate",
                "node_id": graph.hash_index[node.content_hash],
                "message": "此证据已存在"
            }
        
        # 提取关键词
        if self.llm:
            node.keywords = self._extract_keywords(node)
        
        # 更新索引
        graph.keyword_index[node.node_id] = set(node.keywords)
        graph.type_index.setdefault(evidence_type, set()).add(node.node_id)
        graph.hash_index[node.content_hash] = node.node_id
        
        # 添加到图谱
        graph.evidence_nodes[node.node_id] = node
        graph.total_evidence = len(graph.evidence_nodes)
        graph.updated_at = datetime.now().isoformat()
        graph.version += 1
        
        return {
            "status": "added",
            "node_id": node.node_id,
            "content_hash": node.content_hash,
            "keywords": node.keywords,
            "message": "证据已添加"
        }
    
    def analyze_evidence(self, case_id: int, node_id: str) -> EvidenceNode:
        """
        分析单个证据
        
        包括：
        - 证明力评估
        - 证明事实提取
        - 关系发现
        """
        graph = self.get_or_create_graph(case_id)
        if node_id not in graph.evidence_nodes:
            raise ValueError(f"证据节点 {node_id} 不存在")
        
        node = graph.evidence_nodes[node_id]
        
        if not self.llm:
            return node
        
        # AI分析证据
        prompt = f"""分析以下证据的证明力：

【证据名称】{node.name}
【证据类型】{node.evidence_type}
【证据内容】{node.content_full if node.content_full else node.content}

请分析：
1. 证据的证明力评分 (0-1)
2. 影响证明力的因素
3. 这个证据能证明什么事实
4. 证据的优点和弱点

返回JSON格式：
{{
    "strength_score": 0.85,
    "strength_factors": ["因素1", "因素2"],
    "proves_facts": ["事实1", "事实2"],
    "strength": "strong/medium/weak"
}}"""
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "你是一位专业的诉讼证据审查专家。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")
            
            result = json.loads(response)
            
            node.strength_score = result.get("strength_score", 0.5)
            node.strength = EvidenceStrength(result.get("strength", "unknown"))
            node.strength_factors = result.get("strength_factors", [])
            node.proves_facts = result.get("proves_facts", [])
            
            # 提取实体标签
            node.entity_tags = self._extract_entity_tags(node.content_full or node.content)
            
            # 更新状态
            node.status = EvidenceStatus.ANALYZED
            node.analyzed_at = datetime.now().isoformat()
            
            # 更新统计
            graph.analyzed_evidence = sum(
                1 for n in graph.evidence_nodes.values() 
                if n.status in [EvidenceStatus.ANALYZED, EvidenceStatus.VERIFIED]
            )
            
            # 添加事实节点
            for fact_desc in node.proves_facts:
                self._add_fact_node(graph, fact_desc, node.node_id)
            
            graph.updated_at = datetime.now().isoformat()
            
        except Exception as e:
            print(f"证据分析失败: {e}")
        
        return node
    
    def analyze_all_evidence(self, case_id: int) -> Dict:
        """批量分析所有证据"""
        graph = self.get_or_create_graph(case_id)
        
        results = {
            "total": len(graph.evidence_nodes),
            "analyzed": 0,
            "failed": 0,
            "nodes": []
        }
        
        for node_id, node in graph.evidence_nodes.items():
            if node.status == EvidenceStatus.PENDING:
                try:
                    self.analyze_evidence(case_id, node_id)
                    results["analyzed"] += 1
                except Exception as e:
                    results["failed"] += 1
        
        results["nodes"] = list(graph.evidence_nodes.values())
        return results
    
    def build_relations(self, case_id: int) -> List[Dict]:
        """
        构建证据之间的关系
        
        包括：
        - 相关证据
        - 矛盾证据
        - 支持证据
        """
        graph = self.get_or_create_graph(case_id)
        relations = []
        
        # 比较所有证据对
        nodes = list(graph.evidence_nodes.values())
        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                relation = self._analyze_relation(node_a, node_b)
                if relation:
                    relations.append(relation)
                    
                    # 更新节点关系
                    if relation["type"] == "related":
                        node_a.related_evidence.append(node_b.node_id)
                        node_b.related_evidence.append(node_a.node_id)
                    elif relation["type"] == "contradicts":
                        node_a.contradicts_evidence.append(node_b.node_id)
                        node_b.contradicts_evidence.append(node_a.node_id)
                    elif relation["type"] == "supports":
                        node_a.supports_evidence.append(node_b.node_id)
                        node_b.related_evidence.append(node_a.node_id)
        
        return relations
    
    def _analyze_relation(self, node_a: EvidenceNode, node_b: EvidenceNode) -> Optional[Dict]:
        """
        分析两个证据之间的关系 - 法律应用专用：证据完整性优先

        重要原则：证据内容不得截断，必须完整传递给AI进行分析。
        """
        if not self.llm:
            return None

        prompt = f"""分析以下两个证据之间的关系：

【证据A】
名称：{node_a.name}
类型：{node_a.evidence_type}
内容：{node_a.content}

【证据B】
名称：{node_b.name}
类型：{node_b.evidence_type}
内容：{node_b.content}

请判断这两个证据之间的关系：
1. related - 证据相关，可以互相印证
2. contradicts - 证据矛盾，一个可能是假的
3. supports - 一个证据支持另一个
4. none - 没有明显关系

返回JSON格式：
{{
    "type": "related/contradicts/supports/none",
    "reason": "判断理由"
}}"""
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "你是一位专业的诉讼证据分析专家。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")
            
            result = json.loads(response)
            if result.get("type") != "none":
                return {
                    "evidence_a": node_a.node_id,
                    "evidence_b": node_b.node_id,
                    **result
                }
        except:
            pass
        
        return None
    
    def discover_gaps(self, case_id: int, case_type: str = "") -> List[EvidenceGap]:
        """
        发现证据缺口
        
        根据案件类型和已有证据，自动识别缺失的证据类型
        """
        graph = self.get_or_create_graph(case_id)
        
        # 根据案件类型定义需要的证据类型
        required_evidence = self._get_required_evidence_types(case_type or graph.case_type)
        
        # 已有证据类型
        existing_types = set()
        for node in graph.evidence_nodes.values():
            existing_types.add(node.evidence_type)
        
        gaps = []
        
        # 识别缺失的类型
        for req_type in required_evidence:
            if req_type["type"] not in existing_types:
                gap = EvidenceGap(
                    gap_id=f"gap_{len(graph.evidence_gaps) + 1}",
                    missing_type=req_type["type"],
                    proves_fact=req_type["proof_fact"],
                    importance=req_type["importance"],
                    affects_claims=req_type.get("claims", []),
                    risk_description=f"缺少{req_type['type']}可能导致{req_type['proof_fact']}无法证明",
                    how_to_obtain=req_type.get("how_to_get", []),
                    alternative_evidence=req_type.get("alternatives", []),
                    feasibility=req_type.get("feasibility", "medium"),
                    discovery_questions=req_type.get("questions", []),
                    status="identified",
                    discovered_at=datetime.now().isoformat()
                )
                gaps.append(gap)
                graph.evidence_gaps[gap.gap_id] = gap
        
        graph.total_gaps = len(graph.evidence_gaps)
        return gaps
    
    def _get_required_evidence_types(self, case_type: str) -> List[Dict]:
        """获取案件类型所需的证据类型"""
        
        templates = {
            "合同纠纷": [
                {"type": "书面证据", "proof_fact": "合同关系成立", "importance": "high",
                 "how_to_get": ["联系对方获取", "调取工商档案", "申请政府信息公开"],
                 "alternatives": ["微信记录", "录音", "邮件"],
                 "feasibility": "high",
                 "questions": ["有没有签订合同？合同原件还在吗？"]},
                {"type": "转账凭证", "proof_fact": "款项支付情况", "importance": "high",
                 "how_to_get": ["银行流水", "支付宝账单", "微信账单"],
                 "alternatives": ["转账截图+公证", "对方自认"],
                 "feasibility": "high",
                 "questions": ["付款是通过什么方式？银行转账还是现金？"]},
                {"type": "沟通记录", "proof_fact": "双方沟通过程", "importance": "medium",
                 "how_to_get": ["微信聊天", "邮件往来", "通话录音"],
                 "alternatives": ["书面确认函"],
                 "feasibility": "high",
                 "questions": ["有没有保留聊天记录？有没有和对方沟通过？"]},
            ],
            "侵权纠纷": [
                {"type": "侵权证据", "proof_fact": "侵权行为存在", "importance": "high",
                 "how_to_get": ["现场公证", "鉴定报告", "现场照片"],
                 "alternatives": ["录音录像", "证人证言"],
                 "feasibility": "medium",
                 "questions": ["有没有侵权现场的照片或录像？"]},
                {"type": "损害证据", "proof_fact": "损害事实和金额", "importance": "high",
                 "how_to_get": ["评估报告", "医疗票据", "财务账册"],
                 "alternatives": ["鉴定报告"],
                 "feasibility": "high",
                 "questions": ["损失有多少？有没有评估报告？"]},
                {"type": "因果关系证据", "proof_fact": "侵权与损害的因果关系", "importance": "high",
                 "how_to_get": ["鉴定意见", "专家论证"],
                 "alternatives": ["类案参考"],
                 "feasibility": "medium",
                 "questions": ["有没有证明因果关系的鉴定？"]},
            ],
            "债务纠纷": [
                {"type": "借条凭证", "proof_fact": "债务关系成立", "importance": "high",
                 "how_to_get": ["借条原件", "欠条"],
                 "alternatives": ["转账记录", "录音"],
                 "feasibility": "high",
                 "questions": ["有没有借条或欠条？"]},
                {"type": "转账记录", "proof_fact": "款项交付情况", "importance": "high",
                 "how_to_get": ["银行流水", "支付宝账单"],
                 "alternatives": ["证人证言"],
                 "feasibility": "high",
                 "questions": ["借款是怎么支付的？银行转账还是现金？"]},
            ]
        }
        
        return templates.get(case_type, templates["合同纠纷"])
    
    def _add_fact_node(self, graph: EvidenceGraph, fact_desc: str, evidence_id: str):
        """添加事实节点"""
        fact_id = f"fact_{len(graph.fact_nodes) + 1}"
        fact = FactNode(
            fact_id=fact_id,
            description=fact_desc,
            fact_type=self._classify_fact_type(fact_desc),
            proven=True,
            evidence_ids=[evidence_id]
        )
        graph.fact_nodes[fact_id] = fact
    
    def _classify_fact_type(self, fact_desc: str) -> str:
        """分类事实类型"""
        if any(kw in fact_desc for kw in ["时间", "日期", "年", "月", "日"]):
            return "time"
        if any(kw in fact_desc for kw in ["金额", "钱", "元", "支付", "收到"]):
            return "money"
        if any(kw in fact_desc for kw in ["签订", "交付", "违约", "侵权", "行为"]):
            return "action"
        return "relation"
    
    def _extract_keywords(self, node: EvidenceNode) -> List[str]:
        """提取关键词"""
        if not self.llm:
            return self._simple_keyword_extract(node)
        
        prompt = f"""从以下证据中提取5-10个关键词，用于精准检索：

【证据名称】{node.name}
【证据内容】{node.content_full if node.content_full else node.content}

关键词应包括：
- 关键人物
- 关键金额
- 关键行为
- 关键时间
- 关键关系

返回JSON数组格式：["关键词1", "关键词2", ...]"""
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "提取关键词。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")
            return json.loads(response)
        except:
            return self._simple_keyword_extract(node)
    
    def _simple_keyword_extract(self, node: EvidenceNode) -> List[str]:
        """简单关键词提取（无LLM时使用）"""
        text = f"{node.name} {node.content}".lower()
        keywords = []
        
        # 关键模式
        patterns = {
            "金额": r'(\d+[万千百]?元)',
            "日期": r'(\d{4}[年\-]\d{1,2}[月\-]\d{1,2})',
            "转账": ["转账", "汇款", "支付"],
            "合同": ["合同", "协议"],
            "微信": ["微信", "聊天", "记录"],
        }
        
        for key, pattern in patterns.items():
            if isinstance(pattern, list):
                if any(p in text for p in pattern):
                    keywords.append(key)
            else:
                if re.search(pattern, text):
                    keywords.append(key)
        
        return keywords
    
    def _extract_entity_tags(self, text: str) -> List[str]:
        """提取实体标签"""
        tags = []
        
        # 金额
        if re.search(r'\d+[万千百]?元', text):
            tags.append("money")
        
        # 日期
        if re.search(r'\d{4}[年\-]\d{1,2}[月\-]\d{1,2}', text):
            tags.append("date")
        
        # 行为
        actions = ["签订", "付款", "交付", "违约", "侵权", "转账", "承诺"]
        for action in actions:
            if action in text:
                tags.append("action")
        
        return tags
    
    def query_evidence(
        self, 
        case_id: int, 
        query: str,
        search_type: str = "all"
    ) -> List[EvidenceNode]:
        """
        精准查询证据
        
        支持多种查询方式
        """
        graph = self.get_or_create_graph(case_id)
        
        if not query:
            return list(graph.evidence_nodes.values())
        
        query_lower = query.lower()
        
        if search_type == "keywords":
            # 关键词检索
            results = []
            for node in graph.evidence_nodes.values():
                if any(query_lower in kw.lower() for kw in node.keywords):
                    results.append(node)
            return results
        
        elif search_type == "type":
            # 类型检索
            return [
                n for n in graph.evidence_nodes.values()
                if query_lower in n.evidence_type.lower()
            ]
        
        elif search_type == "related":
            # 相关证据
            for node in graph.evidence_nodes.values():
                if query_lower in node.name.lower():
                    related_ids = node.related_evidence + node.supports_evidence
                    return [graph.evidence_nodes[nid] for nid in related_ids if nid in graph.evidence_nodes]
            return []
        
        elif search_type == "contradicts":
            # 矛盾证据
            for node in graph.evidence_nodes.values():
                if query_lower in node.name.lower():
                    return [graph.evidence_nodes[nid] for nid in node.contradicts_evidence if nid in graph.evidence_nodes]
            return []
        
        else:
            # 全局检索
            return [
                n for n in graph.evidence_nodes.values()
                if query_lower in n.name.lower() or
                   query_lower in n.evidence_type.lower() or
                   query_lower in n.content.lower() or
                   any(query_lower in kw.lower() for kw in n.keywords)
            ]
    
    def get_graph_summary(self, case_id: int) -> Dict:
        """获取图谱摘要"""
        graph = self.get_or_create_graph(case_id)
        
        # 按类型统计
        type_counts = {}
        strength_stats = {"strong": 0, "medium": 0, "weak": 0, "unknown": 0}
        
        for node in graph.evidence_nodes.values():
            type_counts[node.evidence_type] = type_counts.get(node.evidence_type, 0) + 1
            strength_stats[node.strength.value] += 1
        
        return {
            "case_id": case_id,
            "total_evidence": graph.total_evidence,
            "analyzed_evidence": graph.analyzed_evidence,
            "by_type": type_counts,
            "strength_distribution": strength_stats,
            "total_gaps": graph.total_gaps,
            "resolved_gaps": graph.resolved_gaps,
            "proof_chain_score": self._calculate_proof_score(graph)
        }
    
    def _calculate_proof_score(self, graph: EvidenceGraph) -> float:
        """计算证明链完整度"""
        if not graph.fact_nodes:
            return 0.0
        
        proven_facts = sum(1 for f in graph.fact_nodes.values() if f.proven and f.evidence_ids)
        total_facts = len(graph.fact_nodes)
        
        return proven_facts / total_facts if total_facts > 0 else 0.0
    
    def get_graph_visualization_data(self, case_id: int) -> Dict:
        """
        获取可视化数据
        
        用于前端渲染证据图谱
        """
        graph = self.get_or_create_graph(case_id)
        
        nodes = []
        edges = []
        
        # 证据节点
        for node in graph.evidence_nodes.values():
            color = {
                EvidenceStrength.STRONG: "#22c55e",
                EvidenceStrength.MEDIUM: "#f59e0b",
                EvidenceStrength.WEAK: "#ef4444",
                EvidenceStrength.UNKNOWN: "#94a3b8"
            }.get(node.strength, "#94a3b8")
            
            nodes.append({
                "id": node.node_id,
                "label": node.name,
                "type": "evidence",
                "category": node.evidence_type,
                "color": color,
                "size": node.strength_score * 20 + 10,
                "strength": node.strength.value,
                "strength_score": node.strength_score,
                "keywords": node.keywords[:3]
            })
        
        # 事实节点
        for fact in graph.fact_nodes.values():
            nodes.append({
                "id": fact.fact_id,
                "label": fact.description[:20],
                "type": "fact",
                "category": fact.fact_type,
                "color": "#3b82f6",
                "size": 15 if fact.proven else 10,
                "proven": fact.proven
            })
        
        # 边（证据到事实）
        for node in graph.evidence_nodes.values():
            for fact_id in node.proves_facts:
                if fact_id in graph.fact_nodes:
                    edges.append({
                        "source": node.node_id,
                        "target": fact_id,
                        "type": "proves"
                    })
        
        # 边（证据间关系）
        for node in graph.evidence_nodes.values():
            for related_id in node.related_evidence:
                edges.append({
                    "source": node.node_id,
                    "target": related_id,
                    "type": "related"
                })
            for related_id in node.contradicts_evidence:
                edges.append({
                    "source": node.node_id,
                    "target": related_id,
                    "type": "contradicts"
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_evidence": len(nodes),
                "total_facts": len(graph.fact_nodes),
                "total_gaps": graph.total_gaps
            }
        }
    
    def check_duplicate(self, case_id: int, content: str, name: str) -> Optional[str]:
        """检查证据是否重复 - 法律应用：使用完整内容"""
        content_hash = hashlib.md5(f"{name}|{content}".encode()).hexdigest()[:16]
        graph = self.get_or_create_graph(case_id)
        return graph.hash_index.get(content_hash)
    
    def remove_evidence(self, case_id: int, node_id: str) -> bool:
        """移除证据"""
        graph = self.get_or_create_graph(case_id)
        
        if node_id not in graph.evidence_nodes:
            return False
        
        node = graph.evidence_nodes[node_id]
        
        # 清理索引
        if node.content_hash in graph.hash_index:
            del graph.hash_index[node.content_hash]
        
        # 从类型索引移除
        if node.evidence_type in graph.type_index:
            graph.type_index[node.evidence_type].discard(node_id)
        
        # 从关键词索引移除
        for kw in node.keywords:
            if kw in graph.keyword_index:
                graph.keyword_index[kw].discard(node_id)
        
        # 从事实节点移除关联
        for fact in graph.fact_nodes.values():
            if node_id in fact.evidence_ids:
                fact.evidence_ids.remove(node_id)
        
        # 删除节点
        del graph.evidence_nodes[node_id]
        graph.total_evidence = len(graph.evidence_nodes)
        graph.updated_at = datetime.now().isoformat()
        
        return True


# 全局实例
evidence_graph_builder = EvidenceGraphBuilder()

def get_evidence_graph_builder(llm_service=None) -> EvidenceGraphBuilder:
    """获取证据图谱构建器实例"""
    global evidence_graph_builder
    if evidence_graph_builder is None:
        evidence_graph_builder = EvidenceGraphBuilder(llm_service)
    elif llm_service and evidence_graph_builder.llm is None:
        evidence_graph_builder.llm = llm_service
    return evidence_graph_builder
