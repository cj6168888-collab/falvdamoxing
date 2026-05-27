"""
AI 配额服务 — SaaS 租户 AI 调用量追踪与限制

每次 AI 调用前检查日配额，调用后记录审计日志。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.ai_audit import AIRetrievalAudit
from app.models.tenant import Tenant


class QuotaService:
    """租户 AI 配额检查与使用量统计。"""

    @staticmethod
    def check_quota(
        db: Session,
        tenant_id: str,
        purpose: str = "ai_chat",
    ) -> dict:
        """在 AI 调用前检查配额。

        Returns:
            {"allowed": True/False, "used_today": N, "daily_limit": N, "message": "..."}
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return {"allowed": False, "used_today": 0, "daily_limit": 0, "message": "租户不存在"}

        daily_limit = tenant.ai_daily_quota or 100

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        used_today = (
            db.query(func.count(AIRetrievalAudit.id))
            .filter(
                AIRetrievalAudit.tenant_id == tenant_id,
                AIRetrievalAudit.created_at >= today_start,
            )
            .scalar()
        ) or 0

        if used_today >= daily_limit:
            return {
                "allowed": False,
                "used_today": used_today,
                "daily_limit": daily_limit,
                "message": f"今日 AI 调用次数已达上限（{daily_limit}次/天）。请明日再试或升级套餐。",
            }

        return {
            "allowed": True,
            "used_today": used_today,
            "daily_limit": daily_limit,
            "message": f"配额正常（{used_today}/{daily_limit}）",
        }

    @staticmethod
    def record_call(
        db: Session,
        *,
        tenant_id: str,
        user_id: Optional[str] = None,
        case_id: Optional[int] = None,
        purpose: str = "ai_chat",
        query_text: Optional[str] = None,
        source_count: int = 0,
    ) -> None:
        """记录一次 AI 调用审计日志并更新月使用量。"""
        query_hash = hashlib.sha256((query_text or "").encode()).hexdigest()[:64]
        query_preview = (query_text or "")[:200] if query_text else None

        audit = AIRetrievalAudit(
            tenant_id=tenant_id,
            user_id=user_id,
            case_id=case_id,
            purpose=purpose,
            query_hash=query_hash,
            query_preview=query_preview,
            source_count=source_count,
        )
        db.add(audit)

        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant:
            tenant.ai_monthly_usage = (tenant.ai_monthly_usage or 0) + 1

        db.commit()


quota_service = QuotaService()
