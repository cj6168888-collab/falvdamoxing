"""
合同风险审查集成服务（biz-8）
将 legal_protection 和 trap_detector 集成到合同模板流程

集成内容：
1. 合同风险深度扫描（legal_protection 系统）
2. 条款陷阱识别（trap_detector 系统）
3. 合同审查建议生成
4. 签约风险评估
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict

from app.services.legal_protection import LegalAIProtectionSystem
from app.services.trap_detector import TrapDetector


@dataclass
class ContractRiskReport:
    """
    合同风险审查报告
    """
    contract_name: str
    review_date: datetime
    overall_risk_level: str  # high/medium/low
    
    # 风险统计
    total_risks: int = 0
    high_risk: int = 0
    medium_risk: int = 0
    low_risk: int = 0
    
    # 条款分析
    clause_analysis: List[Dict] = field(default_factory=list)
    
    # 陷阱识别
    detected_traps: List[Dict] = field(default_factory=list)
    
    # 风险要点
    key_risks: List[str] = field(default_factory=list)
    
    # 签约建议
    signing_advice: str = ""
    recommended_modifications: List[str] = field(default_factory=list)
    negotiation_points: List[str] = field(default_factory=list)
    
    # 引用法条
    cited_laws: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['review_date'] = self.review_date.isoformat()
        return result


class ContractRiskReviewService:
    """
    合同风险审查集成服务（biz-8）
    
    将以下服务集成到统一的合同审查流程：
    - legal_protection: 合同法律风险识别
    - trap_detector: 合同条款陷阱检测
    """
    
    # 合同风险类型定义
    RISK_CATEGORIES = {
        "主体风险": {
            "keywords": ["无权代理", "超越权限", "主体不适格", "资质不足"],
            "severity": "high",
            "legal_basis": "《民法典》第171条（无权代理）、第172条（表见代理）"
        },
        "标的风险": {
            "keywords": ["标的违法", "标的不能", "标的瑕疵", "标的争议"],
            "severity": "high",
            "legal_basis": "《民法典》第143条（民事法律行为有效条件）"
        },
        "履约能力风险": {
            "keywords": ["资金不足", "履约能力", "财务状况", "信用记录"],
            "severity": "high",
            "legal_basis": "《民法典》第500条（先合同义务）、第509条（合同履行）"
        },
        "条款模糊风险": {
            "keywords": ["另行约定", "参照执行", "酌情处理", "协商解决"],
            "severity": "medium",
            "legal_basis": "《民法典》第470条（合同条款解释规则）"
        },
        "违约责任风险": {
            "keywords": ["违约金过高", "赔偿无上限", "单方解除", "不可抗力"],
            "severity": "medium",
            "legal_basis": "《民法典》第585条（违约金调整）、第563条（法定解除）"
        },
        "争议解决风险": {
            "keywords": ["仲裁条款", "管辖法院", "适用法律", "送达地址"],
            "severity": "medium",
            "legal_basis": "《民事诉讼法》第34条（协议管辖）"
        },
        "格式条款风险": {
            "keywords": ["格式条款", "免责条款", "限制责任", "加重对方责任"],
            "severity": "medium",
            "legal_basis": "《民法典》第496-498条（格式条款规制）"
        },
        "附随义务风险": {
            "keywords": ["保密义务", "竞业限制", "通知义务", "协助义务"],
            "severity": "low",
            "legal_basis": "《民法典》第509条（合同附随义务）"
        }
    }
    
    def __init__(self):
        self.protection_system = LegalAIProtectionSystem()
        self.trap_detector = TrapDetector()
        self.risk_categories = self.RISK_CATEGORIES
    
    def review_contract(
        self,
        contract_text: str,
        contract_name: str = "合同",
        contract_type: str = "通用",
        user_position: str = "中立"
    ) -> ContractRiskReport:
        """
        综合审查合同风险
        
        Args:
            contract_text: 合同文本内容
            contract_name: 合同名称
            contract_type: 合同类型（买卖/租赁/劳动/借贷/服务等）
            user_position: 用户立场（有利/不利/中立）
            
        Returns:
            ContractRiskReport 综合风险报告
        """
        report = ContractRiskReport(
            contract_name=contract_name,
            review_date=datetime.now(),
            overall_risk_level="low"
        )
        
        # 1. 基础风险扫描
        clause_analysis = self._scan_clauses(contract_text)
        report.clause_analysis = clause_analysis
        
        # 2. 陷阱条款识别
        traps = self._detect_traps_in_contract(contract_text)
        report.detected_traps = traps
        
        # 3. 风险评级
        risk_stats = self._calculate_risk_stats(clause_analysis, traps)
        report.total_risks = risk_stats["total"]
        report.high_risk = risk_stats["high"]
        report.medium_risk = risk_stats["medium"]
        report.low_risk = risk_stats["low"]
        
        # 4. 确定总体风险等级
        if risk_stats["high"] > 0:
            report.overall_risk_level = "high"
        elif risk_stats["medium"] > 0:
            report.overall_risk_level = "medium"
        else:
            report.overall_risk_level = "low"
        
        # 5. 提取风险要点
        report.key_risks = self._extract_key_risks(clause_analysis, traps)
        
        # 6. 生成签约建议
        advice = self._generate_signing_advice(
            contract_text, risk_stats, user_position
        )
        report.signing_advice = advice["main"]
        report.recommended_modifications = advice["modifications"]
        report.negotiation_points = advice["negotiation"]
        
        # 7. 提取引用法条
        report.cited_laws = self._extract_cited_laws(clause_analysis, traps)
        
        return report
    
    def _scan_clauses(self, contract_text: str) -> List[Dict]:
        """
        扫描合同条款，识别风险
        """
        analysis_results = self.protection_system.process_query(
            query="合同风险审查",
            user_case_facts=contract_text,
            user_position="不利",
            case_direction="contain"
        )
        
        clause_results = []
        
        # 基础关键词扫描
        for category, info in self.risk_categories.items():
            matched_keywords = []
            for keyword in info["keywords"]:
                if keyword in contract_text:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                # 提取含关键词的上下文
                context_clauses = self._extract_clause_context(
                    contract_text, matched_keywords
                )
                
                clause_results.append({
                    "category": category,
                    "severity": info["severity"],
                    "legal_basis": info["legal_basis"],
                    "matched_keywords": matched_keywords,
                    "context_clauses": context_clauses,
                    "suggestion": self._get_category_suggestion(category)
                })
        
        return clause_results
    
    def _detect_traps_in_contract(self, contract_text: str) -> List[Dict]:
        """
        识别合同中的条款陷阱
        """
        traps_found = []
        
        # 按段落/条款分割检测
        clauses = contract_text.split('\n')
        
        for clause in clauses:
            clause = clause.strip()
            if len(clause) < 5:
                continue
            
            # 使用 trap_detector 检测
            trap_result = self.trap_detector.detect_trap(clause, "other")
            
            if trap_result["is_trap"]:
                traps_found.append({
                    "clause": clause[:100] + "..." if len(clause) > 100 else clause,
                    "trap_type": trap_result["trap_types"],
                    "severity": trap_result["severity"],
                    "confidence": trap_result["confidence"],
                    "suggestion": trap_result["suggestion"]
                })
        
        return traps_found
    
    def _calculate_risk_stats(
        self, 
        clause_analysis: List[Dict],
        traps: List[Dict]
    ) -> Dict:
        """计算风险统计"""
        stats = {"total": 0, "high": 0, "medium": 0, "low": 0}
        
        for clause in clause_analysis:
            severity = clause.get("severity", "low")
            if severity in stats:
                stats[severity] += 1
                stats["total"] += 1
        
        for trap in traps:
            severity = trap.get("severity", "low")
            if severity in stats:
                stats[severity] += 1
                stats["total"] += 1
        
        return stats
    
    def _extract_key_risks(
        self,
        clause_analysis: List[Dict],
        traps: List[Dict]
    ) -> List[str]:
        """提取关键风险点"""
        risks = []
        
        # 高风险条款
        for clause in clause_analysis:
            if clause.get("severity") == "high":
                risks.append(
                    f"【{clause['category']}】{', '.join(clause.get('matched_keywords', []))}，"
                    f"依据：{clause.get('legal_basis', '')}"
                )
        
        # 高风险陷阱
        for trap in traps:
            if trap.get("severity") == "high":
                risks.append(
                    f"【条款陷阱】{trap['trap_type'][0] if trap['trap_type'] else '未知陷阱'}：{trap['clause']}"
                )
        
        return risks
    
    def _generate_signing_advice(
        self,
        contract_text: str,
        risk_stats: Dict,
        user_position: str
    ) -> Dict:
        """生成签约建议"""
        advice = {
            "main": "",
            "modifications": [],
            "negotiation": []
        }
        
        # 总体建议
        if risk_stats["high"] > 0:
            advice["main"] = (
                f"⚠️ 该合同存在 {risk_stats['high']} 项高风险条款，建议在签署前进行重大修改。"
                f"建议委托专业律师进行详细审查，必要时拒绝签署。"
            )
        elif risk_stats["medium"] > 0:
            advice["main"] = (
                f"⚡ 该合同存在 {risk_stats['medium']} 项中等风险条款，建议在签署前争取修改。"
                f"以下是建议修改的具体条款。"
            )
        else:
            advice["main"] = (
                f"✅ 该合同整体风险较低，建议关注格式条款和争议解决条款后签署。"
            )
        
        # 具体修改建议
        for clause in clause_analysis:
            if clause.get("severity") in ["high", "medium"]:
                suggestion = clause.get("suggestion", "")
                if suggestion:
                    advice["modifications"].append(
                        f"{clause['category']}：{suggestion}"
                    )
        
        # 谈判要点
        negotiation_points = {
            "主体风险": "要求对方提供资质证明、授权文件",
            "标的风险": "明确标的规格、质量标准",
            "履约能力风险": "要求提供履约担保或预付款",
            "条款模糊风险": "要求明确具体标准和计算方式",
            "违约责任风险": "争取调整违约金比例",
            "争议解决风险": "争取选择对己方有利的管辖法院",
            "格式条款风险": "要求修改或删除不公平格式条款",
            "附随义务风险": "确保义务边界清晰"
        }
        
        for clause in clause_analysis:
            category = clause.get("category", "")
            if category in negotiation_points:
                advice["negotiation"].append(negotiation_points[category])
        
        return advice
    
    def _extract_clause_context(
        self, 
        text: str, 
        keywords: List[str]
    ) -> List[str]:
        """提取含关键词的条款上下文"""
        contexts = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            for keyword in keywords:
                if keyword in line:
                    # 包含前后各一行作为上下文
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    context = '\n'.join(lines[start:end])
                    if context not in contexts:
                        contexts.append(context)
                    break
        
        return contexts[:5]  # 最多返回5个上下文
    
    def _get_category_suggestion(self, category: str) -> str:
        """获取类别建议"""
        suggestions = {
            "主体风险": "建议核实对方主体资格，要求提供营业执照、授权委托书等证明文件",
            "标的风险": "建议明确标的物的具体规格、质量标准、交付要求",
            "履约能力风险": "建议要求对方提供财务证明或履约担保",
            "条款模糊风险": "建议要求将模糊条款具体化，明确计算方式和标准",
            "违约责任风险": "建议审查违约金是否过高，争取合理比例",
            "争议解决风险": "建议选择中立法院管辖，或争取己方所在地法院",
            "格式条款风险": "根据《民法典》第496-498条，格式条款中不合理地免除己方责任、加重对方责任的条款无效",
            "附随义务风险": "建议明确附随义务的范围和违反后果"
        }
        return suggestions.get(category, "建议仔细审查相关条款")
    
    def _extract_cited_laws(
        self,
        clause_analysis: List[Dict],
        traps: List[Dict]
    ) -> List[Dict]:
        """提取报告中的引用法条"""
        laws = {}
        
        # 从条款分析中提取
        for clause in clause_analysis:
            basis = clause.get("legal_basis", "")
            if basis and "《" in basis:
                law_name = basis.split("《")[1].split("》")[0] if "《" in basis else basis
                article = basis.split("第")[1].split("条")[0] if "第" in basis else ""
                
                key = f"{law_name}_{article}"
                if key not in laws:
                    laws[key] = {
                        "law_name": law_name,
                        "article": f"第{article}条" if article else "",
                        "basis": basis
                    }
        
        return list(laws.values())
    
    def quick_scan(self, contract_text: str) -> Dict:
        """
        快速扫描合同，返回简明风险提示
        适用于列表页快速预览
        """
        scan_result = {
            "risk_level": "low",
            "risk_count": 0,
            "key_issues": []
        }
        
        clauses = contract_text.split('\n')
        
        high_risk_keywords = {
            "无条件解除": "单方无条件解除权风险",
            "违约金100%": "违约金过高风险",
            "一切损失": "赔偿范围过大风险",
            "放弃抗辩": "诉讼权利放弃风险",
            "不可抗力免责": "不可抗力范围过宽风险",
            "最终解释权": "格式条款解释权风险",
            "无条件配合": "义务范围不清风险",
        }
        
        issues = []
        for clause in clauses:
            for keyword, issue in high_risk_keywords.items():
                if keyword in clause:
                    issues.append({
                        "keyword": keyword,
                        "issue": issue,
                        "clause_preview": clause[:50]
                    })
        
        scan_result["risk_count"] = len(issues)
        scan_result["key_issues"] = issues
        
        if len(issues) >= 3:
            scan_result["risk_level"] = "high"
        elif len(issues) > 0:
            scan_result["risk_level"] = "medium"
        
        return scan_result

    def review(self, content: str, case_id: int = None, db=None) -> Dict:
        """便捷入口 — 合同风险全面审查。

        先执行 quick_scan 进行规则扫描，再调用 LLM 进行深度风险分析。
        """
        scan = self.quick_scan(content)

        llm_analysis = ""
        try:
            from app.services.llm_service import llm_service

            prompt = f"""你是合同风险审查专家。请审查以下合同，指出风险点并给出修改建议。

合同内容：
{content[:8000]}

请按以下格式输出：
1. 风险等级（高/中/低）
2. 主要风险点（每个风险点包含：条款位置、风险描述、修改建议）
3. 总体评估"""

            llm_analysis = llm_service.chat([
                {"role": "system", "content": "你是资深合同审查律师。"},
                {"role": "user", "content": prompt}
            ])
        except Exception:
            llm_analysis = "LLM 深度分析暂不可用"

        return {
            "scan": scan,
            "llm_analysis": llm_analysis,
            "risk_level": scan.get("risk_level", "low"),
            "risk_count": scan.get("risk_count", 0),
            "key_issues": scan.get("key_issues", []),
        }


# 全局实例
contract_risk_review_service = ContractRiskReviewService()
