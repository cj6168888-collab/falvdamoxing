"""Unified database migration entrypoint.

This command is intentionally conservative: it creates SQLAlchemy-managed
tables for every supported database, then runs legacy sqlite-only migration
scripts when the configured database is sqlite.
"""

from __future__ import annotations

import contextlib
import logging
import os
import subprocess
import sys
import argparse
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    inspect,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.sqltypes import Enum as SqlEnum
from sqlalchemy.schema import CreateIndex

from app.config import settings
from app.db.database import Base, create_all_tables, engine
from app.db.tenant_backfill import backfill_tenant_columns

logger = logging.getLogger(__name__)

REQUIRED_TABLES = ("cases", "documents", "tenants", "users")
MIGRATION_VERSION = "migrate_all_v1"
POSTGRES_LOCK_KEY = 317758726374351


def _is_sqlite() -> bool:
    return settings.database_url.startswith("sqlite:///")


def _sqlite_database_path() -> str:
    path = settings.database_url.replace("sqlite:///", "", 1)
    return os.path.abspath(path)


@contextlib.contextmanager
def _file_lock(lock_path: str):
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def _migration_lock():
    dialect = engine.dialect.name
    if dialect == "sqlite":
        lock_path = f"{_sqlite_database_path()}.migrate.lock"
        logger.info("Acquiring sqlite migration lock: %s", lock_path)
        with _file_lock(lock_path):
            yield
        return

    if dialect == "postgresql":
        logger.info("Acquiring postgres migration advisory lock.")
        with engine.connect() as connection:
            connection.execute(
                text("SELECT pg_advisory_lock(:lock_key)"),
                {"lock_key": POSTGRES_LOCK_KEY},
            )
            try:
                yield
            finally:
                connection.execute(
                    text("SELECT pg_advisory_unlock(:lock_key)"),
                    {"lock_key": POSTGRES_LOCK_KEY},
                )
        return

    logger.info("No migration lock configured for database dialect: %s", dialect)
    yield


def _run_sqlite_legacy_migrations() -> None:
    logger.info("Running legacy sqlite migrations.")
    for module_name in ("app.db.migrate", "app.db.migrate_legal_knowledge"):
        result = subprocess.run([sys.executable, "-m", module_name], check=False)
        if result.returncode != 0:
            raise RuntimeError(
                f"Legacy sqlite migration {module_name} failed with exit code "
                f"{result.returncode}"
            )


def _missing_required_tables() -> list[str]:
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    return [table for table in REQUIRED_TABLES if table not in existing]


def _verify_required_tables() -> None:
    missing = _missing_required_tables()
    if missing:
        raise RuntimeError(f"Missing required database tables: {', '.join(missing)}")


def _drop_cross_table_index_conflicts() -> list[str]:
    if engine.dialect.name != "postgresql":
        return []

    metadata_indexes = {
        index.name: table.name
        for table in Base.metadata.tables.values()
        for index in table.indexes
        if index.name
    }
    if not metadata_indexes:
        return []

    dropped: list[str] = []
    preparer = engine.dialect.identifier_preparer
    with engine.begin() as connection:
        rows = connection.execute(
            text(
                """
                SELECT tablename, indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                """
            )
        ).mappings()
        for row in rows:
            index_name = row["indexname"]
            target_table = metadata_indexes.get(index_name)
            if target_table and row["tablename"] != target_table:
                connection.execute(
                    text(f"DROP INDEX IF EXISTS {preparer.quote(index_name)}")
                )
                dropped.append(index_name)

    if dropped:
        logger.info(
            "Dropped legacy cross-table index conflicts: %s", ", ".join(dropped)
        )
    return dropped


def _compiled_column_type(column) -> str:
    """Return a conservative portable type for adding missing columns.

    SQLAlchemy's create_all creates missing tables but deliberately does not
    alter existing tables. Some historical deployments bootstrapped tables from
    scripts/init-db.sql, whose columns no longer match the ORM. For additive
    repair we avoid inline enum/check/foreign-key constraints and add the
    storage type only; application-level validation still owns those semantics.
    """

    column_type = column.type
    if isinstance(column_type, SqlEnum):
        return "VARCHAR(255)"
    if isinstance(column_type, String):
        return f"VARCHAR({column_type.length})" if column_type.length else "VARCHAR"
    if isinstance(column_type, Text):
        return "TEXT"
    if isinstance(column_type, Integer):
        return "INTEGER"
    if isinstance(column_type, Float):
        return "FLOAT"
    if isinstance(column_type, Boolean):
        return "BOOLEAN"
    if isinstance(column_type, DateTime):
        return "TIMESTAMP"
    if isinstance(column_type, Date):
        return "DATE"
    if isinstance(column_type, (JSON, JSONB)):
        return "JSONB" if engine.dialect.name == "postgresql" else "JSON"
    return column_type.compile(dialect=engine.dialect)


def _sync_missing_columns() -> list[str]:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    preparer = engine.dialect.identifier_preparer
    added: list[str] = []

    with engine.begin() as connection:
        for table in sorted(
            Base.metadata.sorted_tables, key=lambda item: item.name
        ):
            if table.name not in existing_tables:
                continue

            existing_columns = {
                column["name"] for column in inspector.get_columns(table.name)
            }
            for column in table.columns:
                if column.name in existing_columns:
                    continue

                table_name = preparer.quote(table.name)
                column_name = preparer.quote(column.name)
                column_type = _compiled_column_type(column)

                statement = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                if engine.dialect.name == "postgresql":
                    statement = (
                        f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS "
                        f"{column_name} {column_type}"
                    )

                connection.execute(text(statement))
                added.append(f"{table.name}.{column.name}")

    if added:
        logger.info("Added missing database columns: %s", ", ".join(added))
    return added


def _sync_missing_indexes() -> list[str]:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    created: list[str] = []

    with engine.begin() as connection:
        for table in sorted(Base.metadata.sorted_tables, key=lambda item: item.name):
            if table.name not in existing_tables:
                continue

            existing_indexes = {
                index["name"] for index in inspector.get_indexes(table.name)
            }
            for index in sorted(table.indexes, key=lambda item: item.name or ""):
                if not index.name or index.name in existing_indexes:
                    continue
                connection.execute(CreateIndex(index))
                created.append(index.name)

    if created:
        logger.info("Created missing database indexes: %s", ", ".join(created))
    return created


def _sync_postgres_enum_values() -> list[str]:
    if engine.dialect.name != "postgresql":
        return []

    from app.models.tenant import TenantType

    enum_specs = {
        "tenanttype": [member.name for member in TenantType],
    }
    added: list[str] = []
    preparer = engine.dialect.identifier_preparer

    with engine.begin() as connection:
        for enum_name, labels in enum_specs.items():
            exists = connection.execute(
                text("SELECT 1 FROM pg_type WHERE typname = :enum_name"),
                {"enum_name": enum_name},
            ).first()
            if not exists:
                continue

            existing = {
                row[0]
                for row in connection.execute(
                    text(
                        """
                        SELECT e.enumlabel
                        FROM pg_enum e
                        JOIN pg_type t ON t.oid = e.enumtypid
                        WHERE t.typname = :enum_name
                        """
                    ),
                    {"enum_name": enum_name},
                )
            }

            quoted_enum_name = preparer.quote(enum_name)
            for label in labels:
                if label in existing:
                    continue
                escaped_label = label.replace("'", "''")
                connection.execute(
                    text(f"ALTER TYPE {quoted_enum_name} ADD VALUE IF NOT EXISTS '{escaped_label}'")
                )
                added.append(f"{enum_name}.{label}")

    if added:
        logger.info("Added missing postgres enum values: %s", ", ".join(added))
    return added


def _fallback_tenant_id(connection) -> str:
    try:
        result = connection.execute(text("SELECT id FROM tenants LIMIT 1")).first()
        if result:
            return result[0]
    except Exception:
        pass
    return "default"


def _backfill_tenant_columns() -> list[str]:
    skip_tables = {"users", "api_keys"}

    with engine.begin() as connection:
        fallback_tenant_id = _fallback_tenant_id(connection)
        updated = backfill_tenant_columns(
            connection,
            Base.metadata,
            fallback_tenant_id,
            skip_tables,
        )

    if updated:
        logger.info("Backfilled tenant_id columns: %s", ", ".join(updated))
    return updated


def _record_migration_version() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(100) PRIMARY KEY,
                    applied_at VARCHAR(40) NOT NULL
                )
                """
            )
        )
        if _is_sqlite():
            connection.execute(
                text(
                    """
                    INSERT OR REPLACE INTO schema_migrations (version, applied_at)
                    VALUES (:version, :applied_at)
                    """
                ),
                {"version": MIGRATION_VERSION, "applied_at": now},
            )
        else:
            connection.execute(
                text(
                    """
                    INSERT INTO schema_migrations (version, applied_at)
                    VALUES (:version, :applied_at)
                    ON CONFLICT (version) DO UPDATE SET applied_at = EXCLUDED.applied_at
                    """
                ),
                {"version": MIGRATION_VERSION, "applied_at": now},
            )


def has_migration_version(version: str = MIGRATION_VERSION) -> bool:
    return get_migration_record(version) is not None


def get_migration_record(version: str = MIGRATION_VERSION) -> dict[str, str] | None:
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT version, applied_at
                    FROM schema_migrations
                    WHERE version = :version
                    """
                ),
                {"version": version},
            ).first()
        if result is None:
            return None
        row = result._mapping
        return {"version": row["version"], "applied_at": row["applied_at"]}
    except Exception:
        return None


def migrate_all() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    import app.models  # noqa: F401 - register metadata before migration checks

    with _migration_lock():
        _drop_cross_table_index_conflicts()
        logger.info("Creating SQLAlchemy-managed tables.")
        create_all_tables()
        logger.info("Synchronizing postgres enum values.")
        _sync_postgres_enum_values()
        logger.info("Synchronizing missing columns on existing tables.")
        _sync_missing_columns()
        logger.info("Synchronizing missing indexes on existing tables.")
        _sync_missing_indexes()
        logger.info("Backfilling tenant_id columns on legacy rows.")
        _backfill_tenant_columns()

        if _is_sqlite():
            _run_sqlite_legacy_migrations()
        else:
            logger.info("Skipping sqlite legacy migrations for non-sqlite database.")

        _verify_required_tables()
        _record_migration_version()
        logger.info("Database migration completed.")


def check_migrations() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    missing = _missing_required_tables()
    if missing:
        raise RuntimeError(f"Missing required database tables: {', '.join(missing)}")
    if not has_migration_version():
        raise RuntimeError(f"Missing migration marker: {MIGRATION_VERSION}")
    logger.info("Database migration check passed.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or check database migrations.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify required tables and migration marker without modifying schema.",
    )
    args = parser.parse_args()

    try:
        if args.check:
            check_migrations()
        else:
            migrate_all()
        return 0
    except Exception:
        logger.exception("Database migration failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
