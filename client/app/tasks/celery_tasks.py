"""
Celery task wrappers for the four async AI task handlers.

These mirror the in-process handlers in app/tasks/*.py but are executed by
Celery workers instead of background threads.

When Celery is not installed or the broker is unreachable, the system falls
back to threaded execution automatically (see ai_task_service.py).
"""
from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.services.ai_task_service import update_task
from datetime import datetime

logger = logging.getLogger(__name__)

_CELERY_AVAILABLE = celery_app is not None


def _run_handler(task_id: str, task: dict, handler_name: str) -> None:
    """Import and invoke a registered handler, syncing progress to the
    in-memory registry so the polling API still reflects current state."""
    update_task(task_id, status="running",
                message=f"Celery worker picked up {handler_name}")

    try:
        from app.services.ai_task_service import ai_task_registry

        handler = ai_task_registry.get_handler(handler_name)
        if not handler:
            update_task(task_id, status="failed",
                        error=f"No handler registered for {handler_name}",
                        completed_at=datetime.now().isoformat())
            return

        handler(task_id, task)
    except Exception as exc:
        update_task(task_id, status="failed", error=str(exc),
                    message=f"Celery task {handler_name} raised an exception",
                    completed_at=datetime.now().isoformat())
        raise


if _CELERY_AVAILABLE:

    @celery_app.task(name="legal_ai.adversarial", bind=True, max_retries=2, default_retry_delay=30)
    def run_adversarial(self, task_id: str, task: dict) -> None:
        _run_handler(task_id, task, "adversarial")

    @celery_app.task(name="legal_ai.senior_analysis", bind=True, max_retries=2, default_retry_delay=30)
    def run_senior_analysis(self, task_id: str, task: dict) -> None:
        _run_handler(task_id, task, "senior_analysis")

    @celery_app.task(name="legal_ai.report_generate", bind=True, max_retries=2, default_retry_delay=30)
    def run_report_generate(self, task_id: str, task: dict) -> None:
        _run_handler(task_id, task, "report_generate")

    @celery_app.task(name="legal_ai.document_generate", bind=True, max_retries=2, default_retry_delay=30)
    def run_document_generate(self, task_id: str, task: dict) -> None:
        _run_handler(task_id, task, "document_generate")

else:
    # Placeholders so that import-time references don't crash.
    # The CeleryTaskExecutor in ai_task_service.py handles fallback.
    run_adversarial = None       # type: ignore[assignment]
    run_senior_analysis = None   # type: ignore[assignment]
    run_report_generate = None   # type: ignore[assignment]
    run_document_generate = None  # type: ignore[assignment]

    logger.info("Celery not available — task stubs registered (thread fallback active).")
