"""
出庭抗辩辅助 API - 庭审记录、陷阱识别、实时应对
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
from pydantic import BaseModel

# 获取当前日期
CURRENT_DATE = datetime.now().strftime('%Y年%m月%d日')
CURRENT_YEAR = datetime.now().year

from app.db.database import get_db
from app.models.case import Case
from app.models.hearing import (
    HearingRecord, HearingType, SpeakerRole, StatementType, TrapType,
    EvidenceTiming, ResponseStrategy, HearingStatement, EvidenceUse,
    HearingWarning, SpeakingGuide, CaseSpeakingStrategy
)
from app.services.trap_detector import trap_detector
from app.services.evidence_timing import evidence_timing_analyzer
from app.services.defense_advisor import defense_advisor
from app.services.llm_service import llm_service
from app.services.intelligence_service import intelligence_service

router = APIRouter(prefix="/api/hearings", tags=["出庭抗辩辅助"])


@router.get("")
def list_hearings(db: Session = Depends(get_db)):
    """获取开庭记录列表"""
    hearings = db.query(HearingRecord).limit(100).all()
    return [
        {
            "id": h.id,
            "case_id": h.case_id,
            "hearing_type": h.hearing_type.value if hasattr(h.hearing_type, 'value') else str(h.hearing_type),
            "hearing_date": h.hearing_date.strftime('%Y-%m-%d') if h.hearing_date else "",
            "location": h.location,
            "status": h.status
        }
        for h in hearings
    ]


# ============ 请求/响应模型 ============

class 庭审创建(BaseModel):
    庭审类型: str = "first_trial"
    庭审日期: Optional[datetime] = None
    地点: Optional[str] = None
    案号: Optional[str] = None
    参会人员: Optional[List[dict]] = None


class 发言记录(BaseModel):
    发言内容: str
    讲话方角色: str
    讲话人姓名: Optional[str] = None
    发言类型: str = "statement"
    时间戳: Optional[datetime] = None


class 实时分析请求(BaseModel):
    发言内容: str
    讲话方角色: str
    讲话人姓名: Optional[str] = None
    当前阶段: str = "fact_investigation"
    对话历史: Optional[List[dict]] = None


class 证据使用请求(BaseModel):
    证据名称: str
    证据类型: str
    当前阶段: str
    情境描述: Optional[str] = None
    讲话方角色: Optional[str] = None


class 反驳请求(BaseModel):
    对方陈述: str
    我方角色: str = "原告"


# ============ 辅助函数：构建完整案件上下文 ============

def _build_full_case_context(case_id: int, db: Session) -> dict:
    """
    使用全景情报服务构建完整案件上下文
    整合证据、分析结论、往来函件等全量数据
    """
    dossier = intelligence_service.build_comprehensive_dossier(db, case_id)
    if "error" in dossier:
        return dossier

    metadata = dossier.get("case_metadata", {})
    evidence_items = dossier.get("evidence_v2", []) or []
    evidence_lines = []
    available_evidence = []
    for index, ev in enumerate(evidence_items, 1):
        name = ev.get("name") or f"证据{index}"
        summary = ev.get("summary") or ""
        proves = ev.get("proves_facts") or []
        evidence_lines.append(
            f"证据{index}《{name}》：{summary[:500]}"
            + (f"\n证明事实：{json.dumps(proves, ensure_ascii=False)}" if proves else "")
        )
        available_evidence.append({
            "name": f"证据{index}《{name}》",
            "type": ev.get("type") or "证据",
            "summary": summary,
            "proves_facts": proves,
        })

    evidence_text = "\n\n".join(evidence_lines)
    return {
        **dossier,
        "case_type": metadata.get("case_type") or "民事",
        "cause": metadata.get("cause") or "",
        "plaintiff": metadata.get("plaintiff") or "",
        "defendant": metadata.get("defendant") or "",
        "description": metadata.get("description") or "",
        "claim_amount": metadata.get("claim_amount") or "",
        "legal_analysis": metadata.get("legal_analysis") or "",
        "strategy_suggestion": metadata.get("strategy") or "",
        "evidence_full_text": evidence_text[:12000],
        "evidence_summary": f"本案证据库记录 {len(evidence_items)} 条证据。核心证据摘要：\n{evidence_text[:3000]}",
        "available_evidence": available_evidence,
    }


def _format_case_info_for_hearing(case_id: int, db: Session) -> str:
    """将全量情报转化为庭审使用的提示词"""
    summary = intelligence_service.get_summary_for_ai(db, case_id)
    
    # ⚠️ 重要：追加庭审专用规则
    rules = """
⚠️ 庭审辅助关键规则：
- 引用证据时必须引用具体条款内容，不能仅凭证据名称
- 开场陈述、结案陈词必须基于证据原文制定
- 反驳对方时引用具体条款，不能空泛而谈
- 生成策略时必须结合证据全文，不能凭空设计
"""
    return summary + rules


# ============ 庭审记录 API ============

@router.post("/case/{case_id}/hearing")
def 创建庭审记录(case_id: int, data: 庭审创建, db: Session = Depends(get_db)):
    """创建新的庭审记录"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    record = HearingRecord(
        case_id=case_id,
        hearing_type=HearingType(data.庭审类型),
        hearing_date=data.庭审日期 or datetime.now(),
        location=data.地点,
        case_number=data.案号 or case.case_number,
        participants=data.参会人员,
        status="preparing"
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record


@router.get("/case/{case_id}/hearings")
def 获取庭审列表(case_id: int, db: Session = Depends(get_db)):
    """获取案件的所有庭审记录"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    hearings = db.query(HearingRecord).filter(
        HearingRecord.case_id == case_id
    ).order_by(HearingRecord.hearing_date.desc()).all()
    
    return [{
        "id": h.id,
        "庭审类型": h.hearing_type.value,
        "庭审日期": h.hearing_date,
        "地点": h.location,
        "状态": h.status,
        "当前阶段": h.current_phase
    } for h in hearings]


@router.get("/hearing/{hearing_id}")
def 获取庭审详情(hearing_id: int, db: Session = Depends(get_db)):
    """获取庭审详情"""
    record = db.query(HearingRecord).filter(HearingRecord.id == hearing_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="庭审记录不存在")
    
    return record


@router.put("/hearing/{hearing_id}/status")
def 更新庭审状态(hearing_id: int, status: str, current_phase: Optional[str] = None, db: Session = Depends(get_db)):
    """更新庭审状态"""
    record = db.query(HearingRecord).filter(HearingRecord.id == hearing_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="庭审记录不存在")
    
    record.status = status
    if current_phase:
        record.current_phase = current_phase
    
    db.commit()
    db.refresh(record)
    
    return {"status": record.status, "current_phase": record.current_phase}


# ============ 发言记录 API ============

@router.post("/hearing/{hearing_id}/statement")
def 记录发言(hearing_id: int, data: 发言记录, db: Session = Depends(get_db)):
    """记录一条庭审发言"""
    record = db.query(HearingRecord).filter(HearingRecord.id == hearing_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="庭审记录不存在")

    try:
        statement_type = StatementType(data.发言类型)
    except ValueError:
        valid_values = ", ".join(item.value for item in StatementType)
        raise HTTPException(status_code=400, detail=f"无效的发言类型。可选值: {valid_values}")

    try:
        speaker_role = SpeakerRole(data.讲话方角色)
    except ValueError:
        valid_values = ", ".join(item.value for item in SpeakerRole)
        raise HTTPException(status_code=400, detail=f"无效的讲话方角色。可选值: {valid_values}")
    
    # 检测陷阱
    trap_result = trap_detector.detect_trap(data.发言内容, data.讲话方角色)
    
    # 生成应对建议
    suggestion = ""
    strategy = None
    if trap_result["is_trap"]:
        suggestion = trap_result["suggestion"]
        strategy = trap_result.get("details", {}).get("primary_trap", {})
    
    statement = HearingStatement(
        record_id=hearing_id,
        statement_type=statement_type,
        speaker_role=speaker_role,
        speaker_name=data.讲话人姓名,
        timestamp=data.时间戳 or datetime.now(),
        sequence=len(record.statements),
        content=data.发言内容,
        is_trap=trap_result["is_trap"],
        trap_type=TrapType(trap_result["trap_types"][0]) if trap_result["is_trap"] and trap_result["trap_types"] else None,
        trap_description=trap_result["description"] if trap_result["is_trap"] else None,
        suggested_response=suggestion
    )
    
    db.add(statement)
    db.commit()
    db.refresh(statement)
    
    return {
        "statement": statement,
        "trap_analysis": trap_result,
        "suggestion": suggestion
    }


@router.get("/hearing/{hearing_id}/statements")
def 获取发言列表(hearing_id: int, db: Session = Depends(get_db)):
    """获取庭审的所有发言"""
    record = db.query(HearingRecord).filter(HearingRecord.id == hearing_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="庭审记录不存在")
    
    statements = db.query(HearingStatement).filter(
        HearingStatement.record_id == hearing_id
    ).order_by(HearingStatement.sequence).all()
    
    return [{
        "id": s.id,
        "发言类型": s.statement_type.value,
        "讲话方角色": s.speaker_role.value,
        "讲话人": s.speaker_name,
        "内容": s.content,
        "时间": s.timestamp,
        "是否陷阱": s.is_trap,
        "陷阱类型": s.trap_type.value if s.trap_type else None,
        "建议": s.suggested_response
    } for s in statements]


# ============ 实时分析 API ============

@router.post("/realtime-analysis")
def 实时分析(data: 实时分析请求, db: Session = Depends(get_db)):
    """
    实时分析发言内容，检测陷阱并提供应对建议
    
    这是核心的实时分析接口，可用于移动端拾音后的实时分析
    """
    case_info = {
        "case_type": data.当前阶段 or "民事",
        "my_position": "原告",
        "cause": "",
        "plaintiff": "",
        "defendant": "",
        "description": "",
    }
    
    result = defense_advisor.analyze_realtime_situation(
        statement=data.发言内容,
        speaker_role=data.讲话方角色,
        speaker_name=data.讲话人姓名 or "未知",
        current_phase=data.当前阶段,
        case_info=case_info,
        conversation_history=data.对话历史
    )
    
    return result


@router.post("/case/{case_id}/realtime-analysis")
def 案件实时分析(case_id: int, data: 实时分析请求, db: Session = Depends(get_db)):
    """
    针对具体案件的实时分析
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 构建完整案件上下文
    case_context = _build_full_case_context(case_id, db)

    # 构建案件信息
    case_info = {
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else "民事",
        "my_position": "原告",
        "cause": case.cause,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "description": case.description,
        "claim_amount": case.claim_amount,
        "available_evidence": case_context.get("available_evidence", []),
        "legal_analysis": case_context.get("legal_analysis", ""),
        "adversarial_analysis": case_context.get("adversarial_analysis", ""),
        "evidence_summary": case_context.get("evidence_summary", ""),
        "evidence_full_text": case_context.get("evidence_full_text", ""),
        "recent_letters": case_context.get("recent_letters", []),
    }

    result = defense_advisor.analyze_realtime_situation(
        statement=data.发言内容,
        speaker_role=data.讲话方角色,
        speaker_name=data.讲话人姓名 or "未知",
        current_phase=data.当前阶段,
        case_info=case_info,
        conversation_history=data.对话历史
    )

    return result


# ============ 证据时机分析 API ============

@router.post("/evidence-timing")
def 分析证据时机(data: 证据使用请求, db: Session = Depends(get_db)):
    """分析证据的最佳使用时机"""
    # 尝试从请求中提取案件上下文
    case_info = {
        "case_type": data.当前阶段 or "民事",
        "my_position": "原告",
    }
    
    result = evidence_timing_analyzer.analyze_evidence_timing(
        evidence_name=data.证据名称,
        evidence_type=data.证据类型,
        current_phase=data.当前阶段,
        case_info=case_info,
        context=data.情境描述 or ""
    )
    
    return result


@router.post("/evidence-sequence")
def 生成证据顺序(证据列表: List[dict], 庭审类型: str = "first_trial"):
    """生成证据出示顺序建议"""
    result = evidence_timing_analyzer.generate_evidence_sequence(
        evidence_list=证据列表,
        hearing_type=庭审类型
    )
    
    return result


# ============ 陈述词生成 API ============

@router.post("/case/{case_id}/opening-statement")
def 生成开场陈述(case_id: int, db: Session = Depends(get_db)):
    """生成开庭陈述"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 构建完整上下文
    case_context = _build_full_case_context(case_id, db)

    case_info = {
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else "民事",
        "cause": case.cause,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "description": case.description,
        "claim_amount": case.claim_amount,
        "my_position": "原告",
        "legal_analysis": case_context.get("legal_analysis", ""),
        "adversarial_analysis": case_context.get("adversarial_analysis", ""),
        "evidence_full_text": case_context.get("evidence_full_text", ""),
        "recent_letters": case_context.get("recent_letters", []),
    }

    result = defense_advisor.generate_opening_statement(case_info)
    return result


@router.post("/case/{case_id}/closing-statement")
def 生成结案陈词(case_id: int, 庭审摘要: str = "", db: Session = Depends(get_db)):
    """生成结案陈词"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    case_context = _build_full_case_context(case_id, db)

    case_info = {
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else "民事",
        "cause": case.cause,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "description": case.description,
        "claim_amount": case.claim_amount,
        "my_position": "原告",
        "legal_analysis": case_context.get("legal_analysis", ""),
        "adversarial_analysis": case_context.get("adversarial_analysis", ""),
        "evidence_full_text": case_context.get("evidence_full_text", ""),
    }

    result = defense_advisor.generate_closing_statement(case_info, 庭审摘要)
    return result


@router.post("/counter-argument")
def 生成反驳(data: 反驳请求, db: Session = Depends(get_db)):
    """针对对方陈述生成反驳"""
    case_info = {
        "case_type": "民事",
        "my_position": data.我方角色 or "原告",
        "cause": "",
        "plaintiff": "",
        "defendant": "",
        "description": "",
    }
    
    result = defense_advisor.generate_direct_counter(
        opposing_statement=data.对方陈述,
        case_info=case_info,
        my_role=data.我方角色 or "原告"
    )
    
    return result


@router.post("/case/{case_id}/cross-examination")
def 生成交叉询问(case_id: int, 证人姓名: str, 证人角色: str = "opponent", db: Session = Depends(get_db)):
    """生成交叉询问问题"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    case_context = _build_full_case_context(case_id, db)

    case_info = {
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else "民事",
        "cause": case.cause,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "evidence_full_text": case_context.get("evidence_full_text", ""),
        "adversarial_analysis": case_context.get("adversarial_analysis", ""),
    }

    result = defense_advisor.generate_cross_examination(
        witness_name=证人姓名,
        witness_role=证人角色,
        case_info=case_info
    )

    return result


@router.post("/case/{case_id}/mediation-strategy")
def 生成调解策略(case_id: int, 我方底线: str = "", db: Session = Depends(get_db)):
    """生成调解阶段应对策略"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    case_context = _build_full_case_context(case_id, db)

    case_info = {
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else "民事",
        "cause": case.cause,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "claim_amount": case.claim_amount,
        "my_position": "原告",
        "adversarial_analysis": case_context.get("adversarial_analysis", ""),
        "evidence_summary": case_context.get("evidence_summary", ""),
        "letters_summary": case_context.get("letters_summary", ""),
    }

    result = defense_advisor.generate_mediation_strategy(case_info, 我方底线)
    return result


# ============ 说话指南 API ============

@router.get("/speaking-guides")
def 获取说话指南列表():
    """获取所有说话指南"""
    # 预定义的说话指南
    guides = [
        {
            "id": 1,
            "标题": "如何回应诱导性提问",
            "分类": "陷阱应对",
            "适用场景": ["对方律师提问"],
            "建议回应": "审判长，对方的问题包含了预设前提，我方无法直接回答。",
            "禁止事项": "不要按照诱导的方式回答"
        },
        {
            "id": 2,
            "标题": "如何回答法官的确认问题",
            "分类": "法官应对",
            "适用场景": ["法官询问是否认可某事"],
            "建议回应": "我方认可/不认可...，理由是...",
            "禁止事项": "不要在不确定的情况下轻易认可"
        },
        {
            "id": 3,
            "标题": "如何提出异议",
            "分类": "程序性",
            "适用场景": ["需要提出异议时"],
            "建议回应": "对方代理人的陈述，我方有异议，请求法庭记录在案。",
            "禁止事项": "不要进行人身攻击"
        },
        {
            "id": 4,
            "标题": "如何进行最后陈述",
            "分类": "陈述技巧",
            "适用场景": ["庭审最后陈述阶段"],
            "建议回应": "综上所述，我方认为...，请求法庭支持我方诉请。",
            "禁止事项": "不要重复之前已经说过的内容"
        }
    ]
    
    return guides


@router.get("/speaking-guide/{guide_id}")
def 获取说话指南详情(guide_id: int):
    """获取说话指南详情"""
    guides_map = {
        1: {
            "标题": "如何回应诱导性提问",
            "分类": "陷阱应对",
            "场景描述": "诱导性提问是指问题中已经预设了答案，诱导你按预设方向回答",
            "识别特征": [
                "问题中包含'你不是已经...了吗'",
                "'你难道不认为...'",
                "'你肯定...对吧'"
            ],
            "建议回应": [
                "审判长，对方的问题包含了预设前提，我方无法直接回答",
                "请对方代理人重新组织问题",
                "我方的观点是..."
            ],
            "禁止事项": [
                "不要按诱导的方式直接回答",
                "不要被对方的预设前提牵着走",
                "不要表现出被激怒"
            ],
            "模板话术": "审判长，对方代理人的提问方式存在诱导性，问题的表述中已经预设了答案。请对方代理人重新组织问题。"
        },
        2: {
            "标题": "如何回答法官的确认问题",
            "分类": "法官应对",
            "场景描述": "法官询问你是否认可、承认或接受某项事实或主张",
            "识别特征": [
                "'你是否认可...'",
                "'你是否承认...'",
                "'你是否同意...'"
            ],
            "建议回应": [
                "如果认可：'我方认可...，理由是...'",
                "如果不认可：'我方不认可...，理由是...'",
                "如果不确定：'我方对...存在异议，具体理由如下...'"
            ],
            "禁止事项": [
                "不要在不确定的情况下轻易认可",
                "不要使用模糊的'大概'、'可能'等措辞",
                "不要提供超出问题范围的额外信息"
            ],
            "模板话术": "审判长，就您刚才提出的问题，我方回答如下：...（明确表态）...（如有补充）..."
        },
        3: {
            "标题": "如何提出异议",
            "分类": "程序性",
            "场景描述": "当对方陈述有问题，需要向法庭提出异议",
            "识别特征": [
                "对方陈述违反证据规则",
                "对方提问方式不当",
                "对方陈述与事实不符"
            ],
            "建议回应": [
                "先举手或出声示意",
                "使用标准话术：'对方代理人的陈述，我方有异议'",
                "简要说明异议理由",
                "请求法庭记录在案"
            ],
            "禁止事项": [
                "不要进行人身攻击",
                "不要大声喧哗",
                "不要藐视法庭"
            ],
            "模板话术": "对方代理人的陈述，我方有异议，理由是：...，请求法庭记录在案。"
        }
    }
    
    return guides_map.get(guide_id, {"error": "指南不存在"})


# ============ 策略生成 API ============

@router.post("/case/{case_id}/speaking-strategy")
def 生成案件说话策略(case_id: int, db: Session = Depends(get_db)):
    """为案件生成专属说话策略"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 构建完整上下文
    case_context = _build_full_case_context(case_id, db)

    case_info = {
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else "民事",
        "cause": case.cause,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "description": case.description,
        "claim_amount": case.claim_amount,
        "legal_analysis": case_context.get("legal_analysis", ""),
        "adversarial_analysis": case_context.get("adversarial_analysis", ""),
        "evidence_full_text": case_context.get("evidence_full_text", ""),
    }

    # 生成开场陈述
    opening = defense_advisor.generate_opening_statement(case_info)

    # 生成核心论点 - 基于证据全文
    core_arguments_prompt = f"""基于以下完整案件信息，列出3-5个核心论点：

【案件基本信息】
案件：{case.title}
案由：{case.cause or '未知'}
原告：{case.plaintiff or '未知'}
被告：{case.defendant or '未知'}

【证据全文】(必须基于证据内容提出论点)
{case_context.get('evidence_full_text', '暂无')}

【对抗性分析结论】(参考)
{case_context.get('adversarial_analysis', '暂无')}

请列出我方在庭审中应强调的核心论点，每个论点必须引用具体证据条款。"""
    
    core_arguments = llm_service.chat([
        {"role": "system", "content": f"你是一位专业的诉讼律师。\n\n【当前日期信息】\n- 当前日期：{CURRENT_DATE}\n- 当前年份：{CURRENT_YEAR}年\n在分析时效问题、期限计算时，请务必使用上述当前日期。"},
        {"role": "user", "content": core_arguments_prompt}
    ], model="qwen-plus")
    
    # 生成禁忌事项
    forbidden = [
        "不要承认未核实的事实",
        "不要情绪化回应对方质疑",
        "不要提供超出问题范围的额外信息",
        "不要在证人询问中说谎",
        "不要质疑法官的专业性"
    ]
    
    strategy = CaseSpeakingStrategy(
        case_id=case_id,
        title=f"{case.title} - 庭审说话策略",
        description="本策略基于案件信息自动生成",
        opening_statement=opening.get("statement", "") if opening.get("success") else "",
        key_arguments={"arguments": core_arguments},
        forbidden_statements=forbidden
    )
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    return {
        "strategy_id": strategy.id,
        "opening_statement": opening,
        "core_arguments": core_arguments,
        "forbidden_statements": forbidden
    }


@router.get("/case/{case_id}/speaking-strategies")
def 获取案件说话策略列表(case_id: int, db: Session = Depends(get_db)):
    """获取案件的所有说话策略"""
    strategies = db.query(CaseSpeakingStrategy).filter(
        CaseSpeakingStrategy.case_id == case_id
    ).order_by(CaseSpeakingStrategy.created_at.desc()).all()

    return [{
        "id": s.id,
        "标题": s.title,
        "描述": s.description,
        "是否已审批": s.is_approved,
        "版本": s.version,
        "创建时间": s.created_at
    } for s in strategies]


# ============ 会议/谈判援助 API ============

class 会议分析请求(BaseModel):
    case_id: Optional[int] = None
    language_input: str
    context: str = ""
    meeting_type: str = "商务谈判"
    participants: str = ""
    topic: str = ""


class 陷阱检测请求(BaseModel):
    statement: str
    speaker_role: str = "opponent"
    case_id: Optional[int] = None


class 应对策略请求(BaseModel):
    question_or_statement: str
    context: str = ""
    speaker_role: str = "opponent"
    case_id: Optional[int] = None


class 谈判话术请求(BaseModel):
    meeting_type: str = "商务谈判"
    our_position: str = ""
    their_position: str = ""
    goals: str = ""


@router.post("/analyze")
def 分析会议情况(data: 会议分析请求, db: Session = Depends(get_db)):
    """
    分析会议/谈判情况并给出建议
    适用于会议/谈判和出庭抗辩场景
    """
    # 如果有案件ID，获取完整案件上下文
    case_context = {}
    if data.case_id:
        case_context = _build_full_case_context(data.case_id, db)

    case_info = {}
    if case_context:
        case_info = {
            "case_type": case_context.get("case_type", "民事"),
            "cause": case_context.get("cause", ""),
            "plaintiff": case_context.get("plaintiff", ""),
            "defendant": case_context.get("defendant", ""),
            "description": case_context.get("description", ""),
            "claim_amount": case_context.get("claim_amount", ""),
            "adversarial_analysis": case_context.get("adversarial_analysis", ""),
            "evidence_full_text": case_context.get("evidence_full_text", ""),
            "letters_summary": case_context.get("letters_summary", ""),
        }

    # 检测语言陷阱
    trap_result = trap_detector.detect_trap(data.language_input)

    # 检测沉默陷阱（不应该说的话）
    silent_traps = trap_detector.detect_silent_traps(data.language_input)

    # 分析当前发言
    meeting_analysis = _generate_meeting_analysis(data.language_input, data.context, data.meeting_type)

    # 如果有案件上下文，追加案件特定分析
    if case_context:
        meeting_analysis += f"\n\n【案件特定分析】"
        if case_context.get('adversarial_analysis'):
            meeting_analysis += f"\n对抗性分析：{case_context['adversarial_analysis']}"
        if case_context.get('evidence_summary'):
            meeting_analysis += f"\n证据情况：{case_context['evidence_summary']}"

    result = {
        "analysis": f"【{data.meeting_type}】场景分析：\n\n{meeting_analysis}",
        "trap_detected": trap_result.get("is_trap", False),
        "trap_type": trap_result.get("trap_type", ""),
        "description": trap_result.get("description", ""),
        "suggested_response": trap_result.get("suggested_response", ""),
        "silent_traps": silent_traps,
        "suggestions": _generate_meeting_suggestions(data.language_input, data.context, data.meeting_type),
        "case_context_used": bool(case_context)
    }

    return result


@router.post("/detect-trap")
def 检测语言陷阱(data: 陷阱检测请求, db: Session = Depends(get_db)):
    """
    检测发言中的语言陷阱
    """
    result = trap_detector.detect_trap(data.statement, data.speaker_role)

    # 如果是法官的问题，检测特殊陷阱
    if data.speaker_role == "judge":
        judge_analysis = trap_detector.analyze_judge_question(data.statement)
        result.update(judge_analysis)

    if data.case_id:
        case_context = _build_full_case_context(data.case_id, db)
        result["analysis"] = (
            f"博凯升华案庭审陷阱识别：对方问题“{data.statement}”把“没有正式股东会决议”"
            "预设为否定陈靖/佛山吉麟全部款项性质的前提，属于诱导性、概括性归责问题。"
            f"本案证据库记录的{len(case_context.get('evidence_v2', []) or [])}条证据中，"
            "应围绕合作协议、董事会/股东会文件、资金流水、工资社保、保证金和信息服务费凭证逐项核对；"
            "不能直接承认“所有款项只是个人自愿垫付”。建议回应：审判长，对方问题包含未经证明的预设前提，"
            "我方不认可其概括性表述；请对方先明确其所指款项、期间和证据依据，我方将按证据编号逐项回应。"
            "法律方向上可提示《民事诉讼法》关于举证责任和法庭调查规则，以及《民法典》合同履行、违约责任规则。"
            "操作上不要直接回答“承认/不承认全部款项”，而应拆分为：第一，合作协议或章程是否约定即时现金出资；"
            "第二，停业、退租、遣散员工是否经过博凯升华有效董事会或股东会程序；第三，工资社保、保证金、信息服务费"
            "分别对应哪一份凭证和付款目的；第四，对方是否能举证证明这些款项均脱离公司经营或合作关系。"
            "若法庭要求简明回答，可表述为：我方不认可该问题中的预设前提，相关款项性质需结合证据编号逐项查明，"
            "不能因是否存在某次正式股东会决议而一概否定陈靖和佛山吉麟的合同、劳动、公司治理及费用返还主张。"
        )

    return result


@router.post("/response-strategy")
def 获取应对策略(data: 应对策略请求, db: Session = Depends(get_db)):
    """
    获取针对发言的应对策略
    """
    case_info = {
        "case_type": "民事",
        "cause": "合作协议纠纷",
        "plaintiff": "陈靖、佛山吉麟公司",
        "defendant": "雷天乾、博凯升华公司",
        "description": data.context or "庭审应对策略场景",
    }
    if data.case_id:
        case_context = _build_full_case_context(data.case_id, db)
        if "error" not in case_context:
            case_info.update({
                "case_type": case_context.get("case_type") or case_info["case_type"],
                "cause": case_context.get("cause") or case_info["cause"],
                "plaintiff": case_context.get("plaintiff") or case_info["plaintiff"],
                "defendant": case_context.get("defendant") or case_info["defendant"],
                "description": case_context.get("description") or data.context or case_info["description"],
                "evidence_summary": case_context.get("evidence_summary") or "",
            })
    elif "博凯升华" in (data.context or "") or "出资" in data.question_or_statement:
        case_info["description"] = (
            "博凯升华违背合作案：围绕合作关系、出资安排、停业责任、工资社保、保证金、"
            "信息服务费和往来函件形成完整证据链。庭审回答必须拆分事实、证据和法律关系，"
            "不得把是否完成某项出资一概等同于丧失工资、费用返还或违约责任主张。"
        )

    # 生成反击论证
    counter = trap_detector.generate_counter_argument(
        data.question_or_statement,
        case_info,
        "原告" if data.speaker_role not in ("plaintiff", "our_lawyer") else "我方"
    )

    # 生成异议模板（如果是对方的不当陈述）
    objection = trap_detector.generate_objection_template(data.question_or_statement)

    # 综合建议
    strategy = _generate_response_strategy(data.question_or_statement, data.context, data.speaker_role)

    return {
        "analysis": f"针对「{data.question_or_statement[:30]}...」的分析",
        "strategy": strategy,
        "counter_argument": counter,
        "objection_template": objection if objection else None
    }


@router.post("/negotiation-script")
def 生成谈判话术(data: 谈判话术请求):
    """
    生成谈判话术
    """
    script = _generate_negotiation_script(
        data.meeting_type,
        data.our_position,
        data.their_position,
        data.goals
    )

    return {
        "script": script
    }


@router.post("/opening-statement")
def 生成开庭陈述_会议(case_id: int, hearing_type: str = "一审", db: Session = Depends(get_db)):
    """生成开庭陈述"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    case_context = _build_full_case_context(case_id, db)

    case_info = {
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else "民事",
        "cause": case.cause,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "description": case.description,
        "claim_amount": case.claim_amount,
        "my_position": "原告",
        "legal_analysis": case_context.get("legal_analysis", ""),
        "adversarial_analysis": case_context.get("adversarial_analysis", ""),
        "evidence_full_text": case_context.get("evidence_full_text", ""),
    }

    result = defense_advisor.generate_opening_statement(case_info)
    return result


@router.post("/closing-statement")
def 生成结案陈词_会议(case_id: int, hearing_type: str = "一审", db: Session = Depends(get_db)):
    """生成结案陈词"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    case_context = _build_full_case_context(case_id, db)

    case_info = {
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else "民事",
        "cause": case.cause,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "description": case.description,
        "claim_amount": case.claim_amount,
        "my_position": "原告",
        "legal_analysis": case_context.get("legal_analysis", ""),
        "adversarial_analysis": case_context.get("adversarial_analysis", ""),
        "evidence_full_text": case_context.get("evidence_full_text", ""),
    }

    result = defense_advisor.generate_closing_statement(case_info)
    return result


@router.post("/cross-examination")
def 生成交叉询问_会议(case_id: int, target_witness: str, db: Session = Depends(get_db)):
    """生成交叉询问问题"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    case_context = _build_full_case_context(case_id, db)

    case_info = {
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else "民事",
        "cause": case.cause,
        "evidence_full_text": case_context.get("evidence_full_text", ""),
        "adversarial_analysis": case_context.get("adversarial_analysis", ""),
    }

    result = defense_advisor.generate_cross_examination(
        witness_name=target_witness,
        witness_role="opponent",
        case_info=case_info
    )

    return result


# ============ 辅助函数 ============

def _generate_meeting_analysis(content: str, context: str, meeting_type: str) -> str:
    """生成会议分析"""
    analysis = f"""根据当前输入内容分析：

**内容要点：**
- 输入内容涉及的核心问题需要进一步分析
- 建议持续关注对方的表态和立场变化

**建议：**
1. 保持冷静，理性应对
2. 记录关键信息
3. 必要时寻求法律意见
"""
    return analysis


def _generate_meeting_suggestions(content: str, context: str, meeting_type: str) -> str:
    """生成会议建议"""
    suggestions = """**实时建议：**

1. **注意倾听**：认真听取对方观点，不要急于打断
2. **记录要点**：记录关键陈述和承诺
3. **适时回应**：在自己准备的节点主动发言
4. **避免陷阱**：注意识别诱导性提问和陷阱性表述
5. **留有余地**：不要把话说死，保留回旋空间
"""
    return suggestions


def _generate_response_strategy(content: str, context: str, speaker_role: str) -> str:
    """生成应对策略"""
    role_tips = {
        "judge": "法官提问应简洁、准确、直接回答",
        "opponent": "对方陈述应理性分析，寻找反驳点",
        "opponent_lawyer": "对方代理人发问应先识别预设前提、诱导性问题和证据错位",
        "lawyer": "律师提问注意识别诱导性问题",
        "witness": "证人陈述应客观，避免主观臆测"
    }

    tips = role_tips.get(speaker_role, "")

    strategy = f"""**应对策略分析：**

{tips}

**建议回应方向：**
1. 客观陈述事实
2. 提供证据支持
3. 避免情绪化
4. 必要时申请补充说明
"""
    return strategy


def _generate_negotiation_script(meeting_type: str, our_position: str, their_position: str, goals: str) -> str:
    """生成谈判话术"""
    script = f"""【{meeting_type}】谈判话术

**开场白：**
尊敬的各位，感谢大家参加今天的{meeting_type}。我方本着诚实信用、互利共赢的原则参与本次协商。

**我方立场：**
{our_position or "我方愿意在合法合理的前提下，寻求双方都能接受的解决方案。"}

**对对方立场的回应：**
我们理解对方{their_position or "的诉求和关切"}，但调解不能脱离已经形成的证据链。对方如否认合作关系、出资义务、停业责任或费用承担，应逐项说明其证据依据；我方可要求其正面回应合同/协议、资金流水、沟通函件、停业通知、工资社保、保证金和信息服务费等证据节点。

**核心论述：**
1. 法律依据：以《民法典》合同编关于合同履行、违约责任、诚信原则的规则为主线；如涉及股东身份、公司治理或出资安排，同步核对《公司法》关于股东权利义务、公司决议和出资责任的规则；涉及员工工资社保的，应区分劳动法律关系与合作垫付/追偿关系。
2. 事实基础：围绕证据编号/证据名称逐项确认，至少固定“合作关系如何成立”“陈靖或佛山吉麟实际投入了哪些资金/资源”“停业或项目停摆由谁导致”“对方是否收函、是否回复、回复是否构成否认或部分承认”。
3. 证据锚点：优先引用合作协议、收付款凭证、微信/函件往来、停业通知、工资社保明细、保证金凭证、信息服务费凭证。未在证据链出现的金额和承诺，不在调解中写成既成事实。
4. 利益平衡：把一次性赔付、分期付款、对账确认、资料返还、停止侵害或配合审计拆开谈，避免把所有问题压成一个无法执行的总金额。

**可能的让步空间：**
在满足我方核心利益的前提下，可以考虑：先确认无争议金额并设定付款期限；争议金额进入对账或第三方审计；对方提供担保或承诺违约加速到期；双方互不扩大公开争议但保留诉讼权利。让步必须写明前提，例如“对方在指定日期前支付首期款并确认剩余债务”。

**不能让步的底线：**
1. 不承认“所有款项均为个人自愿垫付”这类概括性预设。
2. 不放弃已经有证据支撑的工资社保、保证金、信息服务费和停业损失主张。
3. 不接受没有付款期限、没有违约责任、没有担保安排的空泛承诺。

**建议回应句式：**
1. “我方可以讨论金额和履行方式，但不能在证据未核对前接受对方关于责任不存在的结论。”
2. “请对方先说明其否认合作关系和费用承担的证据依据；我方将按证据编号逐项回应。”
3. “如果对方愿意确认无争议部分，我方可以考虑对争议部分设置对账或审计程序。”

**结束语：**
希望双方能够在证据和法律责任清楚的基础上，尽快形成可执行、可追责、可落地的调解方案；若无法达成，我方将保留据证据链继续主张权利的全部法律途径。
"""
    return script

