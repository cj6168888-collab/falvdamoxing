"""
证据系统 V2 数据模型
支持：智能分类、信度评估、关系分析、去重检查、关键词索引
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import hashlib
import re

from app.db.database import Base


class EvidenceSourceType(str, enum.Enum):
    """证据来源类型"""
    FILE = "file"           # 文件上传
    TEXT = "text"           # 文本粘贴
    INPUT = "input"         # 结构化录入


class EvidenceType(str, enum.Enum):
    """证据类型"""
    CONTRACT = "CONTRACT"           # 合同协议类
    CORRESPONDENCE = "CORRESPONDENCE"  # 函件沟通类
    PAYMENT = "PAYMENT"             # 支付凭证类
    IDENTITY = "IDENTITY"           # 身份证明类
    AUDIO_VIDEO = "AUDIO_VIDEO"     # 视听资料类
    TESTIMONY = "TESTIMONY"         # 证人证言类
    EXPERT = "EXPERT"              # 鉴定意见类
    DOCUMENT = "DOCUMENT"           # 书证类
    MATERIAL = "MATERIAL"          # 物证类
    OTHER = "OTHER"                # 其他类


class EvidenceSourceParty(str, enum.Enum):
    """证据来源方"""
    OUR_SIDE = "己方"           # 己方提供
    THEIR_SIDE = "对方"         # 对方提供
    THIRD_PARTY = "第三方"      # 第三方提供
    COURT = "法院"              # 法院调取


class EvidenceStatus(str, enum.Enum):
    """证据状态"""
    PENDING = "待处理"          # 待处理
    PROCESSING = "处理中"       # 处理中
    PROCESSED = "已处理"        # 已处理
    INDEXED = "已索引"          # 已索引
    ARCHIVED = "已归档"         # 已归档


class EvidenceItem(Base):
    """
    证据项
    核心证据数据模型，支持完整的证据生命周期管理
    """
    __tablename__ = "evidence_items_v2"

    id = Column(String(36), primary_key=True)  # UUID
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # ==================== 来源信息 ====================
    source_type = Column(String(20), default=EvidenceSourceType.FILE.value)  # file/text/input
    original_filename = Column(String(500), nullable=True)  # 原始文件名
    display_name = Column(String(200), nullable=True)  # 规范显示名称（AI生成，用于证据目录）
    file_path = Column(String(1000), nullable=True)  # 文件存储路径
    file_hash = Column(String(64), nullable=True, index=True)  # 文件内容哈希 (SHA256)
    content_hash = Column(String(64), nullable=True, index=True)  # 文本内容哈希 (用于去重)

    # ==================== 内容 ====================
    raw_content = Column(Text, nullable=True)  # 原始内容
    extracted_content = Column(Text, nullable=True)  # 提取的文本
    summary = Column(Text, nullable=True)  # AI生成的摘要

    # ==================== 搜索与编号 ====================
    evidence_number = Column(String(50), nullable=True, index=True)  # 用户自定义证据编号（如E001）
    search_keywords = Column(JSON, default=list)  # 搜索关键词缓存
    related_claims = Column(JSON, default=list)  # 关联的诉求ID列表

    # ==================== 分类 ====================
    evidence_type = Column(String(50), default=EvidenceType.OTHER.value)  # 证据类型
    proves_facts = Column(JSON, default=list)  # 证明的事实列表 [{"fact": "...", "confidence": 0.9}]
    source_party = Column(String(20), default=EvidenceSourceParty.OUR_SIDE.value)  # 来源方

    # ==================== 信度评估 ====================
    credibility_score = Column(Float, default=0.0)  # 综合信度 0-100
    authenticity_score = Column(Float, default=0.0)  # 形式真实性
    reliability_score = Column(Float, default=0.0)  # 来源可靠性
    consistency_score = Column(Float, default=0.0)  # 内容一致性
    corroboration_score = Column(Float, default=0.0)  # 与其他证据印证度
    credibility_analysis = Column(Text, nullable=True)  # 信度分析说明

    # ==================== 索引 ====================
    keywords = Column(JSON, default=list)  # 关键词列表
    entity_tags = Column(JSON, default=list)  # 实体标签 [{"type": "PARTY", "value": "..."}]
    fact_tags = Column(JSON, default=list)  # 事实标签

    # ==================== 用户纠错 ====================
    user_corrections = Column(JSON, default=list)  # 用户纠错记录
    ai_corrections_acknowledged = Column(Boolean, default=False)  # 是否已确认AI纠错

    # ==================== 使用方向标注 ====================
    usage_direction = Column(String(50), nullable=True)  # 使用方向：支持原告/支持被告/双方可用/需谨慎
    usage_annotations = Column(JSON, default=list)  # 使用方向标注记录 [{"direction": "...", "note": "...", "time": "..."}]
    usage_tags = Column(JSON, default=list)  # 使用标签 ["合同履行", "违约金计算"]
    is_highlighted = Column(Boolean, default=False)  # 是否高亮标记
    highlight_reason = Column(String(200), nullable=True)  # 高亮原因

    # ==================== 安全性评估 ====================
    safety_level = Column(String(20), default='safe')  # safe/caution/danger
    safety_warnings = Column(JSON, default=list)  # 安全警告 [{"type": "adverse", "claims": [], "description": "...", "severity": "high"}]
    adverse_impact_analysis = Column(Text, nullable=True)  # 不利影响分析
    is_warning_ignored = Column(Boolean, default=False)  # 用户是否忽略警告
    ignored_reason = Column(Text, nullable=True)  # 忽略原因
    safety_reviewed = Column(Boolean, default=False)  # 是否已人工审核
    safety_reviewed_by = Column(String(100), nullable=True)  # 审核人
    safety_reviewed_at = Column(DateTime, nullable=True)  # 审核时间

    # ==================== 版本控制 ====================
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    previous_version_id = Column(String(36), nullable=True)  # 上一个版本
    version_notes = Column(Text, nullable=True)  # 版本说明

    # ==================== 元数据 ====================
    page_count = Column(Integer, default=0)
    page_numbers = Column(JSON, nullable=True)  # 涉及页码
    language = Column(String(10), default="zh-CN")
    file_size = Column(Integer, nullable=True)  # 文件大小(字节)

    # ==================== 状态 ====================
    status = Column(String(20), default=EvidenceStatus.PENDING.value)
    processing_notes = Column(Text, nullable=True)  # 处理备注

    # ==================== 关联ID缓存 (优化查询) ====================
    related_evidence_ids = Column(JSON, default=list)  # 直接关联的证据ID
    contradicted_evidence_ids = Column(JSON, default=list)  # 矛盾的证据ID

    # ==================== 时间戳 ====================
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    indexed_at = Column(DateTime, nullable=True)  # 索引时间
    processed_at = Column(DateTime, nullable=True)  # 处理完成时间

    # ==================== 关系 ====================
    relationships_from = relationship(
        "EvidenceRelationship",
        foreign_keys="EvidenceRelationship.from_evidence_id",
        back_populates="from_evidence",
        cascade="all, delete-orphan"
    )
    relationships_to = relationship(
        "EvidenceRelationship",
        foreign_keys="EvidenceRelationship.to_evidence_id",
        back_populates="to_evidence",
        cascade="all, delete-orphan"
    )
    # fact_links 使用 JSON 存储的证据ID关联，不需要外键关系

    # ==================== 索引 ====================
    __table_args__ = (
        Index('idx_evidence_tenant_case', 'tenant_id', 'case_id'),
        Index('idx_evidence_case_type', 'case_id', 'evidence_type'),
        Index('idx_evidence_source_party', 'case_id', 'source_party'),
        Index('idx_evidence_status', 'case_id', 'status'),
        Index('idx_evidence_credibility', 'case_id', 'credibility_score'),
        Index('idx_evidence_content_hash', 'content_hash'),
    )

    def generate_content_hash(self) -> str:
        """
        生成规范化后的内容哈希，用于去重检测
        """
        if not self.raw_content:
            return None

        normalized = self._normalize_text(self.raw_content)
        self.content_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        return self.content_hash

    def generate_file_hash(self) -> str:
        """
        生成文件哈希
        """
        if not self.file_path:
            return None

        try:
            with open(self.file_path, 'rb') as f:
                self.file_hash = hashlib.sha256(f.read()).hexdigest()
            return self.file_hash
        except Exception:
            return None

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        规范化文本用于比较：去除空格、换行、标点，统一大小写
        """
        if not text:
            return ""
        # 去除多余空白字符
        text = re.sub(r'\s+', '', text)
        # 去除标点符号
        text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
        return text.lower()

    @staticmethod
    def get_type_display(evidence_type: str) -> dict:
        """获取证据类型的中文显示"""
        type_map = {
            EvidenceType.CONTRACT.value: {'name': '合同协议类', 'icon': '📄', 'color': '#1890ff'},
            EvidenceType.CORRESPONDENCE.value: {'name': '函件沟通类', 'icon': '📧', 'color': '#52c41a'},
            EvidenceType.PAYMENT.value: {'name': '支付凭证类', 'icon': '💰', 'color': '#faad14'},
            EvidenceType.IDENTITY.value: {'name': '身份证明类', 'icon': '🪪', 'color': '#722ed1'},
            EvidenceType.AUDIO_VIDEO.value: {'name': '视听资料类', 'icon': '🎬', 'color': '#eb2f96'},
            EvidenceType.TESTIMONY.value: {'name': '证人证言类', 'icon': '👤', 'color': '#13c2c2'},
            EvidenceType.EXPERT.value: {'name': '鉴定意见类', 'icon': '🔬', 'color': '#2f54d2'},
            EvidenceType.DOCUMENT.value: {'name': '书证类', 'icon': '📃', 'color': '#fa8c16'},
            EvidenceType.MATERIAL.value: {'name': '物证类', 'icon': '📦', 'color': '#8c8c8c'},
            EvidenceType.OTHER.value: {'name': '其他类', 'icon': '📎', 'color': '#bfbfbf'},
        }
        return type_map.get(evidence_type, type_map[EvidenceType.OTHER.value])

    def to_dict(self) -> dict:
        """转换为字典"""
        type_info = self.get_type_display(self.evidence_type)
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'case_id': self.case_id,
            'source_type': self.source_type,
            'original_filename': self.original_filename,
            'display_name': self.display_name,
            'file_path': self.file_path,
            'evidence_type': self.evidence_type,
            'evidence_type_name': type_info['name'],
            'evidence_type_icon': type_info['icon'],
            'source_party': self.source_party,
            'summary': self.summary,
            'extracted_content': self.extracted_content,
            'raw_content': self.raw_content,
            'credibility_score': self.credibility_score,
            'authenticity_score': self.authenticity_score,
            'reliability_score': self.reliability_score,
            'consistency_score': self.consistency_score,
            'corroboration_score': self.corroboration_score,
            'keywords': self.keywords,
            'entity_tags': self.entity_tags,
            'proves_facts': self.proves_facts,
            'status': self.status,
            # ==================== 搜索与编号 ====================
            'evidence_number': self.evidence_number,
            'search_keywords': self.search_keywords,
            'related_claims': self.related_claims,
            # ==================== 用户纠错 ====================
            'user_corrections': self.user_corrections,
            'ai_corrections_acknowledged': self.ai_corrections_acknowledged,
            # ==================== 使用方向标注 ====================
            'usage_direction': self.usage_direction,
            'usage_annotations': self.usage_annotations,
            'usage_tags': self.usage_tags,
            'is_highlighted': self.is_highlighted,
            'highlight_reason': self.highlight_reason,
            # ==================== 安全性评估 ====================
            'safety_level': self.safety_level,
            'safety_warnings': self.safety_warnings,
            'adverse_impact_analysis': self.adverse_impact_analysis,
            'is_warning_ignored': self.is_warning_ignored,
            'ignored_reason': self.ignored_reason,
            'safety_reviewed': self.safety_reviewed,
            'safety_reviewed_by': self.safety_reviewed_by,
            'safety_reviewed_at': self.safety_reviewed_at.isoformat() if self.safety_reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_graph_node(self) -> dict:
        """转换为图谱节点格式"""
        type_info = self.get_type_display(self.evidence_type)
        return {
            'id': f"evidence_{self.id}",
            'type': 'evidence',
            'label': (self.summary or self.original_filename or '证据')[:30],
            'full_label': self.summary or self.original_filename,
            'category': self.evidence_type,
            'category_name': type_info['name'],
            'icon': type_info['icon'],
            'credibility': self.credibility_score,
            'source_party': self.source_party,
            'proves_facts': [f['fact'] for f in (self.proves_facts or [])],
            'size': self._get_graph_size(),
            'color': self._get_safety_color() or type_info['color'],
            'safety_level': self.safety_level,
            'is_highlighted': self.is_highlighted
        }

    def _get_safety_color(self) -> str:
        """根据安全性级别确定颜色"""
        safety_colors = {
            'danger': '#f5222d',
            'caution': '#faad14',
            'safe': '#52c41a'
        }
        return safety_colors.get(self.safety_level)

    @staticmethod
    def get_safety_level_display(safety_level: str) -> dict:
        """获取安全性级别的中文显示"""
        level_map = {
            'danger': {'name': '危险', 'icon': '🚨', 'color': '#f5222d'},
            'caution': {'name': '注意', 'icon': '⚠️', 'color': '#faad14'},
            'safe': {'name': '安全', 'icon': '✅', 'color': '#52c41a'},
        }
        return level_map.get(safety_level, level_map.get('safe'))

    @staticmethod
    def get_usage_direction_display(direction: str) -> dict:
        """获取使用方向的中文显示"""
        direction_map = {
            'support_plaintiff': {'name': '支持原告', 'icon': '📗', 'color': '#52c41a'},
            'support_defendant': {'name': '支持被告', 'icon': '📘', 'color': '#1890ff'},
            'both_available': {'name': '双方可用', 'icon': '📙', 'color': '#722ed1'},
            'use_with_caution': {'name': '需谨慎使用', 'icon': '📕', 'color': '#f5222d'},
        }
        return direction_map.get(direction, {'name': '未标注', 'icon': '❓', 'color': '#bfbfbf'})

    def _get_graph_size(self) -> int:
        """根据信度确定图谱节点大小"""
        if self.credibility_score >= 80:
            return 30
        elif self.credibility_score >= 60:
            return 25
        elif self.credibility_score >= 40:
            return 20
        return 15


class EvidenceRelationship(Base):
    """
    证据关系
    记录证据之间的支持、矛盾、补充等关系
    """
    __tablename__ = "evidence_relationships_v2"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    from_evidence_id = Column(String(36), ForeignKey("evidence_items_v2.id", ondelete="CASCADE"), nullable=False)
    to_evidence_id = Column(String(36), ForeignKey("evidence_items_v2.id", ondelete="CASCADE"), nullable=False)

    # 关系类型
    RELATIONSHIP_TYPES = {
        'SUPPORT': {'name': '支持关系', 'description': '证明同一事实', 'color': '#52c41a'},
        'CONTRADICT': {'name': '矛盾关系', 'description': '证明相反事实', 'color': '#f5222d'},
        'SUPPLEMENT': {'name': '补充关系', 'description': '补强其他证据', 'color': '#1890ff'},
        'DERIVE': {'name': '派生关系', 'description': '派生于其他证据', 'color': '#722ed1'},
        'DEPEND': {'name': '依赖关系', 'description': '依赖其他证据生效', 'color': '#faad14'}
    }

    relationship_type = Column(String(20), nullable=False)  # SUPPORT/CONTRADICT/SUPPLEMENT/DERIVE/DEPEND
    strength = Column(Float, default=50.0)  # 关系强度 0-100

    # 分析
    analysis_note = Column(Text, nullable=True)  # 分析说明
    citation_text = Column(Text, nullable=True)  # 引用片段
    confidence = Column(Float, default=0.5)  # 分析置信度 0-1
    reasoning = Column(Text, nullable=True)  # 判断理由

    # 状态
    is_auto_generated = Column(Boolean, default=True)  # 是否自动生成
    is_confirmed = Column(Boolean, default=False)  # 是否经用户确认
    confirmed_by = Column(String(100), nullable=True)  # 确认人

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    from_evidence = relationship(
        "EvidenceItem",
        foreign_keys=[from_evidence_id],
        back_populates="relationships_from"
    )
    to_evidence = relationship(
        "EvidenceItem",
        foreign_keys=[to_evidence_id],
        back_populates="relationships_to"
    )

    __table_args__ = (
        Index('idx_rel_case', 'case_id'),
        Index('idx_rel_from', 'from_evidence_id'),
        Index('idx_rel_to', 'to_evidence_id'),
        Index('idx_rel_type', 'relationship_type'),
    )

    def get_type_info(self) -> dict:
        """获取关系类型信息"""
        return self.RELATIONSHIP_TYPES.get(
            self.relationship_type,
            {'name': '未知', 'description': '', 'color': '#bfbfbf'}
        )

    def to_graph_edge(self) -> dict:
        """转换为图谱边格式"""
        type_info = self.get_type_info()
        return {
            'from': f"evidence_{self.from_evidence_id}",
            'to': f"evidence_{self.to_evidence_id}",
            'type': self.relationship_type,
            'type_name': type_info['name'],
            'strength': self.strength,
            'color': type_info['color'],
            'analysis_note': self.analysis_note
        }


class EvidenceFact(Base):
    """
    证据事实
    记录案件中的关键事实及其证据支撑
    """
    __tablename__ = "evidence_facts"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    description = Column(Text, nullable=False)  # 事实描述

    # 分类
    fact_type = Column(String(50), nullable=True)  # 合同履行/违约/侵权/时间节点...
    importance = Column(String(20), default='normal')  # critical/important/normal
    dispute_level = Column(String(20), default='undisputed')  # undisputed/minor_dispute/major_dispute

    # 关联证据
    supporting_evidence_ids = Column(JSON, default=list)  # 支持该事实的证据ID列表
    contradicting_evidence_ids = Column(JSON, default=list)  # 矛盾证据ID列表
    evidence_ids = Column(JSON, default=list)  # 所有相关证据ID

    # 证据覆盖率
    coverage_score = Column(Float, default=0.0)  # 证据覆盖程度 0-100
    strength_score = Column(Float, default=0.0)  # 论证强度 0-100

    # 关键词
    keywords = Column(JSON, default=list)
    entity_tags = Column(JSON, default=list)

    # 分析
    analysis_note = Column(Text, nullable=True)  # 分析说明
    risk_points = Column(JSON, default=list)  # 风险点

    # 来源
    source_type = Column(String(20), default='manual')  # manual/auto_generated
    linked_thread_id = Column(Integer, nullable=True)  # 关联的线索ID

    # 排序
    sort_order = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case")

    __table_args__ = (
        Index('idx_fact_case', 'case_id'),
        Index('idx_fact_type', 'fact_type'),
        Index('idx_fact_importance', 'importance'),
    )

    def to_graph_node(self) -> dict:
        """转换为图谱节点格式"""
        color_map = {
            'critical': '#f5222d',
            'important': '#faad14',
            'normal': '#1890ff'
        }
        return {
            'id': f"fact_{self.id}",
            'type': 'fact',
            'label': self.description[:30] + '...' if len(self.description) > 30 else self.description,
            'full_label': self.description,
            'category': self.fact_type,
            'importance': self.importance,
            'dispute_level': self.dispute_level,
            'coverage': self.coverage_score,
            'strength': self.strength_score,
            'size': self._get_node_size(),
            'color': color_map.get(self.importance, '#1890ff')
        }

    def _get_node_size(self) -> int:
        """根据重要性确定节点大小"""
        size_map = {'critical': 40, 'important': 30, 'normal': 20}
        return size_map.get(self.importance, 20)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'case_id': self.case_id,
            'description': self.description,
            'fact_type': self.fact_type,
            'importance': self.importance,
            'dispute_level': self.dispute_level,
            'coverage_score': self.coverage_score,
            'strength_score': self.strength_score,
            'supporting_count': len(self.supporting_evidence_ids or []),
            'contradicting_count': len(self.contradicting_evidence_ids or []),
            'keywords': self.keywords,
            'analysis_note': self.analysis_note,
            'risk_points': self.risk_points,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class EvidenceDuplicateCheck(Base):
    """
    证据去重记录
    记录重复检测的历史，防止重复添加
    """
    __tablename__ = "evidence_duplicate_check"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # 新提交的证据
    new_evidence_hash = Column(String(64), nullable=True)  # 新证据的哈希
    new_filename = Column(String(500), nullable=True)

    # 比对到的已有证据
    existing_evidence_id = Column(String(36), nullable=True)

    # 比对结果
    file_hash_match = Column(Boolean, default=False)  # 文件哈希相同
    content_similarity = Column(Float, default=0.0)  # 内容相似度 0-1
    is_duplicate = Column(Boolean, default=False)  # 是否重复
    duplicate_status = Column(String(30), default='new')  # new/suspected/confirmed/false_positive

    # 建议操作
    suggested_action = Column(String(50), nullable=True)  # skip/update/create

    # 用户确认
    user_decision = Column(String(20), nullable=True)  # 用户选择的操作
    confirmed_by = Column(String(100), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    confirmation_note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_dup_case', 'case_id'),
        Index('idx_dup_hash', 'new_evidence_hash'),
    )


class EvidenceKeywordIndex(Base):
    """
    证据关键词索引
    用于快速检索相关证据
    """
    __tablename__ = "evidence_keyword_index"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    keyword = Column(String(200), nullable=False, index=True)
    normalized_keyword = Column(String(200), nullable=True, index=True)  # 规范化后的关键词
    synonyms = Column(JSON, default=list)  # 同义词列表

    # 关联的证据
    evidence_ids = Column(JSON, default=list)  # 包含该关键词的证据ID列表
    fact_ids = Column(JSON, default=list)  # 关联的事实ID列表

    # 统计
    occurrence_count = Column(Integer, default=0)  # 出现次数
    evidence_count = Column(Integer, default=0)  # 关联证据数

    # 来源
    is_auto_generated = Column(Boolean, default=True)  # 是否自动生成

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_kw_case', 'case_id'),
        Index('idx_kw_normalized', 'normalized_keyword'),
    )


class EvidenceAnalysisRecord(Base):
    """
    证据分析历史记录
    存储每次AI分析的详细结果，支持追溯和改进
    """
    __tablename__ = "evidence_analysis_records"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id = Column(String(36), ForeignKey("evidence_items_v2.id", ondelete="CASCADE"), nullable=False, index=True)

    # 分析类型
    analysis_type = Column(String(50), nullable=False)  # credibility/proof/relationship/comprehensive

    # 完整分析结果 (JSON格式保存)
    analysis_result = Column(JSON, default=dict)  # 完整分析结果
    summary = Column(Text, nullable=True)  # 分析摘要

    # 分析维度
    credibility_score = Column(Float, default=0.0)  # 信度评分
    authenticity_score = Column(Float, default=0.0)  # 真实性评分
    reliability_score = Column(Float, default=0.0)  # 可靠性评分
    consistency_score = Column(Float, default=0.0)  # 一致性评分

    # 证明事实
    proves_facts = Column(JSON, default=list)  # 证明的事实列表
    proves_strength = Column(JSON, default=list)  # 各事实的证明强度

    # 质疑方向
    potential_challenges = Column(JSON, default=list)  # 潜在质疑点
    challenge_responses = Column(JSON, default=list)  # 应对建议

    # 补充建议
    reinforcement_suggestions = Column(JSON, default=list)  # 补强建议
    alternative_evidence = Column(JSON, default=list)  # 替代证据

    # 使用时机
    usage_timing = Column(Text, nullable=True)  # 使用时机建议
    presentation_tips = Column(Text, nullable=True)  # 呈现技巧

    # 风险提示
    risk_points = Column(JSON, default=list)  # 风险点
    risk_level = Column(String(20), default='medium')  # 风险等级

    # AI模型信息
    ai_model = Column(String(100), nullable=True)  # 使用的AI模型
    confidence = Column(Float, default=0.0)  # AI置信度

    # 元数据
    version = Column(Integer, default=1)  # 分析版本号
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    evidence = relationship("EvidenceItem")

    __table_args__ = (
        Index('idx_analysis_case', 'case_id'),
        Index('idx_analysis_evidence', 'evidence_id'),
        Index('idx_analysis_type', 'analysis_type'),
        Index('idx_analysis_created', 'created_at'),
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'case_id': self.case_id,
            'evidence_id': self.evidence_id,
            'analysis_type': self.analysis_type,
            'summary': self.summary,
            'credibility_score': self.credibility_score,
            'authenticity_score': self.authenticity_score,
            'reliability_score': self.reliability_score,
            'consistency_score': self.consistency_score,
            'proves_facts': self.proves_facts,
            'potential_challenges': self.potential_challenges,
            'challenge_responses': self.challenge_responses,
            'reinforcement_suggestions': self.reinforcement_suggestions,
            'risk_points': self.risk_points,
            'risk_level': self.risk_level,
            'ai_model': self.ai_model,
            'confidence': self.confidence,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
