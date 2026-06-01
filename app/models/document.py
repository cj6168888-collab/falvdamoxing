from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class Document(Base):
    """文档模型 - 上传的证据文件"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    filename = Column(String(500), nullable=False)  # 原始文件名
    stored_path = Column(String(1000), nullable=False)  # 存储路径
    file_type = Column(String(50), nullable=True)  # 文件类型 (pdf, docx, txt, image)
    file_size = Column(Integer, nullable=True)  # 文件大小

    # 内容提取
    content = Column(Text, nullable=True)  # 提取的文本内容
    content_summary = Column(Text, nullable=True)  # 内容摘要

    # 向量索引
    vector_id = Column(String(200), nullable=True)  # Chroma 中的 ID
    is_indexed = Column(Integer, default=0)  # 是否已索引

    # 元数据
    doc_type = Column(String(100), nullable=True)  # 文档类型 (合同/证据/判决书等)
    tags = Column(Text, nullable=True)  # 标签，JSON 字符串
    created_by = Column(String(200), nullable=True)  # 创建者
    uploaded_by = Column(String(200), nullable=True)  # 上传者
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ========== 逻辑闭环新增：关联追踪 ==========
    # 关联的回函（如果此文档是对对方来函的回复）
    related_letter_id = Column(Integer, ForeignKey("letters.id"), nullable=True)
    # 关联的生成文书
    related_generated_doc_id = Column(Integer, nullable=True)

    # 关系
    case = relationship("Case", back_populates="documents")
    related_letter = relationship("Letter", foreign_keys=[related_letter_id])


class DocumentTemplate(Base):
    """文书模板"""
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # 模板名称
    template_type = Column(String(100), nullable=False)  # 模板类型
    content = Column(Text, nullable=False)  # 模板内容
    description = Column(Text, nullable=True)  # 模板说明
    variables = Column(Text, nullable=True)  # 变量列表，JSON 字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GeneratedDocument(Base):
    """
    生成的法律文书 - 逻辑闭环核心
    记录系统生成的法律文书，支持关联证据和函件
    """
    __tablename__ = "generated_documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 文书基本信息
    title = Column(String(500), nullable=False)  # 文书标题（如"民事起诉状-2024-001"）
    document_type = Column(String(100), nullable=False)  # 文书类型：起诉状/答辩状/律师函等
    content = Column(Text, nullable=False)  # 文书完整内容

    # 关联追踪（逻辑闭环核心）
    related_letter_id = Column(Integer, ForeignKey("letters.id"), nullable=True)  # 对应的函件（如：催告函的回复）
    related_evidence_ids = Column(JSON, nullable=True)  # 引用的证据ID列表
    referenced_evidence = Column(JSON, nullable=True)  # 引用的具体证据内容摘要
    # 反向关联：此文书关联了哪些文档
    related_document_ids = Column(JSON, nullable=True)

    # ==================== 战役关联 ====================
    claim_id = Column(Integer, ForeignKey("case_claims.id", ondelete="SET NULL"), nullable=True, comment="关联的战役ID")
    campaign_goal = Column(String(500), nullable=True, comment="战役目标描述")
    used_evidence_ids = Column(JSON, default=list, comment="本次文书使用的证据ID列表")

    # 对抗性分析引用
    based_on_adversarial_analysis = Column(Boolean, default=False)  # 是否基于对抗性分析生成
    adversarial_analysis_id = Column(Integer, nullable=True)  # 关联的对抗性分析ID
    adversarial_references = Column(Text, nullable=True)  # 引用的对抗性分析内容摘要

    # AI分析引用
    based_on_ai_analysis = Column(Boolean, default=False)  # 是否基于AI分析生成
    ai_analysis_summary = Column(Text, nullable=True)  # 基于的AI分析摘要

    # 策略来源
    generation_context = Column(Text, nullable=True)  # 生成时的特殊要求摘要
    strategy_notes = Column(Text, nullable=True)  # 策略备注（如：暂不提违约金主张）

    # 版本控制
    version = Column(Integer, default=1)  # 版本号
    parent_doc_id = Column(Integer, ForeignKey("generated_documents.id"), nullable=True)  # 上一版本ID（用于版本追踪）
    change_summary = Column(Text, nullable=True)  # 版本变更说明

    # 文书修改历史（记忆功能）
    modification_history = Column(Text, nullable=True)  # 修改历史记录 [{"feedback": "用户修改意见", "timestamp": "时间", "version": 版本号}, ...]

    # 状态
    status = Column(String(50), default="draft")  # draft（草稿）/approved（已审批）/sent（已发送）/archived（归档）
    is_current = Column(Boolean, default=True)  # 是否为当前版本

    # 回函追踪
    is_response_to_letter = Column(Boolean, default=False)  # 是否是对某函件的回复
    response_letter_id = Column(Integer, nullable=True)  # 回复的函件ID

    # 邮寄追踪
    mail_status = Column(String(50), default="not_sent")  # not_sent/sent/delivered
    mail_sent_date = Column(DateTime, nullable=True)
    tracking_number = Column(String(200), nullable=True)  # 运单号

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(200), nullable=True)  # 创建者（支持多用户场景）

    # 关系
    case = relationship("Case", back_populates="generated_documents")
    related_letter = relationship("Letter", foreign_keys=[related_letter_id])
    parent_document = relationship("GeneratedDocument", remote_side=[id], foreign_keys=[parent_doc_id])
    claim = relationship("CaseClaim", back_populates="documents")


class DocumentExportReviewAudit(Base):
    """Audit trail for document export review checklist confirmations."""

    __tablename__ = "document_export_review_audits"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    user_id = Column(String(200), index=True, nullable=True)
    case_id = Column(Integer, index=True, nullable=True)
    generated_document_id = Column(Integer, ForeignKey("generated_documents.id", ondelete="SET NULL"), index=True, nullable=True)
    document_title = Column(String(500), nullable=True)
    document_type = Column(String(100), nullable=True)
    export_action = Column(String(50), index=True, nullable=False)
    export_format = Column(String(30), index=True, nullable=False)
    checked_items = Column(JSON, nullable=False, default=list)
    checked_item_count = Column(Integer, nullable=False, default=0)
    confirmed_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    generated_document = relationship("GeneratedDocument", foreign_keys=[generated_document_id])


class DocumentSuggestion(Base):
    """
    文书生成建议 - 逻辑闭环
    基于AI分析自动生成文书建议，并追踪生成状态
    """
    __tablename__ = "document_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 文书信息
    doc_type = Column(String(100), nullable=False)  # 文书类型
    doc_name = Column(String(200), nullable=True)  # 文书名称（如"催告函-2024-001"）
    description = Column(Text, nullable=True)  # 文书描述

    # 建议来源
    source = Column(String(50), nullable=False)  # ai_analysis（AI分析）/ adversarial（对抗性分析）/ manual（手动）
    source_detail = Column(Text, nullable=True)  # 来源详情（如：从legal_analysis第3段提取）

    # 优先级和原因
    priority = Column(String(20), default="中")  # 高/中/低
    ai_reason = Column(Text, nullable=True)  # AI建议生成此文的理由
    legal_basis = Column(Text, nullable=True)  # 相关法律依据

    # 关联（逻辑闭环核心）
    suggested_evidence_ids = Column(JSON, nullable=True)  # 建议引用的证据ID
    suggested_letter_id = Column(Integer, nullable=True)  # 关联的函件（如：收到催告函后建议生成律师函）
    related_adversarial_analysis = Column(Text, nullable=True)  # 关联的对抗性分析内容

    # 状态追踪
    status = Column(String(20), default="pending")  # pending（待生成）/generated（已生成）/cancelled（已取消）/superseded（已被替代）
    generated_doc_id = Column(Integer, nullable=True)  # 已生成的文书ID
    cancelled_reason = Column(Text, nullable=True)  # 取消原因

    # 关联的AI分析
    based_on_analysis_at = Column(DateTime, nullable=True)  # 基于哪个时间点的分析
    analysis_snapshot = Column(Text, nullable=True)  # 分析快照（当时分析结果的摘要）

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order = Column(Integer, default=0)  # 显示顺序

    # 关系
    case = relationship("Case", back_populates="document_suggestions")
