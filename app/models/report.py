"""
报告大纲与章节模型
支持：分段生成、增量更新、结构化存储
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class ReportType(str, enum.Enum):
    """报告类型"""
    ANALYSIS = "ANALYSIS"                    # 案件分析
    STRATEGY = "STRATEGY"                  # 策略建议
    FULL_ANALYSIS = "FULL_ANALYSIS"        # 完整对抗性分析
    EVIDENCE_REPORT = "EVIDENCE_REPORT"     # 证据报告
    MILESTONE_REPORT = "MILESTONE_REPORT"  # 里程碑报告
    OPPONENT_ANALYSIS = "OPPONENT_ANALYSIS"  # 对手分析


class ReportStatus(str, enum.Enum):
    """报告状态"""
    PLANNING = "PLANNING"            # 规划中
    GENERATING = "GENERATING"        # 生成中
    VALIDATING = "VALIDATING"        # 校验中
    COMPLETED = "COMPLETED"         # 已完成
    PARTIAL = "PARTIAL"             # 部分完成
    FAILED = "FAILED"               # 生成失败
    EXPIRED = "EXPIRED"             # 已过期


class SectionStatus(str, enum.Enum):
    """章节状态"""
    PENDING = "pending"         # 待生成
    IN_PROGRESS = "in_progress"  # 生成中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"           # 生成失败
    SKIPPED = "skipped"          # 跳过


class ReportOutline(Base):
    """
    报告大纲
    规划报告的整体结构
    """
    __tablename__ = "report_outlines"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # 基本信息
    report_type = Column(String(30), nullable=False)  # 报告类型
    title = Column(String(500), nullable=True)  # 报告标题
    description = Column(Text, nullable=True)  # 报告描述

    # 生成进度
    total_sections = Column(Integer, default=0)  # 总章节数
    completed_sections = Column(Integer, default=0)  # 已完成章节
    failed_sections = Column(Integer, default=0)  # 失败章节

    # 状态
    status = Column(String(20), default=ReportStatus.PLANNING.value)

    # 大纲结构 (JSON)
    outline_data = Column(JSON, default=dict)  # 完整的大纲结构

    # 元数据
    report_metadata = Column(JSON, default=dict)  # 扩展字段

    # 生成配置
    generation_config = Column(JSON, default=dict)  # 生成配置
    max_tokens_per_section = Column(Integer, default=12000)

    # 统计
    total_tokens = Column(Integer, default=0)  # 总token数
    processing_time = Column(Float, default=0.0)  # 处理时间(秒)

    # 错误信息
    error_message = Column(Text, nullable=True)

    # 版本控制
    version = Column(Integer, default=1)  # 报告版本
    is_current = Column(Boolean, default=True)  # 是否当前版本
    previous_version_id = Column(String(36), nullable=True)

    # 缓存
    cached_content = Column(Text, nullable=True)  # 缓存的完整内容
    cache_expires_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    sections = relationship(
        "ReportSection",
        back_populates="outline",
        cascade="all, delete-orphan",
        order_by="ReportSection.section_index"
    )
    references = relationship(
        "SectionReference",
        back_populates="outline",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_outline_case', 'case_id'),
        Index('idx_outline_type', 'report_type'),
        Index('idx_outline_status', 'status'),
        Index('idx_outline_current', 'is_current'),
    )

    TYPE_INFO = {
        'ANALYSIS': {
            'name': '案件分析',
            'icon': '📊',
            'description': '全面分析案件事实和法律问题',
            'section_count': 7
        },
        'STRATEGY': {
            'name': '策略建议',
            'icon': '🎯',
            'description': '诉讼策略和行动建议',
            'section_count': 5
        },
        'FULL_ANALYSIS': {
            'name': '完整对抗性分析',
            'icon': '⚔️',
            'description': '双方视角的完整对抗性分析',
            'section_count': 8
        },
        'EVIDENCE_REPORT': {
            'name': '证据报告',
            'icon': '📎',
            'description': '证据梳理和分析报告',
            'section_count': 5
        },
        'MILESTONE_REPORT': {
            'name': '里程碑报告',
            'icon': '📅',
            'description': '案件进度和待办事项',
            'section_count': 4
        },
        'OPPONENT_ANALYSIS': {
            'name': '对手分析',
            'icon': '🕵️',
            'description': '对手策略和弱点分析',
            'section_count': 5
        },
    }

    def get_type_info(self) -> dict:
        """获取报告类型信息"""
        return self.TYPE_INFO.get(self.report_type, {})

    def get_progress(self) -> dict:
        """获取生成进度"""
        progress = 0
        if self.total_sections > 0:
            progress = (self.completed_sections / self.total_sections) * 100

        return {
            'total': self.total_sections,
            'completed': self.completed_sections,
            'failed': self.failed_sections,
            'progress': progress,
            'status': self.status
        }

    def is_complete(self) -> bool:
        """是否全部完成"""
        return self.status == ReportStatus.COMPLETED.value and \
               self.completed_sections == self.total_sections

    def to_dict(self) -> dict:
        """转换为字典"""
        type_info = self.get_type_info()
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'case_id': self.case_id,
            'report_type': self.report_type,
            'report_type_name': type_info.get('name', ''),
            'report_type_icon': type_info.get('icon', ''),
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'progress': self.get_progress(),
            'total_tokens': self.total_tokens,
            'processing_time': self.processing_time,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class ReportSection(Base):
    """
    报告章节
    存储每个章节的完整内容
    """
    __tablename__ = "report_sections"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    outline_id = Column(String(36), ForeignKey("report_outlines.id", ondelete="CASCADE"), nullable=False)

    # 章节基本信息
    section_index = Column(Integer, nullable=False)  # 章节顺序
    title = Column(String(500), nullable=False)  # 章节标题
    subtitle = Column(String(500), nullable=True)  # 副标题

    # 内容
    content = Column(Text, nullable=True)  # 完整内容
    summary = Column(Text, nullable=True)  # 章节摘要

    # 要点
    key_points = Column(JSON, default=list)  # 关键要点列表
    main_conclusions = Column(JSON, default=list)  # 主要结论

    # 证据引用
    source_evidence_ids = Column(JSON, default=list)  # 引用的证据ID
    cited_laws = Column(JSON, default=list)  # 引用的法条

    # 生成信息
    generation_prompt = Column(Text, nullable=True)  # 生成时的提示词
    model_response = Column(Text, nullable=True)  # 原始模型响应
    tokens_used = Column(Integer, default=0)  # 使用的token数

    # 状态
    status = Column(String(20), default=SectionStatus.PENDING.value)

    # 评估
    confidence_score = Column(Float, default=0.0)  # 置信度
    completeness_score = Column(Float, default=0.0)  # 完整度

    # 依赖关系
    dependencies = Column(JSON, default=list)  # 依赖的其他章节ID
    dependent_sections = Column(JSON, default=list)  # 依赖本章节的ID

    # 错误处理
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)  # 开始生成时间
    completed_at = Column(DateTime, nullable=True)  # 完成时间

    # 关系
    outline = relationship("ReportOutline", back_populates="sections")

    __table_args__ = (
        Index('idx_section_outline', 'outline_id'),
        Index('idx_section_index', 'section_index'),
        Index('idx_section_status', 'status'),
    )

    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == SectionStatus.COMPLETED.value

    def can_generate(self) -> bool:
        """是否可以生成（依赖是否满足）"""
        if self.status != SectionStatus.PENDING.value:
            return False
        # 检查依赖是否都已完成
        # 这里需要检查依赖章节的状态
        return True

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'outline_id': self.outline_id,
            'section_index': self.section_index,
            'title': self.title,
            'subtitle': self.subtitle,
            'summary': self.summary,
            'key_points': self.key_points,
            'content_preview': (self.content or '')[:200] + '...' if len(self.content or '') > 200 else self.content,
            'content_length': len(self.content or ''),
            'status': self.status,
            'confidence_score': self.confidence_score,
            'completeness_score': self.completeness_score,
            'tokens_used': self.tokens_used,
            'source_evidence_count': len(self.source_evidence_ids or []),
            'cited_laws_count': len(self.cited_laws or []),
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def to_full_dict(self) -> dict:
        """转换为完整字典（包含内容）"""
        result = self.to_dict()
        result['content'] = self.content
        result['generation_prompt'] = self.generation_prompt
        result['main_conclusions'] = self.main_conclusions
        return result


class SectionReference(Base):
    """
    章节间的交叉引用
    """
    __tablename__ = "section_references"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    outline_id = Column(String(36), ForeignKey("report_outlines.id", ondelete="CASCADE"), nullable=False)

    source_section_id = Column(String(36), nullable=False)
    target_section_id = Column(String(36), nullable=False)

    # 引用信息
    reference_type = Column(String(20), default='cross_reference')  # cross_reference/see_also/related
    reference_text = Column(String(500), nullable=True)  # 引用片段
    reference_context = Column(Text, nullable=True)  # 引用上下文

    # 位置
    source_position = Column(JSON, nullable=True)  # {"start": 100, "end": 150}
    target_position = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    outline = relationship("ReportOutline", back_populates="references")

    __table_args__ = (
        Index('idx_ref_outline', 'outline_id'),
        Index('idx_ref_source', 'source_section_id'),
        Index('idx_ref_target', 'target_section_id'),
    )


class ReportCache(Base):
    """
    报告缓存
    缓存已生成的报告，支持快速访问
    """
    __tablename__ = "report_cache"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # 缓存键
    cache_key = Column(String(200), nullable=False, unique=True, index=True)
    report_type = Column(String(30), nullable=False)

    # 缓存内容
    content = Column(Text, nullable=True)
    cache_metadata = Column(JSON, default=dict)

    # 统计
    access_count = Column(Integer, default=0)  # 访问次数
    last_accessed_at = Column(DateTime, nullable=True)

    # 有效期
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # 关联的大纲
    outline_id = Column(String(36), ForeignKey("report_outlines.id", ondelete="SET NULL"), nullable=True)

    def is_expired(self) -> bool:
        """是否过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    __table_args__ = (
        Index('idx_cache_case', 'case_id'),
        Index('idx_cache_type', 'report_type'),
    )
