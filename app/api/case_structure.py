"""Case structure extension API routes."""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case import Case, CaseThread, CounterClaim, Party

router = APIRouter(prefix="/api/cases", tags=["Case structure extensions"])


class ThreadUpdate(BaseModel):
    name: Optional[str] = None
    cause: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[str] = None
    related_thread_id: Optional[int] = None
    evidence_summary: Optional[str] = None
    sort_order: Optional[int] = None


class PartyUpdate(BaseModel):
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
    sort_order: Optional[int] = None


class CounterClaimUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None
    counter_plaintiff_id: Optional[int] = None
    counter_defendant_id: Optional[int] = None
    is_filed: Optional[bool] = None
    status: Optional[str] = None


class CaseSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    case_type: str
    status: str
    plaintiff: Optional[str] = None
    defendant: Optional[str] = None
    third_party: Optional[str] = None
    cause: Optional[str] = None
    claim_amount: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    name: str
    cause: Optional[str] = None
    description: Optional[str] = None
    status: str
    amount: Optional[str] = None
    related_thread_id: Optional[int] = None
    evidence_summary: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class PartyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    name: str
    party_type: Optional[str] = None
    role: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_relation: Optional[str] = None
    relation_to_case: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class CounterClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    claim_type: str
    title: str
    description: Optional[str] = None
    amount: Optional[str] = None
    counter_plaintiff_id: Optional[int] = None
    counter_defendant_id: Optional[int] = None
    is_filed: bool
    status: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str


class CaseStructureResponse(BaseModel):
    case: CaseSummaryResponse
    threads: list[ThreadResponse]
    parties: list[PartyResponse]
    counter_claims: list[CounterClaimResponse]


def _apply_updates(instance: Any, data: BaseModel) -> None:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(instance, key, value)


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
def get_thread(thread_id: int, db: Session = Depends(get_db)):
    thread = db.query(CaseThread).filter(CaseThread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.put("/threads/{thread_id}", response_model=ThreadResponse)
def update_thread(thread_id: int, thread_data: ThreadUpdate, db: Session = Depends(get_db)):
    thread = db.query(CaseThread).filter(CaseThread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    _apply_updates(thread, thread_data)
    db.commit()
    db.refresh(thread)
    return thread


@router.delete("/threads/{thread_id}", response_model=MessageResponse)
def delete_thread(thread_id: int, db: Session = Depends(get_db)):
    thread = db.query(CaseThread).filter(CaseThread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    db.delete(thread)
    db.commit()
    return {"message": "Thread deleted"}


@router.get("/parties/{party_id}", response_model=PartyResponse)
def get_party(party_id: int, db: Session = Depends(get_db)):
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    return party


@router.put("/parties/{party_id}", response_model=PartyResponse)
def update_party(party_id: int, party_data: PartyUpdate, db: Session = Depends(get_db)):
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    _apply_updates(party, party_data)
    db.commit()
    db.refresh(party)
    return party


@router.delete("/parties/{party_id}", response_model=MessageResponse)
def delete_party(party_id: int, db: Session = Depends(get_db)):
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    db.delete(party)
    db.commit()
    return {"message": "Party deleted"}


@router.put("/counter-claims/{claim_id}", response_model=CounterClaimResponse)
def update_counter_claim(
    claim_id: int,
    claim_data: CounterClaimUpdate,
    db: Session = Depends(get_db),
):
    claim = db.query(CounterClaim).filter(CounterClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Counter claim not found")

    _apply_updates(claim, claim_data)
    db.commit()
    db.refresh(claim)
    return claim


@router.delete("/counter-claims/{claim_id}", response_model=MessageResponse)
def delete_counter_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(CounterClaim).filter(CounterClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Counter claim not found")

    db.delete(claim)
    db.commit()
    return {"message": "Counter claim deleted"}


@router.get("/{case_id}/structure", response_model=CaseStructureResponse)
def get_case_structure(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    threads = (
        db.query(CaseThread)
        .filter(CaseThread.case_id == case_id)
        .order_by(CaseThread.sort_order)
        .all()
    )
    parties = (
        db.query(Party)
        .filter(Party.case_id == case_id)
        .order_by(Party.sort_order)
        .all()
    )
    counter_claims = db.query(CounterClaim).filter(CounterClaim.case_id == case_id).all()

    return {
        "case": case,
        "threads": threads,
        "parties": parties,
        "counter_claims": counter_claims,
    }
