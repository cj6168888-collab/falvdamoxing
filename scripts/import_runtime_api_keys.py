"""Import operator-managed API keys from a local note/env file.

The script never prints secret values. It supports KEY=value, KEY: value and a
small compatibility fallback for the user's local "摘要.txt" note where the
DashScope key is listed under a "通义千问" label.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


KNOWN_KEYS = {
    "DASHSCOPE_API_KEY",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "LOCAL_EMBEDDING_MODEL",
    "LAW_API_KEY",
    "BAITEN_API_KEY",
    "YILIAN_API_KEY",
    "HOLIDAY_API_KEY",
    "COMPANY_INFO_API_BASE_URL",
    "COMPANY_INFO_API_KEY",
    "CLEARBIT_API_KEY",
    "NUMVERIFY_API_KEY",
    "MAILBOX_VALIDATOR_API_KEY",
    "PDFLAYER_API_KEY",
    "OCR_SPACE_API_KEY",
}


def _parse_existing_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _parse_source(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    pattern = re.compile(rf"^\s*({'|'.join(sorted(KNOWN_KEYS))})\s*[:=]\s*(.+?)\s*$")
    for line in lines:
        match = pattern.match(line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip('"').strip("'")

    # Compatibility for local summary notes:
    # 通义千问
    # sk-...
    for idx, line in enumerate(lines):
        if "通义千问" not in line or values.get("DASHSCOPE_API_KEY"):
            continue
        for candidate in lines[idx + 1 : idx + 5]:
            candidate = candidate.strip()
            if candidate and not re.search(r"[\s:：]", candidate) and len(candidate) >= 20:
                values["DASHSCOPE_API_KEY"] = candidate
                break
    return values


def _write_env(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Runtime API key configuration imported by scripts/import_runtime_api_keys.py.",
        "# Do not commit this file.",
    ]
    for key in sorted(values):
        if values[key]:
            escaped = values[key].replace("\r", "").replace("\n", "")
            lines.append(f"{key}={escaped}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import API keys into data/config/api-keys.env.")
    parser.add_argument("--source", default=str(Path.home() / "Documents" / "摘要.txt"))
    parser.add_argument("--output", default=os.environ.get("API_KEY_CONFIG_FILE", "data/config/api-keys.env"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        raise SystemExit(f"Source not found: {source}")

    output = Path(args.output)
    existing = {} if args.overwrite else _parse_existing_env(output)
    imported = _parse_source(source)
    merged = {**imported, **existing}
    changed = [key for key in sorted(imported) if args.overwrite or key not in existing]

    if not imported:
        raise SystemExit("No supported API keys found.")

    for key in sorted(imported):
        status = "would import" if args.dry_run else ("imported" if key in changed else "kept existing")
        print(f"{status}: {key} len={len(imported[key])}")

    if not args.dry_run:
        _write_env(output, merged)
        print(f"wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
