"""
项目模型 - 随身法律顾问的核心
从日常生活的法律事务开始，陪伴用户，保护用户
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class ProjectType(str, enum.Enum):
    """项目类型"""
    # 商业合作类
    BUSINESS_COOPERATION = "商业合作"
    INVESTMENT = "投资"
    PARTNERSHIP = "合伙/合作"
    JOINT_VENTURE = "合资企业"
    FRANCHISE = "特许经营"
    
    # 劳动合同类
    EMPLOYMENT = "劳动合同"
    PERSONAL_SERVICE = "劳务/服务"
    FREELANCE = "自由职业"
    INTERNSHIP = "实习"
    
    # 合同交易类
    PURCHASE = "采购合同"
    SALE = "销售合同"
    LEASE = "租赁"
    LOAN = "借贷"
    MORTGAGE = "抵押/担保"
    CONTRACT = "合同"
    
    # 家庭生活类
    MARRIAGE = "婚姻家庭"
    DIVORCE = "离婚"
    INHERITANCE = "继承"
    FAMILY_DISPUTE = "家庭纠纷"
    CHILD_CUSTODY = "子女抚养"
    
    # 财产类
    PROPERTY_PURCHASE = "房产交易"
    VEHICLE = "车辆交易"
    PROPERTY_DISPUTE = "财产纠纷"
    DEBT = "债务"
    
    # 知识产权类
    COPYRIGHT = "著作权"
    TRADEMARK = "商标"
    PATENT = "专利"
    TRADE_SECRET = "商业秘密"
    
    # 日常生活类
    CONSUMER_DISPUTE = "消费纠纷"
    NEIGHBOR_DISPUTE = "邻里纠纷"
    PERSONAL_INJURY = "人身损害"
    TRAFFIC_ACCIDENT = "交通事故"
    
    # 行政合规类
    COMPLIANCE = "compliance"
    LICENSE = "license"
    TAX = "tax"
    ENVIRONMENTAL = "environmental"
    
    # 其他
    OTHER = "other"


class ProjectStatus(str, enum.Enum):
    """项目状态"""
    PLANNING = "筹划中"
    NEGOTIATION = "洽谈中"
    DRAFTING = "起草/审核中"
    EXECUTING = "执行中"
    MONITORING = "监控中"
    COMPLETED = "已完成"
    DISPUTE = "发生纠纷"
    LITIGATION = "转入诉讼"
    SUSPENDED = "暂停"
    TERMINATED = "已终止"


class ProjectPhase(str, enum.Enum):
    """项目阶段"""
    INITIATION = "发起/启动"
    DUE_DILIGENCE = "尽职调查"
    NEGOTIATION = "谈判"
    DRAFTING = "起草合同"
    REVIEW = "审核"
    SIGNING = "签约"
    PERFORMANCE = "履行"
    MONITORING = "履约监控"
    COMPLETION = "完成/结算"
    AFTERMARKET = "售后"
    EARLY_WARNING = "预警信号"
    NEGOTIATION_SETTLEMENT = "协商解决"
    MEDIATION = "调解"
    ARBITRATION = "仲裁"
    LITIGATION = "诉讼"


class UserRole(str, enum.Enum):
    """用户角色"""
    INDIVIDUAL = "个人"
    EMPLOYEE = "员工"
    EMPLOYER = "雇主"
    BUSINESS = "企业主"
    INVESTOR = "投资者"
    LANDLORD = "房东"
    TENANT = "租客"
    LANDLORD_TENANT = "租赁双方"
    CONSUMER = "消费者"
    SELLER = "销售方"
    BUYER = "采购方"
    PARENT = "家长"
    CHILD = "子女"
    OTHER = "其他"


class Project(Base):
    """项目 - 随身法律顾问的核心"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    user_id = Column(String(100), nullable=True)

    # 基本信息
    name = Column(String(500), nullable=False)
    project_type = Column(String(100), default="其他")
    description = Column(Text, nullable=True)
    user_role = Column(String(50), default="个人")

    # 涉及对象
    counterpart_name = Column(String(200), nullable=True)
    counterpart_type = Column(String(50), nullable=True)
    counterpart_contact = Column(String(200), nullable=True)

    # 时间
    start_date = Column(DateTime, nullable=True)
    expected_end_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)

    # 状态和阶段
    status = Column(String(50), default="筹划中")
    current_phase = Column(String(50), default="发起/启动")

    # 金额
    amount = Column(String(100), nullable=True)
    currency = Column(String(10), default="CNY")

    # 关系网络
    related_projects = Column(JSON, nullable=True)
    related_cases = Column(JSON, nullable=True)

    # 风险评估
    risk_level = Column(String(20), default="low")
    risk_factors = Column(JSON, nullable=True)
    risk_warnings = Column(JSON, nullable=True)

    # 进度
    progress = Column(Float, default=0.0)

    # AI 法律顾问分析
    legal_analysis = Column(Text, nullable=True)
    legal_advice = Column(Text, nullable=True)
    contract_review = Column(Text, nullable=True)
    suggested_documents = Column(JSON, nullable=True)
    milestones = Column(JSON, nullable=True)
    reminders = Column(JSON, nullable=True)

    # 元数据
    is_archived = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    documents = relationship("ProjectDocument", back_populates="project", cascade="all, delete-orphan")
    milestones_records = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")
    communications = relationship("ProjectCommunication", back_populates="project", cascade="all, delete-orphan")
    evidence_materials = relationship("ProjectEvidence", back_populates="project", cascade="all, delete-orphan")
    legal_advices = relationship("ProjectLegalAdvice", back_populates="project", cascade="all, delete-orphan")
    events = relationship("ProjectEvent", back_populates="project", cascade="all, delete-orphan")
    contracts = relationship("ProjectContract", back_populates="project", cascade="all, delete-orphan")
    risk_records = relationship("ProjectRisk", back_populates="project", cascade="all, delete-orphan")


class ProjectDocument(Base):
    """项目文档"""
    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)

    doc_type = Column(String(50), nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    received_date = Column(DateTime, nullable=True)
    content = Column(Text, nullable=True)
    content_summary = Column(Text, nullable=True)
    
    ai_review = Column(Text, nullable=True)
    risk_points = Column(JSON, nullable=True)
    favorable_clauses = Column(JSON, nullable=True)
    unfavorable_clauses = Column(JSON, nullable=True)
    suggested_amendments = Column(JSON, nullable=True)
    
    status = Column(String(50), default="draft")
    version = Column(String(20), default="1.0")
    previous_version_id = Column(Integer, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="documents")


class ProjectMilestone(Base):
    """项目里程碑"""
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)

    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    milestone_type = Column(String(50), nullable=True)
    phase = Column(String(50))
    planned_date = Column(DateTime, nullable=True)
    actual_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="pending")
    ai_reminder = Column(Text, nullable=True)
    legal_tips = Column(Text, nullable=True)
    related_document_id = Column(Integer, nullable=True)
    order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="milestones_records")


class ProjectCommunication(Base):
    """往来记录"""
    __tablename__ = "project_communications"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)

    communication_type = Column(String(50), nullable=False)
    direction = Column(String(20), nullable=False)
    subject = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    full_content = Column(Text, nullable=True)
    counterpart_name = Column(String(200), nullable=True)
    counterpart_role = Column(String(100), nullable=True)
    communication_date = Column(DateTime, nullable=True)
    recorded_by = Column(String(50), nullable=True)
    
    ai_summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)
    promises_made = Column(JSON, nullable=True)
    disputes_raised = Column(JSON, nullable=True)
    evidence_value = Column(String(20), default="low")
    is_key_evidence = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="communications")


class ProjectEvidence(Base):
    """证据材料"""
    __tablename__ = "project_evidence"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)

    evidence_type = Column(String(50), nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    obtained_date = Column(DateTime, nullable=True)
    content = Column(Text, nullable=True)
    content_summary = Column(Text, nullable=True)
    
    probative_value = Column(String(20), default="medium")
    authenticity = Column(String(20), default="unknown")
    legality = Column(String(20), default="legal")
    
    ai_analysis = Column(Text, nullable=True)
    usage_suggestions = Column(Text, nullable=True)
    risk_warnings = Column(Text, nullable=True)
    
    related_events = Column(JSON, nullable=True)
    related_communications = Column(JSON, nullable=True)
    
    status = Column(String(50), default="collected")
    is_key_evidence = Column(Boolean, default=False)
    file_path = Column(String(500), nullable=True)
    completeness = Column(Float, default=0.5)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="evidence_materials")


class ProjectLegalAdvice(Base):
    """法律建议"""
    __tablename__ = "project_legal_advices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)

    advice_type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    applicable_phase = Column(String(50), nullable=True)
    applicable_situation = Column(Text, nullable=True)
    urgency = Column(String(20), default="medium")
    is_read = Column(Boolean, default=False)
    is_acted = Column(Boolean, default=False)
    action_taken = Column(Text, nullable=True)
    action_date = Column(DateTime, nullable=True)
    model_used = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="legal_advices")


class ProjectEvent(Base):
    """项目事件"""
    __tablename__ = "project_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)

    event_type = Column(String(50), nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(DateTime, nullable=False)
    importance = Column(String(20), default="normal")
    
    ai_analysis = Column(Text, nullable=True)
    legal_significance = Column(Text, nullable=True)
    suggestions = Column(Text, nullable=True)
    
    related_milestone_id = Column(Integer, nullable=True)
    related_communication_id = Column(Integer, nullable=True)
    related_evidence_id = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="events")


class ProjectContract(Base):
    """合同管理"""
    __tablename__ = "project_contracts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)

    contract_type = Column(String(50), nullable=True)
    contract_name = Column(String(500), nullable=False)
    contract_number = Column(String(100), nullable=True)
    party_a = Column(String(500), nullable=True)
    party_b = Column(String(500), nullable=True)
    amount = Column(String(100), nullable=True)
    currency = Column(String(10), default="CNY")
    signing_date = Column(DateTime, nullable=True)
    effective_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="draft")
    
    key_terms = Column(JSON, nullable=True)
    favorable_terms = Column(JSON, nullable=True)
    unfavorable_terms = Column(JSON, nullable=True)
    risk_clauses = Column(JSON, nullable=True)
    
    performance_status = Column(String(50), nullable=True)
    performance_records = Column(JSON, nullable=True)
    
    ai_review = Column(Text, nullable=True)
    risk_level = Column(String(20), default="medium")
    overall_evaluation = Column(Text, nullable=True)
    
    current_version = Column(String(20), default="1.0")
    versions = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="contracts")


class ProjectRisk(Base):
    """风险记录"""
    __tablename__ = "project_risks"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)

    risk_type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="medium")
    probability = Column(String(20), default="medium")
    impact = Column(String(20), default="medium")
    status = Column(String(50), default="identified")
    mitigation_plan = Column(Text, nullable=True)
    preventive_measures = Column(JSON, nullable=True)
    contingency_plan = Column(Text, nullable=True)
    related_clause = Column(Text, nullable=True)
    related_event_id = Column(Integer, nullable=True)
    is_monitored = Column(Boolean, default=True)
    monitor_frequency = Column(String(20), default="weekly")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="risk_records")


class ProjectToCase(Base):
    """项目转案件映射"""
    __tablename__ = "project_case_mappings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    case_id = Column(Integer, nullable=True)

    conversion_reason = Column(Text, nullable=True)
    conversion_date = Column(DateTime, default=datetime.utcnow)
    migrated_documents = Column(JSON, nullable=True)
    migrated_evidence = Column(JSON, nullable=True)
    migrated_communications = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
