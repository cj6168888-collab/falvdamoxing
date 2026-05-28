"""Shared HTTP handlers and response middleware."""

from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def configure_http_handlers(
    app: FastAPI,
    logger: logging.Logger | None = None,
) -> None:
    active_logger = logger or logging.getLogger(__name__)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        active_logger.error("[全局异常] %s %s", request.method, request.url)
        active_logger.error("[异常类型] %s", type(exc).__name__)
        active_logger.error("[异常信息] %s", str(exc))
        active_logger.error("[堆栈跟踪]\n%s", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"服务器内部错误: {str(exc)}",
                "type": type(exc).__name__,
            },
            headers={"content-type": "application/json; charset=utf-8"},
        )

    @app.middleware("http")
    async def ensure_utf8_charset(request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type and "charset" not in content_type:
            response.headers["content-type"] = "application/json; charset=utf-8"
        return response
