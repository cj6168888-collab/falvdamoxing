"""
统一导出 API
提供所有生成物的导出功能：PDF、Word、图片、Markdown等
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
import json
import os

from app.db.database import get_db
from app.models.case import Case
from app.models.letter import Letter
from app.models.document import Document
from app.services.export_service import export_service, ExportService
from app.api.evidence import normalize_evidence_type

router = APIRouter(prefix="/api/exports", tags=["导出功能"])


@router.get("/formats")
def get_export_formats():
    """获取支持的导出格式列表"""
    return {
        "formats": [
            {"name": "PDF", "extension": "pdf", "description": "便携文档格式，适合正式文档"},
            {"name": "Word", "extension": "docx", "description": "微软Word文档，适合编辑"},
            {"name": "Markdown", "extension": "md", "description": "纯文本格式，适合分享"},
            {"name": "HTML", "extension": "html", "description": "网页格式，适合在线查看"},
            {"name": "TXT", "extension": "txt", "description": "纯文本格式"}
        ]
    }


# ============ 请求模型 ============

class ExportRequest(BaseModel):
    """导出请求"""
    content: str  # 要导出的内容
    title: str  # 文档标题
    format: str = "pdf"  # 导出格式: pdf/docx/markdown/txt/html
    document_type: str = ""  # 文档类型
    metadata: Optional[dict] = None  # 额外元数据


class ReportExportRequest(BaseModel):
    """报告导出请求"""
    report_type: str = "analysis"  # analysis/strategy/full_analysis/evidence/milestone/summary
    format: str = "pdf"


class LetterExportRequest(BaseModel):
    """函件导出请求"""
    letter_id: int
    format: str = "pdf"
    include_reply_draft: bool = True


class MeetingMinutesExportRequest(BaseModel):
    """会议纪要导出请求"""
    meeting_type: str = "股东会"
    topic: str = ""
    content: str = ""
    format: str = "pdf"


class DocumentExportRequest(BaseModel):
    """文书导出请求"""
    document_type: str  # 起诉状/答辩状/代理词/上诉状等
    format: str = "docx"
    custom_content: Optional[str] = None  # 自定义内容


def _format_proves_facts(proves_facts) -> str:
    """Format structured proof facts for export tables."""
    if not proves_facts:
        return ""
    if isinstance(proves_facts, str):
        return proves_facts
    if isinstance(proves_facts, list):
        parts = []
        for item in proves_facts:
            if isinstance(item, dict):
                parts.append(item.get("fact") or json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "；".join(part for part in parts if part)
    return json.dumps(proves_facts, ensure_ascii=False)


def _latest_fixed_review(item: Any) -> dict:
    getter = getattr(item, "get_latest_fixed_review", None)
    if callable(getter):
        return getter() or {}
    if isinstance(item, dict):
        return item.get("evidence_review") or item.get("review") or {}
    return {}


def _format_risks(review: dict) -> str:
    authenticity = review.get("authenticity_risk") or "待人工核验"
    legality = review.get("legality_risk") or "待人工核验"
    relevance = review.get("relevance_risk") or "待人工核验"
    return f"真实性：{authenticity}；合法性：{legality}；关联性：{relevance}"


def _format_actions(actions: Any) -> str:
    if isinstance(actions, str):
        return actions
    if isinstance(actions, list):
        return "；".join(str(action).strip() for action in actions if str(action).strip())
    return ""


# ============ 通用导出 API ============

@router.post("/content")
def export_any_content(request: ExportRequest, db: Session = Depends(get_db)):
    """
    通用内容导出接口
    支持导出任何文本内容为 PDF、Word、图片等格式

    请求示例:
    {
        "content": "# 案件分析报告\\n\\n这是报告内容...",
        "title": "案件分析报告",
        "format": "pdf",
        "document_type": "分析报告",
        "metadata": {"case_id": 1}
    }
    """
    # 构建元数据
    metadata = request.metadata or {}
    metadata["title"] = request.title
    metadata["document_type"] = request.document_type

    # 调用导出服务
    try:
        result = export_service.export_content(
            content=request.content,
            title=request.title,
            output_format=request.format,
            metadata=metadata
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/download/{filename}")
def download_file(filename: str):
    """
    下载导出的文件
    """
    # 安全检查：只允许下载导出目录下的文件
    filepath = export_service.get_download_path(filename)

    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 确定文件类型
    ext = os.path.splitext(filename)[1].lower()
    media_type = ExportService.MIME_TYPES.get(ext[1:], "application/octet-stream")

    return FileResponse(
        filepath,
        media_type=media_type,
        filename=filename
    )


@router.get("/list")
def list_exported_files(
    case_id: Optional[int] = Query(None, description="案件ID（可选）"),
    format: Optional[str] = Query(None, description="文件格式筛选")
):
    """
    列出已导出的文件
    """
    exports = export_service.list_exports(case_id)

    # 按格式筛选
    if format:
        exports = [e for e in exports if e['format'] == format]

    return {
        "total": len(exports),
        "files": exports
    }


# ============ 报告导出 API ============

@router.post("/report/{case_id}")
def export_case_report(
    case_id: int,
    request: ReportExportRequest,
    db: Session = Depends(get_db)
):
    """
    导出案件报告为指定格式

    支持的报告类型:
    - analysis: 案件分析报告
    - strategy: 策略建议报告
    - full_analysis: 完整对抗性分析报告
    - evidence: 证据分析报告
    - milestone: 里程碑报告
    - summary: 案件总结报告

    导出格式: pdf/docx/markdown/txt/html
    """
    # 获取案件信息
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 获取报告内容
    from app.services.streaming_report import get_streaming_report_generator, ReportType
    from app.services.llm_service import llm_service

    generator = get_streaming_report_generator(llm_service)

    type_map = {
        "analysis": ReportType.ANALYSIS,
        "strategy": ReportType.STRATEGY,
        "full_analysis": ReportType.FULL_ANALYSIS,
        "evidence": ReportType.EVIDENCE_REPORT,
        "milestone": ReportType.MILESTONE_REPORT,
        "summary": ReportType.SUMMARY_REPORT
    }
    report_type = type_map.get(request.report_type, ReportType.ANALYSIS)

    # 构建案件信息
    case_info = {
        "id": case.id,
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "status": case.status.value if hasattr(case.status, 'value') else str(case.status),
        "cause": case.cause or "",
        "plaintiff": case.plaintiff or "",
        "defendant": case.defendant or "",
        "claim_amount": case.claim_amount or "",
        "description": case.description or "",
        "supplement": case.supplement or "",
        "legal_analysis": case.legal_analysis or "",
        "strategy_suggestion": case.strategy_suggestion or ""
    }

    # 生成报告
    content = generator.generate_report(
        case_id=case_id,
        report_type=report_type,
        case_info=case_info,
        force_regenerate=True
    )

    # 生成标题
    report_type_names = {
        "analysis": "案件分析报告",
        "strategy": "策略建议报告",
        "full_analysis": "完整对抗性分析报告",
        "evidence": "证据分析报告",
        "milestone": "里程碑报告",
        "summary": "案件总结报告"
    }
    title = f"{case.title} - {report_type_names.get(request.report_type, '分析报告')}"

    # 导出
    result = export_service.export_content(
        content=content,
        title=title,
        output_format=request.format,
        metadata={
            "case_id": case_id,
            "report_type": request.report_type,
            "document_type": report_type_names.get(request.report_type, "分析报告")
        }
    )

    return result


# ============ 文书导出 API ============

@router.post("/document/{case_id}")
def export_case_document(
    case_id: int,
    request: DocumentExportRequest,
    db: Session = Depends(get_db)
):
    """
    导出法律文书为指定格式

    支持的文书类型:
    - 起诉状
    - 答辩状
    - 代理词
    - 上诉状
    - 反诉状
    - 申请书
    - 证据目录
    - 强制执行申请书
    - 财产保全申请书
    """
    # 获取案件信息
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 获取文书内容
    from app.services.doc_service import document_generator

    case_data = {
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "case_number": case.case_number,
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "third_party": case.third_party,
        "cause": case.cause,
        "claim_amount": case.claim_amount,
        "description": case.description,
        "supplement": case.supplement,
        "legal_analysis": case.legal_analysis
    }

    # 如果有自定义内容，使用自定义内容
    if request.custom_content:
        content = request.custom_content
    else:
        # 生成文书
        content = document_generator.generate(
            document_type=request.document_type,
            case_data=case_data
        )

    # 生成标题
    title = f"{case.title} - {request.document_type}"

    # 导出
    result = export_service.export_content(
        content=content,
        title=title,
        output_format=request.format,
        metadata={
            "case_id": case_id,
            "document_type": request.document_type
        }
    )

    return result


# ============ 函件导出 API ============

@router.post("/letter/{letter_id}")
def export_letter(
    letter_id: int,
    request: LetterExportRequest,
    db: Session = Depends(get_db)
):
    """
    导出函件为指定格式

    支持导出:
    - 原函件内容
    - AI回复草稿
    """
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="函件不存在")

    case = db.query(Case).filter(Case.id == letter.case_id).first()

    # 构建函件内容
    content = f"""# {letter.title}

## 函件信息

| 项目 | 内容 |
|------|------|
| 函件类型 | {letter.letter_type.value if hasattr(letter.letter_type, 'value') else letter.letter_type} |
| 方向 | {'收函' if letter.direction.value == 'incoming' else '发函'} |
| 发送方 | {letter.sender or '未填写'} |
| 接收方 | {letter.recipient or '未填写'} |
| 函件日期 | {letter.letter_date.strftime('%Y-%m-%d') if letter.letter_date else '未填写'} |
| 收到日期 | {letter.received_date.strftime('%Y-%m-%d') if letter.received_date else '未填写'} |
| 紧急程度 | {letter.urgent_level.value if hasattr(letter.urgent_level, 'value') else letter.urgent_level} |

"""

    if letter.content_summary:
        content += f"""## 内容摘要

{letter.content_summary}

"""

    if letter.key_demands:
        content += f"""## 核心诉求

{letter.key_demands}

"""

    if letter.legal_basis:
        content += f"""## 法律依据

{letter.legal_basis}

"""

    # 添加回复草稿
    if request.include_reply_draft and letter.draft_reply:
        content += f"""## 回复草稿

{letter.draft_reply}

"""

    # 生成标题
    direction_text = "收函" if letter.direction.value == 'incoming' else "发函"
    title = f"{case.title} - {direction_text}: {letter.title}" if case else letter.title

    # 导出
    result = export_service.export_content(
        content=content,
        title=title,
        output_format=request.format,
        metadata={
            "case_id": letter.case_id,
            "letter_id": letter_id,
            "document_type": "函件"
        }
    )

    return result


# ============ 会议纪要导出 API ============

@router.post("/meeting-minutes")
def export_meeting_minutes(request: MeetingMinutesExportRequest):
    """
    导出会议纪要为指定格式
    """
    # 构建会议纪要内容
    content = f"""# 会议纪要

## 基本信息

| 项目 | 内容 |
|------|------|
| 会议类型 | {request.meeting_type} |
| 会议主题 | {request.topic} |
| 生成时间 | {datetime.now().strftime('%Y-%m-%d %H:%M')} |

"""

    if request.content:
        content += f"""## 纪要内容

{request.content}

"""

    # 导出
    result = export_service.export_content(
        content=content,
        title=f"{request.meeting_type} - {request.topic}",
        output_format=request.format,
        metadata={
            "document_type": "会议纪要",
            "meeting_type": request.meeting_type
        }
    )

    return result


# ============ 批量导出 API ============

@router.post("/batch/{case_id}")
def batch_export_case(
    case_id: int,
    formats: List[str] = Query(["pdf", "docx"], description="导出格式列表"),
    include_types: Optional[str] = Query(None, description="包含的内容类型，逗号分隔: report,document,letter,meeting"),
    db: Session = Depends(get_db)
):
    """
    批量导出案件相关内容

    可以一次导出多种格式的多种文件:
    - report: 案件报告
    - document: 法律文书
    - letter: 函件
    - meeting: 会议纪要
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    results = []
    include_list = include_types.split(',') if include_types else ['report']

    # 导出报告
    if 'report' in include_list:
        for fmt in formats:
            try:
                result = export_case_report(
                    case_id=case_id,
                    request=ReportExportRequest(
                        report_type="analysis",
                        format=fmt
                    ),
                    db=db
                )
                results.append({
                    "type": "report",
                    "format": fmt,
                    **result
                })
            except Exception as e:
                results.append({
                    "type": "report",
                    "format": fmt,
                    "success": False,
                    "error": str(e)
                })

    # 导出文书
    if 'document' in include_list:
        for doc_type in ['起诉状', '答辩状', '代理词']:
            for fmt in formats:
                try:
                    result = export_case_document(
                        case_id=case_id,
                        request=DocumentExportRequest(
                            document_type=doc_type,
                            format=fmt
                        ),
                        db=db
                    )
                    results.append({
                        "type": f"document_{doc_type}",
                        "format": fmt,
                        **result
                    })
                except Exception as e:
                    results.append({
                        "type": f"document_{doc_type}",
                        "format": fmt,
                        "success": False,
                        "error": str(e)
                    })

    # 导出函件
    if 'letter' in include_list:
        letters = db.query(Letter).filter(Letter.case_id == case_id).limit(5).all()
        for letter in letters:
            for fmt in formats[:1]:  # 限制函件导出格式
                try:
                    result = export_letter(
                        letter_id=letter.id,
                        request=LetterExportRequest(
                            letter_id=letter.id,
                            format=fmt,
                            include_reply_draft=False
                        ),
                        db=db
                    )
                    results.append({
                        "type": "letter",
                        "letter_id": letter.id,
                        "letter_title": letter.title,
                        "format": fmt,
                        **result
                    })
                except Exception as e:
                    results.append({
                        "type": "letter",
                        "letter_id": letter.id,
                        "format": fmt,
                        "success": False,
                        "error": str(e)
                    })

    success_count = sum(1 for r in results if r.get('success', False))

    return {
        "case_id": case_id,
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "results": results
    }


# ============ 证据导出 API ============

@router.post("/evidence/{case_id}")
def export_evidence_list(
    case_id: int,
    body: dict = Body(default={})
):
    """
    导出证据清单为指定格式
    """
    format = body.get("format", "pdf")
    include_content = body.get("include_content", False)
    
    db = next(get_db())
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="案件不存在")

        # 尝试从 EvidenceItem v2 获取证据
        evidence_items = []
        try:
            from app.models.evidence import EvidenceItem
            evidence_items = db.query(EvidenceItem).filter(
                EvidenceItem.case_id == case_id
            ).all()
        except Exception:
            pass  # 表可能为空或不存在

        # 如果 v2 表为空，尝试从 Document 表获取证据类型的文档
        if not evidence_items:
            evidence_docs = db.query(Document).filter(
                Document.case_id == case_id,
                or_(
                    Document.doc_type.like('证据%'),
                    Document.doc_type.like('%合同%'),
                    Document.doc_type.like('%函件%'),
                    Document.doc_type.like('%协议%'),
                    Document.doc_type.like('%章程%')
                )
            ).all()
            
            # 构建兼容的数据结构
            for i, doc in enumerate(evidence_docs, 1):
                evidence_items.append({
                    'index': i,
                    'id': str(doc.id),
                    'original_filename': doc.filename,
                    'evidence_type': normalize_evidence_type(doc.doc_type) if doc.doc_type else '其他',
                    'source_party': '己方',
                    'summary': doc.content_summary.replace('[证据]', '') if doc.content_summary else '',
                    'proof_purpose': doc.content_summary.replace('[证据]', '') if doc.content_summary else '',
                    'original_status': '待人工核验',
                    'three_natures_risk': _format_risks({}),
                    'strengthening_actions': '',
                    'extracted_content': doc.content if include_content else ''
                })
        else:
            # 转换为兼容格式
            evidence_list = []
            for i, ev in enumerate(evidence_items, 1):
                ev_type = ev.evidence_type if hasattr(ev.evidence_type, 'value') else str(ev.evidence_type)
                review = _latest_fixed_review(ev)
                proof_purpose = review.get("proof_purpose") or _format_proves_facts(ev.proves_facts) or ev.summary or ''
                evidence_list.append({
                    'index': i,
                    'id': ev.id,
                    'original_filename': ev.original_filename,
                    'evidence_type': ev_type,
                    'source_party': ev.source_party or '未填写',
                    'summary': proof_purpose,
                    'proof_purpose': proof_purpose,
                    'original_status': review.get("original_status") or "待人工核验",
                    'three_natures_risk': _format_risks(review),
                    'strengthening_actions': _format_actions(review.get("strengthening_actions") or []),
                    'extracted_content': ev.extracted_content if include_content else ''
                })
            evidence_items = evidence_list

        # 构建证据清单内容
        content = f"""# 证据清单

## 案件信息

| 项目 | 内容 |
|------|------|
| 案件名称 | {case.title} |
| 案件编号 | {case.case_number or '暂无'} |
| 证据数量 | {len(evidence_items)} |
| 生成时间 | {datetime.now().strftime('%Y-%m-%d %H:%M')} |

## 证据目录

| 序号 | 证据名称 | 类型 | 来源 | 证明事项 | 原件状态 | 三性风险 | 补强动作 |
|------|---------|------|------|---------|---------|---------|---------|
"""

        for ev in evidence_items:
            if isinstance(ev, dict):
                ev_name = ev.get('original_filename', ev.get('id', f'证据{ev.get("index", "?")}'))
                ev_type = ev.get('evidence_type', '其他')
                source = ev.get('source_party', '未填写')
                summary = ev.get('summary', '未填写')
                original_status = ev.get('original_status', '待人工核验')
                three_natures_risk = ev.get('three_natures_risk', _format_risks({}))
                strengthening_actions = ev.get('strengthening_actions', '')
            else:
                ev_name = ev.original_filename or str(ev.id)
                ev_type = ev.evidence_type if hasattr(ev.evidence_type, 'value') else str(ev.evidence_type)
                source = ev.source_party or '未填写'
                summary = ev.summary or ''
                review = _latest_fixed_review(ev)
                original_status = review.get("original_status") or "待人工核验"
                three_natures_risk = _format_risks(review)
                strengthening_actions = _format_actions(review.get("strengthening_actions") or [])
            
            if len(summary) > 50:
                summary = summary[:50] + '...'
            if len(three_natures_risk) > 90:
                three_natures_risk = three_natures_risk[:90] + '...'
            if len(strengthening_actions) > 70:
                strengthening_actions = strengthening_actions[:70] + '...'
            content += f"| {ev.get('index', 0) if isinstance(ev, dict) else 0} | {ev_name} | {ev_type} | {source} | {summary} | {original_status} | {three_natures_risk} | {strengthening_actions} |\n"

        # 导出
        result = export_service.export_content(
            content=content,
            title=f"{case.title} - 证据清单",
            output_format=format,
            metadata={
                "case_id": case_id,
                "document_type": "证据清单",
                "evidence_count": len(evidence_items)
            }
        )

        return result
    finally:
        db.close()


# ============ 对抗性分析导出 API ============

@router.post("/adversarial-analysis/{analysis_id}")
def export_adversarial_analysis(
    analysis_id: int,
    format: str = Query("pdf", description="导出格式"),
    db: Session = Depends(get_db)
):
    """
    导出对抗性分析报告
    """
    from app.models.adversarial_analysis import AdversarialAnalysis

    analysis = db.query(AdversarialAnalysis).filter(
        AdversarialAnalysis.id == analysis_id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="分析不存在")

    case = db.query(Case).filter(Case.id == analysis.case_id).first()

    # 构建分析内容
    content = f"""# 对抗性分析报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 分析标题 | {analysis.title} |
| 分析阶段 | {analysis.analysis_phase.value if hasattr(analysis.analysis_phase, 'value') else analysis.analysis_phase} |
| 对方当事人 | {analysis.opponent_name or '待确定'} |
| 生成时间 | {analysis.created_at.strftime('%Y-%m-%d %H:%M') if analysis.created_at else '未知'} |

"""

    if analysis.our_strengths:
        content += f"""## 我方优势

{analysis.our_strengths}

"""

    if analysis.our_weaknesses:
        content += f"""## 我方弱点

{analysis.our_weaknesses}

"""

    if analysis.opponent_strengths:
        content += f"""## 对方优势

{analysis.opponent_strengths}

"""

    if analysis.opponent_weaknesses:
        content += f"""## 对方弱点

{analysis.opponent_weaknesses}

"""

    if analysis.overall_strategy:
        content += f"""## 总体策略

{analysis.overall_strategy}

"""

    if analysis.immediate_actions:
        content += f"""## 立即行动

{analysis.immediate_actions}

"""

    # 导出
    title = f"{case.title} - {analysis.title}" if case else analysis.title
    result = export_service.export_content(
        content=content,
        title=title,
        output_format=format,
        metadata={
            "case_id": analysis.case_id,
            "analysis_id": analysis_id,
            "document_type": "对抗性分析报告"
        }
    )

    return result
