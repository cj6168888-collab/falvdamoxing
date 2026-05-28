"""
跨模块上下文服务 - 打通证据、庭审、执行、上诉之间的数据隔离
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.evidence import EvidenceItem
from app.models.execution import ExecutionAsset, AssetType
from app.models.hearing import HearingRecord, EvidenceUse
import json

class ContextService:
    """系统上下文联动服务"""

    def suggest_execution_assets_from_evidence(self, db: Session, case_id: int) -> List[Dict]:
        """
        从案件证据中提取潜在的财产线索
        分析 EvidenceItem 中的 proves_facts，寻找涉及财产、金额、支付的信息
        """
        evidence_items = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == case_id
        ).all()

        suggestions = []
        asset_keywords = ["财产", "资金", "支付", "银行", "转账", "账号", "房产", "车辆", "股权", "债权"]
        
        for item in evidence_items:
            facts = item.proves_facts or []
            is_relevant = False
            found_reason = ""
            
            # 简单关键词匹配 proves_facts 中的文字
            facts_text = json.dumps(facts, ensure_ascii=False)
            for kw in asset_keywords:
                if kw in facts_text:
                    is_relevant = True
                    found_reason = f"证据「{item.display_name or item.original_filename}」中提到「{kw}」相关事实"
                    break
            
            if is_relevant:
                # 构造建议的财产对象
                suggestions.append({
                    "evidence_id": item.id,
                    "evidence_name": item.display_name or item.original_filename,
                    "suggested_asset_name": (item.display_name or "潜在财产线索").replace("证据", "资产"),
                    "reason": found_reason,
                    "evidence_summary": item.summary,
                    "file_path": item.file_path,
                    "confidence": 0.8 if any(kw in facts_text for kw in ["财产", "资金", "账号"]) else 0.5
                })
        
        return suggestions

    def link_evidence_to_hearing(self, db: Session, hearing_record_id: int, evidence_ids: List[str]):
        """
        将证据关联到特定的庭审记录中
        """
        record = db.query(HearingRecord).filter(HearingRecord.id == hearing_record_id).first()
        if not record:
            return False
            
        current_ids = record.live_suggestions.get("related_evidence_ids", []) if record.live_suggestions else []
        new_ids = list(set(current_ids + evidence_ids))
        
        if not record.live_suggestions:
            record.live_suggestions = {}
        record.live_suggestions["related_evidence_ids"] = new_ids
        
        db.commit()
        return True

    def suggest_appeal_points_from_hearing(self, db: Session, case_id: int) -> List[Dict]:
        """
        根据庭审记录中的事实结论，识别潜在的上诉点
        """
        hearings = db.query(HearingRecord).filter(HearingRecord.case_id == case_id).all()
        points = []
        
        for h in hearings:
            if h.live_suggestions and "fact_conclusions" in h.live_suggestions:
                conclusions = h.live_suggestions["fact_conclusions"]
                for c in conclusions:
                    if "争议" in c or "未被采信" in str(c):
                        points.append({
                            "hearing_id": h.id,
                            "fact_conclusion": c,
                            "suggested_appeal_point": f"针对庭审结论「{c[:20]}...」的上诉理由",
                            "severity": "high"
                        })
        return points

context_service = ContextService()
