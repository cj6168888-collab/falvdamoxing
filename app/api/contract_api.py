"""
合同管理API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.db.database import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/contracts", tags=["合同管理"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ContractCreate(BaseModel):
    title: str = Field(..., description="合同标题")
    contract_type: Optional[str] = Field(None, description="合同类型")
    party_a: Optional[str] = Field(None, description="甲方")
    party_b: Optional[str] = Field(None, description="乙方")
    amount: Optional[str] = Field(None, description="金额")
    signing_date: Optional[str] = Field(None, description="签订日期 YYYY-MM-DD")
    effective_date: Optional[str] = Field(None, description="生效日期 YYYY-MM-DD")
    expiry_date: Optional[str] = Field(None, description="到期日期 YYYY-MM-DD")
    status: str = Field("draft", description="状态: draft / active / completed / terminated")
    notes: Optional[str] = Field(None, description="备注")


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    contract_type: Optional[str] = None
    party_a: Optional[str] = None
    party_b: Optional[str] = None
    amount: Optional[str] = None
    signing_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ContractResponse(BaseModel):
    id: int
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


class ContractMutationResponse(BaseModel):
    id: Optional[int] = None
    message: str


@router.get("/", response_model=List[ContractResponse])
def list_contracts(db: Session = Depends(get_db)):
    """获取所有合同"""
    from app.db.storage import get_contracts
    contracts = get_contracts()
    return contracts


@router.post("/", response_model=ContractMutationResponse)
def create_contract(contract: ContractCreate, db: Session = Depends(get_db)):
    """创建合同"""
    from app.db.storage import save_contract
    
    data = contract.dict()
    contract_id = save_contract(data)
    return {"id": contract_id, "message": "合同创建成功"}


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    """获取单个合同"""
    from app.db.storage import get_contracts
    
    contracts = get_contracts()
    for contract in contracts:
        if contract.get('id') == contract_id:
            return contract
    raise HTTPException(status_code=404, detail="合同不存在")


@router.put("/{contract_id}", response_model=ContractMutationResponse)
def update_contract(contract_id: int, contract: ContractUpdate, db: Session = Depends(get_db)):
    """更新合同"""
    from app.db.storage import update_contract
    
    data = contract.dict(exclude_unset=True)
    if update_contract(contract_id, data):
        return {"id": contract_id, "message": "合同更新成功"}
    raise HTTPException(status_code=404, detail="合同不存在")


@router.delete("/{contract_id}", response_model=ContractMutationResponse)
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    """删除合同"""
    from app.db.storage import delete_contract
    
    if delete_contract(contract_id):
        return {"message": "合同删除成功"}
    raise HTTPException(status_code=404, detail="合同不存在")
