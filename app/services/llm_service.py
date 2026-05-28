"""
通义千问 LLM 服务
支持通义千问系列模型调用

Prompt 模板已提取至 app.services.legal_prompts，以减少主文件体积。
"""
import os
import time
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime
from dashscope import Generation
import dashscope
from app.config import settings
from app.services.legal_prompts import (
    LEGAL_ANALYSIS_PROMPT,
    STRATEGY_SUGGESTION_PROMPT,
    DOCUMENT_GENERATION_TEMPLATES,
    OPPONENT_ANALYSIS_PROMPT,
    EVIDENCE_ATTACK_DEFENSE_PROMPT,
    SCENARIO_PREDICTION_PROMPT,
    ACTION_PLAN_PHASE_PROMPTS,
    AUTOMATED_ACTION_PLAN_PROMPT,
    EVIDENCE_ANALYSIS_RULE,
    ADVERSARIAL_SYSTEM_OPPONENT,
    ADVERSARIAL_SYSTEM_OUR_SIDE,
    ADVERSARIAL_SYSTEM_SYNTHESIZER,
    ADVERSARIAL_SYNTHESIS_PROMPT,
    JUDGE_PERSPECTIVE_PROMPT,
    OPPONENT_ATTACK_PROMPT,
    get_phase_action_plan_prompt,
    get_document_generation_prompt,
)


class LLMService:
    """通义千问 LLM 服务"""

    MAX_CHAT_RETRIES = 3

    def __init__(self):
        self.api_key = settings.get_api_key()
        if self.api_key:
            dashscope.api_key = self.api_key
            self._configured = True
        else:
            self._configured = False

        # 模型配置（支持 Qwen3.5 系列，2026年3月最新）
        # 官方 API 模型参考: https://help.aliyun.com/zh/dashscope/
        self.models = {
            # Qwen3.5 系列 (2026年3月最新)
            "qwen3.5-max": {
                "model": "qwen3.5-max",
                "max_tokens": 32768,
                "temperature": 0.7,
                "description": "Qwen3.5 旗舰版，最强推理能力"
            },
            "qwen3.5-plus": {
                "model": "qwen3.5-plus",
                "max_tokens": 32768,
                "temperature": 0.7,
                "description": "Qwen3.5 增强版，高性价比"
            },
            "qwen3.5-turbo": {
                "model": "qwen3.5-turbo",
                "max_tokens": 32768,
                "temperature": 0.7,
                "description": "Qwen3.5 快速版，低延迟"
            },
            # Qwen-Max 系列（稳定版）
            "qwen-max": {
                "model": "qwen-max",
                "max_tokens": 16384,
                "temperature": 0.7,
                "description": "通义千问旗舰版"
            },
            "qwen-plus": {
                "model": "qwen-plus",
                "max_tokens": 16384,
                "temperature": 0.7,
                "description": "通义千问增强版"
            },
            "qwen-turbo": {
                "model": "qwen-turbo",
                "max_tokens": 16384,
                "temperature": 0.7,
                "description": "通义千问快速版"
            },
            # 法律分析专用模型
            "qwen-plus-legal": {
                "model": "qwen-plus",
                "max_tokens": 16384,
                "temperature": 0.3,
                "description": "法律分析专用，低温度确保准确性"
            },
            "qwen3.5-plus-legal": {
                "model": "qwen3.5-plus",
                "max_tokens": 32768,
                "temperature": 0.3,
                "description": "Qwen3.5 法律分析专用"
            }
        }
        self.default_model = "qwen3.5-plus"  # 升级默认模型为 Qwen3.5-Plus

    def is_configured(self) -> bool:
        """检查是否已配置 API Key"""
        return getattr(self, '_configured', False)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen-max",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        发送对话请求（无 token 限制，一切以真实、全面、完善为准则）

        Args:
            messages: 对话消息列表 [{"role": "user/assistant/system", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数（None = 模型最大限制）
            stream: 是否流式输出

        Returns:
            生成的文本内容
        """
        if not self.is_configured():
            return "错误：请先配置通义千问 API Key"

        model_config = self.models.get(model, self.models[self.default_model])

        params = {
            "model": model_config["model"],
            "messages": messages,
        }

        if temperature is not None:
            params["temperature"] = temperature
        else:
            params["temperature"] = model_config["temperature"]

        # 不设置 max_tokens 限制，让模型尽可能全面回答
        if max_tokens:
            params["max_tokens"] = max_tokens

        if stream:
            params["stream"] = True

        for attempt in range(self.MAX_CHAT_RETRIES):
            try:
                response = Generation.call(**params, timeout=120)
            except Exception as e:
                print(
                    f"[LLM] Unexpected error on attempt {attempt + 1}/{self.MAX_CHAT_RETRIES}: "
                    f"{type(e).__name__}: {e}"
                )
                if attempt < self.MAX_CHAT_RETRIES - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                return "请求出错，请稍后重试"

            if response.status_code == 200:
                # 检查响应结构
                if hasattr(response, 'output') and response.output:
                    if hasattr(response.output, 'choices') and response.output.choices:
                        result = response.output.choices[0].message.content
                    elif hasattr(response.output, 'text'):
                        result = response.output.text
                    else:
                        result = ""
                elif hasattr(response, 'content'):
                    result = response.content
                else:
                    result = ""
                
                print(f"[DEBUG] LLM返回长度: {len(result) if result else 0} 字符")
                return result if result else "AI 返回了空响应，请稍后重试"
            else:
                # 不对外暴露 DashScope 内部错误码和消息
                error_msg = response.message if hasattr(response, 'message') else "未知错误"
                print(
                    f"[LLM] API error on attempt {attempt + 1}/{self.MAX_CHAT_RETRIES}: "
                    f"code={response.code}, msg={error_msg}"
                )
                if attempt < self.MAX_CHAT_RETRIES - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                return "AI 服务暂时不可用，请稍后重试"

        return "请求出错，请稍后重试"

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen-max"
    ) -> Generator[str, None, None]:
        """流式对话"""
        if not self.is_configured():
            yield "错误：请先配置通义千问 API Key"
            return

        model_config = self.models.get(model, self.models[self.default_model])

        params = {
            "model": model_config["model"],
            "messages": messages,
            "temperature": model_config["temperature"],
            "max_tokens": model_config["max_tokens"],
            "stream": True
        }

        try:
            responses = Generation.call(**params)
            for resp in responses:
                if resp.status_code == 200:
                    if hasattr(resp, 'output') and resp.output:
                        if hasattr(resp.output, 'choices') and resp.output.choices:
                            content = resp.output.choices[0].message.content
                        elif hasattr(resp.output, 'text'):
                            content = resp.output.text
                        else:
                            content = ""
                    elif hasattr(resp, 'output') and resp.output is None:
                        continue
                    else:
                        content = getattr(resp, 'content', "")

                    if content:
                        yield content
                else:
                    # 不暴露内部错误码
                    print(f"[LLM Stream] API error: code={resp.code}")
                    yield "\n\nAI 服务暂时不可用，请稍后重试"
                    break
        except Exception as e:
            print(f"[LLM Stream] Unexpected error: {type(e).__name__}: {e}")
            yield "\n\n请求出错，请稍后重试"

    def legal_analysis(
        self,
        question: str,
        context: str = "",
        case_info: str = ""
    ) -> str:
        """
        法律分析 - 深入、细致、全面的分析

        Args:
            question: 用户问题
            context: 上下文（知识库检索结果）
            case_info: 案件基本信息

        Returns:
            分析结果
        """
        # 使用 qwen-turbo 加快响应速度
        system_prompt = LEGAL_ANALYSIS_PROMPT

        user_content = ""
        if case_info:
            user_content += f"【案件基本信息】\n{case_info}\n\n"
        if context:
            user_content += f"【相关材料】\n{context}\n\n"
        user_content += f"【分析要求】\n{question}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def strategy_suggestion(
        self,
        case_info: str,
        current_status: str,
        recent_development: str = ""
    ) -> str:
        """
        策略建议 - 深度、全面、可执行

        Args:
            case_info: 案件信息
            current_status: 当前状态
            recent_development: 最新进展

        Returns:
            策略建议
        """
        user_content = f"【案件信息】\n{case_info}\n\n"
        user_content += f"【当前状态】\n{current_status}\n\n"
        if recent_development:
            user_content += f"【案件分析】\n{recent_development}"

        messages = [
            {"role": "system", "content": STRATEGY_SUGGESTION_PROMPT},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def analyze_case(
        self,
        case_info: dict,
        user_message: str,
        chat_history: List[dict],
        evidence_summary: List[dict],
    ) -> dict:
        """
        分析案情，识别诉讼请求
        
        Args:
            case_info: 案件基本信息
            user_message: 用户当前消息
            chat_history: 对话历史
            evidence_summary: 证据摘要列表
        
        Returns:
            分析结果 {
                "analysis_type": "case_analysis" | "document_request" | "general",
                "response": "AI 响应",
                "suggested_claims": [{"title", "description", "claim_type", "amount", "priority"}],
                "document_type": "起诉状" | ...（如果用户请求生成文书）
            }
        """
        def ensure_case_anchor(response: str) -> str:
            content = (response or "").strip()
            title = case_info.get('title') or "当前案件"
            plaintiff = case_info.get('plaintiff') or "未填写"
            defendant = case_info.get('defendant') or "未填写"
            anchors = []

            if str(evidence_count) not in content:
                anchors.append(f"本次分析以系统记录的共 {evidence_count} 条证据为边界，不应改写为其他数量。")
            if title and title not in content:
                anchors.append(f"案件名称：{title}。")
            if plaintiff and plaintiff not in content:
                anchors.append(f"我方/原告主体：{plaintiff}。")
            if defendant and defendant not in content:
                anchors.append(f"相对方/被告主体：{defendant}。")
            if not any(signal in content for signal in ("民法典", "公司法", "民事诉讼法", "举证责任")):
                anchors.append("法律依据方向：围绕《民法典》合同编及不当得利规则、《公司法》股东出资和公司治理规则、《民事诉讼法》及证据规则下的举证责任组织论证，具体条款需另行核验。")

            if not anchors:
                return content
            return "【案件基准校准】\n" + "\n".join(anchors) + "\n\n" + content

        CASE_ANALYSIS_PROMPT = """
你是资深诉讼律师，正在与当事人进行案件咨询对话。

【案件背景】
案件名称：{case_title}
案件类型：{case_type}
原告：{plaintiff}
被告：{defendant}
案由：{cause}
诉讼金额：{claim_amount}
案件描述：{description}

【已有证据】
系统记录证据总数：{evidence_count} 条。不得改写为其他数量。
{evidence_list}

【对话历史】
{chat_history}

【用户最新消息】
{user_message}

【你的任务】
1. 理解用户描述的案情和诉求
2. 识别用户可能的诉讼请求（可以多个）
3. 判断用户是否在要求生成文书
4. 给出可供律师校准的初步实体分析，而不是只做意图识别

【硬性约束】
1. response 不得少于 900 个中文字符，必须覆盖用户问题中的每一类主张。
2. 必须引用证据编号或证据名称，说明哪些主张有证据、哪些仍有缺口。
3. 当前上下文没有权威类案检索结果，禁止输出具体法院案号、指导案例编号或虚构判例；如需类案，只能写“需另行检索核验”。
4. 不得将用户上传材料中的法律意见、草稿或未核验案号当作已核验裁判依据。
5. 法律评价要区分“可主张”“证据较强”“需补证”“风险较高”，不得直接写成必胜或必然犯罪。
6. response 必须包含法律依据方向，至少覆盖《民法典》《公司法》《民事诉讼法》中与本案相关的规则；当前接口未接入权威法条数据库时，不得输出具体条号，写“条款需核验”。
7. 刑事责任只能作为可能风险线索和另行核验方向，不能直接认定任何主体构成犯罪。

【输出格式】
请以JSON格式输出：
```json
{{
    "analysis_type": "case_analysis" | "document_request" | "general",
    "response": "你对用户的回复（不少于900字，专业、具体、逐项回应）",
    "suggested_claims": [
        {{
            "title": "战役名称（如：主张欠款本金）",
            "description": "战役描述",
            "claim_type": "欠款/违约金/赔偿/其他",
            "amount": "涉及金额",
            "priority": 1-5
        }}
    ],
    "document_type": "起诉状"（如果用户明确要求生成文书）
}}
```
"""

        evidence_count = len(evidence_summary)
        evidence_text = "\n".join([
            f"- 证据{i}: {e['name']} ({e['type']}) - {e['summary'][:180]}"
            for i, e in enumerate(evidence_summary, 1)
        ]) or "暂无证据"

        chat_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else '律师'}: {m['content'][:200]}"
            for m in chat_history[-5:]
        ]) or "（首次对话）"

        user_content = f"""【案件背景】
案件名称：{case_info.get('title', '')}
案件类型：{case_info.get('case_type', '')}
原告：{case_info.get('plaintiff', '')}
被告：{case_info.get('defendant', '')}
案由：{case_info.get('cause', '')}
诉讼金额：{case_info.get('claim_amount', '未明确')}
案件描述：{case_info.get('description', '')[:500]}

【已有证据】
系统记录证据总数：{evidence_count} 条。不得改写为其他数量。
{evidence_text}

【对话历史】
{chat_text}

【用户最新消息】
{user_message}

请分析并给出回复。response 字段必须不少于 900 个中文字符，逐项回应合作出资、停业责任、工资社保、保证金、信息服务费等主张；必须明确写出“系统记录证据总数：{evidence_count} 条”；必须列明法律依据方向；当前未接入权威法条数据库，不得输出具体条号；不得编造未核验法院案号或判例，不得直接作刑事定罪式表述。"""

        messages = [
            {"role": "system", "content": CASE_ANALYSIS_PROMPT},
            {"role": "user", "content": user_content}
        ]

        result = self.chat(messages, model="qwen-plus")

        # 解析 JSON
        try:
            import json
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                parsed = json.loads(result)
            parsed["response"] = ensure_case_anchor(parsed.get("response", ""))
            return parsed
        except (json.JSONDecodeError, AttributeError):
            return {
                "analysis_type": "general",
                "response": ensure_case_anchor(result),
                "suggested_claims": [],
            }

    def generate_document(
        self,
        document_type: str,
        case_info: str,
        specific_requirements: str = ""
    ) -> str:
        """
        生成法律文书

        Args:
            document_type: 文书类型（起诉状/答辩状等）
            case_info: 案件信息
            specific_requirements: 特殊要求

        Returns:
            生成的文书内容
        """
        system_prompt = get_document_generation_prompt(document_type)

        user_content = f"【案件信息】\n{case_info}\n\n"
        if specific_requirements:
            user_content += f"【特殊要求】\n{specific_requirements}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def plan_claim(
        self,
        case_info: dict,
        claim_info: dict,
        evidence_list: List[dict],
    ) -> dict:
        """
        AI 规划战役 - 分析需要哪些文书和证据
        
        Args:
            case_info: 案件信息 {"id", "title", "case_type", "plaintiff", "defendant", "cause", "claim_amount"}
            claim_info: 战役信息 {"title", "description", "claim_type", "amount"}
            evidence_list: 证据列表 [{"id", "name", "type", "summary"}, ...]
        
        Returns:
            规划结果 {
                "suggested_documents": ["起诉状", "代理词"],
                "suggested_evidence_ids": ["ev_id_1", "ev_id_2"],
                "evidence_analysis": [...],
                "analysis": "分析详情",
                "risk_level": "low/medium/high",
                "risk_notes": "风险说明",
            }
        """
        CLAIM_PLANNING_PROMPT = """
你是资深诉讼律师，正在为当事人规划一场战役（诉讼请求）。

【案件背景】
案件名称：{case_title}
案件类型：{case_type}
原告：{plaintiff}
被告：{defendant}
案由：{cause}
诉讼金额：{claim_amount}

【战役目标】
战役名称：{claim_title}
战役描述：{claim_description}
诉求类型：{claim_type}
涉及金额：{claim_amount}

【可用证据】
{evidence_list}

【你的任务】
1. 分析案件证据与战役目标的关联性
2. 推荐适合此战役的文书类型
3. 识别关键证据（直接支持战役主张的证据）
4. 评估诉讼风险等级
5. 给出战役规划建议

【输出格式】
请以JSON格式输出：
```json
{
    "suggested_documents": ["文书类型1", "文书类型2"],
    "suggested_evidence_ids": ["证据ID1", "证据ID2"],
    "evidence_analysis": [{"id": "证据ID", "reason": "关联理由"}],
    "analysis": "详细分析说明",
    "risk_level": "low/medium/high",
    "risk_notes": "风险说明"
}
```

注意：
- 只推荐与战役直接相关的证据
- 文书类型使用标准法律文书名称
- 风险评估要客观
"""

        evidence_text = "\n".join([
            f"- 证据{i}: {e['name']} (ID: {e['id']}, 类型: {e['type']}) - {e.get('summary', '无摘要')[:100]}"
            for i, e in enumerate(evidence_list, 1)
        ])

        user_content = f"""【案件背景】
案件名称：{case_info.get('title', '')}
案件类型：{case_info.get('case_type', '')}
原告：{case_info.get('plaintiff', '')}
被告：{case_info.get('defendant', '')}
案由：{case_info.get('cause', '')}
诉讼金额：{case_info.get('claim_amount', '')}

【战役目标】
战役名称：{claim_info.get('title', '')}
战役描述：{claim_info.get('description', '')}
诉求类型：{claim_info.get('claim_type', '')}
涉及金额：{claim_info.get('amount', '')}

【可用证据】
{evidence_text if evidence_text else '（暂无证据）'}

请分析并给出战役规划建议。"""

        messages = [
            {"role": "system", "content": CLAIM_PLANNING_PROMPT},
            {"role": "user", "content": user_content}
        ]

        result = self.chat(messages, model="qwen-plus")
        
        # 尝试解析 JSON
        try:
            import json
            import re
            
            # 查找 JSON 块
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result)
            if json_match:
                return json.loads(json_match.group(1))
            
            # 尝试直接解析
            return json.loads(result)
        except (json.JSONDecodeError, AttributeError):
            # 如果无法解析 JSON，返回文本分析结果
            return {
                "suggested_documents": [],
                "suggested_evidence_ids": [],
                "evidence_analysis": [],
                "analysis": result,
                "risk_level": "medium",
                "risk_notes": "AI 返回了文本分析，请查看分析结果后手动配置",
            }

    # ============ 对抗性分析相关方法 ============

    def opponent_analysis(
        self,
        case_info: str,
        opponent_info: str = ""
    ) -> str:
        """
        对手视角分析 - 站在对方角度思考

        Args:
            case_info: 案件信息
            opponent_info: 对方当事人信息

        Returns:
            对手视角分析结果
        """
        system_prompt = OPPONENT_ANALYSIS_PROMPT

        user_content = f"【案件基本信息】\n{case_info}\n\n"
        if opponent_info:
            user_content += f"【已知对手信息】\n{opponent_info}\n\n"
        user_content += "请进行深入的对手视角分析。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def evidence_attack_defense_matrix(
        self,
        case_info: str,
        our_evidence: str = "",
        opponent_evidence: str = "",
        opponent_strategies: str = ""
    ) -> str:
        """
        证据攻防矩阵分析 - 全面分析证据的攻守价值

        Args:
            case_info: 案件信息
            our_evidence: 我方现有证据
            opponent_evidence: 对方可能证据
            opponent_strategies: 对方可能的策略

        Returns:
            证据攻防矩阵分析结果
        """
        system_prompt = EVIDENCE_ATTACK_DEFENSE_PROMPT

        user_content = f"【案件基本信息】\n{case_info}\n\n"
        if our_evidence:
            user_content += f"【我方现有证据】\n{our_evidence}\n\n"
        if opponent_evidence:
            user_content += f"【对方可能的证据】\n{opponent_evidence}\n\n"
        if opponent_strategies:
            user_content += f"【对方可能的策略】\n{opponent_strategies}\n\n"
        user_content += "请进行全面的证据攻防矩阵分析。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def scenario_prediction(
        self,
        case_info: str,
        evidence_matrix: str = "",
        opponent_analysis: str = ""
    ) -> str:
        """
        案件走向预测 - 模拟不同证据组合下的可能结果

        Args:
            case_info: 案件信息
            evidence_matrix: 证据攻防矩阵
            opponent_analysis: 对手分析

        Returns:
            情景预测分析结果
        """
        system_prompt = SCENARIO_PREDICTION_PROMPT

        user_content = f"【案件基本信息】\n{case_info}\n\n"
        if evidence_matrix:
            user_content += f"【证据攻防矩阵】\n{evidence_matrix}\n\n"
        if opponent_analysis:
            user_content += f"【对手分析】\n{opponent_analysis}\n\n"
        user_content += "请进行案件走向预测分析。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def automated_action_plan(
        self,
        case_info: str,
        current_phase: str,
        scenario_prediction: str = "",
        evidence_matrix: str = ""
    ) -> str:
        """
        自动化行动方案生成 - 根据案件阶段自动生成任务清单

        Args:
            case_info: 案件信息
            current_phase: 当前阶段
            scenario_prediction: 情景预测
            evidence_matrix: 证据攻防矩阵

        Returns:
            自动化行动方案
        """
        system_prompt = get_phase_action_plan_prompt(current_phase)

        user_content = f"【案件基本信息】\n{case_info}\n\n"
        if scenario_prediction:
            user_content += f"【案件走向预测】\n{scenario_prediction}\n\n"
        if evidence_matrix:
            user_content += f"【证据分析】\n{evidence_matrix}\n\n"
        user_content += f"【当前阶段】{current_phase}\n\n请生成自动化的行动方案。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def full_adversarial_analysis(
        self,
        case_info: str,
        our_evidence: str = "",
        opponent_evidence: str = "",
        current_phase: str = "negotiation",
        max_rounds: int = 3,
        progress_callback=None
    ) -> str:
        """
        完整对抗性分析 - 多轮沙盘推演系统

        核心设计：
        1. 控辩换位思考 - 扮演对手和己方轮番论证
        2. 多轮推演 - 直到对方无牌可打
        3. 完整记录每轮攻防
        4. 最后综合成抗辩手册

        Args:
            case_info: 案件信息
            our_evidence: 我方证据
            opponent_evidence: 对方可能证据
            current_phase: 当前阶段
            max_rounds: 最大推演轮数
            progress_callback: 进度回调函数，接收 (stage_name, progress_percent) 参数

        Returns:
            完整的对抗性分析报告（沙盘推演手册）
        """
        import datetime as dt

        # 注意：不进行截断，保留全部案件信息以确保分析完整性
        def update_progress(stage: str, progress: float):
            if progress_callback:
                try:
                    progress_callback(stage, progress)
                except Exception:
                    pass  # 不因回调错误中断分析

        # ============ 系统设定 ============
        # 重要提示：必须基于完整证据内容进行分析，不能仅凭摘要或标题
        EVIDENCE_ANALYSIS_RULE = """⚠️ 关键规则：分析必须基于【完整证据原文】，禁止以下行为：
1. 仅凭证据名称（"投资协议"、"公司章程"）推测内容
2. 仅分析前几页或摘要，对具体条款全文视而不见
3. 在证据原文未提供时假设条款存在（"假设协议约定..."）
4. 对大篇幅文档只引用标题或首段，忽视全文关键条款
5. 要求用户"补全证据"来替代对已有证据的深度分析

✅ 正确做法：
1. 仔细阅读证据全文的每一个条款
2. 对合同/协议，逐条分析具体约定的权利义务
3. 对财务凭证，逐项核对金额、日期、收付款方
4. 证据内容不完整时，明确标注"原文未提及此条款，请核实"
5. 对未提供的证据才提出"补全"要求"""

        system_opponent = f"""{EVIDENCE_ANALYSIS_RULE}

你是一位经验丰富的诉讼对手律师，拥有以下特点：
- 精通对方的弱点，善于寻找法律漏洞
- 擅长证据突袭和程序性攻击
- 善于利用情感和舆论压力
- 目标：最大化己方利益，击败对手

当前任务：作为对手方，全面分析这个案件，制定攻击策略。
请用中文详细列出所有可能的攻击角度和策略。"""

        system_our_side = f"""{EVIDENCE_ANALYSIS_RULE}

你是一位经验丰富的诉讼代理律师（我方），拥有以下特点：
- 精通法律条文和司法实践
- 善于防守和反击
- 擅长证据运用和论证逻辑
- 会预判对手下一步
- 目标：守住底线，保护当事人利益

当前任务：针对对手的攻击，制定防守和反击策略。"""

        system_synthesizer = """你是一位顶级法律战略专家，需要将多轮辩论综合成一份实战手册。
手册应该：
1. 列出所有关键战斗点
2. 每一点的攻防记录
3. 最终的胜负判断
4. 我方必胜的关键要点
5. 需要立即行动的提醒事项"""

        # ============ 第一轮：对手全面进攻 ============
        update_progress("对手进攻分析", 0.1)
        
        round_1_prompt = f"""{system_opponent}

【案件背景】
{case_info}

【我方证据】（你要攻击的重点）
{our_evidence or '暂无提供'}

【你方证据】（你手中的武器）
{opponent_evidence or '暂无提供'}

【当前阶段】
{current_phase}

请以对手律师的身份，全面列出你的攻击策略：

# 第一轮：对手全面进攻

## 1.1 核心攻击点（3-5个）
对每个攻击点，说明：
- **攻击角度**：从哪个角度切入
- **法律依据**：援引哪些法条
- **证据支持**：用什么证据支撑
- **预期效果**：能达到什么目的

## 1.2 程序性攻击
- [ ] 管辖权异议
- [ ] 当事人资格异议
- [ ] 诉讼时效抗辩
- [ ] 回避申请
- [ ] 其他程序问题

## 1.3 证据攻击
对每份关键证据，列出质疑角度和削弱策略

## 1.4 情感/舆论攻击
## 1.5 谈判策略"""

        round_1_result = self.chat([{"role": "user", "content": round_1_prompt}], model="qwen-plus")
        update_progress("对手进攻分析完成", 0.2)
        
        if not round_1_result:
            return "推演失败：对手进攻阶段无响应"

        debate_record = f"""# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#              诉讼对抗性分析 - 多轮沙盘推演
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

**案件阶段**：{current_phase}
**推演轮数**：{max_rounds}轮
**生成时间**：{dt.datetime.now().strftime('%Y-%m-%d %H:%M')}

---

# 第一轮：对手全面进攻

{round_1_result}

"""

        # ============ 第二轮：我方防守反击 ============
        update_progress("我方防守策略分析", 0.25)
        
        round_2_prompt = f"""{system_our_side}

【案件背景】
{case_info}

【我方证据】
{our_evidence or '暂无提供'}

【对手刚刚发动了以下攻击】
{round_1_result}

请逐一反驳对手的攻击：

# 第二轮：我方防守反击

## 2.1 针对核心攻击点的反驳
## 2.2 程序性防御
## 2.3 证据加固
## 2.4 反将一军（2-3个反守为攻的策略）
## 2.5 我方证据攻势"""

        round_2_result = self.chat([{"role": "user", "content": round_2_prompt}], model="qwen-plus")
        update_progress("我方防守策略分析完成", 0.35)
        
        if round_2_result:
            debate_record += f"""
---

# 第二轮：我方防守反击

{round_2_result}

"""

        # ============ 第三轮及以后：多轮博弈 ============
        current_attack = round_2_result if round_2_result else ""

        for round_num in range(3, max_rounds + 1):
            update_progress(f"第{round_num}轮对抗推演", 0.35 + (round_num - 3) * 0.15)
            
            # 对手的回应/反扑
            opponent_response_prompt = f"""{system_opponent}

【你之前发动的攻击摘要】
{round_1_result}

【对方刚刚的反驳】
{current_attack}

面对对方的反驳，你需要：
1. 承认合理的反驳点
2. 坚守核心攻击点
3. 寻找新的攻击角度
4. 提出更有力的证据

# 第{round_num}轮：对手反扑

## {round_num}.1 针对反驳的回应
## {round_num}.2 调整后的攻击策略
## {round_num}.3 新的攻击点（2-3个）
## {round_num}.4 终极杀招"""

            opponent_response = self.chat([{"role": "user", "content": opponent_response_prompt}], model="qwen-plus")
            if not opponent_response or len(opponent_response) < 100:
                debate_record += f"\n**第{round_num}轮：对手已无牌可打**\n"
                break

            debate_record += f"""
---

# 第{round_num}轮：对手反扑

{opponent_response}

"""

            # 我方的回应
            our_response_prompt = f"""{system_our_side}

【案件背景】
{case_info}

【我方证据】
{our_evidence or '暂无提供'}

【对手最新攻击】
{opponent_response}

# 第{round_num}轮：我方应对

## {round_num}.1 逐条反驳
## {round_num}.2 我方攻势
## {round_num}.3 局势评估"""

            our_response = self.chat([{"role": "user", "content": our_response_prompt}], model="qwen-plus")
            if our_response:
                debate_record += f"""
## {round_num}.2 我方回应

{our_response}

"""
                current_attack = our_response
            else:
                break

        # ============ 综合成最终手册 ============
        update_progress("生成综合分析报告", 0.8)
        synthesis_prompt = f"""{system_synthesizer}

【案件背景】
{case_info}

【完整辩论记录】
{debate_record}

请将上述多轮辩论综合成一份实战抗辩手册：

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#                    诉讼抗辩实战手册
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

## 一、核心战斗点（必争之地）

列出3-5个最关键的争议点，每点包含：争议焦点、我方立场、对方可能攻击、我方应对方案、胜负预判。

## 二、证据攻防地图

| 我方证据 | 对方攻击 | 我方应对 | 法院采信度 |
|---------|---------|---------|-----------|
|         |         |         |           |

| 对方证据 | 我方攻击 | 反驳策略 | 证明力评估 |
|---------|---------|---------|-----------|
|         |         |         |           |

## 三、我方必胜的关键（2-3个）

## 四、高危提醒（必须立即处理）

1. **[最危险的问题]**
   - 风险等级：高
   - 需要：立即补充证据/申请调查/调整策略

2. **[次要风险]**
   - 风险等级：中

## 五、行动清单

### 本周必须完成
- [ ]
- [ ]

### 开庭前必须完成
- [ ]
- [ ]

## 六、最终评估

**胜诉概率**：___%

**关键因素**：
1.
2.
3.

**一句话总结**：

---

*本手册由AI沙盘推演系统生成*
*通过{max_rounds}轮对抗推演*"""

        update_progress("正在生成最终报告", 0.9)
        
        final_handbook = self.chat([{"role": "user", "content": synthesis_prompt}], model="qwen-plus")
        
        update_progress("分析完成", 1.0)

        if final_handbook:
            return final_handbook
        else:
            return debate_record + "\n\n[综合失败，已生成辩论记录]"

    def our_side_analysis(
        self,
        case_info: str,
        opponent_attack: str,
        our_evidence: str = ""
    ) -> str:
        """
        我方视角分析 - 防守反击

        Args:
            case_info: 案件信息
            opponent_attack: 对手攻击分析
            our_evidence: 我方证据

        Returns:
            我方防守反击策略
        """
        system_prompt = """你是一位经验丰富的诉讼代理律师，专门负责防守和反击。

你的任务是：**针对对手的攻击，制定滴水不漏的防守策略，并寻找反击机会**。

请输出以下格式的分析报告：

## 一、针对对手攻击的反驳

### 1.1 逐条反驳对手的核心攻击点
- **对手论点**：...
  - **我方反驳**：...
  - **法律依据**：...
  - **证据支撑**：...

### 1.2 程序性防御
- [ ] 管辖权异议（如适用）
- [ ] 诉讼时效抗辩
- [ ] 举证责任分配
- [ ] 证据合法性质疑

## 二、我方证据加固

### 2.1 关键证据梳理
列出3-5份最关键的我方证据，说明其证明力

### 2.2 证据补强方案
- 需要补充的证据
- 获取途径
- 申请法院调取

### 2.3 证据运用策略
- 何时出示证据
- 出示顺序
- 证据组合

## 三、防守反击

### 3.1 反守为攻的机会
识别可以主动出击的点

### 3.2 反诉可能性分析
- 是否存在反诉机会
- 反诉的法律依据

### 3.3 关键证人策略
- 需要传唤的证人
- 证人证词要点

## 四、我方攻势

### 4.1 主动进攻方向
- 可以主动攻击对手的哪些弱点
- 法律依据

### 4.2 调解谈判筹码
- 我方优势
- 底线
- 谈判策略

## 五、风险预案

### 5.1 如果败诉...
### 5.2 如果被对方证据突袭...
### 5.3 如果法官倾向对方..."""

        user_content = f"""【案件信息】
{case_info}

【对手刚刚发动的攻击】
{opponent_attack}

【我方已有证据】
{our_evidence}

请逐一反驳，并制定反击策略。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def judge_evaluation(
        self,
        case_info: str,
        opponent_attack: str,
        our_defense: str
    ) -> str:
        """
        裁判视角评估 - 模拟法官思维

        Args:
            case_info: 案件信息
            opponent_attack: 对手攻击
            our_defense: 我方防守

        Returns:
            法官视角评估
        """
        system_prompt = """你是一位资深的民事法官，审案无数，思维冷静客观。

你的任务是：**模拟法官的思维方式，评估双方论点的说服力，预测法官可能的判决方向**。

请输出以下格式的评估报告：

## 一、法官关注的核心问题

### 1.1 事实认定层面
法官最关心哪些事实？哪些需要证据证明？

### 1.2 法律适用层面
本案适用哪些法律？法律要件是什么？

### 1.3 证据采信层面
哪些证据会被采信？哪些可能被质疑？

## 二、双方论点评估

### 2.1 对手论点的说服力
| 论点 | 法律依据 | 证明难度 | 法官接受度 |
|-----|---------|---------|-----------|
|     |         |         |           |

### 2.2 我方论点的说服力
| 论点 | 法律依据 | 证明难度 | 法官接受度 |
|-----|---------|---------|-----------|
|     |         |         |           |

## 三、法官心证预测

### 3.1 可能的判决方向
- 可能性1：（占比约__%）
- 可能性2：（占比约__%）
- 可能性3：（占比约__%）

### 3.2 法官可能追问的问题
1.
2.
3.

### 3.3 法官的自由裁量空间
- 哪些地方法官有裁量权
- 我方如何影响裁量

## 四、庭审表现建议

### 4.1 如何应对法官提问
### 4.2 如何打动法官
### 4.3 需要避免的错误

## 五、胜诉概率评估

**综合胜诉概率**：___%

**关键因素**：
1.
2.
3.

**建议**："""

        user_content = f"""【案件信息】
{case_info}

【对手的攻击策略】
{opponent_attack}

【我方的防守策略】
{our_defense}

请从法官视角评估。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def suggest_strategy(self, case_info: dict, evidence_count: int = 0) -> str:
        """一站式策略建议 — 便捷入口。

        从案件信息中提取描述和状态，委托给 strategy_suggestion()。
        """
        desc = case_info.get("description", "") or case_info.get("title", "")
        case_type = case_info.get("case_type", "合同纠纷")
        plaintiff = case_info.get("plaintiff", "")
        defendant = case_info.get("defendant", "")

        case_text = f"案件：{case_info.get('title', '')}\n类型：{case_type}\n原告：{plaintiff}\n被告：{defendant}\n描述：{desc[:3000]}"
        status_text = f"当前证据数：{evidence_count}，诉讼状态：准备起诉阶段"

        return self.strategy_suggestion(
            case_info=case_text,
            current_status=status_text,
            recent_development="委托方要求出具完整诉讼策略建议",
        )

    def strategy_synthesis(
        self,
        case_info: str,
        all_analysis: str
    ) -> str:
        """
        战略综合 - 整合所有分析

        Args:
            case_info: 案件信息
            all_analysis: 所有分析结果

        Returns:
            完整战略方案
        """
        system_prompt = ADVERSARIAL_SYNTHESIS_PROMPT

        user_content = f"""【案件信息】
{case_info}

【所有分析结果】
{all_analysis}

请综合成一份完整的战略方案。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def user_interaction(
        self,
        case_info: str,
        debate_context: str,
        user_question: str
    ) -> str:
        """
        用户交互 - 回应用户问题

        Args:
            case_info: 案件信息
            debate_context: 辩论上下文
            user_question: 用户问题

        Returns:
            AI回应
        """
        system_prompt = """你是一位资深法律顾问，正在参与一场多角色的诉讼对抗分析。

用户提出了问题或发表意见，你需要：
1. 理解用户的问题/意见
2. 结合当前辩论上下文给出专业回答
3. 必要时可以质疑当前分析
4. 给出建设性的建议

回答要：
- 专业但易懂
- 直接回答问题
- 必要时提供多种选择
- 鼓励用户思考"""

        user_content = f"""【案件信息】
{case_info}

【当前辩论进展】
{debate_context}

【用户的问题/意见】
{user_question}

请回应用户。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def legal_analysis_for_adversarial(
        self,
        case_info: str,
        question: str = "",
        analysis_depth: str = "标准分析"
    ) -> str:
        """
        严谨的法律分析 - 仅基于真实资料

        Args:
            case_info: 案件信息
            question: 分析问题
            analysis_depth: 分析深度

        Returns:
            法律分析结果
        """
        system_prompt = f"""你是一位严谨的法律专家。**核心原则：绝对禁止编造任何信息**。

分析要求：
1. **只陈述事实**：基于提供的真实信息
2. **明确标注未知**：不清楚的信息必须标注"未知"
3. **禁止推测**：没有证据支撑的推断必须明确说明
4. **区分事实与观点**：事实用"已核实"，观点用"推测"

分析深度：{analysis_depth}
- 快速分析：仅核心问题
- 标准分析：主要法律关系
- 深度分析：全面细致分析

请输出：
## 一、✅ 已核实的事实
（仅基于提供的真实资料）

## 二、⚠️ 未知但重要的信息
（需要补充才能准确分析）

## 三、📋 法律关系分析
## 四、📝 可能适用的法律条文
## 五、💡 分析结论

如信息不足，请明确指出无法分析的部分。"""

        user_content = f"""【案件信息】
{case_info}

【分析要求】
{question}

请仅基于以上信息进行分析，不要添加任何未提供的事实。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")

    def careful_opponent_analysis(
        self,
        case_info: str,
        known_opponent_info: str = "",
        known_weakness: str = "",
        unknown_info: list = None
    ) -> str:
        """
        谨慎的对方分析 - 强调信息不足

        Args:
            case_info: 案件信息
            known_opponent_info: 已知的对方信息
            known_weakness: 已知的对方弱点
            unknown_info: 未知信息列表

        Returns:
            谨慎的对方分析
        """
        unknown_str = "\n".join([f"- {u}" for u in (unknown_info or [])]) or "无"

        system_prompt = JUDGE_PERSPECTIVE_PROMPT

        user_content = f"""【案件信息】
{case_info}

【已知的对方信息】
{known_opponent_info or '未知'}

【已知的对方弱点】
{known_weakness or '未知'}

【已确认的未知信息】
{unknown_str}

请基于以上信息进行分析，明确区分已知和推测。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.chat(messages, model="qwen-plus")



# ==================== 子模块重导出（向后兼容 + 渐进拆分） ====================
# 原 llm_service.py 已拆分为三个模块，新增引用可直接从子模块导入：
#   from app.services.llm_service import llm_service   # 基础对话 + 全部方法（向后兼容）
#   from app.services.llm_doc_service import legal_doc_service   # 法律文书生成
#   from app.services.llm_adversarial_service import adversarial_service  # 对抗性分析
# 各子模块通过 llm_service.chat() 调用底层 LLM 能力

from app.services.llm_doc_service import LegalDocService, legal_doc_service
from app.services.llm_adversarial_service import AdversarialAnalysisService, adversarial_service


# 单例模式
llm_service = LLMService()
