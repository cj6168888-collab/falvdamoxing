"""
案件画像数据库模型 - 持久化存储
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from datetime import datetime
from app.db.database import Base


class CaseProfile(Base):
    """案件画像"""
    __tablename__ = "case_profiles"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, unique=True, index=True, nullable=False)
    
    # 基础信息
    basic_info = Column(JSON, nullable=True)
    
    # 画像摘要
    summary = Column(Text, nullable=True)
    core_dispute = Column(Text, nullable=True)
    
    # 知识图谱
    knowledge_atoms = Column(JSON, nullable=True)  # 知识原子列表
    knowledge_base_count = Column(Integer, default=0)
    
    # 对话历史
    conversation_history = Column(JSON, nullable=True)  # 对话回合列表
    conversation_count = Column(Integer, default=0)
    
    # 证据
    evidence_ids = Column(JSON, nullable=True)
    
    # 证据缺口
    tracked_gaps = Column(JSON, nullable=True)
    
    # 评分
    completeness_level = Column(String(20), default="稀疏")
    completeness_score = Column(Float, default=0.0)
    
    # 里程碑
    key_milestones = Column(JSON, nullable=True)
    
    # 元数据
    version = Column(Integer, default=1)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
