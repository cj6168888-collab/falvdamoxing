"""
法律大模型 — Windows 客户端 轻量版 FastAPI 应用

去除 PostgreSQL/Redis/Celery 依赖，仅用 SQLite + 内存存储
"""
import os
import sys

os.environ.setdefault("APP_ENV", "client")
os.environ.setdefault("DB_TYPE", "sqlite")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/legal_client.db")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("SMS_PROVIDER", "console")
os.environ.setdefault("PYTHONUNBUFFERED", "1")

# 强制使用 SQLite 以避免 PostgreSQL 导入问题
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'legal_client.db')}"

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

FRONTEND_DIR = Path(__file__).parent / "dist"
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.database import init_db
    init_db()
    yield


def create_client_app() -> FastAPI:
    app = FastAPI(
        title="法律大模型 - 桌面客户端",
        version="2.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 API 路由（跳过需要 PostgreSQL 的模块）
    from app.api.system import router as sys_router
    from app.api.auth import router as auth_router
    from app.api.case import router as case_router
    from app.api.evidence import router as evidence_router
    from app.api.document import router as doc_router
    from app.api.hearing import router as hearing_router
    from app.api.appeal import router as appeal_router
    from app.api.execution import router as exec_router
    from app.api.dashboard import router as dash_router
    from app.api.smart_chat import router as chat_router
    from app.api.tenant_api import router as tenant_router
    from app.api.config_api import router as config_router

    app.include_router(sys_router)
    app.include_router(auth_router)
    app.include_router(case_router)
    app.include_router(evidence_router)
    app.include_router(doc_router)
    app.include_router(hearing_router)
    app.include_router(appeal_router)
    app.include_router(exec_router)
    app.include_router(dash_router)
    app.include_router(chat_router)
    app.include_router(tenant_router)
    app.include_router(config_router)

    # 注册轻量版路由
    try:
        from app.api.advisory_api import router as adv_router
        app.include_router(adv_router)
        from app.api.insight_api import router as ins_router
        app.include_router(ins_router)
        from app.api.export_api import router as exp_router
        app.include_router(exp_router)
    except Exception:
        pass

    # 前端静态文件
    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

    return app


app = create_client_app()
