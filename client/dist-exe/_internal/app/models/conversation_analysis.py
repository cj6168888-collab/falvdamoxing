"""
对话分析结果模型 - 支持全局分析、多轮对话、认可/删除、文书推荐
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class ConversationAnalysis(Base):
    """对话中的分析结果 - 支持认可/删除"""
    __tablename__ = "conversation_analyses"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(50), nullable=True, index=True)  # 关联对话会话

    # 分析内容
    analysis_type = Column(String(50), default="global")  # global / follow_up / correction / supplement
    content = Column(Text, nullable=False)  # 分析结果全文
    summary = Column(Text, nullable=True)  # 分析摘要

    # 用户反馈
    is_approved = Column(Boolean, default=False)  # 用户是否认可
    approved_at = Column(DateTime, nullable=True)  # 认可时间
    is_deleted = Column(Boolean, default=False)  # 用户是否删除
    deleted_at = Column(DateTime, nullable=True)

    # 上下文标记
    is_main_context = Column(Boolean, default=False)  # 是否作为主要脉络参考
    priority = Column(Integer, default=0)  # 优先级（用户可调整）

    # 关联证据
    evidence_ids = Column(JSON, nullable=True)  # 关联的证据 ID 列表
    party_roles = Column(JSON, nullable=True)  # {"plaintiff": "原告名", "defendant": "被告名", "third_party": "第三方名"}

    # 文书推荐
    recommended_documents = Column(JSON, nullable=True)  # [{"type": "起诉状", "reason": "...", "template_id": "..."}]

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "case_id": self.case_id,
            "session_id": self.session_id,
            "analysis_type": self.analysis_type,
            "content": self.content,
            "summary": self.summary,
            "is_approved": self.is_approved,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "is_deleted": self.is_deleted,
            "is_main_context": self.is_main_context,
            "priority": self.priority,
            "evidence_ids": self.evidence_ids,
            "party_roles": self.party_roles,
            "recommended_documents": self.recommended_documents,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ConversationContext(Base):
    """对话上下文 - 存储被认可的分析结果作为后续对话的上下文"""
    __tablename__ = "conversation_contexts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # 上下文内容
    context_data = Column(JSON, nullable=True)  # 结构化上下文
    context_text = Column(Text, nullable=True)  # 文本上下文

    # 来源
    source_analysis_ids = Column(JSON, nullable=True)  # 来源分析记录 ID 列表

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "case_id": self.case_id,
            "context_data": self.context_data,
            "context_text": self.context_text,
            "source_analysis_ids": self.source_analysis_ids,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
