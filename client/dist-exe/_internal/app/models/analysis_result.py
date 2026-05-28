"""
AI 分析结果模型 - 持久化存储
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class AnalysisResult(Base):
    """AI 分析结果持久化存储"""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)  # full / evidence / strategy / risk / custom
    depth = Column(String(20), default="standard")  # quick / standard / deep / exhaustive
    status = Column(String(20), default="pending")  # pending / running / completed / failed

    # 分析参数
    custom_prompt = Column(Text, nullable=True)
    options = Column(JSON, nullable=True)

    # 分析结果
    result_data = Column(JSON, nullable=True)  # 结构化结果
    summary = Column(Text, nullable=True)  # 分析摘要
    full_report = Column(Text, nullable=True)  # 完整报告

    # 统计信息
    evidence_count = Column(Integer, default=0)
    document_count = Column(Integer, default=0)
    total_stages = Column(Integer, default=0)
    completed_stages = Column(Integer, default=0)
    confidence_score = Column(Float, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 错误信息
    error_message = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "case_id": self.case_id,
            "analysis_type": self.analysis_type,
            "depth": self.depth,
            "status": self.status,
            "custom_prompt": self.custom_prompt,
            "options": self.options,
            "result_data": self.result_data,
            "summary": self.summary,
            "full_report": self.full_report,
            "evidence_count": self.evidence_count,
            "document_count": self.document_count,
            "total_stages": self.total_stages,
            "completed_stages": self.completed_stages,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }
