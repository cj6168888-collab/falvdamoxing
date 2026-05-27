# Production Images

The production backend image is intentionally split into small capability layers.
The default API image starts without ChromaDB, OCR engines, local ML packages, or
Celery. Those features are installed only when their build args are enabled.

## Default API image

```bash
docker build -f Dockerfile.prod -t legal-ai-assistant:latest .
```

Includes:

- FastAPI API server
- database clients
- document parsing and export dependencies
- Redis client for rate limiting
- only the backend runtime files copied by `Dockerfile.prod`

Excludes:

- ChromaDB vector store
- PaddleOCR, Tesseract, local ML packages
- Celery worker packages
- curl and extra OS graphics libraries
- local databases, exports, frontend artifacts, tests, and diagnostic scripts

`Dockerfile.prod` uses an explicit copy allowlist (`app`, `migrations`, and the
database init script) instead of `COPY . .`. Keep runtime data mounted through
Compose volumes rather than baking it into the image.

## Worker image

```bash
docker build \
  -f Dockerfile.prod \
  --build-arg INSTALL_WORKER=true \
  -t legal-ai-assistant-worker:latest .
```

The worker image installs `requirements-worker.txt`, currently `celery[redis]`.
It does not install ChromaDB or OCR packages.

Use it through the compose profile:

```bash
docker compose -f docker-compose.prod.yml --profile celery up -d
```

In production, set these image references in `.env.prod` when pulling from a
registry:

```env
BACKEND_IMAGE=ghcr.io/your-org/your-repo:<tag>
WORKER_IMAGE=ghcr.io/your-org/your-repo-worker:<tag>
```

The CD workflow updates those values automatically before deploying the API
service. If the Celery profile is enabled on the server, run the same compose
profile command after the image values are updated.

The workflow builds and deploys immutable image references tagged with the full
Git commit SHA. Branch, version, and `latest` tags are still published for
operator convenience, but production rollout uses the full-SHA tag so the exact
artifact is unambiguous.

Production deployments are serialized by the CD workflow. The container
healthcheck stays on lightweight `/health`, while the deploy step checks
`/ready` from inside the refreshed API container before pruning old images.
`/ready` verifies database connectivity, writable file storage, and Redis when
Redis rate limiting is enabled. It also checks that core database tables already
exist. If the readiness check does not pass, the workflow prints recent app logs
and fails the deployment.

Production should keep `AUTO_CREATE_TABLES=0` so application startup does not
silently mutate the database schema. Run the database migration process before
deploying a new application image; development and CI can opt in with
`AUTO_CREATE_TABLES=1` when they need disposable tables.
The migration command records `migrate_all_v1` in the `schema_migrations` table;
production `/ready` requires that marker when `AUTO_CREATE_TABLES=0`.

Run migrations through the one-off compose profile before starting the refreshed
API container:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml --profile migrate run --rm migrate
```

The CD workflow runs this command automatically after pulling the new backend
image, then runs the non-mutating `--check` verification before restarting the
API service.
The migration entrypoint serializes concurrent runs: PostgreSQL uses an
advisory lock, and SQLite uses a sibling `.migrate.lock` file.
For a non-mutating verification, run the same image with:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm app python -m app.db.migrate_all --check
```

The Docker smoke job follows the same contract: it runs the migration command
against a disposable database volume, starts the API with `AUTO_CREATE_TABLES=0`,
and requires `/ready` to pass. This keeps CI aligned with production startup
behavior.

When using `docker-compose.prod.yml` directly, keep `.env.prod` beside the
compose file. The services load runtime environment from that file, and passing
it with `--env-file` also lets Compose resolve image variables:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml pull app
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --no-deps app
```

For private GHCR images, log in on the target host first:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin
```

## Optional ML/OCR image

```bash
docker build \
  -f Dockerfile.prod \
  --build-arg INSTALL_OPTIONAL_ML=true \
  -t legal-ai-assistant:ml .
```

This installs `requirements-optional.txt` and the OS libraries needed by heavier
OCR/vector/local-ML features. Use it only when those capabilities are required.

## Combined worker plus optional ML

```bash
docker build \
  -f Dockerfile.prod \
  --build-arg INSTALL_WORKER=true \
  --build-arg INSTALL_OPTIONAL_ML=true \
  -t legal-ai-assistant-worker:ml .
```

## Runtime behavior without optional features

- RAG document indexing becomes a no-op when ChromaDB is unavailable.
- RAG search returns an empty context instead of blocking API startup.
- Development embeddings use deterministic placeholder vectors when no provider
  API key is configured.
- OCR falls back according to the parser chain and reports unavailable engines
  without preventing core document uploads.

## Pre-release acceptance

Before exposing the stack beyond an internal/pre-production environment, run the
project-specific acceptance gate in
[`pre-release-acceptance.md`](./pre-release-acceptance.md). It records the
required Docker preflight, migration check, Bokai evidence-chain AI audit, data
lifecycle audit, browser route audit, database cleanup check, and rollback
criteria.

The helper scripts are:

- `scripts/production-backup.ps1` for PostgreSQL `pg_dump` backups.
- `scripts/production-restore.ps1` for explicit confirmed rollback restores.
- `scripts/production-release-gate.ps1` for preflight, backup, migration check,
  Bokai audits, and residue verification.
