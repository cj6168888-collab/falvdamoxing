"""
出庭抗辩辅助模型 - 庭审记录、陷阱识别、实时应对
包括：庭审记录、发言识别、陷阱预警、证据使用时机、应对策略
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class HearingType(str, enum.Enum):
    """庭审类型"""
    FIRST_TRIAL = "first_trial"           # 一审
    SECOND_TRIAL = "second_trial"         # 二审
    RETRIAL = "retrial"                   # 再审
    ARBITRATION = "arbitration"           # 仲裁
    MEDIATION = "mediation"               # 调解
    EXECUTION = "execution"               # 执行听证
    OTHER = "other"                       # 其他


class SpeakerRole(str, enum.Enum):
    """讲话方角色"""
    JUDGE = "judge"                       # 法官
    CLERK = "clerk"                       # 书记员
    PLAINTIFF = "plaintiff"               # 原告
    DEFENDANT = "defendant"               # 被告
    PLAINTIFF_LAWYER = "plaintiff_lawyer"  # 原告律师
    DEFENDANT_LAWYER = "defendant_lawyer"  # 被告律师
    THIRD_PARTY = "third_party"           # 第三人
    WITNESS = "witness"                   # 证人
    EXPERT = "expert"                     # 鉴定人
    MEDIATOR = "mediator"                 # 调解员
    PROSECUTOR = "prosecutor"             # 检察官
    OTHER = "other"                       # 其他


class StatementType(str, enum.Enum):
    """陈述类型"""
    QUESTION = "question"                 # 提问
    ANSWER = "answer"                    # 回答
    STATEMENT = "statement"              # 陈述
    OBJECTION = "objection"              # 异议
    ARGUMENT = "argument"                # 辩论
    EVIDENCE_PRESENT = "evidence_present"  # 出示证据
    RULING = "ruling"                    # 裁定/判决


class TrapType(str, enum.Enum):
    """陷阱类型"""
    LEADING_QUESTION = "leading_question"    # 诱导性提问
    FALSE_DILEMMA = "false_dilemma"          # 虚假两难
    STRAW_MAN = "straw_man"                  # 稻草人
    CIRCULAR_REASONING = "circular_reasoning"  # 循环论证
    APPEAL_TO_AUTHORITY = "appeal_to_authority"  # 权威谬误
    EMOTIONAL_MANIPULATION = "emotional_manipulation"  # 情感操控
    BURDEN_OF_PROOF = "burden_of_proof"      # 举证责任转移
    HASTY_GENERALIZATION = "hasty_generalization"  # 草率概括
    RED_HERRING = "red_herring"              # 转移话题
    EQUIVOCATION = "equivocation"             # 偷换概念
    FALSE_CAUSE = "false_cause"               # 虚假因果
    slippery_slope = "slippery_slope"         # 滑坡谬误
    ACCENT = "accent"                         # 强调误导


class EvidenceTiming(str, enum.Enum):
    """证据使用时机"""
    IMMEDIATE = "immediate"               # 立即出示
    WAIT_BETTER_MOMENT = "wait_better_moment"  # 等待更好时机
    SURREBUTTAL = "surrebuttal"         # 反驳阶段出示
    CLOSING_ARGUMENT = "closing_argument"  # 结案陈词出示
    RESERVE_FOR_APPEAL = "reserve_for_appeal"  # 保留待上诉
    NOT_RECOMMENDED = "not_recommended"  # 不建议使用


class ResponseStrategy(str, enum.Enum):
    """应对策略类型"""
    DIRECT_ANSWER = "direct_answer"      # 直接回答
    CLARIFY = "clarify"                  # 要求澄清
    OBJECT = "object"                    # 提出异议
    COUNTER = "counter"                  # 反问反驳
    DEFLECT = "deflect"                  # 转移注意
    INVOKE_RIGHTS = "invoke_rights"      # 援引权利
    STAY_SILENT = "stay_silent"         # 保持沉默


class HearingRecord(Base):
    """
    庭审记录
    记录完整庭审过程，包括发言、时间戳、陷阱识别等
    """
    __tablename__ = "hearing_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 庭审基本信息
    hearing_type = Column(SQLEnum(HearingType), default=HearingType.FIRST_TRIAL)
    hearing_date = Column(DateTime, default=datetime.utcnow)
    location = Column(String(500), nullable=True)  # 庭审地点
    case_number = Column(String(100), nullable=True)  # 案号

    # 庭审状态
    status = Column(String(50), default="preparing")  # preparing/in_progress/paused/closed
    current_phase = Column(String(100), nullable=True)  # 当前阶段
    is_live = Column(Boolean, default=False)  # 是否为实时记录

    # 参会人员
    participants = Column(JSON, nullable=True)  # [{"role": "judge", "name": "张三"}]

    # 完整记录
    full_transcript = Column(Text, nullable=True)  # 完整笔录
    key_points = Column(JSON, nullable=True)  # 关键要点 [{"time": "10:30", "content": "..."}]

    # 分析结果
    traps_detected = Column(JSON, nullable=True)  # 检测到的陷阱
    evidence_timing_suggestions = Column(JSON, nullable=True)  # 证据使用建议
    overall_strategy_evaluation = Column(Text, nullable=True)  # 整体策略评价

    # 实时建议（供移动端使用）
    live_suggestions = Column(JSON, nullable=True)  # 实时建议队列
    current_recommendation = Column(Text, nullable=True)  # 当前推荐

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="hearing_records")
    statements = relationship("HearingStatement", back_populates="record", cascade="all, delete-orphan")
    evidence_uses = relationship("EvidenceUse", back_populates="record", cascade="all, delete-orphan")
    warnings = relationship("HearingWarning", back_populates="record", cascade="all, delete-orphan")


class HearingStatement(Base):
    """
    庭审发言记录
    记录每一条发言的详细内容
    """
    __tablename__ = "hearing_statements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    record_id = Column(Integer, ForeignKey("hearing_records.id", ondelete="CASCADE"), index=True)

    # 发言基本信息
    statement_type = Column(SQLEnum(StatementType), default=StatementType.STATEMENT)
    speaker_role = Column(SQLEnum(SpeakerRole), nullable=False)
    speaker_name = Column(String(200), nullable=True)  # 发言人姓名

    # 时间信息
    timestamp = Column(DateTime, default=datetime.utcnow)  # 发言时间
    sequence = Column(Integer, default=0)  # 发言顺序

    # 内容
    content = Column(Text, nullable=False)  # 发言内容
    original_content = Column(Text, nullable=True)  # 原始内容（保留口音、语气等）

    # AI 分析
    is_trap = Column(Boolean, default=False)  # 是否为陷阱
    trap_type = Column(SQLEnum(TrapType), nullable=True)  # 陷阱类型
    trap_description = Column(Text, nullable=True)  # 陷阱说明
    target_statement_id = Column(Integer, nullable=True)  # 针对的发言ID

    # 应对建议
    suggested_response = Column(Text, nullable=True)  # 建议的应对方式
    response_strategy = Column(SQLEnum(ResponseStrategy), nullable=True)

    # 关联证据
    related_evidence_ids = Column(JSON, nullable=True)  # 涉及的证据ID

    # 情绪分析
    emotional_tone = Column(String(50), nullable=True)  # 情绪基调
    is_hostile = Column(Boolean, default=False)  # 是否具有敌意

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    record = relationship("HearingRecord", back_populates="statements")


class EvidenceUse(Base):
    """
    证据使用记录
    追踪每个证据在庭审中的使用时机和效果
    """
    __tablename__ = "evidence_uses"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    record_id = Column(Integer, ForeignKey("hearing_records.id", ondelete="CASCADE"), index=True)

    # 证据信息
    evidence_name = Column(String(500), nullable=False)  # 证据名称
    evidence_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    presented_by = Column(SQLEnum(SpeakerRole), nullable=False)  # 出示方

    # 使用时机
    timing = Column(SQLEnum(EvidenceTiming), default=EvidenceTiming.WAIT_BETTER_MOMENT)
    suggested_timing = Column(Text, nullable=True)  # 建议的使用时机
    actual_timing = Column(DateTime, default=datetime.utcnow)  # 实际使用时间
    reason_for_timing = Column(Text, nullable=True)  # 选择该时机的理由

    # 使用效果评估
    impact_score = Column(Float, nullable=True)  # 影响分数 0-10
    was_effective = Column(Boolean, nullable=True)  # 是否有效
    effect_description = Column(Text, nullable=True)  # 效果描述

    # 使用背景
    context = Column(Text, nullable=True)  # 出示时的上下文
    opposing_reaction = Column(Text, nullable=True)  # 对方反应
    judge_reaction = Column(Text, nullable=True)  # 法官反应

    # AI 建议
    ai_analysis = Column(Text, nullable=True)  # AI 分析
    improvement_suggestions = Column(Text, nullable=True)  # 改进建议

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    record = relationship("HearingRecord", back_populates="evidence_uses")


class HearingWarning(Base):
    """
    庭审预警
    记录各种预警信息
    """
    __tablename__ = "hearing_warnings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    record_id = Column(Integer, ForeignKey("hearing_records.id", ondelete="CASCADE"), index=True)

    # 预警信息
    warning_type = Column(String(50), nullable=False)  # warning/danger/tip/success
    category = Column(String(100), nullable=False)  # trap/evidence/timing/forbidden/success

    # 内容
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # 详细信息

    # 相关发言
    related_statement_id = Column(Integer, nullable=True)
    related_evidence_id = Column(Integer, nullable=True)

    # 紧急程度
    urgency = Column(String(20), default="medium")  # critical/high/medium/low
    auto_dismiss = Column(Boolean, default=True)  # 是否自动消失
    dismiss_after_seconds = Column(Integer, default=30)  # 多少秒后消失

    # 状态
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    record = relationship("HearingRecord", back_populates="warnings")


class SpeakingGuide(Base):
    """
    说话指南
    针对不同场景提供说话指导
    """
    __tablename__ = "speaking_guides"

    id = Column(Integer, primary_key=True, index=True)

    # 指南基本信息
    title = Column(String(500), nullable=False)  # 如"如何回应诱导性提问"
    category = Column(String(100), nullable=False)  # 分类

    # 适用场景
    applicable_situations = Column(JSON, nullable=True)  # 适用场景列表
    speaker_roles = Column(JSON, nullable=True)  # 针对的讲话方角色

    # 内容
    description = Column(Text, nullable=True)  # 场景描述
    what_to_say = Column(Text, nullable=True)  # 建议说什么
    what_not_to_say = Column(Text, nullable=True)  # 绝对不要说什么
    key_points = Column(JSON, nullable=True)  # 关键要点

    # 模板
    templates = Column(JSON, nullable=True)  # 模板话术

    # 效果说明
    expected_effect = Column(Text, nullable=True)  # 预期效果
    risks = Column(Text, nullable=True)  # 风险提示

    # 激活状态
    is_active = Column(Boolean, default=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CaseSpeakingStrategy(Base):
    """
    案件专属说话策略
    根据具体案件生成的定制化策略
    """
    __tablename__ = "case_speaking_strategies"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 策略基本信息
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # 策略内容
    opening_statement = Column(Text, nullable=True)  # 开场陈述
    key_arguments = Column(JSON, nullable=True)  # 核心论点
    evidence_presentation_order = Column(JSON, nullable=True)  # 证据出示顺序
    anticipated_opposing_arguments = Column(JSON, nullable=True)  # 预判对方论点
    responses_to_opposing_arguments = Column(JSON, nullable=True)  # 应对方案

    # 禁忌事项
    forbidden_statements = Column(JSON, nullable=True)  # 禁止事项
    risky_statements = Column(JSON, nullable=True)  # 风险事项

    # 时机把握
    timing_guidance = Column(JSON, nullable=True)  # 时机指导
    phase_strategies = Column(JSON, nullable=True)  # 各阶段策略

    # 状态
    is_approved = Column(Boolean, default=False)  # 是否已审批
    version = Column(String(20), default="1.0")

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="speaking_strategies")
