"""
API 密钥模型 - 用于程序化 API 访问（替代 JWT）
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from datetime import datetime

from app.db.database import Base


class APIKey(Base):
    """API Key"""
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    key_prefix = Column(String(20), nullable=False)
    key_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)

    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)

    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
