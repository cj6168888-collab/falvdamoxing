"""
案件全景情报服务 - 系统唯一的情报聚合与分发中心
打通证据、庭审、执行、财务数据孤岛
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.models.case import Case, Party, CounterClaim
from app.models.evidence import EvidenceItem
from app.models.hearing import HearingRecord
from app.models.execution import ExecutionRecord, ExecutionAsset
from app.models.appeal import AppealRecord
from app.models.finance import CaseFinance
from app.models.case_claim import CaseClaim
from app.services.extraction_service import extraction_service

class IntelligenceService:
    """全景情报聚合服务"""

    def sync_intelligence(self, db: Session, case_id: int, ai_text: str) -> Dict[str, Any]:
        """
        根据 AI 分析文本同步系统状态
        1. 自动更新当事人信息
        2. 自动发现并更新潜在的诉讼请求（战役）
        """
        # 1. 更新当事人
        party_sync = extraction_service.auto_update_case_parties(db, case_id, ai_text)
        
        # 2. 尝试从文本中提取并同步诉讼请求 (JSON 格式)
        json_data = extraction_service.extract_json_from_markdown(ai_text)
        claims_added = 0
        if json_data and "suggested_claims" in json_data:
            claims_added = extraction_service.sync_suggested_claims(db, case_id, json_data["suggested_claims"])
            
        return {
            "party_sync": party_sync,
            "claims_added": claims_added
        }

    def build_comprehensive_dossier(self, db: Session, case_id: int) -> Dict[str, Any]:
        """
        构建最完整的案件档案 JSON，用于 AI 对话、画像生成、文书起草
        """
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"error": "案件不存在"}

        # 1. 基础信息与战役
        claims = db.query(CaseClaim).filter(CaseClaim.case_id == case_id).all()
        parties = db.query(Party).filter(Party.case_id == case_id).all()
        
        # 2. 证据 V2 (核心情报源)
        evidence_items = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).all()
        
        # 3. 庭审事实 (质证结论)
        hearings = db.query(HearingRecord).filter(HearingRecord.case_id == case_id).all()
        
        # 4. 执行状态与资产
        assets = db.query(ExecutionAsset).filter(ExecutionAsset.case_id == case_id).all()
        execution_records = db.query(ExecutionRecord).filter(ExecutionRecord.case_id == case_id).all()
        
        # 5. 财务状况
        finance = db.query(CaseFinance).filter(CaseFinance.case_id == case_id).first()

        # 构建聚合数据结构
        dossier = {
            "case_metadata": {
                "id": case.id,
                "title": case.title,
                "case_number": case.case_number,
                "status": case.status,
                "case_type": case.case_type,
                "cause": case.cause,
                "claim_amount": case.claim_amount,
                "description": case.description,
                "legal_analysis": case.legal_analysis,
                "strategy": case.strategy_suggestion
            },
            "parties": [
                {"name": p.name, "role": p.role.value if hasattr(p.role, 'value') else p.role, "type": p.party_type} 
                for p in parties
            ],
            "claims_and_war_plans": [
                {
                    "title": c.title,
                    "status": c.status,
                    "target_amount": c.amount,
                    "ai_plan": c.ai_plan_result
                } for c in claims
            ],
            "evidence_v2": [
                {
                    "id": e.id,
                    "name": e.display_name or e.original_filename,
                    "type": e.evidence_type,
                    "summary": e.summary,
                    "proves_facts": e.proves_facts,
                    "credibility": e.credibility_score
                } for e in evidence_items
            ],
            "hearing_notes": [
                {
                    "date": h.hearing_date.isoformat() if h.hearing_date else None,
                    "summary": h.summary,
                    "fact_conclusions": h.live_suggestions.get("fact_conclusions", []) if h.live_suggestions else []
                } for h in hearings
            ],
            "execution_intelligence": {
                "assets_discovered": [
                    {"name": a.asset_name, "type": a.asset_type, "value": a.estimated_value, "status": a.status}
                    for a in assets
                ],
                "latest_progress": [
                    {"date": r.record_date.isoformat() if r.record_date else None, "title": r.title, "content": r.content}
                    for r in execution_records[-5:] # 最近5条
                ]
            },
            "financial_summary": {
                "total_expenses": finance.total_expenses if finance else None,
                "total_paid": finance.total_paid if finance else None,
                "total_pending": finance.total_pending if finance else None,
                "expected_recovery": finance.expected_recovery if finance else None,
                "win_rate_estimate": finance.win_rate if finance else None
            }
        }
        
        return dossier

    def get_summary_for_ai(self, db: Session, case_id: int) -> str:
        """转换档案为适合 LLM 阅读的 Markdown 文档"""
        d = self.build_comprehensive_dossier(db, case_id)
        if "error" in d:
            return d["error"]
            
        md = f"# 案件全景情报档案: {d['case_metadata']['title']}\n\n"
        md += f"## 1. 基础概括\n- **案号**: {d['case_metadata']['case_number'] or '未分配'}\n- **当前阶段**: {d['case_metadata']['status']}\n- **案由**: {d['case_metadata']['cause']}\n- **诉讼金额**: {d['case_metadata']['claim_amount'] or '未填'}\n\n"
        
        md += "## 2. 关键证据及证明事实\n"
        if not d['evidence_v2']:
            md += "（暂无证据记录）\n"
        for ev in d['evidence_v2']:
            md += f"- **{ev['name']}** ({ev['type']}): {ev['summary']}\n"
            if ev['proves_facts']:
                md += f"  - 证明事实: {json.dumps(ev['proves_facts'], ensure_ascii=False)}\n"
        
        if d['hearing_notes']:
            md += "\n## 3. 往期庭审/沟通关键结论\n"
            for h in d['hearing_notes']:
                md += f"- [{h['date']}] {h['summary'] or '记录'}\n"
                if h['fact_conclusions']:
                    md += f"  - 事实结论: {', '.join(h['fact_conclusions'])}\n"
        
        if d['execution_intelligence']['assets_discovered']:
            md += "\n## 4. 财产线索发现 (执行参考)\n"
            for a in d['execution_intelligence']['assets_discovered']:
                md += f"- {a['name']} ({a['type']}): 估值 {a['value']}, 状态 {a['status']}\n"
        
        fin = d.get('financial_summary', {})
        if fin.get('win_rate_estimate'):
            md += f"\n## 5. 综合评估\n- **胜诉概率预估**: {fin['win_rate_estimate']}\n"

        md += "\n---\n⚠️ 法律分析与策略建议（参考）：\n"
        md += f"- 分析：{d['case_metadata']['legal_analysis'] or '待生成'}\n"
        md += f"- 策略：{d['case_metadata']['strategy'] or '待生成'}\n"
                
        return md

    def get_knowledge_atoms(self, db: Session, case_id: int) -> List[Dict[str, Any]]:
        """
        为画像系统提供“知识原子”列表
        合并基础信息、V2证据事实、庭审发现等
        """
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return []

        atoms = []
        now_str = datetime.utcnow().isoformat()

        # 1. 基础信息原子
        if case.plaintiff:
            atoms.append({"atom_id": f"fact_p_{case.id}", "content": f"原告: {case.plaintiff}", "type": "fact", "source": "case_info", "confidence": 1.0, "verified": True, "keywords": ["原告"], "extracted_at": now_str})
        if case.defendant:
            atoms.append({"atom_id": f"fact_d_{case.id}", "content": f"被告: {case.defendant}", "type": "fact", "source": "case_info", "confidence": 1.0, "verified": True, "keywords": ["被告"], "extracted_at": now_str})
        if case.cause:
            atoms.append({"atom_id": f"claim_c_{case.id}", "content": f"案由: {case.cause}", "type": "claim", "source": "case_info", "confidence": 1.0, "verified": True, "keywords": ["案由"], "extracted_at": now_str})

        # 2. 证据 V2 事实原子 (核心增强)
        evidence_items = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).all()
        for ev in evidence_items:
            # 基础摘要原子
            atoms.append({
                "atom_id": f"ev_sum_{ev.id}",
                "content": f"证据[{ev.display_name or ev.original_filename}]摘要: {ev.summary}",
                "type": "evidence",
                "source": "evidence_v2",
                "confidence": 0.9,
                "verified": False,
                "keywords": ev.keywords or [],
                "extracted_at": now_str
            })
            # 结构化事实原子
            if ev.proves_facts:
                for i, fact_obj in enumerate(ev.proves_facts):
                    fact_text = fact_obj.get("fact") if isinstance(fact_obj, dict) else str(fact_obj)
                    conf = fact_obj.get("confidence", 0.8) if isinstance(fact_obj, dict) else 0.8
                    atoms.append({
                        "atom_id": f"ev_fact_{ev.id}_{i}",
                        "content": f"证明事实: {fact_text}",
                        "type": "fact",
                        "source": "evidence_v2_analysis",
                        "confidence": conf,
                        "verified": False,
                        "keywords": ["证明事实"],
                        "extracted_at": now_str
                    })

        # 3. 执行资产原子 (跨模块发现)
        assets = db.query(ExecutionAsset).filter(ExecutionAsset.case_id == case_id).all()
        for asset in assets:
            atoms.append({
                "atom_id": f"asset_{asset.id}",
                "content": f"发现资产: {asset.asset_name} ({asset.asset_type}) - 估值 {asset.estimated_value}",
                "type": "fact",
                "source": "execution_discovery",
                "confidence": 1.0, 
                "verified": True if asset.status != 'discovered' else False,
                "keywords": ["财产", "执行"],
                "extracted_at": now_str
            })

        return atoms

intelligence_service = IntelligenceService()
