import uuid

import pytest
from httpx import AsyncClient

from app.db.database import SessionLocal
from app.models.case import Case
from app.models.document import DocumentExportReviewAudit, GeneratedDocument


REVIEW_ITEMS = ["parties", "claims", "facts", "evidence", "law", "signature"]


def _create_generated_document() -> tuple[int, int]:
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        case = Case(
            tenant_id="pytest-tenant",
            title=f"export-review-{suffix}",
            case_type="民事",
            plaintiff="甲方公司",
            defendant="乙方公司",
            description="文书导出核验审计测试案件",
        )
        db.add(case)
        db.flush()

        document = GeneratedDocument(
            tenant_id="pytest-tenant",
            case_id=case.id,
            title=f"起诉状草稿-{suffix}",
            document_type="起诉状",
            content="文书草稿内容",
            status="draft",
            version=1,
        )
        db.add(document)
        db.commit()
        return case.id, document.id
    finally:
        db.close()


@pytest.mark.asyncio
async def test_document_export_review_audit_requires_full_checklist(client: AsyncClient):
    case_id, document_id = _create_generated_document()

    response = await client.post(
        "/api/documents/export-review-audits",
        json={
            "generated_document_id": document_id,
            "case_id": case_id,
            "document_title": "起诉状草稿",
            "document_type": "起诉状",
            "export_action": "download",
            "export_format": "docx",
            "checked_items": REVIEW_ITEMS[:-1],
        },
    )

    assert response.status_code == 400, response.text
    assert "signature" in response.text


@pytest.mark.asyncio
async def test_document_export_review_audit_records_user_tenant_and_can_be_listed(
    client: AsyncClient,
):
    case_id, document_id = _create_generated_document()

    response = await client.post(
        "/api/documents/export-review-audits",
        json={
            "generated_document_id": document_id,
            "case_id": case_id,
            "document_title": "起诉状草稿",
            "document_type": "起诉状",
            "export_action": "download",
            "export_format": "pdf",
            "checked_items": REVIEW_ITEMS,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    audit = data["audit"]
    assert data["success"] is True
    assert audit["tenant_id"] == "pytest-tenant"
    assert audit["user_id"] == "pytest-user"
    assert audit["case_id"] == case_id
    assert audit["generated_document_id"] == document_id
    assert audit["export_format"] == "pdf"
    assert audit["checked_item_count"] == len(REVIEW_ITEMS)

    list_response = await client.get(f"/api/documents/{document_id}/export-review-audits")
    assert list_response.status_code == 200, list_response.text
    listed = list_response.json()
    assert listed["document_id"] == document_id
    assert listed["total"] >= 1
    assert any(item["id"] == audit["id"] for item in listed["audits"])

    db = SessionLocal()
    try:
        stored = db.query(DocumentExportReviewAudit).filter_by(id=audit["id"]).one()
        assert stored.checked_items == sorted(REVIEW_ITEMS)
    finally:
        db.close()
