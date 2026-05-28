"""
租户（Tenant）模型 - SaaS 多租户核心
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class TenantType(str, enum.Enum):
    """租户类型"""
    LAW_FIRM = "law_firm"      # 律所
    ENTERPRISE = "enterprise"  # 企业


class SubscriptionPlan(str, enum.Enum):
    """订阅套餐"""
    FREE = "free"
    TRIAL = "trial"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class SubscriptionStatus(str, enum.Enum):
    """订阅状态"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class Tenant(Base):
    """租户（律所/企业）"""
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    tenant_type = Column(SQLEnum(TenantType), nullable=False, default=TenantType.LAW_FIRM)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)

    # 订阅信息
    plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.FREE)
    subscription_status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    subscription_expires_at = Column(DateTime, nullable=True)
    max_users = Column(Integer, default=3)
    max_cases = Column(Integer, default=10)
    max_storage_gb = Column(Integer, default=5)

    # 域配置
    custom_domain = Column(String(255), nullable=True)
    allowed_email_domains = Column(Text, nullable=True)

    # AI 配置
    ai_model_preference = Column(String(50), default="legalone-r1:8b")
    ai_daily_quota = Column(Integer, default=100)
    ai_monthly_usage = Column(Integer, default=0)

    # 计费
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)

    # 审批与计费
    approval_status = Column(String(20), default="approved")  # approved/pending/rejected
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(200), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    billing_cycle = Column(String(20), default="monthly")  # monthly/yearly
    billing_amount = Column(Integer, default=0)  # 月/年费（元）
    billing_due_date = Column(DateTime, nullable=True)
    billing_method = Column(String(50), nullable=True)  # wechat/alipay/bank_transfer
    registered_from = Column(String(500), nullable=True)  # 注册来源（IP/域名）

    # 状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tenant_type": self.tenant_type.value if self.tenant_type else None,
            "slug": self.slug,
            "logo_url": self.logo_url,
            "plan": self.plan.value if self.plan else None,
            "subscription_status": self.subscription_status.value if self.subscription_status else None,
            "approval_status": self.approval_status,
            "billing_cycle": self.billing_cycle,
            "billing_amount": self.billing_amount,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
