from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI, Request

from app.core.tenant_context import TenantContext
from app.config import settings
from app.core.tenant_middleware import _clear_auth_context_cache, configure_tenant_middleware
from app.models.tenant import Tenant
from app.models.user import User


class _FakeQuery:
    def __init__(self, model):
        self.model = model

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        if self.model is User:
            return SimpleNamespace(id="user-1", tenant_id="tenant-1", is_active=True)
        if self.model is Tenant:
            return SimpleNamespace(id="tenant-1", is_active=True)
        return None


class _FakeSession:
    def __init__(self):
        self.closed = False

    def query(self, model):
        return _FakeQuery(model)

    def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_tenant_middleware_releases_auth_session_before_route(monkeypatch):
    _clear_auth_context_cache()
    monkeypatch.setattr(settings, "auth_context_cache_seconds", 10)
    sessions: list[_FakeSession] = []

    def fake_session_local():
        session = _FakeSession()
        sessions.append(session)
        return session

    monkeypatch.setattr(
        "app.core.tenant_middleware.SessionLocal",
        fake_session_local,
    )
    monkeypatch.setattr(
        "app.core.tenant_middleware.jwt_auth_service.verify_token",
        lambda _token: {"type": "access", "user_id": "user-1"},
    )

    app = FastAPI()
    configure_tenant_middleware(app)

    @app.get("/api/private")
    async def private_route(request: Request):
        assert sessions and sessions[0].closed
        return {
            "tenant_id": request.state.tenant_id,
            "tenant_context": TenantContext.get_tenant_id(),
        }

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/private",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": "tenant-1",
        "tenant_context": "tenant-1",
    }
    assert TenantContext.get_tenant_id() is None
    _clear_auth_context_cache()


@pytest.mark.asyncio
async def test_tenant_middleware_reuses_short_lived_auth_context(monkeypatch):
    _clear_auth_context_cache()
    monkeypatch.setattr(settings, "auth_context_cache_seconds", 10)
    sessions: list[_FakeSession] = []

    def fake_session_local():
        session = _FakeSession()
        sessions.append(session)
        return session

    monkeypatch.setattr(
        "app.core.tenant_middleware.SessionLocal",
        fake_session_local,
    )
    monkeypatch.setattr(
        "app.core.tenant_middleware.jwt_auth_service.verify_token",
        lambda _token: {"type": "access", "user_id": "user-1"},
    )

    app = FastAPI()
    configure_tenant_middleware(app)

    @app.get("/api/private")
    async def private_route(request: Request):
        return {"tenant_id": request.state.tenant_id}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.get(
            "/api/private",
            headers={"Authorization": "Bearer valid-token"},
        )
        second = await client.get(
            "/api/private",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == {"tenant_id": "tenant-1"}
    assert second.json() == {"tenant_id": "tenant-1"}
    assert len(sessions) == 1
    assert sessions[0].closed
    assert TenantContext.get_tenant_id() is None
    _clear_auth_context_cache()
