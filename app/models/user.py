"""
用户（User）模型 - SaaS 多租户认证核心
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class UserRole(str, enum.Enum):
    """用户角色"""
    ADMIN = "admin"          # 管理员
    LAWYER = "lawyer"       # 律师
    ASSISTANT = "assistant"  # 助理
    CLIENT = "client"        # 客户
    VIEWER = "viewer"        # 查看者


class User(Base):
    """用户"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    role = Column(SQLEnum(UserRole), default=UserRole.ASSISTANT)

    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    is_platform_admin = Column(Boolean, default=False)  # 平台超管

    last_login_at = Column(DateTime, nullable=True)
    last_active_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    tenant = relationship("Tenant", back_populates="users")

    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "full_name": self.full_name,
            "role": self.role.value if self.role else None,
            "tenant_id": self.tenant_id,
            "is_active": self.is_active,
            "is_email_verified": self.is_email_verified,
            "is_platform_admin": self.is_platform_admin,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        return data
