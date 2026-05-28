"""Reminder extension API routes."""

from typing import Any
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case import Case
from app.services.reminder_service import reminder_service

router = APIRouter(prefix="/api/reminders", tags=["Reminder extensions"])


class BatchUpdateRequest(BaseModel):
    reminder_ids: list[int] = Field(..., min_length=1)
    is_read: Optional[bool] = None
    is_completed: Optional[bool] = None
    priority: Optional[str] = None


class SnoozeRequest(BaseModel):
    days: int = Field(default=1, ge=1, le=365)


class ReminderListResponse(BaseModel):
    reminders: list[dict[str, Any]]
    total: int


class ReminderGenerateResponse(BaseModel):
    message: str
    reminders: list[dict[str, Any]]
    count: int


class MessageCountResponse(BaseModel):
    message: str
    count: int


class BatchUpdateResponse(BaseModel):
    message: str
    updated: int = 0
    failed: int = 0


class AutoGenerateAllResult(BaseModel):
    case_id: int
    case_title: str
    generated: int
    error: bool = False


class AutoGenerateAllResponse(BaseModel):
    message: str
    results: list[AutoGenerateAllResult]
    total: int


class ReminderActionResponse(BaseModel):
    message: str
    reminder: dict[str, Any]


@router.get("/overdue", response_model=ReminderListResponse)
def get_overdue_reminders(db: Session = Depends(get_db)):
    try:
        reminders = reminder_service.check_overdue(db)
        return {"reminders": reminders, "total": len(reminders)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get overdue reminders: {exc}")


@router.put("/batch", response_model=BatchUpdateResponse)
def batch_update_reminders(request: BatchUpdateRequest, db: Session = Depends(get_db)):
    try:
        data = {}
        if request.is_read is not None:
            data["is_read"] = request.is_read
        if request.is_completed is not None:
            data["is_completed"] = request.is_completed
        if request.priority is not None:
            data["priority"] = request.priority

        result = reminder_service.batch_update(db, request.reminder_ids, data)
        return {"message": "Batch reminder update completed.", **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to batch update reminders: {exc}")


@router.put("/mark-all-read", response_model=MessageCountResponse)
def mark_all_read(case_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    try:
        count = reminder_service.mark_all_read(db, case_id=case_id)
        return {"message": "Reminders marked as read.", "count": count}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to mark reminders as read: {exc}")


@router.post("/auto-generate", response_model=ReminderGenerateResponse)
def auto_generate_reminders(case_id: int = Query(...), db: Session = Depends(get_db)):
    try:
        reminders = reminder_service.auto_generate_reminders(db, case_id)
        return {
            "message": f"Generated {len(reminders)} reminders.",
            "reminders": reminders,
            "count": len(reminders),
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to auto-generate reminders: {exc}")


@router.post("/auto-generate-all", response_model=AutoGenerateAllResponse)
def auto_generate_all_reminders(db: Session = Depends(get_db)):
    try:
        cases = db.query(Case).all()
        total_generated = 0
        results = []
        for case in cases:
            try:
                reminders = reminder_service.auto_generate_reminders(db, case.id)
                total_generated += len(reminders)
                results.append(
                    {
                        "case_id": case.id,
                        "case_title": case.title,
                        "generated": len(reminders),
                    }
                )
            except Exception:
                results.append(
                    {
                        "case_id": case.id,
                        "case_title": case.title,
                        "generated": 0,
                        "error": True,
                    }
                )
        return {
            "message": f"Generated {total_generated} reminders for {len(cases)} cases.",
            "results": results,
            "total": total_generated,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to auto-generate reminders: {exc}")


@router.put("/{reminder_id}/complete", response_model=ReminderActionResponse)
def mark_complete(reminder_id: int, db: Session = Depends(get_db)):
    reminder = reminder_service.mark_complete(db, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"message": "Reminder marked as completed.", "reminder": reminder}


@router.put("/{reminder_id}/snooze", response_model=ReminderActionResponse)
def snooze_reminder(reminder_id: int, request: SnoozeRequest, db: Session = Depends(get_db)):
    reminder = reminder_service.snooze_reminder(db, reminder_id, request.days)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {
        "message": f"Reminder snoozed for {request.days} days.",
        "reminder": reminder,
    }
