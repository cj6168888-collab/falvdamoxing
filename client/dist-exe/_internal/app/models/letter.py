"""
函件模型 - 精准把控函件往来时间
包括：律师函、催告函、回复期限、是否需要回复等
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class LetterDirection(str, enum.Enum):
    """函件方向"""
    INCOMING = "incoming"      # 收件（收到对方函件）
    OUTGOING = "outgoing"      # 发件（我方发出的函件）


class LetterType(str, enum.Enum):
    """函件类型"""
    LAWYER_LETTER = "lawyer_letter"           # 律师函
    DEMAND_LETTER = "demand_letter"            # 催告函/催款函
    NOTICE = "notice"                          # 通知书
    RESPONSE = "response"                       # 回复函
    REMINDER = "reminder"                       # 提醒函
    WARNING = "warning"                         # 警告函
    NEGOTIATION = "negotiation"                 # 协商函
    EXPLANATION = "explanation"                 # 说明函
    OTHER = "other"                             # 其他


class ReplyRequirement(str, enum.Enum):
    """回复要求"""
    REQUIRED = "required"              # 必须回复
    RECOMMENDED = "recommended"         # 建议回复
    OPTIONAL = "optional"               # 可选回复
    NOT_REQUIRED = "not_required"       # 不需要回复
    DEADLINE_PASSED = "deadline_passed"  # 已超期


class UrgentLevel(str, enum.Enum):
    """紧急程度"""
    CRITICAL = "critical"    # 紧急（需立即处理）
    HIGH = "high"            # 高（需当日处理）
    MEDIUM = "medium"        # 中（3日内处理）
    LOW = "low"              # 低（7日内处理）
    NONE = "none"            # 无期限


class Letter(Base):
    """
    函件模型 - 精准追踪每一封函件及回复期限
    支持：文书生成、邮寄跟踪、回函管理全流程
    """
    __tablename__ = "letters"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 函件基本信息
    direction = Column(SQLEnum(LetterDirection), nullable=False)  # 收发方向
    letter_type = Column(SQLEnum(LetterType), default=LetterType.OTHER)  # 类型

    # 函件标识
    title = Column(String(500), nullable=False)  # 函件标题
    reference_number = Column(String(100), nullable=True)  # 文号/编号
    sender = Column(String(200), nullable=True)  # 发送方
    recipient = Column(String(200), nullable=True)  # 接收方

    # 日期信息
    letter_date = Column(DateTime, nullable=True)  # 函件日期（落款日期）
    received_date = Column(DateTime, nullable=True)  # 收到日期
    deadline = Column(DateTime, nullable=True)  # 回复截止日期
    responded_date = Column(DateTime, nullable=True)  # 回复日期

    # 回复要求分析
    reply_required = Column(SQLEnum(ReplyRequirement), default=ReplyRequirement.OPTIONAL)  # 是否需要回复
    reply_requirement_reason = Column(Text, nullable=True)  # 回复要求的原因说明
    response_deadline_days = Column(Integer, nullable=True)  # 法定期限天数
    legal_basis = Column(Text, nullable=True)  # 法律依据

    # 紧急程度
    urgent_level = Column(SQLEnum(UrgentLevel), default=UrgentLevel.NONE)
    is_overdue = Column(Boolean, default=False)  # 是否已超期
    days_until_deadline = Column(Integer, nullable=True)  # 距截止日期天数

    # 内容摘要
    content_summary = Column(Text, nullable=True)  # 内容摘要
    key_demands = Column(Text, nullable=True)  # 核心诉求
    risks = Column(Text, nullable=True)  # 风险提示

    # 回复状态
    is_replied = Column(Boolean, default=False)  # 是否已回复
    reply_content = Column(Text, nullable=True)  # 回复内容摘要
    reply_approved = Column(Boolean, nullable=True)  # 回复是否已审批
    draft_reply = Column(Text, nullable=True)  # 回复草稿

    # ============ 新增：邮寄跟踪 ============
    # 邮寄状态
    mail_status = Column(String(50), default="draft")  # draft/draft_confirmed/sending/sent/delivered/read/replied
    mail_sent_date = Column(DateTime, nullable=True)  # 实际邮寄日期
    mail_delivered_date = Column(DateTime, nullable=True)  # 送达日期

    # 运单信息
    tracking_number = Column(String(200), nullable=True)  # 运单号
    courier_company = Column(String(100), nullable=True)  # 快递公司

    # 邮寄目的
    mailing_purpose = Column(Text, nullable=True)  # 邮寄目的说明

    # 回执上传
    proof_of_delivery = Column(JSON, nullable=True)  # 送达证明 [{"file": "...", "upload_date": "...", "type": "签收单/运单截图"}]
    signature_image = Column(String(500), nullable=True)  # 签收回执图片路径

    # 对方回函
    has_reply = Column(Boolean, default=False)  # 是否收到回函
    reply_type = Column(String(50), nullable=True)  # 回函类型：accept/reject/counter/procedural/other
    reply_summary = Column(Text, nullable=True)  # 回函内容摘要
    reply_document = Column(JSON, nullable=True)  # 回函文档 [{"name": "...", "path": "..."}]

    # AI分析
    reply_analysis = Column(Text, nullable=True)  # AI对回函的分析

    # ============ 关联 ============
    related_letter_id = Column(Integer, ForeignKey("letters.id"), nullable=True)  # 关联的函件（如：回复对应的原函）
    related_document_id = Column(Integer, nullable=True)  # 关联生成的文书ID
    related_evidence_ids = Column(JSON, nullable=True)  # 关联的证据ID列表

    # 附件
    attachments = Column(JSON, nullable=True)  # 附件列表 [{"name": "...", "path": "..."}]

    # AI生成前的沟通记录
    generation_notes = Column(Text, nullable=True)  # 生成前的备注（如：哪个证据先不放、哪个主张先不提）

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="letters")
    parent_letter = relationship("Letter", remote_side=[id], backref="replies")


class LegalDeadline(Base):
    """
    法律期限记录 - 精确记录各类法定期限
    包括：诉讼时效、举证期限、上诉期限、执行申请期限等
    """
    __tablename__ = "legal_deadlines"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 期限类型
    deadline_type = Column(String(100), nullable=False)  # 期限类型标识
    deadline_name = Column(String(500), nullable=False)  # 期限名称
    deadline_category = Column(String(50), nullable=True)  # 分类：时效/举证/上诉/执行等

    # 期限详情
    legal_basis = Column(Text, nullable=True)  # 法律依据
    duration_days = Column(Integer, nullable=True)  # 法定期限天数
    description = Column(Text, nullable=True)  # 期限说明

    # 关键日期
    start_date = Column(DateTime, nullable=True)  # 起算日期
    deadline_date = Column(DateTime, nullable=True)  # 截止日期
    extended_deadline = Column(DateTime, nullable=True)  # 展期后日期（如有）

    # 状态
    status = Column(String(50), default="pending")  # pending/active/expired/completed/suspended
    is_mandatory = Column(Boolean, default=True)  # 是否为强制性期限
    can_extend = Column(Boolean, default=False)  # 是否可以申请展期
    extension_days = Column(Integer, nullable=True)  # 已获准展期天数

    # 关联
    related_event = Column(String(200), nullable=True)  # 关联事件
    related_document_id = Column(Integer, nullable=True)  # 关联文档ID

    # AI分析
    ai_suggestions = Column(Text, nullable=True)  # AI建议
    risk_warning = Column(Text, nullable=True)  # 风险提示
    completion_checklist = Column(JSON, nullable=True)  # 完成清单

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="legal_deadlines")


class MilestoneTemplate(Base):
    """
    里程碑模板 - 预定义各类案件的标准化流程节点
    """
    __tablename__ = "milestone_templates"

    id = Column(Integer, primary_key=True, index=True)

    # 模板信息
    name = Column(String(200), nullable=False)  # 模板名称
    description = Column(Text, nullable=True)  # 模板描述
    case_type = Column(String(50), nullable=True)  # 适用案件类型

    # 里程碑定义（JSON存储）
    milestones = Column(JSON, nullable=False)  # 里程碑列表

    # 元数据
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CaseTimeline(Base):
    """
    案件时间线 - 完整记录案件全生命周期的时间节点
    """
    __tablename__ = "case_timelines"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 事件信息
    event_type = Column(String(100), nullable=False)  # 事件类型
    event_name = Column(String(500), nullable=False)  # 事件名称
    event_date = Column(DateTime, nullable=False)  # 事件日期
    event_description = Column(Text, nullable=True)  # 事件描述

    # 关联
    related_deadline_id = Column(Integer, ForeignKey("legal_deadlines.id"), nullable=True)  # 关联期限
    related_letter_id = Column(Integer, ForeignKey("letters.id"), nullable=True)  # 关联函件
    related_document_id = Column(Integer, nullable=True)  # 关联文档
    related_milestone_id = Column(Integer, nullable=True)  # 关联里程碑
    related_evidence_ids = Column(JSON, nullable=True)  # 关联的证据ID列表

    # 重要性
    importance = Column(String(20), default="normal")  # critical/important/normal/minor
    is_milestone = Column(Boolean, default=False)  # 是否为里程碑事件

    # AI生成
    ai_summary = Column(Text, nullable=True)  # AI总结

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="case_timelines")
