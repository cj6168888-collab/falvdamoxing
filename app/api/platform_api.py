"""
平台超管 API — 管理所有租户、审批注册、计费管理
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.tenant import Tenant, TenantType, SubscriptionPlan, SubscriptionStatus

router = APIRouter(prefix="/api/platform", tags=["平台管理"])


def _require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    if not getattr(current_user, "is_platform_admin", False):
        raise HTTPException(status_code=403, detail="仅平台超级管理员可访问")
    return current_user


# ===== 响应模型 =====

class TenantDetail(BaseModel):
    id: str
    name: str
    tenant_type: str
    slug: str
    plan: str
    subscription_status: str
    approval_status: str
    billing_cycle: str
    billing_amount: int
    billing_due_date: Optional[str] = None
    max_users: int
    max_cases: int
    ai_daily_quota: int
    ai_monthly_usage: int
    is_active: bool
    registered_from: Optional[str] = None
    created_at: Optional[str] = None
    user_count: int = 0

    class Config:
        from_attributes = True


class ApproveRequest(BaseModel):
    tenant_id: str
    plan: str = Field(default="trial")
    billing_cycle: str = Field(default="monthly")
    billing_amount: int = Field(default=0)
    max_users: int = Field(default=10)
    max_cases: int = Field(default=50)
    ai_daily_quota: int = Field(default=100)


class RejectRequest(BaseModel):
    tenant_id: str
    reason: str = Field(..., min_length=1)


class BillingUpdateRequest(BaseModel):
    tenant_id: str
    billing_cycle: str = Field(default="monthly")
    billing_amount: int = Field(..., ge=0)
    billing_due_date: Optional[str] = None


class PlatformStats(BaseModel):
    total_tenants: int
    pending_approvals: int
    active_tenants: int
    total_users: int
    total_revenue_monthly: int
    ai_calls_today: int


class SimpleResponse(BaseModel):
    success: bool
    message: str


# ===== 路由 =====

@router.get("/stats", response_model=PlatformStats)
def get_platform_stats(
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    tenants = db.query(Tenant).all()
    from app.models.user import User as U
    from app.models.ai_audit import AIRetrievalAudit

    total_users = db.query(U).count()
    pending = sum(1 for t in tenants if t.approval_status == "pending")
    active = sum(1 for t in tenants if t.approval_status == "approved" and t.is_active)
    monthly_revenue = sum(t.billing_amount or 0 for t in tenants if t.approval_status == "approved")

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ai_today = db.query(AIRetrievalAudit).filter(AIRetrievalAudit.created_at >= today_start).count()

    return PlatformStats(
        total_tenants=len(tenants),
        pending_approvals=pending,
        active_tenants=active,
        total_users=total_users,
        total_revenue_monthly=monthly_revenue,
        ai_calls_today=ai_today,
    )


@router.get("/tenants", response_model=List[TenantDetail])
def list_all_tenants(
    status_filter: Optional[str] = Query(None, alias="status"),
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Tenant)
    if status_filter:
        query = query.filter(Tenant.approval_status == status_filter)
    tenants = query.order_by(Tenant.created_at.desc()).all()

    from app.models.user import User as U
    result = []
    for t in tenants:
        user_count = db.query(U).filter(U.tenant_id == t.id).count()
        result.append(TenantDetail(
            id=t.id,
            name=t.name,
            tenant_type=t.tenant_type.value if t.tenant_type else "",
            slug=t.slug,
            plan=t.plan.value if t.plan else "free",
            subscription_status=t.subscription_status.value if t.subscription_status else "active",
            approval_status=t.approval_status or "pending",
            billing_cycle=t.billing_cycle or "monthly",
            billing_amount=t.billing_amount or 0,
            billing_due_date=t.billing_due_date.isoformat() if t.billing_due_date else None,
            max_users=t.max_users or 3,
            max_cases=t.max_cases or 10,
            ai_daily_quota=t.ai_daily_quota or 100,
            ai_monthly_usage=t.ai_monthly_usage or 0,
            is_active=t.is_active,
            registered_from=t.registered_from,
            created_at=t.created_at.isoformat() if t.created_at else None,
            user_count=user_count,
        ))
    return result


@router.post("/tenants/approve", response_model=SimpleResponse)
def approve_tenant(
    req: ApproveRequest,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == req.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    tenant.approval_status = "approved"
    tenant.approved_at = datetime.utcnow()
    tenant.approved_by = admin.username
    tenant.plan = SubscriptionPlan(req.plan) if req.plan in [p.value for p in SubscriptionPlan] else SubscriptionPlan.TRIAL
    tenant.billing_cycle = req.billing_cycle
    tenant.billing_amount = req.billing_amount
    tenant.max_users = req.max_users
    tenant.max_cases = req.max_cases
    tenant.ai_daily_quota = req.ai_daily_quota
    tenant.billing_due_date = datetime.utcnow() + timedelta(days=30)
    db.commit()

    return {"success": True, "message": f"已批准 {tenant.name}，套餐: {req.plan}"}


@router.post("/tenants/reject", response_model=SimpleResponse)
def reject_tenant(
    req: RejectRequest,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == req.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    tenant.approval_status = "rejected"
    tenant.rejection_reason = req.reason
    db.commit()

    return {"success": True, "message": f"已拒绝 {tenant.name}"}


@router.put("/tenants/billing", response_model=SimpleResponse)
def update_billing(
    req: BillingUpdateRequest,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == req.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    tenant.billing_cycle = req.billing_cycle
    tenant.billing_amount = req.billing_amount
    if req.billing_due_date:
        tenant.billing_due_date = datetime.fromisoformat(req.billing_due_date)
    db.commit()

    return {"success": True, "message": f"已更新 {tenant.name} 的计费信息"}


@router.post("/tenants/{tenant_id}/toggle", response_model=SimpleResponse)
def toggle_tenant_active(
    tenant_id: str,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    tenant.is_active = not tenant.is_active
    db.commit()
    action = "启用" if tenant.is_active else "停用"
    return {"success": True, "message": f"已{action} {tenant.name}"}


class RecordPaymentRequest(BaseModel):
    tenant_id: str
    amount: float = Field(..., gt=0)
    billing_cycle: str = Field(default="monthly")
    payment_method: str = Field(default="manual")


class PaymentRecordResponse(BaseModel):
    id: int
    tenant_id: str
    amount: float
    billing_cycle: str
    payment_method: Optional[str] = None
    paid_at: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/tenants/payment", response_model=SimpleResponse)
def record_payment(
    req: RecordPaymentRequest,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    from app.services.billing_service import billing_service

    record = billing_service.record_payment(
        db, req.tenant_id, req.amount,
        billing_cycle=req.billing_cycle,
        payment_method=req.payment_method,
        created_by=admin.username,
    )
    return {"success": True, "message": f"已记录缴费 {record.amount}元 ({record.billing_cycle})"}


@router.get("/tenants/{tenant_id}/payments", response_model=List[PaymentRecordResponse])
def get_payment_history(
    tenant_id: str,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    from app.services.billing_service import billing_service
    records = billing_service.get_payment_history(db, tenant_id)
    return [
        PaymentRecordResponse(
            id=r.id, tenant_id=r.tenant_id, amount=r.amount,
            billing_cycle=r.billing_cycle, payment_method=r.payment_method,
            paid_at=r.paid_at.isoformat() if r.paid_at else None,
            period_start=r.period_start.isoformat() if r.period_start else None,
            period_end=r.period_end.isoformat() if r.period_end else None,
            status=r.status, notes=r.notes,
        )
        for r in records
    ]
