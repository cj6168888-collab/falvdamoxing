"""
语言陷阱识别服务 - 识别庭审中的逻辑陷阱和诡辩话术
帮助用户识别对方或法官设置的语言陷阱，避免落入圈套
"""

from typing import Dict, List, Optional, Tuple
import re
from app.services.llm_service import llm_service


class TrapDetector:
    """
    语言陷阱检测器
    
    功能：
    1. 识别各类逻辑陷阱
    2. 分析诱导性提问
    3. 检测偷换概念
    4. 识别举证责任转移
    5. 提供应对建议
    """
    
    # 陷阱模式定义
    TRAP_PATTERNS = {
        "leading_question": {
            "name": "诱导性提问",
            "description": "通过问题的措辞暗示期望的答案",
            "patterns": [
                r"你不是已经.*了吗",
                r"你难道不认为",
                r"你肯定.*对吧",
                r"按照.*的规定",
                r"既然.*那.*对吧",
                r"你不反对.*对吗",
                r"你已经.*了对不对",
                r"你应该.*吧",
                r"你.*不是.*吗",
                r"是否承认.*",
                r"你是否承认.*所以.*",
                r"既然没有.*所以.*",
            ],
            "indicators": [
                "预设前提",
                "暗示答案",
                "强制选择"
            ],
            "severity": "high",
            "response": "要求对方重新组织问题，或指出问题中包含预设前提"
        },
        "false_dilemma": {
            "name": "虚假两难",
            "description": "给出两个极端选项，忽略中间地带",
            "patterns": [
                r"要么.*要么.*",
                r"不是.*就是.*",
                r"只有.*才.*",
                r"要么.*要么.*别.*",
                r"不是.*就是.*没有.*",
            ],
            "indicators": [
                "极端选项",
                "忽略中间",
                "强制二选一"
            ],
            "severity": "medium",
            "response": "指出存在其他可能性，揭示虚假两难的本质"
        },
        "straw_man": {
            "name": "稻草人谬误",
            "description": "歪曲对方的观点，然后攻击这个歪曲后的观点",
            "patterns": [
                r"你刚才说.*所以.*",
                r"你的意思是.*",
                r"按照你的逻辑.*",
                r"你都.*了还说.*",
                r"你承认.*就.*",
            ],
            "indicators": [
                "歪曲原意",
                "过度概括",
                "转移话题"
            ],
            "severity": "high",
            "response": "澄清自己的真实观点，指出对方歪曲了你的意思"
        },
        "circular_reasoning": {
            "name": "循环论证",
            "description": "用待证明的结论作为前提来证明结论",
            "patterns": [
                r".*因为.*所以.*",
                r"这是.*因为.*属于.*",
                r".*是.*因为.*是.*",
                r"不言自明.*",
                r"很明显.*因为.*",
            ],
            "indicators": [
                "重复结论",
                "自我证明",
                "缺乏证据"
            ],
            "severity": "medium",
            "response": "指出论证的循环性，要求对方提供独立证据"
        },
        "burden_of_proof": {
            "name": "举证责任转移",
            "description": "将举证责任转移给不应承担举证责任的一方",
            "patterns": [
                r"请你证明.*",
                r"你有证据.*吗",
                r"你凭什么说.*",
                r"你能.*证据吗",
                r"如果没有.*证据",
                r"对方没有提供.*",
            ],
            "indicators": [
                "错误分配举证责任",
                "要求提供不可能的证据",
                "混淆举证责任"
            ],
            "severity": "high",
            "response": "明确指出举证责任的正确归属，依据\"谁主张谁举证\"原则反驳"
        },
        "emotional_manipulation": {
            "name": "情感操控",
            "description": "利用情感而非逻辑来影响判断",
            "patterns": [
                r".*可怜的.*",
                r".*不公平.*",
                r".*良心.*",
                r".*大家.*都.*",
                r".*社会.*",
                r".*道德.*",
                r".*人心.*",
            ],
            "indicators": [
                "诉诸情感",
                "道德绑架",
                "舆论压力"
            ],
            "severity": "medium",
            "response": "将话题拉回到法律和事实层面，不被情感操控"
        },
        "red_herring": {
            "name": "转移话题",
            "description": "引入无关话题来分散注意力",
            "patterns": [
                r"这件事.*不重要",
                r"关键问题是.*",
                r"真正.*是.*",
                r"先不说.*说说.*",
                r".*不是重点.*",
            ],
            "indicators": [
                "话题转移",
                "避重就轻",
                "混淆视听"
            ],
            "severity": "medium",
            "response": "坚持原有话题，指出对方在转移注意力"
        },
        "equivocation": {
            "name": "偷换概念",
            "description": "在论证过程中暗中改变概念的含义",
            "patterns": [
                r".*所谓.*是指.*",
                r"我们说的.*",
                r"这个.*不是那个.*",
                r"按照.*的理解.*",
                r"在.*意义上.*",
            ],
            "indicators": [
                "概念混淆",
                "语义游移",
                "双重标准"
            ],
            "severity": "high",
            "response": "要求对方明确概念的精确定义，指出概念的前后不一致"
        },
        "false_cause": {
            "name": "虚假因果",
            "description": "将时间上的先后关系误认为因果关系",
            "patterns": [
                r"之前.*所以.*",
                r"由于.*因此.*",
                r"因为.*导致.*",
                r".*之后.*就.*",
                r".*随即.*",
            ],
            "indicators": [
                "时间关联",
                "因果误判",
                "过度推断"
            ],
            "severity": "medium",
            "response": "指出相关性不等于因果关系，需要更多证据证明因果"
        },
        "appeal_to_authority": {
            "name": "权威谬误",
            "description": "以权威人士或机构的意见代替论证",
            "patterns": [
                r"专家说.*",
                r"根据.*的规定.*",
                r"法院.*认为.*",
                r"上级.*指示.*",
                r".*权威.*认为.*",
            ],
            "indicators": [
                "诉诸权威",
                "缺乏论证",
                "机械引用"
            ],
            "severity": "low",
            "response": "指出权威意见需要结合具体情况分析，机械套用可能不当"
        }
    }
    
    # 法官提问中的陷阱关键词
    JUDGE_TRAP_KEYWORDS = {
        "clarification_needed": ["请你说明", "你能解释一下", "具体是指什么", "详细说说"],
        "concession_sought": ["你是否认可", "你是否承认", "你是否同意", "你是否接受"],
        "leading_to_contradiction": ["那你的意思是", "这和之前说的", "你前后是否一致"],
        "hypothetical": ["假设", "如果", "假如", "万一"]
    }
    
    def __init__(self):
        self.trap_patterns = self.TRAP_PATTERNS
    
    def detect_trap(self, statement: str, speaker_role: str = "other") -> Dict:
        """
        检测语句中的陷阱
        
        Args:
            statement: 待检测的语句
            speaker_role: 讲话方角色
            
        Returns:
            检测结果，包含是否检测到陷阱、陷阱类型、严重程度、建议等
        """
        speaker_role = self._normalize_role(speaker_role)
        result = {
            "is_trap": False,
            "trap_types": [],
            "confidence": 0.0,
            "description": "",
            "severity": "none",
            "suggestion": "",
            "details": {}
        }
        
        # 预处理语句
        statement_clean = statement.strip()
        
        detected_traps = []
        
        for trap_id, trap_info in self.trap_patterns.items():
            confidence = 0.0
            matched_patterns = []
            
            for pattern in trap_info.get("patterns", []):
                matches = re.findall(pattern, statement_clean, re.IGNORECASE)
                if matches:
                    confidence += 0.3
                    matched_patterns.append(pattern)
            
            # 针对讲话方角色调整置信度
            if speaker_role in ["judge", "clerk"]:
                # 法官的问题通常较为中立，降低陷阱置信度
                confidence *= 0.5
            elif speaker_role in ["opponent_lawyer", "defendant_lawyer"]:
                # 对方律师更可能设置陷阱
                confidence *= 1.2
            
            if confidence >= 0.3:
                detected_traps.append({
                    "trap_id": trap_id,
                    "trap_name": trap_info["name"],
                    "description": trap_info["description"],
                    "confidence": min(confidence, 1.0),
                    "severity": trap_info["severity"],
                    "suggestion": trap_info["response"],
                    "matched_patterns": matched_patterns
                })
        
        # 按置信度排序
        detected_traps.sort(key=lambda x: x["confidence"], reverse=True)
        
        if detected_traps:
            # 最高置信度的陷阱
            top_trap = detected_traps[0]
            result["is_trap"] = True
            result["trap_types"] = [t["trap_name"] for t in detected_traps]
            result["confidence"] = top_trap["confidence"]
            result["description"] = top_trap["description"]
            result["severity"] = top_trap["severity"]
            result["suggestion"] = top_trap["suggestion"]
            result["details"] = {
                "primary_trap": top_trap,
                "all_traps": detected_traps
            }
        
        return result

    def _normalize_role(self, role: str) -> str:
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
    
    def analyze_judge_question(self, question: str) -> Dict:
        """
        分析法官提问的类型和意图
        
        Args:
            question: 法官的问题
            
        Returns:
            分析结果，包含问题类型、意图、回答策略
        """
        result = {
            "question_type": "general",
            "intent": "information_gathering",
            "requires_clarification": False,
            "seeks_concession": False,
            "leads_to_contradiction": False,
            "is_hypothetical": False,
            "response_strategy": "direct_answer",
            "tips": []
        }
        
        question_clean = question.strip()
        
        # 检测问题类型
        for qtype, keywords in self.JUDGE_TRAP_KEYWORDS.items():
            for keyword in keywords:
                if keyword in question_clean:
                    if qtype == "clarification_needed":
                        result["requires_clarification"] = True
                        result["response_strategy"] = "clarify"
                        result["tips"].append("法官希望你对某个问题进行更清晰的说明")
                    elif qtype == "concession_sought":
                        result["seeks_concession"] = True
                        result["response_strategy"] = "careful_answer"
                        result["tips"].append("法官在试探你是否愿意做出让步，回答时需谨慎")
                    elif qtype == "leading_to_contradiction":
                        result["leads_to_contradiction"] = True
                        result["response_strategy"] = "consistent"
                        result["tips"].append("法官可能在验证你陈述的一致性，请保持前后一致")
                    elif qtype == "hypothetical":
                        result["is_hypothetical"] = True
                        result["response_strategy"] = "hypothetical_answer"
                        result["tips"].append("这是假设性问题，可以说明在假设情况下的回答")
        
        # 判断问题类型
        if "?" in question_clean or "？" in question_clean:
            if any(word in question_clean for word in ["是否", "有没有", "是不是", "能不能"]):
                result["question_type"] = "yes_no"
            elif any(word in question_clean for word in ["为什么", "怎么", "如何", "什么", "哪个"]):
                result["question_type"] = "wh_question"
            elif any(word in question_clean for word in ["描述", "说明", "解释", "告诉"]):
                result["question_type"] = "explanation"
            elif any(word in question_clean for word in ["多少", "几", "多长时间"]):
                result["question_type"] = "quantitative"
        
        # 生成详细建议
        result["detailed_strategy"] = self._generate_judge_response_strategy(question, result)
        
        return result
    
    def _generate_judge_response_strategy(self, question: str, analysis: Dict) -> str:
        """生成针对法官问题的详细回答策略"""
        strategies = []
        
        if analysis["question_type"] == "yes_no":
            strategies.append("这是是非题，建议直接、明确地回答是或否")
            strategies.append("如果需要补充说明，在明确回答后再补充原因")
        elif analysis["question_type"] == "wh_question":
            strategies.append("这是开放式问题，建议全面、准确地回答")
            strategies.append("如有不确定的信息，应明确说明不确定的范围")
        elif analysis["question_type"] == "explanation":
            strategies.append("这是解释性问题，建议条理清晰地说明")
            strategies.append("可以使用\"第一、第二、第三\"等结构化表达")
        
        if analysis["requires_clarification"]:
            strategies.append("法官要求你澄清某些内容，请务必明确说明")
        
        if analysis["seeks_concession"]:
            strategies.append("⚠️ 法官在试探你的底线，回答时需谨慎权衡")
            strategies.append("避免轻易做出可能对自己不利的陈述")
        
        if analysis["leads_to_contradiction"]:
            strategies.append("⚠️ 法官可能在检查你陈述的一致性")
            strategies.append("保持冷静，确保回答与之前的陈述一致")
        
        if analysis["is_hypothetical"]:
            strategies.append("这是假设性问题，可以基于假设条件回答")
            strategies.append("注意区分\"假设情况下\"和\"实际情况\"的差异")
        
        return "\n".join(strategies)
    
    def detect_silent_traps(self, context: str, user_role: str = "plaintiff") -> List[Dict]:
        """
        检测沉默陷阱 - 识别不应说的话
        
        Args:
            context: 当前对话上下文
            user_role: 用户角色
            
        Returns:
            识别出的沉默陷阱列表
        """
        result = []
        
        # 定义各类沉默陷阱
        silent_traps = [
            {
                "id": "admission_without_condition",
                "name": "无条件的承认",
                "description": "在未了解全部事实的情况下做出承认",
                "dangerous_patterns": [
                    "我承认",
                    "确实",
                    "没有异议",
                    "你说的对"
                ],
                "avoidance": "任何承认都应附带条件或保留"
            },
            {
                "id": "speculation",
                "name": "无根据的推测",
                "description": "对不确定的事实进行推测性回答",
                "dangerous_patterns": [
                    "我估计",
                    "大概是",
                    "可能是",
                    "好像"
                ],
                "avoidance": "只陈述亲身经历的事实，对推测性内容表示不确定"
            },
            {
                "id": "emotional_response",
                "name": "情绪化回应",
                "description": "被激怒后做出情绪化的反应",
                "dangerous_patterns": [
                    "你胡说",
                    "完全是胡说八道",
                    "你有什么资格"
                ],
                "avoidance": "保持冷静，用事实和证据回应"
            },
            {
                "id": "unnecessary_volunteering",
                "name": "过度自白",
                "description": "提供超出问题范围的信息",
                "dangerous_patterns": [
                    "另外",
                    "还有",
                    "补充一下",
                    "而且"
                ],
                "avoidance": "只回答被问到的问题，不主动提供额外信息"
            },
            {
                "id": "hearsay_admission",
                "name": "传来证据的承认",
                "description": "承认听说的、未亲身验证的信息",
                "dangerous_patterns": [
                    "他们说",
                    "听谁说",
                    "据说",
                    "听说"
                ],
                "avoidance": "明确区分亲身经历的事实和听来的信息"
            }
        ]
        
        for trap in silent_traps:
            for pattern in trap["dangerous_patterns"]:
                if pattern in context:
                    result.append({
                        "type": trap["id"],
                        "name": trap["name"],
                        "description": trap["description"],
                        "avoidance": trap["avoidance"],
                        "warning": f"⚠️ 检测到可能的'{trap['name']}'，{trap['avoidance']}"
                    })
                    break
        
        return result
    
    def generate_counter_argument(self, 
                                 opposing_statement: str,
                                 case_info: Dict,
                                 my_position: str = "原告") -> Dict:
        """
        根据对方陈述生成反驳论据
        
        Args:
            opposing_statement: 对方的陈述
            case_info: 案件信息
            my_position: 我方立场
            
        Returns:
            反驳建议
        """
        prompt = f"""你是一位经验丰富的诉讼律师，现在需要针对对方的陈述进行反驳。

【我方立场】：{my_position}

【对方陈述】：
{opposing_statement}

【案件信息】：
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}
原告：{case_info.get('plaintiff', '未知')}
被告：{case_info.get('defendant', '未知')}
案件描述：{case_info.get('description', '未知')}

请分析对方陈述的漏洞，并提供：
1. 反驳要点（针对对方的每个论点）
2. 反驳话术（可立即使用的反驳语句）
3. 需要调用的证据（如有）
4. 反驳时机建议

请用JSON格式返回，包含：refutation_points, counter_arguments, required_evidence, timing_advice"""

        try:
            response = llm_service.chat([
                {"role": "system", "content": "你是一位专业的诉讼律师，擅长辩论和反驳。"},
                {"role": "user", "content": prompt}
            ])
            
            # 简单解析
            return {"success": True, "response": response}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_objection_template(self, objection_type: str) -> Dict:
        """
        生成异议模板
        
        Args:
            objection_type: 异议类型
            
        Returns:
            异议话术模板
        """
        templates = {
            "hearsay": {
                "title": "传闻证据异议",
                "template": "对方代理人，对于 {statement} 这一点，对方陈述的是传来证据，不具备证据资格。根据《最高人民法院关于民事诉讼证据的若干规定》第五十七条，证人应当陈述其亲历的具体事实。",
                "usage": "当对方陈述的内容是其听说的、非亲历时"
            },
            "leading": {
                "title": "诱导性提问异议",
                "template": "对方代理人的提问方式存在诱导性，问题的表述中已经预设了答案。请对方代理人重新组织问题。",
                "usage": "当对方律师的提问明显暗示期望的答案时"
            },
            "irrelevant": {
                "title": "无关性问题异议",
                "template": "对方代理人的提问与本案争议焦点无关，请法庭要求对方说明该问题与本案的关联性。",
                "usage": "当对方提问的内容与案件事实无关时"
            },
            "compound": {
                "title": "复合问题异议",
                "template": "对方代理人的提问是复合问题，将多个问题混在一起，我方无法针对性地回答。请对方代理人将问题分开询问。",
                "usage": "当对方将多个问题合并成一个时"
            },
            "speculation": {
                "title": "推测性意见异议",
                "template": "对方陈述的是推测性意见而非事实，不具备证据效力。根据证据规则，证人只能陈述亲身经历的事实，不能发表推测性意见。",
                "usage": "当证人或对方发表推测性意见时"
            },
            "argumentative": {
                "title": "辩论性陈述异议",
                "template": "这不是提问，而是在发表辩论意见。请对方代理人仅就事实问题进行提问。",
                "usage": "当对方以提问方式发表辩论意见时"
            }
        }
        
        return templates.get(objection_type, {
            "title": "一般异议",
            "template": "对方代理人的陈述，我方有异议，请求法庭记录在案。",
            "usage": "一般情况下的异议表达"
        })
    def analyze_statement(self, statement: str, speaker_role: str = "other") -> Dict:
        """便捷入口 — 分析单条语句中的陷阱。

        等同于 detect_trap()，提供更直观的 API 名称。
        """
        return self.detect_trap(statement, speaker_role)


# 全局实例
trap_detector = TrapDetector()
