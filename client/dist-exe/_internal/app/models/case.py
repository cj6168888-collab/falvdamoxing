"""
案件模型扩展 - 支持复杂案件结构
包括：多线索、多当事人、反诉等
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Float, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class CaseStatus(str, enum.Enum):
    """案件状态"""
    RECEIVED = "收案"           # 收案
    REVIEWING = "审查中"        # 审查中
    FILED = "已立案"           # 已立案
    EVIDENCE = "证据准备"       # 证据准备
    PRE_TRIAL = "诉前准备"      # 诉前准备
    LITIGATION = "起诉答辩"     # 起诉/答辩
    TRIAL_PREP = "开庭准备"     # 开庭准备
    TRIAL = "开庭审理"         # 开庭审理
    JUDGMENT = "判决"          # 判决
    EXECUTION = "执行中"       # 执行中
    CLOSED = "已结案"          # 已结案
    ARCHIVED = "已归档"        # 已归档（仅存档，不删除）
    # biz-13: 案件中止/休眠状态
    SUSPENDED = "已中止"        # 案件中止（因法定事由暂停审理）
    DORMANT = "休眠"           # 案件休眠（长期无进展，需要激活处理）


class CaseType(str, enum.Enum):
    """案件类型"""
    CIVIL = "民事"
    CRIMINAL = "刑事"
    ADMINISTRATIVE = "行政"
    ARBITRATION = "仲裁"


class ThreadStatus(str, enum.Enum):
    """线索状态"""
    ACTIVE = "进行中"           # 进行中
    PENDING = "待处理"          # 待处理
    RESOLVED = "已解决"         # 已解决
    MERGED = "已合并"           # 已合并
    DROPPED = "已放弃"          # 已放弃


class PartyRole(str, enum.Enum):
    """当事人角色"""
    PLAINTIFF = "原告"          # 原告
    DEFENDANT = "被告"          # 被告
    THIRD_PARTY = "第三人"      # 第三人
    COUNTER_PLAINTIFF = "反诉原告"  # 反诉原告
    COUNTER_DEFENDANT = "反诉被告"  # 反诉被告
    APPELLANT = "上诉人"         # 上诉人
    RESPONDENT = "被上诉人"     # 被上诉人


class Case(Base):
    """案件模型"""
    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_tenant_updated_at", "tenant_id", "updated_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_number = Column(String(100), unique=True, index=True, nullable=True)  # 案号
    title = Column(String(500), nullable=False)  # 案件标题
    case_type = Column(String(50), default="民事")  # 案件类型
    status = Column(String(50), default="收案")  # 案件状态

    # 当事人信息（兼容旧数据）
    plaintiff = Column(Text, nullable=True)  # 原告
    defendant = Column(Text, nullable=True)  # 被告
    third_party = Column(Text, nullable=True)  # 第三人

    # 案件概述
    cause = Column(Text, nullable=True)  # 案由
    claim_amount = Column(String(100), nullable=True)  # 诉讼金额
    description = Column(Text, nullable=True)  # 案件描述
    summary = Column(Text, nullable=True)  # 案件概述
    background = Column(Text, nullable=True)  # 背景介绍
    supplement = Column(Text, nullable=True)  # 补充说明

    # 主要案由
    primary_cause = Column(String(200), nullable=True)  # 主要案由

    # AI 分析结果
    legal_analysis = Column(Text, nullable=True)
    strategy_suggestion = Column(Text, nullable=True)

    # 案件处理方向
    case_direction = Column(String(50), default="mediate")  # 友好协商/调解优先/诉讼解决/战略防守/适时退让

    # 时间相关
    filed_date = Column(DateTime, nullable=True)
    trial_date = Column(DateTime, nullable=True)
    judgment_date = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    # ============ 结案相关字段 ============
    # 结案结果
    closure_result = Column(Text, nullable=True)      # 结案结果/判决内容
    closure_type = Column(String(50), nullable=True)  # 结案类型：判决/调解/和解/撤诉/其他
    closure_amount = Column(String(100), nullable=True)  # 结案金额（实际执行/赔付金额）
    closure_date = Column(DateTime, nullable=True)    # 结案日期

    # 是否转入执行
    is_transferred_to_execution = Column(Boolean, default=False)  # 是否转入执行
    execution_case_number = Column(String(100), nullable=True)     # 执行案号
    execution_status = Column(String(50), nullable=True)           # 执行状态
    execution_progress = Column(Float, default=0.0)                # 执行进度 0-100%

    # 结案备注
    closure_notes = Column(Text, nullable=True)  # 结案备注/总结
    is_archived = Column(Boolean, default=False)  # 是否已归档

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    threads = relationship("CaseThread", back_populates="case", cascade="all, delete-orphan")
    parties = relationship("Party", back_populates="case", cascade="all, delete-orphan")
    counter_claims = relationship("CounterClaim", back_populates="case", cascade="all, delete-orphan")
    claims = relationship("CaseClaim", back_populates="case", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="case", cascade="all, delete-orphan")
    chat_history = relationship("ChatMessage", back_populates="case", cascade="all, delete-orphan")
    adversarial_analyses = relationship("AdversarialAnalysis", back_populates="case", cascade="all, delete-orphan")
    scenario_predictions = relationship("ScenarioPrediction", back_populates="case", cascade="all, delete-orphan")
    process_milestones = relationship("ProcessMilestone", back_populates="case", cascade="all, delete-orphan")
    execution_tracking = relationship("ExecutionTracking", back_populates="case", cascade="all, delete-orphan")
    archive = relationship("CaseArchive", back_populates="case", uselist=False)
    
    # 时间把控相关
    letters = relationship("Letter", back_populates="case", cascade="all, delete-orphan")
    legal_deadlines = relationship("LegalDeadline", back_populates="case", cascade="all, delete-orphan")
    case_timelines = relationship("CaseTimeline", back_populates="case", cascade="all, delete-orphan")

    # 出庭抗辩相关
    hearing_records = relationship("HearingRecord", back_populates="case", cascade="all, delete-orphan")
    speaking_strategies = relationship("CaseSpeakingStrategy", back_populates="case", cascade="all, delete-orphan")

    # 上诉流程相关
    appeal_records = relationship("AppealRecord", back_populates="case", cascade="all, delete-orphan")

    # 案件节点（重要资料补充记录）
    nodes = relationship("CaseNode", back_populates="case", cascade="all, delete-orphan")

    # ========== 证据文件夹相关字段 ==========
    evidence_folder_path = Column(String(1000), nullable=True, comment="证据文件夹路径")
    evidence_folder_enabled = Column(Boolean, default=False, comment="是否启用文件夹监控")
    evidence_last_scan_time = Column(DateTime, nullable=True, comment="最后扫描时间")
    evidence_last_sync_count = Column(Integer, default=0, comment="最后同步文件数")

    # ========== 逻辑闭环新增 ==========
    # 生成的法律文书
    generated_documents = relationship("GeneratedDocument", back_populates="case", cascade="all, delete-orphan")
    # 文书生成建议
    document_suggestions = relationship("DocumentSuggestion", back_populates="case", cascade="all, delete-orphan")

    # 证据文件夹关联 (使用字符串引用，延迟解析)
    folder_scans = relationship("EvidenceFolderScan", back_populates="case", cascade="all, delete-orphan", lazy="noload", overlaps="folder_scans,case")
    folder_files = relationship("EvidenceFolderFile", back_populates="case", cascade="all, delete-orphan", lazy="noload", overlaps="folder_files,case")

    # 执行跟踪 V2 相关
    execution_records = relationship("ExecutionRecord", back_populates="case", cascade="all, delete-orphan")
    execution_tasks = relationship("ExecutionTask", back_populates="case", cascade="all, delete-orphan")
    execution_assets = relationship("ExecutionAsset", back_populates="case", cascade="all, delete-orphan")
    execution_stage_tracking = relationship("ExecutionStage", back_populates="case", cascade="all, delete-orphan")

    # 财务相关
    case_finance = relationship("CaseFinance", back_populates="case", uselist=False, cascade="all, delete-orphan")
    expense_records = relationship("ExpenseRecord", back_populates="case", cascade="all, delete-orphan")
    win_rate_assessments = relationship("WinRateAssessment", back_populates="case", cascade="all, delete-orphan")


class CaseThread(Base):
    """
    案件线索/分支
    支持一个案件包含多个法律关系、多个纠纷类型
    例如：合作纠纷中包含 欠薪、劳务纠纷、债务 多个线索
    """
    __tablename__ = "case_threads"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    # 线索基本信息
    name = Column(String(200), nullable=False)  # 线索名称，如"欠薪纠纷"、"债务纠纷"
    cause = Column(String(200), nullable=True)  # 案由
    description = Column(Text, nullable=True)  # 线索描述

    # 线索状态
    status = Column(SQLEnum(ThreadStatus), default=ThreadStatus.ACTIVE)

    # 金额
    amount = Column(String(100), nullable=True)  # 涉及金额

    # 关联的另一条线索（如果存在关联）
    related_thread_id = Column(Integer, ForeignKey("case_threads.id"), nullable=True)

    # 证据关联
    evidence_summary = Column(Text, nullable=True)  # 证据摘要

    # 排序
    sort_order = Column(Integer, default=0)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="threads")
    parent_thread = relationship("CaseThread", remote_side=[id], backref="child_threads")


class Party(Base):
    """
    当事人
    支持原告、被告、第三人等多种角色
    """
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    # 当事人信息
    name = Column(String(200), nullable=False)  # 名称
    party_type = Column(String(50), nullable=True)  # 个人/企业/其他
    role = Column(SQLEnum(PartyRole), nullable=False)  # 角色

    # 联系方式
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)

    # 代理人
    agent_name = Column(String(100), nullable=True)
    agent_phone = Column(String(50), nullable=True)
    agent_relation = Column(String(100), nullable=True)  # 与当事人关系

    # 当事人之间的关系说明
    relation_to_case = Column(Text, nullable=True)  # 与案件的关联说明

    # 排序
    sort_order = Column(Integer, default=0)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="parties")


class CounterClaim(Base):
    """
    反诉/追加请求
    支持被告反诉、追加诉讼请求等情况
    """
    __tablename__ = "counter_claims"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    # 反诉信息
    claim_type = Column(String(50), nullable=False)  # 反诉/追加第三人/变更诉讼请求等
    title = Column(String(200), nullable=False)  # 反诉标题
    description = Column(Text, nullable=True)  # 详细描述

    # 涉及金额
    amount = Column(String(100), nullable=True)

    # 关联的当事人
    counter_plaintiff_id = Column(Integer, nullable=True)  # 反诉原告（当事人ID）
    counter_defendant_id = Column(Integer, nullable=True)  # 反诉被告（当事人ID）

    # 状态
    is_filed = Column(Boolean, default=False)  # 是否已立案
    status = Column(String(50), default="pending")  # pending/accepted/rejected

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="counter_claims")


class ChatMessage(Base):
    """聊天记录"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    role = Column(String(20))  # user / assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="chat_history")


class ExecutionTracking(Base):
    """执行跟踪记录"""
    __tablename__ = "execution_tracking"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 执行基本信息
    execution_case_number = Column(String(100), nullable=True)  # 执行案号
    execution_court = Column(String(200), nullable=True)       # 执行法院
    executor_name = Column(String(100), nullable=True)         # 执行法官姓名
    executor_phone = Column(String(50), nullable=True)          # 执行法官电话

    # 执行标的
    execution_amount = Column(String(100), nullable=True)      # 执行标的金额
    executed_amount = Column(String(100), nullable=True)        # 已执行金额
    remaining_amount = Column(String(100), nullable=True)       # 剩余金额

    # 执行状态
    status = Column(String(50), default="pending")              # pending/in_progress/partially_completed/fully_completed/terminated
    progress = Column(Float, default=0.0)                       # 执行进度 0-100%

    # 执行进展记录
    records = Column(JSON, nullable=True)                       # 执行记录列表 [{date, content, result}]

    # 需要协助的事项
    assistance_needed = Column(Text, nullable=True)            # 需要我方协助的事项
    assistance_status = Column(String(50), default="pending")   # pending/providing/completed

    # 下次跟进日期
    next_follow_up = Column(DateTime, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="execution_tracking")


class CaseArchive(Base):
    """案件归档记录"""
    __tablename__ = "case_archives"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="SET NULL"), nullable=True)

    # 归档信息
    archive_date = Column(DateTime, default=datetime.utcnow)   # 归档日期
    archive_reason = Column(String(200), nullable=True)        # 归档原因

    # 结案摘要
    case_summary = Column(Text, nullable=True)                # 案件摘要
    outcome = Column(Text, nullable=True)                      # 最终结果
    lessons_learned = Column(Text, nullable=True)              # 经验教训

    # 关联文档
    related_docs = Column(JSON, nullable=True)                 # 相关文档ID列表

    # 归档状态
    is_active = Column(Boolean, default=True)                  # 是否有效（可重新激活）

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="archive")


class CaseNode(Base):
    """案件节点 - 记录重要资料补充和事件"""
    __tablename__ = "case_nodes"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 节点基本信息
    node_type = Column(String(50), nullable=False)  # supplement/evidence/upload/analysis/hearing/other
    title = Column(String(500), nullable=True)       # 节点标题
    description = Column(Text, nullable=True)       # 节点描述

    # 关联内容
    content = Column(Text, nullable=True)           # 补充内容
    related_document_ids = Column(JSON, nullable=True)  # 关联文档ID列表

    # AI分析结果
    key_points = Column(Text, nullable=True)         # AI提炼的关键要点
    analysis_result = Column(Text, nullable=True)    # AI分析结果
    action_suggestions = Column(Text, nullable=True) # 后续行动建议

    # 节点状态
    status = Column(String(50), default="pending")   # pending/processed/reviewed/approved

    # 流程影响
    affects_direction = Column(Boolean, default=False)  # 是否影响案件方向
    direction_change = Column(Text, nullable=True)       # 方向变化说明

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="nodes")
