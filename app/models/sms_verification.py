"""
短信验证码模型
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.database import Base


class SMSVerificationCode(Base):
    """一次性短信验证码记录。"""

    __tablename__ = "sms_verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(32), nullable=False, index=True)
    purpose = Column(String(32), nullable=False, index=True)
    code_hash = Column(String(128), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    remote_ip = Column(String(64), nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
