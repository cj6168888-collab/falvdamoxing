"""Readiness checks used by the API and deployment probes."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from sqlalchemy import inspect, text

from app.config import settings, should_auto_create_tables
from app.db.database import engine
from app.db.migrate_all import MIGRATION_VERSION, get_migration_record

REQUIRED_READY_TABLES = ("cases", "documents", "tenants", "users")


def check_schema_tables() -> dict:
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        missing_tables = [
            table for table in REQUIRED_READY_TABLES if table not in existing_tables
        ]
        if missing_tables:
            return {"status": "error", "missing_tables": missing_tables}

        migration_record = get_migration_record()
        if not should_auto_create_tables() and migration_record is None:
            return {
                "status": "error",
                "missing_migration": MIGRATION_VERSION,
                "required_tables": list(REQUIRED_READY_TABLES),
            }

        schema_status = {
            "status": "ok",
            "required_tables": list(REQUIRED_READY_TABLES),
        }
        if migration_record is not None:
            schema_status["migration"] = migration_record
        return schema_status
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def check_database() -> dict:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def ensure_file_storage_directory() -> Path:
    storage_path = Path(settings.file_storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path


def check_file_storage() -> dict:
    storage_path = ensure_file_storage_directory()
    probe_path = storage_path / f".ready-write-probe-{uuid.uuid4().hex}"
    try:
        probe_path.write_text("ok", encoding="utf-8")
        probe_path.unlink()
        return {"status": "ok", "path": str(storage_path)}
    except Exception as exc:
        return {"status": "error", "path": str(storage_path), "detail": str(exc)}


def check_redis() -> dict:
    use_redis = os.environ.get("USE_REDIS_RATE_LIMIT", "").lower() in (
        "1",
        "true",
        "yes",
    )
    if not use_redis:
        if settings.app_env.lower() == "production":
            return {
                "status": "error",
                "detail": "USE_REDIS_RATE_LIMIT must be enabled in production",
            }
        return {"status": "skipped"}

    redis_url = os.environ.get("REDIS_URL", "").strip()
    if not redis_url:
        return {
            "status": "error",
            "detail": "REDIS_URL is required when USE_REDIS_RATE_LIMIT is enabled",
        }

    try:
        import redis

        client = redis.from_url(
            redis_url,
            password=os.environ.get("REDIS_PASSWORD") or None,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        client.ping()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def check_readiness() -> dict:
    checks = {}

    checks["database"] = check_database()
    if checks["database"]["status"] == "ok":
        checks["schema"] = check_schema_tables()
    else:
        checks["schema"] = {
            "status": "skipped",
            "reason": "database_unavailable",
        }

    checks["file_storage"] = check_file_storage()
    checks["redis"] = check_redis()

    return checks
