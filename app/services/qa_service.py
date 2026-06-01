"""
统一问答服务 (QA Service Facade)
================================
整合三个问答子服务，为API层提供统一的问答入口：
- RAGService: 文档检索增强生成
- SmartQAServiceV2: 智能多轮对话（意图识别 + 澄清机制）
- EvidenceQA: 单条证据深度问答 + 防跑偏机制

Facade 模式：对现有服务零侵入，渐进式合并
"""

from typing import Optional, List, Dict, Any

from app.services.rag_service import RAGService, rag_service as _rag_service
from app.services.smart_qa_v2 import SmartQAServiceV2, smart_qa_service_v2 as _smart_qa_v2
from app.services.evidence_qa import EvidenceQAAntiDeviation


class QAService:
    """
    统一问答服务 Facade

    对外提供三类问答能力：
    1. 基础RAG问答（基于文档检索）
    2. 智能多轮对话（意图识别 + 澄清引导）
    3. 证据专项问答（单条证据深度分析 + 防跑偏）
    """

    def __init__(self):
        # 延迟初始化，避免循环导入
        self._rag: Optional[RAGService] = None
        self._smart_qa: Optional[SmartQAServiceV2] = None

    @property
    def rag(self) -> RAGService:
        if self._rag is None:
            self._rag = _rag_service
        return self._rag

    @property
    def smart_qa(self) -> SmartQAServiceV2:
        if self._smart_qa is None:
            self._smart_qa = _smart_qa_v2
        return self._smart_qa

    # ==================== RAG 基础能力 ====================

    def add_document(
        self,
        case_id: int,
        doc_id: int,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加文档到知识库"""
        return self.rag.add_document(case_id, doc_id, text, metadata)

    def search_documents(
        self,
        query: str,
        case_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """检索相关文档"""
        return self.rag.search(query, case_id=case_id, top_k=top_k)

    def get_context(
        self,
        query: str,
        case_id: int,
        max_length: int = 50000
    ) -> str:
        """获取RAG上下文字符串"""
        return self.rag.get_context(query, case_id, max_length)

    def chat_with_context(
        self,
        query: str,
        case_info: str,
        case_id: int
    ) -> str:
        """基于上下文的基础RAG对话"""
        return self.rag.chat_with_context(query, case_info, case_id)

    def delete_case_documents(self, case_id: int) -> None:
        """删除案件的所有文档"""
        self.rag.delete_case_documents(case_id)

    # ==================== 智能多轮对话 ====================

    def ask(
        self,
        question: str,
        case_id: int,
        session_id: Optional[str] = None,
        user_context: Optional[dict] = None
    ) -> dict:
        """
        智能问答入口（V2）

        支持意图识别、澄清机制、多轮对话、证据缺口检测。
        根据问题清晰度自动选择：
        - 直接回答（清晰问题）
        - 部分回答 + 澄清引导（半清晰问题）
        - 系统性澄清引导（模糊问题）

        Args:
            question: 用户问题
            case_id: 案件ID
            session_id: 会话ID（多轮对话）
            user_context: 用户上下文

        Returns:
            回答结果（含意图、置信度、证据缺口建议等）
        """
        return self.smart_qa.ask(question, case_id, session_id, user_context)

    def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话详情（含消息历史）"""
        return self.smart_qa.get_session(session_id)

    def resolve_clarification(
        self,
        session_id: str,
        clarification_id: str,
        answer: str
    ) -> dict:
        """处理澄清回答，继续原问题的分析"""
        return self.smart_qa.resolve_clarification(session_id, clarification_id, answer)

    def get_conversation_history(
        self,
        case_id: int,
        limit: int = 20
    ) -> List[dict]:
        """获取案件的对话历史"""
        return self.smart_qa.get_conversation_history(case_id, limit)

    # ==================== 证据专项问答 ====================

    def ask_evidence(
        self,
        evidence_id: str,
        question: str,
        evidence_content: str,
        case_id: int,
        evidence_type: str = "",
        evidence_name: str = "",
        case_type: str = "",
        proves_facts: Optional[List[str]] = None,
        credibility_score: float = 0.0
    ) -> dict:
        """
        单条证据深度问答

        针对特定证据的专项问答，带防跑偏机制。

        Args:
            evidence_id: 证据ID
            question: 用户问题
            evidence_content: 证据文本内容
            case_id: 案件ID
            evidence_type: 证据类型
            evidence_name: 证据名称
            case_type: 案件类型
            proves_facts: 该证据证明的事实
            credibility_score: 证据证明力参考

        Returns:
            问答结果（含跑偏检测、话题引导等）
        """
        from app.services.evidence_qa import EvidenceQuestionContext
        ctx = EvidenceQuestionContext(
            evidence_id=evidence_id,
            evidence_name=evidence_name or f"证据{evidence_id}",
            evidence_type=evidence_type,
            evidence_content=evidence_content,
            case_id=case_id,
            case_type=case_type,
            proves_facts=proves_facts or [],
            credibility_score=credibility_score
        )
        qa = EvidenceQAAntiDeviation(ctx)
        return qa.ask(question)

    # ==================== 意图识别（工具方法） ====================

    def classify_intent(self, question: str) -> str:
        """快速识别问题意图（同步版本）"""
        return self.smart_qa._classify_intent_sync(question)

    @property
    def intent_taxonomy(self) -> dict:
        """意图分类体系定义"""
        return self.smart_qa.INTENT_TAXONOMY


# 单例
qa_service = QAService()
