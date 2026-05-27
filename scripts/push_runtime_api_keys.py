"""Push runtime API keys to a running backend through /api/config/api-keys."""

from __future__ import annotations

import argparse
from pathlib import Path

import httpx


def _parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() and value.strip():
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _login(client: httpx.Client, username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    response.raise_for_status()
    payload = response.json()
    return payload["tokens"]["access_token"]


def push_keys(
    base_url: str,
    source: Path,
    timeout_seconds: float,
    *,
    token: str = "",
    username: str = "",
    password: str = "",
) -> dict:
    values = _parse_env(source)
    if not values:
        raise RuntimeError(f"No key values found in {source}")
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout_seconds, trust_env=False) as client:
        resolved_token = token or (_login(client, username, password) if username and password else "")
        headers = {"Authorization": f"Bearer {resolved_token}"} if resolved_token else {}
        response = client.post("/api/config/api-keys", json={"configs": values}, headers=headers)
        response.raise_for_status()
        return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Push local runtime API keys to a running backend.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--source", default="data/config/api-keys.env")
    parser.add_argument("--timeout-seconds", type=float, default=30)
    parser.add_argument("--token", default="")
    parser.add_argument("--username", default="")
    parser.add_argument("--password", default="")
    args = parser.parse_args()

    result = push_keys(
        args.base_url,
        Path(args.source),
        args.timeout_seconds,
        token=args.token,
        username=args.username,
        password=args.password,
    )
    saved_keys = result.get("saved_keys", [])
    print(f"pushed {len(saved_keys)} keys: {', '.join(saved_keys)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
