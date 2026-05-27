"""
单条证据智能问答 API
==================
提供针对单条证据的深度问答接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.db.database import get_db
from app.services.evidence_qa import (
    evidence_qa_service,
    EvidenceQuestionContext,
    EvidenceSpecificQAService
)
from app.services.evidence_v2 import evidence_service_v2
from app.api.evidence import normalize_evidence_type

router = APIRouter(prefix="/api/evidence/qa", tags=["证据问答"])


@router.get("")
def get_qa_info():
    """获取证据问答信息"""
    return {"message": "请使用 POST /api/evidence/qa/ask 进行问答"}


# ============ 请求模型 ============

class EvidenceQARequest(BaseModel):
    """单条证据问答请求"""
    evidence_id: str
    question: str
    conversation_id: Optional[str] = None


class EvidenceQAContextRequest(BaseModel):
    """带上下文的问答请求"""
    evidence_id: Optional[str] = None
    question: Optional[str] = None
    conversation_id: Optional[str] = None
    case_id: Optional[int] = None


# ============ API 接口 ============

@router.post("")
async def ask_evidence_qa(
    request: EvidenceQAContextRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    证据问答主入口 - 支持 case_id + question 格式
    """
    if request.evidence_id:
        # 有证据ID，直接进行问答
        evidence = evidence_service_v2.get_evidence_by_id(request.evidence_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="证据不存在")

        evidence_context = EvidenceQuestionContext(
            evidence_id=evidence.get('id', ''),
            evidence_name=evidence.get('original_filename', '') or evidence.get('summary', '')[:30],
            evidence_type=evidence.get('evidence_type', 'OTHER'),
            evidence_content=evidence.get('extracted_content', '') or evidence.get('raw_content', '') or evidence.get('summary', ''),
            case_id=evidence.get('case_id', 0),
            proves_facts=[f.get('fact', '') for f in (evidence.get('proves_facts', []) or [])],
            credibility_score=evidence.get('credibility_score', 50.0)
        )

        conversation_id = request.conversation_id
        if not conversation_id:
            import uuid
            conversation_id = str(uuid.uuid4())

        result = evidence_qa_service.ask(
            conversation_id=conversation_id,
            evidence_context=evidence_context,
            question=request.question or ""
        )
        return result

    if request.case_id and request.question:
        # 基于案件ID的问答，获取案件所有证据
        from app.models.document import Document as DocModel
        docs = db.query(DocModel).filter(DocModel.case_id == request.case_id).all()
        if not docs:
            return {"case_id": request.case_id, "message": "该案件暂无证据，请先上传证据", "answer": ""}

        # 使用第一个文档的上下文
        doc = docs[0]
        evidence_context = EvidenceQuestionContext(
            evidence_id=str(doc.id),
            evidence_name=doc.filename,
            evidence_type=normalize_evidence_type(doc.doc_type) if doc.doc_type else "未知",
            evidence_content=doc.content or doc.content_summary or "",
            case_id=request.case_id,
            proves_facts=[],
            credibility_score=50.0
        )

        conversation_id = request.conversation_id
        if not conversation_id:
            import uuid
            conversation_id = str(uuid.uuid4())

        result = evidence_qa_service.ask(
            conversation_id=conversation_id,
            evidence_context=evidence_context,
            question=request.question
        )
        return result

    return {"error": "请指定证据ID或案件ID和问题"}


@router.post("/ask")
async def ask_about_evidence(
    request: EvidenceQAContextRequest,
    db: Session = Depends(get_db)
):
    """
    针对单条证据进行智能问答

    功能：
    1. 自动加载证据上下文
    2. 内置防跑偏机制
    3. 支持多轮对话

    防跑偏机制会：
    - 检测问题是否与当前证据相关
    - 如果跑偏，自动引导回到正题
    - 验证回答的相关性
    """
    # 获取证据信息
    evidence = evidence_service_v2.get_evidence_by_id(request.evidence_id)

    if not evidence:
        raise HTTPException(status_code=404, detail="证据不存在")

    # 构建证据上下文 - 优先使用完整提取的内容
    evidence_context = EvidenceQuestionContext(
        evidence_id=evidence.get('id', ''),
        evidence_name=evidence.get('original_filename', '') or evidence.get('summary', '')[:30],
        evidence_type=evidence.get('evidence_type', 'OTHER'),
        # 优先级: extracted_content > raw_content > summary
        evidence_content=evidence.get('extracted_content', '') or evidence.get('raw_content', '') or evidence.get('summary', ''),
        case_id=evidence.get('case_id', 0),
        proves_facts=[f.get('fact', '') for f in (evidence.get('proves_facts', []) or [])],
        credibility_score=evidence.get('credibility_score', 50.0)
    )

    # 生成或使用对话ID
    conversation_id = request.conversation_id
    if not conversation_id:
        import uuid
        conversation_id = str(uuid.uuid4())

    # 进行问答
    result = evidence_qa_service.ask(
        conversation_id=conversation_id,
        evidence_context=evidence_context,
        question=request.question
    )

    return result


@router.get("/templates")
async def get_question_templates():
    """
    获取证据专有问题模板

    返回按类别分类的预设问题
    """
    templates = evidence_qa_service.get_question_templates()

    # 转换为前端友好的格式
    result = []
    for key, template in templates.items():
        result.append({
            "category": key,
            "name": template["name"],
            "icon": template["icon"],
            "questions": template["questions"]
        })

    return {"templates": result}


@router.post("/validate-question")
async def validate_question(
    evidence_id: str = Query(None),
    question: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    预验证问题是否与证据相关

    用于在用户发送问题前检测话题边界
    """
    # 获取证据信息
    evidence = evidence_service_v2.get_evidence_by_id(evidence_id)

    if not evidence:
        raise HTTPException(status_code=404, detail="证据不存在")

    # 构建上下文（简化版）- 优先使用完整提取的内容
    from app.services.evidence_qa import EvidenceQAAntiDeviation, EvidenceQuestionContext

    evidence_context = EvidenceQuestionContext(
        evidence_id=evidence.get('id', ''),
        evidence_name=evidence.get('original_filename', '') or evidence.get('summary', '')[:30],
        evidence_type=evidence.get('evidence_type', 'OTHER'),
        # 优先级: extracted_content > raw_content > summary
        evidence_content=evidence.get('extracted_content', '') or evidence.get('raw_content', '') or evidence.get('summary', ''),
        case_id=evidence.get('case_id', 0)
    )

    # 创建防跑偏实例并检查
    anti_dev = EvidenceQAAntiDeviation(evidence_context)
    analysis = anti_dev.check_topic_boundary(question)

    return {
        "question": question,
        "is_on_topic": analysis.scope.value in ["on_topic", "related"],
        "scope": analysis.scope.value,
        "relevance_score": analysis.relevance_score,
        "reason": analysis.reason,
        "redirect_suggestion": analysis.redirect_suggestion,
        "suggested_questions": evidence_qa_service._get_suggested_questions(evidence.get('evidence_type', 'OTHER'))[:3]
    }


@router.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    清除某个对话会话

    用于重置对话上下文
    """
    success = evidence_qa_service.clear_conversation(conversation_id)

    if success:
        return {"message": "对话已清除", "conversation_id": conversation_id}
    else:
        return {"message": "对话不存在", "conversation_id": conversation_id}


@router.get("/evidence/{evidence_id}/context")
async def get_evidence_context(evidence_id: str, db: Session = Depends(get_db)):
    """
    获取证据上下文摘要

    用于前端显示证据信息
    """
    evidence = evidence_service_v2.get_evidence_by_id(evidence_id)

    if not evidence:
        raise HTTPException(status_code=404, detail="证据不存在")

    return {
        "id": evidence.get('id'),
        "name": evidence.get('original_filename', '') or evidence.get('summary', '')[:50],
        "type": evidence.get('evidence_type'),
        "type_name": evidence.get('evidence_type_name'),
        "summary": evidence.get('summary', ''),
        "credibility": evidence.get('credibility_score', 0),
        "proves_facts": [f.get('fact', '') for f in (evidence.get('proves_facts', []) or [])],
        "source_party": evidence.get('source_party')
    }


@router.post("/batch-questions")
async def get_batch_question_suggestions(
    evidence_id: str,
    db: Session = Depends(get_db)
):
    """
    获取批量问题建议

    返回多个类别的快捷问题
    """
    evidence = evidence_service_v2.get_evidence_by_id(evidence_id)

    if not evidence:
        raise HTTPException(status_code=404, detail="证据不存在")

    templates = evidence_qa_service.get_question_templates()

    suggestions = []
    for key, template in templates.items():
        # 每个类别取一个问题
        suggestions.append({
            "category": key,
            "icon": template["icon"],
            "name": template["name"],
            "question": template["questions"][0] if template["questions"] else ""
        })

    return {"suggestions": suggestions}
