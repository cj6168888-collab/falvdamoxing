import json
import sys
import types

import pytest

import app.core.rate_limiter as rate_limiter_module
from app.core import rate_limit_middleware
from app.core.rate_limit_middleware import RateLimitMiddleware
from app.core.rate_limit_middleware import _client_id_from_scope


def test_client_id_prefers_x_forwarded_for():
    scope = {
        "headers": [(b"x-forwarded-for", b"203.0.113.7, 10.0.0.1")],
        "client": ("127.0.0.1", 12345),
    }

    assert _client_id_from_scope(scope) == "203.0.113.7"


def test_client_id_falls_back_to_client_host():
    assert _client_id_from_scope({"headers": [], "client": ("127.0.0.1", 12345)}) == "127.0.0.1"


@pytest.mark.asyncio
async def test_rate_limit_middleware_skips_exempt_paths(monkeypatch):
    calls = []

    async def app(scope, receive, send):
        calls.append(("app", scope["path"]))

    def fail_get_rate_limiter():
        raise AssertionError("rate limiter should not be loaded for exempt paths")

    monkeypatch.setattr(rate_limit_middleware, "get_rate_limiter", fail_get_rate_limiter)

    middleware = RateLimitMiddleware(app)
    await middleware({"type": "http", "path": "/ready", "headers": []}, None, None)

    assert calls == [("app", "/ready")]


@pytest.mark.asyncio
async def test_rate_limit_middleware_rejects_blocked_client(monkeypatch):
    sent = []

    async def app(scope, receive, send):
        raise AssertionError("blocked request should not reach app")

    class FakeLimiter:
        def is_allowed(self, client_id):
            assert client_id == "203.0.113.7"
            return False, "too many requests"

    monkeypatch.setattr(rate_limit_middleware, "get_rate_limiter", lambda: FakeLimiter())

    async def send(message):
        sent.append(message)

    middleware = RateLimitMiddleware(app)
    await middleware(
        {
            "type": "http",
            "path": "/api/cases",
            "headers": [(b"x-forwarded-for", b"203.0.113.7")],
        },
        None,
        send,
    )

    assert sent[0]["status"] == 429
    assert sent[0]["headers"] == [(b"content-type", b"application/json; charset=utf-8")]
    assert json.loads(sent[1]["body"]) == {"detail": "too many requests"}


@pytest.mark.asyncio
async def test_rate_limit_middleware_allows_request(monkeypatch):
    calls = []

    async def app(scope, receive, send):
        calls.append(("app", scope["path"]))

    class FakeLimiter:
        def is_allowed(self, client_id):
            return True, ""

    monkeypatch.setattr(rate_limit_middleware, "get_rate_limiter", lambda: FakeLimiter())

    middleware = RateLimitMiddleware(app)
    await middleware(
        {"type": "http", "path": "/api/cases", "headers": [], "client": ("127.0.0.1", 1)},
        None,
        None,
    )

    assert calls == [("app", "/api/cases")]


@pytest.mark.asyncio
async def test_rate_limit_middleware_passes_non_http_scopes(monkeypatch):
    calls = []

    async def app(scope, receive, send):
        calls.append(("app", scope["type"]))

    def fail_get_rate_limiter():
        raise AssertionError("rate limiter should not be loaded for non-http scopes")

    monkeypatch.setattr(rate_limit_middleware, "get_rate_limiter", fail_get_rate_limiter)

    middleware = RateLimitMiddleware(app)
    await middleware({"type": "lifespan"}, None, None)

    assert calls == [("app", "lifespan")]


def test_production_redis_limiter_does_not_fallback_when_redis_package_missing(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("USE_REDIS_RATE_LIMIT", "1")
    monkeypatch.delenv("REDIS_RATE_LIMIT_ALLOW_FALLBACK", raising=False)
    monkeypatch.setattr(rate_limiter_module, "REDIS_AVAILABLE", False)

    with pytest.raises(RuntimeError, match="不能降级"):
        rate_limiter_module.create_rate_limiter()


def test_production_redis_limiter_fails_closed_when_runtime_redis_errors(monkeypatch):
    class FakeRedisError(Exception):
        pass

    class FakeScript:
        def __call__(self, *args, **kwargs):
            raise FakeRedisError("redis down")

    class FakeClient:
        def ping(self):
            return True

        def register_script(self, _script):
            return FakeScript()

    fake_redis = types.SimpleNamespace(
        Redis=FakeClient,
        RedisError=FakeRedisError,
        ConnectionError=FakeRedisError,
        from_url=lambda *args, **kwargs: FakeClient(),
    )
    monkeypatch.setitem(sys.modules, "redis", fake_redis)
    monkeypatch.setattr(rate_limiter_module, "redis", fake_redis)
    monkeypatch.setattr(rate_limiter_module, "REDIS_AVAILABLE", True)

    limiter = rate_limiter_module.RedisRateLimiter(allow_fallback=False)

    allowed, message = limiter.is_allowed("client-a")

    assert allowed is False
    assert "限流服务暂不可用" in message


def test_redis_limiter_uses_single_script_with_unique_members(monkeypatch):
    calls = []

    class FakeRedisError(Exception):
        pass

    class FakeScript:
        def __call__(self, *, keys, args):
            calls.append((keys, args))
            return [1, 0]

    class FakeClient:
        def ping(self):
            return True

        def register_script(self, script):
            assert "ZREMRANGEBYSCORE" in script
            return FakeScript()

    fake_redis = types.SimpleNamespace(
        Redis=FakeClient,
        RedisError=FakeRedisError,
        ConnectionError=FakeRedisError,
        from_url=lambda *args, **kwargs: FakeClient(),
    )
    monkeypatch.setitem(sys.modules, "redis", fake_redis)
    monkeypatch.setattr(rate_limiter_module, "redis", fake_redis)
    monkeypatch.setattr(rate_limiter_module, "REDIS_AVAILABLE", True)

    limiter = rate_limiter_module.RedisRateLimiter(rpm=2, rph=3, allow_fallback=False)

    assert limiter.is_allowed("client-a") == (True, "")
    assert limiter.is_allowed("client-a") == (True, "")
    assert len(calls) == 2
    assert calls[0][0] == ["ratelimit:minute:client-a", "ratelimit:hour:client-a"]
    assert calls[0][1][1:3] == [2, 3]
    assert calls[0][1][3] != calls[1][1][3]


def test_redis_limiter_reports_script_denials(monkeypatch):
    class FakeRedisError(Exception):
        pass

    class FakeScript:
        def __call__(self, *, keys, args):
            return [0, 1]

    class FakeClient:
        def ping(self):
            return True

        def register_script(self, _script):
            return FakeScript()

    fake_redis = types.SimpleNamespace(
        Redis=FakeClient,
        RedisError=FakeRedisError,
        ConnectionError=FakeRedisError,
        from_url=lambda *args, **kwargs: FakeClient(),
    )
    monkeypatch.setitem(sys.modules, "redis", fake_redis)
    monkeypatch.setattr(rate_limiter_module, "redis", fake_redis)
    monkeypatch.setattr(rate_limiter_module, "REDIS_AVAILABLE", True)

    limiter = rate_limiter_module.RedisRateLimiter(allow_fallback=False)

    allowed, message = limiter.is_allowed("client-a")

    assert allowed is False
    assert "1分钟内限制" in message
