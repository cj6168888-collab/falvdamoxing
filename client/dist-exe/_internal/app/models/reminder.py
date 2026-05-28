from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class ReminderType(str, enum.Enum):
    """提醒类型"""
    DEADLINE = "deadline"           # 期限提醒
    MATERIAL_MISSING = "material_missing"  # 材料缺失
    HEARING = "hearing"            # 开庭提醒
    EVIDENCE = "evidence"           # 证据提醒
    RISK = "risk"                  # 风险预警
    OPPORTUNITY = "opportunity"    # 机会提示
    STRATEGY = "strategy"          # 策略建议


class ReminderPriority(str, enum.Enum):
    """优先级"""
    HIGH = "high"      # 高
    MEDIUM = "medium"  # 中
    LOW = "low"        # 低


class Reminder(Base):
    """提醒模型"""
    __tablename__ = "reminders"
    __table_args__ = (
        Index("ix_reminders_tenant_case_open_title", "tenant_id", "case_id", "is_completed", "title"),
        Index("ix_reminders_tenant_trigger", "tenant_id", "is_completed", "trigger_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    reminder_type = Column(SQLEnum(ReminderType))
    priority = Column(SQLEnum(ReminderPriority), default=ReminderPriority.MEDIUM)

    title = Column(String(500), nullable=False)  # 提醒标题
    content = Column(Text, nullable=False)  # 提醒内容
    suggestion = Column(Text, nullable=True)  # 建议内容

    # 触发条件
    trigger_date = Column(DateTime, nullable=True)  # 触发日期
    is_triggered = Column(Boolean, default=False)  # 是否已触发
    is_read = Column(Boolean, default=False)  # 是否已读
    is_completed = Column(Boolean, default=False)  # 是否已完成

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="reminders")
