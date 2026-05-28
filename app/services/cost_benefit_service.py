"""
诉讼成本与收益分析服务

为案件提供全面的成本-收益分析，帮助客户做出理性诉讼决策。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CostEstimate:
    """费用估算明细"""
    court_filing_fee: float = 0       # 法院受理费
    preservation_fee: float = 0       # 财产保全费
    appraisal_fee: float = 0          # 鉴定评估费
    lawyer_fee: float = 0             # 律师代理费
    travel_expenses: float = 0        # 差旅费
    notary_fee: float = 0             # 公证费
    other: float = 0                  # 其他费用
    total: float = 0

    def to_dict(self) -> dict:
        return {
            "court_filing_fee": round(self.court_filing_fee, 2),
            "preservation_fee": round(self.preservation_fee, 2),
            "appraisal_fee": round(self.appraisal_fee, 2),
            "lawyer_fee": round(self.lawyer_fee, 2),
            "travel_expenses": round(self.travel_expenses, 2),
            "notary_fee": round(self.notary_fee, 2),
            "other": round(self.other, 2),
            "total": round(self.total, 2),
        }


@dataclass
class CostBenefitResult:
    """成本收益分析结果"""
    claim_amount: float               # 诉讼标的额
    cost: CostEstimate                # 费用明细
    estimated_recovery: float         # 预估回收金额
    win_probability: float            # 预估胜诉概率
    time_to_resolution_months: int    # 预估审理周期（月）
    net_expected_value: float         # 净期望收益
    roi: float                        # 投资回报率
    recommendation: str               # 综合建议
    risk_factors: List[str] = field(default_factory=list)
    cost_saving_tips: List[str] = field(default_factory=list)


class CostBenefitService:
    """诉讼成本-收益分析引擎"""

    # 法院受理费计算规则（财产案件，按《诉讼费用交纳办法》）
    _FILING_FEE_BRACKETS = [
        (0, 10000, 50, 0.00),
        (10000, 100000, 0, 0.025),
        (100000, 200000, 0, 0.02),
        (200000, 500000, 0, 0.015),
        (500000, 1000000, 0, 0.01),
        (1000000, 2000000, 0, 0.009),
        (2000000, 5000000, 0, 0.008),
        (5000000, 10000000, 0, 0.007),
        (10000000, float("inf"), 0, 0.005),
    ]

    @staticmethod
    def calc_filing_fee(claim_amount: float) -> float:
        """计算法院受理费"""
        for low, high, base, rate in CostBenefitService._FILING_FEE_BRACKETS:
            if claim_amount <= low:
                return 0
            if claim_amount <= high:
                return base + (claim_amount - low) * rate
        return 0

    @staticmethod
    def calc_preservation_fee(claim_amount: float) -> float:
        """计算财产保全费"""
        if claim_amount <= 1000:
            return 30
        portions = [
            (1000, 100000, 0.01),
            (100000, float("inf"), 0.005),
        ]
        fee = 0
        remaining = claim_amount
        prev_high = 0
        for low, high, rate in portions:
            if remaining <= 0:
                break
            bracket_amount = min(remaining, high - low)
            fee += bracket_amount * rate
            remaining -= bracket_amount
            prev_high = high
        return min(max(fee, 30), 5000)

    def analyze(
        self,
        claim_amount: float,
        case_type: str = "合同纠纷",
        complexity: str = "medium",
        evidence_strength: str = "medium",
        jurisdiction: str = "郑州",
    ) -> CostBenefitResult:
        """执行完整的成本收益分析。

        Args:
            claim_amount: 诉讼标的额
            case_type: 案件类型
            complexity: 复杂度 (simple/medium/complex)
            evidence_strength: 证据力度 (weak/medium/strong)
            jurisdiction: 管辖地
        """
        # 1. 费用计算
        cost = CostEstimate()
        cost.court_filing_fee = self.calc_filing_fee(claim_amount)
        cost.preservation_fee = self.calc_preservation_fee(claim_amount) if claim_amount > 0 else 0

        # 律师费估算
        lawyer_rates = {"simple": 0.05, "medium": 0.08, "complex": 0.12}
        rate = lawyer_rates.get(complexity, 0.08)
        cost.lawyer_fee = max(claim_amount * rate, 5000)

        # 其他费用估算
        cost.appraisal_fee = claim_amount * 0.005 if complexity == "complex" else 0
        cost.travel_expenses = 2000 if jurisdiction != "本地" else 500
        cost.notary_fee = 800 if evidence_strength == "weak" else 300
        cost.total = sum([
            cost.court_filing_fee, cost.preservation_fee,
            cost.appraisal_fee, cost.lawyer_fee,
            cost.travel_expenses, cost.notary_fee, cost.other
        ])

        # 2. 胜诉概率估算
        prob_map = {
            ("strong", "simple"): 0.85,
            ("strong", "medium"): 0.75,
            ("strong", "complex"): 0.65,
            ("medium", "simple"): 0.70,
            ("medium", "medium"): 0.60,
            ("medium", "complex"): 0.50,
            ("weak", "simple"): 0.55,
            ("weak", "medium"): 0.40,
            ("weak", "complex"): 0.30,
        }
        win_prob = prob_map.get((evidence_strength, complexity), 0.55)

        # 3. 执行到位率估算
        recovery_rates = {"合同纠纷": 0.65, "侵权纠纷": 0.55, "劳动争议": 0.80, "股权纠纷": 0.50}
        recovery_rate = recovery_rates.get(case_type, 0.60)
        estimated_recovery = claim_amount * win_prob * recovery_rate

        # 4. 审理周期
        time_map = {"simple": 4, "medium": 8, "complex": 14}
        time_months = time_map.get(complexity, 8)

        # 5. 净收益和ROI
        net_value = estimated_recovery - cost.total
        roi = (net_value / cost.total * 100) if cost.total > 0 else 0

        # 6. 建议
        if net_value > cost.total * 3 and win_prob > 0.6:
            recommendation = "强烈建议起诉 — 预期收益远高于成本，证据有力。"
        elif net_value > cost.total and win_prob > 0.5:
            recommendation = "建议起诉 — 净收益为正，但需控制诉讼成本。可考虑风险代理。"
        elif net_value > 0:
            recommendation = "审慎起诉 — 预期收益微薄。强烈建议先尝试调解。"
        else:
            recommendation = "不建议起诉 — 诉讼成本可能超过预期回收。优先考虑非诉讼解决方案。"

        # 7. 风险提示
        risk_factors = []
        if complexity == "complex":
            risk_factors.append("案件复杂，审理周期可能延长至1年以上")
        if evidence_strength == "weak":
            risk_factors.append("证据力度不足，需尽快补充关键证据")
        if win_prob < 0.5:
            risk_factors.append("胜诉概率偏低，对方可能利用程序拖延")
        if claim_amount > 500000:
            risk_factors.append("标的额较大，建议申请财产保全以保障判决执行")

        # 8. 省钱建议
        cost_saving_tips = [
            "可申请缓交/减交诉讼费（需提供困难证明）",
            "小额案件可自行诉讼，减少律师费支出",
        ]
        if claim_amount > 100000:
            cost_saving_tips.append("可协商风险代理（胜诉后按比例付费），降低前期支出")
        if complexity == "simple":
            cost_saving_tips.append("可适用简易程序，诉讼费减半")

        return CostBenefitResult(
            claim_amount=claim_amount,
            cost=cost,
            estimated_recovery=round(estimated_recovery, 2),
            win_probability=round(win_prob, 3),
            time_to_resolution_months=time_months,
            net_expected_value=round(net_value, 2),
            roi=round(roi, 1),
            recommendation=recommendation,
            risk_factors=risk_factors,
            cost_saving_tips=cost_saving_tips,
        )


cost_benefit_service = CostBenefitService()
