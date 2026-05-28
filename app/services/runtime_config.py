"""Persistent runtime configuration for operator-managed API keys."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable


def runtime_config_path() -> Path:
    configured = os.environ.get("API_KEY_CONFIG_FILE")
    if configured:
        return Path(configured)
    return Path("./data/config/api-keys.env")


def _parse_env_lines(lines: Iterable[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = value.strip().strip('"').strip("'")
    return values


def read_runtime_config() -> dict[str, str]:
    path = runtime_config_path()
    if not path.exists():
        return {}
    return _parse_env_lines(path.read_text(encoding="utf-8").splitlines())


def write_runtime_config(values: dict[str, str]) -> None:
    path = runtime_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Runtime API key configuration written by /api/config/api-keys.",
        "# Keep this file outside any publicly served upload directory.",
    ]
    for key in sorted(values):
        value = values[key]
        if value:
            escaped = value.replace("\n", "").replace("\r", "")
            lines.append(f"{key}={escaped}")

    content = "\n".join(lines) + "\n"
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def load_runtime_config_into_environ(*, override: bool = False) -> dict[str, str]:
    values = read_runtime_config()
    for key, value in values.items():
        if override or not os.environ.get(key):
            os.environ[key] = value
    return values


def get_config_value(key: str, default: str = "") -> str:
    env_value = os.environ.get(key)
    if env_value:
        return env_value
    return read_runtime_config().get(key, default)


def save_config_values(updates: dict[str, str], sources: dict[str, str] | None = None) -> list[str]:
    values = read_runtime_config()
    saved: list[str] = []
    for key, value in updates.items():
        if not value:
            continue
        values[key] = value
        os.environ[key] = value
        saved.append(key)
        if sources and key in sources:
            source_key = f"{key}_SOURCE"
            values[source_key] = sources[key]
    write_runtime_config(values)
    return saved


def delete_config_value(key: str) -> None:
    values = read_runtime_config()
    values.pop(key, None)
    os.environ.pop(key, None)
    write_runtime_config(values)
