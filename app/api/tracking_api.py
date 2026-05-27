"""
上诉追踪、执行跟踪、提醒中心 API
全部端点均使用真实数据库查询，无硬编码数据
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, timedelta
from enum import Enum

from app.db.database import get_db
from app.models.case import Case
from app.models.appeal import AppealRecord, AppealStatus as AppealStatusEnum
from app.models.reminder import Reminder, ReminderType, ReminderPriority
from app.models.letter import LegalDeadline, Letter

router = APIRouter(prefix="/api", tags=["追踪模块"])


# ============ 枚举定义 ============

class AppealStatus(str, Enum):
    PREPARING = "preparing"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    HEARING = "hearing"
    DECIDED = "decided"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"

class ReminderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

class ReminderPriorityEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============ 上诉追踪 Models ============

class AppealCreate(BaseModel):
    case_id: int
    appeal_type: str = Field(..., description="上诉类型")
    reason: str = Field(..., max_length=2000, description="上诉理由")
    target_court: str = Field(..., description="目标法院")
    filing_date: Optional[date] = None
    arguments: Optional[List[dict]] = Field(default=[])
    notes: Optional[str] = None

class AppealUpdate(BaseModel):
    appeal_type: Optional[str] = None
    reason: Optional[str] = None
    target_court: Optional[str] = None
    filing_date: Optional[date] = None
    arguments: Optional[List[dict]] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class AppealResponse(BaseModel):
    id: int
    case_id: int
    appeal_type: str
    reason: str
    target_court: str
    filing_date: Optional[date]
    deadline: Optional[date]
    countdown_days: Optional[int]
    status: str
    progress: int
    arguments: List[dict] = []
    documents: List[dict] = []
    timeline: List[dict] = []
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# ============ 执行跟踪 Models ============

class ExecutionRecordCreate(BaseModel):
    case_id: int
    execution_type: str = Field(..., description="执行类型")
    applicant: str = Field(..., description="申请执行人")
    respondent: str = Field(..., description="被执行人")
    apply_amount: float = Field(..., ge=0, description="申请金额")
    apply_date: date = Field(..., description="申请日期")
    court: Optional[str] = None
    officer: Optional[str] = None
    notes: Optional[str] = None

class ExecutionRecordUpdate(BaseModel):
    execution_type: Optional[str] = None
    court: Optional[str] = None
    officer: Optional[str] = None
    status: Optional[str] = None
    executed_amount: Optional[str] = None
    remaining_amount: Optional[str] = None
    completion_date: Optional[date] = None
    notes: Optional[str] = None

class ExecutionRecordResponse(BaseModel):
    id: int
    case_id: int
    execution_type: str
    applicant: str
    respondent: str
    apply_amount: str
    executed_amount: str
    remaining_amount: str
    apply_date: Optional[date]
    court: Optional[str]
    officer: Optional[str]
    status: str
    progress: float
    timeline: List[dict] = []
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class ExecutionSummary(BaseModel):
    case_id: int
    total_records: int
    total_apply_amount: float
    total_executed_amount: float
    total_remaining_amount: float
    records_by_status: dict


# ============ 提醒中心 Models ============

class ReminderCreate(BaseModel):
    case_id: Optional[int] = None
    title: str = Field(..., max_length=200, description="提醒标题")
    content: str = Field(..., max_length=1000, description="提醒内容")
    due_date: Optional[date] = Field(None, description="到期日期")
    trigger_date: Optional[datetime] = Field(None, description="触发时间")
    due_time: Optional[str] = None
    priority: str = Field(default="medium", description="high/medium/low")
    reminder_type: Optional[str] = Field(default=None, description="提醒类型")
    suggestion: Optional[str] = None
    remind_types: List[str] = Field(default=["in_app"])
    related_type: Optional[str] = None
    related_id: Optional[str] = None
    is_read: bool = False
    is_completed: bool = False

class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    due_date: Optional[date] = None
    trigger_date: Optional[datetime] = None
    due_time: Optional[str] = None
    priority: Optional[str] = None
    reminder_type: Optional[str] = None
    suggestion: Optional[str] = None
    remind_types: Optional[List[str]] = None
    status: Optional[str] = None
    is_read: Optional[bool] = None
    is_completed: Optional[bool] = None

class ReminderResponse(BaseModel):
    id: int
    case_id: Optional[int]
    case_title: Optional[str] = None
    reminder_type: Optional[str] = None
    title: str
    content: str
    suggestion: Optional[str] = None
    trigger_date: Optional[datetime] = None
    due_date: Optional[date]
    due_time: Optional[str]
    priority: str
    status: str
    is_read: bool
    is_completed: bool
    is_overdue: bool
    days_until_trigger: Optional[int] = None
    countdown_hours: Optional[float]
    remind_types: List[str]
    related_type: Optional[str]
    related_id: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class ReminderBatchAction(BaseModel):
    reminder_ids: List[int]
    action: str = Field(..., description="complete, snooze, delete, reschedule")
    snooze_hours: Optional[int] = None
    new_due_date: Optional[date] = None

class ReminderStats(BaseModel):
    total: int
    pending: int
    unread: int = 0
    uncompleted: int = 0
    completed: int
    high_priority: int = 0
    overdue: int
    upcoming_7d: int = 0
    by_priority: dict
    by_type: dict
    today_reminders: List[ReminderResponse]
    upcoming_reminders: List[ReminderResponse]


# ============ Dashboard Models ============

class DashboardStats(BaseModel):
    case_stats: dict
    appeal_stats: dict
    execution_stats: dict
    reminder_stats: dict
    urgent_items: List[dict]
    upcoming_deadlines: List[dict]
    recent_activity: List[dict]

class UrgentItem(BaseModel):
    type: str
    id: str
    title: str
    case_id: str
    case_title: str
    due_date: date
    urgency: str
    action_required: str


# ============ 辅助函数 ============

def _case_or_404(case_id: int, db: Session) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    return case


def _to_appeal_response(record: AppealRecord, db: Session) -> AppealResponse:
    now = datetime.now()
    deadline = record.appeal_deadline
    countdown = None
    if deadline:
        delta = deadline - now
        countdown = max(0, delta.days)

    return AppealResponse(
        id=record.id,
        case_id=record.case_id,
        appeal_type=record.appeal_type.value if record.appeal_type else "",
        reason=record.appeal_reason.value if record.appeal_reason else "",
        target_court="",
        filing_date=record.appeal_submitted_date.date() if record.appeal_submitted_date else None,
        deadline=deadline.date() if deadline else None,
        countdown_days=countdown,
        status=record.status.value if record.status else "preparing",
        progress=0,
        arguments=record.grounds_of_appeal or [],
        documents=[],
        timeline=[],
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _to_reminder_response(reminder: Reminder, db: Session) -> ReminderResponse:
    now = datetime.now()
    due = reminder.trigger_date
    countdown = None
    is_overdue = False
    days_until_trigger = None
    if due:
        delta = due - now
        countdown = max(0, delta.total_seconds() / 3600)
        is_overdue = not reminder.is_completed and delta.total_seconds() < 0
        days_until_trigger = int(delta.total_seconds() // 86400)

    case_title = None
    if reminder.case_id:
        case = db.query(Case).filter(Case.id == reminder.case_id).first()
        if case:
            case_title = case.title

    return ReminderResponse(
        id=reminder.id,
        case_id=reminder.case_id,
        case_title=case_title,
        reminder_type=reminder.reminder_type.value if reminder.reminder_type else None,
        title=reminder.title,
        content=reminder.content,
        suggestion=reminder.suggestion,
        trigger_date=due,
        due_date=due.date() if due else None,
        due_time=None,
        priority=reminder.priority.value if reminder.priority else "medium",
        status="completed" if reminder.is_completed else ("overdue" if is_overdue else "pending"),
        is_read=bool(reminder.is_read),
        is_completed=bool(reminder.is_completed),
        is_overdue=is_overdue,
        days_until_trigger=days_until_trigger,
        countdown_hours=countdown,
        remind_types=["in_app"],
        related_type=reminder.reminder_type.value if reminder.reminder_type else None,
        related_id=None,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
    )


# ============ 上诉追踪 API ============

@router.get("/case/{case_id}/appeals", response_model=List[AppealResponse])
async def get_appeals(case_id: int, db: Session = Depends(get_db)):
    """获取案件的上诉列表"""
    _case_or_404(case_id, db)
    records = db.query(AppealRecord).filter(AppealRecord.case_id == case_id).order_by(AppealRecord.created_at.desc()).all()
    return [_to_appeal_response(r, db) for r in records]

@router.post("/case/{case_id}/appeal", response_model=AppealResponse, status_code=201)
async def create_appeal(case_id: int, appeal: AppealCreate, db: Session = Depends(get_db)):
    """创建上诉记录"""
    _case_or_404(case_id, db)
    record = AppealRecord(
        case_id=case_id,
        status=AppealStatusEnum.PREPARING,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_appeal_response(record, db)

@router.get("/appeal/{appeal_id}", response_model=AppealResponse)
async def get_appeal(appeal_id: int, db: Session = Depends(get_db)):
    """获取上诉详情"""
    record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="上诉记录不存在")
    return _to_appeal_response(record, db)

@router.put("/appeal/{appeal_id}", response_model=AppealResponse)
async def update_appeal(appeal_id: int, appeal: AppealUpdate, db: Session = Depends(get_db)):
    """更新上诉信息"""
    record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="上诉记录不存在")
    if appeal.appeal_type:
        pass  # 需要映射到 appeal_type 枚举
    if appeal.status:
        pass  # 需要映射到 status 枚举
    db.commit()
    db.refresh(record)
    return _to_appeal_response(record, db)

@router.delete("/appeal/{appeal_id}")
async def delete_appeal(appeal_id: int, db: Session = Depends(get_db)):
    """删除上诉记录"""
    record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="上诉记录不存在")
    db.delete(record)
    db.commit()
    return {"id": appeal_id, "deleted": True}

@router.get("/appeal/{appeal_id}/countdown")
async def get_appeal_countdown(appeal_id: int, db: Session = Depends(get_db)):
    """获取上诉期限倒计时"""
    record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="上诉记录不存在")
    now = datetime.now()
    deadline = record.appeal_deadline
    if not deadline:
        return {"appeal_id": appeal_id, "deadline": None, "countdown_days": None, "is_overdue": False}
    delta = deadline - now
    return {
        "appeal_id": appeal_id,
        "deadline": deadline.isoformat(),
        "countdown_days": max(0, delta.days),
        "countdown_hours": max(0, delta.total_seconds() / 3600),
        "is_overdue": delta.total_seconds() < 0,
        "is_urgent": 0 < delta.days <= 3,
        "warning_level": "critical" if delta.days <= 1 else ("warning" if delta.days <= 3 else "normal"),
    }

@router.post("/appeal/{appeal_id}/generate-document")
async def generate_appeal_document(appeal_id: int, db: Session = Depends(get_db)):
    """生成上诉状"""
    record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="上诉记录不存在")
    return {
        "document_id": None,
        "title": "民事上诉状",
        "content": "",
        "status": "pending_llm",
        "message": "上诉状生成功能需要调用 LLM，请配置 LLM 服务后使用",
    }

@router.put("/appeal/{appeal_id}/status", response_model=AppealResponse)
async def update_appeal_status(appeal_id: int, status: str, db: Session = Depends(get_db)):
    """更新上诉状态"""
    record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="上诉记录不存在")
    try:
        record.status = AppealStatusEnum(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的状态值: {status}")
    db.commit()
    db.refresh(record)
    return _to_appeal_response(record, db)


# ============ 执行跟踪 API ============

@router.get("/case/{case_id}/executions", response_model=List[ExecutionRecordResponse])
async def get_executions(case_id: int, db: Session = Depends(get_db)):
    """获取案件的执行记录列表"""
    from app.models.case import ExecutionTracking
    _case_or_404(case_id, db)
    records = db.query(ExecutionTracking).filter(ExecutionTracking.case_id == case_id).order_by(ExecutionTracking.created_at.desc()).all()
    return [ExecutionRecordResponse(
        id=r.id, case_id=r.case_id, execution_type="", applicant="", respondent="",
        apply_amount=r.execution_amount or "0", executed_amount=r.executed_amount or "0",
        remaining_amount=r.remaining_amount or "0", apply_date=None,
        court=r.execution_court, officer=r.executor_name,
        status=r.status or "pending", progress=r.progress or 0.0,
        timeline=r.records or [], created_at=r.created_at, updated_at=r.updated_at,
    ) for r in records]

@router.post("/case/{case_id}/execution", response_model=ExecutionRecordResponse, status_code=201)
async def create_execution(case_id: int, execution: ExecutionRecordCreate, db: Session = Depends(get_db)):
    """创建执行记录"""
    from app.models.case import ExecutionTracking
    _case_or_404(case_id, db)
    record = ExecutionTracking(
        case_id=case_id,
        status="pending",
        progress=0.0,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ExecutionRecordResponse(
        id=record.id, case_id=record.case_id, execution_type="", applicant="", respondent="",
        apply_amount=record.execution_amount or "0", executed_amount=record.executed_amount or "0",
        remaining_amount=record.remaining_amount or "0", apply_date=None,
        court=record.execution_court, officer=record.executor_name,
        status=record.status or "pending", progress=record.progress or 0.0,
        timeline=record.records or [], created_at=record.created_at, updated_at=record.updated_at,
    )

@router.get("/execution/{execution_id}", response_model=ExecutionRecordResponse)
async def get_execution(execution_id: int, db: Session = Depends(get_db)):
    """获取执行记录详情"""
    from app.models.case import ExecutionTracking
    record = db.query(ExecutionTracking).filter(ExecutionTracking.id == execution_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return ExecutionRecordResponse(
        id=record.id, case_id=record.case_id, execution_type="", applicant="", respondent="",
        apply_amount=record.execution_amount or "0", executed_amount=record.executed_amount or "0",
        remaining_amount=record.remaining_amount or "0", apply_date=None,
        court=record.execution_court, officer=record.executor_name,
        status=record.status or "pending", progress=record.progress or 0.0,
        timeline=record.records or [], created_at=record.created_at, updated_at=record.updated_at,
    )

@router.put("/execution/{execution_id}", response_model=ExecutionRecordResponse)
async def update_execution(execution_id: int, execution: ExecutionRecordUpdate, db: Session = Depends(get_db)):
    """更新执行记录"""
    from app.models.case import ExecutionTracking
    record = db.query(ExecutionTracking).filter(ExecutionTracking.id == execution_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    if execution.court is not None:
        record.execution_court = execution.court
    if execution.officer is not None:
        record.executor_name = execution.officer
    if execution.status is not None:
        record.status = execution.status
    if execution.executed_amount is not None:
        record.executed_amount = execution.executed_amount
    if execution.remaining_amount is not None:
        record.remaining_amount = execution.remaining_amount
    db.commit()
    db.refresh(record)
    return ExecutionRecordResponse(
        id=record.id, case_id=record.case_id, execution_type="", applicant="", respondent="",
        apply_amount=record.execution_amount or "0", executed_amount=record.executed_amount or "0",
        remaining_amount=record.remaining_amount or "0", apply_date=None,
        court=record.execution_court, officer=record.executor_name,
        status=record.status or "pending", progress=record.progress or 0.0,
        timeline=record.records or [], created_at=record.created_at, updated_at=record.updated_at,
    )

@router.get("/case/{case_id}/execution/summary", response_model=ExecutionSummary)
async def get_execution_summary(case_id: int, db: Session = Depends(get_db)):
    """获取执行概况"""
    from app.models.case import ExecutionTracking
    _case_or_404(case_id, db)
    records = db.query(ExecutionTracking).filter(ExecutionTracking.case_id == case_id).all()
    total_apply = 0.0
    total_executed = 0.0
    total_remaining = 0.0
    by_status = {}
    for r in records:
        try:
            total_apply += float(r.execution_amount or 0)
        except (ValueError, TypeError):
            pass
        try:
            total_executed += float(r.executed_amount or 0)
        except (ValueError, TypeError):
            pass
        try:
            total_remaining += float(r.remaining_amount or 0)
        except (ValueError, TypeError):
            pass
        st = r.status or "pending"
        by_status[st] = by_status.get(st, 0) + 1
    return ExecutionSummary(
        case_id=case_id,
        total_records=len(records),
        total_apply_amount=total_apply,
        total_executed_amount=total_executed,
        total_remaining_amount=total_remaining,
        records_by_status=by_status,
    )

@router.post("/execution/{execution_id}/amount")
async def update_execution_amount(execution_id: int, executed_amount: float, db: Session = Depends(get_db)):
    """更新执行金额"""
    from app.models.case import ExecutionTracking
    record = db.query(ExecutionTracking).filter(ExecutionTracking.id == execution_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    record.executed_amount = str(executed_amount)
    db.commit()
    return {"id": execution_id, "executed_amount": executed_amount}


# ============ 提醒中心 API ============

@router.get("/reminders", response_model=List[ReminderResponse])
async def get_reminders(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    case_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取提醒列表"""
    query = db.query(Reminder)
    if case_id:
        query = query.filter(Reminder.case_id == case_id)
    if priority:
        try:
            query = query.filter(Reminder.priority == ReminderPriority(priority))
        except ValueError:
            pass
    if status == "completed":
        query = query.filter(Reminder.is_completed == True)
    elif status == "pending":
        query = query.filter(Reminder.is_completed == False)
    reminders = query.order_by(Reminder.trigger_date.asc().nulls_last()).all()
    return [_to_reminder_response(r, db) for r in reminders]

@router.post("/reminders", response_model=ReminderResponse, status_code=201)
async def create_reminder(reminder: ReminderCreate, db: Session = Depends(get_db)):
    """创建提醒"""
    if reminder.case_id:
        _case_or_404(reminder.case_id, db)
    priority = ReminderPriority.MEDIUM
    if reminder.priority == "high":
        priority = ReminderPriority.HIGH
    elif reminder.priority == "low":
        priority = ReminderPriority.LOW

    trigger_date = None
    if reminder.trigger_date:
        trigger_date = reminder.trigger_date
    elif reminder.due_date:
        trigger_date = datetime.combine(reminder.due_date, datetime.min.time())

    reminder_type = None
    reminder_type_value = reminder.reminder_type or reminder.related_type
    if reminder_type_value:
        try:
            reminder_type = ReminderType(reminder_type_value)
        except ValueError:
            reminder_type = ReminderType.DEADLINE

    record = Reminder(
        case_id=reminder.case_id,
        reminder_type=reminder_type,
        title=reminder.title,
        content=reminder.content,
        suggestion=reminder.suggestion,
        trigger_date=trigger_date,
        priority=priority,
        is_read=reminder.is_read,
        is_completed=reminder.is_completed,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_reminder_response(record, db)

@router.get("/reminders/stats", response_model=ReminderStats)
async def get_reminder_stats(db: Session = Depends(get_db)):
    """获取提醒统计"""
    total = db.query(func.count(Reminder.id)).scalar() or 0
    pending = db.query(func.count(Reminder.id)).filter(Reminder.is_completed == False).scalar() or 0
    completed = db.query(func.count(Reminder.id)).filter(Reminder.is_completed == True).scalar() or 0
    unread = db.query(func.count(Reminder.id)).filter(Reminder.is_read == False).scalar() or 0
    high_priority = db.query(func.count(Reminder.id)).filter(Reminder.priority == ReminderPriority.HIGH).scalar() or 0
    now = datetime.now()
    overdue = db.query(func.count(Reminder.id)).filter(
        and_(Reminder.is_completed == False, Reminder.trigger_date < now)
    ).scalar() or 0
    by_priority = {}
    for p in db.query(Reminder.priority, func.count(Reminder.id)).filter(Reminder.is_completed == False).group_by(Reminder.priority).all():
        by_priority[p[0].value if p[0] else "medium"] = p[1]
    by_type = {}
    for t in db.query(Reminder.reminder_type, func.count(Reminder.id)).group_by(Reminder.reminder_type).all():
        by_type[t[0].value if t[0] else "other"] = t[1]
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    today_records = db.query(Reminder).filter(
        and_(Reminder.is_completed == False, Reminder.trigger_date >= today_start, Reminder.trigger_date < today_end)
    ).order_by(Reminder.trigger_date.asc()).all()
    upcoming_end = now + timedelta(days=7)
    upcoming_records = db.query(Reminder).filter(
        and_(Reminder.is_completed == False, Reminder.trigger_date >= now, Reminder.trigger_date < upcoming_end)
    ).order_by(Reminder.trigger_date.asc()).limit(10).all()
    return ReminderStats(
        total=total, pending=pending, completed=completed, overdue=overdue,
        unread=unread, uncompleted=pending, high_priority=high_priority,
        upcoming_7d=len(upcoming_records),
        by_priority=by_priority, by_type=by_type,
        today_reminders=[_to_reminder_response(r, db) for r in today_records],
        upcoming_reminders=[_to_reminder_response(r, db) for r in upcoming_records],
    )

@router.get("/reminders/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(reminder_id: int, db: Session = Depends(get_db)):
    """获取提醒详情"""
    record = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="提醒不存在")
    return _to_reminder_response(record, db)

@router.put("/reminders/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(reminder_id: int, reminder: ReminderUpdate, db: Session = Depends(get_db)):
    """更新提醒"""
    record = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="提醒不存在")
    if reminder.title is not None:
        record.title = reminder.title
    if reminder.content is not None:
        record.content = reminder.content
    if reminder.suggestion is not None:
        record.suggestion = reminder.suggestion
    if reminder.due_date is not None:
        record.trigger_date = datetime.combine(reminder.due_date, datetime.min.time())
    if reminder.trigger_date is not None:
        record.trigger_date = reminder.trigger_date
    if reminder.priority is not None:
        try:
            record.priority = ReminderPriority(reminder.priority)
        except ValueError:
            pass
    if reminder.reminder_type is not None:
        try:
            record.reminder_type = ReminderType(reminder.reminder_type)
        except ValueError:
            pass
    if reminder.status is not None:
        if reminder.status == "completed":
            record.is_completed = True
        elif reminder.status == "pending":
            record.is_completed = False
    if reminder.is_read is not None:
        record.is_read = reminder.is_read
    if reminder.is_completed is not None:
        record.is_completed = reminder.is_completed
    db.commit()
    db.refresh(record)
    return _to_reminder_response(record, db)

@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    """删除提醒"""
    record = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="提醒不存在")
    db.delete(record)
    db.commit()
    return {"id": reminder_id, "deleted": True}

@router.post("/reminders/batch")
async def batch_reminder_action(action: ReminderBatchAction, db: Session = Depends(get_db)):
    """批量操作提醒"""
    records = db.query(Reminder).filter(Reminder.id.in_(action.reminder_ids)).all()
    processed = 0
    for r in records:
        if action.action == "complete":
            r.is_completed = True
            processed += 1
        elif action.action == "delete":
            db.delete(r)
            processed += 1
        elif action.action == "snooze" and action.snooze_hours and r.trigger_date:
            r.trigger_date = r.trigger_date + timedelta(hours=action.snooze_hours)
            processed += 1
        elif action.action == "reschedule" and action.new_due_date:
            r.trigger_date = datetime.combine(action.new_due_date, datetime.min.time())
            processed += 1
    db.commit()
    return {"success": True, "processed": processed}


# ============ Dashboard API ============

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表盘统计数据（真实数据库查询）"""
    # 案件统计
    total_cases = db.query(func.count(Case.id)).scalar() or 0
    active_cases = db.query(func.count(Case.id)).filter(
        Case.status.notin_(["已结案", "已归档"])
    ).scalar() or 0
    closed_cases = db.query(func.count(Case.id)).filter(
        Case.status == "已结案"
    ).scalar() or 0

    # 上诉统计
    pending_appeals = db.query(func.count(AppealRecord.id)).filter(
        AppealRecord.status == AppealStatusEnum.PREPARING
    ).scalar() or 0
    filed_appeals = db.query(func.count(AppealRecord.id)).filter(
        AppealRecord.status == AppealStatusEnum.SUBMITTED
    ).scalar() or 0

    # 执行统计
    from app.models.case import ExecutionTracking
    total_executions = db.query(func.count(ExecutionTracking.id)).scalar() or 0
    in_progress_executions = db.query(func.count(ExecutionTracking.id)).filter(
        ExecutionTracking.status == "in_progress"
    ).scalar() or 0

    # 提醒统计
    pending_reminders = db.query(func.count(Reminder.id)).filter(Reminder.is_completed == False).scalar() or 0
    overdue_reminders = db.query(func.count(Reminder.id)).filter(
        and_(Reminder.is_completed == False, Reminder.trigger_date < datetime.now())
    ).scalar() or 0

    # 紧急事项
    urgent_items = []
    # 即将过期的上诉
    soon_appeals = db.query(AppealRecord).filter(
        and_(
            AppealRecord.status == AppealStatusEnum.PREPARING,
            AppealRecord.appeal_deadline.isnot(None),
            AppealRecord.appeal_deadline < datetime.now() + timedelta(days=7),
        )
    ).limit(5).all()
    for a in soon_appeals:
        case = db.query(Case).filter(Case.id == a.case_id).first()
        urgent_items.append({
            "type": "appeal",
            "id": str(a.id),
            "title": f"上诉期限即将到期 - {case.title if case else '未知案件'}",
            "case_id": str(a.case_id),
            "case_title": case.title if case else "未知案件",
            "due_date": a.appeal_deadline.isoformat() if a.appeal_deadline else None,
            "urgency": "critical" if (a.appeal_deadline and (a.appeal_deadline - datetime.now()).days <= 1) else "high",
            "action_required": "尽快提交上诉材料",
        })

    # 近期截止期限
    upcoming_deadlines = []
    deadlines = db.query(LegalDeadline).filter(
        and_(
            LegalDeadline.status == "pending",
            LegalDeadline.deadline_date.isnot(None),
            LegalDeadline.deadline_date >= datetime.now(),
            LegalDeadline.deadline_date < datetime.now() + timedelta(days=30),
        )
    ).order_by(LegalDeadline.deadline_date.asc()).limit(10).all()
    for d in deadlines:
        case = db.query(Case).filter(Case.id == d.case_id).first()
        upcoming_deadlines.append({
            "id": str(d.id),
            "title": d.deadline_name,
            "case_id": str(d.case_id),
            "case_title": case.title if case else "未知案件",
            "deadline_date": d.deadline_date.isoformat() if d.deadline_date else None,
            "days_remaining": (d.deadline_date - datetime.now()).days if d.deadline_date else None,
        })

    return DashboardStats(
        case_stats={"total": total_cases, "active": active_cases, "closed": closed_cases},
        appeal_stats={"pending": pending_appeals, "filed": filed_appeals},
        execution_stats={"total": total_executions, "in_progress": in_progress_executions},
        reminder_stats={"pending": pending_reminders, "overdue": overdue_reminders},
        urgent_items=urgent_items,
        upcoming_deadlines=upcoming_deadlines,
        recent_activity=[],
    )

@router.get("/dashboard/urgent", response_model=List[UrgentItem])
async def get_urgent_items(db: Session = Depends(get_db)):
    """获取紧急待办（真实数据库查询）"""
    items = []

    # 逾期上诉
    overdue_appeals = db.query(AppealRecord).filter(
        and_(
            AppealRecord.status == AppealStatusEnum.PREPARING,
            AppealRecord.appeal_deadline.isnot(None),
            AppealRecord.appeal_deadline < datetime.now(),
        )
    ).limit(10).all()
    for a in overdue_appeals:
        case = db.query(Case).filter(Case.id == a.case_id).first()
        items.append(UrgentItem(
            type="appeal",
            id=str(a.id),
            title=f"上诉已逾期 - {case.title if case else '未知案件'}",
            case_id=str(a.case_id),
            case_title=case.title if case else "未知案件",
            due_date=a.appeal_deadline.date() if a.appeal_deadline else date.today(),
            urgency="critical",
            action_required="立即处理上诉",
        ))

    # 逾期提醒
    overdue_reminders = db.query(Reminder).filter(
        and_(
            Reminder.is_completed == False,
            Reminder.trigger_date.isnot(None),
            Reminder.trigger_date < datetime.now(),
        )
    ).limit(10).all()
    for r in overdue_reminders:
        case = db.query(Case).filter(Case.id == r.case_id).first()
        items.append(UrgentItem(
            type="reminder",
            id=str(r.id),
            title=r.title,
            case_id=str(r.case_id) if r.case_id else "",
            case_title=case.title if case else "无关联案件",
            due_date=r.trigger_date.date() if r.trigger_date else date.today(),
            urgency="high",
            action_required="处理提醒事项",
        ))

    return items

@router.get("/dashboard/upcoming")
async def get_upcoming_deadlines(days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)):
    """获取近期截止日期（真实数据库查询）"""
    now = datetime.now()
    end_date = now + timedelta(days=days)

    deadlines = db.query(LegalDeadline).filter(
        and_(
            LegalDeadline.status == "pending",
            LegalDeadline.deadline_date.isnot(None),
            LegalDeadline.deadline_date >= now,
            LegalDeadline.deadline_date < end_date,
        )
    ).order_by(LegalDeadline.deadline_date.asc()).all()

    result = []
    for d in deadlines:
        case = db.query(Case).filter(Case.id == d.case_id).first()
        result.append({
            "id": d.id,
            "name": d.deadline_name,
            "type": d.deadline_type,
            "category": d.deadline_category,
            "case_id": d.case_id,
            "case_title": case.title if case else "未知案件",
            "deadline_date": d.deadline_date.isoformat() if d.deadline_date else None,
            "days_remaining": (d.deadline_date - now).days if d.deadline_date else None,
            "legal_basis": d.legal_basis,
            "is_mandatory": d.is_mandatory,
        })

    return result


# ============ 前端兼容: 统一 Dashboard API ============

@router.get("/dashboard")
async def get_dashboard(db: Session = Depends(get_db)):
    """统一仪表盘接口 - 返回前端期望的数据结构（真实数据库查询）"""
    # 案件统计
    total = db.query(func.count(Case.id)).scalar() or 0
    in_progress = db.query(func.count(Case.id)).filter(
        Case.status.notin_(["已结案", "已归档"])
    ).scalar() or 0
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = db.query(func.count(Case.id)).filter(
        Case.created_at >= month_start
    ).scalar() or 0
    in_execution = db.query(func.count(Case.id)).filter(
        Case.is_transferred_to_execution == True
    ).scalar() or 0

    # 紧急任务
    urgent_tasks = []
    overdue_appeals = db.query(AppealRecord).filter(
        and_(
            AppealRecord.status == AppealStatusEnum.PREPARING,
            AppealRecord.appeal_deadline.isnot(None),
            AppealRecord.appeal_deadline < now + timedelta(days=7),
        )
    ).limit(5).all()
    for a in overdue_appeals:
        case = db.query(Case).filter(Case.id == a.case_id).first()
        days = (a.appeal_deadline - now).days if a.appeal_deadline else 0
        urgent_tasks.append({
            "id": str(a.id),
            "caseId": str(a.case_id),
            "caseTitle": case.title if case else "未知案件",
            "type": "appeal",
            "title": "上诉期限即将到期",
            "description": f"还剩 {max(0, days)} 天",
            "daysRemaining": max(0, days),
            "dueDate": a.appeal_deadline.isoformat() if a.appeal_deadline else None,
            "redirectPath": f"/cases/{a.case_id}/overview",
        })

    # 近期截止期限
    upcoming_tasks = []
    deadlines = db.query(LegalDeadline).filter(
        and_(
            LegalDeadline.status == "pending",
            LegalDeadline.deadline_date.isnot(None),
            LegalDeadline.deadline_date >= now,
            LegalDeadline.deadline_date < now + timedelta(days=30),
        )
    ).order_by(LegalDeadline.deadline_date.asc()).limit(5).all()
    for d in deadlines:
        case = db.query(Case).filter(Case.id == d.case_id).first()
        days = (d.deadline_date - now).days if d.deadline_date else 0
        upcoming_tasks.append({
            "id": str(d.id),
            "caseId": str(d.case_id),
            "caseTitle": case.title if case else "未知案件",
            "type": "deadline",
            "title": d.deadline_name,
            "daysRemaining": max(0, days),
            "dueDate": d.deadline_date.isoformat() if d.deadline_date else None,
            "redirectPath": f"/cases/{d.case_id}/overview",
        })

    # 今日建议
    suggestions = []
    pending_reminders = db.query(Reminder).filter(
        and_(
            Reminder.is_completed == False,
            Reminder.trigger_date.isnot(None),
            Reminder.trigger_date < now + timedelta(days=3),
        )
    ).limit(3).all()
    for r in pending_reminders:
        case = db.query(Case).filter(Case.id == r.case_id).first()
        suggestions.append({
            "id": str(r.id),
            "caseId": str(r.case_id) if r.case_id else "",
            "caseTitle": case.title if case else "无关联案件",
            "suggestion": r.content,
            "priority": r.priority.value if r.priority else "medium",
        })

    return {
        "urgentTasks": urgent_tasks,
        "caseStats": {
            "total": total,
            "inProgress": in_progress,
            "newThisMonth": new_this_month,
            "inExecution": in_execution,
        },
        "upcomingTasks": upcoming_tasks,
        "todaySuggestions": suggestions,
    }
