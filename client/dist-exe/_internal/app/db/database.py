import contextlib
import logging
import os

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import sessionmaker, with_loader_criteria
from app.config import settings, should_auto_create_tables
from app.core.tenant_context import TenantContext
from app.db.tenant_backfill import backfill_tenant_columns

logger = logging.getLogger(__name__)

# SQLite 数据库 - 使用 URI 格式以支持中文
# sqlite:///path/to/db.db
# 特殊字符会在连接时自动处理
if settings.database_url.startswith("sqlite:///"):
    # 将数据库路径转换为绝对路径并正确编码
    db_path = settings.database_url.replace("sqlite:///", "")
    db_path = os.path.abspath(db_path)
    # 使用 URI 格式以支持中文路径
    uri_db_url = f"sqlite:///{db_path}?charset=utf8"
    engine = create_engine(
        uri_db_url,
        connect_args={"check_same_thread": False, "timeout": 30}
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle_seconds,
        pool_pre_ping=settings.db_pool_pre_ping,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

_tenant_scoped_classes_cache = None


def _tenant_scoped_classes():
    global _tenant_scoped_classes_cache
    if _tenant_scoped_classes_cache is not None:
        return _tenant_scoped_classes_cache

    import app.models  # noqa: F401 - ensure all mappers are registered

    classes = []
    for mapper in list(Base.registry.mappers):
        model_class = mapper.class_
        if hasattr(model_class, "tenant_id"):
            classes.append(model_class)
    _tenant_scoped_classes_cache = tuple(classes)
    return _tenant_scoped_classes_cache


@event.listens_for(SQLAlchemySession, "do_orm_execute")
def _apply_tenant_filter(execute_state):
    tenant_id = TenantContext.get_tenant_id()
    if not tenant_id or not execute_state.is_select:
        return

    for model_class in _tenant_scoped_classes():
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                model_class,
                lambda cls: cls.tenant_id == tenant_id,
                include_aliases=True,
            )
        )


@event.listens_for(SQLAlchemySession, "before_flush")
def _assign_tenant_to_new_objects(session, flush_context, instances):
    tenant_id = TenantContext.get_tenant_id()
    if not tenant_id:
        return

    for obj in session.new:
        if hasattr(obj, "tenant_id") and not getattr(obj, "tenant_id", None):
            setattr(obj, "tenant_id", tenant_id)


@contextlib.contextmanager
def _sqlite_init_lock():
    if not settings.database_url.startswith("sqlite:///"):
        yield
        return

    lock_path = f"{db_path}.init.lock"
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _fallback_tenant_id(connection) -> str:
    try:
        row = connection.execute(text("SELECT id FROM tenants LIMIT 1")).first()
        if row:
            return row[0]
    except Exception:
        pass
    return "default"


def _sync_tenant_columns_for_development() -> None:
    """Add tenant_id columns in auto-create dev mode and backfill legacy rows.

    Production deployments should still use app.db.migrate_all, but local
    startup needs this narrow repair because SQLAlchemy create_all does not
    alter existing SQLite tables.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    preparer = engine.dialect.identifier_preparer
    skip_backfill = {"users", "api_keys"}

    with engine.begin() as connection:
        fallback_tenant_id = _fallback_tenant_id(connection)
        for table in sorted(Base.metadata.sorted_tables, key=lambda item: item.name):
            if table.name not in existing_tables or "tenant_id" not in table.columns:
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
            table_name = preparer.quote(table.name)
            column_name = preparer.quote("tenant_id")

            if "tenant_id" not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(36)")
                )

        updated = backfill_tenant_columns(
            connection,
            Base.metadata,
            fallback_tenant_id,
            skip_backfill,
        )
        if updated:
            logger.info(
                "Backfilled tenant_id columns during dev startup: %s",
                ", ".join(updated),
            )


def init_db():
    """初始化数据库"""
    if not should_auto_create_tables():
        logger.info(
            "Skipping automatic table creation because AUTO_CREATE_TABLES is disabled."
        )
        return

    import app.models  # noqa: F401 - register every SQLAlchemy model on Base.metadata

    from app.models import (
        case, document, reminder, adversarial_analysis, letter,
        hearing, appeal, project, meeting, case_profile
    )
    # 新增：生成文书和文书建议模型
    from app.models.document import GeneratedDocument, DocumentSuggestion
    
    # 证据系统 V2
    from app.models.evidence import (
        EvidenceItem, EvidenceRelationship, EvidenceFact,
        EvidenceDuplicateCheck, EvidenceKeywordIndex
    )
    # 对话系统 V2
    from app.models.conversation import (
        ConversationSession, ConversationMessage,
        ClarificationRecord, QuestionAnalysis
    )
    # 报告系统 V2
    from app.models.report import (
        ReportOutline, ReportSection, SectionReference, ReportCache
    )
    
    # 证据文件夹监控
    from app.models.evidence_folder import (
        EvidenceFolderScan, EvidenceFolderFile, EvidenceFolderConfig
    )

    # 执行跟踪 V2
    from app.models.execution import (
        ExecutionRecord, ExecutionTask, ExecutionAsset, ExecutionStage
    )

    # 案件财务
    from app.models.finance import (
        CaseFinance, ExpenseRecord, WinRateAssessment
    )

    # 法律知识库
    from app.models.legal_knowledge_base import (
        LegalArticle, JudicialInterpretation, GuidingCase,
        LitigationCost, JurisdictionRule, ContractTemplate
    )
    from app.models.document import DocumentTemplate

    # AI 分析结果持久化
    from app.models.analysis_result import AnalysisResult

    # 对话分析结果
    from app.models.conversation_analysis import ConversationAnalysis, ConversationContext

    # SaaS 多租户模型
    from app.models.tenant import Tenant, TenantType, SubscriptionPlan, SubscriptionStatus
    from app.models.user import User, UserRole
    from app.models.api_key import APIKey
    from app.models.sms_verification import SMSVerificationCode
    from app.models.ai_audit import AIRetrievalAudit

    with _sqlite_init_lock():
        Base.metadata.create_all(bind=engine)
        _sync_tenant_columns_for_development()


def create_all_tables() -> None:
    previous = os.environ.get("AUTO_CREATE_TABLES")
    os.environ["AUTO_CREATE_TABLES"] = "1"
    try:
        init_db()
    finally:
        if previous is None:
            os.environ.pop("AUTO_CREATE_TABLES", None)
        else:
            os.environ["AUTO_CREATE_TABLES"] = previous
