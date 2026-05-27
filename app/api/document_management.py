"""
文书管理 API - 逻辑闭环
包括：生成文书持久化、文书建议管理、文书关联追踪
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.models.case import Case
from app.models.document import Document, GeneratedDocument, DocumentSuggestion
from app.models.letter import Letter
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/document-management", tags=["文书管理"])


class DocumentSuggestionCreate(BaseModel):
    """创建文书建议"""
    doc_type: str
    doc_name: Optional[str] = None
    description: Optional[str] = None
    source: str = "ai_analysis"
    source_detail: Optional[str] = None
    priority: str = "中"
    ai_reason: Optional[str] = None
    legal_basis: Optional[str] = None
    suggested_evidence_ids: Optional[List[int]] = None
    suggested_letter_id: Optional[int] = None
    analysis_snapshot: Optional[str] = None


@router.get("")
def list_documents():
    """获取文书管理列表"""
    return {"documents": [], "message": "请通过 /api/document-management/case/{case_id}/generated 查询案件生成文书"}


@router.get("/case/{case_id}/generated")
def get_case_generated_documents(case_id: int, db: Session = Depends(get_db)):
    """获取案件的所有生成文书"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    docs = db.query(GeneratedDocument).filter(
        GeneratedDocument.case_id == case_id
    ).order_by(GeneratedDocument.created_at.desc()).all()

    result = []
    for doc in docs:
        result.append({
            "id": doc.id,
            "title": doc.title,
            "document_type": doc.document_type,
            "content": doc.content,
            "status": doc.status,
            "version": doc.version,
            "based_on_adversarial": doc.based_on_adversarial_analysis,
            "based_on_ai_analysis": doc.based_on_ai_analysis,
            "generation_context": doc.generation_context,
            "related_letter_id": doc.related_letter_id,
            "referenced_evidence": doc.referenced_evidence,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        })

    return result


@router.get("/generated/{doc_id}")
def get_generated_document_detail(doc_id: int, db: Session = Depends(get_db)):
    """获取生成文书的详情"""
    doc = db.query(GeneratedDocument).filter(GeneratedDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文书不存在")

    return {
        "id": doc.id,
        "case_id": doc.case_id,
        "title": doc.title,
        "document_type": doc.document_type,
        "content": doc.content,
        "status": doc.status,
        "version": doc.version,
        "based_on_adversarial": doc.based_on_adversarial_analysis,
        "based_on_ai_analysis": doc.based_on_ai_analysis,
        "ai_analysis_summary": doc.ai_analysis_summary,
        "generation_context": doc.generation_context,
        "strategy_notes": doc.strategy_notes,
        "related_letter_id": doc.related_letter_id,
        "related_evidence_ids": doc.related_evidence_ids,
        "referenced_evidence": doc.referenced_evidence,
        "mail_status": doc.mail_status,
        "mail_sent_date": doc.mail_sent_date,
        "tracking_number": doc.tracking_number,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at
    }


@router.put("/generated/{doc_id}")
def update_generated_document(doc_id: int, status: Optional[str] = None, content: Optional[str] = None, db: Session = Depends(get_db)):
    """更新生成文书（修改状态或内容）"""
    doc = db.query(GeneratedDocument).filter(GeneratedDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文书不存在")

    if status:
        doc.status = status
        if status == "sent":
            doc.mail_status = "sent"
            doc.mail_sent_date = datetime.utcnow()

    if content:
        doc.content = content

    db.commit()
    db.refresh(doc)

    return {"id": doc.id, "status": doc.status, "updated_at": doc.updated_at}


@router.delete("/generated/{doc_id}")
def delete_generated_document(doc_id: int, db: Session = Depends(get_db)):
    """删除生成文书（软删除，改为归档状态）"""
    doc = db.query(GeneratedDocument).filter(GeneratedDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文书不存在")

    doc.status = "archived"
    doc.is_current = False
    db.commit()

    return {"message": "文书已归档"}


# ============ 文书建议 API ============

@router.post("/case/{case_id}/suggestions")
def create_document_suggestion(case_id: int, data: DocumentSuggestionCreate, db: Session = Depends(get_db)):
    """创建文书建议（逻辑闭环：从AI分析提取文书生成建议）"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    suggestion = DocumentSuggestion(
        case_id=case_id,
        doc_type=data.doc_type,
        doc_name=data.doc_name or data.doc_type,
        description=data.description,
        source=data.source,
        source_detail=data.source_detail,
        priority=data.priority,
        ai_reason=data.ai_reason,
        legal_basis=data.legal_basis,
        suggested_evidence_ids=data.suggested_evidence_ids or [],
        suggested_letter_id=data.suggested_letter_id,
        analysis_snapshot=data.analysis_snapshot,
        based_on_analysis_at=datetime.utcnow()
    )

    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)

    return {
        "id": suggestion.id,
        "doc_type": suggestion.doc_type,
        "status": suggestion.status,
        "created_at": suggestion.created_at
    }


@router.get("/case/{case_id}/suggestions")
def get_case_document_suggestions(case_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    """获取案件的文书建议列表"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    query = db.query(DocumentSuggestion).filter(DocumentSuggestion.case_id == case_id)

    if status:
        query = query.filter(DocumentSuggestion.status == status)

    suggestions = query.order_by(DocumentSuggestion.order, DocumentSuggestion.created_at.desc()).all()

    result = []
    for s in suggestions:
        result.append({
            "id": s.id,
            "doc_type": s.doc_type,
            "doc_name": s.doc_name,
            "description": s.description,
            "source": s.source,
            "priority": s.priority,
            "ai_reason": s.ai_reason,
            "legal_basis": s.legal_basis,
            "status": s.status,
            "generated_doc_id": s.generated_doc_id,
            "suggested_letter_id": s.suggested_letter_id,
            "suggested_evidence_ids": s.suggested_evidence_ids,
            "created_at": s.created_at
        })

    return result


@router.put("/suggestions/{suggestion_id}")
def update_document_suggestion(suggestion_id: int, status: Optional[str] = None, generated_doc_id: Optional[int] = None, db: Session = Depends(get_db)):
    """更新文书建议状态"""
    suggestion = db.query(DocumentSuggestion).filter(DocumentSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="建议不存在")

    if status:
        suggestion.status = status
    if generated_doc_id:
        suggestion.generated_doc_id = generated_doc_id

    db.commit()
    db.refresh(suggestion)

    return {"id": suggestion.id, "status": suggestion.status}


@router.delete("/suggestions/{suggestion_id}")
def delete_document_suggestion(suggestion_id: int, reason: Optional[str] = None, db: Session = Depends(get_db)):
    """删除文书建议"""
    suggestion = db.query(DocumentSuggestion).filter(DocumentSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="建议不存在")

    suggestion.status = "cancelled"
    suggestion.cancelled_reason = reason or "用户取消"
    db.commit()

    return {"message": "建议已取消"}


# ============ 从AI分析提取文书建议 API ============

@router.post("/case/{case_id}/extract-suggestions")
def extract_suggestions_from_ai_analysis(case_id: int, db: Session = Depends(get_db)):
    """
    从案件AI分析结果中提取文书生成建议
    逻辑闭环：AI分析 → 文书建议 → 文书生成
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    if not case.legal_analysis:
        return {"suggestions": [], "message": "暂无AI分析结果"}

    # 检查已有的建议，避免重复
    existing = db.query(DocumentSuggestion).filter(
        DocumentSuggestion.case_id == case_id,
        DocumentSuggestion.status == "pending"
    ).count()

    if existing > 0:
        return {
            "suggestions": [],
            "message": f"已有 {existing} 条待生成建议，请先生成后再提取新的"
        }

    # ��AI分析文本中提取文书建议
    import re
    suggestions = []

    # 常见的文书类型关键词
    doc_type_patterns = {
        "催告函": ["催告函", "催款函", "催还函", "催促"],
        "律师函": ["律师函", "律师声明", "法律函告"],
        "起诉状": ["起诉状", "民事起诉", "提起诉讼"],
        "答辩状": ["答辩状", "民事答辩", "答辩"],
        "上诉状": ["上诉状", "提起上诉", "上诉"],
        "申请书": ["申请书", "申请", "申请书"],
        "和解协议": ["和解", "和解协议", "协商解决"],
        "证据目录": ["证据目录", "证据清单", "举证"],
        "财产保全": ["财产保全", "查封", "冻结"],
        "管辖权异议": ["管辖权异议", "管辖异议"],
    }

    analysis_text = case.legal_analysis

    for doc_type, keywords in doc_type_patterns.items():
        for keyword in keywords:
            if keyword in analysis_text:
                # 提取周围的上下文作为建议理由
                pattern = rf'.{{0,100}}{re.escape(keyword)}.{{0,100}}'
                matches = re.findall(pattern, analysis_text)
                context = matches[0] if matches else ""

                # 检查是否已存在
                exists = db.query(DocumentSuggestion).filter(
                    DocumentSuggestion.case_id == case_id,
                    DocumentSuggestion.doc_type == doc_type,
                    DocumentSuggestion.status.in_(["pending", "generated"])
                ).first()

                if not exists:
                    suggestion = DocumentSuggestion(
                        case_id=case_id,
                        doc_type=doc_type,
                        doc_name=doc_type,
                        source="ai_analysis",
                        source_detail=f"从legal_analysis提取，关键词：{keyword}",
                        priority="中",
                        ai_reason=f"AI分析中提及「{keyword}」：{context[:100]}..." if context else f"AI分析建议生成{doc_type}",
                        analysis_snapshot=analysis_text[:500],
                        based_on_analysis_at=datetime.utcnow()
                    )
                    db.add(suggestion)
                    suggestions.append(doc_type)
                break

    db.commit()

    return {
        "suggestions": suggestions,
        "count": len(suggestions),
        "message": f"已从AI分析中提取 {len(suggestions)} 条文书建议"
    }


# ============ 文书关联追踪 API ============

@router.get("/case/{case_id}/timeline")
def get_case_document_timeline(case_id: int, db: Session = Depends(get_db)):
    """获取案件的文书时间线（逻辑闭环：展示完整的数据流转）"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    timeline = []

    # 1. 获取AI分析
    if case.legal_analysis:
        timeline.append({
            "type": "ai_analysis",
            "title": "AI法律分析完成",
            "content": case.legal_analysis[:200],
            "timestamp": case.updated_at,
            "related_items": []
        })

    # 2. 获取文书建议
    suggestions = db.query(DocumentSuggestion).filter(
        DocumentSuggestion.case_id == case_id
    ).order_by(DocumentSuggestion.created_at).all()

    for s in suggestions:
        timeline.append({
            "type": "document_suggestion",
            "title": f"文书建议：{s.doc_type}",
            "content": s.ai_reason or "",
            "timestamp": s.created_at,
            "status": s.status,
            "related_items": []
        })

    # 3. 获取生成文书
    docs = db.query(GeneratedDocument).filter(
        GeneratedDocument.case_id == case_id
    ).order_by(GeneratedDocument.created_at).all()

    for doc in docs:
        timeline.append({
            "type": "generated_document",
            "title": f"生成文书：{doc.document_type}",
            "content": doc.generation_context or doc.content[:200],
            "timestamp": doc.created_at,
            "status": doc.status,
            "based_on_adversarial": doc.based_on_adversarial_analysis,
            "based_on_ai_analysis": doc.based_on_ai_analysis,
            "related_items": doc.referenced_evidence
        })

    # 4. 获取函件
    letters = db.query(Letter).filter(
        Letter.case_id == case_id
    ).order_by(Letter.letter_date).all()

    for letter in letters:
        timeline.append({
            "type": "letter",
            "title": f"{'收到' if letter.direction.value == 'incoming' else '发出'}：{letter.title}",
            "content": letter.content_summary or "",
            "timestamp": letter.letter_date or letter.created_at,
            "direction": letter.direction.value,
            "is_replied": letter.is_replied,
            "related_items": []
        })

    # 按时间排序
    timeline.sort(key=lambda x: x.get("timestamp") or datetime.min, reverse=True)

    return timeline


# ============ 文书修改对话 API ============

class DocumentModifyRequest(BaseModel):
    """文书修改请求"""
    document_id: int
    feedback: str


class DocumentModifyResponse(BaseModel):
    """文书修改响应"""
    content: str
    reply: str


@router.post("/modify")
def modify_document_by_chat(request: DocumentModifyRequest, db: Session = Depends(get_db)):
    """
    通过对话方式修改文书
    用户输入修改意见，AI基于原文书内容生成新版本
    """
    doc = db.query(GeneratedDocument).filter(GeneratedDocument.id == request.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文书不存在")

    # 构建 prompt
    prompt = f"""你是一位专业的法律文书助手。请根据用户的修改意见，对以下法律文书进行修改完善。

原文书内容：
{doc.content}

用户修改意见：
{request.feedback}

请按以下JSON格式返回结果：
{{
  "content": "修改后的完整文书内容",
  "reply": "对用户的回复，说明修改了哪些地方（100字以内）"
}}

要求：
1. 保持法律文书的专业性和规范性
2. 根据用户意见进行针对性修改
3. 返回完整的文书内容，不要省略
4. reply字段简要说明修改要点
"""

    try:
        llm_result = llm_service.generate_text(prompt, max_tokens=16384)
        
        # 解析 JSON 响应
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', llm_result)
        if json_match:
            result = json.loads(json_match.group())
            new_content = result.get('content', doc.content)
            reply = result.get('reply', '已根据您的要求修改文书')
        else:
            # 如果解析失败，直接使用返回结果作为内容
            new_content = llm_result
            reply = '已根据您的要求修改文书'
        
        # 更新数据库
        doc.content = new_content
        doc.version = (doc.version or 1) + 1
        doc.updated_at = datetime.utcnow()

        # 保存修改历史（记忆功能）
        history = doc.modification_history or []
        history.append({
            "feedback": request.feedback,
            "timestamp": datetime.utcnow().isoformat(),
            "version": doc.version,
            "change_summary": reply
        })
        doc.modification_history = history

        db.commit()
        db.refresh(doc)
        
        return {
            "content": new_content,
            "reply": reply
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修改失败: {str(e)}")