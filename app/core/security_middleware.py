"""Security-related middleware configuration."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.rate_limit_middleware import RateLimitMiddleware

DEFAULT_DEV_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def parse_cors_origins() -> list[str]:
    configured = os.environ.get("CORS_ORIGINS", "").split(",")
    if configured == [""]:
        return list(DEFAULT_DEV_ORIGINS)
    return [origin.strip() for origin in configured if origin.strip()]


def parse_trusted_hosts(origins: list[str]) -> list[str]:
    configured = os.environ.get("TRUSTED_HOSTS", "")
    if configured.strip():
        hosts = [host.strip() for host in configured.split(",") if host.strip()]
    else:
        hosts = [
            origin.replace("http://", "").replace("https://", "").split(":")[0]
            for origin in origins
        ]

    for internal_host in ("localhost", "127.0.0.1"):
        if internal_host not in hosts:
            hosts.append(internal_host)
    return hosts


def configure_security_middleware(app: FastAPI) -> None:
    origins = parse_cors_origins()

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )

    if origins:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=parse_trusted_hosts(origins),
        )
