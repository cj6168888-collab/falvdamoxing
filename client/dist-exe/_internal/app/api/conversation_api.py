"""
对话 API V2
支持智能问答、澄清机制、多轮对话
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.models.case import Case
from app.services.smart_qa_v2 import SmartQAServiceV2, smart_qa_service_v2

router = APIRouter(prefix="/api/conversations", tags=["对话V2"])


@router.get("")
def list_conversations():
    """获取对话列表"""
    return {"conversations": [], "message": "请通过 /api/conversations/history/{case_id} 查询对话历史"}


# ============ 请求模型 ============

class AskQuestionRequest(BaseModel):
    """提问请求"""
    case_id: int
    question: str
    session_id: Optional[str] = None


class ResolveClarificationRequest(BaseModel):
    """处理澄清请求"""
    session_id: str
    clarification_id: str
    answer: str


# ============ API 接口 ============

@router.post("/ask")
async def ask_question(request: AskQuestionRequest, db: Session = Depends(get_db)):
    """
    智能问答
    支持：意图识别、澄清机制、证据引导

    Returns:
        - direct_answer: 清晰问题的完整回答
        - partial_answer: 半清晰问题的部分回答 + 澄清引导
        - clarification_needed: 模糊问题需要澄清
    """
    # 验证案件
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 调用智能问答
    result = smart_qa_service_v2.ask(
        question=request.question,
        case_id=request.case_id,
        session_id=request.session_id
    )

    return result


@router.get("/session/{session_id}")
async def get_session_detail(session_id: str, db: Session = Depends(get_db)):
    """
    获取会话详情
    """
    session_data = smart_qa_service_v2.get_session(session_id)

    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")

    return session_data


@router.post("/clarification/resolve")
async def resolve_clarification(request: ResolveClarificationRequest, db: Session = Depends(get_db)):
    """
    处理澄清回答
    用户回答澄清问题后，继续生成回答
    """
    result = smart_qa_service_v2.resolve_clarification(
        session_id=request.session_id,
        clarification_id=request.clarification_id,
        answer=request.answer
    )

    return result


@router.get("/history/{case_id}")
async def get_conversation_history(case_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """
    获取对话历史
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    history = smart_qa_service_v2.get_conversation_history(case_id, limit)

    return {
        'case_id': case_id,
        'total': len(history),
        'sessions': history
    }


@router.get("/intent-info")
async def get_intent_info():
    """
    获取意图类型信息
    """
    return {
        'intents': SmartQAServiceV2.INTENT_TAXONOMY
    }


@router.get("/clarification-dimensions")
async def get_clarification_dimensions():
    """
    获取澄清维度信息
    """
    return {
        'dimensions': SmartQAServiceV2.CLARIFICATION_DIMENSIONS
    }
