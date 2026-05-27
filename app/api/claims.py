"""
战役管理 API - 文书对话核心
支持案件下的多诉求（战役）管理，每个战役需要特定的文书和证据
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
import json

from app.db.database import get_db
from app.models.case import Case
from app.models.case_claim import CaseClaim, CaseClaimStatus
from app.models.evidence import EvidenceItem
from app.models.document import GeneratedDocument
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/claims", tags=["战役管理"])


# ============ 请求/响应模型 ============

class ClaimCreate(BaseModel):
    """创建战役请求"""
    case_id: int
    title: str
    description: Optional[str] = None
    claim_type: Optional[str] = None
    amount: Optional[str] = None
    priority: int = 3


class ClaimUpdate(BaseModel):
    """更新战役请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    claim_type: Optional[str] = None
    amount: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    required_documents: Optional[List[str]] = None
    required_evidence_ids: Optional[List[str]] = None
    depends_on: Optional[List[int]] = None
    notes: Optional[str] = None


class ClaimPlanRequest(BaseModel):
    """战役规划请求"""
    auto_generate: bool = True  # 是否自动生成文书


class ClaimResponse(BaseModel):
    """战役响应"""
    id: int
    case_id: int
    title: str
    description: Optional[str]
    claim_type: Optional[str]
    amount: Optional[str]
    priority: int
    status: str
    required_documents: List[str]
    required_evidence_ids: List[str]
    depends_on: List[int]
    ai_plan_result: Optional[str]
    ai_evidence_suggestions: List[str]
    ai_document_suggestions: List[str]
    risk_level: str
    risk_notes: Optional[str]
    notes: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    document_count: int = 0
    evidence_count: int = 0


class ClaimWithEvidence(BaseModel):
    """战役详情（含证据和文书）"""
    id: int
    case_id: int
    title: str
    description: Optional[str]
    claim_type: Optional[str]
    amount: Optional[str]
    priority: int
    status: str
    required_documents: List[str]
    required_evidence_ids: List[str]
    risk_level: str
    risk_notes: Optional[str]
    # 关联的证据列表
    evidence_list: List[dict] = []
    # 关联的文书列表
    documents_list: List[dict] = []
    created_at: Optional[str]


# ============ 辅助函数 ============

def _stringify_suggestion(item: Any) -> str:
    """将 AI 规划返回的对象型建议压平为前端可直接展示的字符串。"""
    if item is None:
        return ""
    if isinstance(item, str):
        return item
    if isinstance(item, (int, float, bool)):
        return str(item)
    if isinstance(item, dict):
        parts = []
        for key in ("id", "name", "title", "type", "document_type", "reason", "summary", "analysis", "建议", "理由"):
            value = item.get(key)
            if value not in (None, ""):
                parts.append(str(value))
        if parts:
            return " - ".join(parts)
        return json.dumps(item, ensure_ascii=False)
    return json.dumps(item, ensure_ascii=False)


def _string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [text for text in (_stringify_suggestion(item) for item in value) if text]
    text = _stringify_suggestion(value)
    return [text] if text else []


def _evidence_id_list(value: Any) -> List[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    result = []
    for item in values:
        if isinstance(item, dict):
            item = item.get("id") or item.get("evidence_id") or item.get("证据ID")
        if item not in (None, ""):
            result.append(str(item))
    return result

def get_claim_with_details(db: Session, claim_id: int) -> Optional[dict]:
    """获取战役详情（含证据和文书）"""
    claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
    if not claim:
        return None
    
    # 获取关联的证据
    evidence_list = []
    required_evidence_ids = _evidence_id_list(claim.required_evidence_ids)
    if required_evidence_ids:
        evidences = db.query(EvidenceItem).filter(
            EvidenceItem.id.in_(required_evidence_ids)
        ).all()
        for ev in evidences:
            evidence_list.append({
                "id": ev.id,
                "name": ev.display_name or ev.original_filename or "未命名",
                "type": ev.evidence_type,
                "summary": ev.summary,
            })
    
    # 获取关联的文书
    documents_list = []
    docs = db.query(GeneratedDocument).filter(
        GeneratedDocument.claim_id == claim_id
    ).all()
    for doc in docs:
        documents_list.append({
            "id": doc.id,
            "title": doc.title,
            "type": doc.document_type,
            "status": doc.status,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        })
    
    return {
        "id": claim.id,
        "case_id": claim.case_id,
        "title": claim.title,
        "description": claim.description,
        "claim_type": claim.claim_type,
        "amount": claim.amount,
        "priority": claim.priority,
        "status": claim.status,
        "required_documents": _string_list(claim.required_documents),
        "required_evidence_ids": required_evidence_ids,
        "risk_level": claim.risk_level,
        "risk_notes": claim.risk_notes,
        "evidence_list": evidence_list,
        "documents_list": documents_list,
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
    }


# ============ API Endpoints ============

@router.post("", response_model=ClaimResponse)
def create_claim(request: ClaimCreate, db: Session = Depends(get_db)):
    """创建战役"""
    # 验证案件存在
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    claim = CaseClaim(
        case_id=request.case_id,
        title=request.title,
        description=request.description,
        claim_type=request.claim_type,
        amount=request.amount,
        priority=request.priority,
        status=CaseClaimStatus.PENDING.value,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    
    return ClaimResponse(
        id=claim.id,
        case_id=claim.case_id,
        title=claim.title,
        description=claim.description,
        claim_type=claim.claim_type,
        amount=claim.amount,
        priority=claim.priority,
        status=claim.status,
        required_documents=_string_list(claim.required_documents),
        required_evidence_ids=_evidence_id_list(claim.required_evidence_ids),
        depends_on=claim.depends_on or [],
        ai_plan_result=claim.ai_plan_result,
        ai_evidence_suggestions=_string_list(claim.ai_evidence_suggestions),
        ai_document_suggestions=_string_list(claim.ai_document_suggestions),
        risk_level=claim.risk_level,
        risk_notes=claim.risk_notes,
        notes=claim.notes,
        created_at=claim.created_at.isoformat() if claim.created_at else None,
        updated_at=claim.updated_at.isoformat() if claim.updated_at else None,
        document_count=0,
        evidence_count=len(_evidence_id_list(claim.required_evidence_ids)),
    )


@router.get("/case/{case_id}", response_model=List[ClaimResponse])
def get_case_claims(case_id: int, db: Session = Depends(get_db)):
    """获取案件所有战役"""
    claims = db.query(CaseClaim).filter(
        CaseClaim.case_id == case_id
    ).order_by(CaseClaim.priority.asc(), CaseClaim.created_at.desc()).all()
    
    result = []
    for claim in claims:
        # 获取关联的文书数量
        doc_count = db.query(GeneratedDocument).filter(
            GeneratedDocument.claim_id == claim.id
        ).count()
        
        result.append(ClaimResponse(
            id=claim.id,
            case_id=claim.case_id,
            title=claim.title,
            description=claim.description,
            claim_type=claim.claim_type,
            amount=claim.amount,
            priority=claim.priority,
            status=claim.status,
            required_documents=_string_list(claim.required_documents),
            required_evidence_ids=_evidence_id_list(claim.required_evidence_ids),
            depends_on=claim.depends_on or [],
            ai_plan_result=claim.ai_plan_result,
            ai_evidence_suggestions=_string_list(claim.ai_evidence_suggestions),
            ai_document_suggestions=_string_list(claim.ai_document_suggestions),
            risk_level=claim.risk_level,
            risk_notes=claim.risk_notes,
            notes=claim.notes,
            created_at=claim.created_at.isoformat() if claim.created_at else None,
            updated_at=claim.updated_at.isoformat() if claim.updated_at else None,
            document_count=doc_count,
            evidence_count=len(_evidence_id_list(claim.required_evidence_ids)),
        ))
    
    return result


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(claim_id: int, db: Session = Depends(get_db)):
    """获取战役详情"""
    claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="战役不存在")
    
    doc_count = db.query(GeneratedDocument).filter(
        GeneratedDocument.claim_id == claim_id
    ).count()
    
    return ClaimResponse(
        id=claim.id,
        case_id=claim.case_id,
        title=claim.title,
        description=claim.description,
        claim_type=claim.claim_type,
        amount=claim.amount,
        priority=claim.priority,
        status=claim.status,
        required_documents=_string_list(claim.required_documents),
        required_evidence_ids=_evidence_id_list(claim.required_evidence_ids),
        depends_on=claim.depends_on or [],
        ai_plan_result=claim.ai_plan_result,
        ai_evidence_suggestions=_string_list(claim.ai_evidence_suggestions),
        ai_document_suggestions=_string_list(claim.ai_document_suggestions),
        risk_level=claim.risk_level,
        risk_notes=claim.risk_notes,
        notes=claim.notes,
        created_at=claim.created_at.isoformat() if claim.created_at else None,
        updated_at=claim.updated_at.isoformat() if claim.updated_at else None,
        document_count=doc_count,
        evidence_count=len(_evidence_id_list(claim.required_evidence_ids)),
    )


@router.get("/{claim_id}/detail")
def get_claim_detail(claim_id: int, db: Session = Depends(get_db)):
    """获取战役详情（含证据和文书）"""
    details = get_claim_with_details(db, claim_id)
    if not details:
        raise HTTPException(status_code=404, detail="战役不存在")
    return details


@router.put("/{claim_id}", response_model=ClaimResponse)
def update_claim(claim_id: int, request: ClaimUpdate, db: Session = Depends(get_db)):
    """更新战役"""
    claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="战役不存在")
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(claim, key, value)
    
    db.commit()
    db.refresh(claim)
    
    doc_count = db.query(GeneratedDocument).filter(
        GeneratedDocument.claim_id == claim_id
    ).count()
    
    return ClaimResponse(
        id=claim.id,
        case_id=claim.case_id,
        title=claim.title,
        description=claim.description,
        claim_type=claim.claim_type,
        amount=claim.amount,
        priority=claim.priority,
        status=claim.status,
        required_documents=_string_list(claim.required_documents),
        required_evidence_ids=_evidence_id_list(claim.required_evidence_ids),
        depends_on=claim.depends_on or [],
        ai_plan_result=claim.ai_plan_result,
        ai_evidence_suggestions=_string_list(claim.ai_evidence_suggestions),
        ai_document_suggestions=_string_list(claim.ai_document_suggestions),
        risk_level=claim.risk_level,
        risk_notes=claim.risk_notes,
        notes=claim.notes,
        created_at=claim.created_at.isoformat() if claim.created_at else None,
        updated_at=claim.updated_at.isoformat() if claim.updated_at else None,
        document_count=doc_count,
        evidence_count=len(_evidence_id_list(claim.required_evidence_ids)),
    )


@router.delete("/{claim_id}")
def delete_claim(claim_id: int, db: Session = Depends(get_db)):
    """删除战役"""
    claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="战役不存在")
    
    db.delete(claim)
    db.commit()
    return {"success": True, "message": "战役已删除"}


@router.post("/{claim_id}/plan")
def plan_claim(claim_id: int, db: Session = Depends(get_db)):
    """
    AI 规划战役 - 分析需要哪些文书和证据
    
    核心功能：
    1. 分析案件全部证据
    2. 根据战役诉求类型，推荐需要的文书类型
    3. 推荐关键证据（与战役相关的证据）
    4. 评估风险
    5. 分析战役依赖关系
    """
    claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="战役不存在")
    
    # 获取案件信息
    case = db.query(Case).filter(Case.id == claim.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    # 获取案件全部证据
    all_evidences = db.query(EvidenceItem).filter(
        EvidenceItem.case_id == case.id
    ).all()
    
    # 构建证据列表供 AI 分析
    evidence_summary = []
    for i, ev in enumerate(all_evidences, 1):
        evidence_summary.append({
            "index": i,
            "id": ev.id,
            "name": ev.display_name or ev.original_filename or "未命名",
            "type": ev.evidence_type,
            "summary": ev.summary or "无摘要",
        })
    
    # 构建案件信息
    case_info = {
        "case_id": case.id,
        "title": case.title,
        "case_type": case.case_type,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "cause": case.cause,
        "claim_amount": case.claim_amount,
    }
    
    # 构建战役信息
    claim_info = {
        "title": claim.title,
        "description": claim.description,
        "claim_type": claim.claim_type,
        "amount": claim.amount,
    }
    
    # 调用 AI 进行规划
    try:
        plan_result = llm_service.plan_claim(
            case_info=case_info,
            claim_info=claim_info,
            evidence_list=evidence_summary,
        )
        
        # 解析 AI 返回的规划结果
        if isinstance(plan_result, dict):
            # 更新战役
            claim.required_documents = _string_list(plan_result.get("suggested_documents", []))
            claim.required_evidence_ids = _evidence_id_list(plan_result.get("suggested_evidence_ids", []))
            claim.ai_document_suggestions = _string_list(plan_result.get("suggested_documents", []))
            claim.ai_evidence_suggestions = _string_list(plan_result.get("evidence_analysis", []))
            claim.ai_plan_result = plan_result.get("analysis", "")
            claim.risk_level = plan_result.get("risk_level", "medium")
            claim.risk_notes = plan_result.get("risk_notes", "")
            claim.status = CaseClaimStatus.ACTIVE.value
            
            db.commit()
            db.refresh(claim)
            
            return {
                "success": True,
                "message": "战役规划完成",
                "plan": plan_result,
            }
        else:
            # 如果返回的是字符串（文本分析），解析它
            claim.ai_plan_result = plan_result
            claim.status = CaseClaimStatus.ACTIVE.value
            db.commit()
            
            return {
                "success": True,
                "message": "战役分析完成，请查看分析结果后手动配置",
                "plan": {"analysis": plan_result},
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 规划失败: {str(e)}")


@router.post("/{claim_id}/activate")
def activate_claim(claim_id: int, db: Session = Depends(get_db)):
    """激活战役"""
    claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="战役不存在")
    
    claim.status = CaseClaimStatus.ACTIVE.value
    db.commit()
    db.refresh(claim)
    
    return {"success": True, "message": "战役已激活"}


@router.post("/{claim_id}/complete")
def complete_claim(claim_id: int, db: Session = Depends(get_db)):
    """完成战役"""
    claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="战役不存在")
    
    claim.status = CaseClaimStatus.COMPLETED.value
    db.commit()
    db.refresh(claim)
    
    return {"success": True, "message": "战役已完成"}


@router.post("/{claim_id}/evidence")
def add_evidence_to_claim(
    claim_id: int,
    evidence_ids: List[str],
    db: Session = Depends(get_db)
):
    """为战役添加证据"""
    claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="战役不存在")
    
    # 验证证据存在
    existing_ids = _evidence_id_list(claim.required_evidence_ids)
    for ev_id in evidence_ids:
        if ev_id not in existing_ids:
            existing_ids.append(ev_id)
    
    claim.required_evidence_ids = existing_ids
    db.commit()
    db.refresh(claim)
    
    return {"success": True, "message": f"已添加 {len(evidence_ids)} 个证据"}


@router.delete("/{claim_id}/evidence")
def remove_evidence_from_claim(
    claim_id: int,
    evidence_ids: List[str],
    db: Session = Depends(get_db)
):
    """从战役移除证据"""
    claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="战役不存在")
    
    existing_ids = _evidence_id_list(claim.required_evidence_ids)
    for ev_id in evidence_ids:
        if ev_id in existing_ids:
            existing_ids.remove(ev_id)
    
    claim.required_evidence_ids = existing_ids
    db.commit()
    db.refresh(claim)
    
    return {"success": True, "message": f"已移除 {len(evidence_ids)} 个证据"}
