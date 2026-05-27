"""
上诉流程 API - 第二审程序的完整流程管理
包括：上诉记录 CRUD、上诉论点、上诉期限、上诉材料、二审策略、上诉状生成
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.db.database import get_db
from app.services.appeal_service import appeal_service

router = APIRouter(prefix="/api/appeal", tags=["上诉追踪"])


# ============ 请求模型 ============

class AppealCreateRequest(BaseModel):
    """创建上诉记录请求"""
    appeal_type: str = "first_to_second"
    appeal_reason: str = "legal_error"
    original_case_number: Optional[str] = None
    original_court: Optional[str] = None
    original_judge: Optional[str] = None
    original_judgment_date: Optional[str] = None
    original_judgment_content: Optional[str] = None
    appellant_type: Optional[str] = None
    appellant_name: Optional[str] = None
    judgment_received_date: Optional[str] = None
    appeal_facts: Optional[str] = None
    new_evidence_list: Optional[str] = None
    original_evidence_used: Optional[str] = None
    appeal_requests: Optional[str] = None
    original_requests: Optional[str] = None
    modified_requests: Optional[str] = None
    grounds_of_appeal: Optional[dict] = None
    opposing_arguments: Optional[str] = None
    key_disputes: Optional[dict] = None
    strategy: Optional[str] = None
    key_arguments: Optional[dict] = None
    evidence_plan: Optional[dict] = None
    milestones: Optional[dict] = None


class AppealUpdateRequest(BaseModel):
    """更新上诉记录请求"""
    appeal_type: Optional[str] = None
    appeal_reason: Optional[str] = None
    original_case_number: Optional[str] = None
    original_court: Optional[str] = None
    original_judge: Optional[str] = None
    original_judgment_date: Optional[str] = None
    original_judgment_content: Optional[str] = None
    appellant_type: Optional[str] = None
    appellant_name: Optional[str] = None
    judgment_received_date: Optional[str] = None
    appeal_submitted_date: Optional[str] = None
    appeal_accepted_date: Optional[str] = None
    hearing_date: Optional[str] = None
    appeal_decision_date: Optional[str] = None
    status: Optional[str] = None
    appeal_petition: Optional[str] = None
    appeal_facts: Optional[str] = None
    new_evidence_list: Optional[str] = None
    original_evidence_used: Optional[str] = None
    appeal_requests: Optional[str] = None
    original_requests: Optional[str] = None
    modified_requests: Optional[str] = None
    grounds_of_appeal: Optional[dict] = None
    opposing_arguments: Optional[str] = None
    key_disputes: Optional[dict] = None
    strategy: Optional[str] = None
    key_arguments: Optional[dict] = None
    evidence_plan: Optional[dict] = None
    milestones: Optional[dict] = None
    decision: Optional[str] = None
    decision_type: Optional[str] = None
    favorable_outcome: Optional[bool] = None


class AppealArgumentCreateRequest(BaseModel):
    """创建上诉论点请求"""
    appeal_record_id: Optional[int] = None
    argument_type: str = "legal_error"
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    original_finding: Optional[str] = None
    appeal_finding: Optional[str] = None
    discrepancy: Optional[str] = None
    supporting_evidence: Optional[dict] = None
    counter_evidence: Optional[dict] = None
    legal_basis: Optional[dict] = None
    reasoning: Optional[str] = None
    expected_opposition: Optional[str] = None
    counter_response: Optional[str] = None
    importance: str = "medium"
    success_probability: Optional[float] = None
    is_key_argument: bool = False
    status: str = "draft"
    ai_suggestions: Optional[str] = None


class AppealArgumentUpdateRequest(BaseModel):
    """更新上诉论点请求"""
    argument_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    original_finding: Optional[str] = None
    appeal_finding: Optional[str] = None
    discrepancy: Optional[str] = None
    supporting_evidence: Optional[dict] = None
    counter_evidence: Optional[dict] = None
    legal_basis: Optional[dict] = None
    reasoning: Optional[str] = None
    expected_opposition: Optional[str] = None
    counter_response: Optional[str] = None
    importance: Optional[str] = None
    success_probability: Optional[float] = None
    is_key_argument: Optional[bool] = None
    status: Optional[str] = None
    ai_suggestions: Optional[str] = None


class AppealDeadlineCreateRequest(BaseModel):
    """创建上诉期限请求"""
    deadline_type: str = Field(..., min_length=1, max_length=100)
    deadline_name: str = Field(..., min_length=1, max_length=500)
    deadline_date: Optional[str] = None
    description: Optional[str] = None
    legal_basis: Optional[str] = None
    status: str = "pending"
    is_mandatory: bool = True
    reminder_days: Optional[list] = None


class AppealDocumentCreateRequest(BaseModel):
    """创建上诉材料请求"""
    document_type: str = Field(..., min_length=1, max_length=100)
    document_name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    source: Optional[str] = None
    status: str = "pending"
    is_required: bool = True
    related_document_id: Optional[int] = None
    purpose: Optional[str] = None
    content_summary: Optional[str] = None
    key_points: Optional[dict] = None
    ai_summary: Optional[str] = None
    ai_suggestions: Optional[str] = None


class SecondTrialStrategyCreateRequest(BaseModel):
    """创建二审策略请求"""
    title: str = Field(..., min_length=1, max_length=500)
    target_arguments: Optional[list] = None
    defense_points: Optional[list] = None
    defense_reasoning: Optional[str] = None
    supporting_evidence: Optional[dict] = None
    counter_evidence: Optional[dict] = None
    legal_basis: Optional[dict] = None
    expected_outcome: Optional[str] = None
    favorable_arguments: Optional[dict] = None
    is_approved: bool = False


# ============ 上诉记录 CRUD ============

@router.get("/case/{case_id}/appeals")
def list_appeals(case_id: int, db: Session = Depends(get_db)):
    """获取案件所有上诉记录"""
    try:
        return appeal_service.get_appeals_by_case(db, case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上诉记录失败: {str(e)}")


@router.post("/case/{case_id}/appeals")
def create_appeal(case_id: int, request: AppealCreateRequest, db: Session = Depends(get_db)):
    """创建上诉记录"""
    try:
        data = request.model_dump(exclude_none=True)
        appeal = appeal_service.create_appeal(db, case_id, data)
        return {"message": "上诉记录创建成功", "appeal": appeal}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建上诉记录失败: {str(e)}")


@router.get("/appeals/{appeal_id}")
def get_appeal(appeal_id: int, db: Session = Depends(get_db)):
    """获取上诉详情"""
    appeal = appeal_service.get_appeal(db, appeal_id)
    if not appeal:
        raise HTTPException(status_code=404, detail="上诉记录不存在")
    return {"appeal": appeal}


@router.put("/appeals/{appeal_id}")
def update_appeal(appeal_id: int, request: AppealUpdateRequest, db: Session = Depends(get_db)):
    """更新上诉记录"""
    data = request.model_dump(exclude_none=True)
    appeal = appeal_service.update_appeal(db, appeal_id, data)
    if not appeal:
        raise HTTPException(status_code=404, detail="上诉记录不存在")
    return {"message": "上诉记录更新成功", "appeal": appeal}


@router.delete("/appeals/{appeal_id}")
def delete_appeal(appeal_id: int, db: Session = Depends(get_db)):
    """删除上诉记录"""
    success = appeal_service.delete_appeal(db, appeal_id)
    if not success:
        raise HTTPException(status_code=404, detail="上诉记录不存在")
    return {"message": "上诉记录删除成功"}


# ============ 上诉论点 ============

@router.get("/case/{case_id}/arguments")
def list_appeal_arguments(case_id: int, db: Session = Depends(get_db)):
    """获取案件上诉论点列表"""
    try:
        return appeal_service.get_appeal_arguments(db, case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上诉论点失败: {str(e)}")


@router.post("/case/{case_id}/arguments")
def create_appeal_argument(case_id: int, request: AppealArgumentCreateRequest, db: Session = Depends(get_db)):
    """创建上诉论点"""
    try:
        data = request.model_dump(exclude_none=True)
        argument = appeal_service.create_appeal_argument(db, case_id, data)
        return {"message": "上诉论点创建成功", "argument": argument}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建上诉论点失败: {str(e)}")


@router.put("/argument/{argument_id}")
def update_appeal_argument(argument_id: int, request: AppealArgumentUpdateRequest, db: Session = Depends(get_db)):
    """更新上诉论点"""
    data = request.model_dump(exclude_none=True)
    argument = appeal_service.update_appeal_argument(db, argument_id, data)
    if not argument:
        raise HTTPException(status_code=404, detail="上诉论点不存在")
    return {"message": "上诉论点更新成功", "argument": argument}


@router.delete("/argument/{argument_id}")
def delete_appeal_argument(argument_id: int, db: Session = Depends(get_db)):
    """删除上诉论点"""
    success = appeal_service.delete_appeal_argument(db, argument_id)
    if not success:
        raise HTTPException(status_code=404, detail="上诉论点不存在")
    return {"message": "上诉论点删除成功"}


# ============ 上诉期限 ============

@router.get("/appeal/{appeal_id}/deadlines")
def list_appeal_deadlines(appeal_id: int, db: Session = Depends(get_db)):
    """获取上诉期限列表"""
    try:
        return appeal_service.get_appeal_deadlines(db, appeal_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上诉期限失败: {str(e)}")


@router.post("/appeal/{appeal_id}/deadlines")
def create_appeal_deadline(appeal_id: int, request: AppealDeadlineCreateRequest, db: Session = Depends(get_db)):
    """创建上诉期限"""
    try:
        data = request.model_dump(exclude_none=True)
        deadline = appeal_service.create_appeal_deadline(db, appeal_id, data)
        return {"message": "上诉期限创建成功", "deadline": deadline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建上诉期限失败: {str(e)}")


# ============ 上诉材料 ============

@router.get("/appeal/{appeal_id}/documents")
def list_appeal_documents(appeal_id: int, db: Session = Depends(get_db)):
    """获取上诉材料列表"""
    try:
        return appeal_service.get_appeal_documents(db, appeal_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上诉材料失败: {str(e)}")


@router.post("/appeal/{appeal_id}/documents")
def create_appeal_document(appeal_id: int, request: AppealDocumentCreateRequest, db: Session = Depends(get_db)):
    """创建上诉材料"""
    try:
        data = request.model_dump(exclude_none=True)
        document = appeal_service.create_appeal_document(db, appeal_id, data)
        return {"message": "上诉材料创建成功", "document": document}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建上诉材料失败: {str(e)}")


# ============ 二审策略 ============

@router.get("/appeal/{appeal_id}/strategy")
def get_appeal_strategy(appeal_id: int, db: Session = Depends(get_db)):
    """获取二审策略"""
    try:
        strategy = appeal_service.get_appeal_strategy(db, appeal_id)
        return {"strategy": strategy}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取二审策略失败: {str(e)}")


@router.post("/appeal/{appeal_id}/strategy")
def create_appeal_strategy(appeal_id: int, request: SecondTrialStrategyCreateRequest, db: Session = Depends(get_db)):
    """创建二审策略"""
    try:
        data = request.model_dump(exclude_none=True)
        strategy = appeal_service.create_appeal_strategy(db, appeal_id, data)
        return {"message": "二审策略创建成功", "strategy": strategy}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建二审策略失败: {str(e)}")


# ============ AI 功能 ============

@router.post("/appeal/{appeal_id}/generate-petition")
def generate_appeal_petition(appeal_id: int, db: Session = Depends(get_db)):
    """AI 生成上诉状"""
    try:
        result = appeal_service.generate_appeal_petition(db, appeal_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成上诉状失败: {str(e)}")


@router.get("/appeal/{appeal_id}/countdown")
def get_appeal_countdown(appeal_id: int, db: Session = Depends(get_db)):
    """上诉期限倒计时"""
    try:
        countdown = appeal_service.get_appeal_countdown(db, appeal_id)
        return countdown
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取倒计时失败: {str(e)}")


# ============ 统计 ============

@router.get("/case/{case_id}/statistics")
def get_appeal_statistics(case_id: int, db: Session = Depends(get_db)):
    """获取上诉统计数据"""
    try:
        stats = appeal_service.get_appeal_statistics(db, case_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")
