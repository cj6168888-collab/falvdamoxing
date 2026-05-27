"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import register_routes
from app.config import assert_production_settings
from app.config import settings
from app.core.http_handlers import configure_http_handlers
from app.core.security_middleware import configure_security_middleware
from app.core.tenant_middleware import configure_tenant_middleware
from app.db.database import init_db
from app.monitoring.readiness import ensure_file_storage_directory
from app.services.folder_watcher_lifecycle import resume_folder_watchers
from app.services.folder_watcher_lifecycle import stop_folder_watchers
from app.services.runtime_config import load_runtime_config_into_environ
from app.tasks.registry import register_task_handlers

logger = logging.getLogger(__name__)

_resume_folder_watchers = resume_folder_watchers
_stop_folder_watchers = stop_folder_watchers


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_runtime_config_into_environ()
    assert_production_settings()
    init_db()
    _resume_folder_watchers()
    yield
    _stop_folder_watchers()


def create_app(
    *,
    include_static_files: bool = True,
    include_task_handlers: bool = True,
) -> FastAPI:
    application = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    if include_static_files:
        application.mount(
            "/api/files",
            StaticFiles(directory=ensure_file_storage_directory()),
            name="files",
        )
    configure_http_handlers(application, logger=logger)
    configure_security_middleware(application)
    configure_tenant_middleware(application)
    register_routes(application, logger=logger)
    if include_task_handlers:
        register_task_handlers()
    return application
