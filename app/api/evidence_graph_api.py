"""
证据图谱 API V2
提供证据可视化、关系分析、缺口检测等功能
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid

# 获取当前日期
CURRENT_DATE = datetime.now().strftime('%Y年%m月%d日')
CURRENT_YEAR = datetime.now().year

from app.db.database import get_db
from app.models.case import Case
from app.models.evidence import EvidenceItem, EvidenceAnalysisRecord
from app.services.evidence_v2 import EvidenceServiceV2, evidence_service_v2
from app.services.llm_service import llm_service
from app.utils.file_parser import file_parser

router = APIRouter(prefix="/api/v2/evidence-graph", tags=["证据图谱V2"])


# ============ 请求模型 ============

class ProcessEvidenceRequest(BaseModel):
    """处理证据请求"""
    case_id: int
    source_type: str = "text"  # file/text/input
    content: Optional[str] = None
    file_path: Optional[str] = None
    original_filename: Optional[str] = None
    source_party: str = "己方"  # 己方/对方/第三方/法院


class UpdateEvidenceRequest(BaseModel):
    """更新证据请求"""
    evidence_id: str
    summary: Optional[str] = None
    evidence_type: Optional[str] = None
    source_party: Optional[str] = None
    proves_facts: Optional[List[dict]] = None
    keywords: Optional[List[str]] = None


class EvidenceCorrectionRequest(BaseModel):
    """证据人工纠偏请求"""
    evidence_id: str
    # 基本信息纠偏
    correct_name: Optional[str] = None  # 正确名称
    correct_type: Optional[str] = None  # 正确类型
    correct_summary: Optional[str] = None  # 正确摘要
    # 证明方向纠偏
    proof_direction: Optional[str] = None  # 证明方向（我方/对方）
    proves_facts_corrected: Optional[List[str]] = None  # 证明的事实（人工纠正）
    # 关联性纠偏
    relevance_score: Optional[float] = None  # 关联性评分 0-100
    related_facts: Optional[List[str]] = None  # 关联事实
    related_evidence_ids: Optional[List[str]] = None  # 关联证据ID
    contradicted_evidence_ids: Optional[List[str]] = None  # 矛盾证据ID
    # 证明力参考纠偏（兼容内部 credibility 字段）
    credibility_corrected: Optional[float] = None  # 证明力参考 0-100
    authenticity_corrected: Optional[float] = None  # 真实性评分 0-100
    reliability_corrected: Optional[float] = None  # 可靠性评分 0-100
    # 分析备注
    manual_notes: Optional[str] = None  # 人工备注
    is_verified: Optional[bool] = None  # 是否已人工核实
    status: Optional[str] = None  # pending/verified/rejected


class AnalyzeRelationshipsRequest(BaseModel):
    """分析关系请求"""
    case_id: int
    force_refresh: bool = False


class SingleEvidenceAnalysisRequest(BaseModel):
    """单条证据深度分析请求"""
    evidence_id: str
    analysis_type: str = "comprehensive"  # credibility/proof/relationship/comprehensive
    force_refresh: bool = False  # 是否强制重新分析


# ============ API 接口 ============

@router.post("/evidence/process")
async def process_evidence(request: ProcessEvidenceRequest, db: Session = Depends(get_db)):
    """
    处理证据
    自动完成：去重检查 → 内容提取 → 分类 → 证明力参考 → 关键词提取
    """
    # 验证案件
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 处理证据
    result = evidence_service_v2.process_evidence(
        case_id=request.case_id,
        source_type=request.source_type,
        content=request.content,
        file_path=request.file_path,
        original_filename=request.original_filename,
        source_party=request.source_party
    )

    return result


@router.get("/evidence/list")
async def get_evidence_list(
    case_id: int,
    evidence_type: Optional[str] = None,
    source_party: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取证据列表
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    filters = {}
    if evidence_type:
        filters['evidence_type'] = evidence_type
    if source_party:
        filters['source_party'] = source_party
    if status:
        filters['status'] = status

    evidence_list = evidence_service_v2.get_evidence_list(case_id, filters)

    return {
        'case_id': case_id,
        'total': len(evidence_list),
        'evidence_list': evidence_list
    }


@router.get("/evidence/{evidence_id}")
async def get_evidence_detail(evidence_id: str, db: Session = Depends(get_db)):
    """
    获取证据详情
    """
    evidence = evidence_service_v2.get_evidence_by_id(evidence_id)

    if not evidence:
        raise HTTPException(status_code=404, detail="证据不存在")

    return evidence


@router.put("/evidence/update")
async def update_evidence(request: UpdateEvidenceRequest, db: Session = Depends(get_db)):
    """
    更新证据信息
    """
    updates = {}
    if request.summary is not None:
        updates['summary'] = request.summary
    if request.evidence_type is not None:
        updates['evidence_type'] = request.evidence_type
    if request.source_party is not None:
        updates['source_party'] = request.source_party
    if request.proves_facts is not None:
        updates['proves_facts'] = request.proves_facts
    if request.keywords is not None:
        updates['keywords'] = request.keywords

    result = evidence_service_v2.update_evidence(request.evidence_id, updates)
    return result


@router.post("/evidence/correct")
async def correct_evidence(request: EvidenceCorrectionRequest, db: Session = Depends(get_db)):
    """
    证据人工纠偏
    允许用户对证据进行全面的人工纠正，包括：
    - 基本信息（名称、类型、摘要）
    - 证明方向（证明什么事实）
    - 关联性（关联证据、矛盾证据）
    - 证明力参考
    - 人工备注
    """
    updates = {}

    # 基本信息
    if request.correct_name is not None:
        updates['summary'] = request.correct_name  # 使用summary字段存储正确名称
    if request.correct_type is not None:
        updates['evidence_type'] = request.correct_type
    if request.correct_summary is not None:
        updates['summary'] = request.correct_summary

    # 证明方向
    if request.proof_direction is not None:
        updates['source_party'] = request.proof_direction
    if request.proves_facts_corrected is not None:
        # 转换为JSON字符串存储
        updates['proves_facts'] = request.proves_facts_corrected

    # 关联性
    if request.relevance_score is not None:
        updates['reliability_score'] = request.relevance_score / 100.0
    if request.related_facts is not None:
        updates['fact_tags'] = request.related_facts
    if request.related_evidence_ids is not None:
        updates['related_evidence_ids'] = request.related_evidence_ids
    if request.contradicted_evidence_ids is not None:
        updates['contradicted_evidence_ids'] = request.contradicted_evidence_ids

    # 证明力参考
    if request.credibility_corrected is not None:
        updates['credibility_score'] = request.credibility_corrected / 100.0
    if request.authenticity_corrected is not None:
        updates['authenticity_score'] = request.authenticity_corrected / 100.0
    if request.reliability_corrected is not None:
        updates['reliability_score'] = request.reliability_corrected / 100.0

    # 分析备注
    if request.manual_notes is not None:
        updates['processing_notes'] = request.manual_notes
    if request.is_verified is not None:
        updates['status'] = 'verified' if request.is_verified else 'pending'
    if request.status is not None:
        updates['status'] = request.status

    # 更新时间
    updates['updated_at'] = datetime.now()

    result = evidence_service_v2.update_evidence(request.evidence_id, updates)

    return {
        "success": True,
        "message": "证据纠偏已保存",
        "evidence_id": request.evidence_id,
        "updates": list(updates.keys())
    }


@router.get("/evidence/{evidence_id}/correction-form")
async def get_correction_form(evidence_id: str, db: Session = Depends(get_db)):
    """
    获取证据纠偏表单数据
    返回证据当前状态和建议，用于人工纠偏
    """
    evidence = evidence_service_v2.get_evidence_by_id(evidence_id)

    if not evidence:
        raise HTTPException(status_code=404, detail="证据不存在")

    # 获取关联证据列表（用于选择关联/矛盾证据）
    if evidence.get('case_id'):
        all_evidence = evidence_service_v2.get_evidence_list(evidence['case_id'], {})
        related_options = [
            {"id": e['id'], "name": e.get('original_filename', e.get('id', '')), "type": e.get('evidence_type', '')}
            for e in all_evidence if e['id'] != evidence_id
        ]
    else:
        related_options = []

    # 类型选项
    type_options = [
        {"value": "CONTRACT", "label": "合同", "icon": "📜"},
        {"value": "CORRESPONDENCE", "label": "函件", "icon": "📧"},
        {"value": "PAYMENT", "label": "支付凭证", "icon": "💰"},
        {"value": "IDENTITY", "label": "身份证明", "icon": "🪪"},
        {"value": "AUDIO_VIDEO", "label": "视听资料", "icon": "🎬"},
        {"value": "DOCUMENT", "label": "书证", "icon": "📄"},
        {"value": "OTHER", "label": "其他", "icon": "📎"}
    ]

    # 来源方选项
    party_options = [
        {"value": "OUR_SIDE", "label": "我方", "color": "green"},
        {"value": "OPPONENT", "label": "对方", "color": "red"},
        {"value": "THIRD_PARTY", "label": "第三方", "color": "gray"},
        {"value": "COURT", "label": "法院", "color": "blue"}
    ]

    return {
        "evidence": evidence,
        "type_options": type_options,
        "party_options": party_options,
        "related_options": related_options,
        "current_values": {
            "name": evidence.get('original_filename', ''),
            "type": evidence.get('evidence_type', ''),
            "summary": evidence.get('summary', ''),
            "party": evidence.get('source_party', ''),
            "proves_facts": evidence.get('proves_facts', []),
            "keywords": evidence.get('keywords', []),
            "credibility_score": round(evidence.get('credibility_score', 0) * 100) if evidence.get('credibility_score') else 0,
            "authenticity_score": round(evidence.get('authenticity_score', 0) * 100) if evidence.get('authenticity_score') else 0,
            "reliability_score": round(evidence.get('reliability_score', 0) * 100) if evidence.get('reliability_score') else 0,
            "related_ids": evidence.get('related_evidence_ids', []),
            "contradicted_ids": evidence.get('contradicted_evidence_ids', []),
            "notes": evidence.get('processing_notes', ''),
            "status": evidence.get('status', 'pending')
        }
    }


@router.delete("/evidence/{evidence_id}")
async def delete_evidence(evidence_id: str, db: Session = Depends(get_db)):
    """
    删除证据（软删除）
    """
    result = evidence_service_v2.delete_evidence(evidence_id)
    return result


@router.post("/relationships/analyze")
async def analyze_evidence_relationships(request: AnalyzeRelationshipsRequest, db: Session = Depends(get_db)):
    """
    分析证据之间的关系
    """
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    result = evidence_service_v2.analyze_relationships(request.case_id)
    return result


@router.get("/graph/data")
async def get_graph_data(
    case_id: int,
    view_type: str = "default",
    db: Session = Depends(get_db)
):
    """
    获取图谱可视化数据
    支持多种视图：default, fact, relationship, timeline
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    graph_data = evidence_service_v2.get_graph_data(case_id, view_type)
    return graph_data


@router.get("/summary")
async def get_evidence_summary(case_id: int, db: Session = Depends(get_db)):
    """
    获取证据汇总信息
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    summary = evidence_service_v2.get_evidence_summary(case_id)
    return {
        'case_id': case_id,
        'summary': summary
    }


@router.get("/statistics")
async def get_evidence_statistics(case_id: int, db: Session = Depends(get_db)):
    """
    获取证据统计
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    stats = evidence_service_v2.get_statistics(case_id)
    return {
        'case_id': case_id,
        'statistics': stats
    }


@router.get("/types")
async def get_evidence_type_info():
    """
    获取证据类型信息
    """
    return {
        'types': EvidenceServiceV2.EVIDENCE_TYPES
    }


@router.get("/relationship-types")
async def get_relationship_type_info():
    """
    获取关系类型信息
    """
    return {
        'types': EvidenceServiceV2.RELATIONSHIP_TYPES
    }


# ============ 单条证据深度分析 ============

@router.post("/evidence/analyze")
async def analyze_single_evidence(
    request: SingleEvidenceAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    对单条证据进行深度分析

    分析内容：
    1. 证明力参考 - 形式真实性、来源可靠性、内容一致性、印证程度
    2. 证明事实 - 这份证据能证明什么
    3. 潜在质疑 - 对方可能如何质疑
    4. 应对建议 - 如何应对质疑
    5. 补强建议 - 需要什么补充证据
    6. 使用时机 - 什么时机出示最好

    分析结果会保存到数据库，支持追溯
    """
    # 获取证据
    evidence = db.query(EvidenceItem).filter(
        EvidenceItem.id == request.evidence_id
    ).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="证据不存在")

    # 检查是否已有分析结果（且不需要强制刷新）
    if not request.force_refresh:
        existing_record = db.query(EvidenceAnalysisRecord).filter(
            EvidenceAnalysisRecord.evidence_id == request.evidence_id,
            EvidenceAnalysisRecord.analysis_type == request.analysis_type
        ).order_by(EvidenceAnalysisRecord.created_at.desc()).first()

        if existing_record:
            return {
                'status': 'cached',
                'record': existing_record.to_dict(),
                'message': '使用已有的分析结果，如需重新分析请设置 force_refresh=true'
            }

    # 获取案件信息用于分析
    case = db.query(Case).filter(Case.id == evidence.case_id).first()

    # 提取文件内容（如果是图片/PDF）
    content_to_analyze = evidence.extracted_content or evidence.raw_content or ""

    if not content_to_analyze and evidence.file_path:
        try:
            content_to_analyze = file_parser.parse(evidence.file_path)
        except Exception:
            pass

    # 调用 LLM 进行深度分析
    if llm_service and llm_service.is_configured():
        analysis_result = await _perform_ai_analysis(
            evidence=evidence,
            case=case,
            content=content_to_analyze,
            analysis_type=request.analysis_type
        )
    else:
        # 使用简单的基于规则的分析
        analysis_result = _perform_rule_based_analysis(evidence, content_to_analyze)

    # 保存分析结果
    record = EvidenceAnalysisRecord(
        id=str(uuid.uuid4()),
        case_id=evidence.case_id,
        evidence_id=str(evidence.id),
        analysis_type=request.analysis_type,
        analysis_result=analysis_result.get('full_result', {}),
        summary=analysis_result.get('summary', ''),
        credibility_score=analysis_result.get('credibility_score', 0.0),
        authenticity_score=analysis_result.get('authenticity_score', 0.0),
        reliability_score=analysis_result.get('reliability_score', 0.0),
        consistency_score=analysis_result.get('consistency_score', 0.0),
        proves_facts=analysis_result.get('proves_facts', []),
        proves_strength=analysis_result.get('proves_strength', []),
        potential_challenges=analysis_result.get('potential_challenges', []),
        challenge_responses=analysis_result.get('challenge_responses', []),
        reinforcement_suggestions=analysis_result.get('reinforcement_suggestions', []),
        alternative_evidence=analysis_result.get('alternative_evidence', []),
        usage_timing=analysis_result.get('usage_timing', ''),
        presentation_tips=analysis_result.get('presentation_tips', ''),
        risk_points=analysis_result.get('risk_points', []),
        risk_level=analysis_result.get('risk_level', 'medium'),
        ai_model='qwen-plus' if llm_service and llm_service.is_configured() else 'rule-based',
        confidence=analysis_result.get('confidence', 0.5)
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    # 同时更新证据的基本分析字段
    evidence.credibility_score = analysis_result.get('credibility_score', 0.0)
    evidence.authenticity_score = analysis_result.get('authenticity_score', 0.0)
    evidence.reliability_score = analysis_result.get('reliability_score', 0.0)
    evidence.consistency_score = analysis_result.get('consistency_score', 0.0)
    evidence.credibility_analysis = analysis_result.get('summary', '')
    evidence.proves_facts = analysis_result.get('proves_facts', [])

    db.commit()

    return {
        'status': 'success',
        'record': record.to_dict(),
        'formatted_report': _format_analysis_report(record, evidence)
    }


async def _perform_ai_analysis(
    evidence: EvidenceItem,
    case: Case,
    content: str,
    analysis_type: str
) -> dict:
    """使用 AI 进行深度分析"""
    # 构建提示词
    prompt = f"""请对以下证据进行深度法律分析：

【证据名称】{evidence.original_filename or '未命名证据'}
【证据类型】{EvidenceItem.get_type_display(evidence.evidence_type)['name']}
【来源方】{evidence.source_party}
【证据内容】
{content if content else '(无内容)'}

【案件基本信息】（如有）
案件类型：{case.case_type.value if case and hasattr(case.case_type, 'value') else '未知'}
案由：{case.cause if case else '未知'}

请从以下维度进行专业分析：

## 1. 证明力与证据风险参考
- 形式真实性评分 (0-100)
- 来源可靠性评分 (0-100)
- 内容一致性评分 (0-100)
- 与其他证据印证程度 (0-100)
- 综合证明力参考 (0-100，仅作工作底稿参考，不等同于法院采信结论)

## 2. 证明事实
这份证据能证明哪些事实？请列出具体事实及其证明强度。

## 3. 潜在质疑方向
对方可能从哪些角度质疑这份证据？

## 4. 应对建议
如何回应对方的质疑？

## 5. 补强建议
需要什么补充证据来增强证明力？

## 6. 使用时机建议
什么时机出示这份证据效果最好？

请用 JSON 格式返回分析结果，包含以下字段：
- credibility_score: 综合证明力参考 (0-100，仅作工作底稿参考)
- authenticity_score: 真实性评分 (0-100)
- reliability_score: 可靠性评分 (0-100)
- consistency_score: 一致性评分 (0-100)
- summary: 简要摘要 (100字以内)
- proves_facts: [{{"fact": "事实描述", "strength": 0-100}}]
- potential_challenges: ["质疑点1", "质疑点2"]
- challenge_responses: ["应对建议1", "应对建议2"]
- reinforcement_suggestions: ["补强建议1", "补强建议2"]
- alternative_evidence: ["替代证据1", "替代证据2"]
- usage_timing: "使用时机建议"
- presentation_tips: "呈现技巧"
- risk_points: ["风险点1", "风险点2"]
- risk_level: "high/medium/low"
- confidence: AI输出稳定性参考 (0-1)"""

    try:
        import asyncio
        messages = [
            {"role": "system", "content": f"你是一位专业的诉讼证据审查专家，擅长分析证据的证明力、风险点和最佳使用方式。\n\n【当前日期信息】\n- 当前日期：{CURRENT_DATE}\n- 当前年份：{CURRENT_YEAR}年"},
            {"role": "user", "content": prompt}
        ]

        # 使用同步方式调用
        import nest_asyncio
        nest_asyncio.apply()

        result_text = llm_service.chat(messages, model="qwen-plus")

        # 尝试解析 JSON
        import json
        import re

        # 提取 JSON
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # 如果无法解析 JSON，生成默认结构
            result = {
                'credibility_score': 60.0,
                'authenticity_score': 60.0,
                'reliability_score': 60.0,
                'consistency_score': 60.0,
                'summary': result_text[:200] if result_text else '分析完成',
                'proves_facts': [],
                'potential_challenges': [],
                'challenge_responses': [],
                'reinforcement_suggestions': [],
                'alternative_evidence': [],
                'usage_timing': '根据庭审情况灵活把握',
                'presentation_tips': '配合其他证据使用效果更好',
                'risk_points': [],
                'risk_level': 'medium',
                'confidence': 0.6
            }

        result['full_result'] = result
        return result

    except Exception as e:
        return _perform_rule_based_analysis(evidence, content)


def _perform_rule_based_analysis(evidence: EvidenceItem, content: str) -> dict:
    """基于规则的简单分析"""
    # 根据证据类型评估
    type_scores = {
        'CONTRACT': {'credibility': 80, 'authenticity': 85, 'reliability': 80},
        'PAYMENT': {'credibility': 85, 'authenticity': 90, 'reliability': 85},
        'DOCUMENT': {'credibility': 75, 'authenticity': 75, 'reliability': 75},
        'CORRESPONDENCE': {'credibility': 65, 'authenticity': 60, 'reliability': 60},
        'AUDIO_VIDEO': {'credibility': 60, 'authenticity': 50, 'reliability': 55},
        'TESTIMONY': {'credibility': 50, 'authenticity': 40, 'reliability': 50},
        'EXPERT': {'credibility': 75, 'authenticity': 80, 'reliability': 75},
        'IDENTITY': {'credibility': 85, 'authenticity': 90, 'reliability': 85},
        'OTHER': {'credibility': 50, 'authenticity': 50, 'reliability': 50}
    }

    ev_type = evidence.evidence_type
    scores = type_scores.get(ev_type, type_scores['OTHER'])

    # 提取简单的事实
    proves_facts = []
    if content:
        # 简单关键词检测
        if any(kw in content for kw in ['合同', '协议', '约定']):
            proves_facts.append({'fact': '合同关系的存在', 'strength': 70})
        if any(kw in content for kw in ['支付', '转账', '汇款', '付款']):
            proves_facts.append({'fact': '款项支付情况', 'strength': 75})
        if any(kw in content for kw in ['日期', '时间', '年', '月', '日']):
            proves_facts.append({'fact': '时间节点', 'strength': 60})
        if any(kw in content for kw in ['金额', '元', '人民币']):
            proves_facts.append({'fact': '涉及金额', 'strength': 65})

    # 根据类型给出质疑点
    challenges_map = {
        'CONTRACT': ['合同是否完整？', '是否存在修改？', '对方是否盖章签字？'],
        'PAYMENT': ['转账凭证与案件关联性？', '是否存在其他款项往来？'],
        'CORRESPONDENCE': ['通信记录真实性？', '是否完整未删减？'],
        'AUDIO_VIDEO': ['录音录像是否经过剪辑？', '取得方式是否合法？']
    }

    potential_challenges = challenges_map.get(ev_type, ['真实性存疑', '关联性待确认'])

    return {
        'credibility_score': scores['credibility'],
        'authenticity_score': scores['authenticity'],
        'reliability_score': scores['reliability'],
        'consistency_score': 65,
        'summary': f'{EvidenceItem.get_type_display(ev_type)["name"]}，基础证明力参考',
        'proves_facts': proves_facts,
        'proves_strength': [f['strength'] for f in proves_facts],
        'potential_challenges': potential_challenges,
        'challenge_responses': ['准备好原件供核对', '准备其他证据印证'],
        'reinforcement_suggestions': ['配合其他证据使用', '必要时进行公证'],
        'alternative_evidence': ['公证书', '鉴定意见'],
        'usage_timing': '根据庭审情况灵活把握',
        'presentation_tips': '配合其他证据使用效果更好',
        'risk_points': potential_challenges,
        'risk_level': 'medium' if scores['credibility'] >= 60 else 'high',
        'confidence': 0.5,
        'full_result': {}
    }


def _format_analysis_report(record: EvidenceAnalysisRecord, evidence: EvidenceItem) -> dict:
    """格式化分析报告为易读格式"""
    type_info = EvidenceItem.get_type_display(evidence.evidence_type)

    # 风险等级显示
    risk_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(record.risk_level, '🟡')

    report = {
        'evidence_info': {
            'name': evidence.original_filename or '未命名',
            'type': type_info['name'],
            'type_icon': type_info['icon']
        },
        'credibility': {
            'label': '证明力参考',
            'notice': '仅为法律工作底稿中的证据风险参考，不等同于法院对真实性、合法性、关联性的最终认定。',
            'overall': record.credibility_score,
            'authenticity': record.authenticity_score,
            'reliability': record.reliability_score,
            'consistency': record.consistency_score
        },
        'proves_facts': record.proves_facts or [],
        'challenges': {
            'potential': record.potential_challenges or [],
            'responses': record.challenge_responses or []
        },
        'suggestions': {
            'reinforcement': record.reinforcement_suggestions or [],
            'alternative': record.alternative_evidence or []
        },
        'usage': {
            'timing': record.usage_timing or '根据庭审情况决定',
            'tips': record.presentation_tips or ''
        },
        'risks': {
            'level': record.risk_level,
            'emoji': risk_emoji,
            'points': record.risk_points or []
        },
        'meta': {
            'ai_model': record.ai_model,
            'confidence': record.confidence,
            'created_at': record.created_at.isoformat() if record.created_at else None,
            'version': record.version
        }
    }

    return report


@router.get("/evidence/{evidence_id}/analysis-history")
async def get_evidence_analysis_history(
    evidence_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    获取证据的分析历史记录
    """
    records = db.query(EvidenceAnalysisRecord).filter(
        EvidenceAnalysisRecord.evidence_id == evidence_id
    ).order_by(EvidenceAnalysisRecord.created_at.desc()).limit(limit).all()

    return {
        'evidence_id': evidence_id,
        'total': len(records),
        'records': [r.to_dict() for r in records]
    }


@router.delete("/evidence/{evidence_id}/analysis-history")
async def clear_evidence_analysis_history(
    evidence_id: str,
    db: Session = Depends(get_db)
):
    """
    清除证据的分析历史记录
    """
    db.query(EvidenceAnalysisRecord).filter(
        EvidenceAnalysisRecord.evidence_id == evidence_id
    ).delete()

    db.commit()

    return {'message': '分析历史已清除'}
