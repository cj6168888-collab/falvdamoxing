"""
单条证据智能问答系统
==================
功能：
1. 针对单条证据的深度问答
2. AI防跑偏机制（话题边界检测、重定向）
3. 证据专有问题模板

防跑偏机制：
- 话题边界系统：检测问题是否与当前证据相关
- 话题重定向：自动引导回到证据相关话题
- 回答相关性验证：确保回答与证据内容一致
"""

import json
import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class QuestionScope(Enum):
    """问题范围枚举"""
    ON_TOPIC = "on_topic"           # 话题相关
    RELATED = "related"             # 间接相关
    OFF_TOPIC = "off_topic"         # 跑偏了
    UNCLEAR = "unclear"             # 模糊不清


class AntiDeviationLevel(Enum):
    """跑偏程度"""
    NONE = 0           # 完全不跑偏
    SLIGHT = 1        # 轻微跑偏
    MODERATE = 2      # 中度跑偏
    SEVERE = 3        # 严重跑偏


@dataclass
class EvidenceQuestionContext:
    """证据问答上下文"""
    evidence_id: str
    evidence_name: str
    evidence_type: str
    evidence_content: str
    case_id: int
    case_type: str = ""
    proves_facts: List[str] = field(default_factory=list)
    credibility_score: float = 0.0

    def to_prompt_context(self) -> str:
        """
        转换为prompt上下文 - 法律应用专用：证据完整性优先

        重要原则：证据内容不得截断，必须完整传递给AI进行分析。
        """
        return f"""
【当前证据信息】
- 证据名称：{self.evidence_name}
- 证据类型：{self.evidence_type}
- 证据内容：{self.evidence_content}
- 证明事实：{', '.join(self.proves_facts) if self.proves_facts else '待分析'}
- 证据信度：{self.credibility_score:.0f}%
- 案件类型：{self.case_type}
"""


@dataclass
class TopicBoundary:
    """话题边界定义"""
    # 证据直接相关的话题
    on_topic_patterns: List[str] = field(default_factory=lambda: [
        # 证明力相关
        r"证明力",
        r"可信度",
        r"真实性",
        r"可靠性",
        r"有效",
        r"效力",
        # 证据内容相关
        r"这份.*?内容",
        r"这个.*?证据",
        r"这个.*?材料",
        r"这份.*?材料",
        r"上面.*?说",
        r"里面.*?提到",
        # 质疑相关
        r"对方.*?质疑",
        r"对方.*?攻击",
        r"对方.*?反驳",
        r"对方.*?否定",
        r"如何.*?质证",
        r"怎样.*?质证",
        r"怎么.*?质证",
        # 补强相关
        r"需要.*?补充",
        r"需要.*?补强",
        r"还缺",
        r"还需要",
        r"不足.*?地方",
        # 使用时机
        r"什么.*?时候",
        r"何时",
        r"哪个.*?阶段",
        r"怎么.*?出示",
        r"如何.*?出示",
        # 证据分析
        r"能证明",
        r"证明了",
        r"说明",
        r"意味着",
        r"能说明",
    ])

    # 间接相关的话题
    related_patterns: List[str] = field(default_factory=lambda: [
        r"案件",
        r"诉讼",
        r"官司",
        r"纠纷",
        r"事实",
        r"证据.*?总",
        r"整体.*?证据",
        r"其他.*?证据",
        r"相关.*?证据",
        r"类似.*?证据",
        r"这种情况",
        r"这类.*?问题",
        r"通常.*?会",
        r"一般.*?会",
    ])

    # 严重跑偏的话题关键词
    off_topic_keywords: List[str] = field(default_factory=lambda: [
        # 完全不相关的话题
        r"天气",
        r"今天.*?吃饭",
        r"股票",
        r"体育",
        r"娱乐",
        r"新闻",
        r"政治",
        # 与法律完全无关的问题
        r"怎么.*?追债",  # 这个还好
        r"讨债公司",
        r"黑社会",
        # 其他案件
        r"其他.*?案件",
        r"别人.*?怎么",
        r"张三.*?李四",
    ])


@dataclass
class TopicAnalysis:
    """话题分析结果"""
    scope: QuestionScope
    deviation_level: AntiDeviationLevel
    relevance_score: float           # 0-1 相关性分数
    matched_pattern: str = ""        # 匹配的模式
    reason: str = ""                # 分析理由
    redirect_suggestion: str = ""    # 重定向建议


class EvidenceQAAntiDeviation:
    """
    证据问答防跑偏系统

    使用方法：
    1. 初始化时传入证据上下文
    2. 用户提问前先调用 check_topic_boundary() 检测话题边界
    3. 如果跑偏，调用 get_redirect_prompt() 获取重定向提示
    4. 生成回答后调用 validate_answer() 验证相关性
    """

    def __init__(self, evidence_context: EvidenceQuestionContext):
        self.evidence_context = evidence_context
        self.boundary = TopicBoundary()
        self.conversation_turns = 0
        self.last_topic = ""

    def check_topic_boundary(self, question: str) -> TopicAnalysis:
        """
        检查问题是否在话题边界内

        Args:
            question: 用户问题

        Returns:
            TopicAnalysis: 话题分析结果
        """
        question_lower = question.lower()
        self.conversation_turns += 1
        self.last_topic = question

        # 检查是否严重跑偏
        for pattern in self.boundary.off_topic_keywords:
            if re.search(pattern, question_lower):
                return TopicAnalysis(
                    scope=QuestionScope.OFF_TOPIC,
                    deviation_level=AntiDeviationLevel.SEVERE,
                    relevance_score=0.0,
                    matched_pattern=pattern,
                    reason="问题与法律咨询完全无关",
                    redirect_suggestion="您好，我是一个法律AI助手，专门帮助您分析案件证据。请告诉我关于这份证据的问题，比如：这份证据的证明力如何？对方可能如何质疑？"
                )

        # 检查是否话题直接相关
        for pattern in self.boundary.on_topic_patterns:
            if re.search(pattern, question_lower):
                return TopicAnalysis(
                    scope=QuestionScope.ON_TOPIC,
                    deviation_level=AntiDeviationLevel.NONE,
                    relevance_score=0.9,
                    matched_pattern=pattern,
                    reason="问题与当前证据直接相关"
                )

        # 检查是否间接相关
        for pattern in self.boundary.related_patterns:
            if re.search(pattern, question_lower):
                return TopicAnalysis(
                    scope=QuestionScope.RELATED,
                    deviation_level=AntiDeviationLevel.SLIGHT,
                    relevance_score=0.5,
                    matched_pattern=pattern,
                    reason="问题与案件间接相关，建议聚焦于当前证据"
                )

        # 检查是否模糊不清
        unclear_patterns = [r"^$", r"^[\s]+$", r"^\?+$", r"^随便.*"]
        for pattern in unclear_patterns:
            if re.match(pattern, question.strip()):
                return TopicAnalysis(
                    scope=QuestionScope.UNCLEAR,
                    deviation_level=AntiDeviationLevel.MODERATE,
                    relevance_score=0.0,
                    reason="问题内容不清晰",
                    redirect_suggestion="您的描述不够清晰，请具体说明您想了解的问题。比如：这份证据的证明力如何？对方可能如何质疑这份证据？"
                )

        # 默认判断：如果对话轮次较多，检查是否跑偏
        if self.conversation_turns > 3:
            # 检查是否还围绕证据讨论
            if not self._is_still_about_evidence(question):
                return TopicAnalysis(
                    scope=QuestionScope.OFF_TOPIC,
                    deviation_level=AntiDeviationLevel.MODERATE,
                    relevance_score=0.3,
                    reason="对话已经偏离了当前证据主题",
                    redirect_suggestion=f"我们的对话似乎已经偏离了证据「{self.evidence_context.evidence_name}」。请问您对这个证据有什么具体问题吗？比如：\n1. 这份证据的证明力如何？\n2. 对方可能如何质疑这份证据？\n3. 我还需要什么证据来补充？"
                )

        return TopicAnalysis(
            scope=QuestionScope.UNCLEAR,
            deviation_level=AntiDeviationLevel.SLIGHT,
            relevance_score=0.4,
            reason="无法确定问题与当前证据的相关性",
            redirect_suggestion="请围绕当前证据提问，比如：这份证据的证明力如何？"
        )

    def _is_still_about_evidence(self, question: str) -> bool:
        """检查问题是否仍然围绕证据"""
        evidence_indicators = [
            "证据", "这份", "这个", "材料", "证明", "真实性",
            "可信", "效力", "证明力", "质疑", "质证", "这份证据"
        ]

        for indicator in evidence_indicators:
            if indicator in question:
                return True

        # 检查是否提到了证据名称
        if self.evidence_context.evidence_name:
            if len(self.evidence_context.evidence_name) >= 3:
                if self.evidence_context.evidence_name[:3] in question:
                    return True

        return False

    def get_constrained_system_prompt(self) -> str:
        """
        获取约束后的系统提示词

        这个提示词会告诉AI：
        1. 专注于当前证据
        2. 如何处理跑偏的问题
        3. 如何引导用户回到正题
        """
        context = self.evidence_context.to_prompt_context()

        return f"""你是一个专业的法律证据分析AI助手，专门帮助用户分析案件中的单条证据。

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

【重要原则】
1. **聚焦原则**：只讨论与当前证据相关的问题，不要主动扩展到其他话题
2. **证据为本**：所有分析都要基于证据内容，不能凭空臆测
3. **用户引导**：如果用户跑偏了，要温和但坚定地把话题引回到证据分析
4. **专业解答**：用通俗易懂的语言解释专业的证据法知识

【当前任务】
{context}

【防跑偏机制】
如果用户问的问题与当前证据无关，请这样回应：
"这个问题与当前的证据「{self.evidence_context.evidence_name}」没有直接关系。关于这份证据，您可能想了解：

1. 📊 **证明力分析**：这份证据能证明什么？证明力有多强？
2. ⚠️ **风险提示**：对方可能如何质疑这份证据？
3. 💡 **补强建议**：需要补充什么证据来增强证明力？
4. 🎯 **使用建议**：在什么时机出示这份证据效果最好？

请问您对这份证据有什么具体问题吗？"

【关于证明力的判断标准】
- 书证（合同、发票等）> 视听资料（录音录像）> 电子数据（微信截图等）
- 原件 > 复印件 > 转述
- 公证过的 > 未公证的
- 与其他证据印证的 > 孤证

请始终聚焦于帮助用户分析和理解当前证据。引用法条时必须写明具体条款内容。"""

    def validate_answer(self, question: str, answer: str) -> Dict[str, Any]:
        """
        验证回答是否与问题和证据相关

        Args:
            question: 用户问题
            answer: AI回答

        Returns:
            验证结果字典
        """
        result = {
            "is_valid": True,
            "relevance_score": 0.8,
            "issues": [],
            "warnings": []
        }

        # 检查回答长度
        if len(answer) < 20:
            result["issues"].append("回答内容过短，可能没有充分解答问题")
            result["relevance_score"] -= 0.2

        # 检查是否提到了证据
        evidence_mentioned = any([
            "这份证据" in answer,
            "该证据" in answer,
            "证据" in answer,
            self.evidence_context.evidence_name[:3] if len(self.evidence_context.evidence_name) >= 3 else "" in answer
        ])

        if not evidence_mentioned:
            result["warnings"].append("回答中未提及证据相关内容，可能跑偏了")

        # 检查是否回答了问题
        question_keywords = self._extract_keywords(question)
        answer_keywords = self._extract_keywords(answer)
        overlap = len(set(question_keywords) & set(answer_keywords))

        if overlap < len(question_keywords) * 0.3:
            result["warnings"].append("回答与问题的关键词重叠度较低，可能答非所问")
            result["relevance_score"] -= 0.3

        result["is_valid"] = result["relevance_score"] >= 0.5

        return result

    def _extract_keywords(self, text: str) -> set:
        """提取关键词"""
        # 简单实现：提取3个字以上的词
        words = re.findall(r'[\u4e00-\u9fa5]{3,}', text)
        return set(words)

    def get_topic_reminder(self) -> str:
        """获取话题提醒"""
        return f"""
【话题提醒】
当前正在讨论的证据：「{self.evidence_context.evidence_name}」
证据类型：{self.evidence_context.evidence_type}
请围绕这个证据提问或讨论。
"""


class EvidenceSpecificQAService:
    """
    单条证据智能问答服务

    核心功能：
    1. 针对单条证据的深度问答
    2. 内置防跑偏机制
    3. 证据专有问题模板
    """

    # 证据专有问题模板
    QUESTION_TEMPLATES = {
        "strength_analysis": {
            "name": "证明力分析",
            "icon": "📊",
            "questions": [
                "这份证据的证明力有多强？",
                "这个证据能证明什么？",
                "这份证据的优缺点是什么？",
                "相比其他证据，这份证据的证明力如何？"
            ]
        },
        "challenge_analysis": {
            "name": "对方质疑分析",
            "icon": "⚠️",
            "questions": [
                "对方可能如何质疑这份证据？",
                "这份证据有什么弱点可能被攻击？",
                "如何应对对方对这份证据的质疑？",
                "对方律师可能会怎么质证？"
            ]
        },
        "reinforcement_suggestion": {
            "name": "补强建议",
            "icon": "💡",
            "questions": [
                "需要什么证据来补强这份证据？",
                "这份证据还缺少什么？",
                "有没有替代这份证据的其他方案？",
                "如何让这份证据更有说服力？"
            ]
        },
        "timing_suggestion": {
            "name": "使用时机建议",
            "icon": "🎯",
            "questions": [
                "什么时机出示这份证据最好？",
                "这份证据应该在哪一阶段提交？",
                "在庭审中如何配合其他证据使用？",
                "出示这份证据时应该说些什么？"
            ]
        },
        "credibility_assessment": {
            "name": "可信度评估",
            "icon": "✅",
            "questions": [
                "这份证据的真实性和合法性如何？",
                "法院会采信这份证据吗？",
                "这份证据需要公证吗？",
                "如何确保证据效力？"
            ]
        }
    }

    def __init__(self, llm_service=None):
        self.llm = llm_service
        self.conversations: Dict[str, EvidenceQAAntiDeviation] = {}

    def get_or_create_conversation(
        self,
        conversation_id: str,
        evidence_context: EvidenceQuestionContext
    ) -> EvidenceQAAntiDeviation:
        """获取或创建对话实例"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = EvidenceQAAntiDeviation(evidence_context)
        return self.conversations[conversation_id]

    def ask(
        self,
        conversation_id: str,
        evidence_context: EvidenceQuestionContext,
        question: str
    ) -> Dict[str, Any]:
        """
        问答入口

        Args:
            conversation_id: 对话ID
            evidence_context: 证据上下文
            question: 用户问题

        Returns:
            回答结果
        """
        # 获取或创建对话
        anti_dev = self.get_or_create_conversation(conversation_id, evidence_context)

        # 检查话题边界
        topic_analysis = anti_dev.check_topic_boundary(question)

        result = {
            "conversation_id": conversation_id,
            "question": question,
            "topic_analysis": {
                "scope": topic_analysis.scope.value,
                "relevance_score": topic_analysis.relevance_score,
                "reason": topic_analysis.reason
            },
            "needs_redirect": topic_analysis.scope in [QuestionScope.OFF_TOPIC, QuestionScope.UNCLEAR],
            "redirect_suggestion": topic_analysis.redirect_suggestion if topic_analysis.scope in [QuestionScope.OFF_TOPIC, QuestionScope.UNCLEAR] else ""
        }

        # 如果严重跑偏，返回重定向提示
        if topic_analysis.scope == QuestionScope.OFF_TOPIC:
            result["status"] = "redirect"
            result["answer"] = topic_analysis.redirect_suggestion
            result["type"] = "redirect"
            return result

        # 如果模糊，尝试解析意图
        if topic_analysis.scope == QuestionScope.UNCLEAR:
            result["status"] = "clarification"
            result["answer"] = topic_analysis.redirect_suggestion
            result["type"] = "clarification"
            result["suggested_questions"] = self._get_suggested_questions(evidence_context.evidence_type)
            return result

        # 生成回答
        answer = self._generate_answer(conversation_id, evidence_context, question, anti_dev)

        # 验证回答
        validation = anti_dev.validate_answer(question, answer)
        result["validation"] = validation
        result["answer"] = answer
        result["status"] = "success" if validation["is_valid"] else "warning"
        result["type"] = "direct_answer"

        # 添加证据上下文摘要
        result["evidence_summary"] = {
            "name": evidence_context.evidence_name,
            "type": evidence_context.evidence_type,
            "credibility": evidence_context.credibility_score
        }

        return result

    def _generate_answer(
        self,
        conversation_id: str,
        evidence_context: EvidenceQuestionContext,
        question: str,
        anti_dev: EvidenceQAAntiDeviation
    ) -> str:
        """生成回答"""
        if not self.llm:
            return self._generate_simple_answer(evidence_context, question)

        # 构建提示词
        system_prompt = anti_dev.get_constrained_system_prompt()

        user_prompt = f"""
【用户问题】
{question}

【回答要求】
1. 回答要聚焦于证据「{evidence_context.evidence_name}」
2. 如果问题不明确，可以先确认用户想问什么
3. 回答要专业但易懂
4. 如果涉及法律风险，要如实告知
"""

        try:
            response = self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])

            return response.strip()

        except Exception as e:
            return self._generate_simple_answer(evidence_context, question)

    def _generate_simple_answer(
        self,
        evidence_context: EvidenceQuestionContext,
        question: str
    ) -> str:
        """生成简单回答（无LLM时使用）"""
        question_lower = question.lower()

        # 证明力相关
        if any(kw in question_lower for kw in ["证明力", "可信度", "有效性", "能证明"]):
            strength = self._assess_strength_simple(evidence_context)
            return f"""【{evidence_context.evidence_name}】的证明力分析：

📊 **证明力评估**：{strength['level']}
- 证据类型：{evidence_context.evidence_type}
- 信度评分：{evidence_context.credibility_score:.0f}%

💡 **分析说明**：
{strength['analysis']}

📋 **证明事实**：
{chr(10).join([f"- {f}" for f in evidence_context.proves_facts]) if evidence_context.proves_facts else "- 待分析"}"""

        # 质疑相关
        if any(kw in question_lower for kw in ["质疑", "攻击", "反驳", "弱点", "质证"]):
            challenges = self._get_common_challenges(evidence_context)
            return f"""【{evidence_context.evidence_name}】的潜在质疑点：

⚠️ **常见质疑方向**：
{chr(10).join([f"- {c}" for c in challenges])}

💡 **应对建议**：
1. 准备好证据原件供法庭核实
2. 如有其他证据印证，准备好证据链
3. 必要时申请鉴定或公证"""

        # 补强相关
        if any(kw in question_lower for kw in ["补强", "补充", "还需要", "不足"]):
            suggestions = self._get_reinforcement_suggestions(evidence_context)
            return f"""【{evidence_context.evidence_name}】的补强建议：

💡 **建议补充的证据**：
{chr(10).join([f"- {s}" for s in suggestions])}"""

        # 默认回答
        return f"""关于证据「{evidence_context.evidence_name}」，您可能想了解：

📊 **证明力分析**：这份证据的证明力有多强？
⚠️ **对方质疑分析**：对方可能如何质疑？
💡 **补强建议**：需要补充什么证据？
🎯 **使用时机**：什么时机出示最好？

请具体说明您想了解的问题。"""

    def _assess_strength_simple(self, evidence_context: EvidenceQuestionContext) -> Dict:
        """简单评估证明力"""
        type_strength_map = {
            "CONTRACT": {"level": "强", "analysis": "合同类证据属于书证，证明力较强。"},
            "PAYMENT": {"level": "强", "analysis": "支付凭证有银行等第三方背书，证明力较强。"},
            "DOCUMENT": {"level": "中强", "analysis": "书证证明力较强，需要确认原件。"},
            "AUDIO_VIDEO": {"level": "中", "analysis": "视听资料需要确认真实性，建议公证。"},
            "CORRESPONDENCE": {"level": "中", "analysis": "函件沟通类证据需要确认发送和接收。"},
            "TESTIMONY": {"level": "弱", "analysis": "证人证言主观性较强，证明力相对较弱。"},
            "EXPERT": {"level": "强", "analysis": "鉴定意见有专业机构背书，证明力强。"},
            "OTHER": {"level": "中", "analysis": "需要根据具体内容评估证明力。"}
        }

        return type_strength_map.get(
            evidence_context.evidence_type,
            {"level": "中", "analysis": "需要根据具体情况评估。"}
        )

    def _get_common_challenges(self, evidence_context: EvidenceQuestionContext) -> List[str]:
        """获取常见质疑方向"""
        challenges = []

        if evidence_context.evidence_type == "AUDIO_VIDEO":
            challenges.append("录音/录像的真实性：是否经过剪辑？")
            challenges.append("取得方式是否合法：是否侵犯隐私？")
        elif evidence_context.evidence_type == "CORRESPONDENCE":
            challenges.append("聊天记录的真实性：是否可以证明是本人操作？")
            challenges.append("聊天记录的完整性：是否有所删减？")
        elif evidence_context.evidence_type == "CONTRACT":
            challenges.append("合同是否已经履行完毕？")
            challenges.append("是否存在补充协议或口头变更？")
        elif evidence_context.evidence_type == "PAYMENT":
            challenges.append("转账凭证与本案的关联性")
            challenges.append("是否存在其他款项往来？")

        challenges.append("证据原件是否能提供？")

        return challenges

    def _get_reinforcement_suggestions(self, evidence_context: EvidenceQuestionContext) -> List[str]:
        """获取补强建议"""
        suggestions = []

        if evidence_context.evidence_type == "AUDIO_VIDEO":
            suggestions.append("公证处公证确认真实性")
            suggestions.append("鉴定机构出具真实性鉴定意见")
            suggestions.append("配合其他书面证据使用")
        elif evidence_context.evidence_type == "CORRESPONDENCE":
            suggestions.append("公证处对电子数据证据进行公证")
            suggestions.append("申请法院向平台调取原始数据")
            suggestions.append("配合通话录音或视频印证")
        elif evidence_context.evidence_type == "CONTRACT":
            suggestions.append("履行证据（送货单、验收单等）")
            suggestions.append("付款凭证印证合同已履行")
            suggestions.append("沟通记录证明合同变更（如有）")
        elif evidence_context.evidence_type == "TESTIMONY":
            suggestions.append("寻找更多知情人作证")
            suggestions.append("收集书面证据印证证人陈述")
            suggestions.append("申请专家证人辅助说明")

        return suggestions if suggestions else ["根据证据类型补充相关证据"]

    def _get_suggested_questions(self, evidence_type: str) -> List[Dict]:
        """获取建议问题"""
        suggested = []

        for key, template in self.QUESTION_TEMPLATES.items():
            for q in template["questions"][:1]:  # 每个类型取一个问题
                suggested.append({
                    "icon": template["icon"],
                    "question": q,
                    "category": template["name"]
                })

        return suggested[:5]

    def get_question_templates(self) -> Dict:
        """获取问题模板"""
        return self.QUESTION_TEMPLATES

    def clear_conversation(self, conversation_id: str) -> bool:
        """清除对话"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False


# 全局实例
evidence_qa_service = EvidenceSpecificQAService()
