"""
统一时间管理服务 (Timeline Service Facade)
==========================================
整合三个时间管理子服务，为API层提供统一的时间/期限/里程碑管理入口：
- LegalDeadlineService: 法律期限计算（时效/举证/上诉/执行等）
- MilestoneManager: 里程碑管理（去重/增量/状态追踪）
- MilestoneGenerator: 里程碑自动生成（模板/AI增强）

Facade 模式：对现有服务零侵入，渐进式合并
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.services.deadline_service import LegalDeadlineService, deadline_service as _deadline_svc
from app.services.milestone_manager import MilestoneManager
from app.services.milestone_generator import MilestoneGenerator


class TimelineService:
    """
    统一时间管理服务 Facade

    对外提供三类时间管理能力：
    1. 法律期限计算：精确计算各类法定期限（含节假日处理）
    2. 里程碑管理：案件的行动计划管理（去重/状态/追踪）
    3. 里程碑生成：基于案件类型和阶段自动生成里程碑
    """

    # 供外部访问的标准期限定义
    STANDARD_DEADLINES = LegalDeadlineService.STANDARD_DEADLINES

    def __init__(self):
        self._deadline: Optional[LegalDeadlineService] = None
        self._milestone_mgr: Optional[MilestoneManager] = None
        self._milestone_gen: Optional[MilestoneGenerator] = None

    @property
    def deadline(self) -> LegalDeadlineService:
        if self._deadline is None:
            self._deadline = _deadline_svc
        return self._deadline

    @property
    def milestone_mgr(self) -> MilestoneManager:
        if self._milestone_mgr is None:
            self._milestone_mgr = MilestoneManager()
        return self._milestone_mgr

    @property
    def milestone_gen(self) -> MilestoneGenerator:
        if self._milestone_gen is None:
            self._milestone_gen = MilestoneGenerator()
        return self._milestone_gen

    # ==================== 期限计算 ====================

    def calculate_deadline(
        self,
        start_date: datetime,
        deadline_type: str,
        business_days_only: bool = True
    ) -> Dict[str, Any]:
        """
        计算法律期限截止日期

        Args:
            start_date: 起始日期（送达日期等）
            deadline_type: 期限类型（如 civil_litigation_appeal / evidence_presentation）
            business_days_only: 是否只计算工作日（节假日自动跳过）

        Returns:
            截止日期及详细信息（含法律依据、风险等级等）
        """
        return self.deadline.calculate_deadline(start_date, deadline_type, business_days_only)

    def get_deadline_info(self, deadline_type: str) -> Dict[str, Any]:
        """获取期限类型定义信息（名称、天数、法律依据、描述）"""
        return self.deadline.get_deadline_info(deadline_type)

    def add_workdays(self, start_date: datetime, days: int) -> datetime:
        """在起始日期后增加工作日天数（自动排除节假日）"""
        return self.deadline.add_workdays(start_date, days)

    def is_workday(self, date: datetime) -> bool:
        """判断某日期是否为工作日"""
        return not self.deadline.is_holiday(date)

    def analyze_letter_reply_requirement(
        self,
        letter_date: datetime,
        letter_content: str = "",
        letter_type: str = ""
    ) -> Dict[str, Any]:
        """
        分析函件回复期限要求

        Args:
            letter_date: 函件日期
            letter_content: 函件内容（可选，用于AI分析紧急程度）
            letter_type: 函件类型（催款函/律师函/法院通知等）

        Returns:
            回复期限建议（含期限天数、法律依据、风险等级、回复建议）
        """
        return self.deadline.analyze_letter_reply_requirement(
            letter_date, letter_content, letter_type
        )

    def generate_deadline_warning(
        self,
        case_id: int,
        case_type: str = ""
    ) -> List[Dict[str, Any]]:
        """
        生成案件期限预警报告

        Args:
            case_id: 案件ID
            case_type: 案件类型

        Returns:
            预警列表（按紧急程度排序）
        """
        return self.deadline.generate_deadline_warning(case_id, case_type)

    def create_standard_deadlines(
        self,
        start_date: datetime,
        case_type: str = "civil"
    ) -> List[Dict[str, Any]]:
        """
        为案件创建标准期限清单

        Args:
            start_date: 起始日期
            case_type: 案件类型（civil/criminal/administrative）

        Returns:
            标准期限列表（含截止日期、风险等级等）
        """
        return self.deadline.create_standard_deadlines(start_date, case_type)

    def get_case_progress_info(
        self,
        case_id: int
    ) -> Dict[str, Any]:
        """获取案件进度信息（含当前阶段、进行中/逾期/待处理等统计）"""
        return self.deadline.get_case_progress_info(case_id)

    # ==================== 里程碑生成 ====================

    def generate_milestones(
        self,
        case_type: str,
        case_phase: str,
        start_date: datetime = None,
        use_ai: bool = True,
        case_info: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        自动生成案件里程碑

        Args:
            case_type: 案件类型（civil_first_trial / criminal_first_trial 等）
            case_phase: 当前阶段（pre_litigation / filing / defense 等）
            start_date: 起始日期（None使用当前日期）
            use_ai: 是否使用AI增强（补充AI建议和清单）
            case_info: 案件详细信息（用于AI增强）

        Returns:
            里程碑列表（含阶段、名称、描述、预计日期、AI提示等）
        """
        return self.milestone_gen.generate_milestones(
            case_type=case_type,
            case_phase=case_phase,
            start_date=start_date,
            use_ai=use_ai,
            case_info=case_info
        )

    def generate_incremental_milestones(
        self,
        case_id: int,
        current_phase: str,
        existing_milestones: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        增量生成里程碑（仅生成新里程碑，避免重复）

        Args:
            case_id: 案件ID
            current_phase: 当前阶段
            existing_milestones: 已有里程碑列表

        Returns:
            新增里程碑列表 + 跳过的重复里程碑
        """
        return self.milestone_gen.generate_incremental(
            case_id=case_id,
            current_phase=current_phase,
            existing_milestones=existing_milestones
        )

    def sync_milestones(
        self,
        case_id: int,
        milestones: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        同步里程碑（去重 + 增量更新）

        Args:
            case_id: 案件ID
            milestones: 目标里程碑列表

        Returns:
            同步结果（新增/更新/跳过的数量）
        """
        return self.milestone_gen.sync_milestones(case_id, milestones)

    def update_milestone_from_case(
        self,
        case_id: int,
        case_status: str,
        case_phase: str = ""
    ) -> Dict[str, Any]:
        """
        根据案件状态更新里程碑

        Args:
            case_id: 案件ID
            case_status: 新案件状态
            case_phase: 新案件阶段（可选）

        Returns:
            更新结果
        """
        return self.milestone_gen.update_milestone_from_case(case_id, case_status, case_phase)

    # ==================== 里程碑管理 ====================

    def add_milestone(
        self,
        case_id: int,
        phase: str,
        name: str,
        description: str = "",
        expected_date: datetime = None,
        due_days: int = 0,
        priority: int = 1,
        required: bool = True,
        is_milestone: bool = True,
        ai_tip: str = "",
        checklist: List[str] = None,
        source: str = "system"
    ) -> Dict[str, Any]:
        """
        添加里程碑

        Args:
            case_id: 案件ID
            phase: 阶段（pre_litigation / filing / defense 等）
            name: 里程碑名称
            description: 描述
            expected_date: 预期日期
            due_days: 距开始的天数
            priority: 优先级 1-5
            required: 是否必须完成
            is_milestone: 是否是关键节点
            ai_tip: AI律师提示
            checklist: 执行清单
            source: 来源（system/custom）

        Returns:
            添加结果
        """
        from app.services.milestone_manager import Milestone, MilestoneStatus
        milestone = Milestone(
            milestone_id=f"{case_id}_{phase}_{int(datetime.now().timestamp())}",
            phase=phase,
            name=name,
            description=description,
            expected_date=expected_date,
            due_days=due_days,
            priority=priority,
            required=required,
            is_milestone=is_milestone,
            ai_tip=ai_tip,
            checklist=checklist or [],
            source=source
        )
        return self.milestone_mgr.add(milestone)

    def remove_milestone(
        self,
        milestone_id: str
    ) -> bool:
        """移除里程碑"""
        return self.milestone_mgr.remove(milestone_id)

    def update_milestone_status(
        self,
        milestone_id: str,
        status: str
    ) -> bool:
        """更新里程碑状态（pending/in_progress/completed/skipped/overdue）"""
        from app.services.milestone_manager import MilestoneStatus
        try:
            ms = MilestoneStatus(status)
        except ValueError:
            return False
        return self.milestone_mgr.update_status(milestone_id, ms)

    def get_milestones_by_phase(
        self,
        phase: str
    ) -> List[Dict[str, Any]]:
        """按阶段获取里程碑"""
        return [m.to_dict() for m in self.milestone_mgr.get_by_phase(phase)]

    def get_pending_milestones(
        self,
        case_id: int = None
    ) -> List[Dict[str, Any]]:
        """获取待处理里程碑"""
        pending = self.milestone_mgr.get_pending()
        if case_id:
            pending = [m for m in pending if str(case_id) in m.milestone_id]
        return [m.to_dict() for m in pending]

    def get_overdue_milestones(
        self,
        case_id: int = None
    ) -> List[Dict[str, Any]]:
        """获取已逾期里程碑"""
        overdue = self.milestone_mgr.get_overdue()
        if case_id:
            overdue = [m for m in overdue if str(case_id) in m.milestone_id]
        return [m.to_dict() for m in overdue]

    def calculate_milestone_dates(
        self,
        case_id: int,
        start_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        计算里程碑日期（基于起始日期自动推算）

        Args:
            case_id: 案件ID
            start_date: 起始日期

        Returns:
            带计算后日期的里程碑列表
        """
        milestones = self.milestone_mgr.calculate_dates(start_date)
        if case_id:
            milestones = [m for m in milestones if str(case_id) in m.milestone_id]
        return [m.to_dict() for m in milestones]

    # ==================== 综合报告 ====================

    def generate_urgency_report(
        self,
        case_id: int
    ) -> Dict[str, Any]:
        """
        生成案件紧急程度报告

        包含：
        - 逾期里程碑
        - 即将到期（7日内）
        - 期限预警
        - 风险等级评估

        Args:
            case_id: 案件ID

        Returns:
            紧急程度报告
        """
        return self.milestone_gen.generate_urgency_report(case_id)

    def get_timeline_overview(
        self,
        case_id: int,
        start_date: datetime = None
    ) -> Dict[str, Any]:
        """
        获取案件时间线总览

        Args:
            case_id: 案件ID
            start_date: 起始日期（None使用当前日期）

        Returns:
            时间线概览（阶段分布、里程碑统计、关键日期等）
        """
        if start_date is None:
            start_date = datetime.now()

        # 获取标准期限
        standard = self.create_standard_deadlines(start_date)

        # 获取里程碑
        milestones = self.calculate_milestone_dates(case_id, start_date)

        # 获取预警
        warnings = self.generate_deadline_warning(case_id)

        return {
            "case_id": case_id,
            "start_date": start_date.isoformat(),
            "standard_deadlines": standard,
            "milestones": milestones,
            "warnings": warnings,
            "overview": {
                "total_deadlines": len(standard),
                "total_milestones": len(milestones),
                "pending_milestones": len([m for m in milestones if m.get("status") == "pending"]),
                "overdue": len(warnings.get("overdue", [])),
                "upcoming": len(warnings.get("upcoming_7_days", []))
            }
        }


# 单例
timeline_service = TimelineService()
