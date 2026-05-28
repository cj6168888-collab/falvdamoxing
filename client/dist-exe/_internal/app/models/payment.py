"""
缴费记录模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey
from datetime import datetime
from app.db.database import Base


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    billing_cycle = Column(String(20), default="monthly")  # monthly/yearly
    payment_method = Column(String(50), nullable=True)  # wechat/alipay/bank_transfer/manual
    paid_at = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    status = Column(String(20), default="paid")  # paid/pending/refunded
    notes = Column(String(500), nullable=True)
    created_by = Column(String(200), nullable=True)  # platform admin who recorded it
