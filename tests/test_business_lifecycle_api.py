import uuid

import pytest
from httpx import AsyncClient


async def _create_case(client: AsyncClient, title_prefix: str = "专项生命周期") -> int:
    unique = uuid.uuid4().hex[:8]
    response = await client.post(
        "/api/cases",
        json={
            "title": f"{title_prefix}-{unique}",
            "case_type": "民事",
            "plaintiff": "甲方公司",
            "defendant": "乙方公司",
            "description": "专项 API 生命周期测试案件",
        },
    )
    assert response.status_code in [200, 201], response.text
    return response.json()["id"]


class FakeReportGenerator:
    def generate_report(self, **kwargs):
        return (
            "一、案件事实\n"
            "甲乙双方存在合同履行争议，已形成付款和沟通证据。\n\n"
            "二、法律关系\n"
            "本案核心法律关系为合同关系。\n\n"
            "三、争议焦点\n"
            "争议焦点为是否违约及损失范围。\n"
        )

    def get_task_status(self, case_id, report_type):
        return {
            "cached": False,
            "progress": 1.0,
            "segments_completed": 3,
            "total_segments": 3,
        }


def test_report_markdown_heading_parser_keeps_all_sections():
    from app.api.report_api import _parse_report_sections

    sections = _parse_report_sections(
        "# 测试报告\n\n"
        "## 一、案件定位\n"
        "定位内容。\n\n"
        "## 二、核心争议\n"
        "争议内容。\n\n"
        "## 三、证据组织\n"
        "证据内容。\n",
        "analysis",
        "report-id",
    )

    assert [section.title for section in sections] == ["一、案件定位", "二、核心争议", "三、证据组织"]
    assert "定位内容" in sections[0].content
    assert "争议内容" in sections[1].content


@pytest.mark.asyncio
async def test_manual_evidence_submit_lists_and_exports(client: AsyncClient, tmp_path, monkeypatch):
    from app.api import export_api

    export_api.export_service.export_dir = str(tmp_path / "exports")
    case_id = await _create_case(client, "手工证据")

    create_response = await client.post(
        f"/api/evidence/submit/{case_id}",
        json={
            "case_id": case_id,
            "name": "付款凭证-手工录入",
            "evidence_type": "票据",
            "content": "2026年5月1日甲方向乙方付款10000元。",
            "source": "银行流水",
            "proof_point": "证明甲方已经履行付款义务",
            "custody": "甲方公司",
        },
    )
    assert create_response.status_code == 200, create_response.text
    evidence_id = create_response.json()["id"]

    list_response = await client.get(f"/api/evidence/case/{case_id}")
    assert list_response.status_code == 200, list_response.text
    evidences = list_response.json()
    assert any(item["id"] == evidence_id for item in evidences)
    assert any("履行付款义务" in item["proof_point"] for item in evidences)

    export_response = await client.post(
        f"/api/exports/evidence/{case_id}",
        json={"format": "markdown", "include_content": True},
    )
    assert export_response.status_code == 200, export_response.text
    export_data = export_response.json()
    assert export_data["success"] is True
    assert export_data["format_used"] == "markdown"
    assert "付款凭证-手工录入" in (tmp_path / "exports" / f"case_{case_id}" / export_data["filename"]).read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_evidence_book_export_tolerates_missing_case_number(client: AsyncClient):
    case_id = await _create_case(client, "证据册无案号")

    create_response = await client.post(
        f"/api/evidence/submit/{case_id}",
        json={
            "case_id": case_id,
            "name": "证据册付款凭证",
            "evidence_type": "票据",
            "content": "甲方已向乙方付款10000元。",
            "source": "银行流水",
            "proof_point": "证明付款事实",
            "custody": "甲方公司",
        },
    )
    assert create_response.status_code == 200, create_response.text

    export_response = await client.get(f"/api/evidence/export-book/{case_id}?format=markdown")
    assert export_response.status_code == 200, export_response.text
    export_data = export_response.json()
    assert export_data["format"] == "markdown"
    assert "（待立案后填写）" in export_data["content"]
    assert "证据册付款凭证" in export_data["content"]


@pytest.mark.asyncio
async def test_document_upload_indexes_evidence_and_structured_fact_export(
    client: AsyncClient,
    tmp_path,
    monkeypatch,
):
    from app.api import export_api
    from app.api import document as document_api
    from app.services import evidence_v2 as evidence_v2_module

    export_api.export_service.export_dir = str(tmp_path / "exports")
    monkeypatch.setattr(document_api.file_parser, "storage_path", str(tmp_path / "files"))
    monkeypatch.setattr(
        evidence_v2_module.evidence_service_v2,
        "_classify_evidence_sync",
        lambda content, case_id: {
            "type": "CONTRACT",
            "facts": [{"fact": "证明双方存在合同履行安排", "confidence": 0.92}],
        },
    )
    monkeypatch.setattr(
        evidence_v2_module.evidence_service_v2,
        "_extract_keywords_sync",
        lambda content: {"keywords": ["合同", "付款"], "entities": []},
    )
    monkeypatch.setattr(evidence_v2_module.evidence_service_v2, "_generate_summary", lambda content: "")

    case_id = await _create_case(client, "上传证据")
    upload_response = await client.post(
        f"/api/documents/upload/{case_id}",
        data={"doc_type": "其他"},
        files={
            "file": (
                "payment-note.txt",
                "甲方与乙方确认合同继续履行，甲方已于2026年5月1日支付10000元。".encode("utf-8"),
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 200, upload_response.text

    list_response = await client.get(f"/api/evidence/case/{case_id}")
    assert list_response.status_code == 200, list_response.text
    evidences = list_response.json()
    assert any(item["type"] == "CONTRACT" and item["name"].startswith("合同") for item in evidences)

    export_response = await client.post(
        f"/api/exports/evidence/{case_id}",
        json={"format": "markdown", "include_content": True},
    )
    assert export_response.status_code == 200, export_response.text
    export_data = export_response.json()
    assert export_data["success"] is True
    exported = (tmp_path / "exports" / f"case_{case_id}" / export_data["filename"]).read_text(encoding="utf-8")
    assert "证明双方存在合同履行安排" in exported


@pytest.mark.asyncio
async def test_report_generate_list_detail_and_markdown_export(client: AsyncClient, monkeypatch):
    from app.api import report_api

    monkeypatch.setattr(report_api, "get_streaming_report_generator", lambda llm: FakeReportGenerator())

    case_id = await _create_case(client, "报告")
    generate_response = await client.post(
        f"/api/reports/generate/{case_id}",
        json={"report_type": "analysis", "force_regenerate": True},
    )
    assert generate_response.status_code == 200, generate_response.text
    assert generate_response.json()["status"] == "completed"

    list_response = await client.get(f"/api/reports/list/{case_id}")
    assert list_response.status_code == 200, list_response.text
    reports = list_response.json()["reports"]
    assert len(reports) >= 1
    report_id = reports[0]["id"]

    detail_response = await client.get(f"/api/reports/detail/{report_id}")
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["status"] == "COMPLETED"
    assert detail["total_sections"] >= 1

    export_response = await client.get(f"/api/reports/export/{report_id}?format=markdown")
    assert export_response.status_code == 200, export_response.text
    assert "甲乙双方存在合同履行争议" in export_response.text


@pytest.mark.asyncio
async def test_time_control_letter_mailing_and_export(client: AsyncClient, tmp_path, monkeypatch):
    from app.api import export_api

    export_api.export_service.export_dir = str(tmp_path / "exports")
    case_id = await _create_case(client, "函件")

    create_response = await client.post(
        f"/api/time-control/case/{case_id}/letters",
        json={
            "标题": "催告付款函",
            "方向": "outgoing",
            "类型": "demand_letter",
            "发送方": "甲方公司",
            "接收方": "乙方公司",
            "函件日期": "2026-05-01T00:00:00",
            "内容摘要": "要求乙方在三日内支付剩余款项。",
            "核心诉求": "支付剩余款项",
        },
    )
    assert create_response.status_code == 200, create_response.text
    letter_id = create_response.json()["letter"]["id"]

    mailing_response = await client.post(
        f"/api/time-control/letters/{letter_id}/mailing",
        json={"运单号": "SF1234567890", "快递公司": "顺丰", "邮寄目的": "催告付款"},
    )
    assert mailing_response.status_code == 200, mailing_response.text

    delivered_response = await client.post(f"/api/time-control/letters/{letter_id}/delivered")
    assert delivered_response.status_code == 200, delivered_response.text
    assert delivered_response.json()["letter"]["邮寄状态"] == "delivered"

    proof_response = await client.post(
        f"/api/time-control/letters/{letter_id}/proof",
        json={"文件路径": "/tmp/proof.jpg", "文件类型": "image", "描述": "签收截图"},
    )
    assert proof_response.status_code == 200, proof_response.text

    tracking_response = await client.get(f"/api/time-control/case/{case_id}/mail-tracking")
    assert tracking_response.status_code == 200, tracking_response.text
    assert any(item["运单号"] == "SF1234567890" for item in tracking_response.json())

    export_response = await client.post(
        f"/api/exports/letter/{letter_id}",
        json={"letter_id": letter_id, "format": "markdown", "include_reply_draft": False},
    )
    assert export_response.status_code == 200, export_response.text
    assert export_response.json()["success"] is True


@pytest.mark.asyncio
async def test_hearing_record_statement_lifecycle(client: AsyncClient):
    case_id = await _create_case(client, "庭审")

    create_response = await client.post(
        f"/api/hearings/case/{case_id}/hearing",
        json={
            "庭审类型": "first_trial",
            "庭审日期": "2026-06-01T09:30:00",
            "地点": "第一法庭",
            "案号": "（2026）测0101民初1号",
            "参会人员": [{"name": "代理律师", "role": "原告代理人"}],
        },
    )
    assert create_response.status_code == 200, create_response.text
    hearing_id = create_response.json()["id"]

    status_response = await client.put(
        f"/api/hearings/hearing/{hearing_id}/status?status=in_progress&current_phase=cross_examination"
    )
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["current_phase"] == "cross_examination"

    statement_response = await client.post(
        f"/api/hearings/hearing/{hearing_id}/statement",
        json={
            "发言内容": "请说明合同履行和付款时间。",
            "讲话方角色": "plaintiff_lawyer",
            "讲话人姓名": "代理律师",
            "发言类型": "question",
        },
    )
    assert statement_response.status_code == 200, statement_response.text
    assert "trap_analysis" in statement_response.json()

    statements_response = await client.get(f"/api/hearings/hearing/{hearing_id}/statements")
    assert statements_response.status_code == 200, statements_response.text
    statements = statements_response.json()
    assert len(statements) == 1
    assert statements[0]["内容"] == "请说明合同履行和付款时间。"


@pytest.mark.asyncio
async def test_meeting_records_generation_and_minutes_export(client: AsyncClient, tmp_path, monkeypatch):
    from app.api import export_api

    export_api.export_service.export_dir = str(tmp_path / "exports")
    case_id = await _create_case(client, "会议")
    session_id = f"meeting-{uuid.uuid4().hex[:8]}"
    topic = "付款争议协商会议"

    save_response = await client.post(
        "/api/meetings/records",
        json={
            "session_id": session_id,
            "case_id": case_id,
            "meeting_type": "商务谈判",
            "topic": topic,
            "date": "2026-06-02",
            "participants": "甲方律师、乙方代表",
            "content": "乙方确认收到付款但要求延期交付。",
            "records": [
                {
                    "type": "analysis",
                    "time": "09:35",
                    "content": {
                        "analysis": "对方承认收款，争议集中在交付期限。",
                        "suggestions": "固定对方承认收款的会议记录。",
                    },
                }
            ],
            "notes": "需形成会议纪要并导出。",
        },
    )
    assert save_response.status_code == 200, save_response.text
    assert save_response.json()["session_id"] == session_id

    list_response = await client.get(f"/api/meetings/records?case_id={case_id}")
    assert list_response.status_code == 200, list_response.text
    records = list_response.json()
    assert any(item["session_id"] == session_id and item["topic"] == topic for item in records)

    detail_response = await client.get(f"/api/meetings/records/{session_id}")
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["content"] == "乙方确认收到付款但要求延期交付。"
    assert detail["records"][0]["content"]["analysis"] == "对方承认收款，争议集中在交付期限。"

    meeting_info = {
        "type": "商务谈判",
        "topic": topic,
        "date": "2026-06-02",
        "our_role": "甲方代理人",
        "participants": "甲方律师、乙方代表",
        "our_position": "要求乙方按合同交付。",
        "their_position": "希望延期交付。",
    }

    minutes_response = await client.post(
        "/api/meetings/generate-minutes",
        json={"meeting_info": meeting_info, "records": detail["records"]},
    )
    assert minutes_response.status_code == 200, minutes_response.text
    minutes = minutes_response.json()["minutes"]
    assert "# 会议纪要" in minutes
    assert topic in minutes
    assert "对方承认收款" in minutes

    contract_response = await client.post(
        "/api/meetings/generate-contract",
        json={"meeting_info": meeting_info, "records": detail["records"], "contract_type": "补充协议"},
    )
    assert contract_response.status_code == 200, contract_response.text
    assert "# 补充协议" in contract_response.json()["contract"]

    resolution_response = await client.post(
        "/api/meetings/generate-resolution",
        json={
            "meeting_info": meeting_info,
            "decisions": [{"content": {"strategy": "确认乙方延期交付需出具书面承诺。"}}],
        },
    )
    assert resolution_response.status_code == 200, resolution_response.text
    assert "确认乙方延期交付" in resolution_response.json()["resolution"]

    export_response = await client.post(
        "/api/exports/meeting-minutes",
        json={
            "meeting_type": "商务谈判",
            "topic": topic,
            "content": minutes,
            "format": "markdown",
        },
    )
    assert export_response.status_code == 200, export_response.text
    export_data = export_response.json()
    assert export_data["success"] is True
    assert export_data["format_used"] == "markdown"
    exported = (tmp_path / "exports" / "case_general" / export_data["filename"]).read_text(encoding="utf-8")
    assert "会议纪要" in exported
    assert topic in exported
    assert "对方承认收款" in exported


@pytest.mark.asyncio
async def test_document_export_uses_custom_content_and_writes_markdown(client: AsyncClient, tmp_path, monkeypatch):
    from app.api import export_api

    export_api.export_service.export_dir = str(tmp_path / "exports")
    case_id = await _create_case(client, "document-export")
    custom_content = "# Custom Claim\n\nPayment balance remains unpaid."

    export_response = await client.post(
        f"/api/exports/document/{case_id}",
        json={
            "document_type": "Custom Claim",
            "format": "markdown",
            "custom_content": custom_content,
        },
    )
    assert export_response.status_code == 200, export_response.text
    export_data = export_response.json()
    assert export_data["success"] is True
    assert export_data["format_used"] == "markdown"

    exported = (tmp_path / "exports" / f"case_{case_id}" / export_data["filename"]).read_text(encoding="utf-8")
    assert "document_type: Custom Claim" in exported
    assert "# Custom Claim" in exported
    assert "Payment balance remains unpaid." in exported


@pytest.mark.asyncio
async def test_adversarial_analysis_export_writes_markdown(client: AsyncClient, tmp_path, monkeypatch):
    from app.api import export_api
    from app.core.tenant_context import TenantContext
    from app.db.database import SessionLocal
    from app.models.adversarial_analysis import AdversarialAnalysis, AnalysisPhase

    export_api.export_service.export_dir = str(tmp_path / "exports")
    case_id = await _create_case(client, "adversarial-export")

    TenantContext.set_tenant("pytest-tenant")
    TenantContext.set_user("pytest-user")
    db = SessionLocal()
    try:
        analysis = AdversarialAnalysis(
            case_id=case_id,
            analysis_phase=AnalysisPhase.LITIGATION,
            title="Adversarial Export Check",
            opponent_name="Counterparty LLC",
            our_strengths="We hold payment records.",
            our_weaknesses="Delivery acceptance is incomplete.",
            opponent_strengths="They keep partial chat history.",
            opponent_weaknesses="They admitted receiving payment.",
            overall_strategy="Secure payment facts first.",
            immediate_actions="Collect bank statements and meeting minutes.",
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        analysis_id = analysis.id
    finally:
        db.close()
        TenantContext.clear()

    export_response = await client.post(f"/api/exports/adversarial-analysis/{analysis_id}?format=markdown")
    assert export_response.status_code == 200, export_response.text
    export_data = export_response.json()
    assert export_data["success"] is True
    assert export_data["format_used"] == "markdown"

    exported = (tmp_path / "exports" / f"case_{case_id}" / export_data["filename"]).read_text(encoding="utf-8")
    assert "Adversarial Export Check" in exported
    assert "We hold payment records." in exported
    assert "Secure payment facts first." in exported
