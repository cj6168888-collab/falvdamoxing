"""
案件画像API - 从数据库真实数据构建画像
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
import uuid

from app.db.database import get_db
from app.models.case import Case, ChatMessage
from app.models.document import Document
from app.models.case_profile import CaseProfile as CaseProfileModel
from app.models.conversation import ConversationSession
from app.services.case_profile import CaseProfileEngine, profile_engine
from app.services.intelligence_service import intelligence_service
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/v2/profile", tags=["案件画像"])


class InteractionRequest(BaseModel):
    case_id: int
    user_input: str
    input_type: str
    system_response: str = ""


class KnowledgeQueryRequest(BaseModel):
    case_id: int
    query: str
    knowledge_type: Optional[str] = None


class GapResolveRequest(BaseModel):
    case_id: int
    gap_id: str
    resolution: str


class BuildProfileRequest(BaseModel):
    case_id: int
    use_ai: bool = True


_profile_engine = None

def get_profile_engine():
    global _profile_engine
    if _profile_engine is None:
        _profile_engine = CaseProfileEngine(llm_service)
    return _profile_engine


def _extract_keywords(text: str) -> list:
    words = [
        "合同", "协议", "转账", "付款", "违约", "侵权", "赔偿",
        "微信", "录音", "邮件", "发票", "收据", "银行", "现金",
        "口头", "书面", "承诺", "承认", "否认", "争议", "借款",
        "利息", "本金", "欠款", "诉讼", "法院", "判决",
    ]
    return [w for w in words if w in text][:10]


# _build_knowledge_atoms 辅助逻辑已被迁移至 intelligence_service.get_knowledge_atoms


def _build_conversations(case_id: int, db: Session) -> list:
    chats = db.query(ChatMessage).filter(ChatMessage.case_id == case_id).order_by(ChatMessage.created_at).limit(50).all()
    convs = []
    for i, msg in enumerate(chats):
        if msg.role == "user":
            convs.append({"turn_id": f"chat_{msg.id}", "turn_number": i + 1, "user_input": msg.content[:200] if len(msg.content) > 200 else msg.content, "input_type": "chat", "system_response": "", "created_at": msg.created_at.isoformat() if msg.created_at else ""})
    if not convs:
        sessions = db.query(ConversationSession).filter(ConversationSession.case_id == case_id).order_by(ConversationSession.updated_at.desc()).limit(10).all()
        for sess in sessions:
            if sess.messages and isinstance(sess.messages, list):
                for i, msg in enumerate(sess.messages):
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        convs.append({"turn_id": f"sess_{sess.id}_{i}", "turn_number": i + 1, "user_input": str(msg.get("content", ""))[:200], "input_type": "chat", "system_response": "", "created_at": sess.updated_at.isoformat() if sess.updated_at else ""})
    return convs


def _find_gaps(case: Case, docs: List[Document]) -> dict:
    doc_types = set()
    for doc in docs:
        if doc.doc_type:
            doc_types.add(doc.doc_type)
        if doc.content:
            if "合同" in doc.content or "协议" in doc.content:
                doc_types.add("合同")
            if "转账" in doc.content or "银行" in doc.content:
                doc_types.add("转账凭证")
            if "微信" in doc.content or "聊天" in doc.content:
                doc_types.add("沟通记录")
    gaps = {}
    for et in ["合同", "转账凭证", "沟通记录"]:
        if et not in doc_types:
            gaps[f"gap_{et}"] = {"status": "identified", "severity": "high" if et in ["合同", "转账凭证"] else "medium", "type": et}
    return gaps


def _calc_completeness(case: Case, docs: List[Document], chat_count: int, knowledge_count: int) -> dict:
    score = 0.0
    fields = ["title", "case_type", "plaintiff", "defendant", "cause", "claim_amount"]
    vals = {"title": case.title, "case_type": case.case_type, "plaintiff": case.plaintiff, "defendant": case.defendant, "cause": case.cause, "claim_amount": case.claim_amount}
    filled = sum(1 for f in fields if vals.get(f))
    score += (filled / len(fields)) * 30
    score += min(knowledge_count / 10, 1.0) * 30
    score += min(chat_count / 5, 1.0) * 20
    score += min(len(docs) / 5, 1.0) * 20
    score = round(score, 1)
    if score >= 80:
        level = "完整"
    elif score >= 60:
        level = "详细"
    elif score >= 30:
        level = "基本"
    else:
        level = "稀疏"
    return {"score": score, "level": level}


def _count_by_type(atoms: list) -> dict:
    counts = {}
    for a in atoms:
        t = a.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


def _type_color(t: str) -> str:
    return {"fact": "#3b82f6", "evidence": "#22c55e", "claim": "#f59e0b", "legal": "#8b5cf6", "relation": "#ec4899"}.get(t, "#94a3b8")


def _get_tips(summary: dict) -> List[str]:
    tips = []
    level = summary.get("completeness", {}).get("level", "稀疏")
    if level == "稀疏":
        tips.append("案件信息较少，建议详细描述事件经过")
    elif level == "基本":
        tips.append("基础信息已完备，可以开始上传证据")
    elif level == "详细":
        tips.append("案件信息较完整，可以生成详细分析报告")
    else:
        tips.append("案件信息非常完整")
    gaps = summary.get("unresolved_gaps", [])
    if gaps:
        tips.append(f"还有 {len(gaps)} 个证据缺口待解决")
    ks = summary.get("knowledge_stats", {})
    if ks.get("total", 0) > 0:
        tips.append(f"已从案件数据中提取 {ks['total']} 条知识")
    if summary.get("evidence_count", 0) > 0:
        tips.append(f"已关联 {summary['evidence_count']} 份证据材料")
    return tips


def _save_to_db(case_id: int, data: dict, db: Session):
    db_profile = db.query(CaseProfileModel).filter(CaseProfileModel.case_id == case_id).first()
    if db_profile:
        for k, v in data.items():
            if hasattr(db_profile, k):
                setattr(db_profile, k, v)
        db_profile.last_updated = datetime.utcnow()
        db_profile.version = (db_profile.version or 1) + 1
        db.commit()
    else:
        db.add(CaseProfileModel(case_id=case_id, **{k: v for k, v in data.items() if hasattr(CaseProfileModel, k)}))
        db.commit()


@router.post("/build")
async def build_profile(request: BuildProfileRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 使用全景情报服务构建知识原子
    atoms = intelligence_service.get_knowledge_atoms(db, request.case_id)
    docs = db.query(Document).filter(Document.case_id == request.case_id).all() # 兼容 V1 文档计数
    from app.models.evidence import EvidenceItem
    evidence_items = db.query(EvidenceItem).filter(EvidenceItem.case_id == request.case_id).all()
    convs = _build_conversations(request.case_id, db)
    gaps = _find_gaps(case, docs)
    completeness = _calc_completeness(case, docs, len(convs), len(atoms))

    _save_to_db(request.case_id, {
        "knowledge_atoms": atoms,
        "knowledge_base_count": len(atoms),
        "conversation_history": convs,
        "conversation_count": len(convs),
        "evidence_ids": [d.id for d in docs],
        "tracked_gaps": gaps,
        "completeness_level": completeness["level"],
        "completeness_score": completeness["score"],
    }, db)

    if request.use_ai and llm_service and llm_service.is_configured():
        try:
            doc_lines = [f"- {d.filename}: {d.content_summary or d.content[:100] if d.content else '无摘要'}" for d in docs[:10]]
            prompt = f"""请分析以下案件并提取关键信息：

案件标题: {case.title}
案件类型: {case.case_type}
原告: {case.plaintiff or '未知'}
被告: {case.defendant or '未知'}
案由: {case.cause or '未知'}
诉讼金额: {case.claim_amount or '未知'}
案件描述: {case.description or '无'}

证据材料:
{chr(10).join(doc_lines) if doc_lines else '无证据材料'}

请以JSON格式返回：
{{"core_dispute": "核心争议焦点", "key_legal_issues": ["问题1", "问题2"], "risk_factors": ["风险1", "风险2"]}}
只返回JSON。"""

            response = llm_service.chat(messages=[{"role": "user", "content": prompt}], model="qwen-turbo", max_tokens=1000)
            if response:
                import re
                m = re.search(r'\{[\s\S]*\}', response)
                if m:
                    ai = json.loads(m.group())
                    if "core_dispute" in ai:
                        atoms.append({"atom_id": f"ai_cd_{uuid.uuid4().hex[:8]}", "content": f"核心争议: {ai['core_dispute']}", "type": "legal", "source": "ai_analysis", "confidence": 0.7, "verified": False, "keywords": _extract_keywords(ai["core_dispute"]), "entity_tags": ["legal"], "extracted_at": datetime.utcnow().isoformat()})
                    for issue in ai.get("key_legal_issues", []):
                        atoms.append({"atom_id": f"ai_li_{uuid.uuid4().hex[:8]}", "content": f"法律争议点: {issue}", "type": "legal", "source": "ai_analysis", "confidence": 0.7, "verified": False, "keywords": _extract_keywords(issue), "entity_tags": ["legal"], "extracted_at": datetime.utcnow().isoformat()})
                    for risk in ai.get("risk_factors", []):
                        atoms.append({"atom_id": f"ai_rf_{uuid.uuid4().hex[:8]}", "content": f"风险: {risk}", "type": "claim", "source": "ai_analysis", "confidence": 0.6, "verified": False, "keywords": _extract_keywords(risk), "entity_tags": ["legal"], "extracted_at": datetime.utcnow().isoformat()})
                    _save_to_db(request.case_id, {"knowledge_atoms": atoms, "knowledge_base_count": len(atoms)}, db)
        except Exception as e:
            print(f"AI增强画像失败: {e}")

    return {"success": True, "case_id": request.case_id, "message": "案件画像已生成", "completeness": completeness, "knowledge_count": len(atoms), "evidence_count": len(evidence_items), "gap_count": len(gaps)}


@router.get("/summary/{case_id}")
async def get_profile_summary(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    from app.models.evidence import EvidenceItem
    evidence_items = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).all()
    docs = db.query(Document).filter(Document.case_id == case_id).all()
    
    atoms = intelligence_service.get_knowledge_atoms(db, case_id)
    convs = _build_conversations(case_id, db)
    gaps = _find_gaps(case, docs)
    completeness = _calc_completeness(case, docs, len(convs), len(atoms))

    _save_to_db(case_id, {
        "knowledge_atoms": atoms,
        "knowledge_base_count": len(atoms),
        "conversation_history": convs,
        "conversation_count": len(convs),
        "evidence_ids": [d.id for d in docs],
        "tracked_gaps": gaps,
        "completeness_level": completeness["level"],
        "completeness_score": completeness["score"],
    }, db)

    unresolved = [{"id": k, **v} for k, v in gaps.items() if not v.get("resolved", False)]

    summary = {
        "case_id": case_id,
        "completeness": completeness,
        "knowledge_stats": {"total": len(atoms), "by_type": _count_by_type(atoms)},
        "conversation_count": len(convs),
        "evidence_count": len(evidence_items) or len(docs),
        "unresolved_gaps": unresolved,
        "last_updated": datetime.utcnow().isoformat(),
    }

    return {
        "case_id": case_id,
        "summary": summary,
        "recent_conversations": convs[-10:],
        "recent_knowledge": atoms[-20:],
        "profile_tips": _get_tips(summary),
        "persisted": True,
    }


@router.get("/gaps/{case_id}")
async def get_unresolved_gaps(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    docs = db.query(Document).filter(Document.case_id == case_id).all()
    gaps = _find_gaps(case, docs)
    unresolved = [{"id": k, **v} for k, v in gaps.items() if not v.get("resolved", False)]
    return {"case_id": case_id, "unresolved_gaps": unresolved, "count": len(unresolved)}


@router.get("/knowledge-graph/{case_id}")
async def get_knowledge_graph(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    atoms = intelligence_service.get_knowledge_atoms(db, case_id)

    nodes = [{"id": a["atom_id"], "label": a["content"][:50] + ("..." if len(a["content"]) > 50 else ""), "type": a["type"], "color": _type_color(a["type"]), "verified": a.get("verified", False), "confidence": a.get("confidence", 0.5)} for a in atoms]

    return {"case_id": case_id, "nodes": nodes, "edges": [], "stats": {"total_nodes": len(nodes), "total_edges": 0, "by_type": _count_by_type(atoms)}}


@router.post("/knowledge/query")
async def query_knowledge(request: KnowledgeQueryRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    atoms = intelligence_service.get_knowledge_atoms(db, request.case_id)
    ql = request.query.lower()
    results = [a for a in atoms if (not request.knowledge_type or a.get("type") == request.knowledge_type) and (ql in a.get("content", "").lower() or any(ql in kw.lower() for kw in a.get("keywords", [])))]
    return {"query": request.query, "knowledge_type": request.knowledge_type, "results": results, "count": len(results)}


@router.post("/gap/resolve")
async def resolve_gap(request: GapResolveRequest, db: Session = Depends(get_db)):
    db_profile = db.query(CaseProfileModel).filter(CaseProfileModel.case_id == request.case_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="案件画像不存在")
    gaps = db_profile.tracked_gaps or {}
    if request.gap_id in gaps:
        gaps[request.gap_id]["resolved"] = True
        gaps[request.gap_id]["resolution"] = request.resolution
        gaps[request.gap_id]["resolution_at"] = datetime.utcnow().isoformat()
        db_profile.tracked_gaps = gaps
        db.commit()
    return {"success": True, "case_id": request.case_id, "gap_id": request.gap_id, "resolution": request.resolution, "message": "缺口已标记为已解决"}


@router.post("/interaction")
async def record_interaction(request: InteractionRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    engine = get_profile_engine()
    basic_info = {"id": case.id, "title": case.title, "case_type": case.case_type, "plaintiff": case.plaintiff or "", "defendant": case.defendant or "", "cause": case.cause or "", "claim_amount": case.claim_amount or ""}
    result = engine.process_interaction(case_id=request.case_id, user_input=request.user_input, input_type=request.input_type, system_response=request.system_response, basic_info=basic_info)
    profile = engine.profiles.get(request.case_id)
    if profile:
        _save_to_db(request.case_id, {
            "knowledge_atoms": [a.to_dict() for a in profile.knowledge_base],
            "knowledge_base_count": len(profile.knowledge_base),
            "conversation_history": [{"turn_id": t.turn_id, "turn_number": t.turn_number, "user_input": t.user_input, "input_type": t.input_type, "system_response": t.system_response, "created_at": t.created_at.isoformat()} for t in profile.conversation_history],
            "conversation_count": len(profile.conversation_history),
            "evidence_ids": profile.evidence_ids,
            "tracked_gaps": profile.tracked_gaps,
            "completeness_level": profile.completeness.value,
            "completeness_score": profile.completeness_score,
            "key_milestones": profile.key_milestones,
        }, db)
    return {"success": True, "case_id": request.case_id, **result}
