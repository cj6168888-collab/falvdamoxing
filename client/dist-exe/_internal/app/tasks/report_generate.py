"""
报告生成 - 异步任务处理器
"""
from app.api.ai_tasks import register_task_handler, _update_task
from app.db.database import SessionLocal
from app.models.case import Case
from datetime import datetime


@register_task_handler("report_generate")
def handle_report_generate(task_id: str, task: dict):
    """异步生成报告"""
    from app.services.streaming_report import get_streaming_report_generator, ReportType
    from app.services.llm_service import llm_service
    from app.api.report_api import _build_full_case_context

    db = SessionLocal()
    try:
        params = task.get("params", {})
        case_id = task["case_id"]
        report_type_str = params.get("report_type", "analysis")

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            _update_task(task_id, status="failed", error="案件不存在", completed_at=datetime.now().isoformat())
            return

        # 映射报告类型
        type_map = {
            "case_analysis": ReportType.ANALYSIS,
            "litigation_strategy": ReportType.STRATEGY,
            "full_analysis": ReportType.FULL_ANALYSIS,
            "evidence_report": ReportType.EVIDENCE_REPORT,
            "milestone_report": ReportType.MILESTONE_REPORT,
            "opponent_analysis": ReportType.ANALYSIS,
        }
        report_type = type_map.get(report_type_str, ReportType.ANALYSIS)

        _update_task(task_id, progress=0.05, message="正在读取案件数据...")

        # 构建完整案件上下文
        case_info = _build_full_case_context(case_id, db)

        _update_task(task_id, progress=0.15, message="正在初始化报告生成器...")

        # 获取报告生成器
        generator = get_streaming_report_generator(llm_service)

        _update_task(task_id, progress=0.25, message="正在生成报告...")

        # 生成报告（同步调用，因为 streaming_report 内部已有分段逻辑）
        content = generator.generate_report(
            case_id=case_id,
            report_type=report_type,
            case_info=case_info,
            force_regenerate=True,
        )

        _update_task(task_id, progress=0.9, message="正在整理报告...")

        # 获取任务状态
        task_status = generator.get_task_status(case_id, report_type)

        result = {
            "report_type": report_type_str,
            "content": content,
            "case_id": case_id,
            "segments_completed": task_status.get("segments_completed", 0) if task_status else 0,
            "total_segments": task_status.get("total_segments", 0) if task_status else 0,
        }

        _update_task(task_id, progress=1.0, message="报告生成完成", status="completed",
                     result=result, completed_at=datetime.now().isoformat())
    except Exception as e:
        _update_task(task_id, status="failed", error=str(e),
                     message=f"报告生成失败: {str(e)}", completed_at=datetime.now().isoformat())
    finally:
        db.close()
