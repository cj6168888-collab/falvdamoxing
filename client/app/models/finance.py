"""
案件财务模型 - 费用记录、成本收益分析、胜诉概率评估
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class ExpenseCategory(str, enum.Enum):
    """费用类别"""
    COURT_FEE = "court_fee"              # 诉讼费
    LAWYER_FEE = "lawyer_fee"            # 律师费
    EVIDENCE_FEE = "evidence_fee"        # 证据费（鉴定/公证等）
    TRAVEL_FEE = "travel_fee"            # 差旅费
    CONSULTATION_FEE = "consultation_fee"  # 咨询费
    DOCUMENT_FEE = "document_fee"        # 文书费
    EXECUTION_FEE = "execution_fee"      # 执行费
    OTHER = "other"                      # 其他


class ExpenseStatus(str, enum.Enum):
    """费用状态"""
    PENDING = "pending"      # 待支付
    PAID = "paid"            # 已支付
    REIMBURSED = "reimbursed"  # 已报销
    REFUNDED = "refunded"    # 已退还


class WinRateFactor(str, enum.Enum):
    """胜诉概率评估因素"""
    EVIDENCE_STRENGTH = "evidence_strength"      # 证据强度
    LEGAL_BASIS = "legal_basis"                   # 法律依据
    PROCEDURAL_COMPLIANCE = "procedural_compliance"  # 程序合规
    OPPONENT_WEAKNESS = "opponent_weakness"       # 对方弱点
    JUDGE_TENDENCY = "judge_tendency"             # 法官倾向
    PRECEDENT_SUPPORT = "precedent_support"       # 判例支持


class CaseFinance(Base):
    """
    案件财务概览
    """
    __tablename__ = "case_finances"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True, unique=True)

    # 费用汇总
    total_expenses = Column(Float, default=0.0)        # 总费用
    total_paid = Column(Float, default=0.0)            # 已支付
    total_pending = Column(Float, default=0.0)         # 待支付
    total_reimbursed = Column(Float, default=0.0)      # 已报销

    # 收益
    expected_recovery = Column(Float, nullable=True)   # 预期追回金额
    actual_recovery = Column(Float, nullable=True)     # 实际追回金额

    # 成本收益
    cost_benefit_ratio = Column(Float, nullable=True)  # 成本收益比
    net_benefit = Column(Float, nullable=True)         # 净收益

    # 胜诉概率
    win_rate = Column(Float, nullable=True)            # 胜诉概率 0-100
    win_rate_confidence = Column(Float, nullable=True)  # 评估置信度
    win_rate_assessed_at = Column(DateTime, nullable=True)  # 评估时间

    # 备注
    notes = Column(Text, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="case_finance")


class ExpenseRecord(Base):
    """
    费用记录
    """
    __tablename__ = "expense_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 费用信息
    category = Column(SQLEnum(ExpenseCategory), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # 金额
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")

    # 状态
    status = Column(SQLEnum(ExpenseStatus), default=ExpenseStatus.PENDING)

    # 时间
    expense_date = Column(DateTime, nullable=True)       # 费用发生日期
    payment_date = Column(DateTime, nullable=True)       # 支付日期
    due_date = Column(DateTime, nullable=True)           # 应付截止日期

    # 对方信息
    payee = Column(String(200), nullable=True)           # 收款方
    invoice_number = Column(String(100), nullable=True)  # 发票号

    # 关联
    related_document_id = Column(Integer, nullable=True)  # 关联文书

    # 备注
    notes = Column(Text, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="expense_records")


class WinRateAssessment(Base):
    """
    胜诉概率评估
    """
    __tablename__ = "win_rate_assessments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 评估结果
    win_rate = Column(Float, nullable=False)             # 胜诉概率 0-100
    confidence = Column(Float, nullable=True)            # 置信度 0-100

    # 评估因素
    factors = Column(JSON, nullable=True)                # 各因素评分 [{"factor": "...", "score": 0-100, "weight": 0-1}]
    overall_analysis = Column(Text, nullable=True)       # 综合分析

    # 分项评估
    evidence_strength = Column(Float, nullable=True)     # 证据强度
    legal_basis_strength = Column(Float, nullable=True)  # 法律依据强度
    procedural_compliance = Column(Float, nullable=True) # 程序合规
    opponent_weakness = Column(Float, nullable=True)     # 对方弱点
    precedent_support = Column(Float, nullable=True)     # 判例支持

    # 风险
    key_risks = Column(JSON, nullable=True)              # 关键风险
    risk_mitigation = Column(Text, nullable=True)        # 风险缓解建议

    # 评估信息
    assessment_method = Column(String(50), default="ai")  # ai/manual/hybrid
    assessor = Column(String(200), nullable=True)         # 评估人

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="win_rate_assessments")
