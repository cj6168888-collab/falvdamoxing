"""
工作台 Dashboard 服务 - 聚合案件统计、紧急事项、待办、AI 建议
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.case import Case, CaseStatus, CaseType
from app.models.reminder import Reminder, ReminderPriority
from app.models.document import Document
from app.models.evidence import EvidenceItem
from app.models.letter import Letter
from app.models.hearing import HearingRecord
from app.services.llm_service import llm_service


class DashboardService:
    """工作台 Dashboard 服务"""

    def get_dashboard_data(self, db: Session) -> Dict:
        """获取工作台聚合数据"""
        stats = self._get_statistics(db)
        urgent = self._get_urgent_items(db)
        upcoming = self._get_upcoming_tasks(db)
        recent = self._get_recent_cases(db)
        activity = self._get_activity_log(db)

        return {
            "stats": stats,
            "urgent_items": urgent,
            "upcoming_tasks": upcoming,
            "recent_cases": recent,
            "activity_log": activity,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_statistics(self, db: Session) -> Dict:
        """获取统计数据"""
        return self._get_statistics(db)

    def get_urgent_items(self, db: Session) -> List[Dict]:
        """获取紧急事项"""
        return self._get_urgent_items(db)

    def get_upcoming_tasks(self, db: Session, days: int = 7) -> List[Dict]:
        """获取近期待办"""
        return self._get_upcoming_tasks(db, days)

    def get_recent_cases(self, db: Session, limit: int = 10) -> List[Dict]:
        """获取最近案件"""
        return self._get_recent_cases(db, limit)

    def generate_ai_suggestions(self, db: Session) -> Dict:
        """生成 AI 建议"""
        stats = self._get_statistics(db)
        urgent = self._get_urgent_items(db)

        urgent_text = "\n".join([
            f"- [{item['type']}] {item['title']}: {item.get('description', '')}"
            for item in urgent[:10]
        ]) if urgent else "暂无紧急事项"

        prompt = f"""根据以下案件工作台数据，提供专业的工作建议：

【案件统计】
- 总案件数：{stats['total_cases']}
- 进行中：{stats['active_cases']}
- 已结案：{stats['closed_cases']}
- 执行中：{stats['execution_cases']}

【紧急事项】
{urgent_text}

请提供：
1. 当前工作重点建议
2. 风险提示
3. 效率优化建议
4. 时间管理建议

要求：简洁、实用、针对性强。"""

        try:
            suggestions = llm_service.chat([
                {"role": "system", "content": "你是一位资深律所管理顾问，擅长案件管理和工作效率优化。请根据工作台数据，提供专业、实用的工作建议。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")

            return {
                "suggestions": suggestions,
                "generated_at": datetime.utcnow().isoformat(),
                "based_on": {
                    "total_cases": stats["total_cases"],
                    "urgent_count": len(urgent),
                }
            }
        except Exception:
            return {
                "suggestions": "AI 建议生成失败，请稍后重试",
                "generated_at": datetime.utcnow().isoformat(),
                "error": True,
            }

    def get_activity_log(self, db: Session, limit: int = 20) -> List[Dict]:
        """获取活动日志"""
        return self._get_activity_log(db, limit)

    def _get_statistics(self, db: Session) -> Dict:
        """获取案件统计"""
        total = db.query(Case).count()
        active = db.query(Case).filter(
            Case.status.in_([
                CaseStatus.RECEIVED, CaseStatus.REVIEWING, CaseStatus.FILED,
                CaseStatus.EVIDENCE, CaseStatus.PRE_TRIAL, CaseStatus.LITIGATION,
                CaseStatus.TRIAL_PREP, CaseStatus.TRIAL, CaseStatus.JUDGMENT,
                CaseStatus.EXECUTION,
            ])
        ).count()
        closed = db.query(Case).filter(
            Case.status.in_([CaseStatus.CLOSED, CaseStatus.ARCHIVED])
        ).count()
        execution = db.query(Case).filter(
            or_(
                Case.status == CaseStatus.EXECUTION,
                Case.is_transferred_to_execution == True
            )
        ).count()

        by_type = {}
        for ct in CaseType:
            count = db.query(Case).filter(Case.case_type == ct.value if hasattr(ct, 'value') else str(ct)).count()
            if count > 0:
                by_type[ct.value if hasattr(ct, 'value') else str(ct)] = count

        by_status = {}
        for cs in CaseStatus:
            count = db.query(Case).filter(Case.status == cs.value if hasattr(cs, 'value') else str(cs)).count()
            if count > 0:
                by_status[cs.value if hasattr(cs, 'value') else str(cs)] = count

        total_documents = db.query(Document).count()
        total_evidence = db.query(EvidenceItem).count()
        total_reminders = db.query(Reminder).count()
        unread_reminders = db.query(Reminder).filter(Reminder.is_read == False).count()
        uncompleted_reminders = db.query(Reminder).filter(Reminder.is_completed == False).count()

        high_priority_reminders = db.query(Reminder).filter(
            Reminder.priority == ReminderPriority.HIGH,
            Reminder.is_completed == False
        ).count()

        return {
            "total_cases": total,
            "active_cases": active,
            "closed_cases": closed,
            "execution_cases": execution,
            "by_type": by_type,
            "by_status": by_status,
            "total_documents": total_documents,
            "total_evidence": total_evidence,
            "total_reminders": total_reminders,
            "unread_reminders": unread_reminders,
            "uncompleted_reminders": uncompleted_reminders,
            "high_priority_reminders": high_priority_reminders,
        }

    def _get_urgent_items(self, db: Session) -> List[Dict]:
        """获取紧急事项"""
        urgent = []
        now = datetime.utcnow()

        overdue_reminders = db.query(Reminder).filter(
            Reminder.is_completed == False,
            Reminder.trigger_date.isnot(None),
            Reminder.trigger_date < now
        ).order_by(Reminder.trigger_date.asc()).limit(10).all()

        for r in overdue_reminders:
            case = db.query(Case).filter(Case.id == r.case_id).first()
            urgent.append({
                "id": f"reminder-{r.id}",
                "type": "overdue_reminder",
                "title": r.title,
                "description": r.content[:100] if r.content else "",
                "case_id": r.case_id,
                "case_title": case.title if case else None,
                "priority": r.priority.value if hasattr(r.priority, 'value') else str(r.priority),
                "trigger_date": r.trigger_date.isoformat() if r.trigger_date else None,
                "severity": "critical",
            })

        upcoming_deadlines = db.query(Reminder).filter(
            Reminder.is_completed == False,
            Reminder.trigger_date.isnot(None),
            Reminder.trigger_date >= now,
            Reminder.trigger_date <= now + timedelta(days=3)
        ).order_by(Reminder.trigger_date.asc()).limit(5).all()

        for r in upcoming_deadlines:
            case = db.query(Case).filter(Case.id == r.case_id).first()
            urgent.append({
                "id": f"reminder-{r.id}",
                "type": "upcoming_deadline",
                "title": r.title,
                "description": f"截止日期: {r.trigger_date.strftime('%Y-%m-%d')}",
                "case_id": r.case_id,
                "case_title": case.title if case else None,
                "priority": r.priority.value if hasattr(r.priority, 'value') else str(r.priority),
                "trigger_date": r.trigger_date.isoformat() if r.trigger_date else None,
                "severity": "high",
            })

        active_trials = db.query(Case).filter(
            Case.status.in_([CaseStatus.TRIAL, CaseStatus.TRIAL_PREP])
        ).limit(5).all()

        for c in active_trials:
            urgent.append({
                "id": f"case-{c.id}",
                "type": "active_trial",
                "title": f"案件【{c.title}】即将/正在开庭",
                "description": f"状态: {c.status}",
                "case_id": c.id,
                "case_title": c.title,
                "priority": "high",
                "severity": "high",
            })

        execution_cases = db.query(Case).filter(
            Case.status == CaseStatus.EXECUTION
        ).limit(5).all()

        for c in execution_cases:
            urgent.append({
                "id": f"execution-{c.id}",
                "type": "execution_tracking",
                "title": f"执行案件【{c.title}】需要跟踪",
                "description": f"执行进度: {c.execution_progress}%",
                "case_id": c.id,
                "case_title": c.title,
                "priority": "medium",
                "severity": "medium",
            })

        urgent.sort(key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity", "low"), 4))

        return urgent

    def _get_upcoming_tasks(self, db: Session, days: int = 7) -> List[Dict]:
        """获取近期待办"""
        now = datetime.utcnow()
        tasks = []

        upcoming_reminders = db.query(Reminder).filter(
            Reminder.is_completed == False,
            Reminder.trigger_date.isnot(None),
            Reminder.trigger_date >= now,
            Reminder.trigger_date <= now + timedelta(days=days)
        ).order_by(Reminder.trigger_date.asc()).limit(20).all()

        for r in upcoming_reminders:
            case = db.query(Case).filter(Case.id == r.case_id).first()
            days_until = (r.trigger_date - now).days if r.trigger_date else None
            tasks.append({
                "id": f"reminder-{r.id}",
                "type": "reminder",
                "title": r.title,
                "description": r.content[:100] if r.content else "",
                "case_id": r.case_id,
                "case_title": case.title if case else None,
                "due_date": r.trigger_date.isoformat() if r.trigger_date else None,
                "days_until": days_until,
                "priority": r.priority.value if hasattr(r.priority, 'value') else str(r.priority),
            })

        upcoming_hearings = db.query(Case).filter(
            Case.trial_date.isnot(None),
            Case.trial_date >= now,
            Case.trial_date <= now + timedelta(days=days),
            Case.status.in_([CaseStatus.TRIAL_PREP, CaseStatus.TRIAL])
        ).order_by(Case.trial_date.asc()).all()

        for c in upcoming_hearings:
            days_until = (c.trial_date - now).days if c.trial_date else None
            tasks.append({
                "id": f"hearing-{c.id}",
                "type": "hearing",
                "title": f"开庭: {c.title}",
                "description": f"案由: {c.cause or '未填写'}",
                "case_id": c.id,
                "case_title": c.title,
                "due_date": c.trial_date.isoformat() if c.trial_date else None,
                "days_until": days_until,
                "priority": "high",
            })

        tasks.sort(key=lambda x: (x.get("days_until") or 999, {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "low"), 3)))

        return tasks

    def _get_recent_cases(self, db: Session, limit: int = 10) -> List[Dict]:
        """获取最近案件"""
        cases = db.query(Case).order_by(Case.updated_at.desc()).limit(limit).all()

        result = []
        for c in cases:
            doc_count = db.query(Document).filter(Document.case_id == c.id).count()
            evidence_count = db.query(EvidenceItem).filter(EvidenceItem.case_id == c.id).count()

            result.append({
                "id": c.id,
                "case_number": c.case_number,
                "title": c.title,
                "case_type": c.case_type.value if hasattr(c.case_type, 'value') else str(c.case_type),
                "status": c.status.value if hasattr(c.status, 'value') else str(c.status),
                "cause": c.cause,
                "plaintiff": c.plaintiff,
                "defendant": c.defendant,
                "claim_amount": c.claim_amount,
                "document_count": doc_count,
                "evidence_count": evidence_count,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            })

        return result

    def _get_activity_log(self, db: Session, limit: int = 20) -> List[Dict]:
        """获取活动日志"""
        activities = []

        recent_cases = db.query(Case).order_by(Case.updated_at.desc()).limit(limit // 3).all()
        for c in recent_cases:
            activities.append({
                "type": "case_updated",
                "title": f"案件更新: {c.title}",
                "description": f"状态: {c.status}",
                "case_id": c.id,
                "timestamp": c.updated_at.isoformat() if c.updated_at else None,
            })

        recent_documents = db.query(Document).order_by(Document.created_at.desc()).limit(limit // 3).all()
        for d in recent_documents:
            case = db.query(Case).filter(Case.id == d.case_id).first()
            document_title = getattr(d, "title", None) or getattr(d, "filename", None) or "未命名文档"
            activities.append({
                "type": "document_created",
                "title": f"文档新增: {document_title}",
                "description": f"案件: {case.title if case else '未知'}",
                "case_id": d.case_id,
                "timestamp": d.created_at.isoformat() if d.created_at else None,
            })

        recent_evidence = db.query(EvidenceItem).order_by(EvidenceItem.created_at.desc()).limit(limit // 3).all()
        for e in recent_evidence:
            case = db.query(Case).filter(Case.id == e.case_id).first()
            evidence_title = (
                getattr(e, "title", None)
                or getattr(e, "display_name", None)
                or getattr(e, "original_filename", None)
                or getattr(e, "filename", None)
                or "未命名证据"
            )
            activities.append({
                "type": "evidence_added",
                "title": f"新增证据: {evidence_title}",
                "description": f"案件: {case.title if case else '未知'}",
                "case_id": e.case_id,
                "timestamp": e.created_at.isoformat() if e.created_at else None,
            })

        activities.sort(key=lambda x: x.get("timestamp") or "", reverse=True)

        return activities[:limit]


dashboard_service = DashboardService()
