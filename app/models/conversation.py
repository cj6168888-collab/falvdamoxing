"""
对话会话管理模型
支持：意图识别、澄清机制、多轮对话、上下文追踪
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class ConversationType(str, enum.Enum):
    """对话类型"""
    QA = "qa"                      # 问答
    ANALYSIS = "analysis"          # 分析
    CLARIFICATION = "clarification" # 澄清
    STRATEGY = "strategy"          # 策略咨询
    DOCUMENT = "document"          # 文书相关


class ConversationStatus(str, enum.Enum):
    """会话状态"""
    ACTIVE = "active"              # 进行中
    COMPLETED = "completed"        # 已完成
    ARCHIVED = "archived"          # 已归档
    EXPIRED = "expired"            # 已过期


class QuestionIntent(str, enum.Enum):
    """问题意图"""
    FACT_QUERY = "FACT_QUERY"                  # 事实查询
    LEGAL_ADVICE = "LEGAL_ADVICE"              # 法律建议
    EVIDENCE_ADVICE = "EVIDENCE_ADVICE"        # 证据建议
    STRATEGY_ADVICE = "STRATEGY_ADVICE"        # 策略建议
    DOCUMENT_GENERATION = "DOCUMENT_GENERATION" # 文书草稿
    RISK_ASSESSMENT = "RISK_ASSESSMENT"         # 风险评估
    CASE_STATUS = "CASE_STATUS"                 # 案件状态


class ClarificationDimension(str, enum.Enum):
    """澄清维度"""
    WHO = "WHO"      # 谁涉及
    WHEN = "WHEN"    # 时间
    WHAT = "WHAT"    # 具体事项
    WHERE = "WHERE"  # 地点
    WHY = "WHY"      # 原因目的
    HOW = "HOW"      # 过程
    EVIDENCE = "EVIDENCE"  # 证据


class ClarificationStatus(str, enum.Enum):
    """澄清状态"""
    PENDING = "pending"      # 待澄清
    RESOLVED = "resolved"    # 已澄清
    DECLINED = "declined"    # 拒绝回答
    DEFERRED = "deferred"    # 延后处理


class ConversationSession(Base):
    """
    对话会话
    管理一个完整的多轮对话上下文
    """
    __tablename__ = "conversation_sessions"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # 会话基本信息
    session_type = Column(String(30), default=ConversationType.QA.value)
    title = Column(String(200), nullable=True)  # 自动生成或用户设置
    description = Column(Text, nullable=True)

    # 状态
    status = Column(String(20), default=ConversationStatus.ACTIVE.value)
    is_pinned = Column(Boolean, default=False)  # 是否置顶

    # 上下文摘要
    context_summary = Column(Text, nullable=True)  # AI生成的上下文摘要
    key_entities = Column(JSON, default=dict)  # 提取的关键实体

    # 意图识别
    primary_intent = Column(String(30), nullable=True)  # 主要意图
    intent_confidence = Column(Float, default=0.0)  # 意图置信度

    # 清晰度评估
    overall_clarity = Column(Float, default=0.0)  # 综合清晰度 0-1
    clarity_dimensions = Column(JSON, default=dict)  # 各维度清晰度

    # 对话轮次
    message_count = Column(Integer, default=0)  # 消息数量
    clarification_count = Column(Integer, default=0)  # 澄清轮次

    # 最终结果
    final_answer = Column(Text, nullable=True)  # 最终回答
    answer_type = Column(String(20), nullable=True)  # DIRECT/PARTIAL/GUIDED
    confidence = Column(Float, default=0.0)  # 答案置信度

    # 证据相关
    referenced_evidence_ids = Column(JSON, default=list)  # 引用的证据ID
    suggested_evidence_ids = Column(JSON, default=list)  # 建议补充的证据ID
    evidence_gaps = Column(JSON, default=list)  # 证据缺口

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)  # 最后消息时间
    expires_at = Column(DateTime, nullable=True)  # 过期时间

    # 关系
    messages = relationship(
        "ConversationMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at"
    )
    clarifications = relationship(
        "ClarificationRecord",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    analyses = relationship(
        "QuestionAnalysis",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_session_case', 'case_id'),
        Index('idx_session_status', 'status'),
        Index('idx_session_type', 'session_type'),
        Index('idx_session_updated', 'updated_at'),
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'case_id': self.case_id,
            'session_type': self.session_type,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'context_summary': self.context_summary,
            'key_entities': self.key_entities,
            'primary_intent': self.primary_intent,
            'intent_confidence': self.intent_confidence,
            'overall_clarity': self.overall_clarity,
            'message_count': self.message_count,
            'clarification_count': self.clarification_count,
            'answer_type': self.answer_type,
            'confidence': self.confidence,
            'referenced_evidence_ids': self.referenced_evidence_ids,
            'suggested_evidence_ids': self.suggested_evidence_ids,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
        }


class ConversationMessage(Base):
    """
    对话消息
    存储会话中的每条消息
    """
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    session_id = Column(String(36), ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False)

    # 消息角色
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_SYSTEM = "system"

    role = Column(String(20), nullable=False)  # user/assistant/system
    content = Column(Text, nullable=False)

    # 消息类型
    message_type = Column(String(30), default='text')  # text/clarification/answer/evidence_suggestion

    # 相关实体
    entities = Column(JSON, default=dict)  # 本条消息提取的实体
    intent = Column(String(30), nullable=True)  # 本条消息的意图

    # 引用
    referenced_evidence_ids = Column(JSON, default=list)  # 引用的证据
    cited_sources = Column(JSON, default=list)  # 引用的法条/案例

    # 评估
    is_satisfactory = Column(Boolean, nullable=True)  # 用户是否满意
    feedback = Column(Text, nullable=True)  # 用户反馈

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    session = relationship("ConversationSession", back_populates="messages")

    __table_args__ = (
        Index('idx_msg_session', 'session_id'),
        Index('idx_msg_role', 'role'),
        Index('idx_msg_created', 'created_at'),
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'message_type': self.message_type,
            'entities': self.entities,
            'intent': self.intent,
            'referenced_evidence_ids': self.referenced_evidence_ids,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ClarificationRecord(Base):
    """
    澄清记录
    记录需要澄清的问题及其回答
    """
    __tablename__ = "clarification_records"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    session_id = Column(String(36), ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False)

    # 澄清的问题
    original_question = Column(Text, nullable=False)  # 原始问题
    dimension = Column(String(20), nullable=True)  # 澄清维度 WHO/WHEN/WHAT...
    priority = Column(String(20), default='normal')  # critical/important/normal
    reason = Column(Text, nullable=True)  # 为什么需要澄清

    # 澄清问题（可能有多条建议）
    clarifying_questions = Column(JSON, default=list)  # [{"question": "...", "reason": "..."}]
    selected_question = Column(Text, nullable=True)  # 用户看到的问题

    # 澄清结果
    status = Column(String(20), default=ClarificationStatus.PENDING.value)
    user_answer = Column(Text, nullable=True)  # 用户回答
    resolved_at = Column(DateTime, nullable=True)

    # 关联性
    affects_answer = Column(Boolean, default=True)  # 是否影响最终答案
    impact_on_clarity = Column(Float, default=0.0)  # 对清晰度的提升

    # 来源
    is_auto_generated = Column(Boolean, default=True)  # 是否自动生成

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    session = relationship("ConversationSession", back_populates="clarifications")

    __table_args__ = (
        Index('idx_clar_session', 'session_id'),
        Index('idx_clar_status', 'status'),
        Index('idx_clar_dimension', 'dimension'),
    )

    DIMENSION_INFO = {
        'WHO': {'name': '当事人', 'description': '涉及哪些人', 'icon': '👤'},
        'WHEN': {'name': '时间', 'description': '关键时间节点', 'icon': '📅'},
        'WHAT': {'name': '事实', 'description': '具体发生了什么', 'icon': '❓'},
        'WHERE': {'name': '地点', 'description': '地点和管辖', 'icon': '📍'},
        'WHY': {'name': '目的', 'description': '动机和目的', 'icon': '🎯'},
        'HOW': {'name': '过程', 'description': '事情经过', 'icon': '📋'},
        'EVIDENCE': {'name': '证据', 'description': '有哪些证据材料', 'icon': '📎'},
    }

    def get_dimension_info(self) -> dict:
        """获取维度信息"""
        return self.DIMENSION_INFO.get(self.dimension, {})

    def to_dict(self) -> dict:
        """转换为字典"""
        dim_info = self.get_dimension_info()
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'session_id': self.session_id,
            'original_question': self.original_question,
            'dimension': self.dimension,
            'dimension_name': dim_info.get('name', ''),
            'dimension_icon': dim_info.get('icon', ''),
            'priority': self.priority,
            'reason': self.reason,
            'clarifying_questions': self.clarifying_questions,
            'selected_question': self.selected_question,
            'status': self.status,
            'user_answer': self.user_answer,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'affects_answer': self.affects_answer,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class QuestionAnalysis(Base):
    """
    问题分析结果
    存储问题理解和意图识别的结果
    """
    __tablename__ = "question_analyses"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    session_id = Column(String(36), ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False)

    # 原始问题
    original_question = Column(Text, nullable=False)
    question_hash = Column(String(64), nullable=True, index=True)  # 问题哈希，用于查重

    # 分析结果 - 意图
    intent = Column(String(30), nullable=True)
    intent_confidence = Column(Float, default=0.0)
    intent_reasoning = Column(Text, nullable=True)

    # 分析结果 - 实体
    entities = Column(JSON, default=dict)  # {"parties": [], "dates": [], "amounts": []}
    relation_graph = Column(JSON, default=list)  # 实体关系图
    ambiguous_entities = Column(JSON, default=list)  # 模糊实体

    # 分析结果 - 清晰度
    clarity_score = Column(Float, default=0.0)  # 综合清晰度 0-1
    dimension_scores = Column(JSON, default=dict)  # 各维度清晰度
    clarity_reasoning = Column(Text, nullable=True)  # 清晰度评估理由

    # 澄清需求
    clarification_needed = Column(Boolean, default=False)
    clarification_dimensions = Column(JSON, default=list)  # 需要澄清的维度
    clarifying_questions = Column(JSON, default=list)  # 生成的澄清问题

    # 回答策略
    answer_type = Column(String(20), nullable=True)  # DIRECT/PARTIAL/GUIDED
    answer_strategy = Column(Text, nullable=True)  # 回答策略说明

    # 证据相关
    key_points_covered = Column(JSON, default=list)  # 回答覆盖的要点
    evidence_gaps = Column(JSON, default=list)  # 证据缺口
    suggested_evidence = Column(JSON, default=list)  # 建议补充的证据

    # 最终结果
    confidence = Column(Float, default=0.0)  # 整体置信度
    quality_score = Column(Float, default=0.0)  # 回答质量评分

    # 元数据
    processing_time = Column(Float, default=0.0)  # 处理时间(秒)
    model_used = Column(String(50), nullable=True)  # 使用的模型

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    session = relationship("ConversationSession", back_populates="analyses")

    __table_args__ = (
        Index('idx_analysis_session', 'session_id'),
        Index('idx_analysis_intent', 'intent'),
        Index('idx_analysis_hash', 'question_hash'),
    )

    # 意图信息
    INTENT_INFO = {
        'FACT_QUERY': {'name': '事实查询', 'icon': '🔍', 'color': '#1890ff'},
        'LEGAL_ADVICE': {'name': '法律建议', 'icon': '⚖️', 'color': '#52c41a'},
        'EVIDENCE_ADVICE': {'name': '证据建议', 'icon': '📎', 'color': '#faad14'},
        'STRATEGY_ADVICE': {'name': '策略建议', 'icon': '🎯', 'color': '#722ed1'},
        'DOCUMENT_GENERATION': {'name': '文书草稿', 'icon': '📝', 'color': '#eb2f96'},
        'RISK_ASSESSMENT': {'name': '风险评估', 'icon': '⚠️', 'color': '#f5222d'},
        'CASE_STATUS': {'name': '案件状态', 'icon': '📋', 'color': '#13c2c2'},
    }

    def get_intent_info(self) -> dict:
        """获取意图信息"""
        return self.INTENT_INFO.get(self.intent, {})

    def to_dict(self) -> dict:
        """转换为字典"""
        intent_info = self.get_intent_info()
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'session_id': self.session_id,
            'original_question': self.original_question,
            'intent': self.intent,
            'intent_name': intent_info.get('name', ''),
            'intent_icon': intent_info.get('icon', ''),
            'intent_confidence': self.intent_confidence,
            'clarity_score': self.clarity_score,
            'clarification_needed': self.clarification_needed,
            'clarification_dimensions': self.clarification_dimensions,
            'clarifying_questions': self.clarifying_questions,
            'answer_type': self.answer_type,
            'entities': self.entities,
            'evidence_gaps': self.evidence_gaps,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
