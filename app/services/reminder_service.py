"""
提醒中心服务
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.reminder import Reminder, ReminderType, ReminderPriority
from app.models.case import Case, CaseStatus
from app.services.deadline_service import deadline_service


class ReminderService:
    """提醒中心服务"""

    def get_reminders(self, db: Session, case_id: Optional[int] = None, reminder_type: Optional[str] = None,
                      priority: Optional[str] = None, is_read: Optional[bool] = None,
                      is_completed: Optional[bool] = None, limit: int = 100) -> List[Dict]:
        """获取提醒列表"""
        query = db.query(Reminder)

        if case_id is not None:
            query = query.filter(Reminder.case_id == case_id)
        if reminder_type:
            query = query.filter(Reminder.reminder_type == ReminderType(reminder_type))
        if priority:
            query = query.filter(Reminder.priority == ReminderPriority(priority))
        if is_read is not None:
            query = query.filter(Reminder.is_read == is_read)
        if is_completed is not None:
            query = query.filter(Reminder.is_completed == is_completed)

        reminders = query.order_by(
            Reminder.is_completed.asc(),
            Reminder.is_read.asc(),
            Reminder.priority.asc(),
            Reminder.trigger_date.desc()
        ).limit(limit).all()

        return [self._reminder_to_dict(r, db) for r in reminders]

    def get_reminder(self, db: Session, reminder_id: int) -> Optional[Dict]:
        """获取提醒详情"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            return None
        return self._reminder_to_dict(reminder, db)

    def create_reminder(self, db: Session, data: Dict) -> Dict:
        """创建提醒"""
        trigger_date = data.get("trigger_date")
        if trigger_date and isinstance(trigger_date, str):
            trigger_date = datetime.fromisoformat(trigger_date.replace("Z", "+00:00"))

        reminder = Reminder(
            case_id=data.get("case_id"),
            reminder_type=ReminderType(data.get("reminder_type", "deadline")),
            priority=ReminderPriority(data.get("priority", "medium")),
            title=data.get("title", ""),
            content=data.get("content", ""),
            suggestion=data.get("suggestion"),
            trigger_date=trigger_date,
            is_triggered=data.get("is_triggered", False),
            is_read=data.get("is_read", False),
            is_completed=data.get("is_completed", False),
        )

        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return self._reminder_to_dict(reminder, db)

    def update_reminder(self, db: Session, reminder_id: int, data: Dict) -> Optional[Dict]:
        """更新提醒"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            return None

        updatable_fields = [
            "title", "content", "suggestion", "reminder_type", "priority",
            "trigger_date", "is_triggered", "is_read", "is_completed",
        ]

        for field in updatable_fields:
            if field in data and data[field] is not None:
                if field == "reminder_type":
                    setattr(reminder, field, ReminderType(data[field]))
                elif field == "priority":
                    setattr(reminder, field, ReminderPriority(data[field]))
                elif field == "trigger_date" and isinstance(data[field], str):
                    setattr(reminder, field, datetime.fromisoformat(data[field].replace("Z", "+00:00")))
                else:
                    setattr(reminder, field, data[field])

        db.commit()
        db.refresh(reminder)
        return self._reminder_to_dict(reminder, db)

    def delete_reminder(self, db: Session, reminder_id: int) -> bool:
        """删除提醒"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            return False
        db.delete(reminder)
        db.commit()
        return True

    def batch_update(self, db: Session, reminder_ids: List[int], data: Dict) -> Dict:
        """批量更新提醒"""
        updated = 0
        for rid in reminder_ids:
            reminder = db.query(Reminder).filter(Reminder.id == rid).first()
            if reminder:
                if "is_read" in data:
                    reminder.is_read = data["is_read"]
                if "is_completed" in data:
                    reminder.is_completed = data["is_completed"]
                if "priority" in data:
                    reminder.priority = ReminderPriority(data["priority"])
                updated += 1

        db.commit()
        return {"updated": updated, "total": len(reminder_ids)}

    def mark_all_read(self, db: Session, case_id: Optional[int] = None) -> int:
        """全部标记已读"""
        query = db.query(Reminder).filter(Reminder.is_read == False)
        if case_id is not None:
            query = query.filter(Reminder.case_id == case_id)
        count = query.update({"is_read": True})
        db.commit()
        return count

    def snooze_reminder(self, db: Session, reminder_id: int, days: int = 1) -> Optional[Dict]:
        """延后提醒"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            return None

        reminder.trigger_date = (reminder.trigger_date or datetime.utcnow()) + timedelta(days=days)
        reminder.is_triggered = False
        db.commit()
        db.refresh(reminder)
        return self._reminder_to_dict(reminder, db)

    def mark_complete(self, db: Session, reminder_id: int) -> Optional[Dict]:
        """标记完成"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            return None

        reminder.is_completed = True
        reminder.is_read = True
        db.commit()
        db.refresh(reminder)
        return self._reminder_to_dict(reminder, db)

    def auto_generate_reminders(
        self,
        db: Session,
        case_id: int,
        *,
        assume_empty: bool = False,
        return_dicts: bool = True,
    ) -> List[Dict]:
        """基于案件自动生成提醒"""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("案件不存在")

        generated_reminders = []
        case_type = case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type)
        status = case.status.value if hasattr(case.status, 'value') else str(case.status)

        reminder_templates = self._get_reminder_templates(case_type, status, case)
        existing_titles = set()
        if not assume_empty and reminder_templates:
            existing_titles = {
                title
                for (title,) in db.query(Reminder.title)
                .filter(
                    Reminder.case_id == case_id,
                    Reminder.title.in_([template["title"] for template in reminder_templates]),
                    Reminder.is_completed == False,
                )
                .all()
            }

        for template in reminder_templates:
            if template["title"] in existing_titles:
                continue

            trigger_date = template.get("trigger_date")
            if trigger_date and isinstance(trigger_date, str):
                trigger_date = datetime.fromisoformat(trigger_date.replace("Z", "+00:00"))

            reminder = Reminder(
                case_id=case_id,
                reminder_type=ReminderType(template.get("reminder_type", "deadline")),
                priority=ReminderPriority(template.get("priority", "medium")),
                title=template["title"],
                content=template["content"],
                suggestion=template.get("suggestion"),
                trigger_date=trigger_date,
                is_triggered=False,
                is_read=False,
                is_completed=False,
            )

            db.add(reminder)
            generated_reminders.append(reminder)

        db.commit()

        if not return_dicts:
            return []

        return [self._reminder_to_dict(reminder, db) for reminder in generated_reminders]

    def get_reminder_stats(self, db: Session, case_id: Optional[int] = None) -> Dict:
        """提醒统计"""
        query = db.query(Reminder)
        if case_id is not None:
            query = query.filter(Reminder.case_id == case_id)

        total = query.count()
        unread = query.filter(Reminder.is_read == False).count()
        uncompleted = query.filter(Reminder.is_completed == False).count()
        completed = query.filter(Reminder.is_completed == True).count()
        high_priority = query.filter(Reminder.priority == ReminderPriority.HIGH).count()

        by_type = {}
        for rt in ReminderType:
            count = query.filter(Reminder.reminder_type == rt).count()
            if count > 0:
                by_type[rt.value] = count

        overdue = query.filter(
            Reminder.is_completed == False,
            Reminder.trigger_date.isnot(None),
            Reminder.trigger_date < datetime.utcnow()
        ).count()

        upcoming_7d = query.filter(
            Reminder.is_completed == False,
            Reminder.trigger_date.isnot(None),
            Reminder.trigger_date >= datetime.utcnow(),
            Reminder.trigger_date <= datetime.utcnow() + timedelta(days=7)
        ).count()

        return {
            "total": total,
            "unread": unread,
            "uncompleted": uncompleted,
            "completed": completed,
            "high_priority": high_priority,
            "overdue": overdue,
            "upcoming_7d": upcoming_7d,
            "by_type": by_type,
        }

    def check_overdue(self, db: Session) -> List[Dict]:
        """检查过期提醒"""
        reminders = db.query(Reminder).filter(
            Reminder.is_completed == False,
            Reminder.is_triggered == True,
            Reminder.trigger_date.isnot(None),
            Reminder.trigger_date < datetime.utcnow()
        ).order_by(Reminder.trigger_date.asc()).all()

        return [self._reminder_to_dict(r, db) for r in reminders]

    def _reminder_to_dict(self, reminder: Reminder, db: Session) -> Dict:
        """将提醒转换为字典"""
        now = datetime.utcnow()
        is_overdue = False
        days_until_trigger = None

        if reminder.trigger_date and not reminder.is_completed:
            delta = reminder.trigger_date - now
            days_until_trigger = delta.days
            is_overdue = delta.days < 0

        case_title = None
        if reminder.case_id:
            case = db.query(Case).filter(Case.id == reminder.case_id).first()
            if case:
                case_title = case.title

        return {
            "id": reminder.id,
            "case_id": reminder.case_id,
            "case_title": case_title,
            "reminder_type": reminder.reminder_type.value if hasattr(reminder.reminder_type, 'value') else str(reminder.reminder_type),
            "priority": reminder.priority.value if hasattr(reminder.priority, 'value') else str(reminder.priority),
            "title": reminder.title,
            "content": reminder.content,
            "suggestion": reminder.suggestion,
            "trigger_date": reminder.trigger_date.isoformat() if reminder.trigger_date else None,
            "is_triggered": reminder.is_triggered,
            "is_read": reminder.is_read,
            "is_completed": reminder.is_completed,
            "is_overdue": is_overdue,
            "days_until_trigger": days_until_trigger,
            "created_at": reminder.created_at.isoformat() if reminder.created_at else None,
            "updated_at": reminder.updated_at.isoformat() if reminder.updated_at else None,
        }

    def _get_reminder_templates(self, case_type: str, status: str, case) -> List[Dict]:
        """获取提醒模板 - 覆盖所有法律场景"""
        from datetime import timedelta

        templates = []
        now = datetime.utcnow()

        # ===== 收案/审查阶段 =====
        if status in ("收案", "审查中"):
            templates.append({
                "title": "案件审查期限提醒",
                "content": f"案件【{case.title}】需要尽快完成审查",
                "suggestion": "建议在收案后7个工作日内完成初步审查",
                "reminder_type": "deadline",
                "priority": "medium",
                "trigger_date": (now + timedelta(days=7)).isoformat(),
            })
            templates.append({
                "title": "催讨权利主张提醒",
                "content": f"案件【{case.title}】建议尽快向对方发出催告函/律师函主张权益",
                "suggestion": "及时发函可中断诉讼时效，建议7日内发出催告函或律师函",
                "reminder_type": "deadline",
                "priority": "high",
                "trigger_date": (now + timedelta(days=7)).isoformat(),
            })

        # ===== 已立案/证据准备/诉前准备阶段 =====
        if status in ("已立案", "证据准备", "诉前准备"):
            templates.append({
                "title": "举证期限提醒",
                "content": f"案件【{case.title}】需要关注举证期限",
                "suggestion": "普通程序举证期限不得少于15日，简易程序一般不超过15日，小额诉讼7日",
                "reminder_type": "evidence",
                "priority": "high",
                "trigger_date": (now + timedelta(days=15)).isoformat(),
            })
            templates.append({
                "title": "管辖权异议期限提醒",
                "content": f"案件【{case.title}】如对管辖权有异议，需在收到起诉状副本之日起15日内提出",
                "suggestion": "管辖权异议应在答辩期内提出，逾期视为接受管辖",
                "reminder_type": "deadline",
                "priority": "high",
                "trigger_date": (now + timedelta(days=15)).isoformat(),
            })
            templates.append({
                "title": "答辩状提交提醒",
                "content": f"案件【{case.title}】需在收到起诉状副本之日起15日内提交答辩状",
                "suggestion": "答辩状应针对原告诉求逐条回应，提出抗辩理由和法律依据",
                "reminder_type": "deadline",
                "priority": "high",
                "trigger_date": (now + timedelta(days=15)).isoformat(),
            })
            templates.append({
                "title": "回函处理提醒",
                "content": f"案件【{case.title}】如有收到对方函件（律师函/催告函等），需及时回复处理",
                "suggestion": "律师函建议7日内回复，催告函建议15日内回复，逾期可能被视为默认",
                "reminder_type": "deadline",
                "priority": "high",
                "trigger_date": (now + timedelta(days=7)).isoformat(),
            })
            templates.append({
                "title": "主张权益期限提醒",
                "content": f"案件【{case.title}】注意及时主张合法权益，避免超过诉讼时效",
                "suggestion": "民事诉讼时效为3年，可通过起诉、发函、协商等方式中断时效",
                "reminder_type": "deadline",
                "priority": "medium",
                "trigger_date": (now + timedelta(days=30)).isoformat(),
            })
            templates.append({
                "title": "催讨/催收提醒",
                "content": f"案件【{case.title}】如涉及债权催讨，建议定期向债务人发出催收通知",
                "suggestion": "每3-6个月发一次催收函，可中断诉讼时效重新计算",
                "reminder_type": "deadline",
                "priority": "medium",
                "trigger_date": (now + timedelta(days=90)).isoformat(),
            })

        # ===== 起诉答辩/开庭准备阶段 =====
        if status in ("起诉答辩", "开庭准备"):
            templates.append({
                "title": "开庭准备提醒",
                "content": f"案件【{case.title}】需要做好开庭准备",
                "suggestion": "准备代理词、证据目录、质证意见、法庭辩论提纲等文书",
                "reminder_type": "hearing",
                "priority": "high",
                "trigger_date": (now + timedelta(days=3)).isoformat(),
            })
            templates.append({
                "title": "证据交换提醒",
                "content": f"案件【{case.title}】开庭前需完成证据交换",
                "suggestion": "提前整理证据原件、制作证据目录、准备质证意见",
                "reminder_type": "evidence",
                "priority": "high",
                "trigger_date": (now + timedelta(days=7)).isoformat(),
            })
            templates.append({
                "title": "回函/回复对方意见提醒",
                "content": f"案件【{case.title}】如收到对方答辩状或代理意见，需及时回复",
                "suggestion": "针对对方观点准备反驳意见，补充有利证据",
                "reminder_type": "deadline",
                "priority": "medium",
                "trigger_date": (now + timedelta(days=5)).isoformat(),
            })

        # ===== 开庭审理阶段 =====
        if status == "开庭审理":
            templates.append({
                "title": "出庭准备提醒",
                "content": f"案件【{case.title}】即将开庭，请做好出庭准备",
                "suggestion": "携带身份证、授权委托书、证据原件、代理词等出庭材料",
                "reminder_type": "hearing",
                "priority": "high",
                "trigger_date": (now + timedelta(days=1)).isoformat(),
            })

        # ===== 判决阶段 =====
        if status == "判决":
            templates.append({
                "title": "上诉期限提醒",
                "content": f"案件【{case.title}】已判决，注意上诉期限",
                "suggestion": "判决书送达之日起15日内可提起上诉（裁定为10日），逾期判决生效",
                "reminder_type": "deadline",
                "priority": "high",
                "trigger_date": (now + timedelta(days=15)).isoformat(),
            })
            templates.append({
                "title": "申诉权利提醒",
                "content": f"案件【{case.title}】如判决已生效但认为有错误，可申请再审/申诉",
                "suggestion": "申请再审期限为判决生效后6个月内，需符合法定再审事由",
                "reminder_type": "deadline",
                "priority": "medium",
                "trigger_date": (now + timedelta(days=30)).isoformat(),
            })

        # ===== 执行阶段 =====
        if status == "执行中":
            templates.append({
                "title": "执行进度跟踪",
                "content": f"案件【{case.title}】正在执行中，需要定期跟踪",
                "suggestion": "建议每两周联系执行法官了解进度，必要时申请强制执行措施",
                "reminder_type": "deadline",
                "priority": "medium",
                "trigger_date": (now + timedelta(days=14)).isoformat(),
            })
            templates.append({
                "title": "执行申请期限提醒",
                "content": f"案件【{case.title}】申请执行的期限为2年，从法律文书规定履行期间的最后一日起计算",
                "suggestion": "注意执行申请期限，逾期将丧失申请强制执行的权利",
                "reminder_type": "deadline",
                "priority": "high",
                "trigger_date": (now + timedelta(days=30)).isoformat(),
            })
            templates.append({
                "title": "催讨执行款提醒",
                "content": f"案件【{case.title}】如被执行人未履行义务，建议及时催讨并申请执行",
                "suggestion": "可向法院申请查封、冻结、扣押被执行人财产",
                "reminder_type": "deadline",
                "priority": "high",
                "trigger_date": (now + timedelta(days=7)).isoformat(),
            })

        # ===== 已中止/休眠阶段 =====
        if status in ("已中止", "休眠"):
            templates.append({
                "title": "案件激活提醒",
                "content": f"案件【{case.title}】当前处于{status}状态，建议尽快激活处理",
                "suggestion": "长期不处理可能导致权利丧失或诉讼时效届满，建议及时联系法院或对方当事人",
                "reminder_type": "risk",
                "priority": "high",
                "trigger_date": (now + timedelta(days=3)).isoformat(),
            })

        # ===== 通用提醒（所有状态） =====
        # 诉讼时效跟踪
        if case.filed_date:
            templates.append({
                "title": "诉讼时效跟踪",
                "content": f"案件【{case.title}】立案日期为{case.filed_date.strftime('%Y-%m-%d')}，注意跟踪诉讼时效",
                "suggestion": "民事诉讼时效一般为3年，注意通过起诉、发函、协商等方式中断时效",
                "reminder_type": "deadline",
                "priority": "medium",
                "trigger_date": (now + timedelta(days=30)).isoformat(),
            })

        # 财产保全提醒
        if status in ("收案", "审查中", "已立案"):
            templates.append({
                "title": "财产保全提醒",
                "content": f"案件【{case.title}】如担心对方转移财产，建议申请财产保全",
                "suggestion": "诉前保全需在48小时内裁定，诉中保全一般5日内裁定，需提供担保",
                "reminder_type": "opportunity",
                "priority": "medium",
                "trigger_date": (now + timedelta(days=3)).isoformat(),
            })

        # 回函/函件处理通用提醒
        templates.append({
            "title": "函件处理检查",
            "content": f"案件【{case.title}】需定期检查是否有待处理的函件（律师函/催告函/回复函等）",
            "suggestion": "收到函件后应及时处理并回复，避免被视为默认或承担不利后果",
            "reminder_type": "deadline",
            "priority": "medium",
            "trigger_date": (now + timedelta(days=2)).isoformat(),
        })

        # 材料缺失检查
        templates.append({
            "title": "案件材料缺失检查",
            "content": f"案件【{case.title}】需要检查材料是否完整",
            "suggestion": "检查起诉状、证据目录、授权委托书、身份证明等是否齐全",
            "reminder_type": "material_missing",
            "priority": "low",
            "trigger_date": (now + timedelta(days=1)).isoformat(),
        })

        return templates


reminder_service = ReminderService()
