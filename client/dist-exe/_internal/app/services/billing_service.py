"""
计费执行服务 — 到期检查、自动停用、缴费记录
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.tenant import SubscriptionStatus
from app.models.payment import PaymentRecord


class BillingService:

    @staticmethod
    def check_and_enforce(db: Session, tenant: Tenant) -> dict:
        """检查租户计费状态，到期自动停用。

        每次登录时调用。平台超管不受影响。
        """
        if not tenant.billing_due_date:
            return {"ok": True, "message": "无到期日"}

        now = datetime.utcnow()
        if now > tenant.billing_due_date and tenant.approval_status == "approved":
            tenant.subscription_status = SubscriptionStatus.PAST_DUE
            tenant.is_active = False
            db.commit()
            return {
                "ok": False,
                "message": f"账户已到期（{tenant.billing_due_date.strftime('%Y-%m-%d')}），请续费后继续使用。",
            }

        # 到期前7天提醒
        days_left = (tenant.billing_due_date - now).days
        if 0 <= days_left <= 7:
            return {"ok": True, "warning": True, "days_left": days_left,
                    "message": f"账户将于{days_left}天后到期，请及时续费。"}

        return {"ok": True, "message": ""}

    @staticmethod
    def record_payment(
        db: Session,
        tenant_id: str,
        amount: float,
        billing_cycle: str = "monthly",
        payment_method: str = "manual",
        created_by: str = "",
    ) -> PaymentRecord:
        """记录一笔缴费，同时更新租户到期日。"""
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError("租户不存在")

        delta = timedelta(days=365) if billing_cycle == "yearly" else timedelta(days=30)
        now = datetime.utcnow()

        # 若未到期则顺延
        if tenant.billing_due_date and tenant.billing_due_date > now:
            period_start = tenant.billing_due_date
        else:
            period_start = now
        period_end = period_start + delta

        record = PaymentRecord(
            tenant_id=tenant_id,
            amount=amount,
            billing_cycle=billing_cycle,
            payment_method=payment_method,
            period_start=period_start,
            period_end=period_end,
            created_by=created_by,
        )
        db.add(record)

        # 更新租户计费信息
        tenant.billing_due_date = period_end
        tenant.billing_amount = amount
        tenant.billing_cycle = billing_cycle
        tenant.subscription_status = SubscriptionStatus.ACTIVE
        tenant.is_active = True
        db.commit()

        return record

    @staticmethod
    def get_payment_history(db: Session, tenant_id: str) -> List[PaymentRecord]:
        return (
            db.query(PaymentRecord)
            .filter(PaymentRecord.tenant_id == tenant_id)
            .order_by(PaymentRecord.paid_at.desc())
            .all()
        )


billing_service = BillingService()
