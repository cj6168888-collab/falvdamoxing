"""
Celery application entrypoint.

The main API currently executes most async AI jobs through the in-process task
API. This module exists so the production celery profile starts cleanly and can
host queued tasks as the app migrates heavier workflows out of web workers.
"""

from __future__ import annotations

import os

from celery import Celery


broker_url = os.environ.get("CELERY_BROKER_URL") or os.environ.get("REDIS_URL")
result_backend = os.environ.get("CELERY_RESULT_BACKEND") or broker_url

celery_app = Celery(
    "legal_ai",
    broker=broker_url,
    backend=result_backend,
    include=[],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(name="legal_ai.healthcheck")
def healthcheck() -> str:
    return "ok"
