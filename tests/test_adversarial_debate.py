import asyncio

import pytest

from app.api import adversarial as adversarial_api
from app.db.database import SessionLocal
from app.models.adversarial_analysis import AdversarialAnalysis, AnalysisPhase
from app.models.case import Case
from app.services import llm_service as llm_service_module


class FakeDebateLLM:
    def opponent_analysis(self, **kwargs):
        return "opponent attack: challenge contract validity and payment proof."

    def our_side_analysis(self, **kwargs):
        evidence = kwargs.get("our_evidence") or "core evidence"
        return f"our response: use {evidence} to prove performance and breach."

    def judge_evaluation(self, **kwargs):
        return "judge evaluation: payment facts and loss calculation are key."

    def strategy_synthesis(self, **kwargs):
        return "strategy report: focus on contract validity and damages."

    def user_interaction(self, case_info, debate_context, user_question):
        return f"followup response: incorporated {user_question}."


class FailingDebateLLM(FakeDebateLLM):
    def opponent_analysis(self, **kwargs):
        raise RuntimeError("llm exploded")


class StrategyFallbackDebateLLM(FakeDebateLLM):
    def strategy_synthesis(self, **kwargs):
        return "请求出错，请稍后重试"


class FakeRedis:
    def __init__(self):
        self.values = {}

    def ping(self):
        return True

    def setex(self, key, ttl, value):
        self.values[key] = value
        return True

    def get(self, key):
        return self.values.get(key)


@pytest.fixture(autouse=True)
def clear_debate_state():
    adversarial_api.辩论状态存储.clear()
    adversarial_api._辩论状态_redis_client = None
    yield
    adversarial_api.辩论状态存储.clear()
    adversarial_api._辩论状态_redis_client = None


def _create_case(title: str = "debate regression case") -> int:
    db = SessionLocal()
    case = Case(
        title=title,
        case_type="民事",
        plaintiff="our company",
        defendant="opponent company",
        cause="contract dispute",
        description="the parties dispute performance and payment proof.",
        legal_analysis="contract formation is likely; proof of performance is central.",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    case_id = case.id
    db.close()
    return case_id


async def _wait_for_terminal_progress(client, prefix: str, debate_id: str) -> dict:
    progress = {}
    for _ in range(100):
        await asyncio.sleep(0.02)
        response = await client.get(f"{prefix}/debate/{debate_id}/progress")
        assert response.status_code == 200
        progress = response.json()
        if progress.get("status") in {"completed", "failed"}:
            return progress
    pytest.fail(f"debate did not finish: {progress}")


@pytest.mark.asyncio
async def test_debate_stream_runs_requested_rounds_and_persists(client, monkeypatch):
    monkeypatch.setattr(llm_service_module, "llm_service", FakeDebateLLM())
    case_id = _create_case()

    response = await client.post(
        f"/api/adversarial/case/{case_id}/debate-stream",
        json={
            "debate_rounds": 6,
            "analysis_phase": "litigation",
            "our_evidence": "payment voucher",
            "opponent_evidence": "chat records",
        },
    )

    assert response.status_code == 200
    debate_id = response.json()["debate_id"]
    progress = await _wait_for_terminal_progress(client, "/api/adversarial", debate_id)

    assert progress["status"] == "completed"
    assert progress["current_round"] == 6
    assert len(progress["rounds"]) == 6
    assert progress["analysis_id"]
    assert "strategy report" in progress["final_report"]

    continue_response = await client.post(
        f"/api/adversarial/debate/{debate_id}/continue",
        json={"user_input": "add trial questioning points"},
    )
    assert continue_response.status_code == 200
    assert "followup response" in continue_response.json()["response"]

    db = SessionLocal()
    analysis = db.query(AdversarialAnalysis).filter(
        AdversarialAnalysis.id == progress["analysis_id"]
    ).first()
    assert analysis is not None
    assert analysis.is_current is True
    assert analysis.analysis_phase == AnalysisPhase.LITIGATION
    assert "strategy report" in analysis.overall_strategy
    db.close()


@pytest.mark.asyncio
async def test_english_debate_route_uses_shared_real_implementation(client, monkeypatch):
    monkeypatch.setattr(llm_service_module, "llm_service", FakeDebateLLM())
    case_id = _create_case("english debate regression case")

    response = await client.post(
        f"/api/en/adversarial-analysis/case/{case_id}/debate-stream",
        json={"debate_rounds": 5},
    )

    assert response.status_code == 200
    debate_id = response.json()["debate_id"]
    progress = await _wait_for_terminal_progress(
        client, "/api/en/adversarial-analysis", debate_id
    )

    assert progress["status"] == "completed"
    assert progress["current_round"] == 5
    assert len(progress["rounds"]) == 5
    assert progress["analysis_id"]


@pytest.mark.asyncio
async def test_debate_progress_survives_worker_local_memory_miss(client, monkeypatch):
    monkeypatch.setattr(llm_service_module, "llm_service", FakeDebateLLM())
    adversarial_api._辩论状态_redis_client = FakeRedis()
    case_id = _create_case("redis backed debate regression case")

    response = await client.post(
        f"/api/adversarial/case/{case_id}/debate-stream",
        json={"debate_rounds": 4},
    )

    assert response.status_code == 200
    debate_id = response.json()["debate_id"]
    progress = await _wait_for_terminal_progress(client, "/api/adversarial", debate_id)
    assert progress["status"] == "completed"

    adversarial_api.辩论状态存储.clear()
    progress_response = await client.get(f"/api/adversarial/debate/{debate_id}/progress")
    assert progress_response.status_code == 200
    redis_progress = progress_response.json()

    assert redis_progress["status"] == "completed"
    assert redis_progress["current_round"] == 4
    assert redis_progress["analysis_id"] == progress["analysis_id"]


@pytest.mark.asyncio
async def test_debate_stream_reports_failed_status_when_llm_fails(client, monkeypatch):
    monkeypatch.setattr(llm_service_module, "llm_service", FailingDebateLLM())
    case_id = _create_case("failing debate regression case")

    response = await client.post(
        f"/api/adversarial/case/{case_id}/debate-stream",
        json={"debate_rounds": 6},
    )

    assert response.status_code == 200
    debate_id = response.json()["debate_id"]
    progress = await _wait_for_terminal_progress(client, "/api/adversarial", debate_id)

    assert progress["status"] == "failed"
    assert "llm exploded" in progress["error"]
    assert progress["current_thinking"] == {}
    assert progress.get("analysis_id") is None


@pytest.mark.asyncio
async def test_debate_stream_uses_fallback_report_when_strategy_synthesis_is_unusable(client, monkeypatch):
    monkeypatch.setattr(llm_service_module, "llm_service", StrategyFallbackDebateLLM())
    case_id = _create_case("strategy fallback debate regression case")

    response = await client.post(
        f"/api/adversarial/case/{case_id}/debate-stream",
        json={"debate_rounds": 4},
    )

    assert response.status_code == 200
    debate_id = response.json()["debate_id"]
    progress = await _wait_for_terminal_progress(client, "/api/adversarial", debate_id)

    assert progress["status"] == "completed"
    assert progress["analysis_id"]
    assert progress["warning"]
    assert "降级战略报告" in progress["final_report"]
    assert "opponent attack" in progress["final_report"]
    assert "请求出错，请稍后重试" in progress["rounds"][-1]["content"]
    assert len(progress["final_report"]) > 300

    db = SessionLocal()
    analysis = db.query(AdversarialAnalysis).filter(
        AdversarialAnalysis.id == progress["analysis_id"]
    ).first()
    assert analysis is not None
    assert "降级战略报告" in analysis.overall_strategy
    assert len(analysis.overall_strategy) > 300
    db.close()


@pytest.mark.asyncio
async def test_adversarial_analysis_update_maps_chinese_fields(client):
    case_id = _create_case("field mapping regression case")
    create_response = await client.post(
        f"/api/adversarial/case/{case_id}/analysis",
        json={"标题": "manual analysis", "分析阶段": "协商"},
    )
    assert create_response.status_code == 200
    analysis_id = create_response.json()["id"]

    update_response = await client.put(
        f"/api/adversarial/{analysis_id}",
        json={
            "总体策略": "mapped strategy",
            "我方优势": "mapped strengths",
            "分析阶段": "诉讼",
        },
    )
    assert update_response.status_code == 200

    db = SessionLocal()
    analysis = db.query(AdversarialAnalysis).filter(
        AdversarialAnalysis.id == analysis_id
    ).first()
    assert analysis.overall_strategy == "mapped strategy"
    assert analysis.our_strengths == "mapped strengths"
    assert analysis.analysis_phase == AnalysisPhase.LITIGATION
    db.close()
