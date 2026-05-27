"""Dashboard extension API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard extensions"])


class RecentCasesResponse(BaseModel):
    recent_cases: list[dict[str, Any]]
    total: int


class ActivityLogResponse(BaseModel):
    activity_log: list[dict[str, Any]]
    total: int


@router.get("/recent-cases", response_model=RecentCasesResponse)
def get_recent_cases(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    try:
        cases = dashboard_service.get_recent_cases(db, limit=limit)
        return {"recent_cases": cases, "total": len(cases)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get recent cases: {exc}")


@router.get("/ai-suggestions", response_model=dict[str, Any])
def get_ai_suggestions(db: Session = Depends(get_db)):
    try:
        suggestions = dashboard_service.generate_ai_suggestions(db)
        return suggestions
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate AI suggestions: {exc}")


@router.get("/activity", response_model=ActivityLogResponse)
def get_activity_log(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    try:
        activities = dashboard_service.get_activity_log(db, limit=limit)
        return {"activity_log": activities, "total": len(activities)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get activity log: {exc}")
