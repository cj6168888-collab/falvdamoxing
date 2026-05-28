"""
资深律师分析 API V2
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.models.case import Case
from app.services.senior_lawyer_engine import SeniorLawyerEngine, senior_lawyer_engine

router = APIRouter(prefix="/api/v2/senior-analysis", tags=["资深律师分析V2"])


# ============ 请求模型 ============

class AnalyzeCaseRequest(BaseModel):
    """分析案件请求"""
    case_id: int
    analysis_level: str = "standard"  # quick/standard/deep


# ============ API 接口 ============

@router.post("/analyze")
async def analyze_case(request: AnalyzeCaseRequest, db: Session = Depends(get_db)):
    """
    资深律师式案件分析
    全面分析：案件理解 → 证据盘点 → 要件核对 → 问题发现 → 风险评估 → 建议生成
    """
    # 验证案件
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 执行分析
    result = senior_lawyer_engine.analyze_case(
        case_id=request.case_id,
        analysis_level=request.analysis_level
    )

    return result


@router.get("/case-understanding/{case_id}")
async def get_case_understanding(case_id: int, db: Session = Depends(get_db)):
    """
    获取案件理解结果
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 获取简单理解
    understanding = senior_lawyer_engine._understand_case(db, case)

    return {
        'case_id': case_id,
        'understanding': understanding
    }


@router.get("/requirements/{case_id}")
async def get_legal_requirements(case_id: int, db: Session = Depends(get_db)):
    """
    获取案件法律要件
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 获取要件库
    requirements = SeniorLawyerEngine.LEGAL_REQUIREMENTS

    # 简单分析案件类型
    cause = (case.cause or '').lower()
    if '合同' in cause or '协议' in cause:
        category = 'CONTRACT_DISPUTE'
    elif '侵权' in cause or '伤害' in cause:
        category = 'TORT_DISPUTE'
    elif '劳动' in cause:
        category = 'LABOR_DISPUTE'
    else:
        category = 'GENERIC'

    return {
        'case_id': case_id,
        'category': category,
        'requirements': requirements.get(category, requirements['GENERIC'])
    }


@router.get("/severity-levels")
async def get_severity_levels():
    """
    获取严重程度等级
    """
    return {
        'levels': SeniorLawyerEngine.SEVERITY_LEVELS
    }
