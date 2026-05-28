"""
上诉流程模型 - 第二审程序的完整流程管理
包括：上诉准备、上诉材料、上诉节点追踪、答辩策略等
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class AppealType(str, enum.Enum):
    """上诉类型"""
    FIRST_TO_SECOND = "first_to_second"     # 一审到二审
    SECOND_TO_RETRIAL = "second_to_retrial"  # 二审到再审
    RETRIAL = "retrial"                    # 再审申请


class AppealReason(str, enum.Enum):
    """上诉理由"""
    FACTUAL_ERROR = "factual_error"         # 事实认定错误
    LEGAL_ERROR = "legal_error"            # 法律适用错误
    PROCEDURAL_VIOLATION = "procedural"     # 程序违法
    NEW_EVIDENCE = "new_evidence"           # 新证据
    INSUFFICIENT_EVIDENCE = "insufficient"  # 证据不足
    OTHER = "other"                         # 其他


class AppealStatus(str, enum.Enum):
    """上诉状态"""
    PREPARING = "preparing"                # 准备中
    SUBMITTED = "submitted"                # 已提交
    ACCEPTED = "accepted"                 # 已受理
    HEARING = "hearing"                   # 开庭审理
    DECIDED = "decided"                   # 已判决
    REJECTED = "rejected"                # 被驳回
    WITHDRAWN = "withdrawn"              # 已撤回


class AppealRecord(Base):
    """
    上诉记录
    完整记录上诉的全过程
    """
    __tablename__ = "appeal_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 上诉基本信息
    appeal_type = Column(SQLEnum(AppealType), default=AppealType.FIRST_TO_SECOND)
    appeal_reason = Column(SQLEnum(AppealReason), default=AppealReason.LEGAL_ERROR)

    # 原审信息
    original_case_number = Column(String(100), nullable=True)  # 原审案号
    original_court = Column(String(200), nullable=True)       # 原审法院
    original_judge = Column(String(100), nullable=True)       # 原审法官
    original_judgment_date = Column(DateTime, nullable=True) # 原审判决日期
    original_judgment_content = Column(Text, nullable=True)   # 原审判决内容

    # 上诉人信息
    appellant_type = Column(String(50), nullable=True)  # 上诉人类型（原告/被告/第三人）
    appellant_name = Column(String(200), nullable=True)  # 上诉人姓名

    # 时间节点
    judgment_received_date = Column(DateTime, nullable=True)  # 收到判决日期
    appeal_deadline = Column(DateTime, nullable=True)        # 上诉期限截止日
    appeal_submitted_date = Column(DateTime, nullable=True)  # 提交上诉日期
    appeal_accepted_date = Column(DateTime, nullable=True)   # 受理日期
    hearing_date = Column(DateTime, nullable=True)           # 开庭日期
    appeal_decision_date = Column(DateTime, nullable=True)    # 判决日期

    # 状态
    status = Column(SQLEnum(AppealStatus), default=AppealStatus.PREPARING)
    days_remaining = Column(Integer, nullable=True)  # 剩余天数
    is_overdue = Column(Boolean, default=False)      # 是否超期

    # 上诉材料
    appeal_petition = Column(Text, nullable=True)     # 上诉状
    appeal_facts = Column(Text, nullable=True)       # 上诉事实和理由
    new_evidence_list = Column(Text, nullable=True)  # 新证据清单
    original_evidence_used = Column(Text, nullable=True)  # 原审使用的证据

    # 上诉请求
    appeal_requests = Column(Text, nullable=True)    # 上诉请求
    original_requests = Column(Text, nullable=True)   # 原审请求
    modified_requests = Column(Text, nullable=True)  # 变更后的请求

    # 理由分析
    grounds_of_appeal = Column(JSON, nullable=True)  # 上诉理由 [{"reason": "...", "evidence": "..."}]
    opposing_arguments = Column(Text, nullable=True)  # 对方可能的抗辩
    key_disputes = Column(JSON, nullable=True)       # 争议焦点

    # 策略
    strategy = Column(Text, nullable=True)            # 整体策略
    key_arguments = Column(JSON, nullable=True)       # 核心论点
    evidence_plan = Column(JSON, nullable=True)        # 证据计划

    # 进度追踪
    milestones = Column(JSON, nullable=True)  # 进度节点 [{"name": "...", "date": "...", "status": "..."}]

    # 结果
    decision = Column(Text, nullable=True)           # 判决结果
    decision_type = Column(String(50), nullable=True)  # 判决类型（维持/改判/发回）
    favorable_outcome = Column(Boolean, nullable=True)  # 是否有利结果

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="appeal_records")


class AppealDeadline(Base):
    """
    上诉期限追踪
    精确管理上诉各环节的时间节点
    """
    __tablename__ = "appeal_deadlines"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    appeal_record_id = Column(Integer, ForeignKey("appeal_records.id", ondelete="CASCADE"), index=True)

    # 期限信息
    deadline_type = Column(String(100), nullable=False)  # 期限类型
    deadline_name = Column(String(500), nullable=False)   # 期限名称
    deadline_date = Column(DateTime, nullable=True)       # 截止日期

    # 期限说明
    description = Column(Text, nullable=True)     # 期限说明
    legal_basis = Column(Text, nullable=True)    # 法律依据

    # 状态
    status = Column(String(50), default="pending")  # pending/active/expired/completed
    days_remaining = Column(Integer, nullable=True)
    is_mandatory = Column(Boolean, default=True)

    # 提醒
    reminder_days = Column(JSON, nullable=True)  # 提醒天数 [30, 15, 7, 3, 1]

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppealArgument(Base):
    """
    上诉论点
    记录每个上诉论点的详细内容
    """
    __tablename__ = "appeal_arguments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    appeal_record_id = Column(Integer, ForeignKey("appeal_records.id", ondelete="CASCADE"), index=True)

    # 论点信息
    argument_type = Column(String(50), nullable=False)  # 事实错误/法律错误/程序违法
    title = Column(String(500), nullable=False)        # 论点标题
    description = Column(Text, nullable=True)          # 详细描述

    # 原审认定 vs 上诉主张
    original_finding = Column(Text, nullable=True)   # 原审认定
    appeal_finding = Column(Text, nullable=True)      # 上诉主张
    discrepancy = Column(Text, nullable=True)          # 差异说明

    # 证据支持
    supporting_evidence = Column(JSON, nullable=True)  # 支持证据
    counter_evidence = Column(JSON, nullable=True)     # 反驳原审证据

    # 法律依据
    legal_basis = Column(JSON, nullable=True)          # 法律依据

    # 论证
    reasoning = Column(Text, nullable=True)           # 论证过程
    expected_opposition = Column(Text, nullable=True)  # 预期反驳
    counter_response = Column(Text, nullable=True)   # 应对反驳

    # 权重和评估
    importance = Column(String(20), default="medium")  # high/medium/low
    success_probability = Column(Float, nullable=True)  # 成功概率 0-1
    is_key_argument = Column(Boolean, default=False)  # 是否为核心论点

    # 状态
    status = Column(String(50), default="draft")  # draft/submitted/accepted/rejected
    ai_suggestions = Column(Text, nullable=True) # AI优化建议

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppealDocument(Base):
    """
    上诉材料
    追踪上诉所需的各种材料
    """
    __tablename__ = "appeal_documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    appeal_record_id = Column(Integer, ForeignKey("appeal_records.id", ondelete="CASCADE"), index=True)

    # 材料信息
    document_type = Column(String(100), nullable=False)  # 材料类型
    document_name = Column(String(500), nullable=False) # 材料名称
    description = Column(Text, nullable=True)            # 材料说明

    # 来源和状态
    source = Column(String(50), nullable=True)   # 来源（我方/原审案卷/新证据）
    status = Column(String(50), default="pending")  # pending/prepared/submitted/accepted/rejected
    is_required = Column(Boolean, default=True)   # 是否必需

    # 关联
    related_document_id = Column(Integer, nullable=True)  # 关联的原始文档ID
    purpose = Column(Text, nullable=True)                # 用途说明

    # 内容
    content_summary = Column(Text, nullable=True)  # 内容摘要
    key_points = Column(JSON, nullable=True)       # 关键要点

    # AI 生成
    ai_summary = Column(Text, nullable=True)      # AI摘要
    ai_suggestions = Column(Text, nullable=True)  # 使用建议

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecondTrialStrategy(Base):
    """
    二审答辩策略
    针对上诉人的上诉进行答辩
    """
    __tablename__ = "second_trial_strategies"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    appeal_record_id = Column(Integer, ForeignKey("appeal_records.id", ondelete="CASCADE"), index=True)

    # 策略基本信息
    title = Column(String(500), nullable=False)

    # 针对的上诉论点
    target_arguments = Column(JSON, nullable=True)  # 针对的上诉论点ID列表

    # 答辩内容
    defense_points = Column(JSON, nullable=True)  # 答辩要点
    defense_reasoning = Column(Text, nullable=True)  # 答辩论证

    # 证据
    supporting_evidence = Column(JSON, nullable=True)  # 支持答辩的证据
    counter_evidence = Column(JSON, nullable=True)     # 反驳上诉证据

    # 法律依据
    legal_basis = Column(JSON, nullable=True)     # 法律依据

    # 预期结果
    expected_outcome = Column(Text, nullable=True)  # 预期结果
    favorable_arguments = Column(JSON, nullable=True)  # 有利论点

    # 状态
    is_approved = Column(Boolean, default=False)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
