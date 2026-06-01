import uuid

import pytest
from httpx import AsyncClient

from app.db.database import SessionLocal
from app.models.case import Case
from app.models.evidence import EvidenceItem


def _create_case_with_reviewed_evidence() -> int:
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        case = Case(
            tenant_id="pytest-tenant",
            title=f"evidence-book-review-{suffix}",
            case_type="民事",
            plaintiff="甲方公司",
            defendant="乙方公司",
            cause="合同纠纷",
            description="证据册人工复核字段导出测试",
        )
        db.add(case)
        db.flush()

        evidence = EvidenceItem(
            id=str(uuid.uuid4()),
            tenant_id="pytest-tenant",
            case_id=case.id,
            original_filename="chat-export.txt",
            display_name="微信聊天记录导出文件",
            evidence_type="电子证据",
            summary="AI 摘要：双方确认欠款沟通过程",
            extracted_content="对方在聊天中确认尚欠本金。",
            proves_facts=[{"fact": "AI 识别：对方承认欠款"}],
            source_party="我方",
            usage_annotations=[
                {
                    "type": "fixed_review_fields",
                    "review_status": "reviewed",
                    "reviewed_by": "pytest-user",
                    "reviewed_at": "2026-06-01T07:00:00",
                    "source": "我方账号导出",
                    "formed_at": "2026-05-30",
                    "proof_purpose": "人工复核：证明对方确认欠款本金",
                    "original_status": "已核验原始聊天导出文件",
                    "authenticity_risk": "需保留原始聊天记录",
                    "legality_risk": "由我方账号依法导出",
                    "relevance_risk": "与欠款确认直接相关",
                    "strengthening_actions": ["补充原始聊天导出文件", "核对对方账号主体"],
                    "review_notes": "提交前核验上下文完整性",
                }
            ],
        )
        db.add(evidence)
        db.commit()
        return case.id
    finally:
        db.close()


@pytest.mark.asyncio
async def test_evidence_book_export_includes_manual_review_fields(client: AsyncClient):
    case_id = _create_case_with_reviewed_evidence()

    response = await client.get(f"/api/evidence/export-book/{case_id}", params={"format": "markdown"})

    assert response.status_code == 200, response.text
    content = response.json()["content"]
    assert "人工复核：证明对方确认欠款本金" in content
    assert "**原件状态**：已核验原始聊天导出文件" in content
    assert "真实性风险：需保留原始聊天记录" in content
    assert "合法性风险：由我方账号依法导出" in content
    assert "关联性风险：与欠款确认直接相关" in content
    assert "补强动作：补充原始聊天导出文件；核对对方账号主体" in content
    assert "复核备注：提交前核验上下文完整性" in content
