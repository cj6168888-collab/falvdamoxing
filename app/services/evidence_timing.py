"""
证据使用时机分析服务 - 精准把握证据出示时机
帮助用户在最恰当的时机出示证据，发挥最大效用
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.services.llm_service import llm_service


class EvidenceTimingAnalyzer:
    """
    证据使用时机分析器
    
    功能：
    1. 分析证据的最佳出示时机
    2. 评估证据之间的协同效应
    3. 识别证据出示的窗口期
    4. 预测对方可能的证据策略
    5. 生成证据使用策略
    """
    
    # 证据类型及其最佳使用时机
    EVIDENCE_TIMING_RULES = {
        "contract": {
            "name": "合同证据",
            "optimal_phases": ["opening", "fact_presentation"],
            "avoid_phases": [],
            "best_moment": "开场时出示，建立事实基础",
            "synergy_with": ["payment_proof", "correspondence"],
            "effect_modifier": "配合其他证据使用效果更佳"
        },
        "payment_proof": {
            "name": "付款凭证",
            "optimal_phases": ["fact_presentation", "evidence_exchange"],
            "avoid_phases": ["argumentation"],
            "best_moment": "证明付款事实时出示",
            "synergy_with": ["contract", "invoice"],
            "effect_modifier": "与其他书证配合形成完整付款链条"
        },
        "correspondence": {
            "name": "往来函件",
            "optimal_phases": ["fact_presentation", "cross_examination"],
            "avoid_phases": [],
            "best_moment": "证明双方沟通过程时出示",
            "synergy_with": ["contract"],
            "effect_modifier": "可揭示对方的真实意思表示"
        },
        "chat_record": {
            "name": "聊天记录",
            "optimal_phases": ["fact_presentation", "cross_examination"],
            "avoid_phases": [],
            "best_moment": "证明事实或意图时出示",
            "synergy_with": ["correspondence"],
            "effect_modifier": "需确认真实性和完整性"
        },
        "witness_testimony": {
            "name": "证人证言",
            "optimal_phases": ["evidence_presentation", "cross_examination"],
            "avoid_phases": ["argumentation"],
            "best_moment": "事实陈述完毕后出示",
            "synergy_with": ["documentary"],
            "effect_modifier": "证人与书面证据相互印证"
        },
        "expert_opinion": {
            "name": "鉴定意见",
            "optimal_phases": ["evidence_presentation", "closing_argument"],
            "avoid_phases": [],
            "best_moment": "涉及专业问题时出示",
            "synergy_with": [],
            "effect_modifier": "具有较高证明力"
        },
        "audio_video": {
            "name": "视听资料",
            "optimal_phases": ["evidence_presentation", "fact_presentation"],
            "avoid_phases": [],
            "best_moment": "需要证明现场情况时出示",
            "synergy_with": [],
            "effect_modifier": "需确保证据来源合法"
        },
        "invoice": {
            "name": "发票收据",
            "optimal_phases": ["fact_presentation", "evidence_exchange"],
            "avoid_phases": [],
            "best_moment": "证明交易关系时出示",
            "synergy_with": ["contract", "payment_proof"],
            "effect_modifier": "可证明实际交易发生"
        },
        "identity_proof": {
            "name": "身份证明",
            "optimal_phases": ["opening", "identification"],
            "avoid_phases": [],
            "best_moment": "开篇时确认身份",
            "synergy_with": [],
            "effect_modifier": "证明当事人身份资格"
        }
    }
    
    # 庭审阶段定义
    HEARING_PHASES = {
        "court_opening": {
            "name": "开庭",
            "description": "法官宣布开庭，核实当事人身份",
            "evidence_type": "identity_proof",
            "appropriate_evidence": ["身份证明", "授权委托书"]
        },
        "case_facts": {
            "name": "事实调查",
            "description": "各方陈述案件事实",
            "evidence_type": "factual",
            "appropriate_evidence": ["合同", "付款凭证", "往来函件", "聊天记录", "发票"]
        },
        "evidence_exchange": {
            "name": "举证质证",
            "description": "各方出示证据并质证",
            "evidence_type": "all",
            "appropriate_evidence": ["所有类型"]
        },
        "cross_examination": {
            "name": "交叉询问",
            "description": "对证人或鉴定人进行询问",
            "evidence_type": "corroborative",
            "appropriate_evidence": ["证人证言", "鉴定意见", "书证"]
        },
        "debate": {
            "name": "法庭辩论",
            "description": "各方进行辩论",
            "evidence_type": "key",
            "appropriate_evidence": ["关键证据", "反驳证据"]
        },
        "mediation": {
            "name": "调解阶段",
            "description": "法官主持调解",
            "evidence_type": "negotiation",
            "appropriate_evidence": ["有利证据（保留）"]
        },
        "closing": {
            "name": "最后陈述",
            "description": "各方进行最后陈述",
            "evidence_type": "summary",
            "appropriate_evidence": ["总结性证据（可选）"]
        }
    }
    
    def __init__(self):
        self.timing_rules = self.EVIDENCE_TIMING_RULES
        self.phases = self.HEARING_PHASES
    
    def analyze_evidence_timing(self,
                               evidence_name: str,
                               evidence_type: str,
                               current_phase: str,
                               case_info: Dict,
                               context: str = "") -> Dict:
        """
        分析证据的最佳使用时机
        
        Args:
            evidence_name: 证据名称
            evidence_type: 证据类型
            current_phase: 当前庭审阶段
            case_info: 案件信息
            context: 当前对话上下文
            
        Returns:
            分析结果，包含建议时机、理由、示例话术等
        """
        result = {
            "evidence_name": evidence_name,
            "evidence_type": evidence_type,
            "current_phase": current_phase,
            "recommendation": "",
            "timing_score": 0,
            "reasons": [],
            "script": "",
            "warnings": [],
            "alternatives": []
        }
        
        # 获取该证据类型的时机规则
        rule = self.timing_rules.get(evidence_type, {
            "name": "一般证据",
            "optimal_phases": ["evidence_exchange"],
            "avoid_phases": [],
            "best_moment": "举证质证阶段出示",
            "synergy_with": []
        })
        
        # 评估当前时机
        current_phase_obj = self.HEARING_PHASES.get(current_phase, {})
        
        # 计算时机评分 (0-100)
        score = 50  # 基础分
        
        if current_phase in rule.get("optimal_phases", []):
            score += 30
            result["reasons"].append(f"当前阶段【{current_phase_obj.get('name', current_phase)}】适合出示{rule['name']}")
        elif current_phase in rule.get("avoid_phases", []):
            score -= 40
            result["reasons"].append(f"⚠️ 当前阶段不适合出示此类证据")
            result["warnings"].append(f"在【{current_phase}】阶段出示可能效果不佳")
        
        # 上下文分析
        if context:
            if "否认" in context or "不承认" in context:
                score += 10
                result["reasons"].append("对方否认相关事实，此时出示证据更有说服力")
            elif "主张" in context or "认为" in context:
                score += 5
                result["reasons"].append("对方提出了主张，需要用证据回应")
        
        # 生成建议
        score = max(0, min(100, score))
        result["timing_score"] = score
        
        if score >= 80:
            result["recommendation"] = "best"
            result["script"] = self._generate_best_timing_script(evidence_name, evidence_type)
        elif score >= 60:
            result["recommendation"] = "good"
            result["script"] = self._generate_good_timing_script(evidence_name, evidence_type)
        elif score >= 40:
            result["recommendation"] = "acceptable"
            result["script"] = self._generate_acceptable_timing_script(evidence_name, evidence_type)
        else:
            result["recommendation"] = "not_recommended"
            result["alternatives"] = self._suggest_alternatives(current_phase, evidence_type)
            result["script"] = self._generate_wait_script(evidence_name)
        
        # 添加时机理由
        result["best_moment"] = rule.get("best_moment", "根据庭审进展选择合适时机")
        result["synergy_suggestions"] = self._generate_synergy_suggestions(evidence_type)
        
        return result
    
    def _generate_best_timing_script(self, evidence_name: str, evidence_type: str) -> str:
        """生成最佳时机的出示话术"""
        return f"""现在出示该证据的推荐话术：

"审判长，我方现在出示{evidence_name}作为证据，请求法庭记录在案。"

（如需详细说明）
"这份证据可以证明{self.timing_rules.get(evidence_type, {}).get('name', '相关事实')}，请法庭予以采纳。"

（如需要求对方质证）
"我方要求对方代理人对该证据进行质证。" """
    
    def _generate_good_timing_script(self, evidence_name: str, evidence_type: str) -> str:
        """生成良好时机的出示话术"""
        return f"""现在出示该证据也是合适的，推荐话术：

"审判长，我方补充提交{evidence_name}，该证据与本案争议焦点相关，证明目的为..."

（如结合之前证据）
"结合我方之前提交的...证据，可以形成完整的证据链条，证明..." """
    
    def _generate_acceptable_timing_script(self, evidence_name: str, evidence_type: str) -> str:
        """生成可接受时机的出示话术"""
        return f"""如果现在必须出示，推荐使用：

"关于{evidence_name}，我方在之前已提交过相应证据，如法庭需要，我方可以再次说明。"

（谨慎表态）
"该证据的具体内容和证明力，我方将在质证环节详细说明。" """
    
    def _generate_wait_script(self, evidence_name: str) -> str:
        """生成等待更好时机的建议"""
        return f"""建议暂不出示{evidence_name}，原因：
1. 当前阶段出示可能无法充分发挥证据效力
2. 可保留到更关键的阶段使用
3. 如果对方先提出相关主张，再出示反击效果更好

等待时机：
- 对方否认相关事实时
- 进入辩论阶段需要反驳时
- 法官主动询问时 """
    
    def _suggest_alternatives(self, current_phase: str, evidence_type: str) -> List[str]:
        """建议替代时机"""
        alternatives = []
        
        for phase_id, phase_info in self.HEARING_PHASES.items():
            if phase_id in self.timing_rules.get(evidence_type, {}).get("optimal_phases", []):
                alternatives.append(f"【{phase_info['name']}】阶段：{phase_info['description']}")
        
        if not alternatives:
            alternatives = ["举证质证阶段", "法庭辩论阶段（反驳用）", "最后陈述阶段（总结用）"]
        
        return alternatives
    
    def _generate_synergy_suggestions(self, evidence_type: str) -> List[Dict]:
        """生成证据协同建议"""
        rule = self.timing_rules.get(evidence_type, {})
        synergy_types = rule.get("synergy_with", [])
        
        suggestions = []
        for syn_type in synergy_types:
            syn_rule = self.timing_rules.get(syn_type, {})
            suggestions.append({
                "evidence_type": syn_type,
                "evidence_name": syn_rule.get("name", syn_type),
                "suggestion": syn_rule.get("effect_modifier", "")
            })
        
        return suggestions
    
    def generate_evidence_sequence(self,
                                   evidence_list: List[Dict],
                                   hearing_type: str = "first_trial") -> Dict:
        """
        生成证据出示顺序建议
        
        Args:
            evidence_list: 证据列表 [{"name": "...", "type": "...", "importance": ...}]
            hearing_type: 庭审类型
            
        Returns:
            证据出示顺序及理由
        """
        # 按重要性排序
        sorted_evidence = sorted(evidence_list, 
                                key=lambda x: x.get("importance", 5), 
                                reverse=True)
        
        # 生成顺序
        sequence = []
        for i, evidence in enumerate(sorted_evidence, 1):
            rule = self.timing_rules.get(evidence.get("type", ""), {})
            phase = rule.get("optimal_phases", ["evidence_exchange"])[0]
            phase_info = self.HEARING_PHASES.get(phase, {"name": "举证阶段"})
            
            sequence.append({
                "order": i,
                "evidence_name": evidence.get("name"),
                "evidence_type": evidence.get("type"),
                "suggested_phase": phase,
                "phase_name": phase_info.get("name"),
                "purpose": evidence.get("purpose", ""),
                "script": self._generate_presentation_script(evidence)
            })
        
        return {
            "total_count": len(sequence),
            "sequence": sequence,
            "summary": f"建议按上述顺序出示{len(sequence)}份证据，关键证据优先出示"
        }
    
    def _generate_presentation_script(self, evidence: Dict) -> str:
        """生成证据出示话术"""
        name = evidence.get("name", "证据")
        purpose = evidence.get("purpose", "相关事实")
        
        return f"""出示话术：
"我方出示{name}，证明{purpose}。"
        
（如需要详细说明）
"该证据的形式为{evidence.get('type', '书证')}，来源为{evidence.get('source', '我方保存')}，能够证明..." """
    
    def predict_opposing_evidence_strategy(self, 
                                         case_info: Dict,
                                         my_evidence_list: List[str]) -> Dict:
        """
        预测对方可能出示的证据及应对策略
        
        Args:
            case_info: 案件信息
            my_evidence_list: 我方已准备的证据
            
        Returns:
            预测结果和应对策略
        """
        prompt = f"""作为一位经验丰富的诉讼律师，分析对方可能的证据策略。

【案件信息】
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}
原告：{case_info.get('plaintiff', '未知')}
被告：{case_info.get('defendant', '未知')}
案件描述：{case_info.get('description', '未知')}

【我方已准备的证据】
{chr(10).join(['- ' + e for e in my_evidence_list]) if my_evidence_list else '暂无'}

请分析：
1. 对方可能出示哪些证据？（基于案件类型和争议焦点）
2. 对方证据可能的弱点在哪里？
3. 如何应对对方的证据策略？
4. 我方证据应如何配合以反驳对方？

请用JSON格式返回，包含：opposing_evidence（对方可能证据列表）, weaknesses（弱点分析）, counter_strategies（应对策略）"""

        try:
            response = llm_service.chat([
                {"role": "system", "content": "你是一位经验丰富的诉讼律师，擅长分析证据策略。"},
                {"role": "user", "content": prompt}
            ])
            
            return {"success": True, "analysis": response}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_evidence_effectiveness(self,
                                     evidence_name: str,
                                     context: str,
                                     speaker_role: str,
                                     judge_attitude: str = "neutral") -> Dict:
        """
        分析证据在当前情境下的效果
        
        Args:
            evidence_name: 证据名称
            context: 当前情境
            speaker_role: 讲话方角色
            judge_attitude: 法官态度
            
        Returns:
            效果分析和建议
        """
        effect_score = 70  # 基础分
        
        # 讲话方角色调整
        if speaker_role == "judge":
            effect_score += 10  # 法官询问时出示效果好
        elif speaker_role == "opponent":
            effect_score += 15  # 反驳对方时出示效果最好
        elif speaker_role == "my_side":
            effect_score += 5  # 我方主动出示
            
        # 法官态度调整
        if judge_attitude == "favorable":
            effect_score += 10
        elif judge_attitude == "hostile":
            effect_score -= 15
        
        # 情境分析
        if any(word in context for word in ["否认", "不承认", "不存在"]):
            effect_score += 10
        elif any(word in context for word in ["认可", "承认", "同意"]):
            effect_score -= 5
        
        effect_score = max(0, min(100, effect_score))
        
        result = {
            "evidence_name": evidence_name,
            "effect_score": effect_score,
            "evaluation": self._get_effect_evaluation(effect_score),
            "advice": self._get_effect_advice(effect_score, speaker_role)
        }
        
        return result
    
    def _get_effect_evaluation(self, score: int) -> str:
        """根据分数获取效果评价"""
        if score >= 90:
            return "极佳时机 - 此时出示效果最佳"
        elif score >= 75:
            return "良好时机 - 此时出示效果较好"
        elif score >= 60:
            return "一般时机 - 可以出示"
        elif score >= 45:
            return "欠佳时机 - 效果可能受限"
        else:
            return "不佳时机 - 建议等待更好机会"
    
    def _get_effect_advice(self, score: int, speaker_role: str) -> str:
        """根据分数获取建议"""
        if speaker_role == "judge":
            if score >= 75:
                return "法官主动询问相关问题，此时出示证据非常合适，可详细说明证据内容和证明目的。"
            else:
                return "法官未主动询问相关内容，建议先表明有相关证据，等待合适时机出示。"
        elif speaker_role == "opponent":
            if score >= 75:
                return "对方否认或质疑相关事实，此时出示证据反击效果最佳，可有力驳斥对方观点。"
            else:
                return "对方暂未涉及该证据内容，可考虑主动出示或等待对方提及后反驳。"
        else:
            return "建议结合庭审进展，在关键节点出示该证据。"


# 全局实例
evidence_timing_analyzer = EvidenceTimingAnalyzer()
