"""
借款记录 ORM 模型
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    project_id = Column(Integer, nullable=True)
    direction = Column(String(10), nullable=False)
    borrower_name = Column(String(100), nullable=False)
    borrower_phone = Column(String(20))
    borrower_id = Column(String(50))
    lender_name = Column(String(100))
    amount = Column(Float, nullable=False)
    start_date = Column(String(20))
    due_date = Column(String(20))
    has_interest = Column(Integer, default=0)
    interest_rate = Column(Float, default=0)
    interest_type = Column(String(20))
    guarantee = Column(String(100))
    purpose = Column(String(200))
    repayment_method = Column(String(50))
    notes = Column(Text)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
