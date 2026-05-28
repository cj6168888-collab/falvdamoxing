"""AI retrieval audit helpers."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.core.tenant_context import TenantContext
from app.db.database import SessionLocal
from app.models.ai_audit import AIRetrievalAudit

logger = logging.getLogger(__name__)


def _unique(values: list[Any]) -> list[Any]:
    seen = set()
    result = []
    for value in values:
        if value is None:
            continue
        marker = str(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def build_retrieval_audit_payload(
    *,
    query: str,
    case_id: int | None,
    results: list[dict[str, Any]],
    purpose: str = "rag_search",
) -> dict[str, Any]:
    """Build a privacy-light audit payload for retrieved AI context."""

    document_ids: list[Any] = []
    chunk_ids: list[Any] = []
    for result in results:
        metadata = result.get("metadata") or {}
        document_ids.append(metadata.get("doc_id"))
        chunk_ids.append(result.get("id"))

    normalized_query = query or ""
    return {
        "tenant_id": TenantContext.get_tenant_id(),
        "user_id": TenantContext.get_user_id(),
        "case_id": case_id,
        "purpose": purpose,
        "query_hash": hashlib.sha256(normalized_query.encode("utf-8")).hexdigest(),
        "query_preview": normalized_query[:200],
        "retrieved_document_ids": _unique(document_ids),
        "retrieved_chunk_ids": _unique(chunk_ids),
        "source_count": len(results),
    }


def record_retrieval_audit(
    *,
    query: str,
    case_id: int | None,
    results: list[dict[str, Any]],
    purpose: str = "rag_search",
) -> None:
    """Persist retrieval audit data without breaking user-facing AI flows."""

    payload = build_retrieval_audit_payload(
        query=query,
        case_id=case_id,
        results=results,
        purpose=purpose,
    )

    db = SessionLocal()
    try:
        db.add(AIRetrievalAudit(**payload))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.warning("Failed to persist AI retrieval audit record.", exc_info=True)
    finally:
        db.close()
