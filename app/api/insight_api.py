"""
增强的案件分析API - 集成智能洞察引擎
解决三大核心问题：
1. 超时问题：分段生成 + 报告缓存
2. 问答质量：问题澄清 + 意图识别
3. 证据管理：知识图谱 + 信度分析
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.models.case import Case
from app.models.document import Document
from app.services.llm_service import llm_service
from app.services.insight_engine import CaseInsightEngine, QuestionIntent
from app.api.evidence import normalize_evidence_type

router = APIRouter(prefix="/api/v2", tags=["增强分析API"])


# ============ 请求模型 ============

class QuestionRequest(BaseModel):
    """问答请求"""
    question: str
    case_id: int


class AnswerRequest(BaseModel):
    """追问回答"""
    case_id: int
    question: str
    answers: dict  # 用户对澄清问题的回答


class EvidenceAnalysisRequest(BaseModel):
    """证据分析请求"""
    case_id: int
    force_refresh: bool = False  # 是否强制重新分析


class ReportRequest(BaseModel):
    """报告生成请求"""
    case_id: int
    report_type: str = "analysis"  # analysis/strategy/full_analysis
    force_regenerate: bool = False


# ============ 全局引擎实例 ============

# 懒加载引擎
_insight_engine = None

def get_insight_engine():
    global _insight_engine
    if _insight_engine is None:
        _insight_engine = CaseInsightEngine(llm_service)
    return _insight_engine


# ============ 智能问答API ============

@router.post("/question")
async def smart_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """
    智能问答 - 带问题澄清机制
    
    工作流程：
    1. 分析用户问题，识别意图和模糊点
    2. 如果问题模糊，返回澄清问题让用户选择
    3. 如果问题清晰，直接回答
    
    返回格式：
    {
        "needs_clarification": true/false,
        "intent": "意图类型",
        "key_entities": [...],
        "clarifying_questions": [...],  // 如果需要澄清
        "answer": "..."  // 如果直接回答
    }
    """
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    case_info = {
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "cause": case.cause or "",
        "plaintiff": case.plaintiff or "",
        "defendant": case.defendant or "",
        "claim_amount": case.claim_amount or "",
        "description": case.description or "",
        "supplement": case.supplement or ""
    }
    
    engine = get_insight_engine()
    
    # 调用智能问答
    result = await engine.answer_with_clarification(
        question=request.question,
        case_info=case_info
    )
    
    return result


@router.post("/question/answer")
async def answer_clarified(request: AnswerRequest, db: Session = Depends(get_db)):
    """
    回答澄清问题后继续问答
    
    用户选择或回答澄清问题后，系统基于回答生成精准答案
    """
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    case_info = {
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "cause": case.cause or "",
        "plaintiff": case.plaintiff or "",
        "defendant": case.defendant or "",
        "claim_amount": case.claim_amount or "",
        "description": case.description or "",
        "supplement": case.supplement or ""
    }
    
    # 构建补充信息
    clarifications = "\n".join([
        f"- {k}: {v}" for k, v in request.answers.items()
    ])
    
    full_question = f"""{request.question}

【用户补充信息】：
{clarifications}"""
    
    engine = get_insight_engine()
    
    # 直接回答，不再次澄清
    result = await engine.answer_with_clarification(
        question=full_question,
        case_info=case_info
    )
    
    return {
        "needs_clarification": False,
        "answer": result.get("answer", ""),
        "intent": result.get("intent", "")
    }


# ============ 证据知识图谱API ============

@router.post("/evidence/graph")
async def build_evidence_graph(request: EvidenceAnalysisRequest, db: Session = Depends(get_db)):
    """
    构建证据知识图谱
    
    对案件的所有证据进行深度分析，包括：
    - 证据证明力参考
    - 证据关联关系
    - 矛盾证据识别
    - 关键词索引
    """
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    # 获取案件的证据
    docs = db.query(Document).filter(
        Document.case_id == request.case_id
    ).all()
    
    evidence_list = []
    for doc in docs:
        if doc.doc_type and ("证据" in doc.doc_type or doc.doc_type.startswith("证据")):
            evidence_list.append({
                "id": str(doc.id),
                "name": doc.filename,
                "type": normalize_evidence_type(doc.doc_type) if doc.doc_type else "未知",
                "content": doc.content or doc.content_summary or "",
                "source": "上传文档",
                "custody": case.plaintiff or "原告"
            })
    
    if not evidence_list:
        return {
            "message": "没有找到证据，请先上传证据",
            "nodes": []
        }
    
    engine = get_insight_engine()
    
    # 构建图谱
    nodes = await engine.build_evidence_graph(
        case_id=request.case_id,
        evidence_list=evidence_list
    )
    
    # 转换结果
    node_data = [
        {
            "id": n.evidence_id,
            "name": n.name,
            "type": n.evidence_type,
            "credibility": n.credibility,
            "credibility_factors": n.credibility_factors,
            "proves_facts": n.proves_facts,
            "related_evidence": n.related_evidence,
            "contradicts_evidence": n.contradicts_evidence,
            "keywords": n.keywords
        }
        for n in nodes
    ]
    
    # 获取摘要
    summary = engine.get_evidence_summary(request.case_id)
    
    return {
        "case_id": request.case_id,
        "nodes": node_data,
        "summary": summary,
        "total_evidence": len(nodes)
    }


@router.get("/evidence/query/{case_id}")
async def query_evidence(
    case_id: int,
    query: str = Query(..., description="查询关键词"),
    search_type: str = Query("all", description="查询类型: all/keywords/related/contradicts"),
    db: Session = Depends(get_db)
):
    """
    精准查询证据
    
    支持多种查询方式：
    - all: 全局检索
    - keywords: 关键词检索
    - related: 相关证据
    - contradicts: 矛盾证据
    """
    engine = get_insight_engine()
    
    nodes = await engine.query_evidence(
        case_id=case_id,
        query=query,
        search_type=search_type
    )
    
    return {
        "query": query,
        "search_type": search_type,
        "results": [
            {
                "id": n.evidence_id,
                "name": n.name,
                "type": n.evidence_type,
                "credibility": n.credibility,
                "proves_facts": n.proves_facts,
                "keywords": n.keywords
            }
            for n in nodes
        ],
        "count": len(nodes)
    }


# ============ 报告生成API ============

@router.post("/report/generate")
async def generate_report(request: ReportRequest, db: Session = Depends(get_db)):
    """
    生成分析报告 - 分段输出
    
    支持的报告类型：
    - analysis: 案件分析报告（7章节）
    - strategy: 策略建议报告（4章节）
    - full_analysis: 完整对抗性分析（6大章节）
    
    特点：
    - 分段生成，可实时看到进度
    - 报告缓存，24小时内不重复生成
    - 支持强制重新生成
    """
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    case_info = {
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "cause": case.cause or "",
        "plaintiff": case.plaintiff or "",
        "defendant": case.defendant or "",
        "claim_amount": case.claim_amount or "",
        "description": case.description or "",
        "supplement": case.supplement or ""
    }
    
    engine = get_insight_engine()
    
    # 如果强制重新生成，清除缓存
    if request.force_regenerate:
        engine.invalidate_cache(request.case_id)
    
    # 生成报告
    segments = []
    full_content = ""
    
    async def on_progress(progress: float, status: str):
        segments.append({
            "progress": progress,
            "status": status
        })
    
    async for segment in engine.generate_report_streaming(
        case_id=request.case_id,
        report_type=request.report_type,
        case_info=case_info,
        on_progress=on_progress
    ):
        full_content += segment
    
    return {
        "case_id": request.case_id,
        "report_type": request.report_type,
        "content": full_content,
        "segments": segments,
        "generated_at": datetime.now().isoformat(),
        "word_count": len(full_content)
    }


@router.get("/report/status/{case_id}")
async def get_report_status(
    case_id: int,
    report_type: str = Query("analysis", description="报告类型")
):
    """
    获取报告生成状态
    """
    engine = get_insight_engine()
    cache_key = f"{case_id}_{report_type}_{datetime.now().strftime('%Y%m%d')}"
    
    if cache_key in engine.analysis_cache:
        task = engine.analysis_cache[cache_key]
        return {
            "status": task.status.value,
            "progress": task.progress,
            "segments": task.segments,
            "error": task.error
        }
    
    return {
        "status": "not_started",
        "progress": 0,
        "segments": []
    }


# ============ 证据信度分析API ============

@router.get("/evidence/credibility/{evidence_id}")
async def get_evidence_credibility(
    evidence_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个证据的信度分析
    """
    doc = db.query(Document).filter(Document.id == evidence_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="证据不存在")
    
    case = db.query(Case).filter(Case.id == doc.case_id).first()
    
    engine = get_insight_engine()
    
    # 构建证据信息
    evidence = {
        "id": str(doc.id),
        "name": doc.filename,
        "type": normalize_evidence_type(doc.doc_type) if doc.doc_type else "未知",
        "content": doc.content or doc.content_summary or "",
        "source": "上传文档",
        "custody": case.plaintiff if case else "未知"
    }
    
    # 分析信度
    credibility = await engine._analyze_evidence_credibility(evidence)
    
    # 提取关键词
    keywords = await engine._extract_evidence_keywords(evidence)
    
    return {
        "evidence_id": evidence_id,
        "name": doc.filename,
        "credibility_score": credibility["score"],
        "credibility_factors": credibility["factors"],
        "proves_facts": credibility["proves_facts"],
        "keywords": keywords
    }


# ============ 清除缓存API ============

@router.post("/cache/clear/{case_id}")
async def clear_case_cache(case_id: int):
    """
    清除案件的缓存，强制重新分析
    """
    engine = get_insight_engine()
    engine.invalidate_cache(case_id)
    
    return {
        "message": f"案件 {case_id} 的缓存已清除",
        "cleared_items": ["report_cache", "analysis_cache"]
    }
