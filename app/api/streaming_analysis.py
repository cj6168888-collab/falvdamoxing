"""
流式 AI 分析 API
支持全量证据综合分析，不受上下文窗口限制，流式输出结果
"""
import uuid
import json
import asyncio
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.models.case import Case
from app.models.document import Document
from app.models.evidence import EvidenceItem
from app.models.analysis_result import AnalysisResult
from app.core.tenant_context import TenantContext
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/streaming-analysis", tags=["流式 AI 分析"])

# 任务存储
_tasks: Dict[str, Dict[str, Any]] = {}
_tasks_lock = threading.Lock()


def _update_task(task_id: str, **kwargs):
    with _tasks_lock:
        if task_id in _tasks:
            _tasks[task_id].update(kwargs)


def _get_task(task_id: str) -> Optional[dict]:
    with _tasks_lock:
        return _tasks.get(task_id)


class CreateAnalysisRequest(BaseModel):
    case_id: int
    analysis_type: str = "full"  # full / evidence / strategy / risk / custom
    custom_prompt: Optional[str] = None
    options: Optional[dict] = None


@router.post("/create")
def create_analysis(request: CreateAnalysisRequest, db: Session = Depends(get_db)):
    """创建流式分析任务"""
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    task_id = str(uuid.uuid4())[:12]

    # 统计证据数量
    evidence_count = db.query(EvidenceItem).filter(EvidenceItem.case_id == request.case_id).count()

    task_data = {
        "task_id": task_id,
        "case_id": request.case_id,
        "analysis_type": request.analysis_type,
        "custom_prompt": request.custom_prompt,
        "options": request.options or {},
        "status": "pending",
        "progress": 0.0,
        "current_stage": "",
        "total_stages": 0,
        "completed_stages": 0,
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "evidence_count": evidence_count,
        "chunks": [],  # 存储所有流式输出片段
    }

    with _tasks_lock:
        _tasks[task_id] = task_data

    return {"task_id": task_id, "evidence_count": evidence_count}


@router.post("/{task_id}/start")
def start_analysis(task_id: str, db: Session = Depends(get_db)):
    """启动分析任务"""
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task["status"] = "running"
    task["progress"] = 0.0
    tenant_id = TenantContext.get_tenant_id()
    user_id = TenantContext.get_user_id()

    def run_analysis():
        previous_tenant_id = TenantContext.get_tenant_id()
        previous_user_id = TenantContext.get_user_id()
        local_db = SessionLocal()
        try:
            TenantContext.clear()
            if tenant_id:
                TenantContext.set_tenant(tenant_id)
            if user_id:
                TenantContext.set_user(user_id)
            _run_full_analysis(task_id, task, local_db)
        except Exception as e:
            _update_task(task_id, status="failed", error=str(e),
                         progress=1.0, current_stage="分析失败")
            # 更新分析记录为失败
            record_id = task.get("analysis_record_id")
            if record_id:
                record = local_db.query(AnalysisResult).filter(AnalysisResult.id == record_id).first()
                if record:
                    from datetime import datetime
                    record.status = "failed"
                    record.error_message = str(e)
                    record.completed_at = datetime.utcnow()
                    local_db.commit()
        finally:
            local_db.close()
            TenantContext.clear()
            if previous_tenant_id:
                TenantContext.set_tenant(previous_tenant_id)
            if previous_user_id:
                TenantContext.set_user(previous_user_id)

    thread = threading.Thread(target=run_analysis, daemon=True)
    thread.start()
    return {"message": "分析已启动"}


def _send_chunk(task_id: str, chunk: dict):
    """发送分析片段"""
    with _tasks_lock:
        if task_id in _tasks:
            _tasks[task_id]["chunks"].append(chunk)
            if chunk.get("progress") is not None:
                _tasks[task_id]["progress"] = chunk["progress"]
            if chunk.get("current_stage") is not None:
                _tasks[task_id]["current_stage"] = chunk["current_stage"]


def _run_full_analysis(task_id: str, task: dict, db: Session):
    """
    全量分析流程 - 不受上下文窗口限制
    自动分阶段、分块处理，结果持久化
    """
    case_id = task["case_id"]
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        _send_chunk(task_id, {"type": "error", "error": "案件不存在"})
        return

    # 创建分析结果记录
    tenant_id = TenantContext.get_tenant_id()
    analysis_record = AnalysisResult(
        tenant_id=tenant_id,
        case_id=case_id,
        analysis_type=task.get("analysis_type", "full"),
        depth=task.get("options", {}).get("depth", "standard"),
        status="running",
        custom_prompt=task.get("custom_prompt"),
        options=task.get("options"),
        evidence_count=task.get("evidence_count", 0),
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)
    task["analysis_record_id"] = analysis_record.id

    # 定义分析阶段
    stages = []

    if task["analysis_type"] == "full" or task["analysis_type"] == "evidence":
        stages.append(("案件概览", _analyze_case_overview))
        stages.append(("证据逐个分析", _analyze_evidence_chunks))
        stages.append(("证据交叉验证", _analyze_evidence_corroboration))

    if task["analysis_type"] == "full" or task["analysis_type"] == "strategy":
        stages.append(("法律适用分析", _analyze_legal_application))
        stages.append(("诉讼策略生成", _generate_strategy))

    if task["analysis_type"] == "full" or task["analysis_type"] == "risk":
        stages.append(("风险评估", _assess_risks))

    if task["analysis_type"] == "full":
        stages.append(("综合报告", _generate_comprehensive_report))

    if task["analysis_type"] == "custom":
        stages.append(("自定义分析", _run_custom_analysis))

    task["total_stages"] = len(stages)
    analysis_record.total_stages = len(stages)
    db.commit()

    # 执行每个阶段
    all_results = {}
    for stage_idx, (stage_name, stage_func) in enumerate(stages):
        _send_chunk(task_id, {
            "type": "progress",
            "stage": stage_name,
            "stageIndex": stage_idx,
            "totalStages": len(stages),
            "progress": stage_idx / len(stages),
            "current_stage": stage_name,
        })

        stage_result = stage_func(task_id, task, case, db, all_results)
        all_results[stage_name] = stage_result
        analysis_record.completed_stages = stage_idx + 1
        db.commit()

        _send_chunk(task_id, {
            "type": "stage_complete",
            "stage": stage_name,
            "stageIndex": stage_idx,
            "totalStages": len(stages),
            "progress": (stage_idx + 1) / len(stages),
            "current_stage": stage_name,
        })

    # 完成 - 持久化结果
    from datetime import datetime
    analysis_record.status = "completed"
    analysis_record.result_data = all_results
    analysis_record.completed_at = datetime.utcnow()
    analysis_record.updated_at = datetime.utcnow()

    # 生成摘要
    summary_parts = []
    for stage_name, result in all_results.items():
        if isinstance(result, dict):
            for k, v in result.items():
                if isinstance(v, str) and len(v) > 10:
                    summary_parts.append(f"【{stage_name}】{v[:200]}...")
                    break
    analysis_record.summary = "\n\n".join(summary_parts) if summary_parts else "分析完成"

    # 生成完整报告
    report_parts = []
    for stage_name, result in all_results.items():
        if isinstance(result, str):
            report_parts.append(f"## {stage_name}\n\n{result}")
        elif isinstance(result, dict):
            for k, v in result.items():
                if isinstance(v, str):
                    report_parts.append(f"## {stage_name} - {k}\n\n{v}")
    analysis_record.full_report = "\n\n".join(report_parts) if report_parts else None

    db.commit()

    _send_chunk(task_id, {
        "type": "complete",
        "progress": 1.0,
        "current_stage": "分析完成",
        "taskId": task_id,
        "analysisRecordId": analysis_record.id,
    })

    with _tasks_lock:
        if task_id in _tasks:
            _tasks[task_id]["status"] = "completed"
            _tasks[task_id]["result"] = all_results
            _tasks[task_id]["progress"] = 1.0
            _tasks[task_id]["analysis_record_id"] = analysis_record.id


def _analyze_case_overview(task_id, task, case, db, results):
    """阶段1：案件概览理解"""
    case_info = f"""
案件名称：{case.title}
案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}
第三人：{case.third_party or '无'}
案由：{case.cause or '未填写'}
诉讼金额：{case.claim_amount or '未填写'}
案件描述：{case.description or '未填写'}
补充说明：{case.supplement or '无'}
"""
    if case.legal_analysis:
        case_info += f"\n已有法律分析：\n{case.legal_analysis}"

    _send_chunk(task_id, {"type": "content", "stage": "案件概览", "content": f"正在分析案件基本信息...\n\n{case_info}"})

    # 调用 LLM 分析
    prompt = f"""请对以下案件进行全面概览分析：

⚠️ 核心约束（必须遵守）：
1. 绝对禁止凭空编造法律条文或司法解释，每条法律结论必须标注具体法条来源
2. 绝对禁止虚构不存在的案例，引用案例必须提供真实案号和法院
3. 不需要刻意讨好用户，说真话才是对用户最大的负责
4. 不确定时必须明确表达不确定性，不能用"一般"、"通常"模糊带过
5. 绝对禁止浮于表面、不深入分析就给出结论，必须深度思考推演

💡 核心要求：
1. 深度思考推演，对每一个问题进行深度思考和推演
2. 突破性创造性的寻找更多真实途径
3. 让用户看到真相、理解真相，找到取胜的真实路径

{case_info}

请分析：
1. 案件性质和核心争议焦点
2. 各方当事人的法律地位
3. 关键时间节点
4. 案件复杂程度评估
5. 初步诉讼风险与裁判支持度参考（必须客观，不作胜诉承诺）"""

    try:
        result = llm_service.chat(prompt)
        _send_chunk(task_id, {"type": "content", "stage": "案件概览", "content": result})
        return {"overview": result}
    except Exception as e:
        _send_chunk(task_id, {"type": "content", "stage": "案件概览", "content": f"概览分析失败：{str(e)}"})
        return {"overview": f"分析失败：{str(e)}"}


def _analyze_evidence_chunks(task_id, task, case, db, results):
    """阶段2：全量证据逐个分析 - 分块处理，不受上下文限制"""
    evidences = db.query(EvidenceItem).filter(EvidenceItem.case_id == case.id).all()
    total = len(evidences)

    if total == 0:
        _send_chunk(task_id, {"type": "content", "stage": "证据逐个分析", "content": "暂无证据"})
        return {"evidence_analysis": "暂无证据", "total": 0}

    _send_chunk(task_id, {"type": "content", "stage": "证据逐个分析",
                          "content": f"共发现 {total} 条证据，开始逐个分析..."})

    chunk_size = 20  # 每 20 条证据为一批次
    all_analyses = []

    for chunk_start in range(0, total, chunk_size):
        chunk_end = min(chunk_start + chunk_size, total)
        chunk_evidences = evidences[chunk_start:chunk_end]

        _send_chunk(task_id, {
            "type": "content",
            "stage": "证据逐个分析",
            "content": f"正在分析第 {chunk_start + 1}-{chunk_end} 条证据（共 {total} 条）...",
        })

        evidence_texts = []
        for ev in chunk_evidences:
            ev_info = f"""
证据ID：{ev.id}
证据类型：{ev.evidence_type or '未分类'}
原始文件：{ev.original_filename or '无'}
规范名称：{ev.display_name or '无'}
证明事实：{ev.proves_facts or '未指定'}
信度评分：{ev.credibility_score or '未评估'}
摘要：{ev.summary or '无'}
"""
            if ev.extracted_content:
                # 法律应用：使用完整证据内容
                ev_info += f"完整内容：{ev.extracted_content}\n"
            evidence_texts.append(ev_info)

        prompt = f"""请对以下 {len(chunk_evidences)} 条证据逐一进行专业法律分析：

⚠️ 核心约束（必须遵守）：
1. 绝对禁止凭空编造法律条文或司法解释，每条法律结论必须标注具体法条来源
2. 绝对禁止虚构不存在的案例，引用案例必须提供真实案号和法院
3. 不需要刻意讨好用户，说真话才是对用户最大的负责
4. 不确定时必须明确表达不确定性，不能用"一般"、"通常"模糊带过
5. 绝对禁止浮于表面、不深入分析就给出结论，必须深度思考推演
6. 分析必须基于证据原文，不能仅凭证据名称推测内容

💡 核心要求：
1. 深度思考推演，对每一个问题进行深度思考和推演
2. 突破性创造性的寻找更多真实途径
3. 让用户看到真相、理解真相，找到取胜的真实路径

{''.join(evidence_texts)}

对每条证据请分析：
1. 证据的法律效力和证明力（必须基于证据原文内容）
2. 证据的真实性和可信度评估
3. 证据与案件争议焦点的关联度
4. 证据的潜在弱点或可被对方质疑的点
5. 补强建议

注意：引用法条时必须写明具体条款内容。"""

        try:
            result = llm_service.chat(prompt)
            all_analyses.append(result)
            _send_chunk(task_id, {"type": "content", "stage": "证据逐个分析",
                                  "content": f"第 {chunk_start + 1}-{chunk_end} 条证据分析完成\n\n{result[:500]}..."})
        except Exception as e:
            _send_chunk(task_id, {"type": "content", "stage": "证据逐个分析",
                                  "content": f"第 {chunk_start + 1}-{chunk_end} 条证据分析失败：{str(e)}"})

    return {"evidence_analysis": all_analyses, "total": total}


def _analyze_evidence_corroboration(task_id, task, case, db, results):
    """阶段3：证据交叉验证"""
    evidence_analysis = results.get("证据逐个分析", {})
    total = evidence_analysis.get("total", 0)

    _send_chunk(task_id, {"type": "content", "stage": "证据交叉验证",
                          "content": f"正在对 {total} 条证据进行交叉验证和关联性分析..."})

    prompt = f"""基于以下案件信息，请分析证据之间的交叉印证关系：

⚠️ 核心约束（必须遵守）：
1. 绝对禁止凭空编造法律条文或司法解释
2. 绝对禁止虚构不存在的案例
3. 不需要刻意讨好用户，说真话才是对用户最大的负责
4. 不确定时必须明确表达不确定性

案件：{case.title}
案由：{case.cause or '未填写'}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}

证据分析结果：
{str(evidence_analysis)[:5000]}

请分析：
1. 证据之间的相互印证关系
2. 证据链的完整性
3. 证据之间的矛盾或不一致
4. 关键证据缺失
5. 证据体系的整体强度评估

注意：引用法条时必须写明具体条款内容。"""

    try:
        result = llm_service.chat(prompt)
        _send_chunk(task_id, {"type": "content", "stage": "证据交叉验证", "content": result})
        return {"corroboration": result}
    except Exception as e:
        return {"corroboration": f"分析失败：{str(e)}"}


def _analyze_legal_application(task_id, task, case, db, results):
    """阶段4：法律适用分析"""
    _send_chunk(task_id, {"type": "content", "stage": "法律适用分析", "content": "正在分析法律适用..."})

    prompt = f"""请对以下案件进行法律适用分析：

⚠️ 核心约束（必须遵守）：
1. 绝对禁止凭空编造法律条文或司法解释，每条法律结论必须标注具体法条来源
2. 绝对禁止虚构不存在的案例，引用案例必须提供真实案号和法院
3. 不需要刻意讨好用户，说真话才是对用户最大的负责
4. 不确定时必须明确表达不确定性

💡 核心要求：
1. 深度思考推演，对每一个问题进行深度思考和推演
2. 突破性创造性的寻找更多真实途径
3. 让用户看到真相、理解真相

案件：{case.title}
案由：{case.cause or '未填写'}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}
诉讼金额：{case.claim_amount or '未填写'}
案件描述：{case.description or '未填写'}

请分析：
1. 适用的法律法规（必须写明具体法条）
2. 相关司法解释（必须写明具体解释）
3. 类似判例参考（必须提供真实案号和法院）
4. 法律适用的争议点
5. 各方的法律依据强弱

注意：每条法律结论必须标注具体法条来源。"""

    try:
        result = llm_service.chat(prompt)
        _send_chunk(task_id, {"type": "content", "stage": "法律适用分析", "content": result})
        return {"legal": result}
    except Exception as e:
        return {"legal": f"分析失败：{str(e)}"}


def _generate_strategy(task_id, task, case, db, results):
    """阶段5：诉讼策略生成"""
    _send_chunk(task_id, {"type": "content", "stage": "诉讼策略生成", "content": "正在制定诉讼策略..."})

    prompt = f"""请为以下案件制定详细的诉讼策略：

案件：{case.title}
案由：{case.cause or '未填写'}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}

请制定：
1. 总体诉讼策略
2. 各阶段的具体战术
3. 关键时间节点把握
4. 对方可能的策略预判
5. 应对方案
6. 调解/和解建议"""

    try:
        result = llm_service.chat(prompt)
        _send_chunk(task_id, {"type": "content", "stage": "诉讼策略生成", "content": result})
        return {"strategy": result}
    except Exception as e:
        return {"strategy": f"分析失败：{str(e)}"}


def _assess_risks(task_id, task, case, db, results):
    """阶段6：风险评估"""
    _send_chunk(task_id, {"type": "content", "stage": "风险评估", "content": "正在评估风险..."})

    prompt = f"""请对以下案件进行全面风险评估：

案件：{case.title}
案由：{case.cause or '未填写'}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}

请评估：
1. 诉讼风险（胜诉/败诉概率）
2. 证据风险
3. 法律适用风险
4. 时间风险
5. 经济风险
6. 声誉风险
7. 执行风险"""

    try:
        result = llm_service.chat(prompt)
        _send_chunk(task_id, {"type": "content", "stage": "风险评估", "content": result})
        return {"risk": result}
    except Exception as e:
        return {"risk": f"分析失败：{str(e)}"}


def _generate_comprehensive_report(task_id, task, case, db, results):
    """阶段7：综合报告"""
    _send_chunk(task_id, {"type": "content", "stage": "综合报告", "content": "正在生成综合分析报告..."})

    prompt = f"""请基于以下各阶段分析结果，生成一份完整的案件综合分析报告：

案件：{case.title}
案由：{case.cause or '未填写'}

各阶段分析：
{json.dumps({k: str(v)[:3000] for k, v in results.items()}, ensure_ascii=False, indent=2)[:10000]}

请生成：
1. 案件摘要
2. 核心争议焦点
3. 证据体系评估
4. 法律适用结论
5. 诉讼策略建议
6. 风险等级评定
7. 下一步行动建议"""

    try:
        result = llm_service.chat(prompt)
        _send_chunk(task_id, {"type": "content", "stage": "综合报告", "content": result})
        return {"comprehensive_report": result}
    except Exception as e:
        return {"comprehensive_report": f"分析失败：{str(e)}"}


def _run_custom_analysis(task_id, task, case, db, results):
    """自定义分析"""
    custom_prompt = task.get("custom_prompt", "请对案件进行全面分析")

    case_info = f"""案件：{case.title}
案由：{case.cause or '未填写'}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}"""

    prompt = f"""{case_info}

{custom_prompt}"""

    try:
        result = llm_service.chat(prompt)
        _send_chunk(task_id, {"type": "content", "stage": "自定义分析", "content": result})
        return {"custom": result}
    except Exception as e:
        return {"custom": f"分析失败：{str(e)}"}


@router.get("/{task_id}/stream")
async def stream_analysis(task_id: str, request: Request):
    """SSE 流式输出分析结果"""
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    async def event_generator():
        sent_count = 0
        while True:
            with _tasks_lock:
                chunks = list(_tasks.get(task_id, {}).get("chunks", []))
                current_task = _tasks.get(task_id)

            for chunk in chunks[sent_count:]:
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                sent_count += 1

            # 检查是否完成
            if not current_task:
                break
            if current_task["status"] in ("completed", "failed"):
                break

            # 等待新数据
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{task_id}/status")
def get_task_status(task_id: str):
    """获取任务状态"""
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "task_id": task["task_id"],
        "status": task["status"],
        "progress": task["progress"],
        "current_stage": task.get("current_stage", ""),
        "total_stages": task.get("total_stages", 0),
        "evidence_count": task.get("evidence_count", 0),
        "error": task.get("error"),
    }


@router.get("/{task_id}/result")
def get_task_result(task_id: str):
    """获取任务结果"""
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task["status"] != "completed":
        return {"status": task["status"], "progress": task["progress"], "result": None}
    return {"status": "completed", "result": task.get("result")}


@router.get("/case/{case_id}/history")
def get_case_analysis_history(case_id: int, db: Session = Depends(get_db)):
    """获取案件的历史分析记录"""
    records = db.query(AnalysisResult).filter(
        AnalysisResult.case_id == case_id
    ).order_by(AnalysisResult.created_at.desc()).all()
    return {
        "case_id": case_id,
        "total": len(records),
        "analyses": [r.to_dict() for r in records]
    }


@router.get("/record/{record_id}")
def get_analysis_record(record_id: int, db: Session = Depends(get_db)):
    """获取特定分析记录的完整内容"""
    record = db.query(AnalysisResult).filter(AnalysisResult.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return record.to_dict()


@router.delete("/record/{record_id}")
def delete_analysis_record(record_id: int, db: Session = Depends(get_db)):
    """删除分析记录"""
    record = db.query(AnalysisResult).filter(AnalysisResult.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "分析记录已删除"}
