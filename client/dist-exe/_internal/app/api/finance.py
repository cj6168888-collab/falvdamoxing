"""
案件财务 API - 费用记录、成本收益分析、胜诉概率评估
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.services.finance_service import finance_service

router = APIRouter(prefix="/api/finance", tags=["案件财务"])


# ============ 请求模型 ============

class FinanceUpdateRequest(BaseModel):
    """更新财务概览请求"""
    expected_recovery: Optional[float] = None
    actual_recovery: Optional[float] = None
    notes: Optional[str] = None


class ExpenseCreateRequest(BaseModel):
    """创建费用记录请求"""
    category: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = "CNY"
    status: str = "pending"
    expense_date: Optional[str] = None
    payment_date: Optional[str] = None
    due_date: Optional[str] = None
    payee: Optional[str] = None
    invoice_number: Optional[str] = None
    related_document_id: Optional[int] = None
    notes: Optional[str] = None


class ExpenseUpdateRequest(BaseModel):
    """更新费用记录请求"""
    category: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    expense_date: Optional[str] = None
    payment_date: Optional[str] = None
    due_date: Optional[str] = None
    payee: Optional[str] = None
    invoice_number: Optional[str] = None
    related_document_id: Optional[int] = None
    notes: Optional[str] = None


# ============ 财务概览 ============

@router.get("/case/{case_id}")
def get_finance_overview(case_id: int, db: Session = Depends(get_db)):
    """获取财务概览"""
    try:
        overview = finance_service.get_finance_overview(db, case_id)
        return overview
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取财务概览失败: {str(e)}")


@router.put("/case/{case_id}")
def update_finance_overview(case_id: int, request: FinanceUpdateRequest, db: Session = Depends(get_db)):
    """更新财务概览"""
    try:
        data = request.model_dump(exclude_none=True)
        overview = finance_service.update_finance_overview(db, case_id, data)
        return {"message": "财务概览更新成功", "overview": overview}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新财务概览失败: {str(e)}")


# ============ 费用记录 ============

@router.get("/case/{case_id}/expenses")
def list_expenses(case_id: int, db: Session = Depends(get_db)):
    """获取费用记录列表"""
    try:
        expenses = finance_service.get_expenses(db, case_id)
        return {"expenses": expenses, "total": len(expenses)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取费用记录失败: {str(e)}")


@router.post("/case/{case_id}/expenses")
def create_expense(case_id: int, request: ExpenseCreateRequest, db: Session = Depends(get_db)):
    """创建费用记录"""
    try:
        data = request.model_dump(exclude_none=True)
        expense = finance_service.create_expense(db, case_id, data)
        return {"message": "费用记录创建成功", "expense": expense}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建费用记录失败: {str(e)}")


@router.put("/expenses/{expense_id}")
def update_expense(expense_id: int, request: ExpenseUpdateRequest, db: Session = Depends(get_db)):
    """更新费用记录"""
    data = request.model_dump(exclude_none=True)
    expense = finance_service.update_expense(db, expense_id, data)
    if not expense:
        raise HTTPException(status_code=404, detail="费用记录不存在")
    return {"message": "费用记录更新成功", "expense": expense}


@router.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """删除费用记录"""
    success = finance_service.delete_expense(db, expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="费用记录不存在")
    return {"message": "费用记录删除成功"}


# ============ 分析 ============

@router.get("/case/{case_id}/cost-analysis")
def get_cost_analysis(case_id: int, db: Session = Depends(get_db)):
    """成本收益分析"""
    try:
        analysis = finance_service.get_cost_benefit_analysis(db, case_id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"成本收益分析失败: {str(e)}")


@router.get("/case/{case_id}/win-rate")
def get_win_rate(case_id: int, db: Session = Depends(get_db)):
    """获取胜诉概率评估"""
    try:
        overview = finance_service.get_finance_overview(db, case_id)
        return {
            "win_rate": overview["finance"]["win_rate"],
            "win_rate_confidence": overview["finance"]["win_rate_confidence"],
            "win_rate_assessed_at": overview["finance"]["win_rate_assessed_at"],
            "latest_assessment": overview.get("latest_win_rate"),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取胜诉概率失败: {str(e)}")


@router.post("/case/{case_id}/win-rate")
def assess_win_rate(case_id: int, force: bool = Query(False), db: Session = Depends(get_db)):
    """重新评估胜诉概率"""
    try:
        result = finance_service.assess_win_rate(db, case_id, force=force)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估胜诉概率失败: {str(e)}")


# ============ 统计 ============

@router.get("/case/{case_id}/statistics")
def get_finance_statistics(case_id: int, db: Session = Depends(get_db)):
    """获取财务统计"""
    try:
        stats = finance_service.get_finance_statistics(db, case_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取财务统计失败: {str(e)}")
