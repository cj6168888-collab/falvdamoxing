"""Small async HTTP load probe for API capacity checks.

Example:
    python scripts/load_test_api.py --base-url http://localhost:8000 \
      --username admin --password secret --endpoint /api/cases \
      --concurrency 500 --duration 60 --target-p95-ms 500
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class LoadStats:
    latencies_ms: list[float] = field(default_factory=list)
    status_counts: Counter[int] = field(default_factory=Counter)
    errors: Counter[str] = field(default_factory=Counter)

    def record_status(self, status_code: int, elapsed_ms: float) -> None:
        self.status_counts[status_code] += 1
        self.latencies_ms.append(elapsed_ms)

    def record_error(self, error: Exception, elapsed_ms: float) -> None:
        self.errors[type(error).__name__] += 1
        self.latencies_ms.append(elapsed_ms)

    @property
    def total(self) -> int:
        return sum(self.status_counts.values()) + sum(self.errors.values())


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((percentile / 100) * (len(ordered) - 1))))
    return ordered[index]


async def _login(args: argparse.Namespace) -> str | None:
    if not args.username:
        return None

    async with httpx.AsyncClient(
        base_url=args.base_url,
        timeout=args.timeout,
        trust_env=False,
    ) as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": args.username, "password": args.password},
        )
        response.raise_for_status()
        data = response.json()
        return data["tokens"]["access_token"]


async def _worker(
    worker_id: int,
    args: argparse.Namespace,
    token: str | None,
    stop_at: float,
    stats: LoadStats,
) -> None:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    limits = httpx.Limits(
        max_connections=max(args.concurrency * 2, 100),
        max_keepalive_connections=max(args.concurrency, 20),
    )
    async with httpx.AsyncClient(
        base_url=args.base_url,
        timeout=args.timeout,
        limits=limits,
        headers=headers,
        trust_env=False,
    ) as client:
        while time.monotonic() < stop_at:
            started = time.perf_counter()
            try:
                response = await client.request(
                    args.method,
                    args.endpoint,
                    json=args.json_body,
                )
                elapsed_ms = (time.perf_counter() - started) * 1000
                stats.record_status(response.status_code, elapsed_ms)
            except Exception as exc:  # noqa: BLE001 - load tool records all failures
                elapsed_ms = (time.perf_counter() - started) * 1000
                stats.record_error(exc, elapsed_ms)

            if args.think_ms > 0:
                await asyncio.sleep(args.think_ms / 1000)


def _summary(stats: LoadStats, elapsed_seconds: float) -> dict[str, Any]:
    successes = sum(
        count for status, count in stats.status_counts.items() if 200 <= status < 400
    )
    failures = stats.total - successes
    error_rate = failures / stats.total if stats.total else 1.0
    latencies = stats.latencies_ms
    return {
        "requests": stats.total,
        "successes": successes,
        "failures": failures,
        "error_rate": round(error_rate, 6),
        "rps": round(stats.total / elapsed_seconds, 2) if elapsed_seconds else 0,
        "latency_ms": {
            "min": round(min(latencies), 2) if latencies else 0,
            "avg": round(statistics.fmean(latencies), 2) if latencies else 0,
            "p50": round(_percentile(latencies, 50), 2),
            "p95": round(_percentile(latencies, 95), 2),
            "p99": round(_percentile(latencies, 99), 2),
            "max": round(max(latencies), 2) if latencies else 0,
        },
        "status_counts": dict(sorted(stats.status_counts.items())),
        "errors": dict(stats.errors),
    }


async def _run(args: argparse.Namespace) -> int:
    token = await _login(args)
    stats = LoadStats()
    stop_at = time.monotonic() + args.duration
    started = time.monotonic()
    await asyncio.gather(
        *[
            _worker(worker_id, args, token, stop_at, stats)
            for worker_id in range(args.concurrency)
        ]
    )
    elapsed = time.monotonic() - started
    result = _summary(stats, elapsed)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    failed = False
    if result["error_rate"] > args.max_error_rate:
        failed = True
    if result["latency_ms"]["p95"] > args.target_p95_ms:
        failed = True
    return 1 if failed else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an async API load probe.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--endpoint", default="/health")
    parser.add_argument("--method", default="GET", choices=["GET", "POST"])
    parser.add_argument("--username", default="")
    parser.add_argument("--password", default="")
    parser.add_argument("--json", dest="json_body", default=None)
    parser.add_argument("--concurrency", type=int, default=100)
    parser.add_argument("--duration", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--think-ms", type=int, default=0)
    parser.add_argument("--target-p95-ms", type=float, default=500.0)
    parser.add_argument("--max-error-rate", type=float, default=0.01)
    args = parser.parse_args()
    if args.concurrency <= 0:
        parser.error("--concurrency must be greater than 0")
    if args.duration <= 0:
        parser.error("--duration must be greater than 0")
    if args.username and not args.password:
        parser.error("--password is required when --username is set")
    if args.json_body:
        args.json_body = json.loads(args.json_body)
    return args


def main() -> int:
    return asyncio.run(_run(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
