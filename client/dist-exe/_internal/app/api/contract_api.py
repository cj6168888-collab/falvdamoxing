"""
合同管理 API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.contract import Contract

router = APIRouter(prefix="/api/contracts", tags=["合同管理"])


class ContractCreate(BaseModel):
    title: str = Field(..., description="合同标题")
    contract_type: Optional[str] = Field(None, description="合同类型")
    counterparty: Optional[str] = Field(None, description="对方当事人")
    amount: Optional[float] = Field(None, description="金额")
    sign_date: Optional[str] = Field(None, description="签订日期 YYYY-MM-DD")
    expiry_date: Optional[str] = Field(None, description="到期日期 YYYY-MM-DD")
    status: str = Field("pending", description="状态: pending / active / completed / terminated")
    content: Optional[str] = Field(None, description="合同内容")
    file_path: Optional[str] = Field(None, description="文件路径")
    notes: Optional[str] = Field(None, description="备注")
    case_id: Optional[int] = Field(None, description="关联案件ID")
    project_id: Optional[int] = Field(None, description="关联项目ID")


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    contract_type: Optional[str] = None
    counterparty: Optional[str] = None
    amount: Optional[float] = None
    sign_date: Optional[str] = None
    expiry_date: Optional[str] = None
    status: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None
    notes: Optional[str] = None


class ContractResponse(BaseModel):
    id: int
    tenant_id: Optional[int] = None
    case_id: Optional[int] = None
    project_id: Optional[int] = None
    title: str
    contract_type: Optional[str] = None
    counterparty: Optional[str] = None
    amount: Optional[float] = None
    sign_date: Optional[str] = None
    expiry_date: Optional[str] = None
    status: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ContractMutationResponse(BaseModel):
    id: Optional[int] = None
    message: str


@router.get("/", response_model=List[ContractResponse])
def list_contracts(db: Session = Depends(get_db)):
    return db.query(Contract).order_by(Contract.id.desc()).all()


@router.post("/", response_model=ContractMutationResponse)
def create_contract(data: ContractCreate, db: Session = Depends(get_db)):
    contract = Contract(**data.dict())
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return {"id": contract.id, "message": "合同创建成功"}


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    return contract


@router.put("/{contract_id}", response_model=ContractMutationResponse)
def update_contract(contract_id: int, data: ContractUpdate, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(contract, key, value)
    db.commit()
    return {"id": contract_id, "message": "合同更新成功"}


@router.delete("/{contract_id}", response_model=ContractMutationResponse)
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    db.delete(contract)
    db.commit()
    return {"message": "合同删除成功"}
