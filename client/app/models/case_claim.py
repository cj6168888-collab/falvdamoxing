"""
战役/诉求模型 - 文书对话核心
支持案件下的多诉求管理，每个诉求对应一场"战役"
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class CaseClaimStatus(str, enum.Enum):
    """战役状态"""
    PENDING = "待处理"
    ACTIVE = "进行中"
    COMPLETED = "已完成"
    ABANDONED = "已放弃"


class CaseClaim(Base):
    """
    战役/诉求模型
    
    核心理念：
    - 一个案件可有多个诉求（战役）
    - 每个战役需要特定的文书和证据
    - 战役之间可能有依赖关系
    - 证据可被多个战役复用
    """
    __tablename__ = "case_claims"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # ==================== 战役基础信息 ====================
    title = Column(String(200), nullable=False, comment="战役标题，如'主张欠款本金'")
    description = Column(Text, nullable=True, comment="诉求详情描述")
    claim_type = Column(String(50), nullable=True, comment="诉求类型：欠款/违约金/赔偿/反诉等")
    amount = Column(String(100), nullable=True, comment="涉及金额")
    
    # ==================== 战役属性 ====================
    priority = Column(Integer, default=3, comment="优先级 1-5，1最高")
    status = Column(String, default=CaseClaimStatus.PENDING.value, comment="战役状态")
    
    # ==================== 战役规划（JSON） ====================
    required_documents = Column(JSON, default=list, comment="需要生成的文书类型列表")
    required_evidence_ids = Column(JSON, default=list, comment="需要的证据ID列表")
    depends_on = Column(JSON, default=list, comment="依赖的其他战役ID")
    
    # ==================== AI 规划结果 ====================
    ai_plan_result = Column(Text, nullable=True, comment="AI 规划详情")
    ai_evidence_suggestions = Column(JSON, default=list, comment="AI 推荐的关键证据")
    ai_document_suggestions = Column(JSON, default=list, comment="AI 推荐的文书类型")
    
    # ==================== 风险评估 ====================
    risk_level = Column(String(20), default="medium", comment="风险等级：low/medium/high")
    risk_notes = Column(Text, nullable=True, comment="风险说明")
    
    # ==================== 元数据 ====================
    notes = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ==================== 关系 ====================
    case = relationship("Case", back_populates="claims")
    documents = relationship("GeneratedDocument", back_populates="claim")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "case_id": self.case_id,
            "title": self.title,
            "description": self.description,
            "claim_type": self.claim_type,
            "amount": self.amount,
            "priority": self.priority,
            "status": self.status,
            "required_documents": self.required_documents or [],
            "required_evidence_ids": self.required_evidence_ids or [],
            "depends_on": self.depends_on or [],
            "ai_plan_result": self.ai_plan_result,
            "ai_evidence_suggestions": self.ai_evidence_suggestions or [],
            "ai_document_suggestions": self.ai_document_suggestions or [],
            "risk_level": self.risk_level,
            "risk_notes": self.risk_notes,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "document_count": len(self.documents) if self.documents else 0,
            "evidence_count": len(self.required_evidence_ids or []),
        }
