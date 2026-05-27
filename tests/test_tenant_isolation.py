from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all SQLAlchemy models
from app.core.tenant_context import TenantContext
from app.db.database import Base
from app.db.tenant_backfill import backfill_tenant_columns
from app.models.adversarial_analysis import AdversarialAnalysis, AdversarialEvidenceItem
from app.models.appeal import AppealDeadline, AppealRecord
from app.models.case import Case
from app.models.case_claim import CaseClaim
from app.models.conversation import ConversationMessage, ConversationSession
from app.models.evidence_analysis import EvidenceAnalysisMessage, EvidenceAnalysisSession
from app.models.hearing import HearingRecord, HearingStatement, SpeakerRole
from app.models.project import Project, ProjectDocument
from app.models.report import ReportOutline, ReportSection
from app.models.tenant import Tenant


def _session_factory():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _add_tenants(db):
    db.add_all(
        [
            Tenant(id="tenant-a", name="Tenant A", slug="tenant-a"),
            Tenant(id="tenant-b", name="Tenant B", slug="tenant-b"),
        ]
    )
    db.commit()


def _create_tenant_graph(db, tenant_id: str) -> dict[str, object]:
    TenantContext.set_tenant(tenant_id)

    case = Case(title=f"{tenant_id} case")
    db.add(case)
    db.flush()

    claim = CaseClaim(case_id=case.id, title=f"{tenant_id} claim")

    outline = ReportOutline(
        id=f"{tenant_id}-outline",
        case_id=case.id,
        report_type="ANALYSIS",
        title=f"{tenant_id} report",
    )
    section = ReportSection(
        id=f"{tenant_id}-section",
        outline_id=outline.id,
        section_index=1,
        title=f"{tenant_id} section",
    )

    appeal = AppealRecord(case_id=case.id)
    db.add(appeal)
    db.flush()
    appeal_deadline = AppealDeadline(
        appeal_record_id=appeal.id,
        deadline_type="submit",
        deadline_name=f"{tenant_id} deadline",
    )

    hearing = HearingRecord(case_id=case.id)
    db.add(hearing)
    db.flush()
    statement = HearingStatement(
        record_id=hearing.id,
        speaker_role=SpeakerRole.JUDGE,
        content=f"{tenant_id} statement",
    )

    adversarial = AdversarialAnalysis(
        case_id=case.id,
        title=f"{tenant_id} adversarial",
    )
    db.add(adversarial)
    db.flush()
    adversarial_item = AdversarialEvidenceItem(
        analysis_id=adversarial.id,
        name=f"{tenant_id} evidence",
        owner="our",
    )

    conversation = ConversationSession(id=f"{tenant_id}-session", case_id=case.id)
    message = ConversationMessage(
        id=f"{tenant_id}-message",
        session_id=conversation.id,
        role="user",
        content=f"{tenant_id} message",
    )

    evidence_session = EvidenceAnalysisSession(case_id=case.id)
    db.add(evidence_session)
    db.flush()
    evidence_message = EvidenceAnalysisMessage(
        session_id=evidence_session.id,
        message_type="user",
        role="user",
        content=f"{tenant_id} evidence message",
    )

    project = Project(name=f"{tenant_id} project")
    db.add(project)
    db.flush()
    project_doc = ProjectDocument(
        project_id=project.id,
        doc_type="contract",
        name=f"{tenant_id} project doc",
    )

    objects = {
        "case": case,
        "claim": claim,
        "section": section,
        "appeal_deadline": appeal_deadline,
        "statement": statement,
        "adversarial_item": adversarial_item,
        "message": message,
        "evidence_message": evidence_message,
        "project": project,
        "project_doc": project_doc,
    }
    db.add_all(list(objects.values()))
    db.flush()

    assert all(getattr(obj, "tenant_id") == tenant_id for obj in objects.values())
    return {name: getattr(obj, "id") for name, obj in objects.items()}


def test_orm_tenant_filter_covers_case_and_child_models():
    _, Session = _session_factory()
    db = Session()
    try:
        _add_tenants(db)
        tenant_a_ids = _create_tenant_graph(db, "tenant-a")
        tenant_b_ids = _create_tenant_graph(db, "tenant-b")
        db.commit()
    finally:
        TenantContext.clear()
        db.close()

    read_db = Session()
    try:
        TenantContext.set_tenant("tenant-a")
        assert read_db.query(Case).filter(Case.id == tenant_a_ids["case"]).first()
        assert read_db.query(Case).filter(Case.id == tenant_b_ids["case"]).first() is None

        blocked_reads = [
            (CaseClaim, tenant_b_ids["claim"]),
            (ReportSection, tenant_b_ids["section"]),
            (AppealDeadline, tenant_b_ids["appeal_deadline"]),
            (HearingStatement, tenant_b_ids["statement"]),
            (AdversarialEvidenceItem, tenant_b_ids["adversarial_item"]),
            (ConversationMessage, tenant_b_ids["message"]),
            (EvidenceAnalysisMessage, tenant_b_ids["evidence_message"]),
            (Project, tenant_b_ids["project"]),
            (ProjectDocument, tenant_b_ids["project_doc"]),
        ]
        for model, blocked_id in blocked_reads:
            assert read_db.query(model).filter(model.id == blocked_id).first() is None

        TenantContext.set_tenant("tenant-b")
        assert read_db.query(Case).filter(Case.id == tenant_b_ids["case"]).first()
        assert read_db.query(Case).filter(Case.id == tenant_a_ids["case"]).first() is None
    finally:
        TenantContext.clear()
        read_db.close()


def test_tenant_backfill_prefers_case_and_parent_lineage():
    engine, Session = _session_factory()
    db = Session()
    try:
        TenantContext.clear()
        _add_tenants(db)

        case_a = Case(title="A case", tenant_id="tenant-a")
        case_b = Case(title="B case", tenant_id="tenant-b")
        db.add_all([case_a, case_b])
        db.flush()

        claim = CaseClaim(case_id=case_a.id, title="claim without tenant")
        outline = ReportOutline(
            id="outline-without-tenant",
            case_id=case_a.id,
            report_type="ANALYSIS",
        )
        section = ReportSection(
            id="section-without-tenant",
            outline_id=outline.id,
            section_index=1,
            title="section without tenant",
        )
        appeal = AppealRecord(case_id=case_b.id)
        project = Project(name="project with tenant", tenant_id="tenant-a")
        db.add_all([claim, outline, section, appeal, project])
        db.flush()

        deadline = AppealDeadline(
            appeal_record_id=appeal.id,
            deadline_type="submit",
            deadline_name="deadline without tenant",
        )
        project_doc = ProjectDocument(
            project_id=project.id,
            doc_type="contract",
            name="project doc without tenant",
        )
        db.add_all([deadline, project_doc])
        db.commit()
    finally:
        TenantContext.clear()
        db.close()

    with engine.begin() as connection:
        updated = backfill_tenant_columns(
            connection,
            Base.metadata,
            "fallback-tenant",
            {"users", "api_keys"},
        )

    assert updated

    read_db = Session()
    try:
        assert read_db.query(CaseClaim).one().tenant_id == "tenant-a"
        assert read_db.query(ReportOutline).one().tenant_id == "tenant-a"
        assert read_db.query(ReportSection).one().tenant_id == "tenant-a"
        assert read_db.query(AppealRecord).one().tenant_id == "tenant-b"
        assert read_db.query(AppealDeadline).one().tenant_id == "tenant-b"
        assert read_db.query(ProjectDocument).one().tenant_id == "tenant-a"
    finally:
        TenantContext.clear()
        read_db.close()
