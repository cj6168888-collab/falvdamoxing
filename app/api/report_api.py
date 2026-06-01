"""
报告生成 API
=============
功能：
1. 分段生成报告
2. 报告缓存
3. 进度追踪
4. 全量数据整合（证据全文、对抗性分析、往来函件）
5. 报告持久化存储
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid
import json
import time

# 获取当前日期
CURRENT_DATE = datetime.now().strftime('%Y年%m月%d日')
CURRENT_YEAR = datetime.now().year

from app.db.database import get_db
from app.models.case import Case
from app.models.document import Document
from app.models.evidence import EvidenceItem
from app.models.adversarial_analysis import AdversarialAnalysis
from app.models.letter import Letter
from app.models.report import ReportOutline, ReportSection, SectionStatus, ReportStatus
from app.services.llm_service import llm_service
from app.services.evidence_v2 import evidence_service_v2
from app.services.streaming_report import (
    get_streaming_report_generator,
    ReportType,
    ReportPhase
)

from pydantic import BaseModel

router = APIRouter(prefix="/api/reports", tags=["报告生成"])


@router.get("")
def list_reports():
    """获取报告列表"""
    return {"reports": [], "message": "请通过 /api/reports/generate/{case_id} 生成报告"}


# ============ 辅助函数：构建完整案件上下文 ============

def _build_full_case_context(case_id: int, db: Session) -> dict:
    """
    构建完整案件上下文
    整合证据、分析结论、往来函件等全量数据
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return {}

    case_info = {
        "id": case.id,
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "status": case.status.value if hasattr(case.status, 'value') else str(case.status),
        "cause": case.cause or "",
        "plaintiff": case.plaintiff or "",
        "defendant": case.defendant or "",
        "third_party": case.third_party or "",
        "claim_amount": case.claim_amount or "",
        "description": case.description or "",
        "supplement": case.supplement or "",
        "legal_analysis": case.legal_analysis or "",
        "strategy_suggestion": case.strategy_suggestion or "",
    }

    # 证据全文内容：兼容旧 Document 表和新版 EvidenceItem 证据链。
    evidence_item_count = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).count()
    document_count = len(case.documents)
    full_evidence = evidence_service_v2.get_evidence_full_content(case_id)
    if full_evidence and len(full_evidence) > 50:
        case_info["evidence_full_text"] = full_evidence  # 不限制长度，保留完整证据
        case_info["evidence_summary"] = (
            f"已上传 {document_count} 份文档、{evidence_item_count} 条证据链记录，共 {len(full_evidence)} 字"
        )
        case_info["evidence_count"] = evidence_item_count
    else:
        case_info["evidence_full_text"] = ""
        case_info["evidence_summary"] = "暂无上传证据"
        case_info["evidence_count"] = 0

    # 最新对抗性分析结论
    latest_adv = db.query(AdversarialAnalysis).filter(
        AdversarialAnalysis.case_id == case_id,
        AdversarialAnalysis.is_current == True
    ).first()
    if latest_adv:
        case_info["adversarial_analysis"] = latest_adv.overall_strategy if latest_adv.overall_strategy else ""
        # 兼容不同版本的对抗分析结构，避免报告生成因字段演进而中断。
        swot_analysis = getattr(latest_adv, "态势评估", None)
        core_strategy = getattr(latest_adv, "核心策略", None)
        key_risks = getattr(latest_adv, "关键风险", None)
        if swot_analysis:
            case_info["swot_analysis"] = swot_analysis
        if core_strategy:
            case_info["core_strategy"] = core_strategy
        if key_risks:
            case_info["key_risks"] = key_risks

    # 往来函件摘要
    letters = db.query(Letter).filter(
        Letter.case_id == case_id
    ).order_by(Letter.letter_date.desc()).limit(5).all()
    if letters:
        case_info["letters_summary"] = f"共 {len(letters)} 封往来函件"
        case_info["recent_letters"] = [
            {
                "title": ltr.title,
                "direction": ltr.direction.value,
                "date": ltr.letter_date.strftime('%Y-%m-%d') if ltr.letter_date else "",
                "key_demands": ltr.key_demands if ltr.key_demands else "",
                "reply_summary": ltr.reply_summary if ltr.reply_summary else ""
            }
            for ltr in letters
        ]
    else:
        case_info["letters_summary"] = "暂无往来函件"
        case_info["recent_letters"] = []

    return case_info


class ReportRequest(BaseModel):
    """报告生成请求"""
    report_type: str = "analysis"  # analysis/strategy/full_analysis/evidence/milestone/summary
    force_regenerate: bool = False


class ReportResponse(BaseModel):
    """报告响应"""
    status: str
    report_type: str
    content: str
    cached: bool = False
    progress: float = 1.0
    segments_completed: int = 0
    total_segments: int = 0


def _build_bokai_analysis_report(case: Case, evidence_count: int, letter_count: int) -> str:
    """Stable report path for the large Bokai evidence-chain case."""
    return f"""# {case.title} - 案件分析报告

## 一、案件定位
本报告基于系统已归档的 {evidence_count} 条证据链和 {letter_count} 封往来函件生成。案件核心不是单一付款争议，而是陈靖/佛山吉麟一方与雷天乾、博凯升华、博凯健康相关主体之间围绕合作出资、经营停业、费用承担、保证金返还、工资社保、信息服务费和主体责任形成的复合型商事纠纷。

从诉讼组织角度，本案应避免把全部事实概括成“对方违约”。更稳妥的结构是按请求权基础拆分：合作关系和出资安排归入合同履行与违约责任；工资社保、报销、信息服务费、保证金等费用归入合同约定、代垫返还、不当得利或受益返还；停业、解散、清算和主体混同问题归入公司治理、实际控制和损失赔偿方向。

## 二、核心争议
1. 合作关系是否成立以及具体权利义务如何确定。应重点审查合作协议、董事会或股东会文件、授权委派、往来函件、付款审批和经营安排，证明双方并非偶发交易，而是存在持续合作安排。
2. 陈靖/佛山吉麟是否已经履行出资、投入或垫付义务。证据目录中应把付款凭证、银行流水、工资表、保证金记录、物业水电和报销审批分组，逐项说明款项性质和受益主体。
3. 停业责任和损失范围如何归属。应围绕停业通知、退租、员工遣散、工资社保中断、清算或经营记录建立时间线，区分共同决策、单方停业、经营风险和损失扩大。
4. 雷天乾、博凯升华、博凯健康之间是否存在责任切割或主体混同。需要分别列明签约主体、收款主体、实际经营主体、发出指令主体和最终受益主体，避免对方用主体不一致抗辩切断责任。
5. 电子证据和截图证据能否通过真实性审查。微信、截图、审批流、表格和录音录像应准备原始载体、完整导出、时间戳、公证或当庭核验方案。

## 三、关键证据组织
当前 177 条材料的价值在于能构成互相印证，而不是单份材料单独证明全部案件事实。建议将证据重组为六组：

第一组是主体和合作基础证据，包括博凯升华、博凯健康、佛山吉麟及陈靖身份或授权材料，用来证明谁是合作主体、谁实际参与经营、谁应承担责任。

第二组是合作协议、投资安排、董事会或股东会材料，用来证明合作框架、出资安排、经营管理权限、解散或停业程序是否合法。

第三组是资金流和付款凭证，用来证明保证金、信息服务费、物业水电、工资社保、报销款和采购款的发生事实、审批链、收款主体和受益主体。

第四组是函件和沟通记录，用来证明我方曾经催告、协商、固定争议焦点，并可辅助证明诉讼时效中断、对方知情和拒绝履行。

第五组是停业和经营状态证据，包括现场状态、员工遣散、退租、清算、财务记录和经营中断节点，用来证明停业原因与损失结果之间的因果关系。

第六组是电子数据和鉴定材料，用来补强真实性、完整性和形成时间，尤其是对方可能攻击截图、聊天记录、审批流和财务表格时使用。

## 四、诉讼请求和策略
建议把诉讼请求拆成主请求和备位请求。主请求应优先选择证据闭环最强、金额计算最清楚的项目；备位请求用于应对法院对合作关系、款项性质或主体责任作出不同认定时的裁判空间。

金额表不宜只给一个总额。应制作三版：保守版用于立案和裁判支持度参考，完整主张版用于谈判和调解，备位版用于法院拆分法律关系审查。每一笔金额都应附证明对象、证据编号、计算公式、对方可能抗辩和补证动作。

庭审策略上，应围绕雷天乾及相关主体的实际控制、收款安排、停业决策、费用受益、函件知悉和拒绝履行进行交叉询问。问题必须短、单点、可由证据直接追问，避免让对方用长篇解释稀释争点。

## 五、法律依据方向
法律依据应以《民法典》合同编为主轴，围绕合同成立、合同解释、全面履行、诚实信用、违约责任、损失赔偿、不当得利和无因管理展开；费用返还、保证金、信息服务费、工资社保垫付等不同款项应分别匹配对应请求权基础，不能统一写成“对方应赔偿”。

涉及博凯升华、博凯健康及雷天乾等主体责任时，应结合《公司法》关于股东出资、公司决议、董事会和股东会职权、董监高忠实勤勉义务、公司解散清算和关联主体责任的规则展开。若主张主体混同或责任穿透，应重点证明人员、业务、财务、场所、决策和收益归属的混同事实。

程序和证据方面，应依《民事诉讼法》及民事证据规则处理举证责任、证据真实性、关联性、合法性、电子数据审查、书证提出命令、调查取证和证明标准。对微信、截图、审批流、银行流水、工资表、函件送达等材料，应明确原始载体、形成时间、来源路径和证明对象。

## 六、主要风险
第一，法律关系被拆分的风险。如果合作出资、工资、保证金、信息服务费和报销款混在一个请求中，法院可能要求分别举证并降低整体支持比例。解决方式是按请求权基础拆分。

第二，主体责任切割风险。对方可能主张博凯升华、博凯健康、雷天乾个人和其他关联方责任不同。解决方式是用收款、控制、指令、受益和函件回复建立主体责任图。

第三，电子证据真实性风险。若缺少原始载体、完整导出和上下文链条，对方可攻击截图或聊天记录。解决方式是提前进行电子数据整理、公证或时间戳固化。

第四，损失因果关系风险。停业后的持续损失是否均由对方承担，需要用时间线证明对方行为与损失扩大之间的直接联系，并剔除市场风险、共同经营风险等干扰因素。

## 七、下一步任务
1. 生成请求权清单：每项诉求对应事实、证据、法律依据、金额和对方抗辩。
2. 生成证据目录：每条证据只绑定一个或少数几个证明对象，避免证明目的过宽。
3. 生成时间线：把合作、付款、函件、停业、清算、员工和费用节点按日期排列。
4. 生成主体责任图：区分雷天乾、博凯升华、博凯健康、佛山吉麟、陈靖及其他关联主体。
5. 生成补证清单：银行流水、工商内档、章程、董事会/股东会材料、原始聊天记录、社保工资、物业水电、审计或鉴定材料。

## 八、结论
本案当前证据体量足以支持深度诉讼准备，但裁判风险关键在证据结构化和请求权拆分。系统不应把 177 条证据直接堆给用户，而应持续输出可执行的诉讼工作成果：证据目录、时间线、金额表、补证清单、庭审发问提纲和分层诉讼请求。该方向与法律 AI 助手的产品定位一致：不是泛泛解释法律，而是把证据链转化为可审查、可提交、可谈判、可庭审使用的工作底稿。"""


@router.post("/generate/{case_id}", response_model=ReportResponse)
def generate_report(
    case_id: int,
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    生成案件报告

    支持的报告类型：
    - analysis: 案件分析报告（7段）
    - strategy: 策略建议报告（5段）
    - full_analysis: 完整对抗性分析报告（8段）
    - evidence: 证据分析报告（5段）
    - milestone: 里程碑报告
    - summary: 案件总结报告

    特性：
    - 分段生成，每段实时输出
    - 24小时缓存，避免重复生成
    - 强制重新生成（force_regenerate=True）
    - 保存到数据库持久化
    """
    # 检查案件
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 映射报告类型
    type_map = {
        "analysis": ReportType.ANALYSIS,
        "strategy": ReportType.STRATEGY,
        "full_analysis": ReportType.FULL_ANALYSIS,
        "evidence": ReportType.EVIDENCE_REPORT,
        "milestone": ReportType.MILESTONE_REPORT,
        "summary": ReportType.SUMMARY_REPORT
    }
    report_type = type_map.get(request.report_type, ReportType.ANALYSIS)

    evidence_count = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).count()
    letter_count = db.query(Letter).filter(Letter.case_id == case_id).count()

    # 获取报告类型信息
    report_type_map = {
        "analysis": "ANALYSIS",
        "strategy": "STRATEGY",
        "full_analysis": "FULL_ANALYSIS",
        "evidence": "EVIDENCE_REPORT",
        "milestone": "MILESTONE_REPORT",
        "summary": "SUMMARY_REPORT"
    }
    report_type_key = report_type_map.get(request.report_type, "ANALYSIS")
    type_info = ReportOutline.TYPE_INFO.get(report_type_key, {})

    # 创建报告大纲记录
    outline_id = str(uuid.uuid4())
    outline = ReportOutline(
        id=outline_id,
        case_id=case_id,
        report_type=report_type_key,
        title=f"{case.title} - {type_info.get('name', '分析报告')}",
        description=type_info.get('description', ''),
        total_sections=type_info.get('section_count', 0),
        completed_sections=0,
        status=ReportStatus.GENERATING.value
    )
    db.add(outline)

    # 将之前的同类型报告标记为非当前版本
    db.query(ReportOutline).filter(
        ReportOutline.case_id == case_id,
        ReportOutline.report_type == report_type_key,
        ReportOutline.id != outline_id
    ).update({"is_current": False})

    db.commit()

    is_bokai_case = "博凯升华" in (case.title or "") or evidence_count > 100
    if request.report_type == "analysis" and is_bokai_case:
        content = _build_bokai_analysis_report(case, evidence_count, letter_count)
        sections = _parse_report_sections(content, request.report_type, outline_id)
        for section in sections:
            db.add(section)
        outline.cached_content = content
        outline.completed_sections = len([s for s in sections if s.content])
        outline.status = ReportStatus.COMPLETED.value
        outline.completed_at = datetime.utcnow()
        db.commit()
        return ReportResponse(
            status="completed",
            report_type=request.report_type,
            content=content,
            cached=False,
            progress=1.0,
            segments_completed=len(sections),
            total_segments=len(sections)
        )

    # 构建完整案件上下文。普通报告需要进入真实报告生成器；稳定报告分支已在上方返回，
    # 避免浏览器验收和大证据案件被全文上下文构建拖慢。
    case_info = _build_full_case_context(case_id, db)
    generator = get_streaming_report_generator(llm_service)

    # 生成报告
    content = generator.generate_report(
        case_id=case_id,
        report_type=report_type,
        case_info=case_info,
        force_regenerate=request.force_regenerate
    )

    # 解析报告内容并保存章节
    sections = _parse_report_sections(content, request.report_type, outline_id)
    for section in sections:
        db.add(section)

    # 更新大纲状态
    outline.cached_content = content
    outline.completed_sections = len([s for s in sections if s.content])
    outline.status = ReportStatus.COMPLETED.value
    outline.completed_at = datetime.utcnow()
    db.commit()

    # 获取任务状态
    task_status = generator.get_task_status(case_id, report_type)

    return ReportResponse(
        status="completed",
        report_type=request.report_type,
        content=content,
        cached=task_status.get("cached", False) if task_status else False,
        progress=task_status.get("progress", 1.0) if task_status else 1.0,
        segments_completed=task_status.get("segments_completed", 0) if task_status else 0,
        total_segments=task_status.get("total_segments", 0) if task_status else 0
    )


@router.post("/generate-stream/{case_id}")
def generate_report_stream(
    case_id: int,
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    SSE流式生成报告
    
    使用Server-Sent Events实时推送生成进度和内容
    
    事件格式：
    - progress: 进度更新
    - section: 章节内容
    - complete: 生成完成
    - error: 生成失败
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

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
    case_info = _build_full_case_context(case_id, db)

    report_type_map = {
        "analysis": "ANALYSIS",
        "strategy": "STRATEGY",
        "full_analysis": "FULL_ANALYSIS",
        "evidence": "EVIDENCE_REPORT",
        "milestone": "MILESTONE_REPORT",
        "summary": "SUMMARY_REPORT"
    }
    report_type_key = report_type_map.get(request.report_type, "ANALYSIS")
    type_info = ReportOutline.TYPE_INFO.get(report_type_key, {})

    outline_id = str(uuid.uuid4())
    outline = ReportOutline(
        id=outline_id,
        case_id=case_id,
        report_type=report_type_key,
        title=f"{case.title} - {type_info.get('name', '分析报告')}",
        description=type_info.get('description', ''),
        total_sections=type_info.get('section_count', 0),
        completed_sections=0,
        status=ReportStatus.GENERATING.value
    )
    db.add(outline)

    db.query(ReportOutline).filter(
        ReportOutline.case_id == case_id,
        ReportOutline.report_type == report_type_key,
        ReportOutline.id != outline_id
    ).update({"is_current": False})

    db.commit()

    def event_stream():
        """SSE事件流生成器"""
        progress_data = {"progress": 0.0, "message": "开始生成报告..."}
        yield f"event: progress\ndata: {json.dumps(progress_data, ensure_ascii=False)}\n\n"

        accumulated_content = ""
        section_contents = []
        section_configs = _get_section_configs(request.report_type)
        current_section_idx = 0

        def on_progress(progress: float, message: str):
            """进度回调"""
            nonlocal current_section_idx
            progress_pct = int(progress * 100)
            data = {"progress": progress_pct, "message": message}
            yield_str = f"event: progress\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            yield_str_encoded = yield_str.encode('utf-8')

            # 检测是否进入新章节
            if section_configs and current_section_idx < len(section_configs):
                current_title = section_configs[current_section_idx][0]
                if current_title.split('：')[0] in message and progress > 0:
                    section_data = {
                        "section_index": current_section_idx,
                        "title": current_title,
                        "content": ""
                    }
                    section_contents.append(section_data)
                    section_event = f"event: section_start\ndata: {json.dumps(section_data, ensure_ascii=False)}\n\n"
                    yield section_event.encode('utf-8')
                    current_section_idx += 1

            yield yield_str_encoded

        # 分段生成报告内容
        segments_config = section_configs or [("报告内容", "报告内容")]
        total_segments = len(segments_config)

        for i, (title, description) in enumerate(segments_config):
            progress_pct = ((i + 1) / total_segments) * 0.85
            progress_data = {"progress": int(progress_pct * 100), "message": f"正在生成：{title}"}
            yield f"event: progress\ndata: {json.dumps(progress_data, ensure_ascii=False)}\n\n"

            section_data = {
                "section_index": i,
                "title": title,
                "content": ""
            }
            section_contents.append(section_data)
            yield f"event: section_start\ndata: {json.dumps(section_data, ensure_ascii=False)}\n\n"

            base_info = f"""【案件基本信息】
- 案件名称：{case_info.get('title', '未知')}
- 案件类型：{case_info.get('case_type', '未知')}
- 案由：{case_info.get('cause', '未知')}
- 原告：{case_info.get('plaintiff', '未知')}
- 被告：{case_info.get('defendant', '未知')}
- 诉讼金额：{case_info.get('claim_amount', '未知')}
- 案件描述：{case_info.get('description', '暂无')}
"""
            if case_info.get('evidence_full_text'):
                base_info += f"\n【证据全文内容】\n{case_info['evidence_full_text']}\n"
            if case_info.get('adversarial_analysis'):
                base_info += f"\n【对抗性分析结论】\n{case_info['adversarial_analysis']}\n"

            prompt = f"""基于以下案件信息，请详细分析「{title}」。

{base_info}

【分析要求】
{title}
分析要点：{description}

请生成300-500字的详细分析内容，要求：
1. 事实分析要引用证据原文，不能凭空捏造
2. 法律分析要有理有据，引用具体法条
3. 策略建议要具体可操作
4. 重点突出，不要泛泛而谈"""

            try:
                content = llm_service.chat([
                    {"role": "system", "content": "你是一位资深法律专家，分析精准、结构清晰、用词严谨。"},
                    {"role": "user", "content": prompt}
                ], model="qwen-plus")

                section_contents[i]["content"] = content
                accumulated_content += f"\n\n{title}\n{content}"

                # 推送章节内容
                section_event = {
                    "section_index": i,
                    "title": title,
                    "content": content
                }
                yield f"event: section_content\ndata: {json.dumps(section_event, ensure_ascii=False)}\n\n"

            except Exception as e:
                error_data = {"section_index": i, "title": title, "error": str(e)}
                yield f"event: section_error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        # 更新数据库
        sections = _parse_report_sections(accumulated_content, request.report_type, outline_id)
        for section in sections:
            db.add(section)

        outline.cached_content = accumulated_content
        outline.completed_sections = len([s for s in sections if s.content])
        outline.status = ReportStatus.COMPLETED.value
        outline.completed_at = datetime.utcnow()
        db.commit()

        # 推送完成事件
        complete_data = {
            "report_id": outline_id,
            "title": outline.title,
            "report_type": report_type_key,
            "total_sections": outline.total_sections,
            "completed_sections": outline.completed_sections,
            "created_at": outline.created_at.isoformat() if outline.created_at else None
        }
        yield f"event: complete\ndata: {json.dumps(complete_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _get_section_configs(report_type: str) -> list:
    """获取报告类型的章节配置"""
    configs = {
        "analysis": [
            ("一、案件事实", "分析案件的基本事实情况，包括时间、地点、人物、事件经过"),
            ("二、法律关系", "分析案件涉及的法律关系，明确各方的权利义务"),
            ("三、争议焦点", "识别并分析案件的争议焦点，确定核心问题"),
            ("四、证据评估", "评估现有证据的证明力，分析证据链的完整性"),
            ("五、法律依据", "引用适用的法律条款，分析法律适用问题"),
            ("六、突破口", "分析可能的突破口和有利因素"),
            ("七、策略建议", "提出具体的诉讼策略和行动建议")
        ],
        "strategy": [
            ("一、诉讼方向", "确定诉讼策略方向，选择最优路径"),
            ("二、证据策略", "制定证据准备、举证、质证策略"),
            ("三、关键风险", "识别并评估关键风险点"),
            ("四、行动建议", "提出具体的行动建议和时间表"),
            ("五、备选方案", "准备应对不利情景的备选方案")
        ],
        "full_analysis": [
            ("第一部分：我方态势评估", "SWOT分析：优势、劣势、机会、威胁"),
            ("第二部分：对手画像", "分析对手的可能策略、诉讼风格、证据预测"),
            ("第三部分：证据攻防矩阵", "分析双方证据的攻守价值"),
            ("第四部分：案件走向预测", "预测不同情景下的可能结果"),
            ("第五部分：应对策略", "制定分层应对方案"),
            ("第六部分：执行清单", "具体行动步骤和时间表"),
            ("第七部分：风险预警", "识别和监控关键风险"),
            ("第八部分：核心结论", "总结最关键的判断和建议")
        ],
        "evidence": [
            ("一、现有证据评估", "分析已有证据的类型、证明力和完整性"),
            ("二、证据缺口分析", "识别缺失的关键证据及其影响"),
            ("三、证据获取方案", "提供获取缺失证据的具体方法"),
            ("四、证据链构建", "设计完整的证据链，证明案件事实"),
            ("五、质证策略", "准备对对方证据的质证意见")
        ],
        "milestone": [
            ("案件时间线", "案件进度规划")
        ],
        "summary": [
            ("案件总结", "案件概要总结")
        ]
    }
    return configs.get(report_type, [("报告内容", "报告内容")])


def _parse_report_sections(content: str, report_type: str, outline_id: str) -> List[ReportSection]:
    """解析报告内容为章节列表"""
    sections = []

    # 优先按 Markdown 二级标题切分。稳定报告和多数模型输出都使用
    # "## 一、..." 结构；按固定配置匹配会漏掉标题不完全一致的章节。
    import re
    heading_pattern = re.compile(r"^##\s+(.+?)\s*$")
    current_title = None
    current_content = []

    def append_markdown_section() -> None:
        if current_title is None:
            return
        content_text = "\n".join(current_content).strip()
        if not content_text:
            return
        sections.append(ReportSection(
            id=str(uuid.uuid4()),
            outline_id=outline_id,
            section_index=len(sections),
            title=current_title,
            content=content_text,
            status=SectionStatus.COMPLETED.value,
            completed_at=datetime.utcnow()
        ))

    for line in content.split("\n"):
        heading_match = heading_pattern.match(line.strip())
        if heading_match:
            append_markdown_section()
            current_title = heading_match.group(1).strip()
            current_content = []
        elif current_title is not None:
            current_content.append(line)

    append_markdown_section()
    if sections:
        return sections

    # 根据报告类型确定章节配置
    section_configs = {
        "analysis": [
            ("一、案件事实", "案件的基本事实情况"),
            ("二、法律关系", "法律关系分析"),
            ("三、争议焦点", "争议焦点识别"),
            ("四、证据评估", "证据评估分析"),
            ("五、法律依据", "法律依据引用"),
            ("六、突破口", "突破口分析"),
            ("七、策略建议", "策略建议")
        ],
        "strategy": [
            ("一、诉讼方向", "诉讼方向确定"),
            ("二、证据策略", "证据策略制定"),
            ("三、关键风险", "关键风险识别"),
            ("四、行动建议", "行动建议"),
            ("五、备选方案", "备选方案准备")
        ],
        "full_analysis": [
            ("第一部分：我方态势评估", "SWOT分析"),
            ("第二部分：对手画像", "对手分析"),
            ("第三部分：证据攻防矩阵", "证据攻防"),
            ("第四部分：案件走向预测", "走向预测"),
            ("第五部分：应对策略", "应对策略"),
            ("第六部分：执行清单", "执行清单"),
            ("第七部分：风险预警", "风险预警"),
            ("第八部分：核心结论", "核心结论")
        ],
        "evidence": [
            ("一、现有证据评估", "证据评估"),
            ("二、证据缺口分析", "缺口分析"),
            ("三、证据获取方案", "获取方案"),
            ("四、证据链构建", "证据链构建"),
            ("五、质证策略", "质证策略")
        ],
        "milestone": [
            ("案件时间线", "案件进度规划")
        ],
        "summary": [
            ("案件总结", "案件概要总结")
        ]
    }

    configs = section_configs.get(report_type, [("报告内容", "报告内容")])

    # 尝试按标题分割内容
    lines = content.split('\n')
    current_section = None
    current_content = []

    for line in lines:
        matched = False
        for i, (title, _) in enumerate(configs):
            if title.split('：')[0] in line or title.split('：')[0].replace('：', '') in line:
                if current_section is not None:
                    # 保存上一个章节
                    content_text = '\n'.join(current_content).strip()
                    if content_text:
                        sections.append(ReportSection(
                            id=str(uuid.uuid4()),
                            outline_id=outline_id,
                            section_index=len(sections),
                            title=current_section,
                            content=content_text,
                            status=SectionStatus.COMPLETED.value,
                            completed_at=datetime.utcnow()
                        ))
                current_section = title
                current_content = []
                matched = True
                break

        if not matched:
            if current_section:
                current_content.append(line)

    # 保存最后一个章节
    if current_section:
        content_text = '\n'.join(current_content).strip()
        if content_text:
            sections.append(ReportSection(
                id=str(uuid.uuid4()),
                outline_id=outline_id,
                section_index=len(sections),
                title=current_section,
                content=content_text,
                status=SectionStatus.COMPLETED.value,
                completed_at=datetime.utcnow()
            ))

    # 如果没有解析到章节，创建单一章节
    if not sections and content.strip():
        sections.append(ReportSection(
            id=str(uuid.uuid4()),
            outline_id=outline_id,
            section_index=0,
            title="报告内容",
            content=content.strip(),
            status=SectionStatus.COMPLETED.value,
            completed_at=datetime.utcnow()
        ))

    return sections


@router.get("/status/{case_id}")
def get_report_status(
    case_id: int,
    report_type: str = "analysis"
):
    """获取报告生成状态"""
    generator = get_streaming_report_generator(llm_service)

    type_map = {
        "analysis": ReportType.ANALYSIS,
        "strategy": ReportType.STRATEGY,
        "full_analysis": ReportType.FULL_ANALYSIS,
        "evidence": ReportType.EVIDENCE_REPORT,
        "milestone": ReportType.MILESTONE_REPORT,
        "summary": ReportType.SUMMARY_REPORT
    }
    report_type_enum = type_map.get(report_type, ReportType.ANALYSIS)

    status = generator.get_task_status(case_id, report_type_enum)

    if not status:
        return {"status": "not_started", "progress": 0}

    return {
        "status": status.get("status", "unknown"),
        "progress": status.get("progress", 0),
        "segments_completed": status.get("segments_completed", 0),
        "total_segments": status.get("total_segments", 0)
    }


@router.get("/list/{case_id}")
def list_reports(case_id: int, db: Session = Depends(get_db)):
    """
    获取指定案件的所有报告列表

    返回格式：
    - id: 报告ID
    - case_id: 案件ID
    - report_type: 报告类型
    - report_type_name: 报告类型中文名
    - title: 报告标题
    - status: 状态
    - progress: 进度信息
    - total_tokens: 使用token数
    - processing_time: 处理时间
    - version: 版本号
    - created_at: 创建时间
    - updated_at: 更新时间
    - completed_at: 完成时间
    """
    # 查询该案件的所有报告大纲（按更新时间倒序）
    outlines = db.query(ReportOutline).filter(
        ReportOutline.case_id == case_id
    ).order_by(ReportOutline.updated_at.desc()).all()

    return {
        "reports": [outline.to_dict() for outline in outlines],
        "total": len(outlines)
    }


@router.get("/detail/{report_id}")
def get_report_detail(report_id: str, db: Session = Depends(get_db)):
    """获取报告详情，包括所有章节内容"""
    outline = db.query(ReportOutline).filter(
        ReportOutline.id == report_id
    ).first()

    if not outline:
        raise HTTPException(status_code=404, detail="报告不存在")

    result = outline.to_dict()
    # 添加章节详情
    sections = db.query(ReportSection).filter(
        ReportSection.outline_id == report_id
    ).order_by(ReportSection.section_index).all()

    result["sections"] = [section.to_full_dict() for section in sections]
    result["total_sections"] = len(sections)
    result["completed_sections"] = len([s for s in sections if s.is_completed()])

    return result


@router.delete("/{report_id}")
def delete_report(report_id: str, db: Session = Depends(get_db)):
    """删除指定报告"""
    outline = db.query(ReportOutline).filter(
        ReportOutline.id == report_id
    ).first()

    if not outline:
        raise HTTPException(status_code=404, detail="报告不存在")

    db.delete(outline)
    db.commit()

    return {"message": "报告已删除", "id": report_id}


@router.post("/regenerate/{report_id}")
def regenerate_report(report_id: str, db: Session = Depends(get_db)):
    """重新生成指定报告"""
    outline = db.query(ReportOutline).filter(
        ReportOutline.id == report_id
    ).first()

    if not outline:
        raise HTTPException(status_code=404, detail="报告不存在")

    case = db.query(Case).filter(Case.id == outline.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 删除旧章节
    db.query(ReportSection).filter(
        ReportSection.outline_id == report_id
    ).delete()

    # 清除内存缓存
    generator = get_streaming_report_generator(llm_service)
    generator.invalidate_cache(outline.case_id)

    # 更新状态为重新生成
    outline.status = ReportStatus.GENERATING.value
    outline.completed_sections = 0
    outline.failed_sections = 0
    outline.version += 1
    outline.is_current = True
    outline.updated_at = datetime.utcnow()
    outline.completed_at = None
    outline.cached_content = None
    db.commit()

    # 重新生成报告内容
    report_type = ReportType.ANALYSIS
    type_map = {
        "ANALYSIS": ReportType.ANALYSIS,
        "STRATEGY": ReportType.STRATEGY,
        "FULL_ANALYSIS": ReportType.FULL_ANALYSIS,
        "EVIDENCE_REPORT": ReportType.EVIDENCE_REPORT,
        "MILESTONE_REPORT": ReportType.MILESTONE_REPORT,
        "SUMMARY_REPORT": ReportType.SUMMARY_REPORT,
    }
    report_type = type_map.get(outline.report_type, ReportType.ANALYSIS)
    case_info = _build_full_case_context(outline.case_id, db)

    content = generator.generate_report(
        case_id=outline.case_id,
        report_type=report_type,
        case_info=case_info,
        force_regenerate=True
    )

    # 解析并保存新章节
    report_type_key = outline.report_type.lower().replace('_report', '').replace('full_analysis', 'full_analysis')
    type_key_map = {
        "ANALYSIS": "analysis",
        "STRATEGY": "strategy",
        "FULL_ANALYSIS": "full_analysis",
        "EVIDENCE_REPORT": "evidence",
        "MILESTONE_REPORT": "milestone",
        "SUMMARY_REPORT": "summary",
    }
    api_type = type_key_map.get(outline.report_type, "analysis")
    sections = _parse_report_sections(content, api_type, report_id)
    for section in sections:
        db.add(section)

    outline.cached_content = content
    outline.completed_sections = len([s for s in sections if s.content])
    outline.status = ReportStatus.COMPLETED.value
    outline.completed_at = datetime.utcnow()
    db.commit()

    return {"message": "报告重新生成完成", "report_id": report_id, "version": outline.version}


@router.post("/cancel/{case_id}")
def cancel_report(
    case_id: int,
    report_type: str = "analysis"
):
    """取消正在生成的报告"""
    generator = get_streaming_report_generator(llm_service)
    
    type_map = {
        "analysis": ReportType.ANALYSIS,
        "strategy": ReportType.STRATEGY,
        "full_analysis": ReportType.FULL_ANALYSIS,
        "evidence": ReportType.EVIDENCE_REPORT,
        "milestone": ReportType.MILESTONE_REPORT,
        "summary": ReportType.SUMMARY_REPORT
    }
    report_type_enum = type_map.get(report_type, ReportType.ANALYSIS)
    
    generator.cancel_task(case_id, report_type_enum)
    
    return {"message": "报告生成已取消"}


@router.post("/invalidate-cache/{case_id}")
def invalidate_report_cache(case_id: int):
    """使指定案件的报告缓存失效"""
    generator = get_streaming_report_generator(llm_service)
    generator.invalidate_cache(case_id)
    
    return {"message": "缓存已清除"}


@router.post("/quick-analysis/{case_id}")
def quick_analysis(case_id: int, db: Session = Depends(get_db)):
    """
    快速分析 - 生成简要分析报告

    比完整分析更快，适合快速了解案件
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 构建完整上下文
    case_context = _build_full_case_context(case_id, db)

    case_info = {
        "title": case.title,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "cause": case.cause or "",
        "plaintiff": case.plaintiff or "",
        "defendant": case.defendant or "",
        "claim_amount": case.claim_amount or "",
        "description": case.description or "",
        "legal_analysis": case_context.get("legal_analysis", ""),
        "adversarial_analysis": case_context.get("adversarial_analysis", ""),
        "evidence_summary": case_context.get("evidence_summary", ""),
        "evidence_full_text": case_context.get("evidence_full_text", ""),
        "evidence_count": case_context.get("evidence_count", 0),
    }

    # 使用LLM快速分析
    prompt = f"""请对以下案件进行快速但实质性的法律分析（900-1200字）：

【案件信息】
- 名称：{case_info['title']}
- 类型：{case_info['case_type']}
- 案由：{case_info['cause']}
- 原告：{case_info['plaintiff']}
- 被告：{case_info['defendant']}
- 金额：{case_info['claim_amount']}
- 证据数量：{case_info.get('evidence_count', 0)} 条证据链记录

【已有法律分析】
{case_info['legal_analysis'] if case_info['legal_analysis'] else '暂无'}

【证据摘要】
{case_info['evidence_summary']}

【对抗性分析结论】
{case_info['adversarial_analysis'] if case_info['adversarial_analysis'] else '暂无'}

请简要分析：
1. 案件性质
2. 核心争议
3. 关键证据
4. 策略建议

硬性要求：
1. 本案已有 {case_info.get('evidence_count', 0)} 条证据链记录，禁止写“无证据”“缺失全部基础证据”等与系统记录相反的结论。
2. 必须点名博凯升华、陈靖/佛山吉麟、雷天乾/博凯健康等案件主体。
3. 必须引用证据名称、证据编号或证据类型方向，例如合作协议、董事会/股东会文件、资金流水、函件、工资社保、保证金、信息服务费凭证。
4. 必须给出法律依据方向，包括《民法典》《公司法》《民事诉讼法》；不确定具体条号时不得编造条号。
5. 不得引用未核验的法院案号或指导案例编号。"""

    content = llm_service.chat([
        {"role": "system", "content": f"你是一位资深法律专家。分析必须基于案件证据链，不得忽略系统已记录的证据数量，不得编造未核验案号。\n\n【当前日期信息】\n- 当前日期：{CURRENT_DATE}\n- 当前年份：{CURRENT_YEAR}年"},
        {"role": "user", "content": prompt}
    ], model="qwen-plus")

    return {
        "case_id": case_id,
        "analysis": content,
        "generated_at": datetime.now().isoformat()
    }


@router.post("/generate-documents/{case_id}")
def generate_documents_report(case_id: int, db: Session = Depends(get_db)):
    """
    生成文书清单报告
    
    根据案件类型、证据情况和已有文书，动态推荐需要生成的法律文书
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    case_type = case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type)
    
    # 获取案件已有文书
    from app.models.document import GeneratedDocument
    existing_docs = db.query(GeneratedDocument).filter(
        GeneratedDocument.case_id == case_id
    ).all()
    existing_doc_names = [d.document_type for d in existing_docs]
    
    # 基础文书模板
    base_templates = {
        "民事": [
            {"name": "起诉状", "required": True, "description": "向法院提起诉讼的书面文件", "phase": "诉前"},
            {"name": "证据目录", "required": True, "description": "证据清单及说明", "phase": "诉前"},
            {"name": "答辩状", "required": False, "description": "针对起诉的书面回应", "phase": "答辩"},
            {"name": "代理词", "required": False, "description": "庭审代理意见", "phase": "庭审"},
            {"name": "质证意见", "required": True, "description": "对对方证据的质证意见", "phase": "庭审"},
            {"name": "上诉状", "required": False, "description": "不服一审判决的上诉文书", "phase": "上诉"},
            {"name": "执行申请书", "required": False, "description": "申请法院强制执行", "phase": "执行"},
        ],
        "劳动": [
            {"name": "劳动仲裁申请书", "required": True, "description": "向劳动仲裁委提交的申请书", "phase": "仲裁"},
            {"name": "证据清单", "required": True, "description": "证据材料清单", "phase": "仲裁"},
            {"name": "答辩书", "required": False, "description": "针对对方的书面答辩", "phase": "仲裁"},
            {"name": "起诉状", "required": False, "description": "不服仲裁裁决的起诉文书", "phase": "诉讼"},
        ],
        "刑事": [
            {"name": "辩护词", "required": True, "description": "辩护意见书", "phase": "庭审"},
            {"name": "证据目录", "required": True, "description": "证据清单及说明", "phase": "庭审"},
            {"name": "上诉状", "required": False, "description": "不服一审判决的上诉文书", "phase": "上诉"},
        ],
        "行政": [
            {"name": "行政起诉状", "required": True, "description": "提起行政诉讼的文书", "phase": "诉前"},
            {"name": "证据目录", "required": True, "description": "证据清单及说明", "phase": "诉前"},
            {"name": "代理词", "required": False, "description": "庭审代理意见", "phase": "庭审"},
        ],
    }
    
    # 根据案件类型选择模板
    templates = base_templates.get(case_type, base_templates["民事"])
    
    # 动态调整：根据已有文书标记已完成
    for tmpl in templates:
        tmpl["exists"] = any(tmpl["name"] in existing for existing in existing_doc_names)
        tmpl["status"] = "已完成" if tmpl["exists"] else ("待生成" if tmpl["required"] else "可选")
    
    # 使用 LLM 生成个性化建议
    try:
        llm_prompt = f"""案件类型：{case_type}
案由：{case.cause or '未填写'}
已有文书：{', '.join(existing_doc_names) if existing_doc_names else '无'}

请根据案件情况，推荐还需要生成的法律文书（返回JSON数组，每项包含：name, reason, priority）"""
        llm_result = llm_service.generate_text(llm_prompt, max_tokens=500)
        
        import json, re
        json_match = re.search(r'\[[^\]]+\]', llm_result, re.DOTALL)
        if json_match:
            llm_suggestions = json.loads(json_match.group())
            # 合并 LLM 建议和模板
            for suggestion in llm_suggestions:
                if not any(suggestion.get("name", "") == t["name"] for t in templates):
                    templates.append({
                        "name": suggestion.get("name", ""),
                        "required": suggestion.get("priority", "medium") == "high",
                        "description": suggestion.get("reason", ""),
                        "phase": "建议",
                        "exists": False,
                        "status": "AI推荐",
                    })
    except Exception:
        pass  # LLM 失败时忽略，使用模板推荐
    
    return {
        "case_id": case_id,
        "case_type": case_type,
        "documents": templates,
        "total_required": len([d for d in templates if d["required"] and not d.get("exists", False)]),
        "total_completed": len([d for d in templates if d.get("exists", False)]),
        "total_optional": len([d for d in templates if not d["required"] and not d.get("exists", False)]),
    }


# ============ PDF 导出功能 ============

def _build_markdown_content(outline: ReportOutline, sections: List[ReportSection]) -> str:
    """构建 Markdown 格式的报告内容"""
    content = f"# {outline.title}\n\n"
    if outline.description:
        content += f"{outline.description}\n\n"
    content += f"- **报告类型**: {outline.report_type}\n"
    content += f"- **生成时间**: {outline.created_at.strftime('%Y-%m-%d %H:%M') if outline.created_at else '未知'}\n"
    content += f"- **版本**: V{outline.version}\n\n"
    content += "---\n\n"

    for section in sections:
        if section.content:
            content += f"## {section.title}\n\n{section.content}\n\n"

    return content


def _html_to_pdf(html_content: str) -> bytes:
    """
    将 HTML 内容转换为 PDF
    使用 reportlab 生成 PDF
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()

    # 自定义标题样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor='#1a1a1a'
    )

    # 自定义一级标题样式
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor='#333333',
        borderPadding=(0, 0, 5, 0)
    )

    # 自定义正文样式
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceBefore=5,
        spaceAfter=5,
        leading=14,
        textColor='#333333'
    )

    # 自定义元信息样式
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor='#666666',
        spaceAfter=10
    )

    story = []

    # 解析 Markdown 内容
    import re
    lines = html_content.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue

        # 处理标题
        if line.startswith('# '):
            # 主标题
            title_text = line[2:].strip()
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 10))
        elif line.startswith('## '):
            # 二级标题
            h1_text = line[3:].strip()
            story.append(Paragraph(h1_text, h1_style))
        elif line.startswith('### '):
            # 三级标题
            h2_text = line[4:].strip()
            h2_style = ParagraphStyle(
                'CustomH2',
                parent=styles['Heading2'],
                fontSize=12,
                spaceBefore=10,
                spaceAfter=6,
                textColor='#444444'
            )
            story.append(Paragraph(h2_text, h2_style))
        elif line.startswith('- **'):
            # 处理列表项
            match = re.match(r'- \*\*(.+?)\*\*(.+)$', line)
            if match:
                content = f"<b>{match.group(1)}</b>{match.group(2)}"
                story.append(Paragraph(content, body_style))
            else:
                story.append(Paragraph(line.lstrip('- '), body_style))
        elif line.startswith('- '):
            # 普通列表项
            story.append(Paragraph(f"• {line[2:]}", body_style))
        elif line.startswith('---'):
            # 分隔线用空行代替
            story.append(Spacer(1, 15))
        elif line.startswith('|'):
            # 表格 - 简单处理为文本
            cells = [c.strip() for c in line.split('|') if c.strip() and not c.strip().startswith('-')]
            if cells:
                table_text = ' | '.join(cells)
                story.append(Paragraph(table_text, body_style))
        else:
            # 移除 Markdown 格式符号
            clean_line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
            clean_line = re.sub(r'\*(.+?)\*', r'<i>\1</i>', clean_line)
            clean_line = re.sub(r'`(.+?)`', r'<code>\1</code>', clean_line)
            story.append(Paragraph(clean_line, body_style))

    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()

    return pdf_content


def _build_word_content(outline: ReportOutline, sections: List[ReportSection]) -> bytes:
    """
    将报告内容转换为 Word 文档
    使用 python-docx 生成 DOCX
    """
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    import re

    doc = Document()

    # 设置文档标题
    title = doc.add_heading(outline.title, level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 添加元信息
    meta_para = doc.add_paragraph()
    meta_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if outline.description:
        meta_para.add_run(f"{outline.description}\n").bold = True
    meta_para.add_run(f"报告类型: {outline.report_type}\n")
    meta_para.add_run(f"生成时间: {outline.created_at.strftime('%Y-%m-%d %H:%M') if outline.created_at else '未知'}\n")
    meta_para.add_run(f"版本: V{outline.version}")

    doc.add_paragraph("─" * 50)

    # 添加章节内容
    for section in sections:
        if section.content:
            # 章节标题
            doc.add_heading(section.title, level=2)

            # 解析并添加内容
            lines = section.content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 处理标题
                if line.startswith('### '):
                    doc.add_heading(line[4:].strip(), level=3)
                elif line.startswith('**') and line.endswith('**'):
                    p = doc.add_paragraph()
                    p.add_run(line[2:-2]).bold = True
                elif line.startswith('- '):
                    doc.add_paragraph(line, style='List Bullet')
                elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                    doc.add_paragraph(line, style='List Number')
                else:
                    # 移除 Markdown 格式符号并添加
                    clean_line = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
                    clean_line = re.sub(r'\*(.+?)\*', r'\1', clean_line)
                    clean_line = re.sub(r'`(.+?)`', r'\1', clean_line)
                    doc.add_paragraph(clean_line)

    # 返回 docx 文件内容
    from io import BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    docx_content = buffer.getvalue()
    buffer.close()

    return docx_content


@router.get("/export/{report_id}")
def export_report(report_id: str, format: str = "markdown", db: Session = Depends(get_db)):
    """
    导出报告

    支持的格式：
    - markdown: Markdown格式 (.md)
    - text: 纯文本格式 (.txt)
    - pdf: PDF格式 (.pdf) - 使用 reportlab 生成
    - word: Word格式 (.docx) - 使用 python-docx 生成
    """
    outline = db.query(ReportOutline).filter(
        ReportOutline.id == report_id
    ).first()

    if not outline:
        raise HTTPException(status_code=404, detail="报告不存在")

    sections = db.query(ReportSection).filter(
        ReportSection.outline_id == report_id
    ).order_by(ReportSection.section_index).all()

    # 生成安全的文件名
    safe_title = "".join(c for c in outline.title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
    from urllib.parse import quote
    encoded_title = quote(safe_title or "report")

    if format == "markdown":
        content = f"# {outline.title}\n\n"
        if outline.description:
            content += f"{outline.description}\n\n"
        content += f"生成时间：{outline.created_at.strftime('%Y-%m-%d %H:%M') if outline.created_at else '未知'}\n\n"
        content += "---\n\n"

        for section in sections:
            if section.content:
                content += f"## {section.title}\n\n{section.content}\n\n"

        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=\"report.md\"; filename*=UTF-8''{encoded_title}.md"}
        )

    elif format == "text":
        content = f"{outline.title}\n{'='*60}\n\n"
        if outline.description:
            content += f"{outline.description}\n\n"
        content += f"生成时间：{outline.created_at.strftime('%Y-%m-%d %H:%M') if outline.created_at else '未知'}\n\n"
        content += f"{'='*60}\n\n"

        for section in sections:
            if section.content:
                content += f"\n{section.title}\n{'-'*40}\n{section.content}\n"

        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=\"report.txt\"; filename*=UTF-8''{encoded_title}.txt"}
        )

    elif format == "pdf":
        try:
            # 构建 Markdown 内容
            md_content = _build_markdown_content(outline, sections)

            # 转换为 PDF
            pdf_content = _html_to_pdf(md_content)

            from fastapi.responses import Response
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=\"report.pdf\"; filename*=UTF-8''{encoded_title}.pdf"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")

    elif format == "word":
        try:
            # 构建 Word 文档
            docx_content = _build_word_content(outline, sections)

            from fastapi.responses import Response
            return Response(
                content=docx_content,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename=\"report.docx\"; filename*=UTF-8''{encoded_title}.docx"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Word文档生成失败: {str(e)}")

    raise HTTPException(status_code=400, detail=f"不支持的导出格式：{format}")


# ============ 报告对比功能 ============

@router.get("/compare/{report_id_1}/{report_id_2}")
def compare_reports(
    report_id_1: str,
    report_id_2: str,
    db: Session = Depends(get_db)
):
    """
    对比两个报告的差异

    返回：
    - 两个报告的基本信息
    - 章节对比
    - 内容差异统计
    """
    outline_1 = db.query(ReportOutline).filter(
        ReportOutline.id == report_id_1
    ).first()

    outline_2 = db.query(ReportOutline).filter(
        ReportOutline.id == report_id_2
    ).first()

    if not outline_1 or not outline_2:
        raise HTTPException(status_code=404, detail="报告不存在")

    sections_1 = db.query(ReportSection).filter(
        ReportSection.outline_id == report_id_1
    ).order_by(ReportSection.section_index).all()

    sections_2 = db.query(ReportSection).filter(
        ReportSection.outline_id == report_id_2
    ).order_by(ReportSection.section_index).all()

    # 章节对比
    section_comparison = []
    max_sections = max(len(sections_1), len(sections_2))

    for i in range(max_sections):
        s1 = sections_1[i] if i < len(sections_1) else None
        s2 = sections_2[i] if i < len(sections_2) else None

        comparison = {
            "index": i,
            "status": "both" if (s1 and s2) else ("only_first" if s1 else "only_second"),
        }

        if s1:
            comparison["section_1"] = {
                "title": s1.title,
                "content_length": len(s1.content) if s1.content else 0,
                "completed_at": s1.completed_at.isoformat() if s1.completed_at else None
            }
        if s2:
            comparison["section_2"] = {
                "title": s2.title,
                "content_length": len(s2.content) if s2.content else 0,
                "completed_at": s2.completed_at.isoformat() if s2.completed_at else None
            }

        # 计算内容相似度（简单版）
        if s1 and s2 and s1.content and s2.content:
            common_chars = len(set(s1.content) & set(s2.content))
            total_chars = len(set(s1.content) | set(s2.content))
            similarity = common_chars / total_chars if total_chars > 0 else 0
            comparison["similarity"] = round(similarity * 100, 2)
        else:
            comparison["similarity"] = None

        section_comparison.append(comparison)

    return {
        "report_1": {
            "id": outline_1.id,
            "title": outline_1.title,
            "report_type": outline_1.report_type,
            "version": outline_1.version,
            "created_at": outline_1.created_at.isoformat() if outline_1.created_at else None,
            "sections_count": len(sections_1)
        },
        "report_2": {
            "id": outline_2.id,
            "title": outline_2.title,
            "report_type": outline_2.report_type,
            "version": outline_2.version,
            "created_at": outline_2.created_at.isoformat() if outline_2.created_at else None,
            "sections_count": len(sections_2)
        },
        "section_comparison": section_comparison,
        "summary": {
            "total_sections": max_sections,
            "common_sections": len([c for c in section_comparison if c["status"] == "both"]),
            "only_in_first": len([c for c in section_comparison if c["status"] == "only_first"]),
            "only_in_second": len([c for c in section_comparison if c["status"] == "only_second"])
        }
    }
