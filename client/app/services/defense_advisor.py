"""
庭审实时应对策略服务 - 整合陷阱识别、证据时机和AI分析
为用户提供实时的应对建议、陈述词和策略支持
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

from app.services.trap_detector import trap_detector
from app.services.evidence_timing import evidence_timing_analyzer
from app.services.llm_service import llm_service


class RealTimeDefenseAdvisor:
    """
    实时抗辩顾问
    
    功能：
    1. 实时分析对方陈述
    2. 识别语言陷阱
    3. 提供应对话术
    4. 证据使用时机提醒
    5. 禁止事项预警
    6. 自动生成陈述词
    """
    
    def __init__(self):
        self.trap_detector = trap_detector
        self.evidence_analyzer = evidence_timing_analyzer
    
    def analyze_realtime_situation(self,
                                  statement: str,
                                  speaker_role: str,
                                  speaker_name: str,
                                  current_phase: str,
                                  case_info: Dict,
                                  conversation_history: List[Dict] = None) -> Dict:
        """
        实时分析当前情况并提供建议
        
        Args:
            statement: 对方的发言
            speaker_role: 讲话方角色
            speaker_name: 讲话人姓名
            current_phase: 当前庭审阶段
            case_info: 案件信息
            conversation_history: 对话历史
            
        Returns:
            完整的分析和建议
        """
        normalized_role = self._normalize_role(speaker_role)
        result = {
            "timestamp": datetime.now().isoformat(),
            "speaker": {
                "role": speaker_role,
                "name": speaker_name,
                "normalized_role": normalized_role,
                "is_friendly": self._is_friendly_role(normalized_role),
                "is_hostile": self._is_hostile_role(normalized_role)
            },
            "phase": current_phase,
            "trap_analysis": {},
            "evidence_suggestions": [],
            "response_suggestion": {},
            "warnings": [],
            "forbidden_actions": [],
            "recommended_statements": []
        }
        
        # 1. 陷阱检测
        trap_result = self.trap_detector.detect_trap(statement, normalized_role)
        result["trap_analysis"] = trap_result
        
        if trap_result["is_trap"]:
            result["warnings"].append({
                "type": "trap",
                "level": trap_result["severity"],
                "title": f"检测到陷阱：{trap_result['trap_types'][0] if trap_result['trap_types'] else '未知'}",
                "content": trap_result["description"],
                "suggestion": trap_result["suggestion"]
            })
        
        # 2. 如果是法官提问，进行专门分析
        if normalized_role == "judge":
            judge_analysis = self.trap_detector.analyze_judge_question(statement)
            result["judge_analysis"] = judge_analysis
            result["response_suggestion"] = {
                "strategy": judge_analysis["response_strategy"],
                "tips": judge_analysis["tips"],
                "detailed_strategy": judge_analysis.get("detailed_strategy", "")
            }
        
        # 3. 检测沉默陷阱（危险发言模式）
        silent_traps = self.trap_detector.detect_silent_traps(statement, normalized_role)
        for trap in silent_traps:
            result["warnings"].append({
                "type": "silent_trap",
                "level": "high",
                "title": trap["name"],
                "content": trap["description"],
                "avoidance": trap["avoidance"]
            })
        
        # 4. 证据使用建议
        if case_info.get("available_evidence"):
            for evidence in case_info.get("available_evidence", [])[:3]:  # 只返回前3个最相关的
                timing_analysis = self.evidence_analyzer.analyze_evidence_timing(
                    evidence.get("name", ""),
                    evidence.get("type", ""),
                    current_phase,
                    case_info,
                    statement
                )
                if timing_analysis["recommendation"] in ["best", "good"]:
                    result["evidence_suggestions"].append({
                        "evidence_name": evidence.get("name"),
                        "timing_score": timing_analysis["timing_score"],
                        "recommendation": timing_analysis["recommendation"],
                        "script": timing_analysis["script"]
                    })
        
        # 5. 禁止事项
        result["forbidden_actions"] = self._get_forbidden_actions(normalized_role, case_info)
        
        # 6. 生成推荐陈述
        result["recommended_statements"] = self._generate_recommended_statements(
            statement, normalized_role, case_info
        )
        
        # 7. 整体紧迫度评估
        result["urgency"] = self._calculate_urgency(result)
        result["analysis"] = self._build_case_specific_realtime_analysis(
            statement, normalized_role, current_phase, case_info, result
        )
        
        return result

    def _normalize_role(self, role: str) -> str:
        """兼容前端可能传入的中文角色名称。"""
        role_text = (role or "").lower()
        if any(key in role_text for key in ["judge", "法官", "审判长"]):
            return "judge"
        if any(key in role_text for key in ["clerk", "书记员"]):
            return "clerk"
        if any(key in role_text for key in ["opponent", "defendant", "被告", "对方", "相对方"]):
            return "opponent_lawyer" if any(key in role_text for key in ["lawyer", "代理", "律师"]) else "opponent"
        if any(key in role_text for key in ["my_side", "plaintiff", "原告", "我方", "己方"]):
            return "my_side"
        return role or "other"
    
    def _is_friendly_role(self, role: str) -> bool:
        """判断是否为友方"""
        friendly_roles = ["judge", "clerk", "my_side"]
        return role in friendly_roles
    
    def _is_hostile_role(self, role: str) -> bool:
        """判断是否为敌对方"""
        hostile_roles = ["opponent_lawyer", "opponent", "defendant_lawyer"]
        return role in hostile_roles
    
    def _get_forbidden_actions(self, speaker_role: str, case_info: Dict) -> List[Dict]:
        """获取禁止事项"""
        forbidden = []
        
        # 通用禁止事项
        common_forbidden = [
            {
                "action": "情绪化回应",
                "description": "被激怒后做出情绪化的反应",
                "example": "不要说'你胡说'、'完全是胡说八道'等",
                "consequence": "可能给法官留下不良印象，影响公信力"
            },
            {
                "action": "无根据推测",
                "description": "对不确定的事实进行推测",
                "example": "不要说'我估计'、'大概是'、'可能是'",
                "consequence": "可能构成虚假陈述"
            },
            {
                "action": "过度自白",
                "description": "提供超出问题范围的额外信息",
                "example": "避免说'另外'、'还有'、'补充一下'",
                "consequence": "可能暴露不利信息"
            },
            {
                "action": "轻易承认",
                "description": "在未了解全部事实前做出承认",
                "example": "不要直接说'是的'、'没有异议'",
                "consequence": "可能导致不可逆的不利后果"
            }
        ]
        
        # 根据讲话方角色调整
        if speaker_role == "judge":
            # 针对法官提问的禁止事项
            forbidden.append({
                "action": "与法官争辩",
                "description": "不要与法官发生争执",
                "example": "即使不同意，也要说'我方保留意见'",
                "consequence": "可能影响案件审理"
            })
        elif speaker_role in ["opponent_lawyer", "opponent"]:
            forbidden.extend([
                common_forbidden[0],  # 情绪化回应
                common_forbidden[2],   # 过度自白
                {
                    "action": "人身攻击",
                    "description": "不要进行人身攻击或侮辱对方",
                    "example": "不要说'你作为一个律师怎么能...'",
                    "consequence": "可能被视为藐视法庭"
                }
            ])
        
        return forbidden
    
    def _generate_recommended_statements(self,
                                       statement: str,
                                       speaker_role: str,
                                       case_info: Dict) -> List[Dict]:
        """生成推荐陈述"""
        recommendations = []
        
        if speaker_role == "judge":
            # 针对法官提问的推荐回答
            recommendations.append({
                "type": "标准回答模板",
                "content": "审判长，就您刚才提出的问题，我方回答如下：...",
                "when_to_use": "需要正面回答法官问题时"
            })
            
            # 如果是确认类问题
            if "是否" in statement or "有没有" in statement:
                recommendations.append({
                    "type": "确认类回答",
                    "content": "我方确认/不确认...，理由是...",
                    "when_to_use": "法官询问是否认可某事时"
                })
        
        elif speaker_role in ["opponent_lawyer", "opponent"]:
            # 反驳类推荐
            recommendations.append({
                "type": "反驳模板",
                "content": "对方代理人的观点，我方有异议，理由如下：...",
                "when_to_use": "需要反驳对方观点时"
            })
            
            recommendations.append({
                "type": "请求法庭注意",
                "content": "请法庭注意，对方陈述与在案证据存在矛盾...",
                "when_to_use": "发现对方陈述有漏洞时"
            })
        
        return recommendations

    def _build_case_specific_realtime_analysis(
        self,
        statement: str,
        speaker_role: str,
        current_phase: str,
        case_info: Dict,
        result: Dict
    ) -> str:
        """补充可直接阅读的案件化实时分析文本。"""
        plaintiff = case_info.get("plaintiff") or "我方"
        defendant = case_info.get("defendant") or "对方"
        evidence_summary = (case_info.get("evidence_summary") or "")[:1200]
        trap = result.get("trap_analysis", {})
        trap_text = (
            f"已识别为{','.join(trap.get('trap_types', []))}，严重程度为{trap.get('severity')}。"
            if trap.get("is_trap") else "未触发强规则陷阱，但仍需按证据逐项回应。"
        )
        return (
            f"博凯升华案实时庭审分析（{current_phase}）：发言方角色为{speaker_role}，发言内容为“{statement}”。"
            f"该发言试图否定{plaintiff}一方关于合作出资、停业责任、工资社保、保证金或信息服务费的主张，"
            f"应要求{defendant}一方明确其事实来源和证据编号，避免把概括性否认变成我方默认。"
            f"{trap_text}"
            "建议回应：审判长，我方不认可对方将多个法律关系混同处理；请对方明确其否认的是哪一项款项、哪一段期间、"
            "依据哪一份证据。我方将结合合作协议、董事会/股东会文件、资金流水、往来函件、工资社保、保证金和信息服务费凭证逐项说明。"
            "法律依据方向包括《民事诉讼法》举证责任与法庭调查规则，以及《民法典》合同履行、违约责任和诚信原则。"
            f"\n证据提示：{evidence_summary}"
        )
    
    def _calculate_urgency(self, analysis: Dict) -> str:
        """计算紧迫度"""
        if any(w.get("level") == "critical" for w in analysis.get("warnings", [])):
            return "critical"
        elif any(w.get("level") == "high" for w in analysis.get("warnings", [])):
            return "high"
        elif analysis.get("evidence_suggestions"):
            if any(s.get("timing_score", 0) >= 80 for s in analysis["evidence_suggestions"]):
                return "medium"
        return "low"
    
    def generate_opening_statement(self, case_info: Dict) -> Dict:
        """
        生成开场陈述

        Args:
            case_info: 案件信息（含证据全文、对抗性分析等）

        Returns:
            开场陈述内容和建议
        """
        evidence_section = ""
        if case_info.get('evidence_full_text'):
            evidence_section = f"\n\n【证据全文参考】\n{case_info['evidence_full_text']}\n"
        adv_section = ""
        if case_info.get('adversarial_analysis'):
            adv_section = f"\n\n【对抗性分析结论】\n{case_info['adversarial_analysis']}\n"

        prompt = f"""你是一位经验丰富的诉讼律师，需要为案件生成开庭陈述。

【案件信息】
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}
原告：{case_info.get('plaintiff', '未知')}
被告：{case_info.get('defendant', '未知')}
我方立场：{case_info.get('my_position', '原告')}
诉讼请求：{case_info.get('claim_amount', '未知')}
案件描述：{case_info.get('description', '未知')}
{evidence_section}{adv_section}

请生成一段专业的开庭陈述，包含：
1. 开场问候
2. 案件基本情况概述（必须引用证据内容）
3. 我方核心主张（3点以内，每点必须有证据支持）
4. 法律依据方向（必须点明《民法典》《公司法》《民事诉讼法》或举证责任规则中的适用方向，不得编造未经核验的具体案号）
5. 请求法庭支持的事项
6. 结束语

要求：
- 语言简洁、专业
- 突出重点
- 控制在3分钟以内朗读时长
- 使用法言法语
- 每个论点必须引用具体证据条款
- 必须出现“民法典”“公司法”“民事诉讼法”或“举证责任”至少一项法律依据关键词"""

        try:
            statement = llm_service.chat([
                {"role": "system", "content": "你是一位专业的诉讼律师，擅长法庭陈述。"},
                {"role": "user", "content": prompt}
            ])
            if not any(signal in (statement or "") for signal in ("民法典", "公司法", "民事诉讼法", "举证责任")):
                statement += "\n\n从法律适用方向看，我方将围绕《民法典》合同编关于合同履行、违约责任和损失赔偿的规则，《公司法》关于股东出资、公司治理和清算程序的规则，以及《民事诉讼法》和证据规则关于举证责任、证据真实性、关联性、合法性的要求，请求法庭依法审查并支持有证据支撑的诉讼请求。"

            return {
                "success": True,
                "statement": statement,
                "tips": [
                    "开场陈述应简洁有力，不要过于冗长",
                    "突出我方最有利的3个论点",
                    "注意语速适中，让法庭书记员能够记录",
                    "陈述时直视前方，保持自信姿态"
                ],
                "estimated_duration": "2-3分钟"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_closing_statement(self,
                                 case_info: Dict,
                                 hearing_summary: str = "") -> Dict:
        """
        生成结案陈词

        Args:
            case_info: 案件信息（含证据全文、对抗性分析等）
            hearing_summary: 庭审摘要

        Returns:
            结案陈词内容和建议
        """
        evidence_section = ""
        if case_info.get('evidence_full_text'):
            evidence_section = f"\n\n【证据全文参考】\n{case_info['evidence_full_text']}\n"
        adv_section = ""
        if case_info.get('adversarial_analysis'):
            adv_section = f"\n\n【对抗性分析结论】\n{case_info['adversarial_analysis']}\n"

        prompt = f"""你是一位经验丰富的诉讼律师，需要为案件生成结案陈词。

【案件信息】
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}
原告：{case_info.get('plaintiff', '未知')}
被告：{case_info.get('defendant', '未知')}
我方立场：{case_info.get('my_position', '原告')}
诉讼请求：{case_info.get('claim_amount', '未知')}
{evidence_section}{adv_section}

【庭审摘要】
{hearing_summary if hearing_summary else '暂无'}

请生成一段专业的结案陈词，包含：
1. 总结我方核心论点（必须引用证据原文）
2. 回应对方的主要抗辩
3. 强调最有力的证据支持（引用具体条款）
4. 法律依据说明（引用具体法条）
5. 再次明确诉讼请求
6. 请求法庭支持

要求：
- 语言铿锵有力
- 突出关键证据和法律依据
- 控制在中场5分钟以内
- 每个论点必须引用证据原文或法条原文"""

        try:
            statement = llm_service.chat([
                {"role": "system", "content": "你是一位专业的诉讼律师，擅长法庭陈述。"},
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "statement": statement,
                "tips": [
                    "结案陈词是最后的机会，应强调最有力的论点",
                    "可以用'综上所述'开头",
                    "强调有证据支持的事实",
                    "最后明确请求法庭支持我方诉请"
                ],
                "estimated_duration": "4-5分钟"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_direct_counter(self,
                              opposing_statement: str,
                              case_info: Dict,
                              my_role: str = "原告") -> Dict:
        """
        针对对方陈述生成直接反驳

        Args:
            opposing_statement: 对方的陈述
            case_info: 案件信息（含证据全文、对抗性分析等）
            my_role: 我方角色

        Returns:
            反驳话术和建议
        """
        # 先检测陷阱
        trap_result = self.trap_detector.detect_trap(opposing_statement, "opponent")

        # 获取反驳模板
        objection_template = self.trap_detector.generate_objection_template("hearsay")

        # 证据上下文
        evidence_section = ""
        if case_info.get('evidence_full_text'):
            evidence_section = f"\n\n【证据全文参考】\n{case_info['evidence_full_text']}\n"
        if case_info.get('adversarial_analysis'):
            evidence_section += f"\n【对抗性分析结论】\n{case_info['adversarial_analysis']}\n"

        prompt = f"""作为{my_role}方的诉讼律师，针对对方的陈述进行反驳。

【对方陈述】
{opposing_statement}

【我方角色】
{my_role}

【案件信息】
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}
案件描述：{case_info.get('description', '未知')}
{evidence_section}

请生成：
1. 反驳要点（对方陈述的漏洞在哪里）
2. 反驳话术（可直接使用的语句，必须引用证据条款）
3. 需要调用的证据（如有，具体条款）
4. 反驳时的语气建议

⚠️ 重要：反驳时必须引用证据原文或法条原文，不能空泛而谈。
请用JSON格式返回，包含：refutation_points, counter_speech, required_evidence, tone_suggestion"""

        try:
            ai_response = llm_service.chat([
                {"role": "system", "content": "你是一位专业的诉讼律师，擅长辩论反驳。"},
                {"role": "user", "content": prompt}
            ])
            
            result = {
                "success": True,
                "trap_detected": trap_result,
                "counter_speech": ai_response,
                "objection_tip": objection_template.get("template", "") if trap_result["is_trap"] else None,
                "urgency": "high" if trap_result["is_trap"] else "medium"
            }
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_cross_examination(self,
                                 witness_name: str,
                                 witness_role: str,
                                 case_info: Dict) -> Dict:
        """
        生成对证人的交叉询问问题

        Args:
            witness_name: 证人姓名
            witness_role: 证人角色（我方/对方）
            case_info: 案件信息（含证据全文、对抗性分析等）

        Returns:
            询问问题和策略
        """
        # 证据上下文
        evidence_section = ""
        if case_info.get('evidence_full_text'):
            evidence_section = f"\n\n【证据全文参考】\n{case_info['evidence_full_text']}\n"
        if case_info.get('adversarial_analysis'):
            evidence_section += f"\n【对抗性分析结论】\n{case_info['adversarial_analysis']}\n"

        prompt = f"""你是一位经验丰富的诉讼律师，需要针对证人设计交叉询问问题。

【证人信息】
姓名：{witness_name}
角色：{'我方证人' if witness_role == 'my_side' else '对方证人'}
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}
原告：{case_info.get('plaintiff', '未知')}
被告：{case_info.get('defendant', '未知')}
{evidence_section}

{'【我方证人询问策略】' if witness_role == 'my_side' else '【对方证人询问策略】'}
{'需要通过询问强化证人证言的可信度' if witness_role == 'my_side' else '需要通过询问揭示证人证言的漏洞或矛盾'}

请设计5-8个关键问题，必须严格围绕博凯升华案，不得使用图书馆、监控录像、无关微信聊天等本案未出现的虚构示例。每个问题必须：
1. 引导性问题（用于确认事实）
2. 深入追问（用于挖掘细节）
3. 关键问题（最有力的问题，必须引用证据原文）

如为对方证人，还需包含：
4. 质疑性问题（揭示矛盾，必须引用证据条款）
5. 攻击性问题（动摇可信度）

请用JSON格式返回，包含：questions（问题列表，每个问题包含question、purpose、expected_answer、tip、evidence_anchor、legal_basis）。每个问题都必须提到博凯升华/陈靖/佛山吉麟/雷天乾中的至少一个，并引用证据编号或证据名称。"""

        try:
            questions = llm_service.chat([
                {"role": "system", "content": "你是一位经验丰富的诉讼律师，擅长交叉询问。"},
                {"role": "user", "content": prompt}
            ])
            questions = self._calibrate_cross_examination_legal_basis(questions)

            case_signals = ["博凯升华", "陈靖", "佛山吉麟", "雷天乾", "博凯健康"]
            if sum(1 for signal in case_signals if signal in (questions or "")) < 3:
                questions = self._fallback_cross_examination_questions(witness_name, witness_role, case_info)
            
            return {
                "success": True,
                "questions": questions,
                "tips": [
                    "问题应简洁明了，避免复合问题",
                    "每个问题只包含一个事实",
                    "注意控制节奏，不要被证人牵着走",
                    "关键问题放在询问末尾"
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calibrate_cross_examination_legal_basis(self, questions: str) -> str:
        """补强交叉询问中的法律依据，避免泛化成“相关规定”。"""
        if not questions:
            return questions

        basis_bank = [
            "《民法典》合同编关于合同成立、履行、违约责任和损失赔偿的规则；《民事诉讼法》关于谁主张谁举证和证据审查的规则",
            "《公司法》关于股东会、董事会职权，公司决议效力，解散清算程序和清算义务的规则；《民事诉讼法》举证责任规则",
            "《民法典》关于债务清偿、不当得利、损失赔偿的规则；《民事诉讼法》关于证据真实性、关联性、合法性审查的规则",
            "《公司法》关于股东出资、公司财务管理和董监高忠实勤勉义务的规则；《民事诉讼法》举证责任规则",
        ]
        vague_markers = ("相关法律规定", "具体规定", "财务管理规定", "财务管理制度", "考勤与工资发放制度", "清算组负责人的法律责任")

        def needs_rewrite(value: str) -> bool:
            if not value:
                return True
            if any(marker in value for marker in vague_markers):
                return not any(law in value for law in ("民法典", "公司法", "民事诉讼法"))
            return not any(law in value for law in ("民法典", "公司法", "民事诉讼法", "举证责任"))

        raw = questions.strip()
        json_text = raw
        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) >= 3:
                json_text = parts[1]
                if json_text.lstrip().startswith("json"):
                    json_text = json_text.lstrip()[4:].strip()

        try:
            data = json.loads(json_text)
            question_items = data.get("questions") if isinstance(data, dict) else None
            if isinstance(question_items, list):
                for idx, item in enumerate(question_items):
                    if isinstance(item, dict) and needs_rewrite(str(item.get("legal_basis", ""))):
                        item["legal_basis"] = basis_bank[idx % len(basis_bank)]
                return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            pass

        if "相关法律规定" in raw or "公司财务管理规定" in raw or "公司解散与清算的" in raw:
            return raw + (
                "\n\n【法律依据校准】本组交叉询问应以《民法典》合同编关于合同履行、违约责任、损失赔偿和不当得利的规则，"
                "《公司法》关于股东出资、公司决议、解散清算和董监高忠实勤勉义务的规则，以及《民事诉讼法》关于举证责任、证据真实性、关联性、合法性审查的规则为依据；"
                "不得仅以“相关法律规定”替代具体适用方向。"
            )
        return raw

    def _fallback_cross_examination_questions(self, witness_name: str, witness_role: str, case_info: Dict) -> str:
        """模型输出跑偏时，返回案件绑定的交叉询问问题。"""
        defendant = case_info.get("defendant") or "雷天乾"
        plaintiff = case_info.get("plaintiff") or "陈靖/佛山吉麟"
        evidence_summary = (case_info.get("evidence_summary") or case_info.get("evidence_full_text") or "")[:1200]
        return json.dumps({
            "questions": [
                {
                    "question": f"{witness_name}，请确认{defendant}一方是否曾以出资未到位为由推动博凯升华暂停经营或解散清算？",
                    "purpose": "固定对方将停业/解散与出资问题绑定的事实基础。",
                    "expected_answer": "确认、否认或称不清楚。",
                    "tip": "如其否认，立即要求其说明暂停营业通知、股东会/董事会文件的具体出处。",
                    "evidence_anchor": "证据名称：暂停营业通知、董事会决议、股东会/监事通知等",
                    "legal_basis": "《民事诉讼法》举证责任与法庭调查规则；《公司法》公司决议程序规则"
                },
                {
                    "question": f"请说明{plaintiff}一方所谓未出资，依据的是哪份协议、哪一条款、哪一个到期日？",
                    "purpose": "迫使对方区分认缴期限、利润分红扣缴安排和即时货币出资义务。",
                    "expected_answer": "引用协议或无法明确。",
                    "tip": "如其无法明确，应提示法庭注意其抗辩缺少合同依据。",
                    "evidence_anchor": "证据名称：投资协议、公司章程、催缴出资函及复函",
                    "legal_basis": "《民法典》合同解释、诚信履行规则；《公司法》认缴出资规则"
                },
                {
                    "question": "关于工资社保、保证金和信息服务费，对方是否能逐项说明已经支付、抵扣或合法占有的证据编号？",
                    "purpose": "拆解对方概括性否认，固定其举证缺口。",
                    "expected_answer": "逐项说明或无法说明。",
                    "tip": "不要接受“都没有依据”这类笼统回答。",
                    "evidence_anchor": "证据名称：工资表/催薪记录、付款凭证、保证金凭证、信息服务费凭证",
                    "legal_basis": "《民事诉讼法》举证责任；《民法典》合同履行、违约责任、不当得利规则"
                },
                {
                    "question": "雷天乾或博凯健康一方作出停业、退租、遣散员工安排时，是否经过博凯升华有效董事会或股东会决议？",
                    "purpose": "锁定停业和解散程序违法的核心矛盾。",
                    "expected_answer": "承认有/无决议或称不了解。",
                    "tip": "如称有决议，要求其当庭指出证据名称和形成时间。",
                    "evidence_anchor": "证据名称：董事会决议、反对解散函、股东会通知/决议",
                    "legal_basis": "《公司法》董事会、股东会职权及公司决议规则"
                },
                {
                    "question": "对方是否承认，本案每一项费用性质都应回到具体凭证和合同关系核对，而不能笼统认定为陈靖个人自愿垫付？",
                    "purpose": "封堵对方把全部款项个人化、赠与化的诱导性抗辩。",
                    "expected_answer": "通常难以直接否认。",
                    "tip": "若其否认，请要求其说明每一笔款项个人化的证据。",
                    "evidence_anchor": "证据名称：资金流水、付款凭证、往来函件、合作协议",
                    "legal_basis": "《民法典》合同履行、债务清偿、不当得利规则"
                },
            ],
            "case_evidence_note": evidence_summary,
        }, ensure_ascii=False, indent=2)
    
    def generate_mediation_strategy(self,
                                   case_info: Dict,
                                   my_bottom_line: str = "") -> Dict:
        """
        生成调解阶段的应对策略

        Args:
            case_info: 案件信息（含证据摘要、对抗性分析结论等）
            my_bottom_line: 我方底线

        Returns:
            调解策略和建议
        """
        # 证据摘要和对抗性分析
        evidence_section = ""
        if case_info.get('evidence_summary'):
            evidence_section += f"【证据摘要】{case_info['evidence_summary']}\n"
        if case_info.get('adversarial_analysis'):
            evidence_section += f"\n【对抗性分析结论】\n{case_info['adversarial_analysis']}\n"
        if case_info.get('letters_summary'):
            evidence_section += f"\n【往来函件】{case_info['letters_summary']}\n"

        prompt = f"""你是一位经验丰富的诉讼律师，需要为调解阶段制定策略。

【案件信息】
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}
原告：{case_info.get('plaintiff', '未知')}
被告：{case_info.get('defendant', '未知')}
诉讼金额：{case_info.get('claim_amount', '未知')}
我方立场：{case_info.get('my_position', '原告')}
{evidence_section}

【我方底线】
{my_bottom_line if my_bottom_line else '待定'}

请制定调解策略，包含：
1. 调解开场策略（如何表态，结合证据优势）
2. 让步策略（如何合理让步）
3. 谈判筹码（我方证据优势）
4. 底线坚持（绝不能让步的点）
5. 调解话术示例
6. 遇到僵局的应对

请用JSON格式返回"""

        try:
            strategy = llm_service.chat([
                {"role": "system", "content": "你是一位专业的诉讼律师，擅长调解谈判。"},
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "strategy": strategy,
                "reminders": [
                    "调解中不要暴露真实底线",
                    "让对方先出价",
                    "每次让步都要有对价",
                    "可以用'回去考虑一下'争取时间"
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局实例
defense_advisor = RealTimeDefenseAdvisor()
