"""
法律知识库 API - 法律法规、司法解释、指导性案例查询
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.models.legal_knowledge_base import (
    LegalArticle, JudicialInterpretation, GuidingCase,
    LitigationCost, JurisdictionRule, ContractTemplate
)
from app.models.document import DocumentTemplate

router = APIRouter(prefix="/api/legal-knowledge", tags=["法律知识库"])


@router.get("/laws")
def search_laws(
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    law_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """搜索法律法规"""
    query = db.query(LegalArticle).filter(LegalArticle.is_valid == True)

    if keyword:
        query = query.filter(
            LegalArticle.title.contains(keyword) |
            LegalArticle.content.contains(keyword) |
            LegalArticle.law_name.contains(keyword)
        )
    if category:
        query = query.filter(LegalArticle.category == category)
    if law_name:
        query = query.filter(LegalArticle.law_name.contains(law_name))

    total = query.count()
    laws = query.order_by(LegalArticle.law_name, LegalArticle.article_number).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "laws": [
            {
                "id": law.id,
                "law_name": law.law_name,
                "article_number": law.article_number,
                "title": law.title,
                "category": law.category,
                "chapter": law.chapter,
                "effective_date": law.effective_date.isoformat() if law.effective_date else None,
                "content_preview": (law.content or "")[:200] + "..." if law.content and len(law.content) > 200 else law.content,
                "content_length": len(law.content or ""),
            }
            for law in laws
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/laws/{law_id}")
def get_law_detail(law_id: str, db: Session = Depends(get_db)):
    """获取法条详情"""
    law = db.query(LegalArticle).filter(LegalArticle.id == law_id).first()
    if not law:
        raise HTTPException(status_code=404, detail="法条不存在")
    return {
        "id": law.id,
        "law_name": law.law_name,
        "article_number": law.article_number,
        "title": law.title,
        "category": law.category,
        "chapter": law.chapter,
        "content": law.content,
        "effective_date": law.effective_date.isoformat() if law.effective_date else None,
        "is_valid": law.is_valid,
        "source": law.source,
        "created_at": law.created_at.isoformat() if law.created_at else None,
    }


@router.get("/interpretations")
def search_interpretations(
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """搜索司法解释"""
    query = db.query(JudicialInterpretation).filter(JudicialInterpretation.is_valid == True)

    if keyword:
        query = query.filter(
            JudicialInterpretation.title.contains(keyword) |
            JudicialInterpretation.content.contains(keyword)
        )

    total = query.count()
    items = query.order_by(JudicialInterpretation.effective_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "interpretations": [
            {
                "id": item.id,
                "title": item.title,
                "doc_number": item.doc_number,
                "effective_date": item.effective_date.isoformat() if item.effective_date else None,
                "content_preview": (item.content or "")[:200] + "..." if item.content and len(item.content) > 200 else item.content,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/cases")
def search_cases(
    keyword: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """搜索指导性案例"""
    query = db.query(GuidingCase)

    if keyword:
        query = query.filter(
            GuidingCase.title.contains(keyword) |
            GuidingCase.summary.contains(keyword) |
            GuidingCase.full_text.contains(keyword)
        )
    if case_type:
        query = query.filter(GuidingCase.case_type == case_type)

    total = query.count()
    items = query.order_by(GuidingCase.publish_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "cases": [
            {
                "id": item.id,
                "title": item.title,
                "case_number": item.case_number,
                "case_type": item.case_type,
                "court": item.court,
                "publish_date": item.publish_date.isoformat() if item.publish_date else None,
                "summary_preview": (item.summary or "")[:200] + "..." if item.summary and len(item.summary) > 200 else item.summary,
                "keywords": item.keywords,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/cases/{case_id}")
def get_case_detail(case_id: str, db: Session = Depends(get_db)):
    """获取案例详情"""
    case = db.query(GuidingCase).filter(GuidingCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    return {
        "id": case.id,
        "title": case.title,
        "case_number": case.case_number,
        "case_type": case.case_type,
        "court": case.court,
        "summary": case.summary,
        "full_text": case.full_text,
        "keywords": case.keywords,
        "related_articles": case.related_articles,
        "publish_date": case.publish_date.isoformat() if case.publish_date else None,
        "source": case.source,
    }


@router.get("/search")
def semantic_search(
    keyword: str = Query(..., min_length=1),
    search_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """全文搜索"""
    results = {"laws": [], "interpretations": [], "cases": []}

    if not search_type or search_type == "laws":
        laws = db.query(LegalArticle).filter(
            LegalArticle.is_valid == True,
            LegalArticle.title.contains(keyword) | LegalArticle.content.contains(keyword)
        ).limit(limit).all()
        results["laws"] = [
            {"id": l.id, "law_name": l.law_name, "article_number": l.article_number, "title": l.title, "type": "law", "preview": (l.content or "")[:100]}
            for l in laws
        ]

    if not search_type or search_type == "interpretations":
        interps = db.query(JudicialInterpretation).filter(
            JudicialInterpretation.is_valid == True,
            JudicialInterpretation.title.contains(keyword) | JudicialInterpretation.content.contains(keyword)
        ).limit(limit).all()
        results["interpretations"] = [
            {"id": i.id, "title": i.title, "type": "interpretation", "preview": (i.content or "")[:100]}
            for i in interps
        ]

    if not search_type or search_type == "cases":
        cases = db.query(GuidingCase).filter(
            GuidingCase.title.contains(keyword) | GuidingCase.summary.contains(keyword)
        ).limit(limit).all()
        results["cases"] = [
            {"id": c.id, "title": c.title, "type": "case", "preview": (c.summary or "")[:100]}
            for c in cases
        ]

    total = len(results["laws"]) + len(results["interpretations"]) + len(results["cases"])
    return {"results": results, "total": total}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """数据统计"""
    return {
        "total_laws": db.query(LegalArticle).count(),
        "total_interpretations": db.query(JudicialInterpretation).count(),
        "total_guiding_cases": db.query(GuidingCase).count(),
        "total_litigation_costs": db.query(LitigationCost).count(),
        "total_document_templates": db.query(DocumentTemplate).count(),
        "total_contract_templates": db.query(ContractTemplate).count(),
    }


@router.post("/import")
def trigger_import(
    db: Session = Depends(get_db)
):
    """触发数据导入"""
    try:
        from app.services.legal_db.run_import import run_all
        result = run_all()
        return {"message": "导入任务已启动", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/export")
def export_data(
    export_type: str = Query("all"),
    format: str = Query("json"),
    db: Session = Depends(get_db)
):
    """导出数据"""
    data = {}

    if export_type in ("all", "laws"):
        laws = db.query(LegalArticle).all()
        data["laws"] = [{"id": l.id, "law_name": l.law_name, "article_number": l.article_number, "title": l.title, "category": l.category, "content": l.content} for l in laws]

    if export_type in ("all", "interpretations"):
        interps = db.query(JudicialInterpretation).all()
        data["interpretations"] = [{"id": i.id, "title": i.title, "doc_number": i.doc_number, "content": i.content} for i in interps]

    if export_type in ("all", "cases"):
        cases = db.query(GuidingCase).all()
        data["cases"] = [{"id": c.id, "title": c.title, "case_number": c.case_number, "summary": c.summary, "full_text": c.full_text} for c in cases]

    return {"data": data, "format": format, "exported_at": datetime.utcnow().isoformat()}
