from app.api import streaming_analysis
from app.core.tenant_context import TenantContext
import pytest


class InlineThread:
    def __init__(self, target, daemon=False):
        self.target = target
        self.daemon = daemon

    def start(self):
        self.target()


class FakeDB:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_start_analysis_uses_sessionlocal_and_completes_thread(monkeypatch):
    fake_db = FakeDB()
    calls = []
    context_calls = []

    def fake_run_full_analysis(task_id, task, db):
        calls.append((task_id, task["case_id"], db))
        context_calls.append(
            (TenantContext.get_tenant_id(), TenantContext.get_user_id())
        )
        streaming_analysis._update_task(
            task_id,
            status="completed",
            progress=1.0,
            result={"custom": "done"},
        )

    monkeypatch.setattr(streaming_analysis, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(streaming_analysis, "_run_full_analysis", fake_run_full_analysis)
    monkeypatch.setattr(streaming_analysis.threading, "Thread", InlineThread)

    task_id = "stream-task"
    with streaming_analysis._tasks_lock:
        streaming_analysis._tasks.clear()
        streaming_analysis._tasks[task_id] = {
            "task_id": task_id,
            "case_id": 12,
            "status": "pending",
            "progress": 0.0,
            "result": None,
            "error": None,
        }

    TenantContext.set_tenant("tenant-thread")
    TenantContext.set_user("user-thread")
    response = streaming_analysis.start_analysis(task_id)

    task = streaming_analysis._get_task(task_id)
    assert response == {"message": "分析已启动"}
    assert calls == [(task_id, 12, fake_db)]
    assert context_calls == [("tenant-thread", "user-thread")]
    assert TenantContext.get_tenant_id() == "tenant-thread"
    assert TenantContext.get_user_id() == "user-thread"
    assert fake_db.closed is True
    assert task["status"] == "completed"
    assert task["progress"] == 1.0
    assert task["result"] == {"custom": "done"}


@pytest.mark.asyncio
async def test_stream_analysis_yields_each_chunk_once():
    task_id = "stream-completed"
    with streaming_analysis._tasks_lock:
        streaming_analysis._tasks.clear()
        streaming_analysis._tasks[task_id] = {
            "task_id": task_id,
            "case_id": 12,
            "status": "completed",
            "progress": 1.0,
            "chunks": [
                {"type": "content", "content": "first"},
                {"type": "complete", "taskId": task_id},
            ],
        }

    response = await streaming_analysis.stream_analysis(task_id, request=object())

    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)

    assert chunks == [
        'data: {"type": "content", "content": "first"}\n\n',
        f'data: {{"type": "complete", "taskId": "{task_id}"}}\n\n',
    ]
