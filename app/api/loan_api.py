"""
借款记录API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.db.database import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/loans", tags=["借款记录"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class LoanCreate(BaseModel):
    borrower_name: str = Field(..., description="借款人姓名")
    amount: float = Field(..., description="金额")
    direction: str = Field(..., description="方向: lend(借出) / borrow(借入)")
    due_date: Optional[str] = Field(None, description="到期日期 YYYY-MM-DD")
    interest_rate: Optional[float] = Field(None, description="利率")
    notes: Optional[str] = Field(None, description="备注")
    status: str = Field("active", description="状态: active / settled / overdue")


class LoanUpdate(BaseModel):
    borrower_name: Optional[str] = None
    amount: Optional[float] = None
    direction: Optional[str] = None
    due_date: Optional[str] = None
    interest_rate: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class LoanResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    direction: str
    borrower_name: str
    borrower_phone: Optional[str] = None
    borrower_id: Optional[str] = None
    lender_name: Optional[str] = None
    amount: float
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    has_interest: Optional[int] = None
    interest_rate: Optional[float] = None
    interest_type: Optional[str] = None
    guarantee: Optional[str] = None
    purpose: Optional[str] = None
    repayment_method: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LoanMutationResponse(BaseModel):
    id: Optional[int] = None
    message: str


@router.get("/", response_model=List[LoanResponse])
def list_loans(db: Session = Depends(get_db)):
    """获取所有借款记录"""
    from app.db.storage import get_loans as db_get_loans
    loans = db_get_loans()
    return loans


@router.post("/", response_model=LoanMutationResponse)
def create_loan(loan: LoanCreate, db: Session = Depends(get_db)):
    """创建借款记录"""
    from app.db.storage import save_loan
    
    data = loan.dict()
    loan_id = save_loan(data)
    return {"id": loan_id, "message": "借款记录创建成功"}


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    """获取单个借款记录"""
    from app.db.storage import get_loans
    
    loans = get_loans()
    for loan in loans:
        if loan.get('id') == loan_id:
            return loan
    raise HTTPException(status_code=404, detail="借款记录不存在")


@router.put("/{loan_id}", response_model=LoanMutationResponse)
def update_loan(loan_id: int, loan: LoanUpdate, db: Session = Depends(get_db)):
    """更新借款记录"""
    from app.db.storage import update_loan
    
    data = loan.dict(exclude_unset=True)
    if update_loan(loan_id, data):
        return {"id": loan_id, "message": "借款记录更新成功"}
    raise HTTPException(status_code=404, detail="借款记录不存在")


@router.delete("/{loan_id}", response_model=LoanMutationResponse)
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    """删除借款记录"""
    from app.db.storage import delete_loan
    
    if delete_loan(loan_id):
        return {"message": "借款记录删除成功"}
    raise HTTPException(status_code=404, detail="借款记录不存在")
