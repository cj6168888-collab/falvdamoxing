"""
租户管理 API — SaaS 多租户核心

- 租户信息查看/编辑（仅管理员）
- 团队成员管理（邀请、删除、角色变更）
- 使用量统计
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
import secrets

from app.db.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType, SubscriptionPlan, SubscriptionStatus

router = APIRouter(prefix="/api/tenant", tags=["租户管理"])


# ========== 请求/响应模型 ==========

class TenantProfileResponse(BaseModel):
    id: str
    name: str
    tenant_type: str
    slug: str
    plan: str
    subscription_status: str
    max_users: int
    max_cases: int
    max_storage_gb: int
    ai_daily_quota: int
    ai_monthly_usage: int
    is_active: bool
    is_verified: bool
    created_at: Optional[str] = None


class TenantUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class TeamMemberResponse(BaseModel):
    id: str
    username: str
    email: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_email_verified: bool
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None


class InviteRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = Field(default="assistant", description="admin/lawyer/assistant/viewer")


class InviteResponse(BaseModel):
    success: bool
    message: str
    invite_code: Optional[str] = None


class ChangeRoleRequest(BaseModel):
    user_id: str
    role: str = Field(..., description="admin/lawyer/assistant/client/viewer")


class UsageStatsResponse(BaseModel):
    tenant_id: str
    total_users: int
    active_users: int
    total_cases: int
    ai_calls_today: int
    ai_calls_this_month: int
    ai_daily_quota: int
    ai_monthly_usage: int
    storage_used_mb: float


class SimpleResponse(BaseModel):
    success: bool
    message: str


# ========== 辅助函数 ==========

def _tenant_admin(user: User = Depends(require_role("admin"))):
    """仅租户管理员可访问"""
    return user


def _parse_role(role_str: str) -> UserRole:
    try:
        return UserRole(role_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色: {role_str}。可用: {[r.value for r in UserRole]}",
        )


# ========== 租户信息 ==========

@router.get("/profile", response_model=TenantProfileResponse)
def get_tenant_profile(
    admin: User = Depends(_tenant_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == admin.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    return TenantProfileResponse(
        id=tenant.id,
        name=tenant.name,
        tenant_type=tenant.tenant_type.value if tenant.tenant_type else "",
        slug=tenant.slug,
        plan=tenant.plan.value if tenant.plan else "free",
        subscription_status=tenant.subscription_status.value if tenant.subscription_status else "active",
        max_users=tenant.max_users,
        max_cases=tenant.max_cases,
        max_storage_gb=tenant.max_storage_gb,
        ai_daily_quota=tenant.ai_daily_quota,
        ai_monthly_usage=tenant.ai_monthly_usage,
        is_active=tenant.is_active,
        is_verified=tenant.is_verified,
        created_at=tenant.created_at.isoformat() if tenant.created_at else None,
    )


@router.put("/profile", response_model=SimpleResponse)
def update_tenant_profile(
    req: TenantUpdateRequest,
    admin: User = Depends(_tenant_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == admin.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    if req.name:
        tenant.name = req.name
    if req.description is not None:
        tenant.description = req.description
    tenant.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": "租户信息已更新"}


# ========== 团队成员管理 ==========

@router.get("/members", response_model=List[TeamMemberResponse])
def list_team_members(
    admin: User = Depends(_tenant_admin),
    db: Session = Depends(get_db),
):
    members = (
        db.query(User)
        .filter(User.tenant_id == admin.tenant_id)
        .order_by(User.created_at.asc())
        .all()
    )
    return [
        TeamMemberResponse(
            id=m.id,
            username=m.username,
            email=m.email,
            phone=m.phone,
            full_name=m.full_name,
            role=m.role.value if m.role else "assistant",
            is_active=m.is_active,
            is_email_verified=m.is_email_verified,
            last_login_at=m.last_login_at.isoformat() if m.last_login_at else None,
            created_at=m.created_at.isoformat() if m.created_at else None,
        )
        for m in members
    ]


@router.post("/members/invite", response_model=InviteResponse)
def invite_member(
    req: InviteRequest,
    admin: User = Depends(_tenant_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == admin.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    current_count = db.query(User).filter(User.tenant_id == admin.tenant_id).count()
    if current_count >= (tenant.max_users or 3):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"已到达用户上限（{tenant.max_users}人）。请升级套餐。",
        )

    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        if existing.tenant_id == admin.tenant_id:
            raise HTTPException(status_code=400, detail="该邮箱已是团队成员")
        raise HTTPException(status_code=400, detail="该邮箱已注册其他租户")

    role = _parse_role(req.role)
    invite_code = secrets.token_urlsafe(16)

    temp_password = secrets.token_urlsafe(12)
    user_id = secrets.token_urlsafe(16)
    password_hash = type(jwt_auth_service)._hash_password(temp_password)

    from app.services.jwt_auth_service import jwt_auth_service

    user = User(
        id=user_id,
        tenant_id=admin.tenant_id,
        username=f"invite-{secrets.token_hex(4)}",
        email=req.email,
        password_hash=password_hash,
        full_name=req.full_name,
        role=role,
        is_active=True,
        is_email_verified=False,
    )
    db.add(user)
    db.commit()

    return {
        "success": True,
        "message": f"已邀请 {req.email}。告知其使用邮箱登录，初始密码: {temp_password}",
        "invite_code": invite_code,
    }


@router.put("/members/role", response_model=SimpleResponse)
def change_member_role(
    req: ChangeRoleRequest,
    admin: User = Depends(_tenant_admin),
    db: Session = Depends(get_db),
):
    if req.user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")

    member = (
        db.query(User)
        .filter(User.id == req.user_id, User.tenant_id == admin.tenant_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="团队成员不存在")

    member.role = _parse_role(req.role)
    member.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": f"已将 {member.username} 的角色更新为 {req.role}"}


@router.delete("/members/{user_id}", response_model=SimpleResponse)
def remove_member(
    user_id: str,
    admin: User = Depends(_tenant_admin),
    db: Session = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    member = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == admin.tenant_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="团队成员不存在")

    db.delete(member)
    db.commit()
    return {"success": True, "message": f"已移除 {member.username}"}


# ========== 使用量统计 ==========

@router.get("/usage", response_model=UsageStatsResponse)
def get_usage_stats(
    admin: User = Depends(_tenant_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == admin.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    members = db.query(User).filter(User.tenant_id == admin.tenant_id).all()
    total_users = len(members)
    active_users = sum(1 for m in members if m.is_active)

    from app.models.case import Case
    total_cases = db.query(Case).filter(Case.tenant_id == admin.tenant_id).count()

    from app.models.ai_audit import AIRetrievalAudit
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ai_calls_today = (
        db.query(AIRetrievalAudit)
        .filter(
            AIRetrievalAudit.tenant_id == admin.tenant_id,
            AIRetrievalAudit.created_at >= today_start,
        )
        .count()
    )

    month_start = today_start.replace(day=1)
    ai_calls_this_month = (
        db.query(AIRetrievalAudit)
        .filter(
            AIRetrievalAudit.tenant_id == admin.tenant_id,
            AIRetrievalAudit.created_at >= month_start,
        )
        .count()
    )

    data_dir_size = 0.0
    import os
    data_path = "data"
    if os.path.exists(data_path):
        for root, _, files in os.walk(data_path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    data_dir_size += os.path.getsize(fp)
                except OSError:
                    pass

    return UsageStatsResponse(
        tenant_id=admin.tenant_id,
        total_users=total_users,
        active_users=active_users,
        total_cases=total_cases,
        ai_calls_today=ai_calls_today,
        ai_calls_this_month=ai_calls_this_month,
        ai_daily_quota=tenant.ai_daily_quota or 100,
        ai_monthly_usage=tenant.ai_monthly_usage or 0,
        storage_used_mb=round(data_dir_size / (1024 * 1024), 2),
    )
