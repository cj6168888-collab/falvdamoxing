"""
证据分析对话模型
用于保存证据分析过程中的问答记录
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class EvidenceAnalysisSession(Base):
    """
    证据分析会话
    记录一次完整的证据分析会话
    """
    __tablename__ = "evidence_analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    evidence_id = Column(String(36), nullable=True, index=True)  # 关联的证据ID

    # 会话概述
    title = Column(String(500), nullable=True)  # 会话标题（如证据名称）
    session_type = Column(String(50), default="evidence_analysis")  # analysis/discussion/debate
    status = Column(String(20), default="active")  # active/completed

    # AI分析结果（JSON存储复杂结构）
    analysis_result = Column(JSON, nullable=True)  # 最终分析结果
    key_findings = Column(JSON, default=list)  # 关键发现
    risk_points = Column(JSON, default=list)  # 风险点
    suggestions = Column(JSON, default=list)  # 建议

    # 统计
    turn_count = Column(Integer, default=0)  # 对话轮次
    user_opinions_count = Column(Integer, default=0)  # 用户意见数
    ai_opinions_count = Column(Integer, default=0)  # AI意见数

    # 最终结论
    final_conclusion = Column(Text, nullable=True)  # 最终结论
    confidence_score = Column(Float, nullable=True)  # 置信度
    conclusion_version = Column(Integer, default=0)  # 结论版本（每次修改+1）

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)  # 完成时间

    # 关系
    case = relationship("Case")
    messages = relationship("EvidenceAnalysisMessage", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


class EvidenceAnalysisMessage(Base):
    """
    证据分析消息
    记录对话中的每一条消息
    """
    __tablename__ = "evidence_analysis_messages"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    session_id = Column(Integer, ForeignKey("evidence_analysis_sessions.id", ondelete="CASCADE"), index=True)

    # 消息概述
    message_type = Column(String(30), nullable=False)  # user/ai/ai_question/ai_challenge/ai_agreement
    role = Column(String(20), nullable=False)  # user/assistant

    # 内容
    content = Column(Text, nullable=False)  # 消息内容
    content_summary = Column(String(500), nullable=True)  # 内容摘要

    # 消息分类
    category = Column(String(50), nullable=True)  # analysis/opinion/challenge/agreement/question/clarification
    is_key_point = Column(Boolean, default=False)  # 是否关键观点

    # AI 角色标识
    ai_role = Column(String(50), nullable=True)  # analyst/critic/devil_advocate/collaborator
    ai_action = Column(String(50), nullable=True)  # 分析/质疑/反驳/同意/提问

    # 关联证据/文件
    related_evidence_id = Column(String(36), nullable=True)  # 关联的证据ID
    related_message_id = Column(Integer, nullable=True)  # 关联的消息ID（用于回复）

    # 评估
    user_rating = Column(Integer, nullable=True)  # 用户评分 1-5
    user_feedback = Column(Text, nullable=True)  # 用户反馈
    is_accepted = Column(Boolean, nullable=True)  # 用户是否采纳

    # AI自我评估
    ai_self_assessment = Column(Text, nullable=True)  # AI自我评估
    reasoning_quality = Column(Float, nullable=True)  # 推理质量 0-1

    # 元数据
    turn_number = Column(Integer, default=1)  # 第几轮对话
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    session = relationship("EvidenceAnalysisSession", back_populates="messages")

    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


class EvidenceAnalysisResult(Base):
    """
    证据分析结果
    存储每次分析的核心结果，用于积累和改进
    """
    __tablename__ = "evidence_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    session_id = Column(Integer, ForeignKey("evidence_analysis_sessions.id", ondelete="CASCADE"), index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    evidence_id = Column(String(36), nullable=True, index=True)

    # 分析类型
    analysis_type = Column(String(50), nullable=False)  # credibility/trap/relationship/completeness
    analysis_target = Column(String(50), nullable=True)  # single/all_files/trap_detection

    # 分析内容
    target_description = Column(Text, nullable=True)  # 分析对象描述
    findings = Column(JSON, default=list)  # 发现的问题/要点
    conclusions = Column(JSON, default=list)  # 结论
    recommendations = Column(JSON, default=list)  # 建议

    # 证据特有字段
    credibility_score = Column(Float, nullable=True)  # 信度评分
    authenticity_assessment = Column(Text, nullable=True)  # 真实性评估
    reliability_factors = Column(JSON, default=list)  # 可靠性因素
    contradiction_points = Column(JSON, default=list)  # 矛盾点
    trap_indicators = Column(JSON, default=list)  # 陷阱指标

    # 来源
    source_type = Column(String(30), default="ai")  # ai/manual/hybrid
    model_version = Column(String(50), nullable=True)  # AI模型版本
    prompt_version = Column(String(50), nullable=True)  # 提示词版本

    # 质量评估
    confidence_score = Column(Float, nullable=True)  # 置信度
    human_verified = Column(Boolean, default=False)  # 是否经过人工验证
    human_corrections = Column(Text, nullable=True)  # 人工修正内容

    # 元数据
    version = Column(Integer, default=1)  # 版本号
    is_latest = Column(Boolean, default=True)  # 是否最新版本
    previous_version_id = Column(Integer, nullable=True)  # 上一个版本ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    session = relationship("EvidenceAnalysisSession")
    case = relationship("Case")

    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )
