"""
调解策略服务

在诉讼路径之外，提供"以打促谈"的调解策略分析，
包括 BATNA 分析、和解区间计算、调解方案生成。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MediationAnalysis:
    """调解策略分析结果"""
    readiness_score: int              # 调解准备度评分 0-100
    readiness_level: str              # 准备度等级

    # BATNA 分析
    best_alternative: str             # 最佳替代方案
    worst_alternative: str            # 最差替代方案
    batna_value: float                # BATNA 估值

    # 和解区间
    settlement_floor: float           # 己方底线
    settlement_target: float          # 己方目标
    settlement_ceiling: float         # 对方预估上限
    recommended_range: str            # 建议和解区间

    # 谈判策略
    opening_position: str             # 开局立场
    concession_plan: List[str]        # 让步计划
    pressure_points: List[str]        # 施压点
    face_saving_options: List[str]    # 给对方台阶的方案

    # 调解建议
    mediation_script: str             # 调解话术


class MediationService:
    """调解策略引擎 — "法庭外的胜负手" """

    _READINESS_FACTORS = {
        "双方有继续合作的商业需求": 25,
        "案件事实争议不大": 20,
        "对方有声誉顾虑": 15,
        "诉讼成本高于争议金额": 15,
        "已有初步和解接触": 10,
        "判决执行难度大": 10,
        "一方有明显证据优势": 5,
    }

    def analyze(
        self,
        claim_amount: float,
        case_summary: str,
        evidence_strength: str = "medium",
        opponent_profile: str = "",
        prior_negotiation: str = "",
    ) -> MediationAnalysis:
        """生成完整调解策略分析。

        Args:
            claim_amount: 争议金额
            case_summary: 案件摘要
            evidence_strength: 证据力度
            opponent_profile: 对方画像
            prior_negotiation: 既往谈判情况
        """
        # 1. 调解准备度
        readiness = 30  # 基准分
        if "合作" in case_summary or "继续" in case_summary:
            readiness += 25
        if evidence_strength == "strong":
            readiness += 15
        if claim_amount < 500000:
            readiness += 15  # 小额案件调解意愿高
        if prior_negotiation:
            readiness += 10
        if "声誉" in case_summary or "品牌" in case_summary:
            readiness += 15
        readiness = min(readiness, 95)

        readiness_level = (
            "高 — 调解成功概率大，应立即启动" if readiness >= 70
            else "中 — 调解有空间，需配合诉讼施压" if readiness >= 40
            else "低 — 建议先通过诉讼建立谈判优势，再寻求调解窗口"
        )

        # 2. BATNA 分析
        if evidence_strength == "strong":
            best_alt = f"诉讼胜诉，预期可获赔 {claim_amount * 0.75:.0f} 元"
            worst_alt = f"诉讼败诉，损失诉讼费约 {claim_amount * 0.05:.0f} 元"
            batna_value = claim_amount * 0.70
        elif evidence_strength == "medium":
            best_alt = f"诉讼部分胜诉，预期获赔 {claim_amount * 0.50:.0f} 元"
            worst_alt = f"诉讼被驳回，损失诉讼费和律师费约 {claim_amount * 0.10:.0f} 元"
            batna_value = claim_amount * 0.40
        else:
            best_alt = f"诉讼侥幸胜诉，预期获赔 {claim_amount * 0.30:.0f} 元"
            worst_alt = "败诉并承担对方诉讼费"
            batna_value = claim_amount * 0.20

        # 3. 和解区间
        floor = claim_amount * 0.40  # 底线：不低于40%
        target = claim_amount * 0.65  # 目标：65%
        ceiling = claim_amount * 0.85  # 预估对方上限
        if evidence_strength == "strong":
            floor = claim_amount * 0.55
            target = claim_amount * 0.75
        elif evidence_strength == "weak":
            floor = claim_amount * 0.25
            target = claim_amount * 0.45

        recommended_range = f"¥{floor:,.0f} — ¥{target:,.0f}"

        # 4. 谈判策略
        opening_position = (
            f"正式提出¥{claim_amount * 0.90:,.0f}的和解方案（预留让步空间），"
            f"同时递交起诉状副本以展示诉讼决心。"
        )

        concession_plan = [
            f"第一轮让步：从¥{claim_amount * 0.90:,.0f}降至¥{claim_amount * 0.75:,.0f}（配合证据展示）",
            f"第二轮让步：降至¥{target:,.0f}（需对方实质性回应）",
            f"最终底线：¥{floor:,.0f}（坚守，越过此线即退出调解）",
        ]

        pressure_points = [
            "已准备好全部证据材料，可随时立案",
            "如进入诉讼，将申请财产保全冻结对方账户",
            "诉讼期间对方需承担律师费和利息损失",
            "判决公开将对对方商业信誉造成损害",
        ] if evidence_strength != "weak" else [
            "持续诉讼将消耗对方管理精力",
            "申请法院调查取证可能暴露对方其他合规问题",
        ]

        face_saving_options = [
            "同意签署保密协议，不对外披露和解内容",
            "允许分期付款，缓解对方现金流压力",
            "可接受部分非现金补偿（如以物抵债）",
            "同意在调解书中使用中性措辞，不承认过错",
        ]

        # 5. 调解话术
        mediation_script = f"""【调解开场】
"我们今天来，不是要把谁逼到绝路。公司的存续和双方的长远合作才是最重要的。
我们已经准备好了全部法律文件，但更希望通过对话解决问题。"

【核心主张】
"我们的底线很明确：事实已经很清楚，3月11日董事会决议是三方共识。
但为了表示诚意，我们在金额上可以谈。关键是恢复公司正常运营。"

【回应对方可能的"出资"论点】
"出资义务和当前的欠薪、违法停业是两个独立的法律关系。
如果贵方坚持混为一谈，我们只能请法官来厘清。但那样对谁都没有好处。"

【最后推动】
"这样吧，今天我们先确定一个框架：公司恢复经营+欠薪支付+赔偿金协商。
如果这三个方向能达成共识，具体数字可以再商量。" """

        return MediationAnalysis(
            readiness_score=readiness,
            readiness_level=readiness_level,
            best_alternative=best_alt,
            worst_alternative=worst_alt,
            batna_value=round(batna_value, 2),
            settlement_floor=round(floor, 2),
            settlement_target=round(target, 2),
            settlement_ceiling=round(ceiling, 2),
            recommended_range=recommended_range,
            opening_position=opening_position,
            concession_plan=concession_plan,
            pressure_points=pressure_points,
            face_saving_options=face_saving_options,
            mediation_script=mediation_script,
        )

    def generate_mediation_brief(
        self,
        analysis: MediationAnalysis,
        case_info: dict,
    ) -> str:
        """生成调解策略备忘录（Markdown格式）"""
        return f"""# 调解策略备忘录

## 案件信息
- 案件：{case_info.get('title', '')}
- 当事人：{case_info.get('plaintiff', '')} v. {case_info.get('defendant', '')}

## 调解准备度：{analysis.readiness_score}/100
{analysis.readiness_level}

## BATNA 分析
- 最佳替代方案：{analysis.best_alternative}
- 最差替代方案：{analysis.worst_alternative}
- BATNA 估值：¥{analysis.batna_value:,.2f}

## 和解区间
- 己方底线：¥{analysis.settlement_floor:,.2f}
- 己方目标：¥{analysis.settlement_target:,.2f}
- 预估对方上限：¥{analysis.settlement_ceiling:,.2f}
- **建议和解区间：{analysis.recommended_range}**

## 谈判策略
### 开局
{analysis.opening_position}

### 让步计划
{chr(10).join(f'- {c}' for c in analysis.concession_plan)}

### 施压点
{chr(10).join(f'- {p}' for p in analysis.pressure_points)}

### 给对方台阶
{chr(10).join(f'- {o}' for o in analysis.face_saving_options)}

## 调解话术
{analysis.mediation_script}
"""


mediation_service = MediationService()
