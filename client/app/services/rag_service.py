"""
Document RAG service.

ChromaDB is an optional runtime dependency. The API should still start and core
document workflows should still work when vector search is not installed.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.tenant_context import TenantContext
from app.services.ai_audit_service import record_retrieval_audit
from app.services.embed_service import embedding_service
from app.services.llm_service import llm_service

try:
    import chromadb

    CHROMADB_AVAILABLE = True
    CHROMADB_IMPORT_ERROR: Optional[BaseException] = None
except Exception as exc:  # pragma: no cover - depends on installed runtime extras
    chromadb = None
    CHROMADB_AVAILABLE = False
    CHROMADB_IMPORT_ERROR = exc


logger = logging.getLogger(__name__)


class RAGService:
    """RAG service backed by ChromaDB when available."""

    def __init__(self, audit_recorder=record_retrieval_audit):
        self.chroma_client = None
        self.collection = None
        self._audit_recorder = audit_recorder

        if not CHROMADB_AVAILABLE:
            logger.warning(
                "ChromaDB is not available; document vector indexing and RAG "
                "retrieval are disabled. Install requirements-optional.txt to enable it.",
                exc_info=CHROMADB_IMPORT_ERROR,
            )
            return

        try:
            self.chroma_client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name="legal_documents",
                metadata={"description": "Legal document knowledge base"},
            )
        except Exception:
            logger.exception(
                "Failed to initialize ChromaDB; document vector indexing and RAG retrieval are disabled."
            )
            self.chroma_client = None
            self.collection = None

    @property
    def is_available(self) -> bool:
        """Return whether the vector store backend is ready for use."""
        return self.collection is not None

    def add_document(
        self,
        case_id: int,
        doc_id: int,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a document to the vector knowledge base."""
        if not self.is_available:
            logger.info(
                "Skipping vector indexing for document %s in case %s because ChromaDB is unavailable.",
                doc_id,
                case_id,
            )
            return ""

        vector_id = str(uuid.uuid4())
        chunks = self._chunk_text(text)
        tenant_id = TenantContext.get_tenant_id()

        for i, chunk in enumerate(chunks):
            chunk_id = f"{vector_id}_{i}"
            embedding = embedding_service.embed_query(chunk)
            chunk_metadata = {
                "case_id": case_id,
                "doc_id": doc_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {}),
            }
            if tenant_id:
                chunk_metadata["tenant_id"] = tenant_id

            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[chunk_metadata],
            )

        return vector_id

    def search(
        self,
        query: str,
        case_id: Optional[int] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search related document chunks."""
        if not self.is_available:
            self._record_audit(query=query, case_id=case_id, results=[])
            return []

        query_embedding = embedding_service.embed_query(query)
        tenant_id = TenantContext.get_tenant_id()
        where_clauses = []
        if case_id:
            where_clauses.append({"case_id": case_id})
        if tenant_id:
            where_clauses.append({"tenant_id": tenant_id})
        if len(where_clauses) == 1:
            where_filter = where_clauses[0]
        elif len(where_clauses) > 1:
            where_filter = {"$and": where_clauses}
        else:
            where_filter = None
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        formatted_results = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                metadata = results["metadatas"][0][i] or {}
                if not self._result_matches_scope(metadata, case_id, tenant_id):
                    logger.warning(
                        "Discarded out-of-scope RAG result: requested case=%s tenant=%s metadata=%s",
                        case_id,
                        tenant_id,
                        metadata,
                    )
                    continue
                formatted_results.append(
                    {
                        "id": doc_id,
                        "content": results["documents"][0][i],
                        "metadata": metadata,
                        "distance": distance,
                        "similarity": 1 - distance,
                    }
                )

        self._record_audit(query=query, case_id=case_id, results=formatted_results)
        return formatted_results

    @staticmethod
    def _result_matches_scope(
        metadata: Dict[str, Any],
        case_id: Optional[int],
        tenant_id: Optional[str],
    ) -> bool:
        if case_id is not None and metadata.get("case_id") != case_id:
            return False
        if tenant_id and metadata.get("tenant_id") != tenant_id:
            return False
        return True

    def _record_audit(
        self,
        *,
        query: str,
        case_id: Optional[int],
        results: List[Dict[str, Any]],
    ) -> None:
        if not self._audit_recorder:
            return
        try:
            self._audit_recorder(
                query=query,
                case_id=case_id,
                results=results,
                purpose="rag_search",
            )
        except Exception:
            logger.warning("Failed to record RAG retrieval audit.", exc_info=True)

    def delete_case_documents(self, case_id: int) -> None:
        """Delete all indexed documents for a case."""
        if not self.is_available:
            return

        tenant_id = TenantContext.get_tenant_id()
        where_filter: Dict[str, Any]
        if tenant_id:
            where_filter = {"$and": [{"case_id": case_id}, {"tenant_id": tenant_id}]}
        else:
            where_filter = {"case_id": case_id}

        self.collection.delete(where=where_filter)

    def get_context(self, query: str, case_id: int, max_length: int = 50000) -> str:
        """Return retrieved context for LLM calls."""
        results = self.search(query, case_id=case_id, top_k=10)

        context = ""
        for result in results:
            content = result["content"]
            if len(context) + len(content) > max_length:
                break

            metadata = result["metadata"]
            source = metadata.get("doc_type", "document")
            doc_id = metadata.get("doc_id", "unknown")
            context += f"\n\n[Source: {source}; doc_id={doc_id}]\n"
            context += content

        return context.strip()

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 5000,
        overlap: int = 500,
    ) -> List[str]:
        """Split text into overlapping chunks while preserving context."""
        sentences = text.replace("\r\n", "\n").split("\n")
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = current_chunk[-overlap:] + sentence
            else:
                current_chunk += "\n" + sentence

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return [chunk for chunk in chunks if chunk.strip()]

    def chat_with_context(
        self,
        query: str,
        case_info: str,
        case_id: int,
    ) -> str:
        """Answer a question with retrieved case document context when available."""
        context = self.get_context(query, case_id)

        system_prompt = """你是一位专业的中国法律顾问，基于案件材料和知识库为用户提供法律分析和建议。

要求：
1. 结合提供的材料回答，不要凭空编造。
2. 如果材料中没有相关信息，请明确说明。
3. 引用材料时标注来源。
4. 提供专业、准确的法律意见。"""

        user_content = f"[案件基本信息]\n{case_info}\n\n"
        if context:
            user_content += f"[相关材料]\n{context}\n\n"
        user_content += f"[用户问题]\n{query}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        return llm_service.chat(messages)


_rag_service = None


def get_rag_service():
    """Return the lazily initialized RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


class RAGServiceProxy:
    """Lazy-loading proxy for route modules."""

    def __getattr__(self, name):
        return getattr(get_rag_service(), name)


rag_service = RAGServiceProxy()
