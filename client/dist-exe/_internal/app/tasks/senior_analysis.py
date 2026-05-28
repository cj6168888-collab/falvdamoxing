"""
资深律师分析 - 异步任务处理器
"""
from app.api.ai_tasks import register_task_handler, _update_task
from app.db.database import SessionLocal
from app.models.case import Case
from datetime import datetime


@register_task_handler("senior_analysis")
def handle_senior_analysis(task_id: str, task: dict):
    """异步资深律师分析"""
    from app.services.senior_lawyer_engine import senior_lawyer_engine

    db = SessionLocal()
    try:
        params = task.get("params", {})
        case_id = task["case_id"]
        depth = params.get("depth", params.get("analysis_level", "standard"))

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            _update_task(task_id, status="failed", error="案件不存在", completed_at=datetime.now().isoformat())
            return

        _update_task(task_id, progress=0.1, message="正在读取案件信息...")
        _update_task(task_id, progress=0.35, message="正在执行资深律师分析...")

        result = senior_lawyer_engine.analyze_case(
            case_id=case_id,
            analysis_level=depth,
        )
        result["analysis_level"] = depth

        if result.get("status") == "error":
            _update_task(
                task_id,
                status="failed",
                error=result.get("message", "分析失败"),
                message=result.get("message", "分析失败"),
                completed_at=datetime.now().isoformat(),
            )
            return

        _update_task(task_id, progress=0.95, message="正在生成完整分析报告...")

        _update_task(task_id, progress=1.0, message="分析完成", status="completed",
                     result=result, completed_at=datetime.now().isoformat())
    except Exception as e:
        _update_task(task_id, status="failed", error=str(e),
                     message=f"分析失败: {str(e)}", completed_at=datetime.now().isoformat())
    finally:
        db.close()
