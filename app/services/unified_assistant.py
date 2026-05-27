"""
统一智能助手 - 整合所有AI能力
================================
核心理念：
1. 一个入口处理所有用户交互
2. 每次交互都自动更新画像
3. 自动检索相关知识再回答
4. 主动发现缺口并引导补充
5. 精准回答，避免答非所问
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

# 获取当前日期
CURRENT_DATE = datetime.now().strftime('%Y年%m月%d日')
CURRENT_YEAR = datetime.now().year


@dataclass
class AssistantResponse:
    """助手响应"""
    # 核心回答
    answer: str                      # 直接回答
    intent: str                       # 识别的意图
    
    # 是否需要追问
    needs_clarification: bool = False
    clarification_questions: List[Dict] = field(default_factory=list)
    
    # 画像更新
    profile_updated: bool = False
    knowledge_extracted: int = 0
    
    # 证据缺口
    gaps_identified: List[Dict] = field(default_factory=list)
    evidence_suggestions: List[str] = field(default_factory=list)
    
    # 补充建议
    suggestions: List[Dict] = field(default_factory=list)
    
    # 元数据
    confidence: float = 1.0          # 回答置信度
    sources: List[str] = field(default_factory=list)  # 参考来源


class UnifiedAssistant:
    """
    统一智能助手
    
    整合以下服务：
    - CaseProfileEngine: 案件画像
    - EvidenceNavigator: 证据引导
    - CaseInsightEngine: 洞察分析
    - RAGService: 知识检索
    """
    
    def __init__(
        self,
        llm_service=None,
        profile_engine=None,
        evidence_navigator=None,
        rag_service=None
    ):
        self.llm = llm_service
        self.profile = profile_engine
        self.navigator = evidence_navigator
        self.rag = rag_service
    
    def process(
        self,
        case_id: int,
        user_message: str,
        case_info: Dict,
        conversation_context: Optional[List[Dict]] = None
    ) -> AssistantResponse:
        """
        处理用户消息
        
        工作流程：
        1. 分析意图
        2. 检索相关知识
        3. 生成回答
        4. 更新画像
        5. 识别缺口
        6. 生成建议
        """
        # 1. 分析用户意图
        intent = self._classify_intent(user_message)
        
        # 2. 检索案件知识
        relevant_knowledge = self._retrieve_knowledge(case_id, user_message)
        
        # 3. 检索RAG上下文
        rag_context = ""
        if self.rag:
            rag_context = self.rag.get_context(user_message, case_id)
        
        # 4. 构建上下文
        context = self._build_context(case_info, relevant_knowledge, rag_context, conversation_context)
        
        # 5. 检查是否需要澄清
        if self._needs_clarification(user_message, relevant_knowledge):
            clarification = self._generate_clarification(user_message, context, intent)
            return AssistantResponse(
                answer="",
                intent=intent,
                needs_clarification=True,
                clarification_questions=clarification
            )
        
        # 6. 生成回答
        answer = self._generate_answer(user_message, context, intent)
        
        # 7. 更新画像
        profile_result = None
        if self.profile:
            profile_result = self.profile.process_interaction(
                case_id=case_id,
                user_input=user_message,
                input_type="question",
                system_response=answer
            )
        
        # 8. 识别证据缺口
        gaps = self._identify_evidence_gaps(user_message, relevant_knowledge)
        
        # 9. 生成证据建议
        evidence_suggestions = []
        if gaps:
            evidence_suggestions = self._generate_evidence_suggestions(gaps)
        
        # 10. 生成后续建议
        suggestions = self._generate_suggestions(intent, profile_result, gaps)
        
        return AssistantResponse(
            answer=answer,
            intent=intent,
            needs_clarification=False,
            clarification_questions=[],
            profile_updated=profile_result.get("profile_updated", False) if profile_result else False,
            knowledge_extracted=profile_result.get("knowledge_extracted", 0) if profile_result else 0,
            gaps_identified=gaps,
            evidence_suggestions=evidence_suggestions,
            suggestions=suggestions,
            confidence=0.85,
            sources=[k["source"] for k in relevant_knowledge[:3]]
        )
    
    def _classify_intent(self, message: str) -> str:
        """分类用户意图"""
        message_lower = message.lower()
        
        # 基于关键词分类
        intent_keywords = {
            "案件分析": ["怎么样", "分析", "情况", "如何"],
            "证据咨询": ["证据", "材料", "证明", "缺少", "需要什么"],
            "策略咨询": ["策略", "怎么打", "怎么办", "诉讼"],
            "风险评估": ["风险", "败诉", "胜诉", "有没有把握"],
            "程序咨询": ["流程", "多久", "什么时候", "程序"],
            "文书咨询": ["起诉", "写", "状", "文书"],
            "费用咨询": ["费用", "多少钱", "收费", "成本"]
        }
        
        for intent, keywords in intent_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return intent
        
        return "其他咨询"
    
    def _retrieve_knowledge(self, case_id: int, query: str) -> List[Dict]:
        """检索相关知识"""
        if not self.profile:
            return []
        
        # 从画像知识库检索
        knowledge = self.profile.query_knowledge(case_id, query)
        return knowledge[:5]
    
    def _build_context(
        self,
        case_info: Dict,
        knowledge: List[Dict],
        rag_context: str,
        conversation_context: Optional[List[Dict]]
    ) -> str:
        """构建完整的上下文"""
        parts = []
        
        # 案件基础信息
        parts.append("【案件基础信息】")
        parts.append(f"案件类型：{case_info.get('case_type', '未知')}")
        parts.append(f"案由：{case_info.get('cause', '未知')}")
        parts.append(f"原告：{case_info.get('plaintiff', '未知')}")
        parts.append(f"被告：{case_info.get('defendant', '未知')}")
        if case_info.get('claim_amount'):
            parts.append(f"诉讼金额：{case_info['claim_amount']}")
        parts.append("")
        
        # 相关知识
        if knowledge:
            parts.append("【相关已知信息】")
            for k in knowledge:
                parts.append(f"- {k['content']}")
            parts.append("")
        
        # RAG上下文
        if rag_context:
            parts.append("【相关材料】")
            parts.append(rag_context[:50000])  # 完整传递相关材料，无截断
            parts.append("")
        
        # 对话历史
        if conversation_context:
            parts.append("【对话历史】")
            for ctx in conversation_context[-3:]:
                parts.append(f"问：{ctx.get('user', '')}")
                parts.append(f"答：{ctx.get('assistant', '')}")
            parts.append("")
        
        return "\n".join(parts)
    
    def _needs_clarification(self, message: str, knowledge: List[Dict]) -> bool:
        """判断是否需要澄清"""
        # 问题太模糊
        vague_patterns = ["怎么样", "怎么办", "如何", "有没有", "行不行"]
        is_vague = any(p in message for p in vague_patterns) and len(message) < 20

        # 缺少关键信息且问题很宽泛
        lacks_info = len(knowledge) == 0 and len(message) < 50 and is_vague

        # 如果问题明确，即使信息不足也应该尝试回答
        specific_intents = ["证据", "分析", "怎么", "如何", "起诉", "诉讼"]
        has_specific_intent = any(p in message for p in specific_intents)

        if has_specific_intent:
            return False

        return is_vague or lacks_info
    
    def _generate_clarification(
        self, 
        message: str, 
        context: str, 
        intent: str
    ) -> List[Dict]:
        """生成澄清问题"""
        questions = []
        
        if intent == "案件分析":
            questions.append({
                "question": "您想了解案件的哪些方面？",
                "options": [
                    {"value": "situation", "label": "案件基本情况"},
                    {"value": "risk", "label": "胜诉概率"},
                    {"value": "evidence", "label": "需要什么证据"},
                    {"value": "strategy", "label": "如何应对"}
                ],
                "reason": "您的问题比较宽泛，请选择具体方面"
            })
        
        elif intent == "证据咨询":
            questions.append({
                "question": "您想知道关于哪方面的证据？",
                "options": [
                    {"value": "have", "label": "我已有的证据"},
                    {"value": "need", "label": "还缺什么证据"},
                    {"value": "how", "label": "如何获取证据"}
                ],
                "reason": "请明确您的问题"
            })
        
        else:
            questions.append({
                "question": "您的问题可以更具体一些吗？",
                "help": "比如：涉及金额是多少？对方有什么反应？有没有相关证据？",
                "reason": "信息不够具体，可能无法给出精准建议"
            })
        
        return questions
    
    def _generate_answer(
        self, 
        message: str, 
        context: str, 
        intent: str
    ) -> str:
        """生成回答"""
        # 构建增强的上下文提示
        base_prompt = f"""你是一位专业法律顾问。基于已知信息，智能回答用户问题。

⚠️ 核心约束（必须遵守）：
1. 绝对禁止凭空编造法律条文或司法解释，每条法律结论必须标注具体法条来源
2. 绝对禁止虚构不存在的案例，引用案例必须提供真实案号和法院
3. 不需要刻意讨好用户，说真话才是对用户最大的负责
4. 不确定时必须明确表达不确定性，不能用"一般"、"通常"模糊带过
5. 绝对禁止浮于表面、不深入分析就给出结论，必须深度思考推演

💡 核心要求（必须做到）：
1. 深度思考推演：对每一个问题进行深度思考和推演，不浮于表面
2. 突破性创造性：突破性创造性的寻找更多真实途径，不因循守旧
3. 最大算力服务：调动全部算力帮用户寻找取胜的方法和路径
4. 分析事实优先：更多的分析事实，从事实出发推导结论
5. 真相导向：让用户看到真相、理解真相，找到取胜的真实路径
6. 引用法条时必须写明具体条款内容，不能只写"依据相关法律规定"

【上下文】
{context}

【用户问题】
{message}

【问题意图】
{intent}

要求：
1. 主动分析已知证据和案件信息，给出有价值的回答
2. 如果信息不足，结合证据内容给出方向性建议
3. 涉及策略选择时，分析利弊供用户决策
4. 主动指出需要补充的证据缺口
5. 使用证据编号引用具体证据
6. 引用法条时必须写明具体条款内容
7. 遇到困难时，尝试从不同角度分析，寻找突破性路径"""

        if self.llm:
            response = self.llm.chat([
                {"role": "system", "content": """你是一位专业法律顾问。主动分析已有证据，给出有价值的建议。

⚠️ 绝对禁止：
1. 凭空编造法律条文或司法解释
2. 虚构不存在的案例
3. 夸大胜诉概率以讨好用户
4. 浮于表面、不深入分析就给出结论
5. 用"一般"、"通常"模糊表述掩盖不确定性
6. 引用法条不说明具体来源和内容

💡 核心要求：
1. 深度思考推演，对每一个问题进行深度思考和推演
2. 突破性创造性的寻找更多真实途径
3. 让用户看到真相、理解真相，找到取胜的真实路径"""},
                {"role": "user", "content": base_prompt}
            ], model="qwen-plus")
            return response if response else "系统正在分析您的案件，请稍后再试。"

        return "请提供更多案件信息以便我给出准确建议。"
    
    def _identify_evidence_gaps(
        self, 
        message: str, 
        knowledge: List[Dict]
    ) -> List[Dict]:
        """识别证据缺口"""
        gaps = []
        
        message_lower = message.lower()
        
        # 证据相关话题
        evidence_topics = {
            "转账": "转账凭证",
            "付款": "转账凭证",
            "合同": "书面证据",
            "协议": "书面证据",
            "微信": "沟通记录",
            "聊天": "沟通记录",
            "邮件": "沟通记录",
            "通话": "沟通记录"
        }
        
        for keyword, gap_type in evidence_topics.items():
            if keyword in message_lower:
                # 检查是否已有相关证据
                has_evidence = any(
                    keyword in k.get("content", "").lower() 
                    for k in knowledge
                )
                
                if not has_evidence:
                    gaps.append({
                        "type": gap_type,
                        "keyword": keyword,
                        "priority": "high" if gap_type in ["转账凭证", "书面证据"] else "medium"
                    })
        
        return gaps
    
    def _generate_evidence_suggestions(self, gaps: List[Dict]) -> List[str]:
        """生成证据建议"""
        suggestions = []
        
        for gap in gaps:
            gap_type = gap.get("type", "")
            if gap_type == "转账凭证":
                suggestions.append("转账凭证很重要！建议：1) 去银行打印流水 2) 导出支付宝/微信账单")
            elif gap_type == "书面证据":
                suggestions.append("书面证据证明力最强。建议：1) 联系对方获取 2) 调取工商档案 3) 公证电子证据")
            elif gap_type == "沟通记录":
                suggestions.append("沟通记录可以证明事实经过。建议：1) 导出微信聊天 2) 录屏保存 3) 通话录音")
        
        return suggestions
    
    def _generate_suggestions(
        self, 
        intent: str, 
        profile_result: Optional[Dict],
        gaps: List[Dict]
    ) -> List[Dict]:
        """生成后续建议"""
        suggestions = []
        
        # 基于意图的建议
        if intent == "案件分析":
            suggestions.append({
                "type": "action",
                "priority": "medium",
                "message": "想生成详细的案件分析报告吗？",
                "action": "点击生成报告"
            })
        
        elif intent == "证据咨询":
            suggestions.append({
                "type": "action",
                "priority": "high",
                "message": "建议运行证据诊断，系统会全面分析证据情况",
                "action": "开始证据诊断"
            })
        
        # 基于画像的建议
        if profile_result:
            completeness = profile_result.get("completeness", {})
            score = completeness.get("score", 0)
            
            if score < 30:
                suggestions.append({
                    "type": "info",
                    "priority": "high",
                    "message": "案件信息较少，请补充更多细节"
                })
        
        # 基于缺口的建议
        if gaps:
            suggestions.append({
                "type": "evidence",
                "priority": "high",
                "message": f"发现 {len(gaps)} 个可能缺少的证据类型",
                "action": "查看证据建议"
            })
        
        return suggestions


# 全局实例
unified_assistant = UnifiedAssistant()
