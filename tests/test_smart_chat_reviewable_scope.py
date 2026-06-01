import uuid

import pytest
from httpx import AsyncClient

from app.db.database import SessionLocal
from app.models.case import Case
from app.models.evidence import EvidenceItem


def _create_case_with_review_scope_evidence() -> int:
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        case = Case(
            tenant_id="pytest-tenant",
            title=f"smart-chat-reviewable-scope-{suffix}",
            case_type="民事",
            plaintiff="甲方公司",
            defendant="乙方公司",
            cause="合同纠纷",
            description="测试智能对话可复核证据范围",
        )
        db.add(case)
        db.flush()

        reviewed = EvidenceItem(
            id=str(uuid.uuid4()),
            tenant_id="pytest-tenant",
            case_id=case.id,
            original_filename="chat-export.txt",
            display_name="微信聊天导出记录",
            evidence_type="电子证据",
            summary="对方确认欠款本金",
            extracted_content="乙方确认仍欠甲方本金 100000 元",
            usage_annotations=[
                {
                    "type": "fixed_review_fields",
                    "review_status": "reviewed",
                    "reviewed_by": "pytest-user",
                    "reviewed_at": "2026-06-01T07:00:00",
                    "original_status": "已核验原始导出文件",
                    "proof_purpose": "证明对方确认欠款本金",
                    "authenticity_risk": "需保留原始聊天记录",
                    "legality_risk": "由我方账号依法导出",
                    "relevance_risk": "与欠款确认直接相关",
                    "strengthening_actions": ["补充原始聊天导出文件"],
                }
            ],
        )
        unreviewed = EvidenceItem(
            id=str(uuid.uuid4()),
            tenant_id="pytest-tenant",
            case_id=case.id,
            original_filename="receipt.pdf",
            display_name="付款凭证",
            evidence_type="书证",
            summary="付款记录摘要",
            extracted_content="付款 100000 元",
            usage_annotations=[],
        )
        db.add(reviewed)
        db.add(unreviewed)
        db.commit()
        return case.id
    finally:
        db.close()


@pytest.mark.asyncio
async def test_global_analysis_returns_reviewable_evidence_scope(client: AsyncClient, monkeypatch):
    from app.api import smart_chat

    case_id = _create_case_with_review_scope_evidence()
    captured_prompts = []

    def fake_chat(messages, model=None):
        captured_prompts.append(messages[-1]["content"])
        return "## 模型分析\n基于证据继续分析。"

    monkeypatch.setattr(smart_chat.llm_service, "chat", fake_chat)
    monkeypatch.setattr(smart_chat.intelligence_service, "get_summary_for_ai", lambda db, case_id: "案件档案摘要")
    monkeypatch.setattr(smart_chat.intelligence_service, "sync_intelligence", lambda db, case_id, content: {})

    response = await client.post(
        "/api/smart-chat/global-analysis",
        json={
            "case_id": case_id,
            "fact_description": "对方已经确认欠款但未付款",
            "user_role": "原告",
        },
    )

    assert response.status_code == 200, response.text
    content = response.json()["full_analysis"]
    assert "## 已读取证据范围" in content
    assert "当前系统证据总数：2 份" in content
    assert "人工复核状态：已完成固定字段复核 1 份；未完整复核 1 份" in content
    assert "证明目的：证明对方确认欠款本金" in content
    assert "真实性：需保留原始聊天记录" in content
    assert "合法性：由我方账号依法导出" in content
    assert "关联性：与欠款确认直接相关" in content
    assert "付款凭证》：未完成人工复核" in content
    assert "## 工作底稿核验清单" in content
    assert "## 模型分析" in content

    assert captured_prompts
    assert "【服务端已读取证据范围与核验清单】" in captured_prompts[0]
    assert "当前系统证据总数：2 份" in captured_prompts[0]

