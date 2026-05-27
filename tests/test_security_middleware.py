from fastapi import FastAPI

from app.core.rate_limit_middleware import RateLimitMiddleware
from app.core.security_middleware import DEFAULT_DEV_ORIGINS
from app.core.security_middleware import configure_security_middleware
from app.core.security_middleware import parse_cors_origins
from app.core.security_middleware import parse_trusted_hosts


def test_parse_cors_origins_defaults_to_dev_origins(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert parse_cors_origins() == DEFAULT_DEV_ORIGINS


def test_parse_cors_origins_trims_configured_origins(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        " https://legal.example.cn, https://www.legal.example.cn ,, ",
    )

    assert parse_cors_origins() == [
        "https://legal.example.cn",
        "https://www.legal.example.cn",
    ]


def test_parse_trusted_hosts_uses_configured_hosts(monkeypatch):
    monkeypatch.setenv("TRUSTED_HOSTS", " legal.example.cn, api.legal.example.cn ")

    assert parse_trusted_hosts(["https://ignored.example.cn"]) == [
        "legal.example.cn",
        "api.legal.example.cn",
        "localhost",
        "127.0.0.1",
    ]


def test_parse_trusted_hosts_derives_hosts_from_origins(monkeypatch):
    monkeypatch.delenv("TRUSTED_HOSTS", raising=False)

    assert parse_trusted_hosts(["https://legal.example.cn", "http://localhost:3000"]) == [
        "legal.example.cn",
        "localhost",
        "127.0.0.1",
    ]


def test_configure_security_middleware_registers_expected_middleware(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://legal.example.cn")
    app = FastAPI()

    configure_security_middleware(app)

    middleware_classes = [middleware.cls for middleware in app.user_middleware]
    assert RateLimitMiddleware in middleware_classes
    assert any(middleware.cls.__name__ == "CORSMiddleware" for middleware in app.user_middleware)
    assert any(
        middleware.cls.__name__ == "TrustedHostMiddleware"
        for middleware in app.user_middleware
    )
