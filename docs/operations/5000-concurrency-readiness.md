# 5000 Concurrent Customer Readiness

This project should not be declared ready for 5000 concurrent customers until
the production stack passes a repeatable load test against PostgreSQL, Redis,
object storage, and the configured LLM/SMS providers.

## Baseline Architecture

- API: multiple Uvicorn worker processes per backend container, configured by
  `WEB_CONCURRENCY`.
- Database: PostgreSQL only for production; tune SQLAlchemy with
  `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`,
  `DB_POOL_RECYCLE_SECONDS`, and `DB_POOL_PRE_PING`.
- Redis: required for distributed rate limits and Celery broker/backend.
- AI workloads: heavy analysis/report generation must run through Celery
  workers, not inside web request workers.
- Tenant safety: all customer-owned ORM models must carry `tenant_id`, and
  RAG queries must include tenant metadata filters.

## Suggested Starting Point

For four backend containers on a PostgreSQL instance capped at 500 connections:

- `WEB_CONCURRENCY=4`
- `EXPECTED_APP_REPLICAS=4`
- `DB_POOL_SIZE=15`
- `DB_MAX_OVERFLOW=10`
- `POSTGRES_MAX_CONNECTIONS=500`
- `POSTGRES_RESERVED_CONNECTIONS=80`
- `AUTH_CONTEXT_CACHE_SECONDS=10`
- `PGBOUNCER_ENABLED=1`
- `PGBOUNCER_POOL_MODE=transaction`
- `PGBOUNCER_MAX_CLIENT_CONN=2000`
- `PGBOUNCER_DEFAULT_POOL_SIZE=80`
- `PGBOUNCER_RESERVE_POOL_SIZE=40`

The validator checks:

```text
WEB_CONCURRENCY * EXPECTED_APP_REPLICAS * (DB_POOL_SIZE + DB_MAX_OVERFLOW)
<= POSTGRES_MAX_CONNECTIONS - POSTGRES_RESERVED_CONNECTIONS
```

Without PgBouncer this prevents the API fleet from opening more SQLAlchemy
connections than PostgreSQL can accept. With PgBouncer enabled, the validator
checks two separate limits:

- app worker pools must fit within `PGBOUNCER_MAX_CLIENT_CONN`;
- `PGBOUNCER_DEFAULT_POOL_SIZE + PGBOUNCER_RESERVE_POOL_SIZE` must fit within
  PostgreSQL's available connection budget.

Keep the PostgreSQL reserve for migrations, admin sessions, Celery workers,
monitoring, and emergency access. Migrations should connect directly to
PostgreSQL with `MIGRATION_DATABASE_URL`; web workers should connect through
PgBouncer with `DATABASE_URL`.

`AUTH_CONTEXT_CACHE_SECONDS` keeps JWT signature verification on every request,
but avoids hitting the database for the same active user/tenant pair on every
hot read request. Set it to `0` if immediate user-disable propagation is more
important than read-path throughput.

Scale horizontally by adding backend containers behind Nginx or a cloud load
balancer. Keep total possible database connections under PostgreSQL limits, or
add PgBouncer before raising replica counts.

## Production Gates

Run the production configuration validator before deployment:

```bash
python scripts/validate_production_config.py .env.prod
```

The application must fail deployment instead of silently downgrading when these
requirements are missing:

- `DATABASE_URL` must point to PostgreSQL or another production database, not
  SQLite.
- `USE_REDIS_RATE_LIMIT=1` and `REDIS_URL`/`REDIS_PASSWORD` must be configured.
- `REDIS_RATE_LIMIT_ALLOW_FALLBACK` should stay disabled for production; Redis
  failures should fail closed instead of switching each worker to independent
  memory limits.
- `WEB_CONCURRENCY` must be at least `2`.
- `POSTGRES_MAX_CONNECTIONS` must be declared and high enough for
  `WEB_CONCURRENCY`, `EXPECTED_APP_REPLICAS`, `DB_POOL_SIZE`, and
  `DB_MAX_OVERFLOW`.
- If `PGBOUNCER_ENABLED=1`, PgBouncer client and server pool limits must be
  declared and internally consistent with PostgreSQL capacity.
- `SMS_PROVIDER=http`, `SMS_HTTP_ENDPOINT`, `SMS_HTTP_TOKEN`, and
  `SMS_DEBUG_RETURN_CODE=0` must be configured.

In `docker-compose.prod.yml`, API and frontend containers are exposed only on
the internal Docker network; Nginx is the public entrypoint. This keeps
`docker compose up --scale app=N` from colliding on host ports.

## Local Staging Stack

Use the staging compose file to verify the production shape without real SMS
credentials:

```powershell
.\scripts\run_staging_capacity.ps1 -HealthConcurrency 200 -ApiConcurrency 200 -DurationSeconds 30 -AppReplicas 4
```

The staging stack uses PostgreSQL, Redis, Nginx, multiple API replicas, and a
local HTTP SMS mock. It is suitable for engineering validation, but it is not a
substitute for final production SMS-provider and infrastructure testing. Its
rate-limit thresholds are intentionally higher than production defaults so a
single load-test client does not turn the test into a rate-limit check.

### Verified Local Staging Results

Last verified on 2026-05-15 with four API replicas, PgBouncer, PostgreSQL,
Redis, Nginx, and the local SMS mock:

- Production-like config validation: passed.
- Focused backend regression tests for config, readiness, tenant auth cache,
  and Redis rate limiting: 43 passed.
- `/api/cases`, 200 concurrency, 30 seconds: 16,545 requests, 0 failures,
  545.54 rps, p95 869.56 ms.
- `/api/cases`, 300 concurrency, 30 seconds: 13,913 requests, 0 failures,
  453.61 rps, p95 1301.89 ms.
- During the 300-concurrency sample, PostgreSQL reported 81 total connections
  against `max_connections=500`.

These numbers prove the current local staging shape handles 200 authenticated
business-read concurrency with the scripted gate and can absorb a 300-concurrent
exploratory run on this machine. They do not prove 5000 concurrent customers;
that claim still requires a production-infrastructure load test with the real
database size, object storage, network, SMS provider, and LLM provider limits.

Mixed workload checks added on 2026-05-15 cover login, case listing, case
details, case creation, AI task queueing, and staging SMS sends. The latest
local mixed run with 40 concurrency and `--sms-weight 1` had 1,368 requests, 0
failures, 66.93 rps, and p95 1882.29 ms, which misses the 1500 ms gate. An
80-concurrency mixed run also had 0 failures but p95 5301.51 ms. Metrics showed
the bottleneck was app/container CPU and request scheduling, not PostgreSQL
connection exhaustion. Treat this as the next scaling target before any 5000
concurrent-customer claim.

## Load Probe

Run a smoke probe first:

```bash
python scripts/load_test_api.py --base-url http://localhost:8000 --endpoint /health --concurrency 100 --duration 30
```

Run authenticated read load:

```bash
python scripts/load_test_api.py --base-url http://localhost:8000 --username admin --password secret --endpoint /api/cases --concurrency 500 --duration 60 --target-p95-ms 500
```

Raise concurrency in stages: 500, 1000, 2000, 5000. Stop when error rate exceeds
1%, p95 exceeds the agreed target, PostgreSQL saturates, Redis saturates, or web
worker CPU stays above 80% for more than five minutes.

Run a mixed authenticated workload before claiming production readiness:

```powershell
python scripts/load_test_mixed.py `
  --base-url http://127.0.0.1:8080 `
  --username loadtest-admin `
  --password loadtest-password-123456 `
  --concurrency 500 `
  --duration 60 `
  --target-p95-ms 1500 `
  --max-error-rate 0.01
```

The mixed probe covers login, case list, case detail, case creation, and AI task
queueing. Add `--sms-weight 1` only in staging or when real SMS-provider cost
and rate limits are approved.

Capture platform metrics while the load test runs:

```powershell
.\scripts\collect_staging_metrics.ps1 -Samples 24 -IntervalSeconds 5
```

The metrics JSONL includes compose health, container CPU/memory/network stats,
PostgreSQL connection state, PostgreSQL database size, and Redis stats/memory.
Attach the JSONL to the load-test result so bottlenecks can be attributed.

## AI Cross-Tenant Guardrail

RAG retrieval now has two boundaries:

- Vector-store query filters include `case_id` and the current `tenant_id`.
- Application code discards any returned chunk whose metadata does not match the
  requested `case_id` and current `tenant_id` before building the LLM context.

Each RAG search also writes an `ai_retrieval_audits` record with `tenant_id`,
`user_id`, `case_id`, query hash, query preview, retrieved document IDs,
retrieved chunk IDs, and source count. This does not make model hallucination
mathematically impossible, but it creates an enforceable boundary and a forensic
trail for investigating any suspected "cross-case" response.

## Acceptance Criteria

- `/health` p95 under 200 ms at target concurrency.
- Authenticated read p95 under 500 ms at target concurrency.
- Mutating workflows p95 target defined per route; no duplicate writes.
- Error rate below 1% excluding intentional rate-limit responses.
- PostgreSQL connection usage below 80% of max capacity.
- Redis memory and CPU stable.
- Celery queue latency bounded for AI jobs; web worker latency must not depend
  on long-running LLM calls.
