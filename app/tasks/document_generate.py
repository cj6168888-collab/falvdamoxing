"""
文书生成 - 异步任务处理器
"""
from app.api.ai_tasks import register_task_handler, _update_task
from app.db.database import SessionLocal
from datetime import datetime


@register_task_handler("document_generate")
def handle_document_generate(task_id: str, task: dict):
    """异步生成文书"""
    from app.api.document import document_generator
    from app.models.case import Case

    db = SessionLocal()
    try:
        params = task.get("params", {})
        case_id = task["case_id"]
        doc_type = params.get("document_type", params.get("type", "custom"))
        requirements = params.get("custom_requirements", params.get("prompt", ""))

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            _update_task(task_id, status="failed", error="案件不存在", completed_at=datetime.now().isoformat())
            return

        _update_task(task_id, progress=0.1, message="正在读取案件信息...")

        case_data = {
            "id": case.id,
            "title": case.title,
            "case_type": case.case_type,
            "case_number": case.case_number,
            "plaintiff": case.plaintiff,
            "defendant": case.defendant,
            "third_party": case.third_party,
            "cause": case.cause,
            "claim_amount": case.claim_amount,
            "description": case.description,
            "supplement": case.supplement,
            "legal_analysis": case.legal_analysis,
        }

        _update_task(task_id, progress=0.3, message=f"正在构建{doc_type}框架...")

        content = document_generator.generate(
            document_type=doc_type,
            case_data=case_data,
            custom_requirements=requirements,
            db=db,
        )

        _update_task(task_id, progress=0.8, message="正在校对格式与引用...")

        # 保存文书到数据库
        from app.models.document import Document
        doc = Document(
            case_id=case_id,
            filename=f"{doc_type}_{datetime.now().strftime('%Y%m%d')}",
            file_type="text",
            doc_type=doc_type,
            content=content,
            content_summary=content[:200] if content else "",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        _update_task(task_id, progress=1.0, message="文书生成完成", status="completed",
                     result={
                         "document_id": doc.id,
                         "document_type": doc_type,
                         "content": content,
                         "title": doc.filename,
                     },
                     completed_at=datetime.now().isoformat())
    except Exception as e:
        _update_task(task_id, status="failed", error=str(e),
                     message=f"文书生成失败: {str(e)}", completed_at=datetime.now().isoformat())
    finally:
        db.close()
