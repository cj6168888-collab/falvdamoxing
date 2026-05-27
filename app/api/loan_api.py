"""
借款记录 API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.loan import Loan

router = APIRouter(prefix="/api/loans", tags=["借款记录"])


class LoanCreate(BaseModel):
    direction: str = Field(..., description="方向: lend(借出) / borrow(借入)")
    borrower_name: str = Field(..., description="借款人姓名")
    borrower_phone: Optional[str] = Field(None, description="借款人电话")
    borrower_id: Optional[str] = Field(None, description="借款人证件号")
    lender_name: Optional[str] = Field(None, description="出借人姓名")
    amount: float = Field(..., description="金额")
    start_date: Optional[str] = Field(None, description="起始日期 YYYY-MM-DD")
    due_date: Optional[str] = Field(None, description="到期日期 YYYY-MM-DD")
    has_interest: int = Field(0, description="是否计息: 0=否 1=是")
    interest_rate: Optional[float] = Field(None, description="利率")
    interest_type: Optional[str] = Field(None, description="利率类型")
    guarantee: Optional[str] = Field(None, description="担保方式")
    purpose: Optional[str] = Field(None, description="借款用途")
    repayment_method: Optional[str] = Field(None, description="还款方式")
    notes: Optional[str] = Field(None, description="备注")
    status: str = Field("active", description="状态: active / settled / overdue")
    case_id: Optional[int] = Field(None, description="关联案件ID")
    project_id: Optional[int] = Field(None, description="关联项目ID")


class LoanUpdate(BaseModel):
    direction: Optional[str] = None
    borrower_name: Optional[str] = None
    borrower_phone: Optional[str] = None
    borrower_id: Optional[str] = None
    lender_name: Optional[str] = None
    amount: Optional[float] = None
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


class LoanResponse(BaseModel):
    id: int
    tenant_id: Optional[int] = None
    case_id: Optional[int] = None
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

    class Config:
        from_attributes = True


class LoanMutationResponse(BaseModel):
    id: Optional[int] = None
    message: str


@router.get("/", response_model=List[LoanResponse])
def list_loans(db: Session = Depends(get_db)):
    return db.query(Loan).order_by(Loan.id.desc()).all()


@router.post("/", response_model=LoanMutationResponse)
def create_loan(data: LoanCreate, db: Session = Depends(get_db)):
    loan = Loan(**data.dict())
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return {"id": loan.id, "message": "借款记录创建成功"}


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="借款记录不存在")
    return loan


@router.put("/{loan_id}", response_model=LoanMutationResponse)
def update_loan(loan_id: int, data: LoanUpdate, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="借款记录不存在")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(loan, key, value)
    db.commit()
    return {"id": loan_id, "message": "借款记录更新成功"}


@router.delete("/{loan_id}", response_model=LoanMutationResponse)
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="借款记录不存在")
    db.delete(loan)
    db.commit()
    return {"message": "借款记录删除成功"}
