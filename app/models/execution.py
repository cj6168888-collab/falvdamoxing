"""
执行跟踪模型 - 判决生效后的强制执行程序管理
包括：执行记录、执行任务、财产线索、执行阶段
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class ExecutionStatus(str, enum.Enum):
    """执行状态"""
    PENDING = "pending"                    # 待申请
    APPLIED = "applied"                    # 已申请执行
    ACCEPTED = "accepted"                  # 法院已受理
    IN_PROGRESS = "in_progress"            # 执行中
    PARTIALLY_COMPLETED = "partially_completed"  # 部分执行
    FULLY_COMPLETED = "fully_completed"    # 全部执行完毕
    TERMINATED = "terminated"              # 终止执行
    SUSPENDED = "suspended"                # 中止执行


class ExecutionStageEnum(str, enum.Enum):
    """执行阶段"""
    APPLICATION = "application"            # 申请执行阶段
    PROPERTY_INVESTIGATION = "property_investigation"  # 财产调查
    PROPERTY_CONTROL = "property_control"  # 财产控制（查封/冻结）
    PROPERTY_DISPOSAL = "property_disposal"  # 财产处置（拍卖/变卖）
    FUND_DISTRIBUTION = "fund_distribution"  # 案款发放
    COMPLETION = "completion"              # 执行完毕


class TaskPriority(str, enum.Enum):
    """任务优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, enum.Enum):
    """任务状态"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssetType(str, enum.Enum):
    """财产类型"""
    BANK_ACCOUNT = "bank_account"          # 银行账户
    REAL_ESTATE = "real_estate"            # 房产
    VEHICLE = "vehicle"                    # 车辆
    EQUITY = "equity"                      # 股权
    RECEIVABLES = "receivables"            # 应收账款
    INTELLECTUAL_PROPERTY = "intellectual_property"  # 知识产权
    OTHER = "other"                        # 其他


class ExecutionRecord(Base):
    """
    执行记录
    记录执行过程中的每一次进展
    """
    __tablename__ = "execution_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 记录信息
    record_date = Column(DateTime, nullable=True)          # 记录日期
    record_type = Column(String(100), nullable=True)       # 记录类型（法院通知/财产查控/案款发放等）
    title = Column(String(500), nullable=True)             # 记录标题
    content = Column(Text, nullable=True)                  # 详细内容
    result = Column(Text, nullable=True)                   # 结果

    # 关联
    court_name = Column(String(200), nullable=True)        # 法院名称
    judge_name = Column(String(100), nullable=True)        # 法官/执行员
    document_number = Column(String(100), nullable=True)   # 文书编号

    # 状态
    stage = Column(SQLEnum(ExecutionStageEnum), nullable=True)  # 当前阶段
    progress = Column(Float, default=0.0)                   # 进度 0-100

    # 附件
    attachments = Column(JSON, nullable=True)              # 附件列表

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="execution_records")


class ExecutionTask(Base):
    """
    执行任务
    管理执行过程中的待办事项
    """
    __tablename__ = "execution_tasks"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 任务信息
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # 分类
    task_type = Column(String(100), nullable=True)         # 任务类型
    stage = Column(SQLEnum(ExecutionStageEnum), nullable=True)  # 所属阶段

    # 优先级和状态
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO)

    # 时间
    due_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)

    # 负责人
    assignee = Column(String(200), nullable=True)

    # 关联
    related_record_id = Column(Integer, nullable=True)
    related_asset_id = Column(Integer, nullable=True)

    # 备注
    notes = Column(Text, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="execution_tasks")


class ExecutionAsset(Base):
    """
    财产线索
    记录被执行人的可供执行财产
    """
    __tablename__ = "execution_assets"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 财产信息
    asset_type = Column(SQLEnum(AssetType), nullable=True)
    asset_name = Column(String(500), nullable=False)       # 财产名称
    description = Column(Text, nullable=True)              # 详细描述

    # 估值
    estimated_value = Column(String(100), nullable=True)   # 估值
    actual_value = Column(String(100), nullable=True)      # 实际处置价值

    # 位置/标识
    location = Column(String(500), nullable=True)          # 财产位置
    identifier = Column(String(200), nullable=True)        # 产权证号/账号等

    # 状态
    status = Column(String(50), default="discovered")      # discovered/confirmed/controlled/disposed
    control_method = Column(String(100), nullable=True)    # 控制方式（查封/冻结/扣押）
    control_date = Column(DateTime, nullable=True)
    disposal_method = Column(String(100), nullable=True)   # 处置方式（拍卖/变卖/抵债）
    disposal_date = Column(DateTime, nullable=True)
    disposal_result = Column(Text, nullable=True)

    # 来源
    source = Column(String(200), nullable=True)            # 线索来源
    source_date = Column(DateTime, nullable=True)

    # 备注
    notes = Column(Text, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="execution_assets")


class ExecutionStage(Base):
    """
    执行阶段追踪
    记录执行程序的各阶段进展
    """
    __tablename__ = "execution_stages"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 阶段信息
    stage = Column(SQLEnum(ExecutionStageEnum), nullable=False)
    stage_name = Column(String(200), nullable=False)

    # 时间
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # 状态
    status = Column(String(50), default="pending")         # pending/active/completed/skipped

    # 内容
    description = Column(Text, nullable=True)
    requirements = Column(JSON, nullable=True)             # 该阶段需要完成的事项
    completed_items = Column(JSON, nullable=True)          # 已完成事项

    # 文书
    documents = Column(JSON, nullable=True)                # 该阶段产生的文书

    # 备注
    notes = Column(Text, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="execution_stage_tracking")
