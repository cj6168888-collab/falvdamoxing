"""
统一证据服务 (Evidence Service Facade)
======================================
整合四个证据子服务，为API层提供统一的证据管理入口：
- EvidenceServiceV2: 完整证据处理引擎（分类/信度/去重/关系）
- EvidenceGraphBuilder: 证据知识图谱（节点/关系/缺口/可视化）
- EvidenceNavigator: 主动式证据引导（缺口识别/行动建议）
- EvidenceQA: 单条证据专项问答

Facade 模式：对现有服务零侵入，渐进式合并
"""

from typing import Optional, List, Dict, Any

from app.services.evidence_v2 import EvidenceServiceV2, evidence_service_v2 as _evidence_v2
from app.services.evidence_graph import EvidenceGraphBuilder, evidence_graph_builder as _eg_builder
from app.services.evidence_navigator import EvidenceNavigator, evidence_navigator as _navigator
from app.services.evidence_system import EvidenceBookGenerator, EvidenceRiskAnalyzer


class EvidenceService:
    """
    统一证据服务 Facade

    对外提供四类证据能力：
    1. 证据处理引擎（V2）：分类、信度、去重、关系分析
    2. 证据图谱：知识图谱构建、关系可视化、缺口发现
    3. 证据引导：主动导航、缺口识别、行动建议
    4. 证据问答：单条证据深度问答
    5. 证据册生成：自动生成符合法院要求的证据册
    6. 证据风险分析：识别不利证据、存疑证据
    """

    # 供外部访问的类型定义
    EVIDENCE_TYPES = EvidenceServiceV2.EVIDENCE_TYPES
    RELATIONSHIP_TYPES = EvidenceServiceV2.RELATIONSHIP_TYPES

    def __init__(self):
        self._v2: Optional[EvidenceServiceV2] = None
        self._graph: Optional[EvidenceGraphBuilder] = None
        self._navigator: Optional[EvidenceNavigator] = None
        self._generator: Optional[EvidenceBookGenerator] = None
        self._risk_analyzer: Optional[EvidenceRiskAnalyzer] = None

    @property
    def v2(self) -> EvidenceServiceV2:
        if self._v2 is None:
            self._v2 = _evidence_v2
        return self._v2

    @property
    def graph(self) -> EvidenceGraphBuilder:
        if self._graph is None:
            self._graph = _eg_builder
        return self._graph

    @property
    def navigator(self) -> EvidenceNavigator:
        if self._navigator is None:
            self._navigator = _navigator
        return self._navigator

    @property
    def generator(self) -> EvidenceBookGenerator:
        """证据册生成器"""
        if self._generator is None:
            self._generator = EvidenceBookGenerator()
        return self._generator

    @property
    def risk_analyzer(self) -> EvidenceRiskAnalyzer:
        """证据风险分析器"""
        if self._risk_analyzer is None:
            self._risk_analyzer = EvidenceRiskAnalyzer()
        return self._risk_analyzer

    # ==================== V2 核心处理流程 ====================

    def process_evidence(
        self,
        case_id: int,
        source_type: str = "file",
        content: str = None,
        file_path: str = None,
        original_filename: str = None,
        source_party: str = "己方",
        metadata: dict = None
    ) -> dict:
        """
        完整的证据处理流程（V2 引擎）

        包括：去重检查 → 智能分类 → 信度评估 → 关系分析 → 存储

        Args:
            case_id: 案件ID
            source_type: 来源类型 (file/text/input)
            content: 文本内容
            file_path: 文件路径
            original_filename: 原始文件名
            source_party: 来源方 (己方/对方/第三方/法院)
            metadata: 其他元数据

        Returns:
            处理结果（含证据ID、类型、信度、去重状态等）
        """
        return self.v2.process_evidence(
            case_id=case_id,
            source_type=source_type,
            content=content,
            file_path=file_path,
            original_filename=original_filename,
            source_party=source_party,
            metadata=metadata
        )

    def get_case_evidence(
        self,
        case_id: int,
        include_relationships: bool = True,
        include_analysis: bool = True
    ) -> List[Dict[str, Any]]:
        """获取案件全部证据（含关系和分析）"""
        return self.v2.get_case_evidence(case_id, include_relationships, include_analysis)

    def analyze_evidence_relationships(
        self,
        evidence_ids: List[int],
        case_id: int
    ) -> Dict[str, Any]:
        """分析证据之间的关系（支持/矛盾/补充/派生/依赖）"""
        return self.v2.analyze_relationships(evidence_ids, case_id)

    def check_duplicates(
        self,
        case_id: int,
        content: str = None,
        file_path: str = None
    ) -> Dict[str, Any]:
        """检查证据是否重复"""
        return self.v2._check_duplicate(None, case_id, content, file_path)

    def update_evidence_status(
        self,
        evidence_id: int,
        new_status: str
    ) -> Dict[str, Any]:
        """更新证据状态"""
        return self.v2.update_status(evidence_id, new_status)

    def get_evidence_statistics(self, case_id: int) -> Dict[str, Any]:
        """获取案件证据统计（类型分布、信度分布、关系统计）"""
        return self.v2.get_statistics(case_id)

    # ==================== 图谱构建 ====================

    def build_graph(
        self,
        case_id: int,
        case_type: str = ""
    ) -> Dict[str, Any]:
        """
        构建案件证据图谱

        Returns:
            图谱数据（节点、事实、缺口、关系、统计）
        """
        graph = self.graph.get_or_create_graph(case_id, case_type)
        return graph.to_dict()

    def add_to_graph(
        self,
        case_id: int,
        evidence_id: int,
        name: str,
        evidence_type: str,
        content: str,
        source: str = "",
        custody: str = "",
        uploaded_at: str = ""
    ) -> Dict[str, Any]:
        """添加证据到图谱（自动处理去重/关键词/信度分析）"""
        return self.graph.add_evidence(
            case_id=case_id,
            evidence_id=evidence_id,
            name=name,
            evidence_type=evidence_type,
            content=content,
            source=source,
            custody=custody,
            uploaded_at=uploaded_at
        )

    def get_graph_data(
        self,
        case_id: int,
        view_type: str = "default"
    ) -> Dict[str, Any]:
        """
        获取图谱可视化数据

        Args:
            case_id: 案件ID
            view_type: default | simplified | detailed

        Returns:
            适合前端可视化的图谱数据
        """
        return self.graph.get_graph_data(case_id, view_type)

    def discover_gaps(self, case_id: int) -> List[Dict[str, Any]]:
        """发现证据缺口"""
        return self.graph.discover_gaps(case_id)

    def search_graph(
        self,
        case_id: int,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """图谱关键词搜索"""
        return self.graph.search_by_keyword(case_id, keyword)

    def get_proof_chain(
        self,
        case_id: int,
        fact: str
    ) -> List[Dict[str, Any]]:
        """获取某事实的完整证明链"""
        return self.graph.get_proof_chain(case_id, fact)

    # ==================== 主动引导 ====================

    def diagnose_case(
        self,
        case_info: Dict[str, Any],
        evidence_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        诊断案件证据状态（像体检一样全面检查）

        Args:
            case_info: 案件信息（包含 id, case_type, claims 等）
            evidence_list: 已有证据列表

        Returns:
            诊断报告（含评分、缺口、关键发现、立即行动等）
        """
        diagnosis = self.navigator.diagnose_case(case_info, evidence_list)
        return diagnosis.to_dict() if hasattr(diagnosis, "to_dict") else diagnosis

    def get_next_guidance(self, case_info: Dict, answered_questions: List[str]) -> Dict[str, Any]:
        """获取下一步引导问题"""
        return self.navigator.get_next_question(case_info, answered_questions)

    # ==================== 证据册 ====================

    def generate_evidence_book(
        self,
        case_id: int,
        evidence_ids: List[int] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        生成证据册

        Args:
            case_id: 案件ID
            evidence_ids: 指定证据ID列表（None表示全部）
            format: 输出格式 (json/markdown/html)

        Returns:
            证据册内容
        """
        return self.v2.generate_evidence_book(case_id, evidence_ids, format)

    def export_evidence_list(
        self,
        case_id: int,
        evidence_ids: List[int] = None
    ) -> Dict[str, Any]:
        """导出证据目录（符合法院格式）"""
        return self.v2.export_evidence_list(case_id, evidence_ids)

    # ==================== 完整性检查 ====================

    def check_completeness(self, case_id: int) -> Dict[str, Any]:
        """检查证据完整性"""
        return self.v2.check_completeness(case_id)

    def suggest_additional_evidence(self, case_id: int) -> List[Dict[str, Any]]:
        """建议补充的证据"""
        return self.v2.suggest_additional_evidence(case_id)


# 单例
evidence_service = EvidenceService()
