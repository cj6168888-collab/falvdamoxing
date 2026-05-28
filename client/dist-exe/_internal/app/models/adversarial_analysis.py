"""
对抗性分析模型 - 诉讼对抗性全面分析
包括：证据攻防矩阵、对手视角分析、案件走向预测、应对策略等
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class AnalysisPhase(str, enum.Enum):
    """分析阶段"""
    NEGOTIATION = "协商"           # 协商阶段
    PRE_LITIGATION = "诉前准备"    # 诉前阶段
    LITIGATION = "诉讼"            # 诉讼阶段
    TRIAL = "审理"                 # 审理阶段
    APPEAL = "上诉"               # 上诉阶段
    EXECUTION = "执行"             # 执行阶段
    CLOSED = "结案"                # 结案


class ActionType(str, enum.Enum):
    """行动类型"""
    LAWSUIT = "起诉"               # 起诉
    ARBITRATION = "仲裁"           # 仲裁
    REPORT = "举报"               # 举报
    MEDIA = "媒体"                # 媒体曝光
    LOBBY = "游说"                # 游说
    NEGOTIATION = "协商"           # 协商
    APPEAL = "上诉"               # 上诉
    EXECUTION = "执行"             # 执行申请
    LETTER = "律师函"              # 律师函


class RiskLevel(str, enum.Enum):
    """风险等级"""
    CRITICAL = "极高"    # 极高风险
    HIGH = "高"          # 高风险
    MEDIUM = "中"        # 中风险
    LOW = "低"           # 低风险
    MINIMAL = "极低"     # 极低风险


class EvidenceType(str, enum.Enum):
    """证据类型"""
    DOCUMENT = "书证"           # 书证
    OBJECT = "物证"            # 物证
    AUDIO = "视听资料"         # 视听资料
    ELECTRONIC = "电子数据"     # 电子数据
    TESTIMONY = "证人证言"      # 证人证言
    STATEMENT = "当事人陈述"    # 当事人陈述
    EXPERT = "鉴定意见"         # 鉴定意见
    SURVEY = "勘验笔录"        # 勘验笔录


class EvidenceRole(str, enum.Enum):
    """证据角色"""
    OFFENSIVE = "进攻性"      # 进攻性证据（对我方有利）
    DEFENSIVE = "防御性"      # 防御性证据（抵消对方证据）
    NEUTRAL = "中性"          # 中性证据
    DAMAGING = "损害性"       # 损害性证据（对对方有利）


class AdversarialAnalysis(Base):
    """
    对抗性分析主记录
    记录一次完整的对抗性分析结果
    """
    __tablename__ = "adversarial_analyses"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 分析概述
    analysis_phase = Column(SQLEnum(AnalysisPhase), default=AnalysisPhase.NEGOTIATION)  # 当前分析对应的阶段
    title = Column(String(500), nullable=False)  # 分析标题

    # 对手信息
    opponent_name = Column(String(200), nullable=True)  # 对方名称
    opponent_type = Column(String(50), nullable=True)  # 对手类型（个人/企业/政府）
    opponent_strength = Column(String(50), nullable=True)  # 对手实力评估

    # 核心分析结果（JSON 存储复杂结构）
    our_strengths = Column(Text, nullable=True)   # 我方优势
    our_weaknesses = Column(Text, nullable=True)  # 我方弱点
    opponent_strengths = Column(Text, nullable=True)  # 对方优势
    opponent_weaknesses = Column(Text, nullable=True)  # 对方弱点

    # 对手可能行动预测
    opponent_likely_actions = Column(Text, nullable=True)  # 对方可能的行动
    opponent_evidence_predictions = Column(Text, nullable=True)  # 对方可能的证据预测
    opponent_attack_angles = Column(Text, nullable=True)  # 对方可能的攻击角度

    # 证据攻防矩阵摘要
    evidence_matrix_summary = Column(Text, nullable=True)  # 证据矩阵摘要

    # 案件走向预测
    possible_scenarios = Column(Text, nullable=True)  # 可能的情景
    scenario_probabilities = Column(JSON, nullable=True)  # 各情景概率

    # 应对策略
    overall_strategy = Column(Text, nullable=True)  # 总体策略
    immediate_actions = Column(Text, nullable=True)  # 立即行动
    contingency_plans = Column(Text, nullable=True)  # 应急预案

    # 风险评估
    risk_assessment = Column(Text, nullable=True)  # 风险评估
    risk_mitigation = Column(Text, nullable=True)  # 风险缓解措施

    # 自动化任务
    auto_tasks = Column(JSON, nullable=True)  # 自动生成的任务清单
    task_progress = Column(JSON, nullable=True)  # 任务进度

    # 分析状态
    is_current = Column(Boolean, default=True)  # 是否为当前分析
    confidence_score = Column(Float, nullable=True)  # 分析置信度

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="adversarial_analyses")
    evidence_items = relationship("AdversarialEvidenceItem", back_populates="analysis", cascade="all, delete-orphan")
    action_plans = relationship("ActionPlan", back_populates="analysis", cascade="all, delete-orphan")


class AdversarialEvidenceItem(Base):
    """
    证据项 - 对抗性分析专用
    单个证据的详细信息和分析
    """
    __tablename__ = "adversarial_evidence_items"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    analysis_id = Column(Integer, ForeignKey("adversarial_analyses.id", ondelete="CASCADE"), index=True)

    # 证据基本信息
    name = Column(String(500), nullable=False)  # 证据名称
    evidence_type = Column(SQLEnum(EvidenceType))  # 证据类型
    source = Column(String(200), nullable=True)  # 证据来源
    description = Column(Text, nullable=True)  # 证据描述
    content_summary = Column(Text, nullable=True)  # 内容摘要

    # 证据归属
    owner = Column(String(50), nullable=False)  # our/opponent/third_party/unknown
    is_in_our_possession = Column(Boolean, default=True)  # 是否在我方手中
    is_in_opponent_possession = Column(Boolean, default=False)  # 是否在对方手中
    possession_probability = Column(Float, nullable=True)  # 对方持有的可能性 (0-1)

    # 证据价值分析
    role = Column(SQLEnum(EvidenceRole))  # 证据角色
    probative_value = Column(Float, nullable=True)  # 证明力 (0-1)
    authenticity_confidence = Column(Float, nullable=True)  # 真实性可信度 (0-1)
    admissibility_risk = Column(Float, nullable=True)  # 可采性风险 (0-1，越高越可能被排除)

    # 攻防分析
    offensive_value = Column(Text, nullable=True)  # 进攻价值
    defensive_value = Column(Text, nullable=True)  # 防御价值
    counter_evidence = Column(Text, nullable=True)  # 可抵消的证据
    counter_by_evidence = Column(Text, nullable=True)  # 可被哪些证据抵消

    # 风险提示
    potential_risks = Column(Text, nullable=True)  # 潜在风险
    recommendations = Column(Text, nullable=True)  # 建议

    # 使用状态
    is_verified = Column(Boolean, default=False)  # 是否已核实
    is_obtained = Column(Boolean, default=False)  # 是否已获取
    obtain_method = Column(String(200), nullable=True)  # 获取方式

    # 排序
    sort_order = Column(Integer, default=0)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    analysis = relationship("AdversarialAnalysis", back_populates="evidence_items")


class ActionPlan(Base):
    """
    行动方案
    针对对方可能的行动制定的对策方案
    """
    __tablename__ = "action_plans"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    analysis_id = Column(Integer, ForeignKey("adversarial_analyses.id", ondelete="CASCADE"), index=True)

    # 行动方案基本信息
    title = Column(String(500), nullable=False)  # 方案标题
    description = Column(Text, nullable=True)  # 方案描述

    # 针对的行动
    target_action = Column(String(200), nullable=True)  # 针对的对方行动
    target_evidence = Column(String(500), nullable=True)  # 针对的对方证据

    # 行动类型
    action_type = Column(SQLEnum(ActionType))  # 我方采取的行动类型

    # 执行计划
    steps = Column(JSON, nullable=True)  # 执行步骤列表
    required_resources = Column(Text, nullable=True)  # 所需资源
    estimated_cost = Column(String(100), nullable=True)  # 预估成本
    estimated_time = Column(String(100), nullable=True)  # 预估时间

    # 效果评估
    expected_effect = Column(Text, nullable=True)  # 预期效果
    success_probability = Column(Float, nullable=True)  # 成功概率 (0-1)
    risk_assessment = Column(Text, nullable=True)  # 风险评估

    # 优先级
    priority = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM)  # 优先级

    # 执行状态
    is_automated = Column(Boolean, default=False)  # 是否自动化
    auto_config = Column(JSON, nullable=True)  # 自动化配置
    is_executed = Column(Boolean, default=False)  # 是否已执行
    executed_at = Column(DateTime, nullable=True)  # 执行时间
    execution_result = Column(Text, nullable=True)  # 执行结果

    # 排序
    sort_order = Column(Integer, default=0)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    analysis = relationship("AdversarialAnalysis", back_populates="action_plans")


class ScenarioPrediction(Base):
    """
    案件走向情景预测
    记录不同证据组合下的可能情景
    """
    __tablename__ = "scenario_predictions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 情景基本信息
    scenario_name = Column(String(500), nullable=False)  # 情景名称
    scenario_description = Column(Text, nullable=True)  # 情景描述

    # 情景类型
    scenario_type = Column(String(50), nullable=True)  # favorable/unfavorable/uncertain

    # 触发条件
    trigger_conditions = Column(Text, nullable=True)  # 触发条件描述
    required_evidence = Column(JSON, nullable=True)  # 需要的证据组合
    avoided_evidence = Column(JSON, nullable=True)  # 需要避免的证据

    # 结果预测
    predicted_outcome = Column(Text, nullable=True)  # 预测结果
    win_probability = Column(Float, nullable=True)  # 胜诉概率 (0-1)
    estimated_amount = Column(String(100), nullable=True)  # 预估金额
    time_estimate = Column(String(100), nullable=True)  # 预估时间

    # 影响分析
    impact_factors = Column(Text, nullable=True)  # 影响因子
    key_variables = Column(JSON, nullable=True)  # 关键变量

    # 应对策略
    strategy_if_occurs = Column(Text, nullable=True)  # 如果发生如何应对
    preparation_checklist = Column(JSON, nullable=True)  # 准备清单

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="scenario_predictions")


class ProcessMilestone(Base):
    """
    流程里程碑
    记录案件流程中的关键节点
    """
    __tablename__ = "process_milestones"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # 里程碑信息
    name = Column(String(500), nullable=False)  # 里程碑名称
    description = Column(Text, nullable=True)  # 描述
    milestone_type = Column(String(50), nullable=True)  # 类型：deadline/action/decision/event

    # 阶段信息
    phase = Column(SQLEnum(AnalysisPhase))  # 所属阶段
    order_in_phase = Column(Integer, default=0)  # 在阶段内的顺序

    # 时间信息
    target_date = Column(DateTime, nullable=True)  # 目标日期
    deadline = Column(DateTime, nullable=True)  # 截止日期
    completed_at = Column(DateTime, nullable=True)  # 完成时间

    # 状态
    status = Column(String(50), default="pending")  # pending/in_progress/completed/skipped/overdue
    completion_rate = Column(Float, default=0.0)  # 完成度 (0-1)

    # 关联行动
    related_actions = Column(JSON, nullable=True)  # 关联的行动方案ID列表
    related_evidence = Column(JSON, nullable=True)  # 关联的证据ID列表

    # AI 自动生成的内容
    ai_suggestions = Column(Text, nullable=True)  # AI 建议
    automated_tasks = Column(JSON, nullable=True)  # 自动生成的任务

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    case = relationship("Case", back_populates="process_milestones")


# 关系已在 Case 模型中定义
