import os
import subprocess
import sys


def test_postgres_migration_lock_uses_advisory_lock(monkeypatch):
    from app.db import migrate_all

    calls = []

    class FakeDialect:
        name = "postgresql"

    class FakeConnection:
        def __enter__(self):
            calls.append(("connect", None))
            return self

        def __exit__(self, exc_type, exc, traceback):
            calls.append(("close", None))

        def execute(self, statement, params):
            calls.append((str(statement), params))

    class FakeEngine:
        dialect = FakeDialect()

        def connect(self):
            return FakeConnection()

    monkeypatch.setattr(migrate_all, "engine", FakeEngine())

    with migrate_all._migration_lock():
        calls.append(("inside", None))

    assert calls == [
        ("connect", None),
        (
            "SELECT pg_advisory_lock(:lock_key)",
            {"lock_key": migrate_all.POSTGRES_LOCK_KEY},
        ),
        ("inside", None),
        (
            "SELECT pg_advisory_unlock(:lock_key)",
            {"lock_key": migrate_all.POSTGRES_LOCK_KEY},
        ),
        ("close", None),
    ]


def test_sqlite_migration_lock_uses_sibling_lock_file(tmp_path, monkeypatch):
    from app.db import migrate_all

    db_path = tmp_path / "lock_test.db"

    class FakeDialect:
        name = "sqlite"

    class FakeEngine:
        dialect = FakeDialect()

    monkeypatch.setattr(migrate_all, "engine", FakeEngine())
    monkeypatch.setattr(migrate_all.settings, "database_url", f"sqlite:///{db_path}")

    with migrate_all._migration_lock():
        assert db_path.with_suffix(".db.migrate.lock").exists()


def test_migrate_all_creates_required_tables(tmp_path):
    db_path = tmp_path / "migration_test.db"
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": f"sqlite:///{db_path}",
            "APP_ENV": "production",
            "AUTO_CREATE_TABLES": "0",
            "JWT_SECRET": "test-jwt-secret",
            "SECRET_KEY": "test-session-secret",
            "CORS_ORIGINS": "https://ci.example.test",
        }
    )

    result = subprocess.run(
        [sys.executable, "-m", "app.db.migrate_all"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr

    import sqlite3

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        migration_rows = connection.execute(
            "SELECT version FROM schema_migrations"
        ).fetchall()

    tables = {row[0] for row in rows}
    assert {"cases", "documents", "tenants", "users"}.issubset(tables)
    assert ("migrate_all_v1",) in migration_rows

    check_result = subprocess.run(
        [sys.executable, "-m", "app.db.migrate_all", "--check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=60,
    )

    assert check_result.returncode == 0, check_result.stderr


def test_migrate_all_check_fails_before_migration(tmp_path):
    db_path = tmp_path / "unmigrated.db"
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": f"sqlite:///{db_path}",
            "APP_ENV": "production",
            "AUTO_CREATE_TABLES": "0",
            "JWT_SECRET": "test-jwt-secret",
            "SECRET_KEY": "test-session-secret",
            "CORS_ORIGINS": "https://ci.example.test",
        }
    )

    result = subprocess.run(
        [sys.executable, "-m", "app.db.migrate_all", "--check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=60,
    )

    assert result.returncode == 1
    assert "Missing required database tables" in result.stderr
