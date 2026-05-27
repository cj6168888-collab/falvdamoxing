"""
法律知识库 SQLAlchemy 模型
"""
from sqlalchemy import Column, String, Integer, Text, Boolean, Date, DateTime, JSON, BigInteger, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


class LegalArticle(Base):
    """法条表"""
    __tablename__ = "legal_articles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    law_name = Column(String(200), nullable=False, index=True)
    article_number = Column(String(50), nullable=False)
    title = Column(String(500))
    content = Column(Text, nullable=False)
    chapter = Column(String(200))
    category = Column(String(50), index=True)
    effective_date = Column(Date)
    is_valid = Column(Boolean, default=True)
    supersedes = Column(String(36))
    source = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class JudicialInterpretation(Base):
    """司法解释表"""
    __tablename__ = "judicial_interpretations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    doc_number = Column(String(100))
    content = Column(Text, nullable=False)
    related_law_id = Column(String(36))
    effective_date = Column(Date)
    is_valid = Column(Boolean, default=True)
    source = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class GuidingCase(Base):
    """指导性案例表"""
    __tablename__ = "guiding_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number = Column(String(100), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    court = Column(String(200))
    case_type = Column(String(50), index=True)
    summary = Column(Text)
    full_text = Column(Text)
    keywords = Column(JSON)
    related_articles = Column(JSON)
    publish_date = Column(Date)
    source = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LitigationCost(Base):
    """诉讼费用规则表"""
    __tablename__ = "litigation_costs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cost_type = Column(String(100), nullable=False)
    calculation_rule = Column(JSON, nullable=False)
    base_law_id = Column(String(36))
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class JurisdictionRule(Base):
    """管辖权规则表"""
    __tablename__ = "jurisdiction_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_type = Column(String(100), nullable=False)
    description = Column(Text)
    condition = Column(JSON)
    base_law_id = Column(String(36))
    created_at = Column(DateTime, server_default=func.now())


class ContractTemplate(Base):
    """合同模板表"""
    __tablename__ = "contract_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_type = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    essential_clauses = Column(JSON)
    risk_clauses = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
