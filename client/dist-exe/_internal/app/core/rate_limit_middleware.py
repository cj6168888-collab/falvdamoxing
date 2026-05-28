"""ASGI middleware for API rate limiting."""

from __future__ import annotations

import json

from app.core.rate_limiter import get_rate_limiter

RATE_LIMIT_EXEMPT_PATHS = {
    "/",
    "/docs",
    "/health",
    "/openapi.json",
    "/ready",
    "/redoc",
}


def _client_id_from_scope(scope: dict) -> str:
    for key, value in scope.get("headers", []):
        if key == b"x-forwarded-for":
            forwarded_for = value.split(b",")[0].strip()
            return forwarded_for.decode(errors="replace")

    client_info = scope.get("client")
    if client_info:
        return str(client_info[0])
    return "unknown"


class RateLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in RATE_LIMIT_EXEMPT_PATHS:
            await self.app(scope, receive, send)
            return

        allowed, message = get_rate_limiter().is_allowed(_client_id_from_scope(scope))
        if not allowed:
            response_body = json.dumps({"detail": message}).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [(b"content-type", b"application/json; charset=utf-8")],
                }
            )
            await send({"type": "http.response.body", "body": response_body})
            return

        await self.app(scope, receive, send)
