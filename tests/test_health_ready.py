import sys
import types

import pytest

from app.app_factory import create_app
from app.app_factory import lifespan
import app.app_factory as app_factory_module
from app.core.security_middleware import parse_trusted_hosts
from app.monitoring.readiness import check_database
from app.monitoring.readiness import check_file_storage
from app.monitoring.readiness import check_redis
from app.monitoring.readiness import ensure_file_storage_directory
import app.monitoring.readiness as readiness_module

@pytest.mark.asyncio
async def test_health_check_is_lightweight(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_ready_check_reports_dependencies(client, monkeypatch):
    monkeypatch.delenv("USE_REDIS_RATE_LIMIT", raising=False)
    monkeypatch.setattr(readiness_module.settings, "app_env", "development")

    response = await client.get("/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["schema"]["status"] == "ok"
    assert data["checks"]["file_storage"]["status"] == "ok"
    assert data["checks"]["redis"]["status"] == "skipped"


@pytest.mark.asyncio
async def test_ready_check_fails_when_redis_url_is_missing(client, monkeypatch):
    monkeypatch.setenv("USE_REDIS_RATE_LIMIT", "1")
    monkeypatch.delenv("REDIS_URL", raising=False)

    response = await client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["redis"]["status"] == "error"
    assert "REDIS_URL is required" in data["checks"]["redis"]["detail"]


@pytest.mark.asyncio
async def test_ready_check_skips_schema_when_database_is_unavailable(client, monkeypatch):
    monkeypatch.delenv("USE_REDIS_RATE_LIMIT", raising=False)
    monkeypatch.setattr(readiness_module.settings, "app_env", "development")
    monkeypatch.setattr(
        readiness_module,
        "check_database",
        lambda: {"status": "error", "detail": "database down"},
    )

    response = await client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["checks"]["database"] == {
        "status": "error",
        "detail": "database down",
    }
    assert data["checks"]["schema"] == {
        "status": "skipped",
        "reason": "database_unavailable",
    }


@pytest.mark.asyncio
async def test_ready_check_fails_when_schema_is_missing(client, monkeypatch):
    monkeypatch.delenv("USE_REDIS_RATE_LIMIT", raising=False)
    monkeypatch.setattr(readiness_module.settings, "app_env", "development")
    monkeypatch.setattr(
        readiness_module,
        "check_schema_tables",
        lambda: {"status": "error", "missing_tables": ["cases"]},
    )

    response = await client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["schema"]["missing_tables"] == ["cases"]


@pytest.mark.asyncio
async def test_ready_check_fails_when_migration_marker_is_missing(client, monkeypatch):
    monkeypatch.delenv("USE_REDIS_RATE_LIMIT", raising=False)
    monkeypatch.setattr(readiness_module.settings, "app_env", "development")
    monkeypatch.setattr(readiness_module, "should_auto_create_tables", lambda: False)
    monkeypatch.setattr(readiness_module, "get_migration_record", lambda: None)

    response = await client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["checks"]["schema"]["missing_migration"] == "migrate_all_v1"


@pytest.mark.asyncio
async def test_ready_check_reports_migration_record(client, monkeypatch):
    monkeypatch.delenv("USE_REDIS_RATE_LIMIT", raising=False)
    monkeypatch.setattr(readiness_module.settings, "app_env", "development")
    monkeypatch.setattr(readiness_module, "should_auto_create_tables", lambda: False)
    monkeypatch.setattr(
        readiness_module,
        "get_migration_record",
        lambda: {
            "version": "migrate_all_v1",
            "applied_at": "2026-05-10T00:00:00+00:00",
        },
    )

    response = await client.get("/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["checks"]["schema"]["migration"] == {
        "version": "migrate_all_v1",
        "applied_at": "2026-05-10T00:00:00+00:00",
    }


def test_trusted_hosts_keep_internal_probe_hosts(monkeypatch):
    monkeypatch.delenv("TRUSTED_HOSTS", raising=False)

    hosts = parse_trusted_hosts(["https://ci.example.test"])

    assert "ci.example.test" in hosts
    assert "localhost" in hosts
    assert "127.0.0.1" in hosts


def test_file_storage_check_writes_probe_file(tmp_path, monkeypatch):
    monkeypatch.setattr(readiness_module.settings, "file_storage_path", str(tmp_path))

    result = check_file_storage()

    assert result == {"status": "ok", "path": str(tmp_path)}
    assert list(tmp_path.glob(".ready-write-probe-*")) == []


def test_ensure_file_storage_directory_creates_missing_path(tmp_path, monkeypatch):
    storage_path = tmp_path / "nested" / "files"
    monkeypatch.setattr(readiness_module.settings, "file_storage_path", str(storage_path))

    result = ensure_file_storage_directory()

    assert result == storage_path
    assert storage_path.is_dir()


def test_file_storage_check_reports_write_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(readiness_module.settings, "file_storage_path", str(tmp_path))

    def fail_write(self, *args, **kwargs):
        raise PermissionError("read-only storage")

    monkeypatch.setattr(readiness_module.Path, "write_text", fail_write)

    result = check_file_storage()

    assert result["status"] == "error"
    assert result["path"] == str(tmp_path)
    assert "read-only storage" in result["detail"]


def test_database_check_executes_select_one(monkeypatch):
    calls = []

    class FakeConnection:
        def __enter__(self):
            calls.append(("connect", None))
            return self

        def __exit__(self, exc_type, exc, traceback):
            calls.append(("close", None))

        def execute(self, statement):
            calls.append(("execute", str(statement)))

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    monkeypatch.setattr(readiness_module, "engine", FakeEngine())

    result = check_database()

    assert result == {"status": "ok"}
    assert calls == [
        ("connect", None),
        ("execute", "SELECT 1"),
        ("close", None),
    ]


def test_database_check_reports_connection_failure(monkeypatch):
    class FakeEngine:
        def connect(self):
            raise RuntimeError("db offline")

    monkeypatch.setattr(readiness_module, "engine", FakeEngine())

    result = check_database()

    assert result["status"] == "error"
    assert "db offline" in result["detail"]


def test_redis_check_skips_when_rate_limit_is_disabled(monkeypatch):
    monkeypatch.delenv("USE_REDIS_RATE_LIMIT", raising=False)
    monkeypatch.setattr(readiness_module.settings, "app_env", "development")

    assert check_redis() == {"status": "skipped"}


def test_redis_check_requires_redis_in_production(monkeypatch):
    monkeypatch.delenv("USE_REDIS_RATE_LIMIT", raising=False)
    monkeypatch.setattr(readiness_module.settings, "app_env", "production")

    result = check_redis()

    assert result["status"] == "error"
    assert "USE_REDIS_RATE_LIMIT" in result["detail"]


def test_redis_check_reports_missing_url(monkeypatch):
    monkeypatch.setenv("USE_REDIS_RATE_LIMIT", "1")
    monkeypatch.delenv("REDIS_URL", raising=False)

    result = check_redis()

    assert result["status"] == "error"
    assert "REDIS_URL is required" in result["detail"]


def test_redis_check_pings_configured_redis(monkeypatch):
    calls = []

    class FakeClient:
        def ping(self):
            calls.append(("ping", None))

    fake_redis = types.SimpleNamespace(
        from_url=lambda *args, **kwargs: calls.append((args, kwargs)) or FakeClient()
    )
    monkeypatch.setitem(sys.modules, "redis", fake_redis)
    monkeypatch.setenv("USE_REDIS_RATE_LIMIT", "true")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("REDIS_PASSWORD", "secret")

    result = check_redis()

    assert result == {"status": "ok"}
    assert calls == [
        (
            ("redis://redis:6379/0",),
            {
                "password": "secret",
                "socket_connect_timeout": 3,
                "socket_timeout": 3,
            },
        ),
        ("ping", None),
    ]


def test_redis_check_reports_ping_failure(monkeypatch):
    class FakeClient:
        def ping(self):
            raise TimeoutError("redis timeout")

    fake_redis = types.SimpleNamespace(
        from_url=lambda *args, **kwargs: FakeClient()
    )
    monkeypatch.setitem(sys.modules, "redis", fake_redis)
    monkeypatch.setenv("USE_REDIS_RATE_LIMIT", "yes")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")

    result = check_redis()

    assert result["status"] == "error"
    assert "redis timeout" in result["detail"]


@pytest.mark.asyncio
async def test_lifespan_runs_startup_and_shutdown_once(monkeypatch):
    calls = []

    monkeypatch.setattr(app_factory_module, "assert_production_settings", lambda: calls.append("assert"))
    monkeypatch.setattr(app_factory_module, "init_db", lambda: calls.append("init"))
    monkeypatch.setattr(app_factory_module, "_resume_folder_watchers", lambda: calls.append("watchers"))

    from app.services.folder_watcher import FolderWatcherService

    monkeypatch.setattr(FolderWatcherService, "stop_all", lambda: calls.append("stop"))

    async with lifespan(create_app(include_static_files=False, include_task_handlers=False)):
        calls.append("running")

    assert calls == ["assert", "init", "watchers", "running", "stop"]
