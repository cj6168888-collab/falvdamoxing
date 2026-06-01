import uuid

import pytest
from httpx import AsyncClient

from app.db.database import SessionLocal
from app.models.case import Case
from app.models.evidence import EvidenceItem


def _create_evidence_item() -> tuple[int, str]:
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        case = Case(
            tenant_id="pytest-tenant",
            title=f"fixed-review-{suffix}",
            case_type="民事",
            plaintiff="甲方公司",
            defendant="乙方公司",
            description="证据固定审查字段测试案件",
        )
        db.add(case)
        db.flush()

        evidence = EvidenceItem(
            id=str(uuid.uuid4()),
            tenant_id="pytest-tenant",
            case_id=case.id,
            original_filename="chat.png",
            display_name="微信聊天记录截图",
            evidence_type="电子证据",
            summary="双方确认欠款金额",
            proves_facts=["对方确认欠款金额"],
            source_party="己方",
            usage_annotations=[],
        )
        db.add(evidence)
        db.commit()
        return case.id, evidence.id
    finally:
        db.close()


@pytest.mark.asyncio
async def test_evidence_fixed_review_fields_can_be_saved_and_read(client: AsyncClient):
    case_id, evidence_id = _create_evidence_item()

    response = await client.put(
        f"/api/evidence/v2/{evidence_id}/fixed-review",
        json={
            "source": "我方提供",
            "formed_at": "2026-05-30",
            "original_status": "截图，已核验原始手机载体",
            "proof_purpose": "证明对方确认欠款本金",
            "authenticity_risk": "中等，需保留原始聊天记录",
            "legality_risk": "取得方式由我方账号导出",
            "relevance_risk": "与欠款事实直接相关",
            "strengthening_actions": ["补充原始聊天导出文件", "核对对方账号主体"],
            "review_notes": "提交前仍需核验上下文完整性",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert data["review"]["reviewed_by"] == "pytest-user"
    assert data["review"]["proof_purpose"] == "证明对方确认欠款本金"
    assert data["review"]["strengthening_actions"] == ["补充原始聊天导出文件", "核对对方账号主体"]

    list_response = await client.get(
        "/api/v2/evidence-graph/evidence/list",
        params={"case_id": case_id},
    )
    assert list_response.status_code == 200, list_response.text
    listed = list_response.json()["evidence_list"]
    stored = next(item for item in listed if item["id"] == evidence_id)
    assert stored["evidence_review"]["review_status"] == "reviewed"
    assert stored["evidence_review"]["proof_purpose"] == "证明对方确认欠款本金"


@pytest.mark.asyncio
async def test_evidence_fixed_review_requires_proof_purpose(client: AsyncClient):
    _, evidence_id = _create_evidence_item()

    response = await client.put(
        f"/api/evidence/v2/{evidence_id}/fixed-review",
        json={
            "source": "我方提供",
            "original_status": "原件状态待核验",
            "proof_purpose": "   ",
            "authenticity_risk": "待核验",
            "legality_risk": "待核验",
            "relevance_risk": "待核验",
            "strengthening_actions": [],
        },
    )

    assert response.status_code == 400, response.text
    assert "证明目的不能为空" in response.text
