import pytest
import importlib
from fastapi import FastAPI

from app.api.ai_tasks import router as ai_tasks_router
from app.api.ai_tasks import get_db
from app.api.ai_tasks import AITaskExecutor
from app.api.ai_tasks import ThreadedAITaskExecutor
from app.api.ai_tasks import register_task_handler
from app.api.ai_tasks import set_task_executor
import app.services.ai_task_service as ai_task_service
from app.services.ai_task_service import InMemoryAITaskRegistry
from app.services.ai_task_service import ai_task_registry
from app.services.ai_task_service import case_exists
from app.services.ai_task_service import create_pending_task
from app.services.ai_task_service import serialize_task


class InlineAITaskExecutor(AITaskExecutor):
    def submit(self, func):
        func()


@pytest.fixture(autouse=True)
def clear_ai_tasks():
    ai_task_registry.clear_tasks()
    ai_task_registry.clear_handlers()
    set_task_executor(InlineAITaskExecutor())
    yield
    ai_task_registry.clear_tasks()
    ai_task_registry.clear_handlers()
    set_task_executor(ThreadedAITaskExecutor())


def _task(task_id, *, case_id=1, status="pending", created_ts=1):
    return {
        "task_id": task_id,
        "type": "test",
        "case_id": case_id,
        "title": f"Task {task_id}",
        "params": {},
        "status": status,
        "progress": 0.0,
        "message": "pending",
        "result": None,
        "error": None,
        "created_at": "2026-05-10T00:00:00",
        "created_ts": created_ts,
        "completed_at": None,
    }


def test_registry_filters_and_sorts_tasks():
    registry = InMemoryAITaskRegistry()
    registry.add_task("old", _task("old", case_id=1, status="pending", created_ts=1))
    registry.add_task("new", _task("new", case_id=1, status="completed", created_ts=2))
    registry.add_task("other", _task("other", case_id=2, status="pending", created_ts=3))

    assert [task["task_id"] for task in registry.list_tasks(case_id=1)] == ["new", "old"]
    assert [task["task_id"] for task in registry.list_tasks(status="pending")] == [
        "other",
        "old",
    ]


def test_registry_cleans_completed_and_failed_tasks_only_after_ttl():
    registry = InMemoryAITaskRegistry()
    registry.add_task("pending", _task("pending", status="pending", created_ts=0))
    registry.add_task("recent", _task("recent", status="completed", created_ts=100))
    registry.add_task("old", _task("old", status="failed", created_ts=0))

    registry.cleanup_old_tasks(now=3601)

    assert registry.get_task("pending") is not None
    assert registry.get_task("recent") is not None
    assert registry.get_task("old") is None


def test_create_pending_task_stores_params_and_serializes_public_fields():
    task = create_pending_task(
        task_type="test",
        case_id=5,
        title="Generated task",
        params={"depth": "full"},
    )

    assert ai_task_registry.get_task(task["task_id"])["params"] == {"depth": "full"}
    serialized = serialize_task(task)
    assert serialized["task_id"] == task["task_id"]
    assert serialized["type"] == "test"
    assert "created_ts" not in serialized
    assert "params" not in serialized


def test_case_exists_uses_case_model_id_filter():
    class FakeCase:
        id = 10

    class FakeQuery:
        def __init__(self, result):
            self.result = result
            self.filter_args = None

        def filter(self, *args):
            self.filter_args = args
            return self

        def first(self):
            return self.result

    class FakeDB:
        def __init__(self, result):
            self.query_obj = FakeQuery(result)

        def query(self, model):
            assert model is FakeCase
            return self.query_obj

    assert case_exists(FakeDB(object()), FakeCase, 10) is True
    assert case_exists(FakeDB(None), FakeCase, 10) is False


@pytest.mark.asyncio
async def test_ai_task_list_route_is_not_shadowed_by_task_id_route(client):
    ai_task_registry.add_task("t1", _task("t1"))

    response = await client.get("/api/ai-tasks/list")

    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_create_get_and_delete_task_routes(client, lightweight_app):
    class FakeCase:
        id = 1

    class FakeQuery:
        def __init__(self, result):
            self.result = result

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return self.result

    class FakeDB:
        def __init__(self, result):
            self.result = result

        def query(self, model):
            return FakeQuery(self.result)

    def override_get_db():
        yield FakeDB(object())

    lightweight_app.dependency_overrides[get_db] = override_get_db

    create_response = await client.post(
        "/api/ai-tasks/create",
        json={
            "type": "test",
            "case_id": 1,
            "title": "Route task",
            "params": {"source": "test"},
        },
    )
    assert create_response.status_code == 200
    task_id = create_response.json()["task_id"]
    assert ai_task_registry.get_task(task_id)["params"] == {"source": "test"}

    get_response = await client.get(f"/api/ai-tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Route task"

    delete_response = await client.delete(f"/api/ai-tasks/{task_id}")
    assert delete_response.status_code == 200
    assert ai_task_registry.get_task(task_id) is None


@pytest.mark.asyncio
async def test_create_task_route_returns_404_when_case_is_missing(client, lightweight_app):
    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

    class FakeDB:
        def query(self, model):
            return FakeQuery()

    def override_get_db():
        yield FakeDB()

    lightweight_app.dependency_overrides[get_db] = override_get_db

    response = await client.post(
        "/api/ai-tasks/create",
        json={"type": "test", "case_id": 404, "title": "Missing case"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"


@pytest.mark.asyncio
async def test_execute_task_marks_task_failed_when_handler_is_missing(client):
    ai_task_registry.add_task("missing-handler", _task("missing-handler", status="pending"))
    ai_task_registry.update_task("missing-handler", type="__missing_handler__")

    response = await client.post("/api/ai-tasks/missing-handler/execute")

    assert response.status_code == 400
    task = ai_task_registry.get_task("missing-handler")
    assert task["status"] == "failed"
    assert "Unsupported task type" in task["error"]


@pytest.mark.asyncio
async def test_execute_task_uses_configured_executor_for_success(client):
    calls = []
    ai_task_registry.add_task("sync-success", _task("sync-success", status="pending"))

    @register_task_handler("test")
    def handler(task_id, task):
        calls.append((task_id, task["status"]))
        ai_task_registry.update_task(
            task_id,
            status="completed",
            progress=1.0,
            result={"ok": True},
        )

    response = await client.post("/api/ai-tasks/sync-success/execute")

    assert response.status_code == 200
    assert calls == [("sync-success", "running")]
    task = ai_task_registry.get_task("sync-success")
    assert task["status"] == "completed"
    assert task["result"] == {"ok": True}


@pytest.mark.asyncio
async def test_get_task_status_includes_completion_payload(client):
    task = _task("completed-payload", status="completed")
    task["result"] = {"summary": "done"}
    task["error"] = None
    task["completed_at"] = "2026-05-17T00:00:01"
    ai_task_registry.add_task("completed-payload", task)

    response = await client.get("/api/ai-tasks/completed-payload")

    assert response.status_code == 200
    body = response.json()
    assert body["result"] == {"summary": "done"}
    assert body["error"] is None
    assert body["completed_at"] == "2026-05-17T00:00:01"


@pytest.mark.asyncio
async def test_execute_task_records_handler_exception(client):
    ai_task_registry.add_task("sync-failure", _task("sync-failure", status="pending"))

    @register_task_handler("test")
    def handler(task_id, task):
        raise RuntimeError("boom")

    response = await client.post("/api/ai-tasks/sync-failure/execute")

    assert response.status_code == 200
    task = ai_task_registry.get_task("sync-failure")
    assert task["status"] == "failed"
    assert task["error"] == "boom"
    assert "Execution failed" in task["message"]


def test_set_task_executor_replaces_executor():
    executor = InlineAITaskExecutor()

    set_task_executor(executor)

    assert ai_task_service.task_executor is executor


def test_senior_analysis_task_uses_current_engine_entry(monkeypatch):
    senior_task_module = importlib.import_module("app.tasks.senior_analysis")
    senior_task_module = importlib.reload(senior_task_module)

    class FakeQuery:
        def filter(self, *args):
            return self

        def first(self):
            return object()

    class FakeDB:
        def query(self, model):
            return FakeQuery()

        def close(self):
            pass

    calls = []

    class FakeSeniorLawyerEngine:
        def analyze_case(self, *, case_id, analysis_level):
            calls.append({"case_id": case_id, "analysis_level": analysis_level})
            return {
                "status": "success",
                "summary": {"overall_assessment": "案件准备较为充分"},
            }

    import app.services.senior_lawyer_engine as senior_engine_module

    monkeypatch.setattr(senior_task_module, "SessionLocal", lambda: FakeDB())
    monkeypatch.setattr(
        senior_engine_module,
        "senior_lawyer_engine",
        FakeSeniorLawyerEngine(),
    )

    task = _task("senior-current-engine", case_id=88)
    task["type"] = "senior_analysis"
    task["params"] = {"depth": "deep"}
    ai_task_registry.add_task(task["task_id"], task)

    senior_task_module.handle_senior_analysis(task["task_id"], task)

    stored = ai_task_registry.get_task(task["task_id"])
    assert ai_task_registry.get_handler("senior_analysis") is not None
    assert calls == [{"case_id": 88, "analysis_level": "deep"}]
    assert stored["status"] == "completed"
    assert stored["progress"] == 1.0
    assert stored["result"]["analysis_level"] == "deep"
    assert stored["result"]["summary"]["overall_assessment"] == "案件准备较为充分"


def test_ai_task_routes_publish_response_models():
    app = FastAPI()
    app.include_router(ai_tasks_router)

    schema = app.openapi()
    paths = schema["paths"]

    assert (
        paths["/api/ai-tasks/create"]["post"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        == "#/components/schemas/CreateTaskResponse"
    )
    assert (
        paths["/api/ai-tasks/list"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        == "#/components/schemas/TaskListResponse"
    )
    assert (
        paths["/api/ai-tasks/{task_id}"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        == "#/components/schemas/TaskResponse"
    )
    assert (
        paths["/api/ai-tasks/{task_id}/execute"]["post"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        == "#/components/schemas/MessageResponse"
    )
