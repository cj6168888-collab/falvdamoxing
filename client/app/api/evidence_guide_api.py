"""
交互式证据补充API
================
核心理念：像资深律师问诊一样，系统主动发现问题，
         用通俗易懂的方式引导用户补充信息。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.models.case import Case
from app.models.document import Document
from app.services.evidence_navigator import EvidenceNavigator, EvidenceGapSeverity
from app.services.llm_service import llm_service
from app.api.evidence import normalize_evidence_type

router = APIRouter(prefix="/api/v2/evidence-guide", tags=["交互式证据引导"])


# ============ 请求模型 ============

class DiagnoseRequest(BaseModel):
    """诊断请求"""
    case_id: int
    force_refresh: bool = False


class AnswerQuestionRequest(BaseModel):
    """回答问题请求"""
    case_id: int
    question_id: str
    answer: str  # 用户选择或输入的答案


class AddEvidenceRequest(BaseModel):
    """添加证据请求"""
    case_id: int
    name: str
    description: str = ""
    evidence_type: str = "其他"
    custody: str = "原告"
    content: str = ""


# ============ 全局导航实例 ============

_navigator = None

def get_navigator():
    global _navigator
    if _navigator is None:
        _navigator = EvidenceNavigator(llm_service)
    return _navigator


# ============ 核心API ============

@router.post("/diagnose")
async def diagnose_case(request: DiagnoseRequest, db: Session = Depends(get_db)):
    """
    诊断案件 - 全面分析现有证据和缺口
    
    像体检一样，系统会：
    1. 分析现有证据的完整性和证明力
    2. 识别关键的证据缺口
    3. 评估案件准备度
    4. 提供可视化的证据图谱数据
    """
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    # 获取案件的证据
    docs = db.query(Document).filter(Document.case_id == request.case_id).all()
    
    evidence_list = []
    for doc in docs:
        if doc.doc_type and ("证据" in doc.doc_type or doc.doc_type.startswith("证据")):
            evidence_list.append({
                "id": str(doc.id),
                "name": doc.filename,
                "type": normalize_evidence_type(doc.doc_type) if doc.doc_type else "其他",
                "description": doc.content_summary or "",
                "content": doc.content or "",
                "custody": case.plaintiff or "原告",
                "status": "已提交"
            })
        else:
            # 普通文档也作为证据看待
            evidence_list.append({
                "id": str(doc.id),
                "name": doc.filename,
                "type": normalize_evidence_type(doc.doc_type) if doc.doc_type else "其他",
                "description": doc.content_summary or "",
                "content": doc.content or "",
                "custody": case.plaintiff or "原告",
                "status": "已提交"
            })
    
    # 构建案件信息
    case_info = {
        "id": case.id,
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "cause": case.cause or "",
        "plaintiff": case.plaintiff or "",
        "defendant": case.defendant or "",
        "claim_amount": case.claim_amount or "",
        "description": case.description or "",
        "claims": [case.cause or ""]  # 诉请默认为案由
    }
    
    # 执行诊断
    navigator = get_navigator()
    diagnosis = navigator.diagnose_case(case_info, evidence_list)
    
    # 生成引导问题
    questions = navigator.generate_guidance_questions(case_info, diagnosis)
    
    # 获取图谱数据
    graph_data = navigator.get_evidence_graph_data(diagnosis)
    
    return {
        "case_id": request.case_id,
        "diagnosis": {
            "overall_score": diagnosis.overall_score,
            "readiness_level": _get_readiness_level(diagnosis.overall_score),
            "proof_chain_completeness": diagnosis.proof_chain_completeness,
            "evidence_count": len(diagnosis.submitted_evidence),
            "gaps_count": len(diagnosis.evidence_gaps),
            "critical_gaps_count": len([g for g in diagnosis.evidence_gaps if g.severity == EvidenceGapSeverity.CRITICAL])
        },
        "evidence_analysis": {
            "submitted": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.evidence_type,
                    "strength": e.strength,
                    "proves": e.proves,
                    "status": e.status
                }
                for e in diagnosis.submitted_evidence
            ],
            "type_distribution": diagnosis.evidence_type_distribution
        },
        "gaps_analysis": {
            "critical": [
                _format_gap(g) for g in diagnosis.evidence_gaps 
                if g.severity == EvidenceGapSeverity.CRITICAL
            ],
            "important": [
                _format_gap(g) for g in diagnosis.evidence_gaps 
                if g.severity == EvidenceGapSeverity.IMPORTANT
            ],
            "optional": [
                _format_gap(g) for g in diagnosis.evidence_gaps 
                if g.severity == EvidenceGapSeverity.OPTIONAL
            ]
        },
        "critical_findings": diagnosis.critical_findings,
        "immediate_actions": diagnosis.immediate_actions,
        "guidance_questions": [
            {
                "id": q.question_id,
                "category": q.category,
                "question": q.question,
                "help_text": q.help_text,
                "options": q.options,
                "input_type": q.input_type
            }
            for q in questions[:5]  # 最多返回5个问题
        ],
        "graph_data": graph_data,
        "diagnosed_at": diagnosis.diagnosed_at.isoformat()
    }


@router.post("/question/answer")
async def answer_guidance_question(
    request: AnswerQuestionRequest, 
    db: Session = Depends(get_db)
):
    """
    回答引导问题
    
    用户选择或输入答案后，系统会：
    1. 分析回答，更新诊断
    2. 如果发现新证据线索，提供上传指引
    3. 如果确认缺口，给出替代方案
    4. 生成下一个引导问题
    """
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    navigator = get_navigator()
    
    # 重新获取证据列表
    docs = db.query(Document).filter(Document.case_id == request.case_id).all()
    evidence_list = [
        {
            "id": str(doc.id),
            "name": doc.filename,
            "type": normalize_evidence_type(doc.doc_type) if doc.doc_type else "其他",
            "description": doc.content_summary or "",
            "custody": case.plaintiff or "原告"
        }
        for doc in docs
    ]
    
    case_info = {
        "id": case.id,
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "cause": case.cause or "",
        "claim_amount": case.claim_amount or ""
    }
    
    # 重新诊断
    diagnosis = navigator.diagnose_case(case_info, evidence_list)
    
    # 处理回答
    result = navigator.process_answer(
        request.case_id, 
        request.question_id, 
        request.answer, 
        diagnosis
    )
    
    # 根据回答生成后续建议
    suggestions = []
    next_question = None
    
    # 分析回答内容（支持中英文关键词）
    answer_lower = request.answer.lower()
    
    if "signed" in answer_lower or "有签订" in request.answer or "签了" in request.answer or "合同" in request.answer or "协议" in request.answer:
        suggestions.append({
            "type": "positive",
            "message": "很好！书面合同是很有力的证据",
            "action": "请尽快上传合同原件或扫描件"
        })
    elif "bank" in answer_lower or "转账" in request.answer or "银行" in request.answer or "流水" in request.answer or "汇款" in request.answer:
        suggestions.append({
            "type": "positive", 
            "message": "银行转账记录证明力很强",
            "action": "请前往银行打印流水账单"
        })
    elif "wechat" in answer_lower or "微信" in request.answer or "聊天记录" in request.answer or "聊天" in request.answer:
        suggestions.append({
            "type": "positive",
            "message": "微信记录可以作为证据使用",
            "action": "请导出微信聊天记录并截图保存"
        })
    elif "yes" in answer_lower or "有" in request.answer or "是的" in request.answer or "对" in request.answer:
        suggestions.append({
            "type": "action",
            "message": "请详细描述或上传相关证据",
            "action": "点击上方'上传证据'按钮添加"
        })
    elif "no" in answer_lower or "没有" in request.answer or "没" in request.answer or "不" in request.answer:
        suggestions.append({
            "type": "warning",
            "message": "缺少直接证据，需要寻找替代方案",
            "alternatives": [
                "1. 寻找间接证据形成证据链",
                "2. 申请法院调查取证",
                "3. 寻找知情人作证"
            ]
        })
    
    # 生成下一个问题（基于当前缺口的下一个引导问题）
    remaining_gaps = [
        g for g in diagnosis.evidence_gaps 
        if g.severity == EvidenceGapSeverity.CRITICAL
    ][:2]
    
    if remaining_gaps:
        next_q = navigator._create_gap_question(remaining_gaps[0])
        if next_q:
            next_question = {
                "id": next_q.question_id,
                "question": next_q.question,
                "options": next_q.options,
                "help_text": next_q.help_text
            }
    
    return {
        "question_id": request.question_id,
        "answer_received": request.answer,
        "suggestions": suggestions,
        "next_question": next_question,
        "updated_diagnosis": {
            "score": diagnosis.overall_score,
            "gaps_remaining": len(diagnosis.evidence_gaps)
        }
    }


@router.post("/evidence/add")
async def add_evidence_from_guide(
    request: AddEvidenceRequest, 
    db: Session = Depends(get_db)
):
    """
    从引导流程中添加证据
    
    用户在引导过程中发现新证据，可以直接添加
    """
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    # 创建新文档
    content = request.content or ""
    new_doc = Document(
        case_id=request.case_id,
        filename=request.name,
        stored_path=f"guided-evidence://case/{request.case_id}/{request.name}",
        file_type="text/plain",
        file_size=len(content.encode("utf-8")),
        doc_type=f"证据_{request.evidence_type}",
        content=content,
        content_summary=request.description[:500] if request.description else "",
        created_by=case.plaintiff or "用户",
        uploaded_by=case.plaintiff or "用户"
    )
    
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    return {
        "success": True,
        "document_id": new_doc.id,
        "message": f"证据'{request.name}'已添加成功",
        "tip": "建议重新运行诊断，系统会分析新证据的作用"
    }


@router.get("/evidence-types")
async def get_evidence_types():
    """
    获取所有证据类型及说明
    
    帮助用户理解不同证据的作用
    """
    return {
        "types": [
            {
                "type": "书面证据",
                "description": "合同、协议、函件、证书等纸质文件",
                "examples": ["软件开发合同", "保密协议", "发票收据", "学历证书"],
                "proof_purpose": "证明法律关系和具体约定",
                "strength": "高",
                "obtaining_tips": ["联系对方获取原件", "调取工商档案", "政府信息公开"]
            },
            {
                "type": "转账凭证",
                "description": "银行转账记录、支付宝/微信支付记录",
                "examples": ["银行流水", "转账截图", "支付凭证"],
                "proof_purpose": "证明款项支付和收取",
                "strength": "高",
                "obtaining_tips": ["银行柜台打印", "手机银行导出", "申请法院调查令"]
            },
            {
                "type": "沟通记录",
                "description": "微信、短信、邮件、通话录音等",
                "examples": ["微信聊天记录", "工作邮件", "通话录音", "短信往来"],
                "proof_purpose": "证明双方沟通过程和事实确认",
                "strength": "中高",
                "obtaining_tips": ["手机截图保存", "邮箱导出", "通话录音公证"]
            },
            {
                "type": "视听资料",
                "description": "录音、录像、照片等",
                "examples": ["现场录音", "监控录像", "现场照片", "视频录像"],
                "proof_purpose": "证明事实发生经过",
                "strength": "中",
                "obtaining_tips": ["手机录音录像", "监控调取申请", "现场拍照公证"]
            },
            {
                "type": "证人证言",
                "description": "了解案件事实的第三人陈述",
                "examples": ["同事证言", "朋友证言", "目击者陈述"],
                "proof_purpose": "还原事实经过",
                "strength": "中低",
                "obtaining_tips": ["寻找知情者", "记录证人联系方式", "申请证人出庭"]
            },
            {
                "type": "鉴定意见",
                "description": "专业机构出具的鉴定报告",
                "examples": ["笔迹鉴定", "损失评估", "质量检测"],
                "proof_purpose": "证明专门性问题",
                "strength": "高",
                "obtaining_tips": ["委托有资质鉴定机构", "申请法院委托鉴定"]
            }
        ]
    }


@router.get("/gap-solutions/{gap_type}")
async def get_gap_solutions(gap_type: str):
    """
    获取特定证据缺口的解决方案
    
    用户知道缺什么证据，系统告诉怎么补
    """
    navigator = get_navigator()
    tips = navigator._get_obtaining_tips(gap_type)
    
    return {
        "gap_type": gap_type,
        "proof_purpose": navigator._get_proof_purpose(gap_type),
        "solutions": tips["how"],
        "alternatives": tips["alternatives"],
        "feasibility": tips["feasibility"],
        "urgency": "高" if gap_type in ["书面证据", "转账凭证", "侵权证据"] else "中"
    }


# ============ 辅助函数 ============

def _get_readiness_level(score: float) -> str:
    """根据评分获取准备度等级"""
    if score >= 80:
        return "充分准备"
    elif score >= 60:
        return "基本就绪"
    elif score >= 40:
        return "准备不足"
    else:
        return "严重缺失"


def _format_gap(gap) -> dict:
    """格式化缺口信息"""
    return {
        "id": gap.gap_id,
        "type": gap.missing_type,
        "proves": gap.proves_fact,
        "severity": gap.severity.value,
        "importance": gap.importance,
        "risk": gap.risk_description,
        "how_to_get": gap.how_to_obtain,
        "alternatives": gap.alternative_evidence,
        "feasibility": gap.feasibility,
        "questions": gap.discovery_questions
    }
