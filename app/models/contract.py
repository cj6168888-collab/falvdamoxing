"""
合同管理 ORM 模型
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    project_id = Column(Integer, nullable=True)
    title = Column(String(200), nullable=False)
    contract_type = Column(String(50))
    counterparty = Column(String(200))
    amount = Column(Float, default=0)
    sign_date = Column(String(20))
    expiry_date = Column(String(20))
    status = Column(String(20), default="pending")
    content = Column(Text)
    file_path = Column(String(500))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
