"""
Celery application entrypoint.

The main API executes most async AI jobs through the in-process task API.
When a broker (Redis / RabbitMQ) is available, tasks are dispatched to Celery
workers; otherwise the system falls back to background threads.

Start a worker (production):
    celery -A app.celery_app worker -Q celery --loglevel=info

Start a worker (development with Redis on localhost):
    CELERY_BROKER_URL=redis://localhost:6379/0 celery -A app.celery_app worker -Q celery --loglevel=info
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

try:
    from celery import Celery  # noqa: F401
    _celery_installed = True
except ImportError:
    _celery_installed = False
    logger.info("Celery not installed — async AI tasks will use background threads.")


def _build_celery_app() -> "Celery | None":
    """Create the Celery application instance, or return None when Celery is
    unavailable (development without worker dependencies)."""
    if not _celery_installed:
        return None

    broker_url = os.environ.get("CELERY_BROKER_URL") or os.environ.get("REDIS_URL")
    result_backend = os.environ.get("CELERY_RESULT_BACKEND") or broker_url

    app = Celery(
        "legal_ai",
        broker=broker_url,
        backend=result_backend,
        include=["app.tasks.celery_tasks"],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Shanghai",
        enable_utc=True,
        task_track_started=True,
    )

    @app.task(name="legal_ai.healthcheck")
    def healthcheck() -> str:
        return "ok"

    return app


celery_app = _build_celery_app()
