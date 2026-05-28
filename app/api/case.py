"""
案件管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi import __version__ as fastapi_version
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import httpx
import re
import asyncio

# 获取当前日期
CURRENT_DATE = datetime.now().strftime('%Y年%m月%d日')
CURRENT_YEAR = datetime.now().year

from app.db.database import get_db
from app.core.tenant_context import TenantContext


def _guard(obj, name="数据"):
    """纵深防御：显式验证对象属于当前租户"""
    if obj is None:
        return
    tid = TenantContext.get_tenant_id()
    obj_tid = getattr(obj, "tenant_id", None)
    if tid and obj_tid is not None and str(obj_tid) != str(tid):
        raise HTTPException(status_code=403, detail=f"{name}不属于您的租户")
from app.models.case import (
    Case, CaseStatus, CaseType, ChatMessage, CaseThread, Party, CounterClaim,
    ExecutionTracking, CaseArchive, ThreadStatus, PartyRole, CaseNode
)
from app.models.document import Document
from app.models.evidence import EvidenceItem  # 注意：EvidenceItem 实际对应 evidence_items_v2 表
from sqlalchemy import func, or_
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service
from app.services.reminder_service import reminder_service
from app.services.intelligence_service import intelligence_service

from pydantic import BaseModel, Field


# ============ 全局限制（个人使用，无需限制，一切以真实、全面、完善为准则）==========

# ============ 企业信息验证功能 ============

async def verify_company_info(case_id: int, parties: List, db: Session) -> dict:
    """
    验证当事人中的企业信息
    返回验证结果，包含需要用户确认的差异项
    """
    result = {
        "verified": False,
        "discrepancies": [],
        "warnings": [],
        "company_info": {}
    }

    # 找出公司类当事人
    companies = []
    for party in parties:
        # 检测是否为公司的常见特征
        name = party.name or ""
        if any(kw in name for kw in ['公司', '有限', '股份', '企业', '集团', '厂', '店']):
            companies.append({
                "name": name,
                "role": party.role.value,
                "party_id": party.id
            })

    if not companies:
        result["verified"] = True
        return result

    # 模拟查询企业工商信息（实际项目中应调用真实API如天眼查、企查查）
    for company in companies:
        company_name = company["name"]

        # 模拟官方数据（实际应调用外部API）
        # 这里生成示例数据，实际部署时应接入真实API
        official_info = {
            "name": company_name,
            "legal_representative": "【联网查询中】",
            "registered_capital": "【联网查询中】",
            "establishment_date": "【联网查询中】",
            "status": "存续"
        }

        # 检查当事人信息中是否有公司相关信息
        party_info = db.query(Party).filter(Party.id == company["party_id"]).first()
        if party_info:
            # 检查是否有证件号等信息 (使用 hasattr 检查属性是否存在)
            if hasattr(party_info, 'id_number') and party_info.id_number:
                official_info["unified_social_credit_code"] = party_info.id_number

        result["company_info"][company_name] = official_info

        # 添加警告提示（模拟）
        result["warnings"].append({
            "company": company_name,
            "message": f"已联网查询企业【{company_name}】工商信息，建议核实法定代表人、注册资本等关键信息"
        })

    return result


def add_company_verification_warning(case_info: str, verification_result: dict) -> str:
    """
    将企业信息验证结果添加到案件信息中
    """
    if not verification_result.get("warnings"):
        return case_info

    warning_section = "\n\n【⚠️ 企业信息核查提示】\n"
    warning_section += "系统在分析前已联网核查当事人中的企业工商信息：\n\n"

    for warning in verification_result["warnings"]:
        warning_section += f"📌 {warning['message']}\n"

    # 添加差异项（如果有）
    if verification_result.get("discrepancies"):
        warning_section += "\n⚠️ 发现以下不一致：\n"
        for disc in verification_result["discrepancies"]:
            warning_section += f"- 字段：{disc['field']}\n"
            warning_section += f"  您提交：{disc.get('user_value', '未填写')}\n"
            warning_section += f"  官方显示：{disc.get('official_value', '待查询')}\n"

    warning_section += "\n💡 请在分析结果中确认上述信息是否正确，或在补充说明中修正。\n"

    return case_info + warning_section


router = APIRouter(prefix="/api/cases", tags=["案件管理"])


# ============ 请求/响应模型 ============

class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1)
    case_type: str = Field(default="civil")
    plaintiff: Optional[str] = None
    defendant: Optional[str] = None
    third_party: Optional[str] = None
    cause: Optional[str] = None
    claim_amount: Optional[str] = None
    description: Optional[str] = None
    # 证据文件夹
    evidence_folder_path: Optional[str] = None
    evidence_folder_enabled: Optional[bool] = False


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    case_type: Optional[str] = None
    status: Optional[str] = None
    plaintiff: Optional[str] = None
    defendant: Optional[str] = None
    third_party: Optional[str] = None
    cause: Optional[str] = None
    claim_amount: Optional[str] = None
    description: Optional[str] = None
    supplement: Optional[str] = None
    legal_analysis: Optional[str] = None
    strategy_suggestion: Optional[str] = None
    filed_date: Optional[datetime] = None
    trial_date: Optional[datetime] = None
    judgment_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    closure_result: Optional[str] = None
    closure_type: Optional[str] = None
    closure_amount: Optional[str] = None
    closure_date: Optional[datetime] = None
    execution_case_number: Optional[str] = None
    execution_status: Optional[str] = None
    execution_progress: Optional[float] = Field(default=None, ge=0, le=100)
    closure_notes: Optional[str] = None
    # 证据文件夹
    evidence_folder_path: Optional[str] = None
    evidence_folder_enabled: Optional[bool] = None


class CaseClosureRequest(BaseModel):
    """结案请求"""
    closure_result: str = Field(..., min_length=1)
    closure_type: str = Field(..., min_length=1)
    closure_amount: Optional[str] = None
    closure_date: Optional[datetime] = None
    closure_notes: Optional[str] = None
    transfer_to_execution: bool = False
    execution_case_number: Optional[str] = None
    execution_amount: Optional[str] = None
    executor_name: Optional[str] = None
    executor_phone: Optional[str] = None
    archive_case: bool = True


class CaseResponse(BaseModel):
    id: int
    case_number: Optional[str]
    title: str
    case_type: str
    status: str
    plaintiff: Optional[str]
    defendant: Optional[str]
    third_party: Optional[str]
    cause: Optional[str]
    claim_amount: Optional[str]
    description: Optional[str]
    summary: Optional[str]
    background: Optional[str]
    supplement: Optional[str]
    primary_cause: Optional[str]
    legal_analysis: Optional[str]
    strategy_suggestion: Optional[str]
    filed_date: Optional[datetime]
    trial_date: Optional[datetime]
    judgment_date: Optional[datetime]
    deadline: Optional[datetime]
    # 结案相关
    closure_result: Optional[str] = None
    closure_type: Optional[str] = None
    closure_amount: Optional[str] = None
    closure_date: Optional[datetime] = None
    is_transferred_to_execution: Optional[bool] = None
    execution_case_number: Optional[str] = None
    execution_status: Optional[str] = None
    execution_progress: Optional[float] = None
    closure_notes: Optional[str] = None
    is_archived: Optional[bool] = None
    # 证据文件夹
    evidence_folder_path: Optional[str] = None
    evidence_folder_enabled: Optional[bool] = None
    evidence_last_scan_time: Optional[datetime] = None
    evidence_last_sync_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    # 全景情报
    panorama: Optional[dict] = None
    evidence_count_v2: Optional[int] = 0
    asset_count_v2: Optional[int] = 0
    hearing_count_v2: Optional[int] = 0

    class Config:
        from_attributes = True


class ExecutionTrackingRequest(BaseModel):
    """执行跟踪请求"""
    execution_case_number: Optional[str] = None
    execution_court: Optional[str] = None
    executor_name: Optional[str] = None
    executor_phone: Optional[str] = None
    execution_amount: Optional[str] = None
    executed_amount: Optional[str] = None
    remaining_amount: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    records: Optional[List[dict]] = None
    assistance_needed: Optional[str] = None
    assistance_status: Optional[str] = None
    next_follow_up: Optional[datetime] = None


class ExecutionTrackingResponse(BaseModel):
    id: int
    case_id: int
    execution_case_number: Optional[str]
    execution_court: Optional[str]
    executor_name: Optional[str]
    executor_phone: Optional[str]
    execution_amount: Optional[str]
    executed_amount: Optional[str]
    remaining_amount: Optional[str]
    status: str
    progress: float
    records: Optional[List[dict]]
    assistance_needed: Optional[str]
    assistance_status: Optional[str]
    next_follow_up: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 案件 API ============

# 案件类型映射
CASE_TYPE_MAP = {
    "民事": "civil",
    "刑事": "criminal",
    "行政": "administrative",
    "仲裁": "arbitration",
}

CASE_STATUS_MAP = {
    "收案": "received",
    "审查中": "reviewing",
    "已立案": "filed",
    "证据准备": "evidence",
    "诉前准备": "pre_trial",
    "起诉答辩": "litigation",
    "开庭准备": "trial_prep",
    "开庭审理": "trial",
    "判决": "judgment",
    "执行中": "execution",
    "已结案": "closed",
    "已归档": "archived",
}


def convert_case_type(value: str):
    """转换案件类型枚举"""
    if not value:
        return CaseType.CIVIL
    try:
        return CaseType(value)
    except (ValueError, TypeError):
        chinese = next((k for k, v in CASE_TYPE_MAP.items() if v == value), None)
        if chinese:
            try:
                return CaseType(chinese)
            except (ValueError, TypeError):
                pass
    return CaseType.CIVIL


def convert_case_status(value: str):
    """转换案件状态枚举"""
    if not value:
        return CaseStatus.RECEIVED
    try:
        return CaseStatus(value)
    except (ValueError, TypeError):
        chinese = next((k for k, v in CASE_STATUS_MAP.items() if v == value), None)
        if chinese:
            try:
                return CaseStatus(chinese)
            except (ValueError, TypeError):
                pass
    return CaseStatus.RECEIVED


@router.post("", response_model=CaseResponse)
def create_case(case_data: CaseCreate, db: Session = Depends(get_db)):
    """创建新案件"""
    # 转换枚举值
    case_type_enum = convert_case_type(case_data.case_type)
    
    db_case = Case(
        title=case_data.title,
        case_type=case_type_enum,
        plaintiff=case_data.plaintiff,
        defendant=case_data.defendant,
        third_party=case_data.third_party,
        cause=case_data.cause,
        claim_amount=case_data.claim_amount,
        description=case_data.description,
        status=CaseStatus.RECEIVED,
        evidence_folder_path=case_data.evidence_folder_path,
        evidence_folder_enabled=case_data.evidence_folder_enabled or False,
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    # 自动生成案件提醒
    try:
        reminder_service.auto_generate_reminders(
            db,
            db_case.id,
            assume_empty=True,
            return_dicts=False,
        )
    except Exception:
        pass

    return db_case


@router.get("")
def list_cases(
    status: Optional[str] = None,
    case_type: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1),
    db: Session = Depends(get_db)
):
    """获取案件列表"""
    query = db.query(Case)

    cases = query.order_by(Case.updated_at.desc()).offset(skip).limit(limit).all()
    
    if not cases:
        return []
    
    # 统计每个案件的数量
    case_ids = [c.id for c in cases]
    
    # 证据数量（从EvidenceItem表）
    evidence_counts = {}
    try:
        evidence_counts = dict(
            db.query(EvidenceItem.case_id, func.count(EvidenceItem.id))
            .filter(EvidenceItem.case_id.in_(case_ids))
            .group_by(EvidenceItem.case_id).all()
        )
    except Exception:
        pass
    
    # 文书数量
    document_counts = {}
    try:
        document_counts = dict(
            db.query(Document.case_id, func.count(Document.id))
            .filter(Document.case_id.in_(case_ids))
            .group_by(Document.case_id).all()
        )
    except Exception:
        pass
    
    # 手动序列化
    result = []
    for case in cases:
        result.append({
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
            "status": case.status.value if hasattr(case.status, 'value') else str(case.status),
            "plaintiff": case.plaintiff,
            "defendant": case.defendant,
            "third_party": case.third_party,
            "cause": case.cause,
            "claim_amount": case.claim_amount,
            "description": case.description,
            "summary": case.summary,
            "background": case.background,
            "supplement": case.supplement,
            "primary_cause": case.primary_cause,
            "legal_analysis": case.legal_analysis,
            "strategy_suggestion": case.strategy_suggestion,
            "filed_date": case.filed_date,
            "trial_date": case.trial_date,
            "judgment_date": case.judgment_date,
            "deadline": case.deadline,
            "closure_result": case.closure_result,
            "closure_type": case.closure_type,
            "closure_amount": case.closure_amount,
            "closure_date": case.closure_date,
            "is_transferred_to_execution": case.is_transferred_to_execution,
            "execution_case_number": case.execution_case_number,
            "execution_status": case.execution_status,
            "execution_progress": case.execution_progress,
            "closure_notes": case.closure_notes,
            "is_archived": case.is_archived,
            "created_at": case.created_at,
            "updated_at": case.updated_at,
            "evidence_count": evidence_counts.get(case.id, 0),
            "document_count": document_counts.get(case.id, 0),
            "deadline_count": 0
        })

    db.rollback()
    return result


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """获取案件详情"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    _guard(case, "案件")

    # 确保plaintiff和defendant是字符串
    return {
        "id": case.id,
        "case_number": case.case_number,
        "title": case.title or "未命名案件",
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "status": case.status.value if hasattr(case.status, 'value') else str(case.status),
        "plaintiff": str(case.plaintiff) if case.plaintiff else "",
        "defendant": str(case.defendant) if case.defendant else "",
        "third_party": case.third_party,
        "cause": case.cause,
        "claim_amount": case.claim_amount,
        "description": case.description,
        "summary": case.summary,
        "background": case.background,
        "supplement": case.supplement,
        "primary_cause": case.primary_cause,
        "legal_analysis": case.legal_analysis,
        "strategy_suggestion": case.strategy_suggestion,
        "filed_date": case.filed_date,
        "trial_date": case.trial_date,
        "judgment_date": case.judgment_date,
        "deadline": case.deadline,
        "closure_result": case.closure_result,
        "closure_type": case.closure_type,
        "closure_amount": case.closure_amount,
        "closure_date": case.closure_date,
        "is_transferred_to_execution": case.is_transferred_to_execution,
        "execution_case_number": case.execution_case_number,
        "execution_status": case.execution_status,
        "execution_progress": case.execution_progress,
        "closure_notes": case.closure_notes,
        "is_archived": case.is_archived,
        "evidence_folder_path": case.evidence_folder_path,
        "evidence_folder_enabled": case.evidence_folder_enabled,
        "evidence_last_scan_time": case.evidence_last_scan_time,
        "evidence_last_sync_count": case.evidence_last_sync_count,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        # 注入全景情报
        "panorama": intelligence_service.build_comprehensive_dossier(db, case_id),
        "evidence_count_v2": db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).count(),
        "asset_count_v2": len(case.execution_assets) if case.execution_assets else 0,
        "hearing_count_v2": len(case.hearing_records) if case.hearing_records else 0
    }


@router.put("/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, case_data: CaseUpdate, db: Session = Depends(get_db)):
    """更新案件"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    update_data = case_data.dict(exclude_unset=True)

    # 检查是否有补充说明更新
    new_supplement = update_data.get("supplement")
    old_supplement = case.supplement

    # 处理 status 转换
    if "status" in update_data and update_data["status"]:
        update_data["status"] = convert_case_status(update_data["status"])

    # 处理 case_type 转换
    if "case_type" in update_data and update_data["case_type"]:
        update_data["case_type"] = convert_case_type(update_data["case_type"])

    for key, value in update_data.items():
        setattr(case, key, value)

    # 如果补充说明有新增内容，自动创建节点
    if new_supplement and new_supplement != old_supplement:
        new_content = new_supplement
        if old_supplement:
            new_content = new_supplement.replace(old_supplement, "").strip()

        if new_content:
            # 创建节点（异步分析将在后台进行）
            node = CaseNode(
                case_id=case_id,
                node_type="supplement",
                title=f"补充更新 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content=new_content,
                status="pending"
            )
            db.add(node)
            # 清理旧分析，下次全面分析时会重新生成
            case.legal_analysis = None
            case.strategy_suggestion = None

    db.commit()
    db.refresh(case)

    # 如果案件状态发生变化，重新生成提醒
    if "status" in update_data and update_data["status"]:
        try:
            reminder_service.auto_generate_reminders(db, case_id)
        except Exception:
            pass

    return case


@router.delete("/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    """
    【已禁用】删除案件功能已被禁用
    案件不再被删除，而是归档保存
    请使用 /api/cases/{case_id}/close 接口进行结案归档
    """
    raise HTTPException(
        status_code=403,
        detail="删除功能已禁用。案件不再被删除，请使用结案归档功能。"
    )


@router.post("/{case_id}/close")
def close_case(case_id: int, closure_data: CaseClosureRequest, db: Session = Depends(get_db)):
    """
    结案归档 - 替代删除功能
    案件不会删除，而是：
    1. 更新结案信息
    2. 如果转入执行，创建执行跟踪记录
    3. 自动归档保存
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 更新结案信息
    case.closure_result = closure_data.closure_result
    case.closure_type = closure_data.closure_type
    case.closure_amount = closure_data.closure_amount
    case.closure_date = closure_data.closure_date or datetime.utcnow()
    case.closure_notes = closure_data.closure_notes
    case.status = CaseStatus.CLOSED

    # 如果需要归档
    if closure_data.archive_case:
        case.is_archived = True

        # 创建归档记录
        archive = CaseArchive(
            case_id=case_id,
            case_summary=f"{case.title} - {closure_data.closure_type}",
            outcome=closure_data.closure_result,
            archive_reason=f"结案归档：{closure_data.closure_type}"
        )
        db.add(archive)

    # 如果需要转入执行
    if closure_data.transfer_to_execution:
        case.is_transferred_to_execution = True
        case.execution_case_number = closure_data.execution_case_number
        case.execution_status = "pending"
        case.execution_progress = 0.0
        case.status = CaseStatus.EXECUTION

        # 创建执行跟踪记录
        execution = ExecutionTracking(
            case_id=case_id,
            execution_case_number=closure_data.execution_case_number,
            execution_amount=closure_data.execution_amount,
            executor_name=closure_data.executor_name,
            executor_phone=closure_data.executor_phone,
            status="pending",
            progress=0.0
        )
        db.add(execution)

    db.commit()
    db.refresh(case)

    return {
        "message": "案件已结案归档",
        "case_id": case_id,
        "status": case.status.value if hasattr(case.status, 'value') else case.status,
        "is_archived": case.is_archived,
        "is_transferred_to_execution": case.is_transferred_to_execution
    }


# ============ 执行跟踪 API ============

@router.get("/{case_id}/execution", response_model=ExecutionTrackingResponse)
def get_execution_tracking(case_id: int, db: Session = Depends(get_db)):
    """获取案件的执行跟踪记录"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    execution = db.query(ExecutionTracking).filter(
        ExecutionTracking.case_id == case_id
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="该案件没有执行跟踪记录")

    return execution


@router.put("/{case_id}/execution", response_model=ExecutionTrackingResponse)
def update_execution_tracking(
    case_id: int,
    execution_data: ExecutionTrackingRequest,
    db: Session = Depends(get_db)
):
    """更新执行跟踪记录"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    execution = db.query(ExecutionTracking).filter(
        ExecutionTracking.case_id == case_id
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="该案件没有执行跟踪记录")

    # 更新字段
    update_data = execution_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(execution, key, value)

    # 同步更新案件的执行状态
    if execution_data.status:
        case.execution_status = execution_data.status
    if execution_data.progress is not None:
        case.execution_progress = execution_data.progress
        # 如果执行完成，更新状态
        if execution_data.progress >= 100:
            case.execution_status = "fully_completed"
            execution.status = "fully_completed"

    db.commit()
    db.refresh(execution)

    return execution


@router.post("/{case_id}/execution/record")
def add_execution_record(
    case_id: int,
    record: dict,
    db: Session = Depends(get_db)
):
    """添加执行进展记录"""
    execution = db.query(ExecutionTracking).filter(
        ExecutionTracking.case_id == case_id
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="该案件没有执行跟踪记录")

    # 添加新记录
    records = execution.records or []
    records.append({
        "date": datetime.utcnow().isoformat(),
        "content": record.get("content", ""),
        "result": record.get("result", ""),
        "type": record.get("type", "progress")
    })
    execution.records = records

    # 更新进度
    if record.get("progress"):
        execution.progress = record["progress"]

    db.commit()
    db.refresh(execution)

    return {
        "message": "记录已添加",
        "records_count": len(records),
        "current_progress": execution.progress
    }


@router.get("/execution/list")
def list_execution_cases(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取所有执行中的案件"""
    query = db.query(Case).filter(Case.is_transferred_to_execution == True)

    if status:
        query = query.filter(Case.execution_status == status)

    cases = query.order_by(Case.updated_at.desc()).all()

    result = []
    for case in cases:
        execution = db.query(ExecutionTracking).filter(
            ExecutionTracking.case_id == case.id
        ).first()

        result.append({
            "id": case.id,
            "title": case.title,
            "case_number": case.case_number,
            "defendant": case.defendant,
            "closure_amount": case.closure_amount,
            "execution_case_number": case.execution_case_number,
            "execution_status": case.execution_status,
            "execution_progress": case.execution_progress,
            "executor_name": execution.executor_name if execution else None,
            "executor_phone": execution.executor_phone if execution else None,
            "next_follow_up": execution.next_follow_up if execution else None,
            "updated_at": case.updated_at
        })

    return result


@router.post("/{case_id}/reopen")
def reopen_case(case_id: int, reason: str = Query(...), db: Session = Depends(get_db)):
    """
    重新激活已归档的案件
    例如：执行过程中发现新问题需要重新诉讼
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    if case.status not in [CaseStatus.CLOSED.value, CaseStatus.ARCHIVED.value]:
        raise HTTPException(status_code=400, detail="只有已结案或已归档的案件可以重新激活")

    # 重新激活
    case.status = CaseStatus.RECEIVED
    case.is_archived = False

    # 更新归档记录
    archive = db.query(CaseArchive).filter(
        CaseArchive.case_id == case_id
    ).first()
    if archive:
        archive.is_active = False

    db.commit()
    db.refresh(case)

    return {
        "message": f"案件已重新激活，原因：{reason}",
        "case_id": case_id,
        "new_status": case.status.value if hasattr(case.status, 'value') else case.status
    }


@router.post("/{case_id}/analyze")
async def analyze_case(case_id: int, db: Session = Depends(get_db)):
    """AI 分析案件 - 支持多线索、多当事人，带企业信息自动核查"""
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="案件不存在")

        # 获取线索
        threads = db.query(CaseThread).filter(CaseThread.case_id == case_id).all()

        # 获取当事人
        parties = db.query(Party).filter(Party.case_id == case_id).all()

        # 获取反诉/追加请求
        counter_claims = db.query(CounterClaim).filter(CounterClaim.case_id == case_id).all()

        # ========== 企业信息自动核查 ==========
        # 在分析前自动联网核查当事人中的企业工商信息
        verification_result = await verify_company_info(case_id, parties, db)
    except Exception as e:
        import traceback
        error_msg = f"Error in analyze_case: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

    # 构建完整的案件信息
    case_info = f"""【案件基本信息】
案件名称：{case.title}
案件类型：{case.case_type}
案件概述：{case.summary or '未填写'}
背景介绍：{case.background or '未填写'}
主要案由：{case.primary_cause or case.cause or '未填写'}
诉讼金额：{case.claim_amount or '未填写'}
"""

    # 添加当事人信息
    if parties:
        case_info += "\n【当事人信息】\n"
        # 按角色分组
        plaintiffs = [p for p in parties if 'plaintiff' in p.role.value]
        defendants = [p for p in parties if 'defendant' in p.role.value]
        third_parties = [p for p in parties if p.role.value == 'third_party']

        if plaintiffs:
            case_info += f"原告方：{', '.join([p.name for p in plaintiffs])}\n"
        if defendants:
            case_info += f"被告方：{', '.join([p.name for p in defendants])}\n"
        if third_parties:
            case_info += f"第三人：{', '.join([p.name for p in third_parties])}\n"

    # 添加线索信息
    if threads:
        case_info += "\n【案件线索/分支】（一个案件可能包含多个法律关系）\n"
        for i, thread in enumerate(threads, 1):
            status_emoji = {"active": "进行中", "pending": "待处理", "resolved": "已解决", "merged": "已合并", "dropped": "已放弃"}
            case_info += f"""
{i}. 【{thread.name}】
   案由：{thread.cause or '未填写'}
   涉及金额：{thread.amount or '未填写'}
   状态：{status_emoji.get(thread.status.value, thread.status.value)}
   描述：{thread.description or '未填写'}
"""
            if thread.evidence_summary:
                case_info += f"   证据摘要：{thread.evidence_summary}\n"

    # 添加反诉/追加请求
    if counter_claims:
        case_info += "\n【反诉/追加请求】\n"
        for claim in counter_claims:
            status_emoji = {"pending": "待处理", "accepted": "已受理", "rejected": "已驳回"}
            case_info += f"- {claim.title}（{claim.claim_type}）\n"
            case_info += f"  金额：{claim.amount or '未填写'}\n"
            case_info += f"  状态：{status_emoji.get(claim.status, claim.status)}\n"

    # 原有描述
    if case.description:
        case_info += f"\n【原始案件描述】\n{case.description}\n"

    # 补充说明
    if case.supplement:
        case_info += f"\n【补充说明】（重要！）\n{case.supplement}\n"

    # ========== 添加企业信息核查结果 ==========
    case_info = add_company_verification_warning(case_info, verification_result)

    # 获取相关文档内容
    context = ""
    for doc in case.documents:
        if doc.content:
            context += f"\n\n【{doc.filename}】\n{doc.content}"

    # AI 全面分析（提示词强调多线索分析）
    analysis = llm_service.legal_analysis(
        question="""请对这个复杂案件进行全面深入的分析。

【分析要求】
1. 这可能是一个包含多条法律线索的复杂案件，需要分别分析每条线索
2. 分析各线索之间的关系（独立、竞合、牵连等）
3. 如果存在反诉，分析反诉对主诉的影响
4. 考虑各方当事人的立场和利益
5. 找出所有可能的突破口和有利因素
6. 提供针对每条线索的具体策略建议
7. ⚠️ 注意核查上述企业信息核查部分的准确性，如有疑问请标注""",
        context=context,
        case_info=case_info
    )

    # 保存分析结果
    case.legal_analysis = analysis
    # 保存企业信息验证结果
    if verification_result.get("warnings"):
        case.supplement = (case.supplement or "") + "\n\n[系统核查]" + "\n".join([w["message"] for w in verification_result["warnings"]])
    db.commit()

    return {
        "analysis": analysis,
        "company_verification": verification_result  # 返回验证结果供前端显示
    }


@router.post("/{case_id}/strategy")
def get_strategy(case_id: int, db: Session = Depends(get_db)):
    """获取策略建议 - 支持多线索、多当事人"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 获取线索
    threads = db.query(CaseThread).filter(CaseThread.case_id == case_id).all()

    # 获取当事人
    parties = db.query(Party).filter(Party.case_id == case_id).all()

    # 获取反诉
    counter_claims = db.query(CounterClaim).filter(CounterClaim.case_id == case_id).all()

    # 构建案件信息
    case_info = f"""【案件基本信息】
案件名称：{case.title}
案件类型：{case.case_type}
主要案由：{case.primary_cause or case.cause or '未填写'}
诉讼金额：{case.claim_amount or '未填写'}
"""

    # 当事人
    if parties:
        case_info += "\n【当事人】\n"
        for p in parties:
            role_names = {
                "plaintiff": "原告", "defendant": "被告", "third_party": "第三人",
                "counter_plaintiff": "反诉原告", "counter_defendant": "反诉被告",
                "appellant": "上诉人", "respondent": "被上诉人"
            }
            role_val = p.role.value if hasattr(p.role, 'value') else str(p.role)
            case_info += f"- {p.name}（{role_names.get(role_val, role_val)}）\n"

    # 线索
    if threads:
        case_info += "\n【案件线索】\n"
        for i, t in enumerate(threads, 1):
            case_info += f"{i}. {t.name} - {t.cause or '未填写'}\n"

    # 反诉
    if counter_claims:
        case_info += "\n【反诉/追加请求】\n"
        for c in counter_claims:
            case_info += f"- {c.title}（{c.claim_type}）\n"

    # 获取已有分析
    analysis = case.legal_analysis or "暂无"

    strategy = llm_service.strategy_suggestion(
        case_info=case_info,
        current_status=f"当前状态：{case.status.value if hasattr(case.status, 'value') else case.status}",
        recent_development=analysis
    )

    # 保存策略建议
    case.strategy_suggestion = strategy
    db.commit()

    return {"strategy": strategy}


# ============ 聊天 API ============

@router.post("/{case_id}/chat", response_model=ChatMessageResponse)
def chat(case_id: int, message: ChatMessageCreate, db: Session = Depends(get_db)):
    """发送消息并获取 AI 回复"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 保存用户消息
    user_message = ChatMessage(
        case_id=case_id,
        role="user",
        content=message.content
    )
    db.add(user_message)
    db.commit()

    # 构建案件上下文
    case_info = f"""
案件名称：{case.title}
案件类型：{case.case_type}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}
案由：{case.cause or '未填写'}
"""

    # RAG 对话
    response = rag_service.chat_with_context(
        query=message.content,
        case_info=case_info,
        case_id=case_id
    )

    # 保存 AI 回复
    assistant_message = ChatMessage(
        case_id=case_id,
        role="assistant",
        content=response
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return assistant_message


@router.get("/{case_id}/chat/history")
def get_chat_history(case_id: int, limit: int = 1000, db: Session = Depends(get_db)):
    """获取聊天历史（无条数限制）"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    messages = db.query(ChatMessage).filter(
        ChatMessage.case_id == case_id
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

    return list(reversed(messages))


@router.delete("/{case_id}/chat/history")
def delete_chat_history(case_id: int, db: Session = Depends(get_db)):
    """清空案件的所有聊天历史"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 删除该案件的所有聊天消息
    deleted_count = db.query(ChatMessage).filter(
        ChatMessage.case_id == case_id
    ).delete()
    db.commit()

    return {"deleted": deleted_count, "message": "聊天历史已清空"}


# ============ 新增 API ============

class AskQuestion(BaseModel):
    question: str = Field(..., min_length=1)  # 无字数限制，支持深度分析
    doc_ids: Optional[List[int]] = None  # 可指定分析的文档


class EvidenceSuggestionsRequest(BaseModel):
    focus_area: Optional[str] = None


@router.post("/{case_id}/ask")
def ask_case_question(case_id: int, data: AskQuestion, db: Session = Depends(get_db)):
    """针对案件向 AI 提问"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 构建完整案件信息（包含补充说明）
    case_info = f"""【案件基本信息】
案件名称：{case.title}
案件类型：{case.case_type}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}
案由：{case.cause or '未填写'}
诉讼金额：{case.claim_amount or '未填写'}
案件描述：{case.description or '未填写'}
补充说明：{case.supplement or '无'}"""

    # 获取案件中的所有文档/函件列表
    documents = db.query(Document).filter(Document.case_id == case_id).all()
    doc_list = []
    for doc in documents:
        doc_type = doc.doc_type or '其他'
        doc_list.append({
            "name": doc.filename,
            "type": doc_type,
            "has_content": bool(doc.content)
        })
    
    # 格式化文档列表供 AI 查看
    doc_list_display = "\n".join([f"{i+1}. 【{d['name']}】（类型：{d['type']}）" 
                                   for i, d in enumerate(doc_list)]) if doc_list else "（案件中暂无上传的文档）"

    # 获取对话历史（最近10轮）
    history = db.query(ChatMessage).filter(
        ChatMessage.case_id == case_id
    ).order_by(ChatMessage.created_at.desc()).limit(20).all()
    history = list(reversed(history))[-10:] if history else []

    # 构建对话历史字符串
    history_str = ""
    for msg in history:
        role = "用户" if msg.role == "user" else "AI助手"
        content = msg.content  # 完整内容，不截断
        history_str += f"\n{role}：{content}"
    if not history_str:
        history_str = "（首次对话，无历史记录）"

    # 获取相关文档内容
    # 如果指定了 doc_ids，只获取这些文档；否则获取所有文档
    if data.doc_ids:
        docs_to_analyze = [doc for doc in documents if doc.id in data.doc_ids]
        doc_list_display = "\n".join([f"{i+1}. 【{d.filename}】（类型：{d.doc_type or '其他'}）" 
                                      for i, d in enumerate(docs_to_analyze)]) if docs_to_analyze else "（未找到指定的文档）"
    else:
        docs_to_analyze = documents
        doc_list_display = "\n".join([f"{i+1}. 【{d.filename}】（类型：{d.doc_type or '其他'}）" 
                                      for i, d in enumerate(docs_to_analyze)]) if docs_to_analyze else "（案件中暂无上传的文档）"
    
    context_parts = []
    failed_docs = []
    empty_docs = []
    for idx, doc in enumerate(docs_to_analyze):
        if doc.content:
            content_lower = doc.content.lower()
            is_failed = any([
                content_lower.startswith("[pdf 解析失败]"),
                content_lower.startswith("[扫描件 pdf]"),
                content_lower.startswith("pdf 解析失败"),
                content_lower.startswith("pdf 解析需要"),
                content_lower.startswith("不支持的文件类型"),
                content_lower.startswith("图片识别失败"),
                content_lower.startswith("图片 ocr"),
                content_lower.startswith("word 解析失败"),
                content_lower.startswith("文本解析失败"),
                "内容解析待处理" in content_lower,
                "内容解析失败" in content_lower,
                "需要安装" in content_lower,
            ])
            if is_failed:
                failed_docs.append({
                    "name": doc.filename,
                    "error": doc.content[:200]
                })
                continue
            doc_type = doc.doc_type or '其他'
            context_parts.append(f"\n\n【文档{idx+1}：{doc.filename}】（类型：{doc_type}）\n{doc.content}")
        else:
            # 文档没有内容（可能文件已丢失或从未正确上传）
            empty_docs.append(doc.filename)
    context = "".join(context_parts)

    # 构建空文档警告
    empty_docs_warning = ""
    if empty_docs:
        empty_docs_warning = "\n\n【⚠️ 重要警告 - 文档内容为空】\n"
        empty_docs_warning += "以下文档的原始文件可能已丢失或从未正确上传内容：\n"
        for name in empty_docs:
            empty_docs_warning += f"  - {name}\n"
        empty_docs_warning += "\n**请重新上传这些文档。**\n"

    # 构建失败文档警告
    failed_docs_warning = ""
    if failed_docs:
        failed_docs_warning = "\n\n【⚠️ 重要警告 - 部分文档解析失败】\n"
        for fd in failed_docs:
            failed_docs_warning += f"""
📄 文档：{fd['name']}
❌ 状态：{fd['error']}

"""
        failed_docs_warning += """【强制执行规则】
当用户要求分析上述文档时，您必须：
1. 明确告知用户该文档无法被系统解析
2. 说明具体原因（扫描件、加密、损坏等）
3. 提供解决建议：
   - 如为扫描件，建议用户上传文字版 PDF 或使用图片格式
   - 如为加密文档，建议解密后重新上传
   - 如为损坏文件，建议重新上传
4. 禁止基于文档名称或猜测内容进行任何分析
5. 禁止给出任何法律建议，因为缺乏基础材料

【正确的回复示例】
"抱歉，我无法分析该文档。该文档为扫描件 PDF，系统无法直接提取其中的文字内容。

建议您：
1. 如有原始文字版本，请上传文字版 PDF
2. 如必须使用扫描件，请将每一页单独保存为图片（JPG/PNG）后上传
3. 或者在问题中直接粘贴文档的关键文字内容，我再为您分析"
"""

    # 构建文档名称映射（用于 AI 匹配）
    doc_names_str = "\n".join([f"- \"{d.filename}\"" for d in documents]) if documents else "无"

    # 检测问题类型，决定使用哪种提示词模板
    question_lower = data.question.lower()
    
    # 如果指定了 doc_ids，强制使用文档分析模式并只分析这些文档
    has_selected_docs = bool(data.doc_ids)
    
    is_document_analysis = has_selected_docs or any(kw in question_lower for kw in [
        "分析", "解读", "这份函", "这份文件", "这封", "什么意思",
        "目的", "企图", "建议", "如何应对", "怎么回复", "如何回复",
        "逐条", "逐项", "法律依据", "条款"
    ])

    # 构建文档分析专用的强化提示词
    if is_document_analysis:
        # 统计有效文档数量
        if has_selected_docs:
            valid_docs = [doc for doc in docs_to_analyze if doc.content and not any(
                doc.content.lower().startswith(prefix) for prefix in [
                    "[pdf 解析失败]", "[扫描件 pdf]", "pdf 解析失败", "pdf 解析需要",
                    "不支持的文件类型", "图片识别失败", "图片 ocr", "word 解析失败", "文本解析失败"
                ]
            )]
        else:
            valid_docs = [doc for doc in documents if doc.content and not any(
                doc.content.lower().startswith(prefix) for prefix in [
                    "[pdf 解析失败]", "[扫描件 pdf]", "pdf 解析失败", "pdf 解析需要",
                    "不支持的文件类型", "图片识别失败", "图片 ocr", "word 解析失败", "文本解析失败"
                ]
            )]
        doc_count = len(valid_docs)
        
        analysis_prompt = f"""【任务】分析所有 {doc_count} 份函件文件，逐一给出法律意见。

【身份】你是执业律师，代理甲方。与用户进行专业讨论。

【案件基本信息 - 请务必记住】
{case_info}

【重要：对话历史 - 请务必参考之前的对话】
{history_str if history_str != '（首次对话，无历史记录）' else '（首次对话，这是第一轮交流）'}

【必须分析的所有文档清单】
{doc_list_display}

【所有文档完整内容】
{context if context else '（无文档内容）'}
{empty_docs_warning if empty_docs_warning else ''}
{failed_docs_warning if failed_docs_warning else ''}

【用户问题】
{data.question}

【核心要求 - 绝对禁止偷懒】
🚨 您必须对 {doc_count} 份文档中的【每一份】进行【完整】分析！
- 禁止只分析第一份文档就结束
- 禁止只分析部分条款就总结
- 必须逐文档、逐条款完整分析

【重要：对话历史】
请务必参考上方的【对话历史】，如果这是追问或延续之前的话题，必须：
1. 明确引用"根据我们之前的讨论..."
2. 结合之前的分析结论进行深入
3. 不要从头开始分析已经讨论过的内容

【输出格式】

## 一、发函主体（每份文档都要分析）
【文档1：文件名】
- 发函主体身份：
- 利益诉求：
- 与本案关系：

【文档2：文件名】
（如有更多文档，依次类推...）

## 二、【文档1】逐条分析
【条款1】原文：... | 法律性质：... | 分析：... | 法律依据：...
【条款2】原文：... | 法律性质：... | 分析：... | 法律依据：...
（必须列出所有条款）

## 三、【文档2】逐条分析
（如有更多文档，依次类推...）

## 四、文档间的关联与陷阱分析
⚠️ 分析多份文档之间是否存在：
- 相互矛盾的内容
- 设置的陷阱/圈套
- 证据链的完整性
- 对方的整体策略

## 五、综合风险评估
接受的风险：
拒绝的风险：

## 六、综合应对建议（针对每份文档）
【文档1】建议：...
【文档2】建议：...

## 七、法律条款汇总
（必须准确，禁止编造）

【讨论机制 - 主动参与】
✅ 您的职责不仅是回答问题，还要主动参与讨论：
1. 如发现用户观点有误，主动提出异议并说明理由
2. 如发现遗漏的重要条款，主动补充分析
3. 如发现潜在风险，主动警示
4. 可以反问用户："您是否考虑过...？" "关于这一点，您的判断依据是...？"
5. 如与用户观点不一致，据理力争，但保持专业态度

【强制规则】
1. 必须对所有 {doc_count} 份文档逐一分析，禁止遗漏
2. 每条分析必须有具体法律依据，禁止笼统表述
3. 禁止使用"建议咨询专业律师"等废话
4. 禁止基于猜测而非原文内容分析
5. 如发现问题或矛盾，必须主动指出

请对所有 {doc_count} 份文档进行完整逐条分析："""

    # 后续处理 - 在回答末尾添加文书建议提示
    # 注意：AI回答本身会包含文书建议格式
    else:
        # 通用问答提示词 - 支持追问、反驳、讨论
        analysis_prompt = f"""【角色】您是执业律师，代理甲方。用户是当事人。您需要与用户进行专业、热烈的法律讨论。

【案件基本信息 - 请务必记住】
{case_info}

【重要：对话历史 - 请务必参考之前的对话】
{history_str if history_str != '（首次对话，无历史记录）' else '（首次对话，这是第一轮交流）'}

【案件文档清单】
{doc_list_display if doc_list_display else "（案件中暂无上传的文档）"}

【相关材料内容】
{context if context else '（无文档内容）'}
{empty_docs_warning if empty_docs_warning else ''}
{failed_docs_warning if failed_docs_warning else ''}

【用户当前问题/观点】
{data.question}

【核心职责 - 讨论而非敷衍】
🔥 请务必参考上方【对话历史】，因为这是用户与您之前的交流内容！
您的职责是：
1. 【记住历史】如果用户提到"之前"、"上面"、或追问之前讨论的内容，必须准确引用对话历史中的信息
2. 【上下文连贯】如果用户的问题是对之前讨论的延续或追问，必须结合之前的对话内容回答
3. 如果用户观点正确，给予肯定并深化分析
4. 如果用户观点有误，【必须明确指出并反驳】，不能含糊其辞
5. 如果用户遗漏了重要因素，主动补充说明
6. 如有新发现的风险或机会，主动提示用户
7. 可以反问用户："您是否考虑过...？" "关于这一点，您怎么看？"
8. 如发现文档中有相关内容未提及，主动引用分析

【回答要求】
1. 基于文档内容和对话历史回答，明确引用文件名（用《》标注）
2. 如果用户的问题是追问，必须明确说明"根据我们之前的讨论..."
3. 给出具体的、可操作的法律建议
4. 禁止使用"建议您咨询专业律师"、"具体情况具体分析"等废话
5. 【禁止敷衍】回答必须详尽、有深度，禁止一句话带过

【禁止事项】
❌ "这个情况比较复杂，建议咨询专业律师"
❌ "需要综合考虑各种因素"
❌ 只回答一句话就结束
❌ 完全忽略对话历史，从头开始分析

【重要：文书建议】
当分析完毕后，请根据案件情况，在回答末尾添加文书建议。必须使用以下固定格式：

---
## 📄 下一步文书建议

根据以上分析，建议您考虑生成以下文书（可直接点击生成）：

🎯 **[文书类型名称]**
   说明：简要说明文书的用途
   优先级：高/中/低

🎯 **[另一文书类型名称]**
   说明：简要说明文书的用途
   优先级：高/中/低

---
💡 **使用说明**：点击上方【文书类型名称】可与AI进一步沟通完善后生成对应文书

请进行深入讨论："""

    # 调用 LLM
    try:
        # 法律分析使用 qwen-plus 增强推理能力
        response = llm_service.chat([
            {"role": "system", "content": f"你是一位专业的法律AI助手。请严格按照用户要求，准确回答法律问题。\n\n【当前日期信息】\n- 当前日期：{CURRENT_DATE}\n- 当前年份：{CURRENT_YEAR}年\n在分析时效问题、期限计算时，请务必使用上述当前日期。"},
            {"role": "user", "content": analysis_prompt}
        ], model="qwen-plus")

        # 保存对话消息到数据库
        user_msg = ChatMessage(
            case_id=case_id,
            role="user",
            content=data.question
        )
        db.add(user_msg)

        assistant_msg = ChatMessage(
            case_id=case_id,
            role="assistant",
            content=response
        )
        db.add(assistant_msg)
        db.commit()

        return {"answer": response}
    except Exception as e:
        import traceback
        print(f"Error in ask_case_question: {traceback.format_exc()}")
        return {"answer": f"处理您的问题时出现错误，请稍后重试。错误信息：{str(e)}"}


@router.post("/{case_id}/evidence-suggestions")
def get_evidence_suggestions(case_id: int, db: Session = Depends(get_db)):
    """获取证据链补充建议"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 构建案件信息
    case_info = f"""案件名称：{case.title}
案件类型：{case.case_type}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}
案由：{case.cause or '未填写'}
诉讼金额：{case.claim_amount or '未填写'}
案件描述：{case.description or '未填写'}
补充说明：{case.supplement or '无'}"""

    # 获取已有分析
    analysis = case.legal_analysis or "暂无"

    # 构建提示词
    prompt = f"""基于以下案件信息和已有分析，针对案件发展方向，提供详细的证据链补充建议。

【案件信息】
{case_info}

【已有分析】
{analysis}

请提供以下方面的证据补充建议：
1. **现有证据评估**：分析现有证据的充分性和证明力
2. **缺失证据清单**：列出需要补充的关键证据
3. **证据收集方法**：说明如何获取这些证据（调查取证、申请法院调取、证人证言等）
4. **证据链完善建议**：如何形成完整的证据链条
5. **风险提示**：证据不足可能带来的风险

请用清晰的格式输出建议。"""

    # 调用 LLM (使用 qwen-plus 增强推理)
    try:
        suggestions = llm_service.chat([
            {"role": "system", "content": f"你是一位专业的诉讼证据顾问，擅长分析案件证据需求并提供收集建议。\n\n【当前日期信息】\n- 当前日期：{CURRENT_DATE}\n- 当前年份：{CURRENT_YEAR}年\n在分析时效问题、期限计算时，请务必使用上述当前日期。"},
            {"role": "user", "content": prompt}
        ], model="qwen-plus", timeout=30)
    except Exception as e:
        print(f"LLM调用失败: {e}")
        # 返回基于已有证据的建议 - 从 Document 表中查询证据
        docs = db.query(Document).filter(Document.case_id == case_id).all()
        evidence_count = len([d for d in docs if d.doc_type and (
            d.doc_type.lower().startswith("证据") or
            "合同" in d.doc_type or
            "函件" in d.doc_type or
            "章程" in d.doc_type or
            "协议" in d.doc_type
        )])

        # 根据案件类型提供不同建议
        case_type = case.case_type or "合同纠纷"
        base_suggestions = ""

        if "劳动" in case_type:
            base_suggestions = """
**1. 劳动关系证据建议：**
- 劳动合同原件
- 工资条、银行流水（证明工资标准）
- 社保缴纳记录
- 考勤记录
- 工作证、工牌等身份证明

**2. 纠纷相关证据：**
- 解除/终止劳动合同通知书
- 违法解除的证据材料
- 离职交接单"""
        elif "侵权" in case_type or "损害" in case_type:
            base_suggestions = """
**1. 侵权事实证据建议：**
- 侵权行为的具体描述和证据
- 损害后果的证明材料（医疗记录、财产损失评估等）
- 因果关系证明
- 过错证据

**2. 赔偿相关证据：**
- 医疗费用票据
- 误工证明
- 伤残鉴定报告"""
        else:
            base_suggestions = """
**1. 合同协议类证据建议：**
- 合同原件及附件
- 合同签订过程中的沟通记录
- 合同履行过程中的相关凭证
- 对方违约的证据材料

**2. 基础证据收集：**
- 整理现有全部书面材料
- 保存相关微信、邮件沟通记录
- 如涉及款项往来，整理银行转账记录"""

        suggestions = f"""【基于案件分析的证据建议】

案件类型：{case_type}
现有证据数量: {evidence_count} 项

由于AI服务暂时不可用，以下是基于案件类型的基础建议：
{base_suggestions}

**3. 下一步建议：**
- 详细整理已有证据材料
- 梳理案件时间线
- 标记关键证据及缺失证据
- 必要时可申请法院调查取证"""

    return {"suggestions": suggestions}


# ============ 案件线索 API ============

class CaseThreadCreate(BaseModel):
    """创建线索请求"""
    name: str = Field(..., min_length=1)
    cause: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None
    status: Optional[str] = "active"


class CaseThreadUpdate(BaseModel):
    """更新线索请求"""
    name: Optional[str] = Field(default=None, min_length=1)
    cause: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None
    status: Optional[str] = None
    evidence_summary: Optional[str] = None


class CaseThreadItemResponse(BaseModel):
    id: int
    name: str
    cause: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None
    status: Optional[str] = None
    evidence_summary: Optional[str] = None
    related_thread_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CasePartyItemResponse(BaseModel):
    id: int
    name: str
    party_type: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_relation: Optional[str] = None
    relation_to_case: Optional[str] = None
    created_at: Optional[str] = None


class CaseCounterClaimItemResponse(BaseModel):
    id: int
    title: str
    claim_type: Optional[str] = None
    amount: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None


class CaseMessageResponse(BaseModel):
    message: str


@router.post("/{case_id}/threads", response_model=CaseThreadItemResponse)
def create_thread(case_id: int, thread_data: CaseThreadCreate, db: Session = Depends(get_db)):
    """创建案件线索"""
    # 检查案件是否存在
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 转换状态枚举
    status_enum = ThreadStatus.ACTIVE
    if thread_data.status:
        try:
            status_enum = ThreadStatus(thread_data.status)
        except (ValueError, TypeError):
            pass

    db_thread = CaseThread(
        case_id=case_id,
        name=thread_data.name,
        cause=thread_data.cause,
        description=thread_data.description,
        amount=thread_data.amount,
        status=status_enum
    )
    db.add(db_thread)
    db.commit()
    db.refresh(db_thread)

    return {
        "id": db_thread.id,
        "name": db_thread.name,
        "cause": db_thread.cause,
        "description": db_thread.description,
        "amount": db_thread.amount,
        "status": db_thread.status.value if hasattr(db_thread.status, 'value') else str(db_thread.status),
        "created_at": db_thread.created_at.isoformat() if db_thread.created_at else None
    }


@router.get("/{case_id}/threads", response_model=List[CaseThreadItemResponse])
def list_threads(case_id: int, db: Session = Depends(get_db)):
    """获取案件的所有线索"""
    threads = db.query(CaseThread).filter(
        CaseThread.case_id == case_id
    ).order_by(CaseThread.sort_order, CaseThread.created_at.desc()).all()

    return [{
        "id": t.id,
        "name": t.name,
        "cause": t.cause,
        "description": t.description,
        "amount": t.amount,
        "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
        "evidence_summary": t.evidence_summary,
        "related_thread_id": t.related_thread_id,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None
    } for t in threads]


@router.put("/{case_id}/threads/{thread_id}", response_model=CaseThreadItemResponse)
def update_thread(case_id: int, thread_id: int, thread_data: CaseThreadUpdate, db: Session = Depends(get_db)):
    """更新线索"""
    thread = db.query(CaseThread).filter(
        CaseThread.id == thread_id,
        CaseThread.case_id == case_id
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail="线索不存在")

    update_dict = thread_data.dict(exclude_unset=True)

    # 处理状态转换
    if "status" in update_dict and update_dict["status"]:
        try:
            update_dict["status"] = ThreadStatus(update_dict["status"])
        except (ValueError, TypeError):
            pass

    for key, value in update_dict.items():
        setattr(thread, key, value)

    db.commit()
    db.refresh(thread)

    return {
        "id": thread.id,
        "name": thread.name,
        "cause": thread.cause,
        "description": thread.description,
        "amount": thread.amount,
        "status": thread.status.value if hasattr(thread.status, 'value') else str(thread.status),
        "evidence_summary": thread.evidence_summary
    }


@router.delete("/{case_id}/threads/{thread_id}", response_model=CaseMessageResponse)
def delete_thread(case_id: int, thread_id: int, db: Session = Depends(get_db)):
    """删除线索"""
    thread = db.query(CaseThread).filter(
        CaseThread.id == thread_id,
        CaseThread.case_id == case_id
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail="线索不存在")

    db.delete(thread)
    db.commit()

    return {"message": "线索已删除"}


# ============ 当事人 API ============

class PartyCreate(BaseModel):
    """创建当事人请求"""
    name: str
    party_type: Optional[str] = "个人"
    role: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_relation: Optional[str] = None
    relation_to_case: Optional[str] = None


class PartyUpdate(BaseModel):
    """更新当事人请求"""
    name: Optional[str] = None
    party_type: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_relation: Optional[str] = None
    relation_to_case: Optional[str] = None


@router.post("/{case_id}/parties", response_model=CasePartyItemResponse)
def create_party(case_id: int, party_data: PartyCreate, db: Session = Depends(get_db)):
    """创建当事人"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 转换角色枚举
    role_enum = PartyRole.PLAINTIFF
    if party_data.role:
        try:
            role_enum = PartyRole(party_data.role)
        except (ValueError, TypeError):
            pass

    db_party = Party(
        case_id=case_id,
        name=party_data.name,
        party_type=party_data.party_type,
        role=role_enum,
        phone=party_data.phone,
        email=party_data.email,
        address=party_data.address,
        agent_name=party_data.agent_name,
        agent_phone=party_data.agent_phone,
        agent_relation=party_data.agent_relation,
        relation_to_case=party_data.relation_to_case
    )
    db.add(db_party)
    db.commit()
    db.refresh(db_party)

    return {
        "id": db_party.id,
        "name": db_party.name,
        "party_type": db_party.party_type,
        "role": db_party.role.value if hasattr(db_party.role, 'value') else str(db_party.role),
        "phone": db_party.phone,
        "email": db_party.email,
        "address": db_party.address,
        "agent_name": db_party.agent_name,
        "agent_phone": db_party.agent_phone,
        "agent_relation": db_party.agent_relation,
        "relation_to_case": db_party.relation_to_case,
        "created_at": db_party.created_at.isoformat() if db_party.created_at else None
    }


@router.get("/{case_id}/parties", response_model=List[CasePartyItemResponse])
def list_parties(case_id: int, db: Session = Depends(get_db)):
    """获取案件的所有当事人"""
    parties = db.query(Party).filter(
        Party.case_id == case_id
    ).order_by(Party.sort_order, Party.created_at.desc()).all()

    return [{
        "id": p.id,
        "name": p.name,
        "party_type": p.party_type,
        "role": p.role.value if hasattr(p.role, 'value') else str(p.role),
        "phone": p.phone,
        "email": p.email,
        "address": p.address,
        "agent_name": p.agent_name,
        "agent_phone": p.agent_phone,
        "agent_relation": p.agent_relation,
        "relation_to_case": p.relation_to_case,
        "created_at": p.created_at.isoformat() if p.created_at else None
    } for p in parties]


@router.put("/{case_id}/parties/{party_id}", response_model=CasePartyItemResponse)
def update_party(case_id: int, party_id: int, party_data: PartyUpdate, db: Session = Depends(get_db)):
    """更新当事人"""
    party = db.query(Party).filter(
        Party.id == party_id,
        Party.case_id == case_id
    ).first()

    if not party:
        raise HTTPException(status_code=404, detail="当事人不存在")

    update_dict = party_data.dict(exclude_unset=True)

    # 处理角色转换
    if "role" in update_dict and update_dict["role"]:
        try:
            update_dict["role"] = PartyRole(update_dict["role"])
        except (ValueError, TypeError):
            pass

    for key, value in update_dict.items():
        setattr(party, key, value)

    db.commit()
    db.refresh(party)

    return {
        "id": party.id,
        "name": party.name,
        "party_type": party.party_type,
        "role": party.role.value if hasattr(party.role, 'value') else str(party.role),
        "phone": party.phone,
        "email": party.email,
        "address": party.address
    }


@router.delete("/{case_id}/parties/{party_id}", response_model=CaseMessageResponse)
def delete_party(case_id: int, party_id: int, db: Session = Depends(get_db)):
    """删除当事人"""
    party = db.query(Party).filter(
        Party.id == party_id,
        Party.case_id == case_id
    ).first()

    if not party:
        raise HTTPException(status_code=404, detail="当事人不存在")

    db.delete(party)
    db.commit()

    return {"message": "当事人已删除"}


# ============ 反诉/追加请求 API ============

class CounterClaimCreate(BaseModel):
    """创建反诉请求"""
    title: str
    claim_type: Optional[str] = None
    amount: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "pending"


class CounterClaimUpdate(BaseModel):
    """更新反诉请求"""
    title: Optional[str] = None
    claim_type: Optional[str] = None
    amount: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


@router.post("/{case_id}/counter-claims", response_model=CaseCounterClaimItemResponse)
def create_counter_claim(case_id: int, claim_data: CounterClaimCreate, db: Session = Depends(get_db)):
    """创建反诉/追加请求"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    db_claim = CounterClaim(
        case_id=case_id,
        title=claim_data.title,
        claim_type=claim_data.claim_type,
        amount=claim_data.amount,
        description=claim_data.description,
        status=claim_data.status or "pending"
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)

    return {
        "id": db_claim.id,
        "title": db_claim.title,
        "claim_type": db_claim.claim_type,
        "amount": db_claim.amount,
        "description": db_claim.description,
        "status": db_claim.status,
        "created_at": db_claim.created_at.isoformat() if db_claim.created_at else None
    }


@router.get("/{case_id}/counter-claims", response_model=List[CaseCounterClaimItemResponse])
def list_counter_claims(case_id: int, db: Session = Depends(get_db)):
    """获取案件的所有反诉/追加请求"""
    claims = db.query(CounterClaim).filter(
        CounterClaim.case_id == case_id
    ).order_by(CounterClaim.created_at.desc()).all()

    return [{
        "id": c.id,
        "title": c.title,
        "claim_type": c.claim_type,
        "amount": c.amount,
        "description": c.description,
        "status": c.status,
        "created_at": c.created_at.isoformat() if c.created_at else None
    } for c in claims]


@router.put("/{case_id}/counter-claims/{claim_id}", response_model=CaseCounterClaimItemResponse)
def update_counter_claim(case_id: int, claim_id: int, claim_data: CounterClaimUpdate, db: Session = Depends(get_db)):
    """更新反诉/追加请求"""
    claim = db.query(CounterClaim).filter(
        CounterClaim.id == claim_id,
        CounterClaim.case_id == case_id
    ).first()

    if not claim:
        raise HTTPException(status_code=404, detail="反诉不存在")

    update_dict = claim_data.dict(exclude_unset=True)

    for key, value in update_dict.items():
        setattr(claim, key, value)

    db.commit()
    db.refresh(claim)

    return {
        "id": claim.id,
        "title": claim.title,
        "claim_type": claim.claim_type,
        "amount": claim.amount,
        "description": claim.description,
        "status": claim.status
    }


@router.delete("/{case_id}/counter-claims/{claim_id}", response_model=CaseMessageResponse)
def delete_counter_claim(case_id: int, claim_id: int, db: Session = Depends(get_db)):
    """删除反诉/追加请求"""
    claim = db.query(CounterClaim).filter(
        CounterClaim.id == claim_id,
        CounterClaim.case_id == case_id
    ).first()

    if not claim:
        raise HTTPException(status_code=404, detail="反诉不存在")

    db.delete(claim)
    db.commit()

    return {"message": "反诉已删除"}


# ============ 自动分析机制 ============

class SupplementRequest(BaseModel):
    """补充资料请求"""
    content: str = Field(..., min_length=1)  # 无字数限制
    title: Optional[str] = None  # 补充标题
    auto_analyze: bool = True  # 是否自动分析


class AutoAnalysisResponse(BaseModel):
    """自动分析响应"""
    node_id: int
    key_points: str
    analysis_result: str
    action_suggestions: str
    affects_direction: bool
    direction_change: Optional[str]
    needs_full_reanalysis: bool


async def analyze_new_content(case_id: int, content: str, title: str, db: Session) -> dict:
    """
    AI分析新增内容，提炼关键要点，评估对案件方向的影响
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return None

    # 构建上下文
    context = f"""【案件基本信息】
案件名称：{case.title}
案件类型：{case.case_type}
案由：{case.cause or '未填写'}
诉讼金额：{case.claim_amount or '未填写'}

【现有分析摘要】
{case.legal_analysis if case.legal_analysis else '暂无'}

【补充的新内容】
{content}
"""

    prompt = f"""请分析以下新增内容，提炼关键要点并评估对案件的影响。

{context}

请以JSON格式返回分析结果：
{{
    "key_points": "提炼的关键要点（3-5条）",
    "analysis_result": "对该内容的详细分析",
    "action_suggestions": "后续建议行动（3-5条）",
    "affects_direction": true/false,  // 是否影响案件方向
    "direction_change": "如果影响案件方向，说明具体变化"  // 如果不影响则为空
}}

只返回JSON，不要其他内容。"""

    try:
        result = llm_service.chat([
            {"role": "system", "content": f"你是一位专业的诉讼律师助理，擅长分析案件资料并提供建议。\n\n【当前日期信息】\n- 当前日期：{CURRENT_DATE}\n- 当前年份：{CURRENT_YEAR}年\n在分析时效问题、期限计算时，请务必使用上述当前日期。"},
            {"role": "user", "content": prompt}
        ], model="qwen-plus", timeout=60)

        # 尝试解析JSON
        import json
        import re
        json_match = re.search(r'\{[^{}]*"key_points"[^{}]*\}[^{}]*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # 尝试直接解析
            for line in result.split('\n'):
                if line.strip().startswith('{') or line.strip().startswith('{'):
                    try:
                        return json.loads(line)
                    except:
                        pass
    except Exception as e:
        print(f"自动分析失败: {e}")

    # 默认返回值
    return {
        "key_points": "内容已记录，待详细分析",
        "analysis_result": "需要结合案件整体情况进行深入分析",
        "action_suggestions": "建议手动触发全面分析",
        "affects_direction": False,
        "direction_change": None
    }


@router.post("/{case_id}/supplement", response_model=AutoAnalysisResponse)
async def add_supplement(case_id: int, request: SupplementRequest, db: Session = Depends(get_db)):
    """
    添加案件补充说明，自动分析并创建节点
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 记录旧的分析结果（用于判断是否需要重新分析）
    old_analysis = case.legal_analysis

    # 如果有补充内容，更新案件
    if request.content:
        old_supplement = case.supplement or ""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        case.supplement = f"{old_supplement}\n\n[{timestamp}] {request.content}".strip()

    # 创建节点记录
    node = CaseNode(
        case_id=case_id,
        node_type="supplement",
        title=request.title or f"补充说明 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        content=request.content,
        status="pending"
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    # 自动分析
    if request.auto_analyze:
        analysis = await analyze_new_content(case_id, request.content, request.title, db)

        # 更新节点
        node.key_points = analysis.get("key_points", "")
        node.analysis_result = analysis.get("analysis_result", "")
        node.action_suggestions = analysis.get("action_suggestions", "")
        node.affects_direction = analysis.get("affects_direction", False)
        node.direction_change = analysis.get("direction_change")
        node.status = "processed"

        # 判断是否需要全面重新分析
        needs_reanalysis = analysis.get("affects_direction", False)

        db.commit()

        # 如果影响案件方向，清理旧分析
        if needs_reanalysis:
            case.legal_analysis = None
            case.strategy_suggestion = None
            # 清理对话历史
            db.query(ChatMessage).filter(ChatMessage.case_id == case_id).delete()
            db.commit()

        return AutoAnalysisResponse(
            node_id=node.id,
            key_points=node.key_points or "",
            analysis_result=node.analysis_result or "",
            action_suggestions=node.action_suggestions or "",
            affects_direction=node.affects_direction,
            direction_change=node.direction_change,
            needs_full_reanalysis=needs_reanalysis
        )

    db.commit()
    return AutoAnalysisResponse(
        node_id=node.id,
        key_points="",
        analysis_result="",
        action_suggestions="",
        affects_direction=False,
        direction_change=None,
        needs_full_reanalysis=False
    )


@router.post("/{case_id}/document-analyzed/{document_id}", response_model=AutoAnalysisResponse)
async def analyze_uploaded_document(case_id: int, document_id: int, db: Session = Depends(get_db)):
    """
    分析上传的文档，自动提炼要点并创建节点
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.case_id == case_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 提取文档内容
    content = document.content or ""
    if not content and document.stored_path:
        try:
            with open(document.stored_path, 'r', encoding='utf-8') as f:
                content = f.read()  # 读取完整内容
        except:
            content = f"文档: {document.filename}"

    # 创建节点
    node = CaseNode(
        case_id=case_id,
        node_type="upload",
        title=f"上传文档: {document.filename}",
        content=content,
        related_document_ids=[document_id],
        status="pending"
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    # 自动分析
    analysis = await analyze_new_content(case_id, content, node.title, db)

    # 更新节点
    node.key_points = analysis.get("key_points", "")
    node.analysis_result = analysis.get("analysis_result", "")
    node.action_suggestions = analysis.get("action_suggestions", "")
    node.affects_direction = analysis.get("affects_direction", False)
    node.direction_change = analysis.get("direction_change")
    node.status = "processed"

    # 判断是否需要全面重新分析
    needs_reanalysis = analysis.get("affects_direction", False)

    # 如果影响案件方向，清理旧分析
    if needs_reanalysis:
        case.legal_analysis = None
        case.strategy_suggestion = None
        db.query(ChatMessage).filter(ChatMessage.case_id == case_id).delete()
        db.commit()

    db.commit()

    return AutoAnalysisResponse(
        node_id=node.id,
        key_points=node.key_points or "",
        analysis_result=node.analysis_result or "",
        action_suggestions=node.action_suggestions or "",
        affects_direction=node.affects_direction,
        direction_change=node.direction_change,
        needs_full_reanalysis=needs_reanalysis
    )


@router.get("/{case_id}/nodes")
def list_case_nodes(case_id: int, db: Session = Depends(get_db)):
    """获取案件的所有节点"""
    nodes = db.query(CaseNode).filter(
        CaseNode.case_id == case_id
    ).order_by(CaseNode.created_at.desc()).all()

    return [{
        "id": n.id,
        "node_type": n.node_type,
        "title": n.title,
        "description": n.description,
        "content": n.content,
        "key_points": n.key_points,
        "analysis_result": n.analysis_result,
        "action_suggestions": n.action_suggestions,
        "status": n.status,
        "affects_direction": n.affects_direction,
        "direction_change": n.direction_change,
        "created_at": n.created_at.isoformat() if n.created_at else None
    } for n in nodes]


@router.get("/{case_id}/nodes/{node_id}")
def get_case_node(case_id: int, node_id: int, db: Session = Depends(get_db)):
    """获取指定节点详情"""
    node = db.query(CaseNode).filter(
        CaseNode.id == node_id,
        CaseNode.case_id == case_id
    ).first()

    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    return {
        "id": node.id,
        "node_type": node.node_type,
        "title": node.title,
        "description": node.description,
        "content": node.content,
        "key_points": node.key_points,
        "analysis_result": node.analysis_result,
        "action_suggestions": node.action_suggestions,
        "status": node.status,
        "affects_direction": node.affects_direction,
        "direction_change": node.direction_change,
        "created_at": node.created_at.isoformat() if node.created_at else None
    }
