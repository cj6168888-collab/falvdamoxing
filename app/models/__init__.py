from app.models.case import Case, CaseStatus, CaseType, ChatMessage
from app.models.case_claim import CaseClaim, CaseClaimStatus
from app.models.document import Document, DocumentTemplate, GeneratedDocument, DocumentSuggestion
from app.models.reminder import Reminder, ReminderType, ReminderPriority
from app.models.adversarial_analysis import (
    AdversarialAnalysis, AdversarialEvidenceItem, ActionPlan, ScenarioPrediction, ProcessMilestone,
    AnalysisPhase, ActionType, RiskLevel, EvidenceType, EvidenceRole
)
from app.models.letter import (
    Letter, LetterDirection, LetterType, ReplyRequirement, UrgentLevel,
    LegalDeadline, MilestoneTemplate, CaseTimeline
)
from app.models.hearing import (
    HearingRecord, HearingType, SpeakerRole, StatementType, TrapType,
    EvidenceTiming, ResponseStrategy, HearingStatement, EvidenceUse,
    HearingWarning, SpeakingGuide, CaseSpeakingStrategy
)
from app.models.appeal import (
    AppealRecord, AppealType, AppealReason, AppealStatus,
    AppealDeadline, AppealArgument, AppealDocument, SecondTrialStrategy
)
from app.models.project import (
    Project, ProjectType, ProjectStatus, ProjectPhase, UserRole,
    ProjectDocument, ProjectMilestone, ProjectCommunication, ProjectEvidence,
    ProjectLegalAdvice, ProjectEvent, ProjectContract, ProjectRisk, ProjectToCase
)

# 证据分析对话模型
from app.models.evidence_analysis import (
    EvidenceAnalysisSession,
    EvidenceAnalysisMessage,
    EvidenceAnalysisResult
)

# 证据系统 V2 模型
from app.models.evidence import (
    EvidenceItem as EvidenceItemV2,
    EvidenceRelationship as EvidenceRelationshipV2,
    EvidenceFact,
    EvidenceDuplicateCheck,
    EvidenceKeywordIndex,
    EvidenceSourceType,
    EvidenceType as EvidenceTypeEnum,
    EvidenceSourceParty,
    EvidenceStatus
)

# 对话系统 V2 模型
from app.models.conversation import (
    ConversationSession,
    ConversationMessage,
    ClarificationRecord,
    QuestionAnalysis,
    ConversationType,
    ConversationStatus,
    ClarificationStatus,
    QuestionIntent,
    ClarificationDimension
)

# 报告系统 V2 模型
from app.models.report import (
    ReportOutline,
    ReportSection,
    SectionReference,
    ReportCache,
    ReportType,
    ReportStatus,
    SectionStatus
)

# biz-7: 质证意见管理模型
from app.models.cross_examination import (
    CrossExaminationRecord,
    CrossExaminationTemplate,
    CrossExaminationType,
    CrossExaminationResult,
    EvidenceChallengerType
)

# 案件节点
try:
    from app.models.case_node import CaseNode
except ImportError:
    pass

# 证据文件夹
from app.models.evidence_folder import (
    EvidenceFolderScan, EvidenceFolderFile, EvidenceFolderConfig
)

# 执行跟踪 V2
from app.models.execution import (
    ExecutionRecord, ExecutionTask, ExecutionAsset, ExecutionStage
)

# 财务
from app.models.finance import CaseFinance, ExpenseRecord, WinRateAssessment

# 对话分析结果
from app.models.conversation_analysis import ConversationAnalysis, ConversationContext

# AI 分析结果
from app.models.analysis_result import AnalysisResult

# 归档
try:
    from app.models.case_archive import CaseArchive
except ImportError:
    pass

# 执行跟踪旧版
try:
    from app.models.execution_tracking import ExecutionTracking
except ImportError:
    pass

# 案件画像
from app.models.case_profile import CaseProfile

# 会议
from app.models.meeting import MeetingRecord

# 当事人
from app.models.case import Party, CounterClaim

# SaaS 多租户
from app.models.tenant import Tenant, TenantType, SubscriptionPlan, SubscriptionStatus
from app.models.user import User, UserRole
from app.models.api_key import APIKey
from app.models.sms_verification import SMSVerificationCode
from app.models.ai_audit import AIRetrievalAudit
