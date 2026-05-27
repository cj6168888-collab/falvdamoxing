"""Validate a production env file without printing secret values."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import Settings, validate_production_settings


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.strip().lower() in ("1", "true", "yes", "on")


def _parse_int(values: dict[str, str], key: str, default: int, errors: list[str]) -> int:
    raw_value = values.get(key)
    if raw_value is None or raw_value == "":
        return default
    try:
        return int(raw_value)
    except ValueError:
        errors.append(f"{key} must be an integer")
        return default


def validate_env_file(path: Path, expected_app_replicas: Optional[int] = None) -> list[str]:
    values = _parse_env_file(path)
    errors: list[str] = []
    if expected_app_replicas is not None:
        values["EXPECTED_APP_REPLICAS"] = str(expected_app_replicas)

    settings = Settings(
        app_env=values.get("APP_ENV", "production"),
        database_url=values.get("DATABASE_URL", ""),
        db_pool_size=_parse_int(values, "DB_POOL_SIZE", 20, errors),
        db_max_overflow=_parse_int(values, "DB_MAX_OVERFLOW", 40, errors),
        db_pool_timeout=_parse_int(values, "DB_POOL_TIMEOUT", 30, errors),
        jwt_secret=values.get("JWT_SECRET", ""),
        file_storage_path=values.get("FILE_STORAGE_PATH", ""),
        sms_provider=values.get("SMS_PROVIDER", "console"),
        sms_http_endpoint=values.get("SMS_HTTP_ENDPOINT", ""),
        sms_http_token=values.get("SMS_HTTP_TOKEN", ""),
        sms_debug_return_code=_parse_bool(values.get("SMS_DEBUG_RETURN_CODE")),
    )
    return errors + validate_production_settings(settings, environ=values)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate production configuration before deployment.",
    )
    parser.add_argument(
        "env_file",
        nargs="?",
        default=".env.prod",
        help="Path to the production env file. Defaults to .env.prod.",
    )
    parser.add_argument(
        "--expected-app-replicas",
        type=int,
        help="Override EXPECTED_APP_REPLICAS for capacity validation.",
    )
    args = parser.parse_args()

    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"ERROR: env file not found: {env_path}")
        return 1

    errors = validate_env_file(env_path, expected_app_replicas=args.expected_app_replicas)
    if errors:
        print("ERROR: production configuration is not deployable")
        for error in errors:
            print(f"- {error}")
        return 1

    print("OK: production configuration is deployable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
