"""
对抗分析 - 异步任务处理器
"""
import traceback
from app.api.ai_tasks import register_task_handler, _update_task
from app.db.database import SessionLocal
from app.models.case import Case
from datetime import datetime


@register_task_handler("adversarial")
def handle_adversarial(task_id: str, task: dict):
    """异步对抗分析"""
    from app.services.llm_service import llm_service

    db = SessionLocal()
    
    # 用于追踪LLM内部的进度
    last_progress = [0.0]
    
    def progress_callback(stage_name: str, progress: float):
        """LLM内部进度回调 - 将LLM进度映射到整体进度"""
        # LLM进度范围是 0.0-1.0，映射到整体进度的 0.35-0.75
        llm_progress = progress
        mapped_progress = 0.35 + (llm_progress * 0.40)
        last_progress[0] = mapped_progress
        _update_task(task_id, progress=mapped_progress, message=f"AI分析: {stage_name}")
    
    try:
        params = task.get("params", {})
        case_id = task["case_id"]

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            _update_task(task_id, status="failed", error="案件不存在", completed_at=datetime.now().isoformat())
            return

        # 阶段0: 准备阶段
        _update_task(task_id, progress=0.05, message="正在初始化分析环境...")

        case_info = f"""【案件基本信息】
案件名称：{case.title}
案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}
案号：{case.case_number or '暂无'}
原告：{case.plaintiff or '未填写'}
被告：{case.defendant or '未填写'}
第三人：{case.third_party or '无'}
案由：{case.cause or '未填写'}
诉讼金额：{case.claim_amount or '未填写'}
案件描述：{case.description or '未填写'}
补充说明：{case.supplement or '无'}
"""
        if case.legal_analysis:
            case_info += f"\n【已有法律分析】\n{case.legal_analysis}\n"

        # 阶段1: 数据收集
        _update_task(task_id, progress=0.1, message="正在收集案件信息...")
        
        # 尝试获取证据信息
        try:
            from app.services.evidence_v2 import evidence_service_v2
            our_evidence = evidence_service_v2.get_evidence_full_content(case_id)
            if not our_evidence or len(our_evidence) < 50:
                our_evidence = params.get("our_evidence", "")
        except Exception as e:
            print(f"[adversarial] 获取证据失败: {e}")
            our_evidence = params.get("our_evidence", "")

        opponent_evidence = params.get("opponent_evidence", "")
        phase = params.get("phase", "litigation")

        # 阶段2: 准备分析
        _update_task(task_id, progress=0.15, message="正在准备分析参数...")
        
        _update_task(task_id, progress=0.2, message="正在启动AI分析引擎...")
        
        _update_task(task_id, progress=0.25, message="正在进行第一轮对抗分析...")

        # 阶段3: 第二轮分析
        _update_task(task_id, progress=0.3, message="正在进行防守策略分析...")

        # 调用 LLM 进行分析（传递进度回调）
        result = llm_service.full_adversarial_analysis(
            case_info=case_info,
            our_evidence=our_evidence,
            opponent_evidence=opponent_evidence,
            current_phase=phase,
            max_rounds=3,  # 减少推演轮数，加快速度
            progress_callback=progress_callback,
        )

        # 阶段4: 保存结果
        _update_task(task_id, progress=0.85, message="正在保存分析结果...")

        _update_task(task_id, progress=1.0, message="对抗分析完成", status="completed",
                     result={
                         "case_id": case_id,
                         "analysis": result,
                         "phase": phase,
                     },
                     completed_at=datetime.now().isoformat())
    except Exception as e:
        error_detail = str(e)
        print(f"[adversarial] 分析失败: {error_detail}")
        print(f"[adversarial] Traceback: {traceback.format_exc()}")
        _update_task(task_id, status="failed", error=error_detail,
                     message=f"对抗分析失败: {error_detail}", completed_at=datetime.now().isoformat())
    finally:
        db.close()
