"""
质证意见管理模型（biz-7）
存储和管理质证意见、反驳意见

参考法规：
- 《民事诉讼法》第68-73条（质证规定）
- 《最高人民法院关于民事诉讼证据的若干规定》
- 《最高人民法院关于适用〈中华人民共和国民事诉讼法〉的解释》第90-108条
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class CrossExaminationType(str, enum.Enum):
    """质证类型"""
    AUTHENTICITY = "authenticity"      # 真实性质证
    LEGALITY = "legality"             # 合法性质证
    RELEVANCE = "relevance"           # 关联性质证
    COMPREHENSIVE = "comprehensive"   # 综合性质证


class CrossExaminationResult(str, enum.Enum):
    """质证结论"""
    ACCEPT = "accept"               # 认可
    OBJECT = "object"               # 异议
    PARTIAL = "partial"             # 部分认可
    RESERVE = "reserve"             # 保留意见


class EvidenceChallengerType(str, enum.Enum):
    """质证方类型"""
    OUR_SIDE = "己方"              # 己方质证
    THEIR_SIDE = "对方"            # 对方质证
    COURT = "法院"                 # 法院发问


class CrossExaminationRecord(Base):
    """
    质证意见记录（biz-7）
    
    记录针对证据的质证意见，包括：
    - 对真实性的质证（是否伪造、是否原件）
    - 对合法性的质证（取得方式是否合法）
    - 对关联性的质证（与待证事实的关系）
    - 反驳意见和补充说明
    """
    __tablename__ = "cross_examination_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id = Column(String(36), nullable=True, index=True)  # 证据ID（可为null，表示对案件的总体质证）
    evidence_name = Column(String(500), nullable=True)  # 证据名称（冗余存储便于显示）

    # 质证类型和立场
    examination_type = Column(SQLEnum(CrossExaminationType), default=CrossExaminationType.COMPREHENSIVE)
    examiner_side = Column(SQLEnum(EvidenceChallengerType), default=EvidenceChallengerType.OUR_SIDE)
    
    # 质证结论
    result = Column(SQLEnum(CrossExaminationResult), default=CrossExaminationResult.RESERVE)
    
    # 质证内容
    authenticity_comment = Column(Text, nullable=True)    # 真实性意见
    legality_comment = Column(Text, nullable=True)        # 合法性意见
    relevance_comment = Column(Text, nullable=True)       # 关联性意见
    comprehensive_comment = Column(Text, nullable=True)    # 综合质证意见
    
    # 异议要点
    objection_points = Column(JSON, default=list)  # 异议点列表 [{"point": "...", "severity": "high"}]
    objection_reasons = Column(Text, nullable=True)  # 异议理由详情
    
    # 证据分析引用
    three_natures_analysis_id = Column(String(36), nullable=True)  # 引用三性分析记录ID
    
    # 对方回应
    opponent_response = Column(Text, nullable=True)  # 对方对质证意见的回应
    court_ruling = Column(Text, nullable=True)        # 法院对该质证的处理结果
    
    # 风险评估
    risk_level = Column(String(20), default="low")  # high/medium/low
    risk_description = Column(Text, nullable=True)  # 风险描述
    
    # 关联证据
    supporting_evidence_ids = Column(JSON, default=list)  # 支持质证意见的其他证据
    contradictory_evidence_ids = Column(JSON, default=list)  # 与质证意见矛盾的证据
    
    # 元数据
    is_auto_generated = Column(Boolean, default=False)  # 是否AI自动生成
    is_confirmed = Column(Boolean, default=False)  # 是否经用户确认
    confirmed_by = Column(String(100), nullable=True)  # 确认人
    confirmed_at = Column(DateTime, nullable=True)  # 确认时间
    
    hearing_id = Column(Integer, nullable=True)  # 关联的庭审记录ID
    hearing_date = Column(DateTime, nullable=True)  # 庭审日期
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case")

    __table_args__ = (
        Index('idx_ce_case', 'case_id'),
        Index('idx_ce_evidence', 'evidence_id'),
        Index('idx_ce_type', 'examination_type'),
        Index('idx_ce_side', 'examiner_side'),
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'case_id': self.case_id,
            'evidence_id': self.evidence_id,
            'evidence_name': self.evidence_name,
            'examination_type': self.examination_type.value if self.examination_type else None,
            'examiner_side': self.examiner_side.value if self.examiner_side else None,
            'result': self.result.value if self.result else None,
            'authenticity_comment': self.authenticity_comment,
            'legality_comment': self.legality_comment,
            'relevance_comment': self.relevance_comment,
            'comprehensive_comment': self.comprehensive_comment,
            'objection_points': self.objection_points,
            'objection_reasons': self.objection_reasons,
            'three_natures_analysis_id': self.three_natures_analysis_id,
            'opponent_response': self.opponent_response,
            'court_ruling': self.court_ruling,
            'risk_level': self.risk_level,
            'risk_description': self.risk_description,
            'supporting_evidence_ids': self.supporting_evidence_ids,
            'contradictory_evidence_ids': self.contradictory_evidence_ids,
            'is_auto_generated': self.is_auto_generated,
            'is_confirmed': self.is_confirmed,
            'confirmed_by': self.confirmed_by,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'hearing_id': self.hearing_id,
            'hearing_date': self.hearing_date.isoformat() if self.hearing_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CrossExaminationTemplate(Base):
    """
    质证意见模板（biz-7）
    
    预设的质证意见模板，便于快速生成
    """
    __tablename__ = "cross_examination_templates"

    id = Column(Integer, primary_key=True, index=True)

    # 模板基本信息
    name = Column(String(200), nullable=False)  # 模板名称
    description = Column(Text, nullable=True)  # 模板描述
    category = Column(String(50), default="通用")  # 分类：通用/合同/侵权/劳动
    
    # 适用证据类型
    applicable_evidence_types = Column(JSON, default=list)  # 适用的证据类型列表
    
    # 模板内容
    authenticity_template = Column(Text, nullable=True)  # 真实性质证模板
    legality_template = Column(Text, nullable=True)     # 合法性质证模板
    relevance_template = Column(Text, nullable=True)     # 关联性质证模板
    comprehensive_template = Column(Text, nullable=True)  # 综合质证模板
    
    # 使用统计
    usage_count = Column(Integer, default=0)  # 使用次数
    success_rate = Column(Float, default=0.0)  # 成功率（被法院采纳的比例）
    
    # 元数据
    is_active = Column(Boolean, default=True)  # 是否启用
    is_system = Column(Boolean, default=False)  # 是否系统内置模板
    created_by = Column(String(100), nullable=True)  # 创建人
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_cet_category', 'category'),
        Index('idx_cet_active', 'is_active'),
    )

    @staticmethod
    def get_default_templates() -> list:
        """获取系统默认质证模板"""
        return [
            {
                "name": "合同真实性质证",
                "description": "对合同类证据真实性进行质证的通用模板",
                "category": "合同",
                "applicable_evidence_types": ["CONTRACT", "DOCUMENT"],
                "authenticity_template": """对{evidence_name}的真实性提出如下异议：

1. 【原件缺失】该证据为复印件，未能提供原件供核对，根据《民诉证据规定》第87条，无法确认真实性的复印件不能单独作为定案依据。

2. 【签章真伪不明】该合同上的签章真实性存疑，未能提供签章样本进行比对，也未申请鉴定。

3. 【内容篡改嫌疑】合同中{highlighted_content}与双方实际约定不符，疑似事后添加或篡改。

综上，该证据真实性无法确认，不能作为认定案件事实的依据。""",
                "legality_template": """对{evidence_name}的合法性无异议。""",
                "relevance_template": """对{evidence_name}的关联性有异议。该合同与本案争议焦点'{dispute_point}'无直接关联，不能证明{prove_fact}。""",
            },
            {
                "name": "录音证据质证",
                "description": "对视听资料类证据进行质证的模板",
                "category": "侵权",
                "applicable_evidence_types": ["AUDIO_VIDEO"],
                "authenticity_template": """对{evidence_name}的真实性提出如下异议：

1. 【原始载体缺失】未提供原始录音载体（录音设备或原始文件），无法确认录音是否经过剪辑、合成。

2. 【录音环境不明】未能证明录音的时间、地点、环境，无法确认录音的完整性。

3. 【声音识别问题】录音中的声音难以辨识是否为{party_name}，存在认定的困难。""",
                "legality_template": """对{evidence_name}的合法性提出如下异议：

该录音系{collection_method}取得，根据《民法典》第1033条，{legality_issue}，该录音证据的取得方式存在合法性瑕疵，不应被采纳。""",
                "relevance_template": """即使该录音被采纳，其内容也只能证明{limited_fact}，与本案争议焦点'{dispute_point}'的关联性有限。""",
            },
            {
                "name": "证人证言质证",
                "description": "对证人证言进行质证的模板",
                "category": "通用",
                "applicable_evidence_types": ["TESTIMONY"],
                "authenticity_template": """对{evidence_name}的真实性提出如下异议：

1. 【证人与当事人关系】证人{ witness_name }系{relationship}，与{related_party}存在利害关系，其证言证明力需结合利害关系审查。

2. 【传闻证据】证言内容系证人听{witness_source}所说，属于传来证据，未经亲身经历。

3. 【证言不稳定】证人本次陈述与{witness_previous_statement}存在矛盾。""",
                "legality_template": """对{evidence_name}的合法性提出如下异议：

1. 【未出庭作证】证人{ witness_name }未按《民事诉讼法》第73条的规定出庭接受质询。

2. 【书面证言】仅提供了书面证言，未出庭作证，不符合法定形式。""",
                "relevance_template": """即使该证言被采纳，证人陈述的内容仅能证明{limited_fact}，与本案核心争议焦点关联性不强。""",
            }
        ]
