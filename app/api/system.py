"""System-level API endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings
from app.monitoring.metrics import get_metrics
from app.monitoring.readiness import check_readiness

router = APIRouter()


@router.get("/")
def root():
    return {
        "name": "法律大模型辅助系统 API",
        "version": settings.api_version,
        "status": "running",
    }


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.get("/ready")
def readiness_check():
    checks = check_readiness()
    ready = all(check["status"] in ("ok", "skipped") for check in checks.values())
    status_code = 200 if ready else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if ready else "not_ready", "checks": checks},
    )


@router.get("/metrics")
def metrics():
    return get_metrics()
