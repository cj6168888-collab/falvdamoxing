"""
案件财务服务 - 费用记录、成本收益分析、诉讼风险评估
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.finance import (
    CaseFinance, ExpenseRecord, WinRateAssessment,
    ExpenseCategory, ExpenseStatus, WinRateFactor
)
from app.models.case import Case
from app.models.evidence import EvidenceItem
from app.models.document import Document
from app.services.llm_service import llm_service


class FinanceService:
    """案件财务服务"""

    def get_finance_overview(self, db: Session, case_id: int) -> Dict:
        """获取财务概览"""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("案件不存在")

        finance = db.query(CaseFinance).filter(CaseFinance.case_id == case_id).first()
        if not finance:
            finance = self._ensure_finance_record(db, case_id)

        expenses = db.query(ExpenseRecord).filter(ExpenseRecord.case_id == case_id).all()

        total_expenses = sum(e.amount for e in expenses)
        total_paid = sum(e.amount for e in expenses if (e.status.value if hasattr(e.status, 'value') else str(e.status)) == ExpenseStatus.PAID.value)
        total_pending = sum(e.amount for e in expenses if (e.status.value if hasattr(e.status, 'value') else str(e.status)) == ExpenseStatus.PENDING.value)
        total_reimbursed = sum(e.amount for e in expenses if (e.status.value if hasattr(e.status, 'value') else str(e.status)) == ExpenseStatus.REIMBURSED.value)

        finance.total_expenses = total_expenses
        finance.total_paid = total_paid
        finance.total_pending = total_pending
        finance.total_reimbursed = total_reimbursed

        if finance.expected_recovery is not None and total_expenses > 0:
            finance.cost_benefit_ratio = finance.expected_recovery / total_expenses if total_expenses > 0 else None
            finance.net_benefit = finance.expected_recovery - total_expenses

        db.commit()
        db.refresh(finance)

        expenses_by_category = {}
        for e in expenses:
            cat = (e.category.value if hasattr(e.category, 'value') else str(e.category)) if e.category else "other"
            if cat not in expenses_by_category:
                expenses_by_category[cat] = {"count": 0, "total": 0.0}
            expenses_by_category[cat]["count"] += 1
            expenses_by_category[cat]["total"] += e.amount

        expenses_by_status = {}
        for es in ExpenseStatus:
            count = len([e for e in expenses if (e.status.value if hasattr(e.status, 'value') else str(e.status)) == es.value])
            if count > 0:
                expenses_by_status[es.value] = count

        latest_assessment = db.query(WinRateAssessment).filter(
            WinRateAssessment.case_id == case_id
        ).order_by(WinRateAssessment.created_at.desc()).first()

        return {
            "case_id": case_id,
            "case_title": case.title,
            "claim_amount": case.claim_amount,
            "finance": {
                "id": finance.id,
                "total_expenses": finance.total_expenses,
                "total_paid": finance.total_paid,
                "total_pending": finance.total_pending,
                "total_reimbursed": finance.total_reimbursed,
                "expected_recovery": finance.expected_recovery,
                "actual_recovery": finance.actual_recovery,
                "cost_benefit_ratio": finance.cost_benefit_ratio,
                "net_benefit": finance.net_benefit,
                "win_rate": finance.win_rate,
                "win_rate_confidence": finance.win_rate_confidence,
                "win_rate_assessed_at": finance.win_rate_assessed_at.isoformat() if finance.win_rate_assessed_at else None,
                "notes": finance.notes,
                "updated_at": finance.updated_at.isoformat() if finance.updated_at else None,
            },
            "expenses_by_category": expenses_by_category,
            "expenses_by_status": expenses_by_status,
            "latest_win_rate": {
                "win_rate": latest_assessment.win_rate,
                "confidence": latest_assessment.confidence,
                "assessed_at": latest_assessment.created_at.isoformat() if latest_assessment.created_at else None,
            } if latest_assessment else None,
        }

    def update_finance_overview(self, db: Session, case_id: int, data: Dict) -> Dict:
        """更新财务概览"""
        finance = db.query(CaseFinance).filter(CaseFinance.case_id == case_id).first()
        if not finance:
            finance = CaseFinance(case_id=case_id)
            db.add(finance)

        updatable_fields = [
            "expected_recovery", "actual_recovery", "notes",
        ]

        for field in updatable_fields:
            if field in data and data[field] is not None:
                setattr(finance, field, data[field])

        db.commit()
        db.refresh(finance)

        return self.get_finance_overview(db, case_id)

    def get_expenses(self, db: Session, case_id: int) -> List[Dict]:
        """获取费用记录"""
        expenses = db.query(ExpenseRecord).filter(
            ExpenseRecord.case_id == case_id
        ).order_by(ExpenseRecord.expense_date.desc()).all()

        return [self._expense_to_dict(e) for e in expenses]

    def create_expense(self, db: Session, case_id: int, data: Dict) -> Dict:
        """创建费用记录"""
        expense_date = data.get("expense_date")
        if expense_date and isinstance(expense_date, str):
            expense_date = datetime.fromisoformat(expense_date.replace("Z", "+00:00"))

        payment_date = data.get("payment_date")
        if payment_date and isinstance(payment_date, str):
            payment_date = datetime.fromisoformat(payment_date.replace("Z", "+00:00"))

        due_date = data.get("due_date")
        if due_date and isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))

        expense = ExpenseRecord(
            case_id=case_id,
            category=ExpenseCategory(data["category"]) if data.get("category") else None,
            title=data.get("title", ""),
            description=data.get("description"),
            amount=data.get("amount", 0.0),
            currency=data.get("currency", "CNY"),
            status=ExpenseStatus(data.get("status", "pending")),
            expense_date=expense_date,
            payment_date=payment_date,
            due_date=due_date,
            payee=data.get("payee"),
            invoice_number=data.get("invoice_number"),
            related_document_id=data.get("related_document_id"),
            notes=data.get("notes"),
        )

        db.add(expense)
        db.commit()
        db.refresh(expense)
        return self._expense_to_dict(expense)

    def update_expense(self, db: Session, expense_id: int, data: Dict) -> Optional[Dict]:
        """更新费用记录"""
        expense = db.query(ExpenseRecord).filter(ExpenseRecord.id == expense_id).first()
        if not expense:
            return None

        updatable_fields = [
            "category", "title", "description", "amount", "currency", "status",
            "expense_date", "payment_date", "due_date", "payee", "invoice_number",
            "related_document_id", "notes",
        ]

        for field in updatable_fields:
            if field in data and data[field] is not None:
                if field == "category" and data[field]:
                    setattr(expense, field, ExpenseCategory(data[field]))
                elif field == "status" and data[field]:
                    setattr(expense, field, ExpenseStatus(data[field]))
                elif field in ("expense_date", "payment_date", "due_date") and isinstance(data[field], str):
                    setattr(expense, field, datetime.fromisoformat(data[field].replace("Z", "+00:00")))
                else:
                    setattr(expense, field, data[field])

        db.commit()
        db.refresh(expense)
        return self._expense_to_dict(expense)

    def delete_expense(self, db: Session, expense_id: int) -> bool:
        """删除费用记录"""
        expense = db.query(ExpenseRecord).filter(ExpenseRecord.id == expense_id).first()
        if not expense:
            return False
        db.delete(expense)
        db.commit()
        return True

    def get_cost_benefit_analysis(self, db: Session, case_id: int) -> Dict:
        """成本收益分析"""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("案件不存在")

        expenses = db.query(ExpenseRecord).filter(ExpenseRecord.case_id == case_id).all()
        total_expenses = sum(e.amount for e in expenses)

        finance = db.query(CaseFinance).filter(CaseFinance.case_id == case_id).first()
        expected_recovery = finance.expected_recovery if finance else None
        actual_recovery = finance.actual_recovery if finance else None

        recovery_amount = actual_recovery if actual_recovery is not None else expected_recovery

        cost_benefit_ratio = None
        net_benefit = None
        roi = None

        if recovery_amount is not None and total_expenses > 0:
            cost_benefit_ratio = recovery_amount / total_expenses
            net_benefit = recovery_amount - total_expenses
            roi = (net_benefit / total_expenses) * 100

        expense_breakdown = {}
        for e in expenses:
            cat = (e.category.value if hasattr(e.category, 'value') else str(e.category)) if e.category else "other"
            if cat not in expense_breakdown:
                expense_breakdown[cat] = {"amount": 0.0, "count": 0, "percentage": 0.0}
            expense_breakdown[cat]["amount"] += e.amount
            expense_breakdown[cat]["count"] += 1

        for cat in expense_breakdown:
            if total_expenses > 0:
                expense_breakdown[cat]["percentage"] = (expense_breakdown[cat]["amount"] / total_expenses) * 100

        monthly_trend = {}
        for e in expenses:
            if e.expense_date:
                month_key = e.expense_date.strftime("%Y-%m")
                if month_key not in monthly_trend:
                    monthly_trend[month_key] = 0.0
                monthly_trend[month_key] += e.amount

        return {
            "case_id": case_id,
            "case_title": case.title,
            "claim_amount": case.claim_amount,
            "total_expenses": total_expenses,
            "expected_recovery": expected_recovery,
            "actual_recovery": actual_recovery,
            "cost_benefit_ratio": cost_benefit_ratio,
            "net_benefit": net_benefit,
            "roi": roi,
            "expense_breakdown": expense_breakdown,
            "monthly_trend": monthly_trend,
            "expense_count": len(expenses),
        }

    def assess_win_rate(self, db: Session, case_id: int, force: bool = False) -> Dict:
        """AI 评估诉讼风险和裁判支持度参考"""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("案件不存在")

        if not force:
            latest = db.query(WinRateAssessment).filter(
                WinRateAssessment.case_id == case_id
            ).order_by(WinRateAssessment.created_at.desc()).first()

            if latest and (datetime.utcnow() - latest.created_at).total_seconds() < 86400:
                return {
                    "assessment": self._assessment_to_dict(latest),
                    "cached": True,
                }

        evidence_count = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).count()
        doc_count = db.query(Document).filter(Document.case_id == case_id).count()

        evidence_items = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).limit(10).all()
        evidence_summary = "\n".join([
            f"- {e.display_name or e.original_filename or '未命名'}: {(e.extracted_content or e.raw_content or e.summary or '无内容')[:300]}"
            for e in evidence_items
        ]) if evidence_items else "暂无证据"

        prompt = f"""请对以下案件进行诉讼风险评估，并给出“裁判支持度参考”。

【案件信息】
- 案件名称：{case.title}
- 案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type)}
- 案由：{case.cause or '未填写'}
- 原告：{case.plaintiff or '未填写'}
- 被告：{case.defendant or '未填写'}
- 诉讼金额：{case.claim_amount or '未填写'}
- 案件描述：{case.description or '未填写'}
- 法律分析：{case.legal_analysis or '暂无'}

【证据情况】
- 证据数量：{evidence_count}
- 文书数量：{doc_count}
- 证据摘要：
{evidence_summary}

请从以下维度进行评估（0-100分）：
1. 证据强度（evidence_strength）
2. 法律依据（legal_basis）
3. 程序合规（procedural_compliance）
4. 对方弱点（opponent_weakness）
5. 判例支持（precedent_support）

本接口未接入权威类案检索。评估“判例支持”时只能基于常见裁判规则和待检索方向概括，不得输出具体法院案号、指导案例编号或虚构判例；如需具体类案，请写“需另行检索核验”。

并给出综合裁判支持度参考（0-100%，仅为风险分析指标，不构成胜诉承诺）和评估参考度（0-100%）。

请返回JSON格式：
{{
  "win_rate": 综合裁判支持度参考,
  "confidence": 评估参考度,
  "factors": [
    {{"factor": "evidence_strength", "score": 分数, "weight": 权重, "analysis": "分析"}},
    ...
  ],
  "evidence_strength": 证据强度分数,
  "legal_basis_strength": 法律依据分数,
  "procedural_compliance": 程序合规分数,
  "opponent_weakness": 对方弱点分数,
  "precedent_support": 判例支持分数,
  "overall_analysis": "综合分析",
  "key_risks": ["风险1", "风险2"],
  "risk_mitigation": "风险缓解建议"
}}"""

        result_text = llm_service.chat([
            {"role": "system", "content": "你是一位资深法官，具有20年审判经验。请客观、公正地评估案件诉讼风险和裁判支持度参考，严禁承诺胜诉结果。返回纯JSON格式，不要包含其他文字。当前接口未接入权威类案检索，禁止编造具体法院案号、指导案例编号或判例。"},
            {"role": "user", "content": prompt}
        ], model="qwen-plus")

        import json, re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            try:
                assessment_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                assessment_data = {}
        else:
            assessment_data = {}

        win_rate = assessment_data.get("win_rate", 50.0)
        confidence = assessment_data.get("confidence", 50.0)

        assessment = WinRateAssessment(
            case_id=case_id,
            win_rate=min(100.0, max(0.0, float(win_rate))),
            confidence=min(100.0, max(0.0, float(confidence))),
            factors=assessment_data.get("factors"),
            overall_analysis=assessment_data.get("overall_analysis"),
            evidence_strength=assessment_data.get("evidence_strength"),
            legal_basis_strength=assessment_data.get("legal_basis_strength"),
            procedural_compliance=assessment_data.get("procedural_compliance"),
            opponent_weakness=assessment_data.get("opponent_weakness"),
            precedent_support=assessment_data.get("precedent_support"),
            key_risks=assessment_data.get("key_risks"),
            risk_mitigation=assessment_data.get("risk_mitigation"),
            assessment_method="ai",
        )

        db.add(assessment)

        finance = db.query(CaseFinance).filter(CaseFinance.case_id == case_id).first()
        if not finance:
            finance = CaseFinance(case_id=case_id)
            db.add(finance)
        finance.win_rate = assessment.win_rate
        finance.win_rate_confidence = assessment.confidence
        finance.win_rate_assessed_at = datetime.utcnow()

        db.commit()
        db.refresh(assessment)

        return {
            "assessment": self._assessment_to_dict(assessment),
            "cached": False,
        }

    def get_finance_statistics(self, db: Session, case_id: int) -> Dict:
        """获取财务统计"""
        expenses = db.query(ExpenseRecord).filter(ExpenseRecord.case_id == case_id).all()

        total = sum(e.amount for e in expenses)
        avg = total / len(expenses) if expenses else 0

        return {
            "case_id": case_id,
            "total_expenses": total,
            "average_expense": avg,
            "expense_count": len(expenses),
            "max_expense": max((e.amount for e in expenses), default=0),
            "min_expense": min((e.amount for e in expenses), default=0),
            "expenses_by_category": self._expenses_by_category(expenses),
            "expenses_by_status": self._expenses_by_status(expenses),
        }

    def _ensure_finance_record(self, db: Session, case_id: int) -> CaseFinance:
        """确保财务记录存在"""
        finance = db.query(CaseFinance).filter(CaseFinance.case_id == case_id).first()
        if not finance:
            finance = CaseFinance(case_id=case_id)
            db.add(finance)
            db.commit()
            db.refresh(finance)
        return finance

    def _expense_to_dict(self, expense: ExpenseRecord) -> Dict:
        return {
            "id": expense.id,
            "case_id": expense.case_id,
            "category": expense.category.value if expense.category and hasattr(expense.category, 'value') else str(expense.category) if expense.category else None,
            "title": expense.title,
            "description": expense.description,
            "amount": expense.amount,
            "currency": expense.currency,
            "status": expense.status.value if hasattr(expense.status, 'value') else str(expense.status),
            "expense_date": expense.expense_date.isoformat() if expense.expense_date else None,
            "payment_date": expense.payment_date.isoformat() if expense.payment_date else None,
            "due_date": expense.due_date.isoformat() if expense.due_date else None,
            "payee": expense.payee,
            "invoice_number": expense.invoice_number,
            "related_document_id": expense.related_document_id,
            "notes": expense.notes,
            "created_at": expense.created_at.isoformat() if expense.created_at else None,
            "updated_at": expense.updated_at.isoformat() if expense.updated_at else None,
        }

    def _assessment_to_dict(self, assessment: WinRateAssessment) -> Dict:
        return {
            "id": assessment.id,
            "case_id": assessment.case_id,
            "win_rate": assessment.win_rate,
            "confidence": assessment.confidence,
            "factors": assessment.factors,
            "overall_analysis": assessment.overall_analysis,
            "evidence_strength": assessment.evidence_strength,
            "legal_basis_strength": assessment.legal_basis_strength,
            "procedural_compliance": assessment.procedural_compliance,
            "opponent_weakness": assessment.opponent_weakness,
            "precedent_support": assessment.precedent_support,
            "key_risks": assessment.key_risks,
            "risk_mitigation": assessment.risk_mitigation,
            "assessment_method": assessment.assessment_method,
            "assessor": assessment.assessor,
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
            "updated_at": assessment.updated_at.isoformat() if assessment.updated_at else None,
        }

    def _expenses_by_category(self, expenses: List[ExpenseRecord]) -> Dict:
        result = {}
        for e in expenses:
            cat = (e.category.value if hasattr(e.category, 'value') else str(e.category)) if e.category else "other"
            if cat not in result:
                result[cat] = {"count": 0, "total": 0.0}
            result[cat]["count"] += 1
            result[cat]["total"] += e.amount
        return result

    def _expenses_by_status(self, expenses: List[ExpenseRecord]) -> Dict:
        result = {}
        for es in ExpenseStatus:
            count = len([e for e in expenses if (e.status.value if hasattr(e.status, 'value') else str(e.status)) == es.value])
            if count > 0:
                result[es.value] = count
        return result


finance_service = FinanceService()
