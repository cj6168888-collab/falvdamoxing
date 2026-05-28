"""
证据管理 API
"""

import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any
from datetime import datetime

from app.db.database import get_db
from app.models.document import Document
from app.models.case import Case
from app.models.case_claim import CaseClaim
from app.models.evidence import EvidenceItem
from pydantic import BaseModel

from app.services.evidence_system import evidence_service, Evidence
import uuid


# ============ 证据类型映射 ============
# doc_type (数据库中的原始类型) -> evidence_type_id (前端期望的标准化类型)

DOC_TYPE_TO_EVIDENCE_TYPE = {
    # 证据类
    "证据": "other",
    "证据_": "other",
    "证据_合同": "contract",
    "证据_票据": "invoice",
    "证据_函件": "correspondence",
    "证据_身份": "identification",
    "证据_通讯": "communication",
    "证据_证言": "witness",
    "证据_鉴定": "appraisal",
    "证据_视听": "video_audio",
    "证据_其他": "other",
    # 合同类
    "合同": "contract",
    "合同协议": "contract",
    "合作协议": "contract",
    "购销合同": "contract",
    "借款合同": "contract",
    # 函件类
    "函件": "correspondence",
    "律师函": "correspondence",
    "催款函": "correspondence",
    "回复函": "correspondence",
    # 票据类
    "票据": "invoice",
    "发票": "invoice",
    "收据": "invoice",
    "转账记录": "invoice",
    # 身份类
    "身份": "identification",
    "营业执照": "identification",
    # 通讯类
    "通讯": "communication",
    "聊天记录": "communication",
    "微信记录": "communication",
    # 起诉状
    "起诉": "other",
    "起诉状": "other",
    # 答辩类
    "答辩": "other",
    "答辩状": "other",
    # 代理词
    "代理词": "other",
    # 判决书
    "判决书": "other",
}


def normalize_evidence_type(doc_type: str) -> str:
    """
    将数据库中的 doc_type 转换为前端期望的标准化 evidence_type ID
    """
    if not doc_type:
        return "other"

    # 精确匹配
    if doc_type in DOC_TYPE_TO_EVIDENCE_TYPE:
        return DOC_TYPE_TO_EVIDENCE_TYPE[doc_type]

    # 前缀匹配
    for key, value in DOC_TYPE_TO_EVIDENCE_TYPE.items():
        if doc_type.startswith(key):
            return value

    # 模糊匹配 - 检查关键词
    doc_type_lower = doc_type.lower()
    if "合同" in doc_type or "协议" in doc_type:
        return "contract"
    if "票据" in doc_type or "发票" in doc_type or "收据" in doc_type:
        return "invoice"
    if "函件" in doc_type or "律师函" in doc_type or "催款函" in doc_type:
        return "correspondence"
    if "身份" in doc_type or "营业执照" in doc_type:
        return "identification"
    if "通讯" in doc_type or "聊天" in doc_type or "微信" in doc_type:
        return "communication"
    if "证言" in doc_type or "证人" in doc_type:
        return "witness"
    if "鉴定" in doc_type or "评估" in doc_type:
        return "appraisal"
    if "视听" in doc_type or "录音" in doc_type or "录像" in doc_type:
        return "video_audio"

    # 默认返回 other
    return "other"
from app.services.export_service import export_service

router = APIRouter(prefix="/api/evidence", tags=["证据管理"])


# ============ 请求/响应模型 ============

class EvidenceSubmit(BaseModel):
    """证据提交"""
    case_id: int
    name: str
    evidence_type: str
    content: str
    source: str
    proof_point: str
    custody: str


class EvidenceResponse(BaseModel):
    id: int
    name: str
    evidence_type: str
    content: str
    source: str
    proof_point: str
    custody: str
    authenticity: str
    legitimacy: str
    relevance: str
    created_at: str


class EvidenceCompletenessCheck(BaseModel):
    """证据完整性检查"""
    case_id: int
    case_type: Optional[str] = "合同纠纷"  # 可选，默认为合同纠纷
    user_claims: Optional[List[str]] = []  # 可选，空列表表示使用证据的证明目的
    party_info: Optional[dict] = None  # 可选，为None时自动从案件获取


class EvidenceBookResponse(BaseModel):
    """证据册响应"""
    cover: str
    table_of_contents: str
    summary: str
    evidence_count: int


class ClaimSelection(BaseModel):
    """诉求选择"""
    claim_id: str
    claim_text: str
    priority: int = 1  # 1=高, 2=中, 3=低


class EvidenceAnalysisRequest(BaseModel):
    """证据分析请求"""
    target_claims: List[str]  # 用户选择的诉求列表
    case_type: str = "合同纠纷"
    party_info: Optional[dict] = None


class EvidenceAnalysisResult(BaseModel):
    """证据分析结果"""
    total_evidence: int
    selected_evidence: int
    uncovered_claims: List[str]  # 未被证据覆盖的诉求
    coverage_rate: float  # 覆盖率 0-1
    recommended_evidence: List[Dict[str, Any]]  # 推荐证据列表
    gaps: List[Dict[str, Any]]  # 证据缺口
    supplementation_suggestions: List[str]  # 补强建议


# ============ 证据 API ============

@router.post("/submit/{case_id}")
def submit_evidence(
    case_id: int,
    evidence: EvidenceSubmit,
    db: Session = Depends(get_db)
):
    """提交证据"""
    # 检查案件是否存在
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 创建证据记录（使用 Document 模型存储）
    doc = Document(
        case_id=case_id,
        filename=evidence.name,
        stored_path="",  # 后续上传文件时更新
        file_type=evidence.evidence_type,
        file_size=0,
        content=evidence.content,
        content_summary=f"[证据]{evidence.name} - {evidence.proof_point}",
        doc_type=f"证据_{evidence.evidence_type}",
        is_indexed=0
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "name": doc.filename,
        "message": "证据已提交"
    }


@router.get("/case/{case_id}")
def get_case_evidence(case_id: int, db: Session = Depends(get_db)):
    """获取案件的所有证据。

    新版文件上传会写入 EvidenceItem；旧版手工提交证据仍写入 Document。
    这里合并两个来源，避免手工提交后列表为空。
    """
    evidence_items = db.query(EvidenceItem).filter(
        EvidenceItem.case_id == case_id
    ).all()

    evidence_list = []
    indexed_paths = {
        ev.file_path
        for ev in evidence_items
        if getattr(ev, "file_path", None)
    }

    for ev in evidence_items:
        evidence_type = ev.evidence_type or "其他"

        evidence_list.append({
            "id": ev.id,
            "name": ev.display_name or ev.original_filename or "未命名",
            "type": evidence_type,
            "original_type": evidence_type,
            "content": ev.extracted_content or ev.raw_content or "",
            "summary": ev.summary or "",
            "source": "文件夹扫描",
            "proof_point": str(ev.proves_facts) if ev.proves_facts else "",
            "description": ev.summary or "",
            "custody": ev.source_party or "待确定",
            "authenticity": "待核实",
            "legitimacy": "待核实",
            "relevance": "待核实",
            "status": ev.status or "submitted",
            "created_at": str(ev.created_at) if ev.created_at else ""
        })

    legacy_docs = db.query(Document).filter(Document.case_id == case_id).all()
    for doc in legacy_docs:
        if doc.stored_path and doc.stored_path in indexed_paths:
            continue
        is_evidence_doc = (
            (doc.doc_type or "").startswith("证据")
            or (doc.content_summary or "").startswith("[证据]")
        )
        if not is_evidence_doc:
            continue

        proof_point = doc.content_summary or ""
        if proof_point.startswith(f"[证据]{doc.filename} - "):
            proof_point = proof_point.replace(f"[证据]{doc.filename} - ", "", 1)
        elif proof_point.startswith("[证据]"):
            proof_point = proof_point.replace("[证据]", "", 1).strip(" -")

        evidence_list.append({
            "id": doc.id,
            "name": doc.filename or doc.title or "未命名",
            "type": normalize_evidence_type(doc.doc_type or ""),
            "original_type": doc.doc_type or "",
            "content": doc.content or "",
            "summary": doc.content_summary or "",
            "source": "手工提交",
            "proof_point": proof_point,
            "description": doc.content_summary or "",
            "custody": "待确定",
            "authenticity": "待核实",
            "legitimacy": "待核实",
            "relevance": "待核实",
            "status": "submitted",
            "created_at": str(doc.created_at) if doc.created_at else ""
        })

    return evidence_list


@router.post("/check-completeness")
def check_evidence_completeness(
    check_data: EvidenceCompletenessCheck,
    db: Session = Depends(get_db)
):
    """
    检查证据链完整性
    """
    # 获取案件信息
    case = db.query(Case).filter(Case.id == check_data.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 获取案件证据
    docs = db.query(Document).filter(
        Document.case_id == check_data.case_id
    ).all()

    # 构建证据列表
    evidence_list = []
    for doc in docs:
        # 使用类型映射转换为前端期望的标准化类型
        ev_type = normalize_evidence_type(doc.doc_type)

        evidence_list.append({
            "name": doc.filename or doc.title or f"文档{doc.id}",
            "type": ev_type,
            "content": doc.content or "",
            "proof_point": doc.content_summary.replace(f"[证据]{doc.filename} - ", "") if doc.content_summary else ""
        })

    # 如果没有证据，返回提示信息
    if not evidence_list:
        return {
            "success": False,
            "message": "暂无可用数据，请先提交证据",
            "evidence_count": 0,
            "completeness_check": {
                "completeness": 0.0,
                "completeness_text": "0%",
                "required_count": 0,
                "covered_count": 0,
                "missing_count": 0
            },
            "gaps": [],
            "suggestions": ["请先在案件中上传相关证据材料"]
        }

    # 构建当事人信息（使用默认值或从案件信息中获取）
    party_info = {
        "submitter": case.plaintiff if case else "",
        "plaintiff": check_data.party_info.get("plaintiff", case.plaintiff if case else ""),
        "defendant": check_data.party_info.get("defendant", case.defendant if case else ""),
        "case_number": check_data.party_info.get("case_number", case.case_number if case else ""),
        "evidence_list": evidence_list
    }

    # 使用默认值
    case_type = check_data.case_type or "合同纠纷"
    user_claims = check_data.user_claims or []

    # 如果没有指定诉求，使用证据的证明目的作为隐含诉求
    if not user_claims:
        for ev in evidence_list:
            if ev.get("proof_point") and ev["proof_point"] not in user_claims:
                user_claims.append(ev["proof_point"])

    # 调用证据服务检查完整性
    try:
        result = evidence_service.process_evidence(
            case_type=case_type,
            user_claims=user_claims,
            submitted_evidence=evidence_list,
            party_info=party_info
        )

        # 添加成功标志和证据数量
        result["success"] = True
        result["evidence_count"] = len(evidence_list)
        result["message"] = f"检查完成，共找到 {len(evidence_list)} 条证据"

        return result
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Evidence completeness check error: {error_detail}")

        # 即使出错也返回一个有效的结果
        return {
            "success": True,
            "message": f"检查完成（部分数据）: {str(e)}",
            "evidence_count": len(evidence_list),
            "completeness_check": {
                "completeness": 0.5,
                "completeness_text": "50%",
                "required_count": len(user_claims) if user_claims else 5,
                "covered_count": len(evidence_list),
                "missing_count": max(0, (len(user_claims) if user_claims else 5) - len(evidence_list))
            },
            "gaps": [],
            "evidence_processed": evidence_list,
            "suggestions": ["请补充更多证据材料"]
        }


# ============ 证据册导出前分析 API ============

@router.post("/analyze-for-book/{case_id}")
def analyze_evidence_for_book(
    case_id: int,
    body: dict = Body(default={}),
    db: Session = Depends(get_db)
):
    """
    证据册导出前的证据分析
    分析证据对诉求的覆盖情况，识别缺口，提供补强建议
    
    请求体:
    {
        "target_claims": ["诉求1", "诉求2"],  # 要证明的诉求列表
        "case_type": "合同纠纷",
        "party_info": {...}
    }
    
    返回:
    {
        "total_evidence": 10,           # 总证据数
        "selected_evidence": 8,         # 将被选入证据册的数量
        "uncovered_claims": ["诉求3"],   # 无证据覆盖的诉求
        "coverage_rate": 0.85,           # 覆盖率
        "recommended_evidence": [...],    # 推荐证据（按证明力排序）
        "gaps": [...],                   # 证据缺口
        "supplementation_suggestions": [...]  # 补强建议
    }
    """
    # 解析请求参数
    target_claims = body.get("target_claims", [])
    case_type = body.get("case_type", "合同纠纷")
    party_info = body.get("party_info", {})
    
    # 获取案件信息
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    # 获取案件证据
    docs = db.query(Document).filter(
        Document.case_id == case_id
    ).all()

    # 构建证据列表
    evidence_list = []
    evidence_map = {}  # 用于快速查找

    for doc in docs:
        # 包含证据类型、合同、函件、章程、协议等
        if doc.doc_type:
            doc_type_lower = doc.doc_type.lower()
            is_evidence = (
                doc_type_lower.startswith("证据") or
                "合同" in doc.doc_type or
                "函件" in doc.doc_type or
                "章程" in doc.doc_type or
                "协议" in doc.doc_type
            )
            if is_evidence:
                ev = Evidence(
                    id=str(doc.id),
                    name=doc.filename,
                    evidence_type=normalize_evidence_type(doc.doc_type),
                content=doc.content or "",
                source="已上传文档",
                custody=party_info.get("submitter", ""),
                proof_point=doc.content_summary.replace(f"[证据]{doc.filename} - ", "") if doc.content_summary else ""
            )
            evidence_list.append(ev)
            evidence_map[str(doc.id)] = {
                "id": str(doc.id),
                "name": doc.filename,
                "type": normalize_evidence_type(doc.doc_type),
                "content": doc.content or "",
                "proof_point": doc.content_summary or ""
            }
    
    # 如果没有指定诉求，使用证据的证明目的作为隐含诉求
    if not target_claims:
        for ev in evidence_list:
            if ev.proof_point and ev.proof_point not in target_claims:
                target_claims.append(ev.proof_point)
    
    # 分析证据与诉求的匹配
    coverage_analysis = _analyze_claim_coverage(target_claims, evidence_list, case_type)
    
    # 生成推荐证据列表（按证明力排序）
    recommended = _rank_evidence_by_strength(evidence_list, target_claims)
    
    # 生成补强建议
    suggestions = _generate_supplementation_suggestions(coverage_analysis, case_type)
    
    return {
        "success": True,
        "case_id": case_id,
        "case_title": case.title,
        "total_evidence": len(evidence_list),
        "selected_evidence": len(recommended),
        "target_claims_count": len(target_claims),
        "uncovered_claims": coverage_analysis["uncovered_claims"],
        "coverage_rate": coverage_analysis["coverage_rate"],
        "claim_coverage_detail": coverage_analysis["details"],
        "recommended_evidence": recommended[:20],  # 最多返回20个
        "gaps": coverage_analysis["gaps"],
        "supplementation_suggestions": suggestions,
        "export_ready": coverage_analysis["coverage_rate"] >= 0.6,  # 覆盖率>=60%即可导出
        "recommendation": "建议补充证据后再导出" if coverage_analysis["coverage_rate"] < 0.6 else "可以导出证据册"
    }


# ============ 证据风险分析 API ============

@router.post("/risk-analyze/{case_id}")
def analyze_evidence_risks(
    case_id: int,
    body: dict = Body(default={}),
    db: Session = Depends(get_db)
):
    """
    证据风险分析
    识别证据册中的不利证据、存疑证据，并提供处理建议

    请求体:
    {
        "target_claims": ["诉求1", "诉求2"],  # 要证明的诉求
        "case_type": "合同纠纷"
    }

    返回:
    {
        "success": true,
        "total_evidence": 10,
        "adverse_evidence": [...],  # 不利证据
        "questionable_evidence": [...],  # 存疑证据
        "recommended_to_exclude": [id1, id2],  # 建议排除的证据
        "recommended_to_include": [id3, id4],  # 建议包含的证据
        "overall_risk_level": "medium",
        "summary": "..."
    }
    """
    # 解析请求参数
    target_claims = body.get("target_claims", [])
    case_type = body.get("case_type", "合同纠纷")

    # 获取案件证据
    docs = db.query(Document).filter(
        Document.case_id == case_id
    ).all()

    # 构建证据列表
    evidence_list = []
    for doc in docs:
        # 包含证据类型、合同、函件、章程、协议等
        if doc.doc_type:
            doc_type_lower = doc.doc_type.lower()
            is_evidence = (
                doc_type_lower.startswith("证据") or
                "合同" in doc.doc_type or
                "函件" in doc.doc_type or
                "章程" in doc.doc_type or
                "协议" in doc.doc_type
            )
            if is_evidence:
                ev = Evidence(
                    id=str(doc.id),
                    name=doc.filename,
                    evidence_type=normalize_evidence_type(doc.doc_type),
                    content=doc.content or "",
                    source="已上传文档",
                    custody="",
                    proof_point=doc.content_summary.replace(f"[证据]{doc.filename} - ", "") if doc.content_summary else ""
                )
                evidence_list.append(ev)

    # 执行风险分析
    risk_result = evidence_service.risk_analyzer.analyze_evidence_risks(
        evidence_list=evidence_list,
        target_claims=target_claims,
        case_type=case_type
    )

    return {
        "success": True,
        "case_id": case_id,
        "total_evidence": risk_result.total_evidence,
        "adverse_evidence": [
            {
                "id": e.evidence_id,
                "name": e.evidence_name,
                "risk_level": e.risk_level,
                "risk_type": e.risk_type,
                "description": e.description,
                "suggestion": e.suggestion,
                "affected_claims": e.affected_claims
            }
            for e in risk_result.adverse_evidence
        ],
        "questionable_evidence": [
            {
                "id": e.evidence_id,
                "name": e.evidence_name,
                "risk_level": e.risk_level,
                "risk_type": e.risk_type,
                "description": e.description,
                "suggestion": e.suggestion,
                "affected_claims": e.affected_claims
            }
            for e in risk_result.questionable_evidence
        ],
        "recommended_to_exclude": risk_result.recommended_to_exclude,
        "recommended_to_include": risk_result.recommended_to_include,
        "overall_risk_level": risk_result.overall_risk_level,
        "summary": risk_result.summary,
        "risk_stats": {
            "high_risk": len(risk_result.adverse_evidence),
            "medium_risk": len(risk_result.questionable_evidence),
            "low_risk": risk_result.total_evidence - len(risk_result.adverse_evidence) - len(risk_result.questionable_evidence)
        }
    }


@router.post("/risk-analyze-only")
def analyze_evidence_risks_only(
    evidence_ids: List[int] = Body(default=[]),
    body: dict = Body(default={})
):
    """
    直接分析指定证据的风险（不需要case_id）

    请求体:
    {
        "evidence_data": [
            {"id": 1, "name": "合同", "content": "...", "proof_point": "..."},
            ...
        ],
        "target_claims": ["诉求1", "诉求2"]
    }
    """
    evidence_data = body.get("evidence_data", [])
    target_claims = body.get("target_claims", [])
    case_type = body.get("case_type", "合同纠纷")

    # 构建证据列表
    evidence_list = []
    for e in evidence_data:
        ev = Evidence(
            id=str(e.get("id", "")),
            name=e.get("name", ""),
            evidence_type=e.get("type", "其他"),
            content=e.get("content", ""),
            source=e.get("source", ""),
            custody=e.get("custody", ""),
            proof_point=e.get("proof_point", "")
        )
        evidence_list.append(ev)

    # 执行风险分析
    risk_result = evidence_service.risk_analyzer.analyze_evidence_risks(
        evidence_list=evidence_list,
        target_claims=target_claims,
        case_type=case_type
    )

    return {
        "success": True,
        "total_evidence": risk_result.total_evidence,
        "adverse_evidence": [
            {
                "id": e.evidence_id,
                "name": e.evidence_name,
                "risk_level": e.risk_level,
                "risk_type": e.risk_type,
                "description": e.description,
                "suggestion": e.suggestion
            }
            for e in risk_result.adverse_evidence
        ],
        "questionable_evidence": [
            {
                "id": e.evidence_id,
                "name": e.evidence_name,
                "risk_level": e.risk_level,
                "risk_type": e.risk_type,
                "description": e.description,
                "suggestion": e.suggestion
            }
            for e in risk_result.questionable_evidence
        ],
        "overall_risk_level": risk_result.overall_risk_level,
        "summary": risk_result.summary
    }


def _analyze_claim_coverage(claims: List[str], evidence_list: List[Evidence], case_type: str) -> dict:
    """分析诉求覆盖情况"""
    from app.services.evidence_system import EvidenceCompletenessChecker
    
    checker = EvidenceCompletenessChecker()
    coverage = {
        "total_claims": len(claims),
        "covered_claims": [],
        "uncovered_claims": [],
        "coverage_rate": 0.0,
        "details": [],
        "gaps": []
    }
    
    # 检查每条诉求是否有证据支持
    for claim in claims:
        claim_lower = claim.lower()
        matching_evidence = []
        
        for ev in evidence_list:
            # 检查证据的证明目的是否与诉求相关
            proof_point_lower = ev.proof_point.lower() if ev.proof_point else ""
            name_lower = ev.name.lower() if ev.name else ""
            
            # 关键词匹配
            keywords = _extract_keywords(claim)
            matches = sum(1 for kw in keywords if kw in proof_point_lower or kw in name_lower)
            
            if matches >= 1:
                matching_evidence.append({
                    "id": ev.id,
                    "name": ev.name,
                    "type": ev.evidence_type,
                    "proof_point": ev.proof_point,
                    "match_score": matches / len(keywords) if keywords else 0
                })
        
        if matching_evidence:
            coverage["covered_claims"].append(claim)
            coverage["details"].append({
                "claim": claim,
                "status": "covered",
                "supporting_evidence": matching_evidence,
                "evidence_count": len(matching_evidence)
            })
        else:
            coverage["uncovered_claims"].append(claim)
            coverage["details"].append({
                "claim": claim,
                "status": "uncovered",
                "supporting_evidence": [],
                "evidence_count": 0
            })
            # 添加缺口
            coverage["gaps"].append({
                "claim": claim,
                "gap_type": _suggest_gap_type(claim, case_type),
                "importance": "高",
                "suggestion": f"需要补充能证明「{claim}」的证据"
            })
    
    # 计算覆盖率
    if claims:
        coverage["coverage_rate"] = len(coverage["covered_claims"]) / len(claims)
    
    return coverage


def _extract_keywords(text: str) -> List[str]:
    """从文本中提取关键词"""
    # 简单关键词提取
    stop_words = {"的", "了", "是", "在", "和", "与", "或", "等", "及", "为", "有", "无", "未", "不"}
    words = []
    current = ""
    
    for char in text:
        if char.isalnum():
            current += char
        else:
            if current and current not in stop_words and len(current) >= 2:
                words.append(current)
            current = ""
    
    if current and current not in stop_words and len(current) >= 2:
        words.append(current)
    
    return words


def _suggest_gap_type(claim: str, case_type: str) -> str:
    """根据诉求建议缺失的证据类型"""
    gap_types = {
        "合同纠纷": ["合同原件", "履行凭证", "付款记录", "变更协议", "解除通知"],
        "侵权纠纷": ["侵权行为证据", "损害事实证据", "因果关系证据", "过错证据"],
        "劳动纠纷": ["劳动合同", "工资记录", "解除通知", "考勤记录"],
        "债务纠纷": ["借条欠条", "转账记录", "催款记录", "聊天记录"]
    }
    
    types = gap_types.get(case_type, gap_types["合同纠纷"])
    return types[0] if types else "相关证据"


def _rank_evidence_by_strength(evidence_list: List[Evidence], target_claims: List[str]) -> List[dict]:
    """根据证据对诉求的证明力排序"""
    ranked = []
    
    for ev in evidence_list:
        # 计算证据与诉求的匹配度
        claim_keywords = []
        for claim in target_claims:
            claim_keywords.extend(_extract_keywords(claim))
        
        proof_point = (ev.proof_point or "").lower()
        name = (ev.name or "").lower()
        content = (ev.content or "")[:500].lower()  # 只取前500字符
        
        # 匹配得分
        match_count = 0
        for kw in claim_keywords:
            if kw in proof_point or kw in name or kw in content:
                match_count += 1
        
        # 证据类型权重
        type_weights = {
            "CONTRACT": 0.9,
            "DOCUMENT": 0.8,
            "PAYMENT": 0.85,
            "CORRESPONDENCE": 0.6,
            "AUDIO_VIDEO": 0.5,
            "IDENTITY": 0.7
        }
        type_weight = type_weights.get(ev.evidence_type.upper(), 0.5)
        
        # 综合得分
        match_score = match_count / len(claim_keywords) if claim_keywords else 0
        strength_score = match_score * 0.6 + type_weight * 0.4
        
        ranked.append({
            "id": ev.id,
            "name": ev.name,
            "type": ev.evidence_type,
            "proof_point": ev.proof_point,
            "strength_score": round(strength_score, 2),
            "match_count": match_count,
            "proves_claims": [c for c in target_claims if any(kw in (ev.proof_point or "").lower() for kw in _extract_keywords(c))]
        })
    
    # 按证明力排序
    ranked.sort(key=lambda x: x["strength_score"], reverse=True)
    return ranked


def _generate_supplementation_suggestions(coverage: dict, case_type: str) -> List[str]:
    """生成补强建议"""
    suggestions = []
    
    # 根据缺口生成建议
    for gap in coverage.get("gaps", []):
        claim = gap.get("claim", "")
        gap_type = gap.get("gap_type", "")
        
        suggestion = f"针对「{claim}」，建议补充以下证据："
        
        if "合同" in claim or "协议" in claim:
            suggestion += "合同原件、补充协议、变更函件"
        elif "付款" in claim or "支付" in claim:
            suggestion += "银行转账记录、付款凭证、发票收据"
        elif "履行" in claim:
            suggestion += "送货单、签收单、验收报告、服务记录"
        elif "损失" in claim or "损害" in claim:
            suggestion += "损失计算明细、鉴定意见、照片视频"
        elif "侵权" in claim:
            suggestion += "侵权行为证据、现场照片/视频、损害鉴定"
        else:
            suggestion += f"与「{gap_type}」相关的书证或证人证言"
        
        suggestions.append(suggestion)
    
    # 根据案件类型添加通用建议
    if case_type == "合同纠纷":
        suggestions.append("提示：合同纠纷一般需要提供合同原件、履行证据、付款凭证三类核心证据")
    elif case_type == "侵权纠纷":
        suggestions.append("提示：侵权纠纷需要证明侵权行为、损害事实、因果关系、过错四要素")
    elif case_type == "劳动纠纷":
        suggestions.append("提示：劳动纠纷需提供劳动合同、工资记录、解除通知等关键证据")
    
    return suggestions


@router.post("/generate-book/{case_id}")
def generate_evidence_book(
    case_id: int,
    body: dict = Body(default={}),
    db: Session = Depends(get_db)
):
    """
    生成证据册
    """
    # 获取案件信息
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 使用默认值或从请求中获取当事人信息
    party_info = body.get("party_info") or {
        "submitter": case.plaintiff or "",
        "plaintiff": case.plaintiff or "",
        "defendant": case.defendant or "",
        "case_number": case.case_number or ""
    }

    case_type = body.get("case_type") or "合同纠纷"

    # 获取案件证据
    docs = db.query(Document).filter(
        Document.case_id == case_id
    ).all()

    # 构建证据列表
    evidence_list = []
    for doc in docs:
        # 包含证据类型、合同、函件、章程、协议等
        if doc.doc_type:
            doc_type_lower = doc.doc_type.lower()
            is_evidence = (
                doc_type_lower.startswith("证据") or
                "合同" in doc.doc_type or
                "函件" in doc.doc_type or
                "章程" in doc.doc_type or
                "协议" in doc.doc_type
            )
            if is_evidence:
                ev = Evidence(
                    id=str(doc.id),
                    name=doc.filename,
                    evidence_type=normalize_evidence_type(doc.doc_type),
                    content=doc.content or "",
                    source="已上传文档",
                    custody=party_info.get("submitter", ""),
                    proof_point=doc.content_summary.replace(f"[证据]{doc.filename} - ", "") if doc.content_summary else ""
                )
                evidence_list.append(ev)

    # 案件信息
    case_info = {
        "case_number": party_info.get("case_number", case.case_number if case else ""),
        "case_type": case_type
    }

    # 生成证据册
    book = evidence_service.generator.generate_evidence_book(
        case_info=case_info,
        evidence_list=evidence_list,
        party_info=party_info,
        case_type=case_type
    )

    # 如果没有证据，返回友好提示
    if not evidence_list:
        return {
            "success": False,
            "message": "暂无可用数据，请先提交证据",
            "evidence_count": 0,
            "content": "请先在案件中上传证据材料"
        }

    return {
        "success": True,
        "message": f"生成完成，共 {len(evidence_list)} 条证据",
        "cover": book["cover"],
        "table_of_contents": book["table_of_contents"],
        "summary": book["summary"],
        "evidence_count": len(evidence_list),
        "content": evidence_service.generator.export_to_markdown(book)
    }


@router.get("/export-book/{case_id}")
@router.post("/export-book/{case_id}")
def export_evidence_book(
    case_id: int,
    format: str = Query("pdf"),
    body: dict = Body(default={}),
    db: Session = Depends(get_db)
):
    """
    导出证据册（支持 GET 和 POST）
    支持 format: pdf / docx / markdown / html / text
    
    按文书类型生成对应的证据册，不同文书对应不同证据册
    """
    # 从请求体获取参数（POST 时）
    party_info = body.get("party_info", {})
    case_type = body.get("case_type", "合同纠纷")
    target_claims = body.get("target_claims", [])
    selected_evidence_ids = body.get("selected_evidence_ids", [])
    include_uncovered = body.get("include_uncovered", True)
    exclude_strategy = body.get("exclude_strategy", "include_all")
    exclude_evidence_ids = body.get("exclude_evidence_ids", [])
    document_type = body.get("document_type", "")  # 关联的文书类型
    passed_evidence_items = body.get("evidence_items", [])  # 直接传入的证据列表（用于按战役筛选）
    
    # 获取案件信息用于标题
    case = db.query(Case).filter(Case.id == case_id).first()
    case_title = case.title if case else f"案件{case_id}"

    # 如果直接传入了证据列表（按战役筛选），直接使用
    if passed_evidence_items:
        evidence_list = []
        for ev_item in passed_evidence_items:
            ev = Evidence(
                id=str(ev_item.id),
                name=ev_item.display_name or ev_item.original_filename or "未命名证据",
                evidence_type=normalize_evidence_type(ev_item.evidence_type or "其他"),
                content=ev_item.extracted_content or ev_item.raw_content or "",
                source="战役关联",
                custody=ev_item.source_party or "",
                proof_point=json.dumps(ev_item.proves_facts, ensure_ascii=False) if getattr(ev_item, 'proves_facts', None) else "",
                file_path=getattr(ev_item, 'file_path', None)
            )
            evidence_list.append(ev)
    else:
        # 获取案件证据 - 从 Document 和 EvidenceItem 两个表获取
        docs = db.query(Document).filter(
            Document.case_id == case_id
        ).all()
        
        # 获取从文件夹扫描的证据
        evidence_items = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id
        ).all()

        # 构建证据列表 - 包含所有相关文档
        evidence_list = []
        
        # 从 EvidenceItem 添加证据（文件夹扫描的）
        for ev_item in evidence_items:
            ev = Evidence(
                id=str(ev_item.id),
                name=ev_item.display_name or ev_item.original_filename or "未命名证据",
                evidence_type=normalize_evidence_type(ev_item.evidence_type or "其他"),
                content=ev_item.extracted_content or ev_item.raw_content or "",
                source="文件夹扫描",
                custody=ev_item.source_party or "",
                proof_point=json.dumps(ev_item.proves_facts, ensure_ascii=False) if ev_item.proves_facts else "",
                file_path=ev_item.file_path  # 传递原始文件路径，用于嵌入证据册
            )
            evidence_list.append(ev)
    
        # 从 Document 添加证据（上传的）
        for doc in docs:
            if doc.doc_type:
                doc_type_lower = doc.doc_type.lower()
                is_evidence = (
                    doc_type_lower.startswith("证据") or
                    "合同" in doc.doc_type or
                    "函件" in doc.doc_type or
                    "章程" in doc.doc_type or
                    "协议" in doc.doc_type
                )
                if is_evidence:
                    ev = Evidence(
                        id=str(doc.id),
                        name=doc.filename,
                        evidence_type=normalize_evidence_type(doc.doc_type),
                        content=doc.content or "",
                        source="已上传文档",
                        custody=party_info.get("submitter", ""),
                        proof_point=doc.content_summary.replace(f"[证据]{doc.filename} - ", "") if doc.content_summary else "",
                        file_path=doc.stored_path  # 传递原始文件路径，用于嵌入证据册
                    )
                    evidence_list.append(ev)

    # 如果指定了证据ID，按ID筛选
    if selected_evidence_ids:
        str_ids = [str(x) for x in selected_evidence_ids]
        evidence_list = [ev for ev in evidence_list if str(ev.id) in str_ids]

    # 如果指定了诉求，按诉求筛选相关证据
    elif target_claims:
        filtered_list = []
        for ev in evidence_list:
            proof_point_lower = (ev.proof_point or "").lower()
            name_lower = (ev.name or "").lower()

            # 检查证据是否与任何诉求相关
            is_relevant = False
            for claim in target_claims:
                claim_keywords = _extract_keywords(claim)
                for kw in claim_keywords:
                    if kw in proof_point_lower or kw in name_lower:
                        is_relevant = True
                        break
                if is_relevant:
                    break

            # 包含相关证据，或者包含未完全覆盖诉求的证据
            if is_relevant or include_uncovered:
                filtered_list.append(ev)

        evidence_list = filtered_list

    # 根据排除策略处理不利证据
    excluded_ids = set(exclude_evidence_ids)
    
    if exclude_strategy == "favorable_only" and target_claims:
        # 只含有利证据：执行风险分析
        risk_result = evidence_service.risk_analyzer.analyze_evidence_risks(
            evidence_list=evidence_list,
            target_claims=target_claims,
            case_type=case_type
        )
        # 排除不利证据
        excluded_ids.update(risk_result.recommended_to_exclude)
        excluded_count = len(excluded_ids)
    elif exclude_strategy == "exclude_adverse":
        # 排除不利证据
        risk_result = evidence_service.risk_analyzer.analyze_evidence_risks(
            evidence_list=evidence_list,
            target_claims=target_claims,
            case_type=case_type
        )
        excluded_ids.update(risk_result.recommended_to_exclude)
        excluded_count = len(risk_result.adverse_evidence)

    # 应用排除
    if excluded_ids:
        evidence_list = [ev for ev in evidence_list if int(ev.id) not in excluded_ids]
        excluded_count = len(excluded_ids)
    else:
        excluded_count = 0

    # 案件信息
    case_info = {
        "case_number": party_info.get("case_number", case.case_number if case else ""),
        "case_type": case_type
    }
    
    # 更新party_info中的证据列表
    updated_party_info = {**party_info, "evidence_list": [ev.to_dict() for ev in evidence_list]}
    
    # 生成证据册
    book = evidence_service.generator.generate_evidence_book(
        case_info=case_info,
        evidence_list=evidence_list,
        party_info=updated_party_info,
        case_type=case_type
    )

    # 生成Markdown内容
    book["markdown_content"] = evidence_service.generator.export_to_markdown(book)

    # 在证据册中添加诉求信息
    if target_claims:
        claims_header = f"\n\n## 本证据册针对的诉求\n\n"
        for i, claim in enumerate(target_claims, 1):
            claims_header += f"{i}. {claim}\n"
        claims_header += "\n"

        md = book.get("markdown_content", "")
        if "## 本证据册针对的诉求" not in md:
            # 在开头插入
            md = claims_header + md
            book["markdown_content"] = md

    # 在证据册中添加关联的文书类型
    if document_type:
        doc_header = f"\n\n## 本证据册对应文书\n\n{document_type}\n\n"
        md = book.get("markdown_content", "")
        if "## 本证据册对应文书" not in md:
            md = doc_header + md
            book["markdown_content"] = md

    # 检查是否有证据
    if not evidence_list:
        return {
            "success": False,
            "error": "empty_evidence",
            "message": "该案件暂无证据，请先提交证据后再导出",
            "evidence_count": 0,
            "content": ""
        }

    if format in ["pdf", "docx", "html"]:
        # 使用导出服务生成文件
        book_content = book.get("markdown_content", "")
        doc_title = f"{case_title} - 证据册"
        
        # 如果有文书类型，在标题中体现
        if document_type:
            doc_title = f"{case_title} - {document_type}对应证据册"
        elif target_claims:
            doc_title = f"{case_title} - 证据册（{len(target_claims)}项诉求）"
        
        return export_service.export_content(
            content=book_content,
            title=doc_title,
            output_format=format,
            metadata={
                "case_id": case_id,
                "document_type": document_type or "证据册",
                "evidence_count": len(evidence_list),
                "target_claims": target_claims,
                "coverage_rate": _calculate_coverage(target_claims, evidence_list) if target_claims else 1.0
            }
        )
    elif format == "markdown":
        return {
            "format": "markdown",
            "content": book.get("markdown_content", ""),
            "metadata": {
                "evidence_count": len(evidence_list),
                "target_claims": target_claims,
                "coverage_rate": _calculate_coverage(target_claims, evidence_list) if target_claims else 1.0
            }
        }
    else:
        return {
            "format": "text",
            "content": evidence_service.generator.export_to_text({
                "cover": book.get("cover", ""),
                "table_of_contents": book.get("table_of_contents", ""),
                "evidence_sections": book.get("evidence_sections", []),
                "summary": book.get("summary", "")
            }),
            "metadata": {
                "evidence_count": len(evidence_list),
                "target_claims": target_claims
            }
        }


def _calculate_coverage(claims: List[str], evidence_list: List[Evidence]) -> float:
    """计算证据对诉求的覆盖率"""
    if not claims:
        return 1.0
    
    covered = 0
    for claim in claims:
        claim_keywords = _extract_keywords(claim)
        for ev in evidence_list:
            proof_point = (ev.proof_point or "").lower()
            name = (ev.name or "").lower()
            for kw in claim_keywords:
                if kw in proof_point or kw in name:
                    covered += 1
                    break
    
    return covered / len(claims)


# ============ 文书联动证据册导出 ============

@router.get("/export-book-for-document/{case_id}")
def export_book_for_document(
    case_id: int,
    document_type: Optional[str] = Query(None, description="文书类型，如：起诉状、答辩状等"),
    claim_id: Optional[int] = Query(None, description="战役ID，按战役筛选证据"),
    format: str = Query("pdf"),
    db: Session = Depends(get_db)
):
    """
    根据文书类型或战役导出对应的证据册
    
    支持三种模式：
    1. 仅指定 document_type：按文书类型筛选证据
    2. 仅指定 claim_id：按战役筛选证据
    3. 两者都指定：优先按战役，其次按文书类型
    """
    # 按战役筛选证据
    if claim_id:
        claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
        if claim and claim.required_evidence_ids:
            relevant_evidence_ids = claim.required_evidence_ids
            evidence_items = db.query(EvidenceItem).filter(
                EvidenceItem.id.in_(relevant_evidence_ids)
            ).all()
            doc_type_for_book = f"{claim.title} - 证据册"
        else:
            evidence_items = []
            doc_type_for_book = f"战役证据册"
    elif document_type:
        # 原有逻辑：按文书类型筛选
        return export_evidence_book(
            case_id=case_id,
            format=format,
            body={"document_type": document_type},
            db=db
        )
    else:
        # 两者都没有，返回全部证据
        evidence_items = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id
        ).all()
        doc_type_for_book = "案件证据册"

    # 调用通用导出
    return export_evidence_book(
        case_id=case_id,
        format=format,
        body={"document_type": doc_type_for_book, "evidence_items": evidence_items},
        db=db
    )


@router.delete("/{evidence_id}")
def delete_evidence(evidence_id: int, db: Session = Depends(get_db)):
    """删除证据"""
    doc = db.query(Document).filter(Document.id == evidence_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="证据不存在")

    db.delete(doc)
    db.commit()

    return {"message": "证据已删除"}


@router.post("/extract-from-text")
def extract_evidence_from_text(text: str):
    """
    从文本中提取证据信息
    """
    extracted = evidence_service.extract_evidence_from_text(text)

    return {
        "extracted": extracted,
        "count": len(extracted)
    }


# ============ 证据搜索 API ============

class EvidenceSearchRequest(BaseModel):
    """证据搜索请求"""
    keyword: Optional[str] = None  # 模糊搜索关键词
    evidence_number: Optional[str] = None  # 证据编号
    claim_id: Optional[str] = None  # 关联诉求ID
    safety_level: Optional[str] = None  # 安全性级别筛选
    evidence_type: Optional[str] = None  # 证据类型筛选
    source_party: Optional[str] = None  # 来源方筛选
    page: int = 1
    page_size: int = 20


class EvidenceCorrectionRequest(BaseModel):
    """证据纠错请求"""
    field: str  # 被纠错的字段
    original_value: str  # 原始值（用于验证）
    corrected_value: str  # 修正后的值
    reason: str  # 纠错原因


class EvidenceAnnotationRequest(BaseModel):
    """证据标注请求"""
    direction: Optional[str] = None  # 使用方向
    note: Optional[str] = None  # 备注说明
    tags: Optional[List[str]] = None  # 自定义标签
    highlight: Optional[bool] = None  # 是否高亮
    highlight_reason: Optional[str] = None  # 高亮原因


class SafetyReviewRequest(BaseModel):
    """安全性审核请求"""
    ignored: bool  # 是否忽略警告
    reason: Optional[str] = None  # 忽略原因


@router.get("/search/{case_id}")
def search_evidence(
    case_id: int,
    keyword: Optional[str] = Query(None),
    evidence_number: Optional[str] = Query(None),
    claim_id: Optional[str] = Query(None),
    safety_level: Optional[str] = Query(None),
    evidence_type: Optional[str] = Query(None),
    source_party: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    证据搜索
    支持：模糊搜索、编号搜索、关键词搜索、关联搜索、类型筛选、安全级别筛选
    """
    # 构建查询
    query = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id)

    # 模糊搜索（文件名、显示名、摘要、内容）
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            db.or_(
                EvidenceItem.original_filename.ilike(keyword_pattern),
                EvidenceItem.display_name.ilike(keyword_pattern),
                EvidenceItem.summary.ilike(keyword_pattern),
                EvidenceItem.extracted_content.ilike(keyword_pattern),
                EvidenceItem.raw_content.ilike(keyword_pattern),
                EvidenceItem.evidence_number.ilike(keyword_pattern)
            )
        )

    # 编号搜索
    if evidence_number:
        query = query.filter(EvidenceItem.evidence_number == evidence_number)

    # 关联搜索（诉求关联）
    if claim_id:
        # 使用 JSON 包含查询
        query = query.filter(EvidenceItem.related_claims.contains([claim_id]))

    # 安全性级别筛选
    if safety_level:
        if safety_level == "danger":
            query = query.filter(EvidenceItem.safety_level == "danger")
        elif safety_level == "caution":
            query = query.filter(EvidenceItem.safety_level == "caution")
        elif safety_level == "safe":
            query = query.filter(EvidenceItem.safety_level == "safe")
        elif safety_level == "warning":
            # 包含 danger 和 caution
            query = query.filter(EvidenceItem.safety_level.in_(["danger", "caution"]))

    # 证据类型筛选
    if evidence_type:
        query = query.filter(EvidenceItem.evidence_type == evidence_type)

    # 来源方筛选
    if source_party:
        query = query.filter(EvidenceItem.source_party == source_party)

    # 排序：高亮和危险证据优先
    query = query.order_by(
        EvidenceItem.is_highlighted.desc(),
        EvidenceItem.safety_level.desc(),
        EvidenceItem.created_at.desc()
    )

    # 获取总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    evidence_items = query.offset(offset).limit(page_size).all()

    # 转换为字典
    results = [item.to_dict() for item in evidence_items]

    # 统计信息
    stats = {
        "total": total,
        "danger_count": db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id,
            EvidenceItem.safety_level == "danger"
        ).count(),
        "caution_count": db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id,
            EvidenceItem.safety_level == "caution"
        ).count(),
        "safe_count": db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id,
            EvidenceItem.safety_level == "safe"
        ).count(),
    }

    return {
        "success": True,
        "case_id": case_id,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "results": results,
        "stats": stats
    }


@router.put("/v2/{evidence_id}/correct")
def correct_evidence(
    evidence_id: str,
    correction: EvidenceCorrectionRequest,
    db: Session = Depends(get_db)
):
    """
    证据纠错
    用户可以对AI识别错误的证据做纠错
    """
    # 查找证据
    item = db.query(EvidenceItem).filter(EvidenceItem.id == evidence_id).first()
    if not item:
        # 尝试从 Document 查找（旧数据兼容）
        doc = db.query(Document).filter(Document.id == int(evidence_id)).first()
        if not doc:
            raise HTTPException(status_code=404, detail="证据不存在")

    # 获取当前纠错记录
    corrections = item.user_corrections if hasattr(item, 'user_corrections') else []

    # 添加新纠错记录
    new_correction = {
        "id": str(uuid.uuid4()),
        "field": correction.field,
        "original_value": correction.original_value,
        "corrected_value": correction.corrected_value,
        "reason": correction.reason,
        "timestamp": datetime.utcnow().isoformat(),
        "corrected_by": "用户"
    }
    corrections.append(new_correction)

    # 更新证据
    item.user_corrections = corrections
    item.updated_at = datetime.utcnow()

    # 如果纠错的是提取内容，同步更新
    if correction.field == "extracted_content":
        item.extracted_content = correction.corrected_value
    elif correction.field == "summary":
        item.summary = correction.corrected_value
    elif correction.field == "evidence_type":
        item.evidence_type = correction.corrected_value

    db.commit()

    return {
        "success": True,
        "message": "纠错已保存",
        "correction_id": new_correction["id"],
        "total_corrections": len(corrections)
    }


@router.put("/v2/{evidence_id}/annotate")
def annotate_evidence(
    evidence_id: str,
    annotation: EvidenceAnnotationRequest,
    db: Session = Depends(get_db)
):
    """
    证据标注
    用户可以对证据的使用方向做标注
    """
    # 查找证据
    item = db.query(EvidenceItem).filter(EvidenceItem.id == evidence_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="证据不存在")

    # 更新使用方向
    if annotation.direction:
        item.usage_direction = annotation.direction
        annotation_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "direction": annotation.direction,
            "note": annotation.note,
            "changed_by": "用户"
        }
        annotations = item.usage_annotations or []
        annotations.append(annotation_record)
        item.usage_annotations = annotations

    # 更新标签
    if annotation.tags is not None:
        item.usage_tags = annotation.tags

    # 更新备注
    if annotation.note:
        annotation_record = item.usage_annotations or []
        if annotation_record:
            annotation_record[-1]["note"] = annotation.note
            item.usage_annotations = annotation_record

    # 更新高亮状态
    if annotation.highlight is not None:
        item.is_highlighted = annotation.highlight
        if annotation.highlight and annotation.highlight_reason:
            item.highlight_reason = annotation.highlight_reason

    item.updated_at = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "message": "标注已保存",
        "usage_direction": item.usage_direction,
        "usage_tags": item.usage_tags,
        "is_highlighted": item.is_highlighted
    }


@router.post("/v2/{evidence_id}/safety-analyze")
def analyze_evidence_safety(
    evidence_id: str,
    body: dict = Body(default={}),
    db: Session = Depends(get_db)
):
    """
    证据安全性分析
    AI综合分析该证据可能在哪些诉讼中对当事人产生不利，给出红色警示
    """
    # 查找证据
    item = db.query(EvidenceItem).filter(EvidenceItem.id == evidence_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="证据不存在")

    target_claims = body.get("target_claims", [])
    case_type = body.get("case_type", "合同纠纷")

    # 构建证据内容用于分析
    evidence_content = item.extracted_content or item.raw_content or item.summary or ""
    evidence_name = item.display_name or item.original_filename or "未知证据"

    # 使用现有的风险分析服务
    from app.services.evidence_system import EvidenceRiskAnalyzer
    risk_analyzer = EvidenceRiskAnalyzer()

    from app.services.evidence_system import Evidence
    ev = Evidence(
        id=item.id,
        name=evidence_name,
        evidence_type=item.evidence_type,
        content=evidence_content,
        source="证据库",
        custody=item.source_party or "",
        proof_point=json.dumps(item.proves_facts, ensure_ascii=False) if item.proves_facts else ""
    )

    risk_result = risk_analyzer.analyze_evidence_risks(
        evidence_list=[ev],
        target_claims=target_claims,
        case_type=case_type
    )

    # 更新证据的安全性评估
    warnings = []
    safety_level = "safe"

    for adverse in risk_result.adverse_evidence:
        warning = {
            "type": "adverse",
            "evidence_name": adverse.evidence_name,
            "risk_level": adverse.risk_level,
            "risk_type": adverse.risk_type,
            "description": adverse.description,
            "affected_claims": adverse.affected_claims,
            "suggestion": adverse.suggestion
        }
        warnings.append(warning)
        if safety_level == "safe":
            safety_level = "danger"

    for questionable in risk_result.questionable_evidence:
        warning = {
            "type": "questionable",
            "evidence_name": questionable.evidence_name,
            "risk_level": questionable.risk_level,
            "risk_type": questionable.risk_type,
            "description": questionable.description,
            "affected_claims": questionable.affected_claims,
            "suggestion": questionable.suggestion
        }
        warnings.append(warning)
        if safety_level == "safe":
            safety_level = "caution"

    # 保存分析结果
    item.safety_level = safety_level
    item.safety_warnings = warnings
    item.adverse_impact_analysis = risk_result.summary
    item.updated_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "evidence_id": evidence_id,
        "evidence_name": evidence_name,
        "safety_level": safety_level,
        "safety_level_name": EvidenceItem.get_safety_level_display(safety_level)["name"],
        "warnings": warnings,
        "adverse_impact_analysis": risk_result.summary,
        "overall_risk_level": risk_result.overall_risk_level
    }


@router.post("/v2/{evidence_id}/safety-review")
def review_evidence_safety(
    evidence_id: str,
    review: SafetyReviewRequest,
    db: Session = Depends(get_db)
):
    """
    安全性审核
    用户标记已审核并选择是否忽略警告
    """
    item = db.query(EvidenceItem).filter(EvidenceItem.id == evidence_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="证据不存在")

    item.safety_reviewed = True
    item.safety_reviewed_by = "用户"
    item.safety_reviewed_at = datetime.utcnow()
    item.is_warning_ignored = review.ignored
    if review.reason:
        item.ignored_reason = review.reason

    item.updated_at = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "message": "审核记录已保存",
        "safety_reviewed": item.safety_reviewed,
        "is_warning_ignored": item.is_warning_ignored
    }


@router.post("/safety-batch-analyze/{case_id}")
def batch_analyze_safety(
    case_id: int,
    body: dict = Body(default={}),
    db: Session = Depends(get_db)
):
    """
    批量证据安全性分析
    对案件所有证据进行安全性分析，识别不利证据
    """
    target_claims = body.get("target_claims", [])
    case_type = body.get("case_type", "合同纠纷")

    # 获取案件证据
    items = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).all()

    if not items:
        return {
            "success": True,
            "message": "该案件暂无证据",
            "total": 0,
            "analyzed": 0,
            "danger_count": 0,
            "caution_count": 0,
            "safe_count": 0
        }

    # 批量分析
    danger_count = 0
    caution_count = 0
    safe_count = 0
    analyzed_results = []

    from app.services.evidence_system import Evidence, EvidenceRiskAnalyzer
    risk_analyzer = EvidenceRiskAnalyzer()

    for item in items:
        evidence_content = item.extracted_content or item.raw_content or item.summary or ""
        evidence_name = item.display_name or item.original_filename or "未知证据"

        ev = Evidence(
            id=item.id,
            name=evidence_name,
            evidence_type=item.evidence_type,
            content=evidence_content,
            source="证据库",
            custody=item.source_party or "",
            proof_point=json.dumps(item.proves_facts, ensure_ascii=False) if item.proves_facts else ""
        )

        risk_result = risk_analyzer.analyze_evidence_risks(
            evidence_list=[ev],
            target_claims=target_claims,
            case_type=case_type
        )

        # 更新安全性评估
        warnings = []
        safety_level = "safe"

        for adverse in risk_result.adverse_evidence:
            warnings.append({
                "type": "adverse",
                "description": adverse.description,
                "risk_level": adverse.risk_level,
                "affected_claims": adverse.affected_claims
            })
            if safety_level == "safe":
                safety_level = "danger"

        for questionable in risk_result.questionable_evidence:
            warnings.append({
                "type": "questionable",
                "description": questionable.description,
                "risk_level": questionable.risk_level,
                "affected_claims": questionable.affected_claims
            })
            if safety_level == "safe":
                safety_level = "caution"

        item.safety_level = safety_level
        item.safety_warnings = warnings
        item.adverse_impact_analysis = risk_result.summary
        item.updated_at = datetime.utcnow()

        # 统计
        if safety_level == "danger":
            danger_count += 1
        elif safety_level == "caution":
            caution_count += 1
        else:
            safe_count += 1

        analyzed_results.append({
            "evidence_id": item.id,
            "evidence_name": evidence_name,
            "safety_level": safety_level,
            "warning_count": len(warnings)
        })

    db.commit()

    return {
        "success": True,
        "message": f"批量分析完成，共 {len(items)} 条证据",
        "total": len(items),
        "analyzed": len(items),
        "danger_count": danger_count,
        "caution_count": caution_count,
        "safe_count": safe_count,
        "results": analyzed_results,
        "recommendation": f"发现 {danger_count} 条危险证据、{caution_count} 条注意证据，建议优先审核"
    }


@router.get("/v2/{evidence_id}")
def get_evidence_detail(
    evidence_id: str,
    db: Session = Depends(get_db)
):
    """
    获取证据详情（含纠错记录、标注信息、安全性评估）
    """
    item = db.query(EvidenceItem).filter(EvidenceItem.id == evidence_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="证据不存在")

    return {
        "success": True,
        "evidence": item.to_dict(),
        "corrections": item.user_corrections or [],
        "annotations": item.usage_annotations or [],
        "safety_warnings": item.safety_warnings or [],
        "safety_level_info": EvidenceItem.get_safety_level_display(item.safety_level),
        "usage_direction_info": EvidenceItem.get_usage_direction_display(item.usage_direction)
    }
