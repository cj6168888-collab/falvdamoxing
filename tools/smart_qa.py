"""
增强版智能问答系统 - 问题澄清与精准回答
==========================================
核心特性：
1. 问题澄清机制 - 模糊问题时主动追问
2. 意图识别 - 精准识别用户想问什么
3. 上下文感知 - 利用已有信息精准回答
4. 证据发现 - 在问答中发现证据缺口
5. 引导补充 - 主动引导用户补充关键信息

设计理念：
- 精准是法律AI的第一原理
- 不确定时主动追问，而不是模糊处理
- 像资深律师一样，先理解清楚再回答
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class QuestionIntent(Enum):
    """问题意图类型"""
    UNCLEAR = "unclear"                    # 问题模糊
    FACT_QUERY = "fact_query"              # 事实查询
    EVIDENCE_QUERY = "evidence_query"      # 证据相关
    STRATEGY_QUERY = "strategy_query"      # 策略咨询
    RISK_QUERY = "risk_query"             # 风险评估
    PROCEDURE_QUERY = "procedure_query"    # 程序问题
    LEGAL_QUERY = "legal_query"            # 法律问题
    EVIDENCE_NEED = "evidence_need"       # 需要什么证据
    EVIDENCE_CHECK = "evidence_check"      # 证据核实
    GENERAL = "general"                   # 一般咨询


class ClarityLevel(Enum):
    """问题清晰度"""
    VERY_CLEAR = "very_clear"      # 非常清晰
    CLEAR = "clear"               # 清晰
    UNCLEAR = "unclear"           # 不清晰
    VERY_UNCLEAR = "very_unclear" # 完全模糊


@dataclass
class ClarifyingQuestion:
    """澄清性问题"""
    question: str                        # 问题文本
    reason: str                         # 需要澄清的原因
    options: Optional[List[str]] = None  # 选项（如有）
    key_point: str = ""                 # 关键点
    priority: int = 1                  # 优先级 1-5


@dataclass
class QuestionAnalysis:
    """问题分析结果"""
    # 意图识别
    intent: QuestionIntent
    intent_confidence: float = 1.0  # 置信度 0-1
    
    # 清晰度评估
    clarity: ClarityLevel = ClarityLevel.UNCLEAR
    clarity_reasons: List[str] = field(default_factory=list)
    
    # 关键实体
    key_entities: Dict[str, Any] = field(default_factory=dict)
    # {
    #   "money": ["金额1", "金额2"],
    #   "time": ["2024-01-01"],
    #   "person": ["原告", "被告"],
    #   "action": ["签订合同", "违约"]
    # }
    
    # 模糊点
    ambiguity_points: List[str] = field(default_factory=list)
    
    # 需要澄清的问题
    clarifying_questions: List[ClarifyingQuestion] = field(default_factory=list)
    
    # 建议补充的上下文
    suggested_context: List[str] = field(default_factory=list)
    
    # 是否有证据发现
    evidence_discoveries: List[Dict] = field(default_factory=list)
    
    @property
    def needs_clarification(self) -> bool:
        """是否需要澄清"""
        return (self.clarity in [ClarityLevel.UNCLEAR, ClarityLevel.VERY_UNCLEAR] or
                len(self.clarifying_questions) > 0 or
                self.intent == QuestionIntent.UNCLEAR)
    
    def to_dict(self) -> dict:
        return {
            "intent": self.intent.value,
            "intent_confidence": self.intent_confidence,
            "clarity": self.clarity.value,
            "key_entities": self.key_entities,
            "ambiguity_points": self.ambiguity_points,
            "clarifying_questions": [
                {
                    "question": q.question,
                    "reason": q.reason,
                    "options": q.options,
                    "key_point": q.key_point,
                    "priority": q.priority
                }
                for q in self.clarifying_questions
            ],
            "needs_clarification": self.needs_clarification,
            "evidence_discoveries": self.evidence_discoveries
        }


class SmartQuestionAnalyzer:
    """
    智能问题分析器
    
    核心能力：
    1. 意图识别 - 精准识别用户问题类型
    2. 清晰度评估 - 评估问题是否足够具体
    3. 澄清追问 - 模糊时主动追问
    4. 证据发现 - 从问题中发现证据线索
    """
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
    
    def analyze_question(
        self, 
        question: str, 
        case_info: Dict = None,
        conversation_context: List[Dict] = None
    ) -> QuestionAnalysis:
        """
        全面分析用户问题
        
        Args:
            question: 用户问题
            case_info: 案件信息
            conversation_context: 对话历史
            
        Returns:
            问题分析结果
        """
        analysis = QuestionAnalysis(intent=QuestionIntent.GENERAL)
        
        # 1. 意图识别
        analysis.intent = self._classify_intent(question)
        
        # 2. 清晰度评估
        analysis.clarity, analysis.clarity_reasons = self._assess_clarity(
            question, case_info
        )
        
        # 3. 提取关键实体
        analysis.key_entities = self._extract_entities(question, case_info)
        
        # 4. 识别模糊点
        analysis.ambiguity_points = self._identify_ambiguities(
            question, case_info, analysis
        )
        
        # 5. 如果模糊，生成澄清问题
        if analysis.clarity in [ClarityLevel.UNCLEAR, ClarityLevel.VERY_UNCLEAR]:
            analysis.clarifying_questions = self._generate_clarifying_questions(
                question, case_info, analysis
            )
        
        # 6. 检查是否发现证据线索
        analysis.evidence_discoveries = self._check_evidence_mentions(question)
        
        return analysis
    
    def _classify_intent(self, question: str) -> QuestionIntent:
        """分类问题意图"""
        question_lower = question.lower()
        
        # 意图关键词映射
        intent_keywords = {
            QuestionIntent.EVIDENCE_QUERY: [
                "证据", "材料", "证明", "有什么证据", "需要什么证据",
                "证据不足", "补充证据", "证据链"
            ],
            QuestionIntent.STRATEGY_QUERY: [
                "怎么办", "怎么处理", "怎么打", "策略", "诉讼策略",
                "怎么应对", "下一步", "建议"
            ],
            QuestionIntent.RISK_QUERY: [
                "风险", "败诉", "胜诉", "有没有把握", "会不会输",
                "赢了", "输的可能性", "风险点"
            ],
            QuestionIntent.PROCEDURE_QUERY: [
                "流程", "多久", "什么时候", "程序", "步骤",
                "时间线", "周期", "一审", "二审"
            ],
            QuestionIntent.LEGAL_QUERY: [
                "法律", "规定", "条", "条款", "违法", "合法",
                "权利", "义务", "责任", "构成要件"
            ],
            QuestionIntent.FACT_QUERY: [
                "事实", "经过", "情况", "发生了什么", "事实是什么",
                "时间", "地点", "金额", "人名"
            ],
            QuestionIntent.EVIDENCE_NEED: [
                "需要什么证据", "还缺什么", "应该准备什么",
                "缺少证据", "补充什么"
            ],
            QuestionIntent.EVIDENCE_CHECK: [
                "有没有证据", "有没有合同", "有没有转账",
                "有没有记录", "这个能不能证明"
            ]
        }
        
        for intent, keywords in intent_keywords.items():
            if any(kw in question_lower for kw in keywords):
                return intent
        
        return QuestionIntent.GENERAL
    
    def _assess_clarity(
        self, 
        question: str, 
        case_info: Dict = None
    ) -> tuple:
        """评估问题清晰度"""
        clarity = ClarityLevel.CLEAR
        reasons = []
        
        # 太短的问题通常模糊
        if len(question) < 10:
            clarity = ClarityLevel.VERY_UNCLEAR
            reasons.append("问题太简短，无法确定具体意图")
        elif len(question) < 20:
            clarity = ClarityLevel.UNCLEAR
            reasons.append("问题较为简短，可能需要补充信息")
        
        # 模糊词检查
        vague_words = ["怎么样", "如何", "有没有", "能不能", "行不行", "怎么办", "怎么"]
        vague_count = sum(1 for w in vague_words if w in question)
        
        if vague_count >= 2:
            clarity = ClarityLevel.UNCLEAR if clarity == ClarityLevel.CLEAR else clarity
            reasons.append(f"问题包含{vague_count}个模糊词，需要具体化")
        
        # 缺少关键信息
        missing_info = []
        
        if case_info:
            # 检查是否提到当事人
            if case_info.get('plaintiff') and case_info['plaintiff'] not in question:
                # 原告在案件中，但问题没提
                pass  # 不算缺失
            
            # 检查是否提到金额
            if "金额" in question or "多少" in question:
                if not re_search(r'\d+[万千百]?元', question) and not case_info.get('claim_amount'):
                    missing_info.append("金额")
        
        # 问句结构检查
        if question.endswith("？") or question.endswith("?"):
            pass  # 正常问题
        
        # 综合判断
        if len(reasons) >= 2 or clarity == ClarityLevel.VERY_UNCLEAR:
            clarity = ClarityLevel.VERY_UNCLEAR
        elif reasons or missing_info:
            clarity = ClarityLevel.UNCLEAR
        
        return clarity, reasons
    
    def _extract_entities(self, question: str, case_info: Dict = None) -> Dict[str, List]:
        """提取关键实体"""
        import re
        
        entities = {
            "money": [],
            "time": [],
            "person": [],
            "action": [],
            "place": []
        }
        
        # 提取金额
        money_pattern = r'(\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:[万千百]?元|万|千))'
        money_matches = re.findall(money_pattern, question)
        entities["money"] = money_matches
        
        # 提取日期
        date_pattern = r'(\d{4}[年\-/]\d{1,2}[月\-/]\d{1,2}日?)'
        date_matches = re.findall(date_pattern, question)
        entities["time"] = date_matches
        
        # 提取人名（简单模式）
        if case_info:
            for person in [case_info.get('plaintiff'), case_info.get('defendant')]:
                if person and person in question:
                    entities["person"].append(person)
        
        # 提取关键行为
        actions = ["签订", "付款", "违约", "侵权", "转账", "交付", "催告", "承诺"]
        for action in actions:
            if action in question:
                entities["action"].append(action)
        
        return entities
    
    def _identify_ambiguities(
        self, 
        question: str, 
        case_info: Dict,
        analysis: QuestionAnalysis
    ) -> List[str]:
        """识别问题中的模糊点"""
        ambiguities = []
        
        # 缺少金额
        if ("多少" in question or "金额" in question) and not analysis.key_entities["money"]:
            ambiguities.append("未明确具体金额")
        
        # 缺少时间
        if ("什么时候" in question or "时间" in question) and not analysis.key_entities["time"]:
            ambiguities.append("未明确具体时间")
        
        # 缺少行为描述
        if ("怎么" in question or "情况" in question) and len(question) < 30:
            ambiguities.append("问题缺乏具体事实描述")
        
        # 证据相关但不清楚
        if analysis.intent in [QuestionIntent.EVIDENCE_QUERY, QuestionIntent.EVIDENCE_NEED]:
            if not analysis.key_entities["money"] and not analysis.key_entities["action"]:
                ambiguities.append("未说明需要证明的具体事实")
        
        return ambiguities
    
    def _generate_clarifying_questions(
        self, 
        question: str, 
        case_info: Dict,
        analysis: QuestionAnalysis
    ) -> List[ClarifyingQuestion]:
        """生成澄清问题"""
        questions = []
        
        # 基于意图生成问题
        if analysis.intent == QuestionIntent.GENERAL or analysis.clarity == ClarityLevel.VERY_UNCLEAR:
            questions.append(ClarifyingQuestion(
                question="您想了解的是哪方面？",
                reason="问题比较模糊，我需要知道您的具体需求",
                options=[
                    "案件事实情况",
                    "需要准备哪些证据",
                    "如何制定诉讼策略",
                    "胜诉的可能性有多大",
                    "诉讼的流程和时间"
                ],
                key_point="明确问题方向",
                priority=1
            ))
        
        # 证据相关
        if analysis.intent in [QuestionIntent.EVIDENCE_QUERY, QuestionIntent.EVIDENCE_NEED]:
            if not analysis.key_entities["action"]:
                questions.append(ClarifyingQuestion(
                    question="您想证明的是什么事实？",
                    reason="证据需要与具体事实对应",
                    options=[
                        "合同关系成立",
                        "款项已经支付",
                        "对方存在违约行为",
                        "损失的具体金额",
                        "侵权行为的存在"
                    ],
                    key_point="明确证明目标",
                    priority=1
                ))
        
        # 金额相关
        if not analysis.key_entities["money"] and ("多少" in question or "金额" in question):
            questions.append(ClarifyingQuestion(
                question="涉及的具体金额是多少？",
                reason="需要知道金额才能准确分析",
                options=None,
                key_point="明确金额"
            ))
        
        # 风险相关
        if analysis.intent == QuestionIntent.RISK_QUERY:
            questions.append(ClarifyingQuestion(
                question="您更关心的是胜诉概率还是诉讼风险？",
                reason="不同关注点需要不同的分析角度",
                options=[
                    "胜诉的概率有多大",
                    "可能面临哪些风险",
                    "两者都想知道"
                ],
                key_point="明确分析重点",
                priority=2
            ))
        
        # 策略相关
        if analysis.intent == QuestionIntent.STRATEGY_QUERY:
            questions.append(ClarifyingQuestion(
                question="您目前处于案件的哪个阶段？",
                reason="不同阶段的策略重点不同",
                options=[
                    "还没起诉，在考虑是否起诉",
                    "已经起诉，在准备答辩",
                    "已经立案，在准备开庭",
                    "判决后，在考虑是否上诉"
                ],
                key_point="明确案件阶段",
                priority=1
            ))
        
        return questions[:3]  # 最多返回3个问题
    
    def _check_evidence_mentions(self, question: str) -> List[Dict]:
        """检查问题中提到的证据线索"""
        discoveries = []
        
        evidence_keywords = {
            "合同": ["合同", "协议"],
            "转账": ["转账", "汇款", "支付", "付款"],
            "聊天记录": ["微信", "聊天", "短信"],
            "录音": ["录音", "通话"],
            "发票": ["发票", "收据"],
            "邮件": ["邮件", "email"]
        }
        
        for evidence_type, keywords in evidence_keywords.items():
            if any(kw in question for kw in keywords):
                discoveries.append({
                    "type": evidence_type,
                    "mentioned": True,
                    "action": "询问证据情况"
                })
        
        return discoveries


class SmartQAService:
    """
    智能问答服务
    
    核心流程：
    1. 分析问题 - 理解用户想问什么
    2. 澄清追问 - 不清晰时主动追问
    3. 精准回答 - 结合上下文准确回答
    4. 证据发现 - 发现证据缺口并提示
    """
    
    def __init__(self, llm_service=None, evidence_graph=None):
        self.llm = llm_service
        self.evidence_graph = evidence_graph
        self.analyzer = SmartQuestionAnalyzer(llm_service)
    
    def ask(
        self,
        question: str,
        case_info: Dict,
        case_id: int = None,
        conversation_context: List[Dict] = None
    ) -> Dict:
        """
        处理问答请求
        
        返回格式：
        {
            "needs_clarification": bool,
            "clarifying_questions": [...],
            "answer": str,
            "intent": str,
            "evidence_suggestions": [...],
            "confidence": float
        }
        """
        # 1. 分析问题
        analysis = self.analyzer.analyze_question(
            question, case_info, conversation_context
        )
        
        # 2. 如果需要澄清，返回澄清问题
        if analysis.needs_clarification:
            return {
                "needs_clarification": True,
                "clarifying_questions": [
                    {
                        "question": q.question,
                        "reason": q.reason,
                        "options": q.options,
                        "key_point": q.key_point,
                        "priority": q.priority
                    }
                    for q in analysis.clarifying_questions
                ],
                "answer": None,
                "intent": analysis.intent.value,
                "evidence_suggestions": [],
                "confidence": 0.5,
                "analysis": analysis.to_dict()
            }
        
        # 3. 构建精准回答的提示词
        answer = self._generate_precise_answer(
            question, case_info, analysis, case_id
        )
        
        # 4. 生成证据建议
        evidence_suggestions = self._generate_evidence_suggestions(
            question, case_info, analysis, case_id
        )
        
        return {
            "needs_clarification": False,
            "clarifying_questions": [],
            "answer": answer,
            "intent": analysis.intent.value,
            "evidence_suggestions": evidence_suggestions,
            "confidence": 0.85,
            "analysis": analysis.to_dict()
        }
    
    def _generate_precise_answer(
        self,
        question: str,
        case_info: Dict,
        analysis: QuestionAnalysis,
        case_id: int = None
    ) -> str:
        """生成精准回答"""
        
        # 根据意图构建不同的提示词
        intent_prompts = {
            QuestionIntent.EVIDENCE_QUERY: """你是一位专业诉讼律师，擅长证据分析。
请根据案件证据内容，直接回答关于证据的问题。
必须引用证据原文条款，不能凭空回答。
如果涉及证据不足，明确指出并给出补充建议。""",

            QuestionIntent.EVIDENCE_NEED: """你是一位专业诉讼律师，擅长证据策略。
请根据案件证据内容和类型，列出需要的关键证据。
对于缺失的证据，给出具体的获取建议和优先级。""",

            QuestionIntent.STRATEGY_QUERY: """你是一位顶级诉讼策略专家。
请结合案件证据全文，给出具体的、可执行的策略建议。
每个策略建议必须基于具体证据条款。
策略要分清主次，给出优先级。""",

            QuestionIntent.RISK_QUERY: """你是一位专业诉讼风险评估专家。
请客观分析案件的风险点和胜诉概率。
必须结合证据全文和对抗性分析结论评估。
用数据或百分比说明，更具说服力。""",

            QuestionIntent.PROCEDURE_QUERY: """你是一位专业诉讼律师，擅长诉讼程序。
请说明具体的流程、时间和注意事项。
包含各阶段的大致时间节点。""",

            QuestionIntent.LEGAL_QUERY: """你是一位专业法律专家。
请引用具体的法律条文，给出准确的法律分析。
区分法律规定和学理解释。
结合案件证据指出法律适用问题。""",

            QuestionIntent.FACT_QUERY: """你是一位专业诉讼律师，擅长事实分析。
请基于证据原文，准确描述案件事实。
必须引用证据条款支撑事实陈述。
如有不清楚的地方，明确指出证据缺口。"""
        }
        
        system_prompt = intent_prompts.get(
            analysis.intent,
            "你是一位专业法律顾问。请直接、精准地回答用户问题。"
        )
        
        # 构建用户提示词
        # 如果 case_info 包含证据全文和分析结论，则使用
        evidence_section = ""
        if case_info.get('evidence_full_text'):
            evidence_section = f"\n\n【证据全文内容】\n{case_info['evidence_full_text']}\n"
        elif case_info.get('evidence_summary'):
            evidence_section = f"\n\n【证据摘要】\n{case_info['evidence_summary']}\n"

        adv_section = ""
        if case_info.get('adversarial_analysis'):
            adv_section = f"\n\n【对抗性分析结论】\n{case_info['adversarial_analysis']}\n"

        user_content = f"""【案件信息】
案件名称：{case_info.get('title', '未知')}
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}
原告：{case_info.get('plaintiff', '未知')}
被告：{case_info.get('defendant', '未知')}
诉讼金额：{case_info.get('claim_amount', '未知')}
案件描述：{case_info.get('description', '暂无描述')}
补充说明：{case_info.get('supplement', '暂无')}
{evidence_section}{adv_section}

【用户问题】
{question}

【问题意图】
{analysis.intent.value}

【已识别的关键实体】
{json.dumps(analysis.key_entities, ensure_ascii=False)}

⚠️ 重要要求：
- 回答必须引用证据原文或法条原文，不能凭空回答
- 如问题涉及证据条款，必须指出具体条款
- 如证据不足，明确指出需要补充的证据类型
        
        if self.llm:
            answer = self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ], model="qwen-plus")
            return answer
        
        return "请提供更多案件信息以便我给出准确建议。"
    
    def _generate_evidence_suggestions(
        self,
        question: str,
        case_info: Dict,
        analysis: QuestionAnalysis,
        case_id: int = None
    ) -> List[Dict]:
        """生成证据建议"""
        suggestions = []
        
        # 从问题中发现证据线索
        for discovery in analysis.evidence_discoveries:
            evidence_type = discovery["type"]
            
            # 检查证据图谱
            if self.evidence_graph and case_id:
                existing = self.evidence_graph.query_evidence(
                    case_id, evidence_type, "type"
                )
                
                if existing:
                    suggestions.append({
                        "type": "confirm",
                        "evidence_type": evidence_type,
                        "message": f"您提到了{evidence_type}，系统中已有相关记录",
                        "action": "确认是否需要补充"
                    })
                else:
                    suggestions.append({
                        "type": "suggest",
                        "evidence_type": evidence_type,
                        "message": f"您提到了{evidence_type}，建议上传相关证据",
                        "action": "上传证据"
                    })
            else:
                suggestions.append({
                    "type": "suggest",
                    "evidence_type": evidence_type,
                    "message": f"您提到了{evidence_type}，这是重要证据",
                    "action": "确认是否有相关证据"
                })
        
        # 基于案件类型建议证据
        if analysis.intent in [QuestionIntent.EVIDENCE_QUERY, QuestionIntent.EVIDENCE_NEED]:
            case_type = case_info.get('case_type', '')
            
            common_evidence = {
                "合同纠纷": ["合同原件", "转账凭证", "沟通记录", "发票收据"],
                "侵权纠纷": ["侵权证据", "损害证明", "因果关系鉴定", "现场照片"],
                "债务纠纷": ["借条欠条", "转账记录", "催款记录", "聊天记录"]
            }
            
            evidence_list = common_evidence.get(case_type, common_evidence["合同纠纷"])
            suggestions.append({
                "type": "common",
                "evidence_list": evidence_list,
                "message": f"根据{case_type}类型，通常需要以下证据"
            })
        
        return suggestions
    
    def get_followup_questions(
        self,
        question: str,
        answer: str,
        case_info: Dict
    ) -> List[str]:
        """根据回答生成追问建议"""
        if not self.llm:
            return []
        
        prompt = f"""基于以下问答，生成3个用户可能想追问的问题。

【用户问题】
{question}

【AI回答】
{answer}

【案件信息】
案件类型：{case_info.get('case_type', '未知')}
案由：{case_info.get('cause', '未知')}

请生成3个追问，格式为JSON数组：
["追问1", "追问2", "追问3"]

追问应该：
1. 深入挖掘回答中的关键点
2. 提出用户实际可能关心的问题
3. 引导用户补充案件信息"""
        
        try:
            response = self.llm.chat([
                {"role": "system", "content": "生成追问问题。"},
                {"role": "user", "content": prompt}
            ], model="qwen-plus")
            
            return json.loads(response)
        except:
            return []


# 全局实例
smart_qa_service = None

def get_smart_qa_service(llm_service=None, evidence_graph=None) -> SmartQAService:
    """获取智能问答服务实例"""
    global smart_qa_service
    if smart_qa_service is None:
        smart_qa_service = SmartQAService(llm_service, evidence_graph)
    elif llm_service and smart_qa_service.llm is None:
        smart_qa_service.llm = llm_service
        smart_qa_service.analyzer.llm = llm_service
    return smart_qa_service
