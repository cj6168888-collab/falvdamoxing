import uuid

import pytest
from httpx import AsyncClient

from app.db.database import SessionLocal
from app.models.case import Case
from app.models.evidence import EvidenceItem


def _create_case_with_many_reviewed_evidence() -> int:
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        case = Case(
            tenant_id="pytest-tenant",
            title=f"review-purpose-doc-{suffix}",
            case_type="民事",
            plaintiff="甲方公司",
            defendant="乙方公司",
            cause="合同纠纷",
            description="测试人工复核证明目的进入证据目录",
        )
        db.add(case)
        db.flush()

        for index in range(101):
            review_purpose = "人工复核：证明对方确认欠款本金" if index == 0 else f"人工复核证明目的 {index + 1}"
            evidence = EvidenceItem(
                id=str(uuid.uuid4()),
                tenant_id="pytest-tenant",
                case_id=case.id,
                original_filename=f"evidence-{index + 1}.txt",
                display_name=f"证据材料 {index + 1}",
                evidence_type="书证",
                summary="AI 摘要：仅说明双方沟通情况",
                extracted_content="原始内容片段",
                proves_facts=[{"fact": "AI 识别事实"}],
                source_party="己方",
                usage_annotations=[
                    {
                        "type": "fixed_review_fields",
                        "review_status": "reviewed",
                        "reviewed_by": "pytest-user",
                        "reviewed_at": "2026-06-01T07:00:00",
                        "proof_purpose": review_purpose,
                        "original_status": "已核验原件",
                        "authenticity_risk": "低",
                        "legality_risk": "低",
                        "relevance_risk": "直接相关",
                        "strengthening_actions": [],
                    }
                ],
            )
            db.add(evidence)

        db.commit()
        return case.id
    finally:
        db.close()


@pytest.mark.asyncio
async def test_generated_large_evidence_catalog_uses_manual_review_proof_purpose(client: AsyncClient):
    case_id = _create_case_with_many_reviewed_evidence()

    response = await client.post(
        "/api/documents/generate",
        json={
            "case_id": case_id,
            "document_type": "证据目录",
            "custom_requirements": "生成可复核证据目录",
        },
    )

    assert response.status_code == 200, response.text
    content = response.json()["content"]
    assert "人工复核：证明对方确认欠款本金" in content
    assert "证明目的：人工复核：证明对方确认欠款本金" in content
