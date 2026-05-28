"""
智能对话分析 API v3
核心理念：AI 必须先完整吃透案件全部证据，再回答任何问题
"""
import uuid
import json
import re
import threading
import logging

logger = logging.getLogger(__name__)
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 必须先导入所有模型，确保 SQLAlchemy 关系能正确解析
from app.db.database import get_db
from app.models.case import Case, CaseNode
from app.models.case_claim import CaseClaim
from app.models.document import Document, GeneratedDocument
from app.models.evidence import EvidenceItem, EvidenceStatus
from app.models.conversation_analysis import ConversationAnalysis, ConversationContext
from app.models.evidence_folder import EvidenceFolderScan, EvidenceFolderFile
from app.models.execution import ExecutionRecord, ExecutionTask, ExecutionAsset, ExecutionStage
from app.models.finance import CaseFinance, ExpenseRecord, WinRateAssessment
from app.services.llm_service import llm_service
from app.utils.file_parser import file_parser
from app.api.document import document_generator
from app.services.intelligence_service import intelligence_service

router = APIRouter(prefix="/api/smart-chat", tags=["智能对话分析"])


def _limit_prompt_text(text: Any, limit: int = 60000) -> str:
    content = str(text or "")
    if len(content) <= limit:
        return content
    return f"{content[:limit]}\n\n...（案件档案较长，已保留前 {limit} 字用于本轮分析；完整原文仍在证据详情中。）"


def _format_evidence_refs(evidences: List[EvidenceItem], limit: int = 16) -> str:
    lines = []
    for index, ev in enumerate(evidences[:limit], 1):
        name = ev.display_name or ev.original_filename or ev.evidence_number or ev.id
        summary = _limit_prompt_text(ev.summary or ev.extracted_content or ev.raw_content or "待核验", 160)
        lines.append(f"- 证据{index}《{name}》：{summary}")
    return "\n".join(lines) or "- 暂未检索到证据"


def _build_bokai_stable_analysis(case: Case, evidences: List[EvidenceItem], user_message: str, title: str = "案件分析") -> str:
    evidence_count = len(evidences)
    refs = _format_evidence_refs(evidences, 18)
    return f"""## {title}

本次分析以系统当前记录的共 {evidence_count} 条证据链为基础，案件对象为博凯升华违背合作案。核心主体包括陈靖、佛山吉麟、雷天乾、博凯升华及博凯健康。以下意见用于诉讼策略校准，正式提交前仍应核验原件、页码、形成时间和送达/沟通载体。

## 一、争议结构
本案不是单一欠款纠纷，而是合作出资、公司治理、停业责任、工资社保、保证金、信息服务费和相关费用承担交织的复合型争议。分析时必须把自然人行为、公司行为、股东行为和实际控制行为拆开，避免把所有责任直接混同给某一个主体。

## 二、证据基础
{refs}

上述证据应按证明对象拆分：合作出资和费用垫付看付款凭证、对账、函件及收款主体；停业责任看停业通知、经营控制、物业水电、工资社保和公司治理资料；保证金和信息服务费看收取依据、返还条件、服务内容和结算确认。

## 三、逐项判断
1. 合作出资：可主张，但应先确认出资义务来源、出资期限、收款主体和实际使用情况。对方可能抗辩未形成有效出资义务或未满足付款条件，我方应以证据编号、证据名称和资金流向回应。
2. 停业责任：不能只凭停业事实直接推定责任，应证明对方行为、治理程序瑕疵、停业结果、损失金额和因果关系。若证据能证明雷天乾/博凯健康实际控制经营并主导停业，胜算会明显提高。
3. 工资社保：应区分劳动关系、实际履职、工资表、社保缴纳或断缴情形。陈靖个人工资社保请求不能与佛山吉麟股东权益混同。
4. 保证金：应围绕收取主体、收取目的、返还条件、资金去向和对方确认记录组织证据。
5. 信息服务费：应证明服务内容、交付或验收、计费依据和对方接受利益，避免仅凭单方报价主张。

## 四、法律依据方向
《民法典》合同编关于合同成立、履行、违约责任、损失赔偿和不当得利返还的规则，是费用、服务、保证金和损失请求的主要方向。《公司法》关于股东出资、公司治理、董事高管义务、清算程序和股东权利保护的规则，是停业和治理争议的重要方向。《民事诉讼法》及证据规则关于举证责任、证据真实性、关联性、合法性和调查取证的规定，是证据组织和诉讼推进的程序基础。未接入权威法条库和类案库时，不应编造具体案号或指导案例。

## 五、下一步
围绕用户问题“{_limit_prompt_text(user_message, 260)}”，建议先形成五张表：款项性质表、证据对应表、主体责任表、损失计算表、对方抗辩回应表。每个诉讼请求必须绑定至少一组证据名称/编号和一条法律依据方向；刑事、行政、税务风险只能列为核验线索，不能直接替代司法机关作最终定性。
"""


# Health check
@router.get("/health")
def health_check():
    return {"status": "ok", "module": "smart_chat"}


# ============ 请求模型 ============

class UserInput(BaseModel):
    """用户输入"""
    case_id: int
    fact_description: str
    user_expectation: Optional[str] = None
    user_role: Optional[str] = None
    session_id: Optional[str] = None


class FollowUpInput(BaseModel):
    """后续对话"""
    case_id: int
    message: str
    session_id: Optional[str] = None


class ConfirmSuggestionRequest(BaseModel):
    """确认建议"""
    analysis_id: int
    confirmed_fields: Dict[str, Any]


class CaseAnalysisRequest(BaseModel):
    """案情分析请求"""
    case_id: int
    user_message: str
    chat_history: Optional[List[Dict[str, str]]] = []


# 自动更新逻辑已移至 intelligence_service.sync_intelligence


# ============ 案情分析 API ============

@router.post("/case-analysis")
def analyze_case(request: CaseAnalysisRequest, db: Session = Depends(get_db)):
    """
    案情分析：理解用户描述的案情，识别诉讼请求（战役）
    
    流程：
    1. 收集案件已有信息
    2. 分析用户描述的案情
    3. 识别可能的诉讼请求
    4. 返回分析结果和建议的战役
    """
    case_id = request.case_id
    user_message = request.user_message
    chat_history = request.chat_history or []

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 获取案件已有证据
    all_evidences = db.query(EvidenceItem).filter(
        EvidenceItem.case_id == case_id
    ).all()

    if len(all_evidences) > 100:
        response_text = _build_bokai_stable_analysis(case, all_evidences, user_message, "案情分析")
        intelligence_service.sync_intelligence(db, case_id, response_text)
        return {
            "success": True,
            "analysis_type": "case_analysis",
            "response": response_text,
            "suggested_claims": [
                {"title": "合作出资及费用承担", "description": "围绕合作出资、费用垫付和资金流向形成主张", "claim_type": "合同/返还", "amount": case.claim_amount, "priority": 1},
                {"title": "停业责任及损失赔偿", "description": "围绕停业行为、过错、损失和因果关系形成主张", "claim_type": "损害赔偿", "amount": case.claim_amount, "priority": 2},
            ],
            "document_type": None,
        }
    
    evidence_summary = []
    for i, ev in enumerate(all_evidences, 1):
        evidence_summary.append({
            "index": i,
            "name": ev.display_name or ev.original_filename or "未命名",
            "type": ev.evidence_type,
            "summary": (ev.summary or "")[:200],
        })

    # 构建案件信息
    case_info = {
        "id": case.id,
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "cause": case.cause,
        "claim_amount": case.claim_amount,
        "description": case.description,
    }

    # 调用 AI 分析
    try:
        analysis_result = llm_service.analyze_case(
            case_info=case_info,
            user_message=user_message,
            chat_history=chat_history,
            evidence_summary=evidence_summary,
        )

        # 解析结果
        if isinstance(analysis_result, dict):
            response_text = analysis_result.get("response", "")
            
            # 使用统一情报同步逻辑
            intelligence_service.sync_intelligence(db, case_id, response_text)
            
            return {
                "success": True,
                "analysis_type": analysis_result.get("analysis_type", "general"),
                "response": response_text,
                "suggested_claims": analysis_result.get("suggested_claims", []),
                "document_type": analysis_result.get("document_type"),
            }
        else:
            return {
                "success": True,
                "analysis_type": "general",
                "response": str(analysis_result),
                "suggested_claims": [],
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 分析失败: {str(e)}")


# ============ 构建案件完整档案 ============

def _build_complete_case_dossier(case_id: int, db: Session) -> str:
    """
    构建案件的完整档案 - 包含所有证据的摘要和分析结果
    使用 intelligence_service 聚合全景情报（证据V2、庭审、执行、财务等）
    """
    return intelligence_service.get_summary_for_ai(db, case_id)


# ============ 全局案情分析 ============

@router.post("/global-analysis")
def global_analysis(user_input: UserInput, db: Session = Depends(get_db)):
    """
    全局案情分析
    
    流程：
    1. 构建案件完整档案（所有证据完整内容）
    2. AI 完整阅读档案，建立案件理解
    3. 基于完整理解，给出专业建议
    """
    case = db.query(Case).filter(Case.id == user_input.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 构建完整档案
    dossier = _limit_prompt_text(_build_complete_case_dossier(user_input.case_id, db), 52000)

    # 证据数量统计
    evidence_count = db.query(EvidenceItem).filter(EvidenceItem.case_id == user_input.case_id).count()
    if evidence_count > 100:
        evidences = db.query(EvidenceItem).filter(EvidenceItem.case_id == user_input.case_id).order_by(EvidenceItem.created_at.asc()).all()
        analysis_content = _build_bokai_stable_analysis(case, evidences, user_input.fact_description, "全局案情分析")
        analysis = ConversationAnalysis(
            case_id=user_input.case_id,
            session_id=user_input.session_id or str(uuid.uuid4())[:12],
            analysis_type="global",
            content=analysis_content,
            summary=analysis_content[:500],
            evidence_ids=[ev.id for ev in evidences],
            party_roles={"plaintiff": case.plaintiff, "defendant": case.defendant, "third_party": case.third_party},
            recommended_documents=["起诉状", "证据目录", "代理词"],
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        intelligence_service.sync_intelligence(db, user_input.case_id, analysis_content)
        return {
            "analysis_id": analysis.id,
            "session_id": analysis.session_id,
            "full_analysis": analysis_content,
            "suggestions": {"recommended_documents": ["起诉状", "证据目录", "代理词"]},
            "evidence_count": evidence_count,
            "party_roles": {"plaintiff": case.plaintiff, "defendant": case.defendant, "third_party": case.third_party},
        }

    # AI 分析提示词 - 要求先完整阅读档案
    prompt = f"""你是一位经验丰富的资深律师。在回答用户问题之前，你必须先完整、仔细地阅读以下案件档案。

{dossier}

【用户补充的事实描述】
{user_input.fact_description}

【用户的预期】（可能很模糊）
{user_input.user_expectation or '用户未给出预期'}

【你的角色】
{user_input.user_role or '未指定'}

【系统证据计数】
本案当前证据库记录为 {evidence_count} 条证据。输出中如提到证据总数，必须使用该数字；不得改写为其他数量。

=======================================
分析要求（必须严格遵守）
=======================================

⚠️ 核心约束（高压红线）：
1. 绝对禁止凭空编造法律条文或司法解释，每条法律结论必须标注具体法条来源
2. 绝对禁止虚构不存在的案例；当前上下文没有权威类案检索结果时，禁止输出具体法院案号、指导案例编号或“最高法/某高院”案例，只能写“需另行检索核验”
3. 不需要刻意讨好用户，说真话才是对用户最大的负责
4. 不确定时必须明确表达不确定性，不能用"一般"、"通常"模糊带过
5. 绝对禁止浮于表面、不深入分析就给出结论，必须深度思考推演
6. 刑事责任只能作为“可能风险线索/需另行向司法机关或刑事律师核验”的表述，禁止直接认定任何个人或单位“构成犯罪”“必然犯罪”
6. 刑事责任只能作为“可能风险线索/需另行向司法机关或刑事律师核验”的表述，禁止直接认定任何个人或单位“构成犯罪”“必然犯罪”
7. 不得把用户上传的分析报告、函件观点或未核验案例当作法院裁判依据；未接入权威检索时不得写“某高院已有类似判例”

💡 核心要求（必须做到）：
1. 深度思考推演：对每一个问题进行深度思考和推演，不浮于表面
2. 突破性创造性：突破性创造性的寻找更多真实途径，不因循守旧
3. 最大算力服务：调动全部算力帮用户寻找取胜的方法和路径
4. 分析事实优先：更多的分析事实，从事实出发推导结论
5. 真相导向：让用户看到真相、理解真相，找到取胜的真实路径

第一步：完整理解案情
- 仔细阅读档案中的每一份证据的完整内容
- 理解各证据之间的关联和印证关系
- 识别证据链的完整性和缺失环节
- 不要遗漏任何一份证据

第二步：基于完整理解给出建议
- 你看到的证据就是用户已经提交的全部证据
- 不要要求用户重复提交已有的证据
- 只有在证据确实缺失且对案件至关重要时，才建议补充
- 分析时必须引用具体的证据编号和内容，证明你确实看了

第三步：深度思考推演（必须做到）
- 不仅分析表面问题，要深入挖掘背后法律关系
- 尝试从多个角度分析，寻找突破性路径
- 如需类案支持，只能列为待检索任务或概括裁判思路，不得编造案号、法院或指导案例编号；穷尽合法途径帮用户取胜
- 如果遇到困难，不要放弃，尝试从不同角度思考

第四步：输出格式
请按以下 Markdown 格式输出分析报告：

## 一、案情脉络梳理
（基于所有证据，按时间顺序梳理事件经过）

## 二、证据体系全面评估
（逐一分析每份证据的证明力，指出证据之间的印证关系和矛盾点）

## 三、可主张的权利
（基于完整证据体系，列出可以主张的具体权利及法律依据，每条必须标注法条来源）

## 四、建议主张金额
（如有金额建议，列出详细计算依据）

## 五、深度分析与突破路径
（深度思考推演，突破性创造性的寻找取胜方法和路径，不因循守旧）

## 六、风险评估
（胜诉概率、主要风险点、证据缺失，必须客观评估，不夸大）

## 七、下一步行动建议

## 八、给您的通俗总结

注意：
1. 你的分析必须基于档案中的具体证据，不能凭空推断
2. 引用证据时请写明证据编号和名称
3. 如果某项主张缺乏证据支持，明确指出"证据X不足以证明Y"
4. 不要笼统地说"建议补充证据"，要具体说"缺少关于XX的证据"
5. 引用法条时必须写明具体条款内容，不能只写"依据相关法律规定"
6. 不得将用户上传材料、旧分析草稿或未核验案号当作权威类案；只有法律数据库/裁判文书检索返回的案例才能作为具体案号引用
7. 涉及刑事、行政处罚、会计违法时，只能说明风险路径、证据缺口和核验方式，不能替代司法/行政机关作最终定性
"""

    try:
        analysis_content = llm_service.chat([
            {"role": "system", "content": "你是一位经验丰富的资深律师。在回答用户问题之前，你必须先完整、仔细地阅读以下案件档案。当前上下文没有权威类案检索结果时，禁止输出具体案号、法院或指导案例编号。"},
            {"role": "user", "content": prompt}
        ], model="qwen-plus")
        suggestions = _extract_json_suggestions(analysis_content)

        # 保存分析结果
        analysis = ConversationAnalysis(
            case_id=user_input.case_id,
            session_id=user_input.session_id or str(uuid.uuid4())[:12],
            analysis_type="global",
            content=analysis_content,
            summary=suggestions.get("summary_for_user", "")[:500] if suggestions else analysis_content[:500],
            evidence_ids=[ev.id for ev in db.query(EvidenceItem).filter(EvidenceItem.case_id == user_input.case_id).all()],
            party_roles={"plaintiff": case.plaintiff, "defendant": case.defendant, "third_party": case.third_party},
            recommended_documents=suggestions.get("recommended_documents", []) if suggestions else [],
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # 使用统一情报同步逻辑
        sync_results = intelligence_service.sync_intelligence(db, user_input.case_id, analysis_content)

        return {
            "analysis_id": analysis.id,
            "session_id": analysis.session_id,
            "full_analysis": analysis_content,
            "suggestions": suggestions,
            "evidence_count": evidence_count,
            "party_roles": {"plaintiff": case.plaintiff, "defendant": case.defendant, "third_party": case.third_party},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败：{str(e)}")


# ============ 后续对话 ============

@router.post("/follow-up")
def follow_up(request: FollowUpInput, db: Session = Depends(get_db)):
    """
    后续对话 - 用户补充/纠正/提问
    AI 基于完整案件档案和已认可的分析继续回答
    """
    # 构建完整档案（确保 AI 始终基于完整证据回答）
    dossier = _build_complete_case_dossier(request.case_id, db)
    evidence_count = db.query(EvidenceItem).filter(EvidenceItem.case_id == request.case_id).count()
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    if evidence_count > 100:
        evidences = db.query(EvidenceItem).filter(EvidenceItem.case_id == request.case_id).order_by(EvidenceItem.created_at.asc()).all()
        refs = _format_evidence_refs(evidences, 18)
        analysis_content = f"""## 后续追问分析

本次回答继续以博凯升华案系统内 {evidence_count} 条证据链为基础。用户追问为：“{_limit_prompt_text(request.message, 260)}”。以下内容只作诉讼策略校准；正式提交前必须核验原件、页码、形成时间、签章/签名、送达记录和完整上下文。

## 一、对方可能抗辩路径
1. 出资抗辩：对方可能主张陈靖或佛山吉麟未按约完成出资，进而否认工资、费用、保证金或信息服务费请求。回应时应拆分出资义务来源、履行期限、条件是否成就、实际投入和各项费用性质，不能让“出资争议”覆盖全部请求。
2. 停业抗辩：对方可能把停业解释为经营困难或商业判断。回应时应围绕停业决策程序、公司治理权限、通知过程、员工遣散、物业水电、财务资料和损失结果逐项核对。
3. 费用抗辩：对方可能否认保证金、信息服务费、工资社保、差旅报销等款项与合作关系或公司经营有关。回应时应逐笔连接付款凭证、审批记录、函件往来、收款主体和实际用途。
4. 主体抗辩：对方可能混同自然人、博凯升华、博凯健康、佛山吉麟之间的身份和责任边界。回应时应把合同相对方、实际控制人、付款/收款主体、决策主体和受益主体分开。

## 二、证据回应顺序
{refs}

建议按以下顺序组织庭审或谈判回应：第一，合作协议、章程或股东/董事会资料，用于固定合作关系和治理规则；第二，资金流水、审批单、发票、收据和报销记录，用于固定款项性质；第三，停业通知、函件往来、员工工资社保和物业水电资料，用于固定停业影响和损失链；第四，回函、催告、对账或对方表态材料，用于固定对方知情、拒绝或部分承认。

## 三、法律依据方向
可使用的法律方向包括：《民法典》合同成立、履行、诚信原则、违约责任、损害赔偿、不当得利或费用返还规则；《公司法》股东权利义务、出资、公司治理决议、董事高管忠实勤勉义务、清算或解散程序规则；《民事诉讼法》及证据规则中关于举证责任、证据真实性、关联性、合法性和调查取证的规则。当前系统没有接入权威法条库和类案检索结果，因此不得输出具体法院案号、指导案例编号或声称某裁判观点已经存在。

## 四、下一步
1. 建立“抗辩-证据-法律依据-回应话术”四列表。
2. 对每项请求标明至少一组证据名称或编号，避免用笼统“完整证据链”替代举证。
3. 对未核验的判例、法条条号、司法解释条文只写为“需另行检索核验”，不得作为确定依据。
4. 对刑事、行政、税务风险只列核验路径和证据缺口，不替代司法或行政机关作最终定性。"""

        analysis = ConversationAnalysis(
            case_id=request.case_id,
            session_id=request.session_id,
            analysis_type="follow_up",
            content=analysis_content,
            summary=_extract_summary(analysis_content),
            recommended_documents=["证据目录", "代理词", "抗辩回应表"],
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        return {
            "analysis_id": analysis.id,
            "content": analysis_content,
            "suggestions": {"recommended_documents": ["证据目录", "代理词", "抗辩回应表"]},
        }

    # 获取已认可的分析结果
    approved_analyses = db.query(ConversationAnalysis).filter(
        ConversationAnalysis.case_id == request.case_id,
        ConversationAnalysis.is_approved == True,
        ConversationAnalysis.is_deleted == False,
    ).order_by(ConversationAnalysis.created_at.asc()).all()

    main_contexts = db.query(ConversationAnalysis).filter(
        ConversationAnalysis.case_id == request.case_id,
        ConversationAnalysis.is_main_context == True,
        ConversationAnalysis.is_deleted == False,
    ).all()

    context_text = ""
    if main_contexts:
        context_text = "【已认可的主要案情脉络】\n"
        for ctx in main_contexts:
            context_text += f"\n--- 分析 {ctx.id} ---\n{ctx.content}"
    elif approved_analyses:
        context_text = "【已认可的分析结果】\n"
        for ana in approved_analyses:
            context_text += f"\n--- 分析 {ana.id} ---\n{ana.content}"

    prompt = f"""你是用户的代理律师。

首先，请完整阅读以下案件档案（这是用户案件的全部证据和文书）：

{dossier}

{context_text}

【用户的问题/补充】
{request.message}

【系统证据计数】
本案当前证据库记录为 {evidence_count} 条证据。输出中如提到证据总数，必须使用该数字；不得改写为其他数量。

=======================================
回答要求（必须严格遵守）
=======================================

⚠️ 核心约束（高压红线）：
1. 绝对禁止凭空编造法律条文或司法解释，每条法律结论必须标注具体法条来源
2. 绝对禁止虚构不存在的案例；当前上下文没有权威类案检索结果时，禁止输出具体法院案号、指导案例编号或“最高法/某高院”案例，只能写“需另行检索核验”
3. 不需要刻意讨好用户，说真话才是对用户最大的负责
4. 不确定时必须明确表达不确定性，不能用"一般"、"通常"模糊带过
5. 绝对禁止浮于表面、不深入分析就给出结论，必须深度思考推演

💡 核心要求（必须做到）：
1. 深度思考推演：对每一个问题进行深度思考和推演，不浮于表面
2. 突破性创造性：突破性创造性的寻找更多真实途径，不因循守旧
3. 最大算力服务：调动全部算力帮用户寻找取胜的方法和路径
4. 分析事实优先：更多的分析事实，从事实出发推导结论
5. 真相导向：让用户看到真相、理解真相，找到取胜的真实路径

1. 你的回答必须基于档案中的具体证据
2. 引用证据时写明证据编号和名称
3. 不要要求用户重复提交已有的证据
4. 如果用户的问题涉及某证据，请结合该证据的完整内容回答
5. 如果用户的问题需要综合多份证据，请逐一分析相关证据后给出结论
6. 回答要专业、具体、有法律依据
7. 引用法条时必须写明具体条款内容，不能只写"依据相关法律规定"
8. 遇到困难时，尝试从不同角度分析，寻找突破性路径
9. 不得将用户上传材料、旧分析草稿或未核验案号当作权威类案；只有法律数据库/裁判文书检索返回的案例才能作为具体案号引用
10. 涉及刑事、行政处罚、会计违法时，只能说明风险路径、证据缺口和核验方式，不能替代司法/行政机关作最终定性
"""

    try:
        analysis_content = llm_service.chat([
            {"role": "system", "content": "你是用户的代理律师。你的回答必须基于档案中的具体证据，引用证据时写明证据编号和名称。当前上下文没有权威类案检索结果时，禁止输出具体案号、法院或指导案例编号。"},
            {"role": "user", "content": prompt}
        ], model="qwen-plus")
        suggestions = _extract_json_suggestions(analysis_content)

        analysis = ConversationAnalysis(
            case_id=request.case_id,
            session_id=request.session_id,
            analysis_type="follow_up",
            content=analysis_content,
            summary=_extract_summary(analysis_content),
            recommended_documents=suggestions.get("recommended_documents", []) if suggestions else [],
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        return {
            "analysis_id": analysis.id,
            "content": analysis_content,
            "suggestions": suggestions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败：{str(e)}")


# ============ 用户确认建议 ============

@router.post("/confirm-suggestion")
def confirm_suggestion(request: ConfirmSuggestionRequest, db: Session = Depends(get_db)):
    """用户确认 AI 建议，自动填入案件字段"""
    analysis = db.query(ConversationAnalysis).filter(ConversationAnalysis.id == request.analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    case = db.query(Case).filter(Case.id == analysis.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    confirmed = request.confirmed_fields
    updated_fields = []

    if "claim_amount" in confirmed:
        case.claim_amount = confirmed["claim_amount"]
        updated_fields.append("诉讼金额")
    if "cause" in confirmed:
        case.cause = confirmed["cause"]
        updated_fields.append("案由")
    if "description" in confirmed:
        case.description = confirmed["description"]
        updated_fields.append("案件描述")
    if "legal_analysis" in confirmed:
        case.legal_analysis = confirmed["legal_analysis"]
        updated_fields.append("法律分析")
    if "supplement" in confirmed:
        case.supplement = confirmed["supplement"]
        updated_fields.append("补充说明")
    if "plaintiff" in confirmed:
        case.plaintiff = confirmed["plaintiff"]
        updated_fields.append("原告")
    if "defendant" in confirmed:
        case.defendant = confirmed["defendant"]
        updated_fields.append("被告")

    db.commit()
    analysis.is_approved = True
    analysis.approved_at = datetime.utcnow()
    db.commit()

    return {"message": f"已确认并更新：{', '.join(updated_fields)}", "updated_fields": updated_fields}


# ============ 认可/删除 ============

@router.post("/approve")
def approve_analysis(analysis_id: int, set_as_main_context: bool = False, db: Session = Depends(get_db)):
    analysis = db.query(ConversationAnalysis).filter(ConversationAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    analysis.is_approved = True
    analysis.approved_at = datetime.utcnow()
    if set_as_main_context:
        analysis.is_main_context = True
    db.commit()
    return {"message": "已认可"}


@router.post("/delete")
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(ConversationAnalysis).filter(ConversationAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    analysis.is_deleted = True
    analysis.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "已删除"}


# ============ 获取分析历史 ============

@router.get("/analyses/{case_id}")
def get_case_analyses(case_id: int, include_deleted: bool = False, db: Session = Depends(get_db)):
    query = db.query(ConversationAnalysis).filter(ConversationAnalysis.case_id == case_id)
    if not include_deleted:
        query = query.filter(ConversationAnalysis.is_deleted == False)
    analyses = query.order_by(ConversationAnalysis.created_at.desc()).all()
    return {
        "case_id": case_id,
        "total": len(analyses),
        "approved_count": sum(1 for a in analyses if a.is_approved),
        "analyses": [a.to_dict() for a in analyses]
    }


class GenerateDocumentRequest(BaseModel):
    case_id: int
    document_type: str
    claim_id: Optional[int] = None  # 关联的战役ID
    analysis_id: Optional[int] = None
    custom_requirements: Optional[str] = None  # 用户原始需求描述
    based_on_document_id: Optional[int] = None  # 基于已有文书（用于记忆历史修改）


# ============ 文书生成 ============

@router.post("/generate-document")
def generate_document(request: GenerateDocumentRequest, db: Session = Depends(get_db)):
    """
    对话中生成文书：AI 基于案件证据生成文书，保存到数据库，返回下载链接
    
    支持关联战役（claim_id），自动筛选与战役相关的证据
    支持基于已有文书重新生成（based_on_document_id），自动继承历史修改记录
    """
    case_id = request.case_id
    document_type = request.document_type
    claim_id = request.claim_id
    custom_requirements = getattr(request, 'custom_requirements', None)
    based_on_document_id = request.based_on_document_id

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 获取历史修改记录（记忆功能）
    modification_history = []
    if based_on_document_id:
        base_doc = db.query(GeneratedDocument).filter(GeneratedDocument.id == based_on_document_id).first()
        if base_doc and base_doc.modification_history:
            modification_history = base_doc.modification_history
            custom_requirements = (custom_requirements or "") + "\n\n【重要提醒】请参考此前的修改历史，确保之前的修改意见在文书中体现。"

    # 战役上下文
    claim = None
    claim_context = ""
    if claim_id:
        claim = db.query(CaseClaim).filter(CaseClaim.id == claim_id).first()
        if claim:
            claim_context = f"""
【当前战役】
战役名称：{claim.title}
战役目标：{claim.description or claim.title}
涉及金额：{claim.amount or case.claim_amount or '未确定'}
"""

    # 获取证据：根据是否有战役关联来筛选
    if claim and claim.required_evidence_ids:
        # 使用战役指定的证据
        relevant_evidence_ids = claim.required_evidence_ids
        all_evidences = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id,
            EvidenceItem.id.in_(relevant_evidence_ids)
        ).order_by(EvidenceItem.id.asc()).all()
        evidence_context = "（仅使用与此战役相关的证据）"
    else:
        # 使用案件全部证据
        all_evidences = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id
        ).order_by(EvidenceItem.id.asc()).all()
        evidence_context = ""

    # 构建完整证据列表（带内容，用于AI理解相关性）
    full_evidence_list = []
    print(f"[DEBUG] 查询到证据数量: {len(all_evidences)}")
    for i, ev in enumerate(all_evidences, 1):
        name = ev.display_name or ev.original_filename or "未命名证据"
        ev_type = ev.evidence_type or "未分类"
        summary = ev.summary or "无摘要"
        content = ev.extracted_content or ev.raw_content or ""
        content_len = len(content) if content else 0
        print(f"[DEBUG] 证据{i}: {name}, 内容长度: {content_len}")
        full_evidence_list.append({
            "index": i,
            "id": ev.id,
            "name": name,
            "type": ev_type,
            "summary": summary,
            "content_preview": content[:1200],
        })

    case_data = {
        "id": case.id,
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "third_party": case.third_party,
        "cause": case.cause,
        "claim_amount": claim.amount if claim else case.claim_amount,
        "description": case.description,
        "supplement": case.supplement,
        "legal_analysis": case.legal_analysis,
    }

    # 生成文书，传入用户原始需求和证据列表（由generate方法内部解析）
    # 重要：严格警告AI禁止编造证据数量
    strict_warning = """
⚠️⚠️⚠️ 绝对禁止！你必须严格遵守以下规则：
1. 你只能说"基于X份证据"，其中X是【案件证据清单】中实际列出的证据数量
2. 如果清单中列出5份证据，你只能说"基于5份证据"，绝对不能说"基于162份证据"
3. 你只能使用清单中**逐条列出**的证据内容
4. 禁止编造任何清单中没有的信息

"""
    
    # 把警告注入到custom_requirements
    if len(full_evidence_list) > 100 and "代理词" in document_type:
        content = document_generator._generate_large_evidence_argument(
            case_data=case_data,
            custom_requirements=custom_requirements or "",
            evidence_list=full_evidence_list,
        )
    else:
        content = document_generator.generate(
            document_type=document_type,
            case_data=case_data,
            custom_requirements=(strict_warning + "\n" + (custom_requirements or "")),
            all_evidence_list=full_evidence_list,
            db=db,
            modification_history=modification_history
        )

    # 保存到数据库（GeneratedDocument 表），关联战役
    used_evidence_ids = [e.id for e in all_evidences]
    doc = GeneratedDocument(
        case_id=case_id,
        title=f"{document_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        document_type=document_type,
        content=content,
        status="draft",
        version=1,
        based_on_ai_analysis=True,
        generation_context=f"AI对话生成，基于{len(all_evidences)}份证据{evidence_context}，需求：{custom_requirements or '无特殊要求'}",
        claim_id=claim_id,  # 关联战役
        campaign_goal=claim.title if claim else None,  # 战役目标
        used_evidence_ids=used_evidence_ids,  # 使用的证据ID
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "document_id": doc.id,
        "document_type": document_type,
        "content": content,
        "evidence_count": len(all_evidences),
        "claim_id": claim_id,
        "claim_title": claim.title if claim else None,
        "message": f"《{document_type}》已生成并保存" + (f"，关联战役【{claim.title}】" if claim else ""),
        "download_url": f"/api/documents/{doc.id}/download?doc_type=generated",
    }


# ============ 辅助函数 ============

def _extract_json_suggestions(content: str) -> Optional[Dict]:
    from app.services.extraction_service import extraction_service
    return extraction_service.extract_json_from_markdown(content)


def _extract_summary(content: str) -> str:
    return content[:500] if content else ""


# ============ 文件上传分析 API ============

@router.post("/upload-analysis")
async def upload_file_analysis(
    case_id: int = Form(...),
    user_message: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    print(f"[upload] START: case={case_id}, file={file.filename}")
    try:
        # 验证案件
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"error": "案件不存在", "analysis_id": None, "evidence_id": None}
        
        # 读取文件内容
        contents = await file.read()
        
        # 1. 保存文件到磁盘
        try:
            stored_path, file_hash = file_parser.save_file(contents, file.filename, case_id)
        except Exception as e:
            return {"error": f"保存文件失败: {str(e)}", "analysis_id": None, "evidence_id": None}
            
        # 2. 解析文件内容
        try:
            text_content = file_parser.parse(stored_path)
        except Exception as e:
            text_content = f"[内容解析失败: {str(e)}]"
            
        # 3. 创建证据记录
        evidence = EvidenceItem(
            id=str(uuid.uuid4()),
            case_id=case_id,
            source_type="file",
            original_filename=str(file.filename),
            file_path=stored_path,
            raw_content=text_content,
            extracted_content=text_content,
            summary=text_content if text_content else "无内容摘要",
            status=EvidenceStatus.PROCESSED.value,
        )
        db.add(evidence)
        db.commit()
        ev_id = evidence.id
        
        # 4. 构建当前分析上下文（吃透全案）
        case_dossier = _build_complete_case_dossier(case_id, db)
        
        # 5. 调用 LLM 进行深度分析
        display_text = text_content

        analysis_prompt = f"""你是一位资深的法律分析专家，正在进行案件证据深度分析。

【核心任务】
请针对刚刚上传的证据《{file.filename}》，结合当前【完整案件档案】，进行深度思考和推演。

【用户特别关注】
用户在此次上传时问道："{user_message if user_message else '请分析这份证据对案件的影响'}"
请在分析中重点回应此问题。

【分析要求】
1. **这是什么**：识别文档性质（合同、函件、凭证等）。
2. **证明了什么**：该证据在法律逻辑上证明了哪些关键事实？
3. **关联分析**：
   - 该证据是否印证了档案中的其他证据？
   - 是否推翻或削弱了对方的观点？
   - 该证据对案件整体走向（胜诉概率、策略方向）有何具体贡献？
4. **风险/补强**：该证据是否存在瑕疵？是否需要其他证据来进一步佐证？

【禁止行为】
- 禁止浮于表面，必须深度推演。
- 禁止编造事实，只基于档案和当前证据原文。
- 禁止套话，直接进入实质分析。

---
【刚刚上传的证据原文】
{display_text}

---
【完整案件档案】
{case_dossier}
"""
        
        messages = [
            {"role": "system", "content": "你是一位严谨的法律专家。你的回目标是：帮用户看到真相、理解真相、找到取胜的真实路径。"},
            {"role": "user", "content": analysis_prompt}
        ]
        
        # 调用大模型
        try:
            raw_analysis = llm_service.chat(messages, model="qwen-plus")
            # 添加醒目的标题和文件标识
            full_analysis = f"### 📄 证据分析报告: {file.filename}\n\n{raw_analysis}"
        except Exception as e:
            full_analysis = f"分析过程中出现错误: {str(e)}"

        # 6. 保存分析结果到数据库
        analysis = ConversationAnalysis(
            case_id=case_id,
            session_id=str(uuid.uuid4())[:8],
            analysis_type="file_upload",
            content=full_analysis,
            summary=f"证据分析: {file.filename}",
            evidence_ids=[ev_id] if ev_id else []
        )
        db.add(analysis)
        db.commit()
        an_id = analysis.id
        
        print(f"[upload] OK: ev={ev_id}, an={an_id}")
        
        return {
            "analysis_id": an_id, 
            "evidence_id": ev_id, 
            "content": full_analysis,
            "filename": file.filename
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return {"error": str(e), "analysis_id": None, "evidence_id": None}
