"""Mixed async HTTP load probe for production-readiness checks.

This script exercises a more realistic authenticated workload than
load_test_api.py: login, case listing, case detail reads, case creation, AI task
queueing, and optional SMS-code sends.

Keep SMS weight at 0 unless the target environment uses a mock provider or the
external provider spend/limits are explicitly approved.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

import httpx


@dataclass
class OperationStats:
    latencies_ms: list[float] = field(default_factory=list)
    status_counts: Counter[int] = field(default_factory=Counter)
    errors: Counter[str] = field(default_factory=Counter)

    @property
    def total(self) -> int:
        return sum(self.status_counts.values()) + sum(self.errors.values())

    def record_status(self, status_code: int, elapsed_ms: float) -> None:
        self.status_counts[status_code] += 1
        self.latencies_ms.append(elapsed_ms)

    def record_error(self, error: Exception, elapsed_ms: float) -> None:
        self.errors[type(error).__name__] += 1
        self.latencies_ms.append(elapsed_ms)


@dataclass
class MixedStats:
    operations: dict[str, OperationStats] = field(
        default_factory=lambda: defaultdict(OperationStats)
    )

    @property
    def total(self) -> int:
        return sum(op.total for op in self.operations.values())

    @property
    def status_counts(self) -> Counter[int]:
        merged: Counter[int] = Counter()
        for op in self.operations.values():
            merged.update(op.status_counts)
        return merged

    @property
    def errors(self) -> Counter[str]:
        merged: Counter[str] = Counter()
        for op in self.operations.values():
            merged.update(op.errors)
        return merged

    @property
    def latencies_ms(self) -> list[float]:
        latencies: list[float] = []
        for op in self.operations.values():
            latencies.extend(op.latencies_ms)
        return latencies

    def record_status(self, operation: str, status_code: int, elapsed_ms: float) -> None:
        self.operations[operation].record_status(status_code, elapsed_ms)

    def record_error(self, operation: str, error: Exception, elapsed_ms: float) -> None:
        self.operations[operation].record_error(error, elapsed_ms)


@dataclass
class ScenarioState:
    case_ids: list[int] = field(default_factory=list)
    sequence: int = 0

    def next_sequence(self) -> int:
        self.sequence += 1
        return self.sequence

    def add_case_id(self, case_id: Any) -> None:
        try:
            normalized = int(case_id)
        except (TypeError, ValueError):
            return
        if normalized not in self.case_ids:
            self.case_ids.append(normalized)

    def choose_case_id(self) -> int | None:
        if not self.case_ids:
            return None
        return random.choice(self.case_ids)


@dataclass(frozen=True)
class Operation:
    name: str
    weight: int
    func: Callable[[httpx.AsyncClient, ScenarioState, MixedStats, argparse.Namespace], Awaitable[None]]


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((percentile / 100) * (len(ordered) - 1))))
    return ordered[index]


def _operation_summary(stats: OperationStats, elapsed_seconds: float) -> dict[str, Any]:
    successes = sum(
        count for status, count in stats.status_counts.items() if 200 <= status < 400
    )
    failures = stats.total - successes
    latencies = stats.latencies_ms
    return {
        "requests": stats.total,
        "successes": successes,
        "failures": failures,
        "error_rate": round(failures / stats.total, 6) if stats.total else 0,
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


def _summary(stats: MixedStats, elapsed_seconds: float) -> dict[str, Any]:
    global_stats = OperationStats(
        latencies_ms=stats.latencies_ms,
        status_counts=stats.status_counts,
        errors=stats.errors,
    )
    return {
        **_operation_summary(global_stats, elapsed_seconds),
        "operations": {
            name: _operation_summary(op_stats, elapsed_seconds)
            for name, op_stats in sorted(stats.operations.items())
        },
    }


async def _login(client: httpx.AsyncClient, username: str, password: str) -> str:
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    response.raise_for_status()
    return response.json()["tokens"]["access_token"]


async def _timed_request(
    stats: MixedStats,
    operation: str,
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    *,
    json_body: dict[str, Any] | None = None,
) -> httpx.Response | None:
    started = time.perf_counter()
    try:
        response = await client.request(method, endpoint, json=json_body)
        elapsed_ms = (time.perf_counter() - started) * 1000
        stats.record_status(operation, response.status_code, elapsed_ms)
        return response
    except Exception as exc:  # noqa: BLE001 - load tool records all failures
        elapsed_ms = (time.perf_counter() - started) * 1000
        stats.record_error(operation, exc, elapsed_ms)
        return None


def _extract_case_ids(payload: Any) -> list[int]:
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            payload = payload["items"]
        elif isinstance(payload.get("cases"), list):
            payload = payload["cases"]
    if not isinstance(payload, list):
        return []

    case_ids: list[int] = []
    for item in payload:
        if isinstance(item, dict) and item.get("id") is not None:
            try:
                case_ids.append(int(item["id"]))
            except (TypeError, ValueError):
                continue
    return case_ids


def _case_payload(args: argparse.Namespace, state: ScenarioState) -> dict[str, Any]:
    sequence = state.next_sequence()
    return {
        "title": f"{args.case_title_prefix}-{int(time.time())}-{sequence}",
        "case_type": "civil",
        "plaintiff": "Load Test Plaintiff",
        "defendant": "Load Test Defendant",
        "description": "Created by scripts/load_test_mixed.py",
    }


async def op_login(
    client: httpx.AsyncClient,
    state: ScenarioState,
    stats: MixedStats,
    args: argparse.Namespace,
) -> None:
    await _timed_request(
        stats,
        "login",
        client,
        "POST",
        "/api/auth/login",
        json_body={"username": args.username, "password": args.password},
    )


async def op_health(
    client: httpx.AsyncClient,
    state: ScenarioState,
    stats: MixedStats,
    args: argparse.Namespace,
) -> None:
    await _timed_request(stats, "health", client, "GET", "/health")


async def op_case_list(
    client: httpx.AsyncClient,
    state: ScenarioState,
    stats: MixedStats,
    args: argparse.Namespace,
) -> None:
    response = await _timed_request(
        stats,
        "case_list",
        client,
        "GET",
        f"/api/cases?limit={args.case_list_limit}",
    )
    if response and 200 <= response.status_code < 300:
        for case_id in _extract_case_ids(response.json()):
            state.add_case_id(case_id)


async def op_case_detail(
    client: httpx.AsyncClient,
    state: ScenarioState,
    stats: MixedStats,
    args: argparse.Namespace,
) -> None:
    case_id = state.choose_case_id()
    if case_id is None:
        await op_case_create(client, state, stats, args)
        return
    await _timed_request(stats, "case_detail", client, "GET", f"/api/cases/{case_id}")


async def op_case_create(
    client: httpx.AsyncClient,
    state: ScenarioState,
    stats: MixedStats,
    args: argparse.Namespace,
) -> None:
    response = await _timed_request(
        stats,
        "case_create",
        client,
        "POST",
        "/api/cases",
        json_body=_case_payload(args, state),
    )
    if response and 200 <= response.status_code < 300:
        try:
            state.add_case_id(response.json().get("id"))
        except ValueError:
            pass


async def op_ai_task_create(
    client: httpx.AsyncClient,
    state: ScenarioState,
    stats: MixedStats,
    args: argparse.Namespace,
) -> None:
    case_id = state.choose_case_id()
    if case_id is None:
        await op_case_create(client, state, stats, args)
        case_id = state.choose_case_id()
    if case_id is None:
        return

    sequence = state.next_sequence()
    await _timed_request(
        stats,
        "ai_task_create",
        client,
        "POST",
        "/api/ai-tasks/create",
        json_body={
            "type": "load_probe",
            "case_id": case_id,
            "title": f"Load probe task {sequence}",
            "params": {"source": "load_test_mixed", "sequence": sequence},
        },
    )


async def op_sms_send(
    client: httpx.AsyncClient,
    state: ScenarioState,
    stats: MixedStats,
    args: argparse.Namespace,
) -> None:
    phone = f"{args.sms_phone_prefix}{random.randint(10_000_000, 99_999_999)}"
    await _timed_request(
        stats,
        "sms_send",
        client,
        "POST",
        "/api/auth/sms/send",
        json_body={"phone": phone, "purpose": "register"},
    )


async def _prime_cases(
    client: httpx.AsyncClient,
    state: ScenarioState,
    args: argparse.Namespace,
) -> None:
    response = await client.get(f"/api/cases?limit={max(args.seed_cases, 20)}")
    response.raise_for_status()
    for case_id in _extract_case_ids(response.json()):
        state.add_case_id(case_id)

    while len(state.case_ids) < args.seed_cases:
        response = await client.post("/api/cases", json=_case_payload(args, state))
        response.raise_for_status()
        state.add_case_id(response.json().get("id"))


def _build_operations(args: argparse.Namespace) -> list[Operation]:
    candidates = [
        Operation("login", args.login_weight, op_login),
        Operation("health", args.health_weight, op_health),
        Operation("case_list", args.case_list_weight, op_case_list),
        Operation("case_detail", args.case_detail_weight, op_case_detail),
        Operation("case_create", args.case_create_weight, op_case_create),
        Operation("ai_task_create", args.ai_task_weight, op_ai_task_create),
        Operation("sms_send", args.sms_weight, op_sms_send),
    ]
    operations = [operation for operation in candidates if operation.weight > 0]
    if not operations:
        raise ValueError("At least one operation weight must be greater than zero.")
    return operations


async def _worker(
    client: httpx.AsyncClient,
    state: ScenarioState,
    stats: MixedStats,
    args: argparse.Namespace,
    operations: list[Operation],
    stop_at: float,
) -> None:
    weights = [operation.weight for operation in operations]
    while time.monotonic() < stop_at:
        operation = random.choices(operations, weights=weights, k=1)[0]
        await operation.func(client, state, stats, args)
        if args.think_ms > 0:
            await asyncio.sleep(args.think_ms / 1000)


async def _run(args: argparse.Namespace) -> int:
    state = ScenarioState()
    stats = MixedStats()
    operations = _build_operations(args)

    limits = httpx.Limits(
        max_connections=max(args.concurrency * 2, 100),
        max_keepalive_connections=max(args.concurrency, 20),
    )
    async with httpx.AsyncClient(
        base_url=args.base_url,
        timeout=args.timeout,
        limits=limits,
        trust_env=False,
    ) as setup_client:
        token = await _login(setup_client, args.username, args.password)

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(
        base_url=args.base_url,
        timeout=args.timeout,
        limits=limits,
        headers=headers,
        trust_env=False,
    ) as client:
        await _prime_cases(client, state, args)
        stop_at = time.monotonic() + args.duration
        started = time.monotonic()
        await asyncio.gather(
            *[
                _worker(client, state, stats, args, operations, stop_at)
                for _ in range(args.concurrency)
            ]
        )
    elapsed = time.monotonic() - started

    result = _summary(stats, elapsed)
    result["scenario"] = {
        "concurrency": args.concurrency,
        "duration_seconds": args.duration,
        "seed_cases": args.seed_cases,
        "known_case_ids": len(state.case_ids),
        "weights": {operation.name: operation.weight for operation in operations},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    failed = False
    if result["error_rate"] > args.max_error_rate:
        failed = True
    if result["latency_ms"]["p95"] > args.target_p95_ms:
        failed = True
    return 1 if failed else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a mixed authenticated API load probe.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--concurrency", type=int, default=100)
    parser.add_argument("--duration", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--think-ms", type=int, default=0)
    parser.add_argument("--target-p95-ms", type=float, default=1500.0)
    parser.add_argument("--max-error-rate", type=float, default=0.01)
    parser.add_argument("--seed-cases", type=int, default=20)
    parser.add_argument("--case-list-limit", type=int, default=50)
    parser.add_argument("--case-title-prefix", default="load-mixed-case")
    parser.add_argument("--sms-phone-prefix", default="139")
    parser.add_argument("--login-weight", type=int, default=5)
    parser.add_argument("--health-weight", type=int, default=5)
    parser.add_argument("--case-list-weight", type=int, default=45)
    parser.add_argument("--case-detail-weight", type=int, default=30)
    parser.add_argument("--case-create-weight", type=int, default=10)
    parser.add_argument("--ai-task-weight", type=int, default=5)
    parser.add_argument("--sms-weight", type=int, default=0)
    args = parser.parse_args()

    if args.concurrency <= 0:
        parser.error("--concurrency must be greater than 0")
    if args.duration <= 0:
        parser.error("--duration must be greater than 0")
    if args.seed_cases < 0:
        parser.error("--seed-cases must be greater than or equal to 0")
    if args.case_list_limit <= 0:
        parser.error("--case-list-limit must be greater than 0")
    return args


def main() -> int:
    return asyncio.run(_run(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
