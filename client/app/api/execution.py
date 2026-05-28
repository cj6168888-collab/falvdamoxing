"""
执行跟踪 API - 判决生效后的强制执行程序管理
包括：执行概览、执行记录、执行任务、财产线索、执行申请书生成
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.db.database import get_db
from app.services.execution_service import execution_service
from app.services.context_service import context_service

router = APIRouter(prefix="/api/execution", tags=["执行跟踪"])


# ============ 请求模型 ============

class ExecutionOverviewUpdateRequest(BaseModel):
    """更新执行概览请求"""
    execution_case_number: Optional[str] = None
    execution_court: Optional[str] = None
    executor_name: Optional[str] = None
    executor_phone: Optional[str] = None
    execution_amount: Optional[str] = None
    executed_amount: Optional[str] = None
    remaining_amount: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    assistance_needed: Optional[str] = None
    assistance_status: Optional[str] = None
    next_follow_up: Optional[str] = None


class ExecutionRecordCreateRequest(BaseModel):
    """创建执行记录请求"""
    record_date: Optional[str] = None
    record_type: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    result: Optional[str] = None
    court_name: Optional[str] = None
    judge_name: Optional[str] = None
    document_number: Optional[str] = None
    stage: Optional[str] = None
    progress: float = 0.0
    attachments: Optional[dict] = None


class ExecutionRecordUpdateRequest(BaseModel):
    """更新执行记录请求"""
    record_date: Optional[str] = None
    record_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    result: Optional[str] = None
    court_name: Optional[str] = None
    judge_name: Optional[str] = None
    document_number: Optional[str] = None
    stage: Optional[str] = None
    progress: Optional[float] = None
    attachments: Optional[dict] = None


class ExecutionTaskCreateRequest(BaseModel):
    """创建执行任务请求"""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    task_type: Optional[str] = None
    stage: Optional[str] = None
    priority: str = "medium"
    status: str = "todo"
    due_date: Optional[str] = None
    assignee: Optional[str] = None
    related_record_id: Optional[int] = None
    related_asset_id: Optional[int] = None
    notes: Optional[str] = None


class ExecutionTaskUpdateRequest(BaseModel):
    """更新执行任务请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    stage: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    completed_date: Optional[str] = None
    assignee: Optional[str] = None
    related_record_id: Optional[int] = None
    related_asset_id: Optional[int] = None
    notes: Optional[str] = None


class ExecutionAssetCreateRequest(BaseModel):
    """创建财产线索请求"""
    asset_type: Optional[str] = None
    asset_name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    estimated_value: Optional[str] = None
    actual_value: Optional[str] = None
    location: Optional[str] = None
    identifier: Optional[str] = None
    status: str = "discovered"
    control_method: Optional[str] = None
    control_date: Optional[str] = None
    disposal_method: Optional[str] = None
    disposal_date: Optional[str] = None
    disposal_result: Optional[str] = None
    source: Optional[str] = None
    source_date: Optional[str] = None
    notes: Optional[str] = None


# ============ 执行概览 ============

@router.get("/case/{case_id}")
def get_execution_overview(case_id: int, db: Session = Depends(get_db)):
    """获取执行跟踪概览"""
    try:
        overview = execution_service.get_execution_overview(db, case_id)
        return overview
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行概览失败: {str(e)}")


@router.put("/case/{case_id}")
def update_execution_overview(case_id: int, request: ExecutionOverviewUpdateRequest, db: Session = Depends(get_db)):
    """更新执行跟踪概览"""
    try:
        data = request.model_dump(exclude_none=True)
        overview = execution_service.update_execution_overview(db, case_id, data)
        return {"message": "执行概览更新成功", "overview": overview}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新执行概览失败: {str(e)}")


# ============ 执行记录 ============

@router.get("/case/{case_id}/records")
def list_execution_records(case_id: int, db: Session = Depends(get_db)):
    """获取执行记录列表"""
    try:
        return execution_service.get_execution_records(db, case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行记录失败: {str(e)}")


@router.post("/case/{case_id}/records")
def create_execution_record(case_id: int, request: ExecutionRecordCreateRequest, db: Session = Depends(get_db)):
    """创建执行记录"""
    try:
        data = request.model_dump(exclude_none=True)
        record = execution_service.create_execution_record(db, case_id, data)
        return {"message": "执行记录创建成功", "record": record}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建执行记录失败: {str(e)}")


@router.put("/records/{record_id}")
def update_execution_record(record_id: int, request: ExecutionRecordUpdateRequest, db: Session = Depends(get_db)):
    """更新执行记录"""
    data = request.model_dump(exclude_none=True)
    record = execution_service.update_execution_record(db, record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return {"message": "执行记录更新成功", "record": record}


@router.delete("/records/{record_id}")
def delete_execution_record(record_id: int, db: Session = Depends(get_db)):
    """删除执行记录"""
    success = execution_service.delete_execution_record(db, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return {"message": "执行记录删除成功"}


# ============ 执行任务 ============

@router.get("/case/{case_id}/tasks")
def list_execution_tasks(case_id: int, db: Session = Depends(get_db)):
    """获取执行任务列表"""
    try:
        return execution_service.get_execution_tasks(db, case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行任务失败: {str(e)}")


@router.post("/case/{case_id}/tasks")
def create_execution_task(case_id: int, request: ExecutionTaskCreateRequest, db: Session = Depends(get_db)):
    """创建执行任务"""
    try:
        data = request.model_dump(exclude_none=True)
        task = execution_service.create_execution_task(db, case_id, data)
        return {"message": "执行任务创建成功", "task": task}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建执行任务失败: {str(e)}")


@router.put("/tasks/{task_id}")
def update_execution_task(task_id: int, request: ExecutionTaskUpdateRequest, db: Session = Depends(get_db)):
    """更新执行任务"""
    data = request.model_dump(exclude_none=True)
    task = execution_service.update_execution_task(db, task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="执行任务不存在")
    return {"message": "执行任务更新成功", "task": task}


@router.delete("/tasks/{task_id}")
def delete_execution_task(task_id: int, db: Session = Depends(get_db)):
    """删除执行任务"""
    success = execution_service.delete_execution_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="执行任务不存在")
    return {"message": "执行任务删除成功"}


# ============ 财产线索 ============

@router.get("/case/{case_id}/assets")
def list_execution_assets(case_id: int, db: Session = Depends(get_db)):
    """获取财产线索列表"""
    try:
        return execution_service.get_execution_assets(db, case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取财产线索失败: {str(e)}")


@router.post("/case/{case_id}/assets")
def create_execution_asset(case_id: int, request: ExecutionAssetCreateRequest, db: Session = Depends(get_db)):
    """创建财产线索"""
    try:
        data = request.model_dump(exclude_none=True)
        asset = execution_service.create_execution_asset(db, case_id, data)
        return {"message": "财产线索创建成功", "asset": asset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建财产线索失败: {str(e)}")


@router.get("/case/{case_id}/discover-assets")
def discover_assets_from_evidence(case_id: int, db: Session = Depends(get_db)):
    """从证据库发现财产线索"""
    try:
        return context_service.suggest_execution_assets_from_evidence(db, case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发现财产失败: {str(e)}")


@router.delete("/assets/{asset_id}")
def delete_execution_asset(asset_id: int, db: Session = Depends(get_db)):
    """删除财产线索"""
    success = execution_service.delete_execution_asset(db, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="财产线索不存在")
    return {"message": "财产线索删除成功"}


# ============ AI 功能 ============

@router.post("/case/{case_id}/generate-application")
def generate_execution_application(case_id: int, db: Session = Depends(get_db)):
    """AI 生成执行申请书"""
    try:
        result = execution_service.generate_execution_application(db, case_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成执行申请书失败: {str(e)}")


# ============ 统计 ============

@router.get("/case/{case_id}/statistics")
def get_execution_statistics(case_id: int, db: Session = Depends(get_db)):
    """获取执行统计"""
    try:
        stats = execution_service.get_execution_statistics(db, case_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")
