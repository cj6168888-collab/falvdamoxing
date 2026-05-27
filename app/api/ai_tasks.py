"""Unified asynchronous AI task API."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case import Case
from app.services.ai_task_service import AITaskExecutor
from app.services.ai_task_service import InMemoryAITaskRegistry
from app.services.ai_task_service import ThreadedAITaskExecutor
from app.services.ai_task_service import ai_task_registry
from app.services.ai_task_service import case_exists
from app.services.ai_task_service import cleanup_old_tasks
from app.services.ai_task_service import create_pending_task
from app.services.ai_task_service import execute_registered_task
from app.services.ai_task_service import get_task
from app.services.ai_task_service import register_task_handler
from app.services.ai_task_service import serialize_task
from app.services.ai_task_service import set_task_executor
from app.services.ai_task_service import update_task

router = APIRouter(prefix="/api/ai-tasks", tags=["AI async tasks"])

__all__ = [
    "AITaskExecutor",
    "CreateTaskRequest",
    "InMemoryAITaskRegistry",
    "TaskResponse",
    "ThreadedAITaskExecutor",
    "_cleanup_old_tasks",
    "_get_task",
    "_serialize_task",
    "_update_task",
    "ai_task_registry",
    "register_task_handler",
    "router",
    "set_task_executor",
]


class CreateTaskRequest(BaseModel):
    type: str
    case_id: int
    title: str
    params: dict = Field(default_factory=dict)


class TaskResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    message: str
    type: str
    title: str
    case_id: int
    created_at: str
    result: Optional[Any] = None
    error: Optional[str] = None
    completed_at: Optional[str] = None


class CreateTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskListResponse(BaseModel):
    tasks: list[dict[str, Any]]
    total: int


class MessageResponse(BaseModel):
    message: str


def _update_task(task_id: str, **kwargs) -> None:
    update_task(task_id, **kwargs)


def _get_task(task_id: str) -> Optional[dict]:
    return get_task(task_id)


def _cleanup_old_tasks() -> None:
    cleanup_old_tasks()


def _serialize_task(task: dict) -> dict:
    return serialize_task(task)


@router.post("/create", response_model=CreateTaskResponse)
def create_task(request: CreateTaskRequest, db: Session = Depends(get_db)):
    if not case_exists(db, Case, request.case_id):
        raise HTTPException(status_code=404, detail="Case not found")

    task_data = create_pending_task(
        task_type=request.type,
        case_id=request.case_id,
        title=request.title,
        params=request.params,
    )
    return {
        "task_id": task_data["task_id"],
        "status": "pending",
        "message": "Task created. Poll with task_id for status.",
    }


@router.get("/list", response_model=TaskListResponse)
def list_tasks(case_id: Optional[int] = None, status: Optional[str] = None):
    _cleanup_old_tasks()
    tasks = ai_task_registry.list_tasks(case_id=case_id, status=status)
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_status(task_id: str):
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _serialize_task(task)


@router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(task_id: str):
    if ai_task_registry.delete_task(task_id):
        return {"message": "Task deleted"}
    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/execute", response_model=MessageResponse)
def execute_task(task_id: str):
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    handler = ai_task_registry.get_handler(task["type"])
    if not handler:
        _update_task(task_id, status="failed", error=f"Unsupported task type: {task['type']}")
        raise HTTPException(status_code=400, detail=f"Unsupported task type: {task['type']}")

    execute_registered_task(task_id, task, handler)
    return {"message": "Task started"}
