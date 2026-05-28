from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String

from app.db.database import Base


class AIRetrievalAudit(Base):
    """Audit record for tenant-scoped retrieval context passed toward AI calls."""

    __tablename__ = "ai_retrieval_audits"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    user_id = Column(String(200), index=True, nullable=True)
    case_id = Column(Integer, index=True, nullable=True)
    purpose = Column(String(100), index=True, nullable=False, default="rag_search")
    query_hash = Column(String(64), nullable=False)
    query_preview = Column(String(200), nullable=True)
    retrieved_document_ids = Column(JSON, nullable=True)
    retrieved_chunk_ids = Column(JSON, nullable=True)
    source_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
