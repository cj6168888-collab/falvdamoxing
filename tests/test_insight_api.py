from datetime import datetime
from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.core.tenant_context import TenantContext
from app.db.database import SessionLocal
from app.models.document import Document


async def _create_case(client: AsyncClient, title_prefix: str = "增强分析") -> int:
    response = await client.post(
        "/api/cases",
        json={
            "title": f"{title_prefix}-{datetime.utcnow().timestamp()}",
            "case_type": "civil",
            "cause": "买卖合同纠纷",
            "plaintiff": "甲方公司",
            "defendant": "乙方公司",
            "claim_amount": "10000",
            "description": "用于验证增强分析 API 的测试案件。",
        },
    )
    assert response.status_code in [200, 201], response.text
    return response.json()["id"]


def _create_evidence_document(case_id: int) -> int:
    TenantContext.set_tenant("pytest-tenant")
    TenantContext.set_user("pytest-user")
    db = SessionLocal()
    try:
        doc = Document(
            case_id=case_id,
            filename="付款凭证-增强分析.txt",
            stored_path="/tmp/payment-evidence.txt",
            file_type="txt",
            file_size=128,
            doc_type="证据-付款凭证",
            content="甲方公司于2026年5月1日向乙方公司支付10000元。",
            content_summary="付款凭证摘要",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc.id
    finally:
        db.close()


class FakeInsightEngine:
    def __init__(self):
        self.invalidated_case_ids = []
        self.analysis_cache = {}
        self.graph_nodes = {}
        self.last_question = None

    async def answer_with_clarification(self, question, case_info, context=""):
        self.last_question = question
        return {
            "needs_clarification": False,
            "intent": "strategy_query",
            "key_entities": [case_info["plaintiff"], case_info["defendant"]],
            "clarifying_questions": [],
            "answer": f"{case_info['title']} 的策略建议：围绕付款凭证和合同履行抗辩。",
        }

    def invalidate_cache(self, case_id=None):
        self.invalidated_case_ids.append(case_id)

    async def generate_report_streaming(self, case_id, report_type, case_info, on_progress=None):
        cache_key = f"{case_id}_{report_type}_{datetime.now().strftime('%Y%m%d')}"
        segments = [
            {"title": "一、案件事实", "content": "双方存在合同履行争议。", "progress": 0.5},
            {"title": "二、策略建议", "content": "优先固定付款凭证。", "progress": 1.0},
        ]
        self.analysis_cache[cache_key] = SimpleNamespace(
            status=SimpleNamespace(value="已完成"),
            progress=1.0,
            segments=segments,
            error=None,
        )
        if on_progress:
            await on_progress(0.5, "生成中: 一、案件事实")
            await on_progress(1.0, "生成中: 二、策略建议")
        yield "\n\n一、案件事实\n双方存在合同履行争议。"
        yield "\n\n二、策略建议\n优先固定付款凭证。"

    async def build_evidence_graph(self, case_id, evidence_list):
        node = SimpleNamespace(
            evidence_id=evidence_list[0]["id"],
            name=evidence_list[0]["name"],
            evidence_type=evidence_list[0]["type"],
            credibility=0.91,
            credibility_factors=["银行流水来源明确"],
            proves_facts=["证明付款事实"],
            related_evidence=[],
            contradicts_evidence=[],
            keywords=["付款", "银行流水"],
        )
        self.graph_nodes[case_id] = [node]
        return [node]

    def get_evidence_summary(self, case_id):
        return {
            "total_count": len(self.graph_nodes.get(case_id, [])),
            "by_type": {"PAYMENT": 1},
            "average_credibility": 0.91,
            "high_credibility_count": 1,
            "low_credibility_count": 0,
            "keywords": ["付款", "银行流水"],
        }

    async def query_evidence(self, case_id, query, search_type="all"):
        return [
            node
            for node in self.graph_nodes.get(case_id, [])
            if query in node.name or query in node.keywords
        ]

    async def _analyze_evidence_credibility(self, evidence):
        return {
            "score": 0.91,
            "factors": ["原始付款凭证"],
            "proves_facts": ["证明付款事实"],
        }

    async def _extract_evidence_keywords(self, evidence):
        return ["付款", "合同履行"]


@pytest.mark.asyncio
async def test_insight_question_report_status_and_cache(client: AsyncClient, monkeypatch):
    from app.api import insight_api

    fake_engine = FakeInsightEngine()
    monkeypatch.setattr(insight_api, "get_insight_engine", lambda: fake_engine)
    case_id = await _create_case(client, "增强问答报告")

    question_response = await client.post(
        "/api/v2/question",
        json={"case_id": case_id, "question": "下一步诉讼策略是什么？"},
    )
    assert question_response.status_code == 200, question_response.text
    question_data = question_response.json()
    assert question_data["needs_clarification"] is False
    assert "付款凭证" in question_data["answer"]

    clarified_response = await client.post(
        "/api/v2/question/answer",
        json={
            "case_id": case_id,
            "question": "下一步诉讼策略是什么？",
            "answers": {"补充事实": "对方已收款但拒绝履行"},
        },
    )
    assert clarified_response.status_code == 200, clarified_response.text
    assert clarified_response.json()["needs_clarification"] is False
    assert "对方已收款但拒绝履行" in fake_engine.last_question

    report_response = await client.post(
        "/api/v2/report/generate",
        json={"case_id": case_id, "report_type": "analysis", "force_regenerate": True},
    )
    assert report_response.status_code == 200, report_response.text
    report_data = report_response.json()
    assert report_data["report_type"] == "analysis"
    assert "一、案件事实" in report_data["content"]
    assert report_data["word_count"] == len(report_data["content"])
    assert fake_engine.invalidated_case_ids == [case_id]

    status_response = await client.get(f"/api/v2/report/status/{case_id}?report_type=analysis")
    assert status_response.status_code == 200, status_response.text
    status_data = status_response.json()
    assert status_data["status"] == "已完成"
    assert status_data["progress"] == 1.0
    assert status_data["segments"][0]["title"] == "一、案件事实"

    clear_response = await client.post(f"/api/v2/cache/clear/{case_id}")
    assert clear_response.status_code == 200, clear_response.text
    assert clear_response.json()["cleared_items"] == ["report_cache", "analysis_cache"]
    assert fake_engine.invalidated_case_ids == [case_id, case_id]


@pytest.mark.asyncio
async def test_insight_evidence_graph_query_and_credibility(client: AsyncClient, monkeypatch):
    from app.api import insight_api

    fake_engine = FakeInsightEngine()
    monkeypatch.setattr(insight_api, "get_insight_engine", lambda: fake_engine)
    case_id = await _create_case(client, "增强证据图谱")
    document_id = _create_evidence_document(case_id)

    graph_response = await client.post(
        "/api/v2/evidence/graph",
        json={"case_id": case_id, "force_refresh": True},
    )
    assert graph_response.status_code == 200, graph_response.text
    graph_data = graph_response.json()
    assert graph_data["case_id"] == case_id
    assert graph_data["total_evidence"] == 1
    assert graph_data["nodes"][0]["name"] == "付款凭证-增强分析.txt"
    assert graph_data["nodes"][0]["credibility"] == 0.91
    assert graph_data["summary"]["high_credibility_count"] == 1

    query_response = await client.get(
        f"/api/v2/evidence/query/{case_id}?query=付款&search_type=keywords"
    )
    assert query_response.status_code == 200, query_response.text
    query_data = query_response.json()
    assert query_data["count"] == 1
    assert query_data["results"][0]["keywords"] == ["付款", "银行流水"]

    credibility_response = await client.get(f"/api/v2/evidence/credibility/{document_id}")
    assert credibility_response.status_code == 200, credibility_response.text
    credibility_data = credibility_response.json()
    assert credibility_data["evidence_id"] == document_id
    assert credibility_data["credibility_score"] == 0.91
    assert "证明付款事实" in credibility_data["proves_facts"]
