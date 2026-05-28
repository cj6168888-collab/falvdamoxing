"""Tenant authentication and request context middleware."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock
import time

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.tenant_context import TenantContext
from app.db.database import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.services.jwt_auth_service import jwt_auth_service


PUBLIC_API_PREFIXES = (
    "/api/auth",
)

PUBLIC_PATHS = {
    "/",
    "/health",
    "/ready",
    "/metrics",
    "/openapi.json",
    "/api/smart-chat/health",
    "/api/third-party/health",
    "/api/llm/health",
}

PUBLIC_DOC_PREFIXES = (
    "/docs",
    "/redoc",
)


@dataclass(frozen=True)
class _AuthenticatedContext:
    user_id: str
    tenant_id: str


_AUTH_CONTEXT_CACHE: dict[str, tuple[float, _AuthenticatedContext]] = {}
_AUTH_CONTEXT_CACHE_LOCK = Lock()


def _clear_auth_context_cache() -> None:
    with _AUTH_CONTEXT_CACHE_LOCK:
        _AUTH_CONTEXT_CACHE.clear()


def _get_cached_auth_context(user_id: str) -> _AuthenticatedContext | None:
    ttl_seconds = max(settings.auth_context_cache_seconds, 0)
    if ttl_seconds <= 0:
        return None

    now = time.monotonic()
    with _AUTH_CONTEXT_CACHE_LOCK:
        cached = _AUTH_CONTEXT_CACHE.get(user_id)
        if not cached:
            return None
        expires_at, context = cached
        if expires_at <= now:
            _AUTH_CONTEXT_CACHE.pop(user_id, None)
            return None
        return context


def _set_cached_auth_context(context: _AuthenticatedContext) -> None:
    ttl_seconds = max(settings.auth_context_cache_seconds, 0)
    if ttl_seconds <= 0:
        return

    expires_at = time.monotonic() + ttl_seconds
    with _AUTH_CONTEXT_CACHE_LOCK:
        _AUTH_CONTEXT_CACHE[context.user_id] = (expires_at, context)


def _should_authenticate(path: str, method: str) -> bool:
    if method.upper() == "OPTIONS":
        return False
    if path in PUBLIC_PATHS:
        return False
    if any(path.startswith(prefix) for prefix in PUBLIC_DOC_PREFIXES):
        return False
    if any(path.startswith(prefix) for prefix in PUBLIC_API_PREFIXES):
        return False
    return path.startswith("/api")


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


def configure_tenant_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def tenant_middleware(request: Request, call_next):
        TenantContext.clear()
        path = request.url.path
        if not _should_authenticate(path, request.method):
            try:
                return await call_next(request)
            finally:
                TenantContext.clear()

        token = _extract_bearer_token(request)
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "未提供认证令牌"},
            )

        payload = jwt_auth_service.verify_token(token)
        if not payload or payload.get("type") != "access":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "无效或已过期的令牌"},
            )

        user_id = str(payload.get("user_id") or "")
        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "无效的令牌载荷"},
            )

        auth_context = _get_cached_auth_context(user_id)
        if auth_context is None:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.is_active:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "用户不可用"},
                    )

                tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
                if not tenant or not tenant.is_active:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "租户不可用"},
                    )

                if not user.is_platform_admin:
                    if tenant.approval_status and tenant.approval_status != "approved":
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": "租户尚未通过审批"},
                        )
                    if tenant.billing_due_date and tenant.billing_due_date < datetime.utcnow():
                        return JSONResponse(
                            status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            content={"detail": f"账户已到期（{tenant.billing_due_date.strftime('%Y-%m-%d')}），请续费。"},
                        )

                auth_context = _AuthenticatedContext(
                    user_id=user.id,
                    tenant_id=user.tenant_id,
                )
                _set_cached_auth_context(auth_context)
            finally:
                db.close()

        TenantContext.set_tenant(auth_context.tenant_id)
        TenantContext.set_user(auth_context.user_id)
        request.state.tenant_id = auth_context.tenant_id
        request.state.user_id = auth_context.user_id

        try:
            return await call_next(request)
        finally:
            TenantContext.clear()
