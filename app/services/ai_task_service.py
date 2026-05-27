"""In-memory AI task registry and execution primitives."""

from __future__ import annotations

from datetime import datetime
import threading
import time
from typing import Any, Callable, Dict, Optional, TypedDict
import uuid


class AITaskData(TypedDict):
    task_id: str
    type: str
    case_id: int
    title: str
    params: dict[str, Any]
    status: str
    progress: float
    message: str
    result: Any
    error: Optional[str]
    created_at: str
    created_ts: float
    completed_at: Optional[str]


class SerializedAITask(TypedDict):
    task_id: str
    type: str
    case_id: int
    title: str
    status: str
    progress: float
    message: str
    result: Any
    error: Optional[str]
    created_at: str
    completed_at: Optional[str]


AITaskHandler = Callable[[str, AITaskData], None]


class InMemoryAITaskRegistry:
    def __init__(self) -> None:
        self._tasks: Dict[str, AITaskData] = {}
        self._handlers: Dict[str, AITaskHandler] = {}
        self._lock = threading.Lock()

    def add_task(self, task_id: str, task_data: AITaskData) -> None:
        with self._lock:
            self._tasks[task_id] = task_data

    def get_task(self, task_id: str) -> Optional[AITaskData]:
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].update(kwargs)

    def delete_task(self, task_id: str) -> bool:
        with self._lock:
            if task_id not in self._tasks:
                return False
            del self._tasks[task_id]
            return True

    def list_tasks(
        self,
        *,
        case_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> list[AITaskData]:
        with self._lock:
            tasks = list(self._tasks.values())

        if case_id is not None:
            tasks = [task for task in tasks if task["case_id"] == case_id]
        if status:
            tasks = [task for task in tasks if task["status"] == status]
        return sorted(tasks, key=lambda task: task.get("created_ts", 0), reverse=True)

    def cleanup_old_tasks(self, *, now: Optional[float] = None) -> None:
        active_now = time.time() if now is None else now
        with self._lock:
            to_remove = [
                task_id
                for task_id, task in self._tasks.items()
                if task.get("status") in ("completed", "failed")
                and active_now - task.get("created_ts", 0) > 3600
            ]
            for task_id in to_remove:
                del self._tasks[task_id]

    def register_handler(self, task_type: str, func: AITaskHandler):
        self._handlers[task_type] = func
        return func

    def get_handler(self, task_type: str):
        return self._handlers.get(task_type)

    def clear_tasks(self) -> None:
        with self._lock:
            self._tasks.clear()

    def clear_handlers(self) -> None:
        self._handlers.clear()


class AITaskExecutor:
    def submit(self, func: Callable[[], None]) -> None:
        raise NotImplementedError


class ThreadedAITaskExecutor(AITaskExecutor):
    def submit(self, func: Callable[[], None]) -> None:
        thread = threading.Thread(target=func, daemon=True)
        thread.start()


ai_task_registry = InMemoryAITaskRegistry()
task_executor: AITaskExecutor = ThreadedAITaskExecutor()


def set_task_executor(executor: AITaskExecutor) -> None:
    global task_executor
    task_executor = executor


def update_task(task_id: str, **kwargs) -> None:
    ai_task_registry.update_task(task_id, **kwargs)


def get_task(task_id: str) -> Optional[AITaskData]:
    return ai_task_registry.get_task(task_id)


def cleanup_old_tasks() -> None:
    ai_task_registry.cleanup_old_tasks()


def case_exists(db, case_model, case_id: int) -> bool:
    return db.query(case_model).filter(case_model.id == case_id).first() is not None


def create_pending_task(
    *,
    task_type: str,
    case_id: int,
    title: str,
    params: dict,
) -> AITaskData:
    task_id = str(uuid.uuid4())[:12]
    task_data: AITaskData = {
        "task_id": task_id,
        "type": task_type,
        "case_id": case_id,
        "title": title,
        "params": params,
        "status": "pending",
        "progress": 0.0,
        "message": "Task submitted and waiting for execution.",
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "created_ts": time.time(),
        "completed_at": None,
    }
    ai_task_registry.add_task(task_id, task_data)
    return task_data


def serialize_task(task: AITaskData) -> SerializedAITask:
    return {
        "task_id": task["task_id"],
        "type": task["type"],
        "case_id": task["case_id"],
        "title": task["title"],
        "status": task["status"],
        "progress": task["progress"],
        "message": task["message"],
        "result": task.get("result"),
        "error": task.get("error"),
        "created_at": task["created_at"],
        "completed_at": task.get("completed_at"),
    }


def register_task_handler(task_type: str):
    def decorator(func: AITaskHandler):
        return ai_task_registry.register_handler(task_type, func)

    return decorator


def execute_registered_task(task_id: str, task: AITaskData, handler: AITaskHandler) -> None:
    update_task(task_id, status="running", progress=0.0, message="Task started.")

    def run_task():
        try:
            handler(task_id, task)
        except Exception as exc:
            update_task(
                task_id,
                status="failed",
                error=str(exc),
                message=f"Execution failed: {exc}",
                completed_at=datetime.now().isoformat(),
            )

    task_executor.submit(run_task)
