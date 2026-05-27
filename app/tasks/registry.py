"""Background task handler registration."""

from __future__ import annotations

import importlib


TASK_HANDLER_MODULES = (
    "app.tasks.document_generate",
    "app.tasks.senior_analysis",
    "app.tasks.report_generate",
    "app.tasks.adversarial",
)


def register_task_handlers() -> None:
    for module_name in TASK_HANDLER_MODULES:
        importlib.import_module(module_name)
