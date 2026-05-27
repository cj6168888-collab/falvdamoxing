import pytest

from app.config import (
    Settings,
    settings,
    should_auto_create_tables,
    validate_production_settings,
)
from app.services.jwt_auth_service import JWTAuthService


def test_jwt_secret_is_required_in_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "jwt_secret", "")

    with pytest.raises(RuntimeError, match="JWT_SECRET must be set"):
        JWTAuthService()


def test_jwt_secret_can_be_generated_outside_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "jwt_secret", "")

    service = JWTAuthService()

    assert service.secret_key


def test_configured_jwt_secret_is_used(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "jwt_secret", "configured-secret")

    service = JWTAuthService()

    assert service.secret_key == "configured-secret"


def test_production_settings_reject_placeholders():
    prod_settings = Settings(
        app_env="production",
        database_url="postgresql://legal_user:change_me_password@postgres:5432/legal_db",
        jwt_secret="change_me_jwt_secret",
        file_storage_path="/app/data/files",
        sms_provider="console",
        sms_debug_return_code=True,
    )

    errors = validate_production_settings(
        prod_settings,
        environ={
            "SECRET_KEY": "change_me_session_secret",
            "CORS_ORIGINS": "https://your-domain.com",
            "USE_REDIS_RATE_LIMIT": "1",
            "REDIS_URL": "redis://:change_me_redis_password@redis:6379/0",
            "REDIS_PASSWORD": "change_me_redis_password",
            "WEB_CONCURRENCY": "1",
        },
    )

    assert any("JWT_SECRET" in error for error in errors)
    assert any("DATABASE_URL" in error for error in errors)
    assert any("CORS_ORIGINS" in error for error in errors)
    assert any("REDIS_PASSWORD" in error for error in errors)
    assert any("WEB_CONCURRENCY" in error for error in errors)
    assert any("SMS_PROVIDER" in error for error in errors)
    assert any("SMS_DEBUG_RETURN_CODE" in error for error in errors)


def test_production_settings_accept_real_values():
    prod_settings = Settings(
        app_env="production",
        database_url="postgresql://legal_user:strong-password@postgres:5432/legal_db",
        db_pool_size=15,
        db_max_overflow=5,
        jwt_secret="configured-jwt-secret",
        file_storage_path="/app/data/files",
        sms_provider="http",
        sms_http_endpoint="https://sms.example.cn/send",
        sms_http_token="configured-sms-token",
        sms_debug_return_code=False,
    )

    errors = validate_production_settings(
        prod_settings,
        environ={
            "SECRET_KEY": "configured-session-secret",
            "CORS_ORIGINS": "https://legal.example.cn,https://www.legal.example.cn",
            "USE_REDIS_RATE_LIMIT": "1",
            "REDIS_URL": "redis://:configured-redis-password@redis:6379/0",
            "REDIS_PASSWORD": "configured-redis-password",
            "WEB_CONCURRENCY": "4",
            "EXPECTED_APP_REPLICAS": "2",
            "POSTGRES_MAX_CONNECTIONS": "300",
            "POSTGRES_RESERVED_CONNECTIONS": "50",
        },
    )

    assert errors == []


def test_production_settings_reject_db_pool_that_exceeds_postgres_capacity():
    prod_settings = Settings(
        app_env="production",
        database_url="postgresql://legal_user:strong-password@postgres:5432/legal_db",
        db_pool_size=25,
        db_max_overflow=50,
        jwt_secret="configured-jwt-secret",
        file_storage_path="/app/data/files",
        sms_provider="http",
        sms_http_endpoint="https://sms.example.cn/send",
        sms_http_token="configured-sms-token",
        sms_debug_return_code=False,
    )

    errors = validate_production_settings(
        prod_settings,
        environ={
            "SECRET_KEY": "configured-session-secret",
            "CORS_ORIGINS": "https://legal.example.cn",
            "USE_REDIS_RATE_LIMIT": "1",
            "REDIS_URL": "redis://:configured-redis-password@redis:6379/0",
            "REDIS_PASSWORD": "configured-redis-password",
            "WEB_CONCURRENCY": "4",
            "EXPECTED_APP_REPLICAS": "2",
            "POSTGRES_MAX_CONNECTIONS": "100",
            "POSTGRES_RESERVED_CONNECTIONS": "20",
        },
    )

    assert any("DB connection capacity is unsafe" in error for error in errors)


def test_production_settings_accept_pgbouncer_capacity_model():
    prod_settings = Settings(
        app_env="production",
        database_url="postgresql://legal_user:strong-password@pgbouncer:6432/legal_db",
        db_pool_size=15,
        db_max_overflow=10,
        jwt_secret="configured-jwt-secret",
        file_storage_path="/app/data/files",
        sms_provider="http",
        sms_http_endpoint="https://sms.example.cn/send",
        sms_http_token="configured-sms-token",
        sms_debug_return_code=False,
    )

    errors = validate_production_settings(
        prod_settings,
        environ={
            "SECRET_KEY": "configured-session-secret",
            "CORS_ORIGINS": "https://legal.example.cn",
            "USE_REDIS_RATE_LIMIT": "1",
            "REDIS_URL": "redis://:configured-redis-password@redis:6379/0",
            "REDIS_PASSWORD": "configured-redis-password",
            "WEB_CONCURRENCY": "4",
            "EXPECTED_APP_REPLICAS": "8",
            "POSTGRES_MAX_CONNECTIONS": "500",
            "POSTGRES_RESERVED_CONNECTIONS": "80",
            "PGBOUNCER_ENABLED": "1",
            "PGBOUNCER_MAX_CLIENT_CONN": "2000",
            "PGBOUNCER_DEFAULT_POOL_SIZE": "80",
            "PGBOUNCER_RESERVE_POOL_SIZE": "40",
        },
    )

    assert errors == []


def test_production_settings_reject_pgbouncer_server_pool_that_exceeds_postgres():
    prod_settings = Settings(
        app_env="production",
        database_url="postgresql://legal_user:strong-password@pgbouncer:6432/legal_db",
        db_pool_size=15,
        db_max_overflow=10,
        jwt_secret="configured-jwt-secret",
        file_storage_path="/app/data/files",
        sms_provider="http",
        sms_http_endpoint="https://sms.example.cn/send",
        sms_http_token="configured-sms-token",
        sms_debug_return_code=False,
    )

    errors = validate_production_settings(
        prod_settings,
        environ={
            "SECRET_KEY": "configured-session-secret",
            "CORS_ORIGINS": "https://legal.example.cn",
            "USE_REDIS_RATE_LIMIT": "1",
            "REDIS_URL": "redis://:configured-redis-password@redis:6379/0",
            "REDIS_PASSWORD": "configured-redis-password",
            "WEB_CONCURRENCY": "4",
            "EXPECTED_APP_REPLICAS": "4",
            "POSTGRES_MAX_CONNECTIONS": "100",
            "POSTGRES_RESERVED_CONNECTIONS": "20",
            "PGBOUNCER_ENABLED": "1",
            "PGBOUNCER_MAX_CLIENT_CONN": "2000",
            "PGBOUNCER_DEFAULT_POOL_SIZE": "80",
            "PGBOUNCER_RESERVE_POOL_SIZE": "40",
        },
    )

    assert any("PgBouncer server pool is unsafe" in error for error in errors)


def test_production_settings_reject_sqlite_and_disabled_redis():
    prod_settings = Settings(
        app_env="production",
        database_url="sqlite:///./legal_system.db",
        jwt_secret="configured-jwt-secret",
        file_storage_path="/app/data/files",
        sms_provider="http",
        sms_http_endpoint="https://sms.example.cn/send",
        sms_http_token="configured-sms-token",
        sms_debug_return_code=False,
    )

    errors = validate_production_settings(
        prod_settings,
        environ={
            "SECRET_KEY": "configured-session-secret",
            "CORS_ORIGINS": "https://legal.example.cn",
            "USE_REDIS_RATE_LIMIT": "0",
            "REDIS_URL": "",
            "REDIS_PASSWORD": "",
            "WEB_CONCURRENCY": "4",
        },
    )

    assert any("not SQLite" in error for error in errors)
    assert any("USE_REDIS_RATE_LIMIT" in error for error in errors)
    assert any("REDIS_URL" in error for error in errors)


def test_development_settings_do_not_require_production_values():
    dev_settings = Settings(app_env="development", jwt_secret="")

    assert validate_production_settings(dev_settings, environ={}) == []


def test_auto_create_tables_defaults_to_development_only():
    assert should_auto_create_tables(Settings(app_env="development"), environ={}) is True
    assert should_auto_create_tables(Settings(app_env="production"), environ={}) is False


def test_auto_create_tables_env_override():
    prod_settings = Settings(app_env="production")

    assert should_auto_create_tables(prod_settings, environ={"AUTO_CREATE_TABLES": "1"}) is True
    assert should_auto_create_tables(prod_settings, environ={"AUTO_CREATE_TABLES": "0"}) is False
