"""
执行跟踪服务 - 判决生效后的强制执行程序管理
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.execution import (
    ExecutionRecord, ExecutionTask, ExecutionAsset, ExecutionStage as ExecutionStageModel,
    ExecutionStageEnum, TaskPriority, TaskStatus, AssetType
)
from app.models.case import Case, ExecutionTracking
from app.services.llm_service import llm_service


class ExecutionService:
    """执行跟踪服务"""

    @staticmethod
    def _safe_execution_value(value, fallback: str = "待填写") -> str:
        """Avoid leaking audit placeholders into generated legal documents."""
        if value is None:
            return fallback
        text = str(value).strip()
        if not text or "审计临时" in text or text == "0":
            return fallback
        return text

    def get_execution_overview(self, db: Session, case_id: int) -> Dict:
        """获取执行跟踪概览"""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("案件不存在")

        legacy_tracking = db.query(ExecutionTracking).filter(
            ExecutionTracking.case_id == case_id
        ).first()

        records = db.query(ExecutionRecord).filter(
            ExecutionRecord.case_id == case_id
        ).order_by(ExecutionRecord.record_date.desc()).all()

        tasks = db.query(ExecutionTask).filter(
            ExecutionTask.case_id == case_id
        ).all()

        assets = db.query(ExecutionAsset).filter(
            ExecutionAsset.case_id == case_id
        ).all()

        stages = db.query(ExecutionStageModel).filter(
            ExecutionStageModel.case_id == case_id
        ).order_by(ExecutionStageModel.created_at.asc()).all()

        todo_tasks = len([t for t in tasks if (t.status.value if hasattr(t.status, 'value') else str(t.status)) == TaskStatus.TODO.value])
        in_progress_tasks = len([t for t in tasks if (t.status.value if hasattr(t.status, 'value') else str(t.status)) == TaskStatus.IN_PROGRESS.value])
        completed_tasks = len([t for t in tasks if (t.status.value if hasattr(t.status, 'value') else str(t.status)) == TaskStatus.COMPLETED.value])

        controlled_assets = len([a for a in assets if (a.status or "discovered") == "controlled"])
        disposed_assets = len([a for a in assets if (a.status or "discovered") == "disposed"])

        current_stage = None
        for s in reversed(stages):
            if (s.status or "pending") == "active":
                current_stage = (s.stage.value if hasattr(s.stage, 'value') else str(s.stage))
                break

        status = None
        if legacy_tracking:
            status = legacy_tracking.status
        elif case.execution_status:
            status = case.execution_status
        else:
            status = "pending"

        return {
            "case_id": case_id,
            "case_title": case.title,
            "case_number": case.case_number,
            "execution_case_number": legacy_tracking.execution_case_number if legacy_tracking else case.execution_case_number,
            "execution_court": legacy_tracking.execution_court if legacy_tracking else None,
            "executor_name": legacy_tracking.executor_name if legacy_tracking else None,
            "executor_phone": legacy_tracking.executor_phone if legacy_tracking else None,
            "execution_amount": legacy_tracking.execution_amount if legacy_tracking else case.claim_amount,
            "executed_amount": legacy_tracking.executed_amount if legacy_tracking else None,
            "remaining_amount": legacy_tracking.remaining_amount if legacy_tracking else None,
            "status": status,
            "progress": legacy_tracking.progress if legacy_tracking else case.execution_progress,
            "current_stage": current_stage,
            "total_records": len(records),
            "total_tasks": len(tasks),
            "todo_tasks": todo_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completed_tasks": completed_tasks,
            "total_assets": len(assets),
            "controlled_assets": controlled_assets,
            "disposed_assets": disposed_assets,
            "next_follow_up": legacy_tracking.next_follow_up.isoformat() if legacy_tracking and legacy_tracking.next_follow_up else None,
            "assistance_needed": legacy_tracking.assistance_needed if legacy_tracking else None,
            "stages": [self._stage_to_dict(s) for s in stages],
        }

    def update_execution_overview(self, db: Session, case_id: int, data: Dict) -> Dict:
        """更新执行跟踪概览"""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("案件不存在")

        legacy_tracking = db.query(ExecutionTracking).filter(
            ExecutionTracking.case_id == case_id
        ).first()

        if not legacy_tracking:
            legacy_tracking = ExecutionTracking(case_id=case_id)
            db.add(legacy_tracking)

        updatable_fields = [
            "execution_case_number", "execution_court", "executor_name", "executor_phone",
            "execution_amount", "executed_amount", "remaining_amount", "status", "progress",
            "records", "assistance_needed", "assistance_status", "next_follow_up",
        ]

        for field in updatable_fields:
            if field in data and data[field] is not None:
                setattr(legacy_tracking, field, data[field])

        if "status" in data and data["status"]:
            case.execution_status = data["status"]
        if "progress" in data and data["progress"] is not None:
            case.execution_progress = data["progress"]

        db.commit()
        db.refresh(legacy_tracking)

        return self.get_execution_overview(db, case_id)

    def get_execution_records(self, db: Session, case_id: int) -> List[Dict]:
        """获取执行记录列表"""
        records = db.query(ExecutionRecord).filter(
            ExecutionRecord.case_id == case_id
        ).order_by(ExecutionRecord.record_date.desc()).all()

        return [self._record_to_dict(r) for r in records]

    def create_execution_record(self, db: Session, case_id: int, data: Dict) -> Dict:
        """创建执行记录"""
        record_date = data.get("record_date")
        if record_date and isinstance(record_date, str):
            record_date = datetime.fromisoformat(record_date.replace("Z", "+00:00"))

        record = ExecutionRecord(
            case_id=case_id,
            record_date=record_date or datetime.utcnow(),
            record_type=data.get("record_type"),
            title=data.get("title", ""),
            content=data.get("content"),
            result=data.get("result"),
            court_name=data.get("court_name"),
            judge_name=data.get("judge_name"),
            document_number=data.get("document_number"),
            stage=ExecutionStageEnum(data["stage"]) if data.get("stage") else None,
            progress=data.get("progress", 0.0),
            attachments=data.get("attachments"),
        )

        db.add(record)
        db.commit()
        db.refresh(record)
        return self._record_to_dict(record)

    def update_execution_record(self, db: Session, record_id: int, data: Dict) -> Optional[Dict]:
        """更新执行记录"""
        record = db.query(ExecutionRecord).filter(ExecutionRecord.id == record_id).first()
        if not record:
            return None

        updatable_fields = [
            "record_date", "record_type", "title", "content", "result",
            "court_name", "judge_name", "document_number", "stage", "progress", "attachments",
        ]

        for field in updatable_fields:
            if field in data and data[field] is not None:
                if field == "stage" and data[field]:
                    setattr(record, field, ExecutionStageEnum(data[field]))
                elif field == "record_date" and isinstance(data[field], str):
                    setattr(record, field, datetime.fromisoformat(data[field].replace("Z", "+00:00")))
                else:
                    setattr(record, field, data[field])

        db.commit()
        db.refresh(record)
        return self._record_to_dict(record)

    def delete_execution_record(self, db: Session, record_id: int) -> bool:
        """删除执行记录"""
        record = db.query(ExecutionRecord).filter(ExecutionRecord.id == record_id).first()
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True

    def get_execution_tasks(self, db: Session, case_id: int) -> List[Dict]:
        """获取执行任务列表"""
        tasks = db.query(ExecutionTask).filter(
            ExecutionTask.case_id == case_id
        ).order_by(
            ExecutionTask.status.asc(),
            ExecutionTask.priority.asc(),
            ExecutionTask.due_date.asc()
        ).all()

        return [self._task_to_dict(t) for t in tasks]

    def create_execution_task(self, db: Session, case_id: int, data: Dict) -> Dict:
        """创建执行任务"""
        due_date = data.get("due_date")
        if due_date and isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))

        task = ExecutionTask(
            case_id=case_id,
            title=data.get("title", ""),
            description=data.get("description"),
            task_type=data.get("task_type"),
            stage=ExecutionStageEnum(data["stage"]) if data.get("stage") else None,
            priority=TaskPriority(data.get("priority", "medium")),
            status=TaskStatus(data.get("status", "todo")),
            due_date=due_date,
            assignee=data.get("assignee"),
            related_record_id=data.get("related_record_id"),
            related_asset_id=data.get("related_asset_id"),
            notes=data.get("notes"),
        )

        db.add(task)
        db.commit()
        db.refresh(task)
        return self._task_to_dict(task)

    def update_execution_task(self, db: Session, task_id: int, data: Dict) -> Optional[Dict]:
        """更新执行任务"""
        task = db.query(ExecutionTask).filter(ExecutionTask.id == task_id).first()
        if not task:
            return None

        updatable_fields = [
            "title", "description", "task_type", "stage", "priority", "status",
            "due_date", "completed_date", "assignee", "related_record_id",
            "related_asset_id", "notes",
        ]

        for field in updatable_fields:
            if field in data and data[field] is not None:
                if field == "stage" and data[field]:
                    setattr(task, field, ExecutionStageEnum(data[field]))
                elif field == "priority" and data[field]:
                    setattr(task, field, TaskPriority(data[field]))
                elif field == "status" and data[field]:
                    setattr(task, field, TaskStatus(data[field]))
                    if data[field] == "completed" and not task.completed_date:
                        task.completed_date = datetime.utcnow()
                elif field in ("due_date", "completed_date") and isinstance(data[field], str):
                    setattr(task, field, datetime.fromisoformat(data[field].replace("Z", "+00:00")))
                else:
                    setattr(task, field, data[field])

        db.commit()
        db.refresh(task)
        return self._task_to_dict(task)

    def delete_execution_task(self, db: Session, task_id: int) -> bool:
        """删除执行任务"""
        task = db.query(ExecutionTask).filter(ExecutionTask.id == task_id).first()
        if not task:
            return False
        db.delete(task)
        db.commit()
        return True

    def get_execution_assets(self, db: Session, case_id: int) -> List[Dict]:
        """获取财产线索列表"""
        assets = db.query(ExecutionAsset).filter(
            ExecutionAsset.case_id == case_id
        ).order_by(ExecutionAsset.created_at.desc()).all()

        return [self._asset_to_dict(a) for a in assets]

    def create_execution_asset(self, db: Session, case_id: int, data: Dict) -> Dict:
        """创建财产线索"""
        source_date = data.get("source_date")
        if source_date and isinstance(source_date, str):
            source_date = datetime.fromisoformat(source_date.replace("Z", "+00:00"))

        control_date = data.get("control_date")
        if control_date and isinstance(control_date, str):
            control_date = datetime.fromisoformat(control_date.replace("Z", "+00:00"))

        disposal_date = data.get("disposal_date")
        if disposal_date and isinstance(disposal_date, str):
            disposal_date = datetime.fromisoformat(disposal_date.replace("Z", "+00:00"))

        asset = ExecutionAsset(
            case_id=case_id,
            asset_type=AssetType(data["asset_type"]) if data.get("asset_type") else AssetType.OTHER,
            asset_name=data.get("asset_name", ""),
            description=data.get("description"),
            estimated_value=data.get("estimated_value"),
            actual_value=data.get("actual_value"),
            location=data.get("location"),
            identifier=data.get("identifier"),
            status=data.get("status", "discovered"),
            control_method=data.get("control_method"),
            control_date=control_date,
            disposal_method=data.get("disposal_method"),
            disposal_date=disposal_date,
            disposal_result=data.get("disposal_result"),
            source=data.get("source"),
            source_date=source_date,
            notes=data.get("notes"),
        )

        db.add(asset)
        db.commit()
        db.refresh(asset)
        return self._asset_to_dict(asset)

    def delete_execution_asset(self, db: Session, asset_id: int) -> bool:
        """删除财产线索"""
        asset = db.query(ExecutionAsset).filter(ExecutionAsset.id == asset_id).first()
        if not asset:
            return False
        db.delete(asset)
        db.commit()
        return True

    def get_execution_stages(self, db: Session, case_id: int) -> List[Dict]:
        """获取执行阶段"""
        stages = db.query(ExecutionStageModel).filter(
            ExecutionStageModel.case_id == case_id
        ).order_by(ExecutionStageModel.created_at.asc()).all()

        return [self._stage_to_dict(s) for s in stages]

    def generate_execution_application(self, db: Session, case_id: int) -> Dict:
        """起草执行申请书草稿，提交或发送前必须人工核验。"""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("案件不存在")

        legacy_tracking = db.query(ExecutionTracking).filter(
            ExecutionTracking.case_id == case_id
        ).first()

        assets = db.query(ExecutionAsset).filter(
            ExecutionAsset.case_id == case_id,
            ExecutionAsset.status.in_(["confirmed", "controlled"])
        ).all()

        try:
            from app.models.evidence import EvidenceItem
            evidence_count = db.query(func.count(EvidenceItem.id)).filter(
                EvidenceItem.case_id == case_id
            ).scalar() or 0
        except Exception:
            evidence_count = 0

        try:
            from app.models.letter import Letter
            letter_count = db.query(func.count(Letter.id)).filter(
                Letter.case_id == case_id
            ).scalar() or 0
        except Exception:
            letter_count = 0

        assets_text = "\n".join([
            f"- {a.asset_name}: {a.asset_type.value if a.asset_type and hasattr(a.asset_type, 'value') else str(a.asset_type or '未知')}, 估值: {a.estimated_value or '未知'}, 状态: {a.status}"
            for a in assets
        ]) if assets else "暂未发现财产线索"

        execution_case_number = self._safe_execution_value(
            legacy_tracking.execution_case_number if legacy_tracking else case.execution_case_number
        )
        execution_court = self._safe_execution_value(
            legacy_tracking.execution_court if legacy_tracking else None
        )
        execution_amount = self._safe_execution_value(
            legacy_tracking.execution_amount if legacy_tracking else case.claim_amount,
            fallback=case.claim_amount or "待填写"
        )
        executed_amount = self._safe_execution_value(
            legacy_tracking.executed_amount if legacy_tracking else None,
            fallback="0"
        )

        prompt = f"""请根据以下案件信息，起草一份强制执行申请书草稿。

【案件基本信息】
- 案件名称：{case.title}
- 案由：{case.cause or '未填写'}
- 案号：{case.case_number or '未填写'}
- 申请人/我方主体：{case.plaintiff or '陈靖、佛山吉麟相关主体（以生效文书为准）'}
- 被申请人/对方主体：{case.defendant or '雷天乾、博凯升华、博凯健康相关主体（以生效文书为准）'}
- 第三人：{case.third_party or '无'}
- 诉讼金额：{case.claim_amount or '未填写'}
- 案件描述：{case.description or '未填写'}
- 补充说明：{case.supplement or '无'}
- 系统证据链数量：{evidence_count} 条
- 系统函件/往来记录数量：{letter_count} 封

【执行信息】
- 执行案号：{execution_case_number}
- 执行法院：{execution_court}
- 执行标的金额：{execution_amount}
- 已执行金额：{executed_amount}

【已发现的财产线索】
{assets_text}

【结案结果】
{case.closure_result or '未填写'}

请按照标准强制执行申请书格式起草草稿，包含：
1. 申请人信息
2. 被执行人信息
3. 执行请求
4. 事实与理由
5. 财产线索
6. 此致（执行法院）
7. 申请人及日期

要求：
1. 必须紧扣本案主体和案件名称，不得写成通用空模板；
2. 必须体现系统已有证据链与函件记录可作为执行申请附件或履行催告、财产线索补充依据；
3. 如执行法院、案号、金额尚未确定，可以用【待核实/按生效法律文书填写】占位，但不得编造不存在的法院、案号或金额；
4. 不得引用未经核验的案例号或虚构裁判文书号；
5. 输出开头必须标注“AI 草稿，待人工核验”；
6. 末尾必须附“提交前核验清单”，至少包含生效法律文书、执行法院、案号、主体身份、金额计算、履行情况、财产线索、附件目录、签名盖章和日期；
7. 格式规范、请求明确，法律依据仅作为待核验引用，不得表达为已完成律师最终审查。"""

        content = llm_service.chat([
            {"role": "system", "content": "你是一位资深执行律师，正在协助起草强制执行申请书工作底稿。输出必须保持草稿定位，提示提交前逐项人工核验，不得将结果表述为可直接提交的最终文书。"},
            {"role": "user", "content": prompt}
        ], model="qwen-plus")

        return {
            "case_id": case_id,
            "application": content,
            "document_status": "AI 草稿，待人工核验",
            "requires_human_review": True,
            "review_checklist": [
                "生效法律文书及履行期限",
                "执行法院和执行案号",
                "申请人、被执行人主体身份",
                "申请执行金额、利息和迟延履行金计算",
                "已履行或部分履行情况",
                "财产线索来源和可核验材料",
                "证据及附件目录",
                "签名盖章、日期和授权手续",
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_execution_statistics(self, db: Session, case_id: int) -> Dict:
        """获取执行统计"""
        records = db.query(ExecutionRecord).filter(ExecutionRecord.case_id == case_id).count()
        tasks = db.query(ExecutionTask).filter(ExecutionTask.case_id == case_id).all()
        assets = db.query(ExecutionAsset).filter(ExecutionAsset.case_id == case_id).all()

        return {
            "case_id": case_id,
            "total_records": records,
            "total_tasks": len(tasks),
            "tasks_by_status": {
                status.value: len([t for t in tasks if (t.status.value if hasattr(t.status, 'value') else str(t.status)) == status.value])
                for status in TaskStatus
            },
            "total_assets": len(assets),
            "assets_by_status": {
                status: len([a for a in assets if (a.status or "discovered") == status])
                for status in ["discovered", "confirmed", "controlled", "disposed"]
            },
        }

    def _record_to_dict(self, record: ExecutionRecord) -> Dict:
        return {
            "id": record.id,
            "case_id": record.case_id,
            "record_date": record.record_date.isoformat() if record.record_date else None,
            "record_type": record.record_type,
            "title": record.title,
            "content": record.content,
            "result": record.result,
            "court_name": record.court_name,
            "judge_name": record.judge_name,
            "document_number": record.document_number,
            "stage": record.stage.value if record.stage and hasattr(record.stage, 'value') else str(record.stage) if record.stage else None,
            "progress": record.progress,
            "attachments": record.attachments,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }

    def _task_to_dict(self, task: ExecutionTask) -> Dict:
        return {
            "id": task.id,
            "case_id": task.case_id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "stage": task.stage.value if task.stage and hasattr(task.stage, 'value') else str(task.stage) if task.stage else None,
            "priority": task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
            "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "completed_date": task.completed_date.isoformat() if task.completed_date else None,
            "assignee": task.assignee,
            "related_record_id": task.related_record_id,
            "related_asset_id": task.related_asset_id,
            "notes": task.notes,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    def _asset_to_dict(self, asset: ExecutionAsset) -> Dict:
        return {
            "id": asset.id,
            "case_id": asset.case_id,
            "asset_type": asset.asset_type.value if asset.asset_type and hasattr(asset.asset_type, 'value') else str(asset.asset_type) if asset.asset_type else None,
            "asset_name": asset.asset_name,
            "description": asset.description,
            "estimated_value": asset.estimated_value,
            "actual_value": asset.actual_value,
            "location": asset.location,
            "identifier": asset.identifier,
            "status": asset.status,
            "control_method": asset.control_method,
            "control_date": asset.control_date.isoformat() if asset.control_date else None,
            "disposal_method": asset.disposal_method,
            "disposal_date": asset.disposal_date.isoformat() if asset.disposal_date else None,
            "disposal_result": asset.disposal_result,
            "source": asset.source,
            "source_date": asset.source_date.isoformat() if asset.source_date else None,
            "notes": asset.notes,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
        }

    def _stage_to_dict(self, stage: ExecutionStageModel) -> Dict:
        return {
            "id": stage.id,
            "case_id": stage.case_id,
            "stage": stage.stage.value if hasattr(stage.stage, 'value') else str(stage.stage),
            "stage_name": stage.stage_name,
            "start_date": stage.start_date.isoformat() if stage.start_date else None,
            "end_date": stage.end_date.isoformat() if stage.end_date else None,
            "status": stage.status,
            "description": stage.description,
            "requirements": stage.requirements,
            "completed_items": stage.completed_items,
            "documents": stage.documents,
            "notes": stage.notes,
            "created_at": stage.created_at.isoformat() if stage.created_at else None,
            "updated_at": stage.updated_at.isoformat() if stage.updated_at else None,
        }


execution_service = ExecutionService()
