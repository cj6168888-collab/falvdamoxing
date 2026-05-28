"""
认证依赖 - FastAPI 依赖注入
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.user import User
from app.services.jwt_auth_service import jwt_auth_service
from app.core.tenant_context import TenantContext

security = HTTPBearer(auto_error=False)


def decode_token(token: str) -> Optional[dict]:
    return jwt_auth_service.verify_token(token)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = None
    if credentials:
        token = credentials.credentials
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
        )

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的令牌",
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌载荷",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号已被停用",
        )

    TenantContext.set_tenant(user.tenant_id)
    TenantContext.set_user(user.id)
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


def require_role(*roles):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in [r.value if hasattr(r, "value") else r for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return current_user
    return role_checker


async def check_ai_quota(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """验证当前租户的 AI 配额，配额耗尽时返回 429。"""
    from app.services.quota_service import quota_service

    quota = quota_service.check_quota(db, current_user.tenant_id)
    if not quota["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=quota["message"],
        )
    return current_user


class TenantIsolation:
    """纵深防御 — 显式验证数据属于当前租户。

    用法: Depends(TenantIsolation.check)
    """
    @staticmethod
    def check(current_user: User = Depends(get_current_user)):
        """返回一个验证函数，调用方用它检查对象的 tenant_id。"""
        return lambda obj, name="数据": TenantIsolation._verify(obj, current_user, name)

    @staticmethod
    def _verify(obj, user: User, name: str = "数据"):
        """显式检查对象的 tenant_id 是否匹配当前用户。"""
        if obj is None:
            return
        obj_tenant = getattr(obj, "tenant_id", None)
        if obj_tenant is not None and obj_tenant != user.tenant_id:
            from fastapi import HTTPException as HE
            raise HE(status_code=403, detail=f"{name}不属于您的租户")
