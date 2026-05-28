"""
租户上下文 - 线程/协程安全的租户信息存储
"""
from contextvars import ContextVar
from typing import Optional

_tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
_user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class TenantContext:
    @staticmethod
    def set_tenant(tenant_id: str) -> None:
        _tenant_id_var.set(tenant_id)

    @staticmethod
    def get_tenant_id() -> Optional[str]:
        return _tenant_id_var.get()

    @staticmethod
    def set_user(user_id: str) -> None:
        _user_id_var.set(user_id)

    @staticmethod
    def get_user_id() -> Optional[str]:
        return _user_id_var.get()

    @staticmethod
    def clear() -> None:
        _tenant_id_var.set(None)
        _user_id_var.set(None)
