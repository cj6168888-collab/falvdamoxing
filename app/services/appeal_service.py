"""
上诉流程服务 - 第二审程序的完整流程管理
包括：上诉准备、上诉材料、上诉节点追踪、答辩策略等
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.appeal import (
    AppealRecord, AppealType, AppealReason, AppealStatus,
    AppealDeadline, AppealArgument, AppealDocument, SecondTrialStrategy
)
from app.models.case import Case
from app.services.deadline_service import deadline_service
from app.services.llm_service import llm_service


class AppealService:
    """上诉流程服务"""

    def get_appeals_by_case(self, db: Session, case_id: int) -> List[Dict]:
        """获取案件所有上诉记录"""
        records = db.query(AppealRecord).filter(
            AppealRecord.case_id == case_id
        ).order_by(AppealRecord.created_at.desc()).all()

        return [self._appeal_to_dict(r, db) for r in records]

    def get_appeal(self, db: Session, appeal_id: int) -> Optional[Dict]:
        """获取上诉详情"""
        record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
        if not record:
            return None
        return self._appeal_to_dict(record, db)

    def create_appeal(self, db: Session, case_id: int, data: Dict) -> Dict:
        """创建上诉记录"""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("案件不存在")

        judgment_received = data.get("judgment_received_date")
        if judgment_received and isinstance(judgment_received, str):
            judgment_received = datetime.fromisoformat(judgment_received.replace("Z", "+00:00"))

        appeal_deadline_date = None
        days_remaining = None
        if judgment_received:
            appeal_deadline_date = judgment_received + timedelta(days=15)
            now = datetime.utcnow()
            days_remaining = max(0, (appeal_deadline_date - now).days)

        record = AppealRecord(
            case_id=case_id,
            appeal_type=AppealType(data.get("appeal_type", "first_to_second")),
            appeal_reason=AppealReason(data.get("appeal_reason", "legal_error")),
            original_case_number=data.get("original_case_number"),
            original_court=data.get("original_court"),
            original_judge=data.get("original_judge"),
            original_judgment_date=data.get("original_judgment_date"),
            original_judgment_content=data.get("original_judgment_content"),
            appellant_type=data.get("appellant_type"),
            appellant_name=data.get("appellant_name"),
            judgment_received_date=judgment_received,
            appeal_deadline=appeal_deadline_date,
            status=AppealStatus.PREPARING,
            days_remaining=days_remaining,
            is_overdue=(days_remaining is not None and days_remaining <= 0),
            appeal_petition=data.get("appeal_petition"),
            appeal_facts=data.get("appeal_facts"),
            new_evidence_list=data.get("new_evidence_list"),
            original_evidence_used=data.get("original_evidence_used"),
            appeal_requests=data.get("appeal_requests"),
            original_requests=data.get("original_requests"),
            modified_requests=data.get("modified_requests"),
            grounds_of_appeal=data.get("grounds_of_appeal"),
            opposing_arguments=data.get("opposing_arguments"),
            key_disputes=data.get("key_disputes"),
            strategy=data.get("strategy"),
            key_arguments=data.get("key_arguments"),
            evidence_plan=data.get("evidence_plan"),
            milestones=data.get("milestones"),
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        self._auto_create_deadlines(db, record.id, judgment_received, appeal_deadline_date)

        return self._appeal_to_dict(record, db)

    def update_appeal(self, db: Session, appeal_id: int, data: Dict) -> Optional[Dict]:
        """更新上诉记录"""
        record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
        if not record:
            return None

        updatable_fields = [
            "appeal_type", "appeal_reason", "original_case_number", "original_court",
            "original_judge", "original_judgment_date", "original_judgment_content",
            "appellant_type", "appellant_name", "judgment_received_date",
            "appeal_submitted_date", "appeal_accepted_date", "hearing_date",
            "appeal_decision_date", "status", "appeal_petition", "appeal_facts",
            "new_evidence_list", "original_evidence_used", "appeal_requests",
            "original_requests", "modified_requests", "grounds_of_appeal",
            "opposing_arguments", "key_disputes", "strategy", "key_arguments",
            "evidence_plan", "milestones", "decision", "decision_type", "favorable_outcome",
        ]

        for field in updatable_fields:
            if field in data and data[field] is not None:
                if field in ("appeal_type",):
                    setattr(record, field, AppealType(data[field]))
                elif field in ("appeal_reason",):
                    setattr(record, field, AppealReason(data[field]))
                elif field in ("status",):
                    setattr(record, field, AppealStatus(data[field]))
                else:
                    setattr(record, field, data[field])

        if "judgment_received_date" in data and data["judgment_received_date"]:
            jrd = data["judgment_received_date"]
            if isinstance(jrd, str):
                jrd = datetime.fromisoformat(jrd.replace("Z", "+00:00"))
            record.appeal_deadline = jrd + timedelta(days=15)
            now = datetime.utcnow()
            record.days_remaining = max(0, (record.appeal_deadline - now).days)
            record.is_overdue = record.days_remaining <= 0

        db.commit()
        db.refresh(record)
        return self._appeal_to_dict(record, db)

    def delete_appeal(self, db: Session, appeal_id: int) -> bool:
        """删除上诉记录"""
        record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True

    def get_appeal_arguments(self, db: Session, case_id: int) -> List[Dict]:
        """获取案件上诉论点列表"""
        records = db.query(AppealRecord).filter(AppealRecord.case_id == case_id).all()
        record_ids = [r.id for r in records]

        if not record_ids:
            return []

        arguments = db.query(AppealArgument).filter(
            AppealArgument.appeal_record_id.in_(record_ids)
        ).order_by(AppealArgument.created_at.desc()).all()

        return [self._argument_to_dict(a) for a in arguments]

    def create_appeal_argument(self, db: Session, case_id: int, data: Dict) -> Optional[Dict]:
        """创建上诉论点"""
        appeal_record_id = data.get("appeal_record_id")
        if not appeal_record_id:
            records = db.query(AppealRecord).filter(
                AppealRecord.case_id == case_id
            ).order_by(AppealRecord.created_at.desc()).first()
            if not records:
                raise ValueError("该案件没有上诉记录，请先创建上诉记录")
            appeal_record_id = records.id

        argument = AppealArgument(
            appeal_record_id=appeal_record_id,
            argument_type=data.get("argument_type", "legal_error"),
            title=data.get("title", ""),
            description=data.get("description"),
            original_finding=data.get("original_finding"),
            appeal_finding=data.get("appeal_finding"),
            discrepancy=data.get("discrepancy"),
            supporting_evidence=data.get("supporting_evidence"),
            counter_evidence=data.get("counter_evidence"),
            legal_basis=data.get("legal_basis"),
            reasoning=data.get("reasoning"),
            expected_opposition=data.get("expected_opposition"),
            counter_response=data.get("counter_response"),
            importance=data.get("importance", "medium"),
            success_probability=data.get("success_probability"),
            is_key_argument=data.get("is_key_argument", False),
            status=data.get("status", "draft"),
            ai_suggestions=data.get("ai_suggestions"),
        )

        db.add(argument)
        db.commit()
        db.refresh(argument)
        return self._argument_to_dict(argument)

    def update_appeal_argument(self, db: Session, argument_id: int, data: Dict) -> Optional[Dict]:
        """更新上诉论点"""
        argument = db.query(AppealArgument).filter(AppealArgument.id == argument_id).first()
        if not argument:
            return None

        updatable_fields = [
            "argument_type", "title", "description", "original_finding",
            "appeal_finding", "discrepancy", "supporting_evidence", "counter_evidence",
            "legal_basis", "reasoning", "expected_opposition", "counter_response",
            "importance", "success_probability", "is_key_argument", "status", "ai_suggestions",
        ]

        for field in updatable_fields:
            if field in data and data[field] is not None:
                setattr(argument, field, data[field])

        db.commit()
        db.refresh(argument)
        return self._argument_to_dict(argument)

    def delete_appeal_argument(self, db: Session, argument_id: int) -> bool:
        """删除上诉论点"""
        argument = db.query(AppealArgument).filter(AppealArgument.id == argument_id).first()
        if not argument:
            return False
        db.delete(argument)
        db.commit()
        return True

    def get_appeal_deadlines(self, db: Session, appeal_id: int) -> List[Dict]:
        """获取上诉期限"""
        deadlines = db.query(AppealDeadline).filter(
            AppealDeadline.appeal_record_id == appeal_id
        ).order_by(AppealDeadline.deadline_date.asc()).all()

        result = []
        now = datetime.utcnow()
        for d in deadlines:
            days_remaining = None
            if d.deadline_date:
                days_remaining = max(0, (d.deadline_date - now).days)
                d.days_remaining = days_remaining
                if d.status == "pending" and d.deadline_date < now:
                    d.status = "expired"
                elif d.status == "pending" and days_remaining <= 3:
                    d.status = "active"

            result.append({
                "id": d.id,
                "appeal_record_id": d.appeal_record_id,
                "deadline_type": d.deadline_type,
                "deadline_name": d.deadline_name,
                "deadline_date": d.deadline_date.isoformat() if d.deadline_date else None,
                "description": d.description,
                "legal_basis": d.legal_basis,
                "status": d.status,
                "days_remaining": days_remaining,
                "is_mandatory": d.is_mandatory,
                "reminder_days": d.reminder_days,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            })

        db.commit()
        return result

    def create_appeal_deadline(self, db: Session, appeal_id: int, data: Dict) -> Dict:
        """创建上诉期限"""
        deadline_date = data.get("deadline_date")
        if deadline_date and isinstance(deadline_date, str):
            deadline_date = datetime.fromisoformat(deadline_date.replace("Z", "+00:00"))

        deadline = AppealDeadline(
            appeal_record_id=appeal_id,
            deadline_type=data.get("deadline_type", ""),
            deadline_name=data.get("deadline_name", ""),
            deadline_date=deadline_date,
            description=data.get("description"),
            legal_basis=data.get("legal_basis"),
            status=data.get("status", "pending"),
            is_mandatory=data.get("is_mandatory", True),
            reminder_days=data.get("reminder_days", [30, 15, 7, 3, 1]),
        )

        db.add(deadline)
        db.commit()
        db.refresh(deadline)

        return {
            "id": deadline.id,
            "appeal_record_id": deadline.appeal_record_id,
            "deadline_type": deadline.deadline_type,
            "deadline_name": deadline.deadline_name,
            "deadline_date": deadline.deadline_date.isoformat() if deadline.deadline_date else None,
            "description": deadline.description,
            "legal_basis": deadline.legal_basis,
            "status": deadline.status,
            "is_mandatory": deadline.is_mandatory,
            "created_at": deadline.created_at.isoformat() if deadline.created_at else None,
        }

    def get_appeal_documents(self, db: Session, appeal_id: int) -> List[Dict]:
        """获取上诉材料"""
        documents = db.query(AppealDocument).filter(
            AppealDocument.appeal_record_id == appeal_id
        ).order_by(AppealDocument.created_at.desc()).all()

        return [self._document_to_dict(d) for d in documents]

    def create_appeal_document(self, db: Session, appeal_id: int, data: Dict) -> Dict:
        """创建上诉材料"""
        doc = AppealDocument(
            appeal_record_id=appeal_id,
            document_type=data.get("document_type", ""),
            document_name=data.get("document_name", ""),
            description=data.get("description"),
            source=data.get("source"),
            status=data.get("status", "pending"),
            is_required=data.get("is_required", True),
            related_document_id=data.get("related_document_id"),
            purpose=data.get("purpose"),
            content_summary=data.get("content_summary"),
            key_points=data.get("key_points"),
            ai_summary=data.get("ai_summary"),
            ai_suggestions=data.get("ai_suggestions"),
        )

        db.add(doc)
        db.commit()
        db.refresh(doc)
        return self._document_to_dict(doc)

    def get_appeal_strategy(self, db: Session, appeal_id: int) -> Optional[Dict]:
        """获取二审策略"""
        strategy = db.query(SecondTrialStrategy).filter(
            SecondTrialStrategy.appeal_record_id == appeal_id
        ).first()

        if not strategy:
            return None

        return {
            "id": strategy.id,
            "appeal_record_id": strategy.appeal_record_id,
            "title": strategy.title,
            "target_arguments": strategy.target_arguments,
            "defense_points": strategy.defense_points,
            "defense_reasoning": strategy.defense_reasoning,
            "supporting_evidence": strategy.supporting_evidence,
            "counter_evidence": strategy.counter_evidence,
            "legal_basis": strategy.legal_basis,
            "expected_outcome": strategy.expected_outcome,
            "favorable_arguments": strategy.favorable_arguments,
            "is_approved": strategy.is_approved,
            "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
            "updated_at": strategy.updated_at.isoformat() if strategy.updated_at else None,
        }

    def create_appeal_strategy(self, db: Session, appeal_id: int, data: Dict) -> Dict:
        """创建二审策略"""
        strategy = SecondTrialStrategy(
            appeal_record_id=appeal_id,
            title=data.get("title", ""),
            target_arguments=data.get("target_arguments"),
            defense_points=data.get("defense_points"),
            defense_reasoning=data.get("defense_reasoning"),
            supporting_evidence=data.get("supporting_evidence"),
            counter_evidence=data.get("counter_evidence"),
            legal_basis=data.get("legal_basis"),
            expected_outcome=data.get("expected_outcome"),
            favorable_arguments=data.get("favorable_arguments"),
            is_approved=data.get("is_approved", False),
        )

        db.add(strategy)
        db.commit()
        db.refresh(strategy)

        return {
            "id": strategy.id,
            "appeal_record_id": strategy.appeal_record_id,
            "title": strategy.title,
            "target_arguments": strategy.target_arguments,
            "defense_points": strategy.defense_points,
            "defense_reasoning": strategy.defense_reasoning,
            "supporting_evidence": strategy.supporting_evidence,
            "counter_evidence": strategy.counter_evidence,
            "legal_basis": strategy.legal_basis,
            "expected_outcome": strategy.expected_outcome,
            "favorable_arguments": strategy.favorable_arguments,
            "is_approved": strategy.is_approved,
            "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
        }

    def generate_appeal_petition(self, db: Session, appeal_id: int) -> Dict:
        """起草上诉状草稿，提交或发送前必须人工核验。"""
        record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
        if not record:
            raise ValueError("上诉记录不存在")

        case = db.query(Case).filter(Case.id == record.case_id).first()

        arguments = db.query(AppealArgument).filter(
            AppealArgument.appeal_record_id == appeal_id
        ).all()

        arguments_text = "\n".join([
            f"- {a.title}: {a.description or ''}\n  原审认定: {a.original_finding or '无'}\n  上诉主张: {a.appeal_finding or '无'}"
            for a in arguments
        ]) if arguments else "暂无论点"

        prompt = f"""请根据以下案件信息，起草一份民事上诉状草稿。

【案件基本信息】
- 案件名称：{case.title if case else '未知'}
- 案由：{case.cause if case and case.cause else '未填写'}
- 上诉人：{record.appellant_name or '未填写'}（{record.appellant_type or '未填写'}）
- 原审法院：{record.original_court or '未填写'}
- 原审案号：{record.original_case_number or '未填写'}

【上诉类型】
{record.appeal_type.value if record.appeal_type else '一审到二审'}

【上诉理由】
{record.appeal_reason.value if record.appeal_reason else '法律适用错误'}

【上诉论点】
{arguments_text}

【原审判决内容】
{record.original_judgment_content or '未填写'}

【上诉请求】
{record.appeal_requests or '未填写'}

【事实和理由】
{record.appeal_facts or '未填写'}

请按照标准民事上诉状格式起草草稿，包含：
1. 标题
2. 当事人信息
3. 上诉请求
4. 事实与理由
5. 此致（上诉法院）
6. 具状人及日期

要求：
1. 输出开头必须标注“AI 草稿，待人工核验”；
2. 原审法院、案号、当事人身份、上诉期限、上诉请求和金额如未核实，必须使用【待核实】占位，不得编造；
3. 法律依据仅作为待核验引用，不得表达为已完成律师最终审查；
4. 不得引用未经核验的案例号、指导案例编号或虚构裁判文书号；
5. 末尾必须附“提交前核验清单”，至少包含上诉期限、原审案号、当事人身份、上诉请求、事实理由、证据目录、法条现行有效性、法院/管辖、签名盖章和日期；
6. 结构完整、论证清晰，但保持工作底稿和草稿定位。"""

        content = llm_service.chat([
            {"role": "system", "content": "你是一位资深上诉律师，正在协助起草民事上诉状工作底稿。输出必须保持草稿定位，提示提交前逐项人工核验，不得将结果表述为可直接提交的最终文书。"},
            {"role": "user", "content": prompt}
        ], model="qwen-plus")

        record.appeal_petition = content
        db.commit()

        return {
            "appeal_id": appeal_id,
            "petition": content,
            "document_status": "AI 草稿，待人工核验",
            "requires_human_review": True,
            "review_checklist": [
                "上诉期限和送达日期",
                "原审法院、案号和裁判文书信息",
                "上诉人、被上诉人及第三人主体身份",
                "上诉请求、金额和计算依据",
                "事实与理由对应的证据目录",
                "法条和司法解释现行有效性",
                "二审法院/管辖信息",
                "签名盖章、日期和授权手续",
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_appeal_countdown(self, db: Session, appeal_id: int) -> Dict:
        """上诉期限倒计时"""
        record = db.query(AppealRecord).filter(AppealRecord.id == appeal_id).first()
        if not record:
            raise ValueError("上诉记录不存在")

        now = datetime.utcnow()
        days_remaining = None
        is_overdue = False
        deadline_info = None

        if record.appeal_deadline:
            delta = record.appeal_deadline - now
            days_remaining = max(0, delta.days)
            is_overdue = delta.days <= 0
            record.days_remaining = days_remaining
            record.is_overdue = is_overdue
            deadline_info = {
                "deadline_date": record.appeal_deadline.isoformat(),
                "days_remaining": days_remaining,
                "hours_remaining": max(0, int(delta.total_seconds() / 3600)),
                "is_overdue": is_overdue,
            }

        deadlines = self.get_appeal_deadlines(db, appeal_id)

        db.commit()

        return {
            "appeal_id": appeal_id,
            "status": record.status.value if hasattr(record.status, 'value') else str(record.status),
            "judgment_received_date": record.judgment_received_date.isoformat() if record.judgment_received_date else None,
            "appeal_deadline": deadline_info,
            "appeal_submitted_date": record.appeal_submitted_date.isoformat() if record.appeal_submitted_date else None,
            "hearing_date": record.hearing_date.isoformat() if record.hearing_date else None,
            "deadlines": deadlines,
        }

    def get_appeal_statistics(self, db: Session, case_id: int) -> Dict:
        """获取上诉统计数据"""
        records = db.query(AppealRecord).filter(AppealRecord.case_id == case_id).all()
        record_ids = [r.id for r in records]

        total_arguments = 0
        key_arguments = 0
        total_documents = 0
        prepared_documents = 0

        if record_ids:
            total_arguments = db.query(AppealArgument).filter(
                AppealArgument.appeal_record_id.in_(record_ids)
            ).count()
            key_arguments = db.query(AppealArgument).filter(
                AppealArgument.appeal_record_id.in_(record_ids),
                AppealArgument.is_key_argument == True
            ).count()
            total_documents = db.query(AppealDocument).filter(
                AppealDocument.appeal_record_id.in_(record_ids)
            ).count()
            prepared_documents = db.query(AppealDocument).filter(
                AppealDocument.appeal_record_id.in_(record_ids),
                AppealDocument.status == "prepared"
            ).count()

        return {
            "total_appeals": len(records),
            "appeals_by_status": {
                status.value: len([r for r in records if (r.status.value if hasattr(r.status, 'value') else str(r.status)) == status.value])
                for status in AppealStatus
            },
            "total_arguments": total_arguments,
            "key_arguments": key_arguments,
            "total_documents": total_documents,
            "prepared_documents": prepared_documents,
        }

    def _auto_create_deadlines(self, db: Session, appeal_id: int, judgment_received_date, appeal_deadline_date):
        """自动创建上诉期限"""
        if not judgment_received_date:
            return

        default_deadlines = [
            {
                "deadline_type": "appeal_submission",
                "deadline_name": "递交上诉状",
                "deadline_date": appeal_deadline_date,
                "description": "在收到判决书之日起15日内递交上诉状",
                "legal_basis": "《中华人民共和国民事诉讼法》第一百七十一条",
                "is_mandatory": True,
                "reminder_days": [15, 7, 3, 1],
            },
            {
                "deadline_type": "fee_payment",
                "deadline_name": "缴纳上诉费",
                "deadline_date": appeal_deadline_date,
                "description": "在递交上诉状之日起7日内缴纳上诉费",
                "legal_basis": "《诉讼费用交纳办法》",
                "is_mandatory": True,
                "reminder_days": [7, 3, 1],
            },
        ]

        for dl_data in default_deadlines:
            dl = AppealDeadline(
                appeal_record_id=appeal_id,
                **dl_data,
            )
            db.add(dl)

        db.commit()

    def _appeal_to_dict(self, record: AppealRecord, db: Session) -> Dict:
        """将上诉记录转换为字典"""
        argument_count = db.query(AppealArgument).filter(
            AppealArgument.appeal_record_id == record.id
        ).count()
        document_count = db.query(AppealDocument).filter(
            AppealDocument.appeal_record_id == record.id
        ).count()

        return {
            "id": record.id,
            "case_id": record.case_id,
            "appeal_type": record.appeal_type.value if hasattr(record.appeal_type, 'value') else str(record.appeal_type),
            "appeal_reason": record.appeal_reason.value if hasattr(record.appeal_reason, 'value') else str(record.appeal_reason),
            "original_case_number": record.original_case_number,
            "original_court": record.original_court,
            "original_judge": record.original_judge,
            "original_judgment_date": record.original_judgment_date.isoformat() if record.original_judgment_date else None,
            "original_judgment_content": record.original_judgment_content,
            "appellant_type": record.appellant_type,
            "appellant_name": record.appellant_name,
            "judgment_received_date": record.judgment_received_date.isoformat() if record.judgment_received_date else None,
            "appeal_deadline": record.appeal_deadline.isoformat() if record.appeal_deadline else None,
            "appeal_submitted_date": record.appeal_submitted_date.isoformat() if record.appeal_submitted_date else None,
            "appeal_accepted_date": record.appeal_accepted_date.isoformat() if record.appeal_accepted_date else None,
            "hearing_date": record.hearing_date.isoformat() if record.hearing_date else None,
            "appeal_decision_date": record.appeal_decision_date.isoformat() if record.appeal_decision_date else None,
            "status": record.status.value if hasattr(record.status, 'value') else str(record.status),
            "days_remaining": record.days_remaining,
            "is_overdue": record.is_overdue,
            "appeal_petition": record.appeal_petition,
            "appeal_facts": record.appeal_facts,
            "new_evidence_list": record.new_evidence_list,
            "original_evidence_used": record.original_evidence_used,
            "appeal_requests": record.appeal_requests,
            "original_requests": record.original_requests,
            "modified_requests": record.modified_requests,
            "grounds_of_appeal": record.grounds_of_appeal,
            "opposing_arguments": record.opposing_arguments,
            "key_disputes": record.key_disputes,
            "strategy": record.strategy,
            "key_arguments": record.key_arguments,
            "evidence_plan": record.evidence_plan,
            "milestones": record.milestones,
            "decision": record.decision,
            "decision_type": record.decision_type,
            "favorable_outcome": record.favorable_outcome,
            "argument_count": argument_count,
            "document_count": document_count,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }

    def _argument_to_dict(self, arg: AppealArgument) -> Dict:
        """将上诉论点转换为字典"""
        return {
            "id": arg.id,
            "appeal_record_id": arg.appeal_record_id,
            "argument_type": arg.argument_type,
            "title": arg.title,
            "description": arg.description,
            "original_finding": arg.original_finding,
            "appeal_finding": arg.appeal_finding,
            "discrepancy": arg.discrepancy,
            "supporting_evidence": arg.supporting_evidence,
            "counter_evidence": arg.counter_evidence,
            "legal_basis": arg.legal_basis,
            "reasoning": arg.reasoning,
            "expected_opposition": arg.expected_opposition,
            "counter_response": arg.counter_response,
            "importance": arg.importance,
            "success_probability": arg.success_probability,
            "is_key_argument": arg.is_key_argument,
            "status": arg.status,
            "ai_suggestions": arg.ai_suggestions,
            "created_at": arg.created_at.isoformat() if arg.created_at else None,
            "updated_at": arg.updated_at.isoformat() if arg.updated_at else None,
        }

    def _document_to_dict(self, doc: AppealDocument) -> Dict:
        """将上诉材料转换为字典"""
        return {
            "id": doc.id,
            "appeal_record_id": doc.appeal_record_id,
            "document_type": doc.document_type,
            "document_name": doc.document_name,
            "description": doc.description,
            "source": doc.source,
            "status": doc.status,
            "is_required": doc.is_required,
            "related_document_id": doc.related_document_id,
            "purpose": doc.purpose,
            "content_summary": doc.content_summary,
            "key_points": doc.key_points,
            "ai_summary": doc.ai_summary,
            "ai_suggestions": doc.ai_suggestions,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        }


appeal_service = AppealService()
