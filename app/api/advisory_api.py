"""
案件决策支持 API — 成本收益分析 + 调解策略
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.db.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.cost_benefit_service import cost_benefit_service
from app.services.mediation_service import mediation_service

router = APIRouter(prefix="/api/advisory", tags=["决策支持"])


class CostBenefitRequest(BaseModel):
    claim_amount: float = Field(..., gt=0, description="诉讼标的额")
    case_type: str = Field(default="合同纠纷", description="案件类型")
    complexity: str = Field(default="medium", description="复杂度: simple/medium/complex")
    evidence_strength: str = Field(default="medium", description="证据力度: weak/medium/strong")
    jurisdiction: str = Field(default="郑州", description="管辖地")


class CostBenefitResponse(BaseModel):
    claim_amount: float
    cost: dict
    estimated_recovery: float
    win_probability: float
    time_to_resolution_months: int
    net_expected_value: float
    roi: float
    recommendation: str
    risk_factors: List[str]
    cost_saving_tips: List[str]


class MediationRequest(BaseModel):
    case_id: Optional[int] = Field(None, description="关联案件ID")
    claim_amount: float = Field(..., gt=0, description="争议金额")
    case_summary: str = Field(..., description="案件摘要")
    evidence_strength: str = Field(default="medium", description="证据力度")
    opponent_profile: str = Field(default="", description="对方当事人画像")
    prior_negotiation: str = Field(default="", description="既往谈判情况")


class MediationResponse(BaseModel):
    readiness_score: int
    readiness_level: str
    best_alternative: str
    worst_alternative: str
    batna_value: float
    settlement_floor: float
    settlement_target: float
    settlement_ceiling: float
    recommended_range: str
    opening_position: str
    concession_plan: List[str]
    pressure_points: List[str]
    face_saving_options: List[str]
    mediation_script: str
    mediation_brief: str


@router.post("/cost-benefit", response_model=CostBenefitResponse)
def analyze_cost_benefit(
    req: CostBenefitRequest,
    current_user: User = Depends(get_current_user),
):
    result = cost_benefit_service.analyze(
        claim_amount=req.claim_amount,
        case_type=req.case_type,
        complexity=req.complexity,
        evidence_strength=req.evidence_strength,
        jurisdiction=req.jurisdiction,
    )
    return CostBenefitResponse(
        claim_amount=result.claim_amount,
        cost=result.cost.to_dict(),
        estimated_recovery=result.estimated_recovery,
        win_probability=result.win_probability,
        time_to_resolution_months=result.time_to_resolution_months,
        net_expected_value=result.net_expected_value,
        roi=result.roi,
        recommendation=result.recommendation,
        risk_factors=result.risk_factors,
        cost_saving_tips=result.cost_saving_tips,
    )


@router.post("/mediation", response_model=MediationResponse)
def analyze_mediation(
    req: MediationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case_info = {"title": "", "plaintiff": "", "defendant": ""}
    if req.case_id:
        from app.models.case import Case
        case = db.query(Case).filter(Case.id == req.case_id).first()
        if case:
            case_info = {
                "title": case.title or "",
                "plaintiff": case.plaintiff or "",
                "defendant": case.defendant or "",
            }

    analysis = mediation_service.analyze(
        claim_amount=req.claim_amount,
        case_summary=req.case_summary,
        evidence_strength=req.evidence_strength,
        opponent_profile=req.opponent_profile,
        prior_negotiation=req.prior_negotiation,
    )
    brief = mediation_service.generate_mediation_brief(analysis, case_info)

    return MediationResponse(
        readiness_score=analysis.readiness_score,
        readiness_level=analysis.readiness_level,
        best_alternative=analysis.best_alternative,
        worst_alternative=analysis.worst_alternative,
        batna_value=analysis.batna_value,
        settlement_floor=analysis.settlement_floor,
        settlement_target=analysis.settlement_target,
        settlement_ceiling=analysis.settlement_ceiling,
        recommended_range=analysis.recommended_range,
        opening_position=analysis.opening_position,
        concession_plan=analysis.concession_plan,
        pressure_points=analysis.pressure_points,
        face_saving_options=analysis.face_saving_options,
        mediation_script=analysis.mediation_script,
        mediation_brief=brief,
    )
