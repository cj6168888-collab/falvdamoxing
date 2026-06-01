from app.services.mediation_service import MediationService


def test_mediation_analysis_uses_reviewable_workpaper_wording():
    service = MediationService()

    analysis = service.analyze(
        claim_amount=100000,
        case_summary="双方有继续合作基础，案件涉及品牌声誉",
        evidence_strength="strong",
        prior_negotiation="已初步沟通",
    )
    brief = service.generate_mediation_brief(
        analysis,
        {"title": "合同纠纷", "plaintiff": "甲方", "defendant": "乙方"},
    )

    forbidden = [
        "调解成功概率大",
        "诉讼胜诉",
        "诉讼败诉",
        "部分胜诉",
        "侥幸胜诉",
        "胜负手",
        "施压点",
        "事实已经很清楚",
        "违法停业",
    ]

    combined = "\n".join(
        [
            analysis.readiness_level,
            analysis.best_alternative,
            analysis.worst_alternative,
            brief,
        ]
    )

    for term in forbidden:
        assert term not in combined

    assert "调解达成可能性较高" in analysis.readiness_level
    assert "诉讼请求获得较高支持" in analysis.best_alternative
    assert "谈判风险提示" in brief
    assert "现有材料显示" in brief
