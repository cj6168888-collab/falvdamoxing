"""
LLM 服务 - 对抗性分析模块
=========================
提供完整的对抗性诉讼分析能力（对手分析/证据攻防/情景预测/沙盘推演）
本模块由 llm_service.py 拆分导出
"""

from typing import Optional, List, Dict, Any

from app.services.llm_service import LLMService


class AdversarialAnalysisService:
    """
    对抗性诉讼分析服务

    提供完整的多角色对抗性分析能力：
    1. 对手视角分析（opponent_analysis）
    2. 证据攻防矩阵（evidence_attack_defense_matrix）
    3. 情景预测（scenario_prediction）
    4. 自动化行动方案（automated_action_plan）
    5. 完整对抗性分析/沙盘推演（full_adversarial_analysis）
    6. 我方防守分析 / 法官评估 / 战略综合
    """

    # 证据分析核心规则
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

    # 阶段提示词
    PHASE_PROMPTS = {
        "negotiation": """当前阶段：协商阶段

协商阶段的核心任务：
1. 评估协商的可能性和价值
2. 准备协商筹码
3. 制定协商策略
4. 设定协商底线
5. 准备应急预案（协商破裂后的诉讼）

协商阶段特别关注：
- 对方的协商诚意
- 我方的底线和上限
- 协商破裂后进入诉讼的准备工作""",

        "pre_litigation": """当前阶段：诉前准备阶段

诉前准备阶段的核心任务：
1. 完善证据材料
2. 锁定法律关系
3. 评估诉讼风险
4. 制定诉讼策略
5. 选择管辖法院
6. 准备诉讼材料

诉前准备阶段特别关注：
- 证据的收集和保全
- 财产保全的必要性
- 诉讼时效的把握""",

        "litigation": """当前阶段：诉讼阶段（起诉/答辩）

诉讼阶段的核心任务：
1. 起草诉状/答辩状
2. 提交证据清单
3. 申请财产保全
4. 应对管辖权异议
5. 准备质证意见

诉讼阶段特别关注：
- 诉讼请求的设计
- 举证期限的把握
- 程序性权利的行使""",

        "trial": """当前阶段：审理阶段

审理阶段的核心任务：
1. 庭前准备
2. 开庭陈述
3. 举证质证
4. 法庭辩论
5. 调解谈判

审理阶段特别关注：
- 庭审表现的把控
- 突发情况的应对
- 法官倾向的把握
- 调解时机判断""",

        "appeal": """当前阶段：上诉阶段

上诉阶段的核心任务：
1. 评估上诉价值
2. 制定上诉策略
3. 准备上诉材料
4. 分析一审判决

上诉阶段特别关注：
- 上诉理由的确定
- 新证据的提交
- 二审改判的可能性""",

        "execution": """当前阶段：执行阶段

执行阶段的核心任务：
1. 申请执行
2. 查找财产线索
3. 应对执行异议
4. 推进执行进程

执行阶段特别关注：
- 被执行人的财产状况
- 执行异议的处理
- 执行和解的可能""",
    }

    def __init__(self, llm_service: Optional[LLMService] = None):
        self._llm = llm_service

    @property
    def llm(self) -> LLMService:
        if self._llm is None:
            from app.services.llm_service import llm_service as _llm
            self._llm = _llm
        return self._llm

    # ==================== 对手视角分析 ====================

    def opponent_analysis(
        self,
        case_info: str,
        opponent_info: str = ""
    ) -> str:
        """对手视角分析 - 站在对方角度思考"""
        system_prompt = f"""{self.EVIDENCE_ANALYSIS_RULE}

你是一位顶级的诉讼策略专家，专门研究"对手在想什么"。

你的任务是：**站在对方当事人的角度，进行全面深入的策略分析**。

诉讼如同战争，"知己知彼，百战不殆"。"""

        user_content = f"【案件基本信息】\n{case_info}\n\n"
        if opponent_info:
            user_content += f"【已知对手信息】\n{opponent_info}\n\n"
        user_content += "请进行深入的对手视角分析。"

        return self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ], model="qwen-plus")

    # ==================== 证据攻防矩阵 ====================

    def evidence_attack_defense_matrix(
        self,
        case_info: str,
        our_evidence: str = "",
        opponent_evidence: str = "",
        opponent_strategies: str = ""
    ) -> str:
        """证据攻防矩阵分析"""
        system_prompt = f"""{self.EVIDENCE_ANALYSIS_RULE}

你是一位顶级的诉讼证据专家，擅长构建"证据攻防矩阵"。

你的任务是：**对案件中的所有证据进行双向分析，既分析进攻价值，也分析防御价值**。"""

        user_content = f"【案件基本信息】\n{case_info}\n\n"
        if our_evidence:
            user_content += f"【我方现有证据】\n{our_evidence}\n\n"
        if opponent_evidence:
            user_content += f"【对方可能的证据】\n{opponent_evidence}\n\n"
        if opponent_strategies:
            user_content += f"【对方可能的策略】\n{opponent_strategies}\n\n"
        user_content += "请进行全面的证据攻防矩阵分析。"

        return self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ], model="qwen-plus")

    # ==================== 情景预测 ====================

    def scenario_prediction(
        self,
        case_info: str,
        evidence_matrix: str = "",
        opponent_analysis: str = ""
    ) -> str:
        """案件走向预测 - 模拟不同证据组合下的可能结果"""
        system_prompt = """你是一位资深法官/仲裁员转型的高级顾问，拥有丰富的案件走向预判经验。

你的任务是：**基于不同的证据组合和策略选择，预测案件可能的走向**。

诉讼不是单一路径，而是多分支的决策树。每一个关键变量的变化，都可能导致完全不同的结果。"""

        user_content = f"【案件基本信息】\n{case_info}\n\n"
        if evidence_matrix:
            user_content += f"【证据攻防矩阵】\n{evidence_matrix}\n\n"
        if opponent_analysis:
            user_content += f"【对手分析】\n{opponent_analysis}\n\n"
        user_content += "请进行案件走向预测分析。"

        return self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ], model="qwen-plus")

    # ==================== 自动化行动方案 ====================

    def automated_action_plan(
        self,
        case_info: str,
        current_phase: str,
        scenario_prediction: str = "",
        evidence_matrix: str = ""
    ) -> str:
        """自动化行动方案生成"""
        phase_prompt = self.PHASE_PROMPTS.get(
            current_phase,
            "请根据案件信息生成行动方案。"
        )

        system_prompt = f"""你是一位顶级的诉讼项目总监，擅长将复杂的诉讼过程分解为可执行的任务清单。

你的任务是：**根据案件所处阶段，生成自动化的行动方案，让用户可以"一键傻瓜操作"完成复杂任务**。

{phase_prompt}"""

        user_content = f"【案件基本信息】\n{case_info}\n\n"
        if scenario_prediction:
            user_content += f"【案件走向预测】\n{scenario_prediction}\n\n"
        if evidence_matrix:
            user_content += f"【证据分析】\n{evidence_matrix}\n\n"
        user_content += f"【当前阶段】{current_phase}\n\n请生成自动化的行动方案。"

        return self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ], model="qwen-plus")

    # ==================== 完整对抗性分析（沙盘推演） ====================

    def full_adversarial_analysis(
        self,
        case_info: str,
        our_evidence: str = "",
        opponent_evidence: str = "",
        current_phase: str = "negotiation",
        max_rounds: int = 5
    ) -> str:
        """
        完整对抗性分析 - 多轮沙盘推演系统

        核心设计：
        1. 控辩换位思考 - 扮演对手和己方轮番论证
        2. 多轮推演 - 直到对方无牌可打
        3. 完整记录每轮攻防
        4. 最后综合成抗辩手册
        """
        import datetime as dt

        system_opponent = f"""{self.EVIDENCE_ANALYSIS_RULE}

你是一位经验丰富的诉讼对手律师，拥有以下特点：
- 精通对方的弱点，善于寻找法律漏洞
- 擅长证据突袭和程序性攻击
- 善于利用情感和舆论压力
- 目标：最大化己方利益，击败对手

当前任务：作为对手方，全面分析这个案件，制定攻击策略。
请用中文详细列出所有可能的攻击角度和策略。"""

        system_our_side = f"""{self.EVIDENCE_ANALYSIS_RULE}

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

        # 第一轮
        round_1_result = self.llm.chat([{
            "role": "user",
            "content": f"""{system_opponent}

【案件背景】
{case_info}

【我方证据】（你要攻击的重点）
{our_evidence}

【你方证据】（你手中的武器）
{opponent_evidence}

【当前阶段】
{current_phase}

请以对手律师的身份，全面列出你的攻击策略。"""
        }], model="qwen-plus")

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

        # 第二轮
        round_2_result = self.llm.chat([{
            "role": "user",
            "content": f"""{system_our_side}

【案件背景】
{case_info}

【我方证据】
{our_evidence}

【对手刚刚发动了以下攻击】
{round_1_result}

请逐一反驳对手的攻击。"""
        }], model="qwen-plus")

        if round_2_result:
            debate_record += f"""
---

# 第二轮：我方防守反击

{round_2_result}

"""

        # 第三轮及以后
        current_attack = round_2_result if round_2_result else ""

        for round_num in range(3, max_rounds + 1):
            opponent_response = self.llm.chat([{
                "role": "user",
                "content": f"""{system_opponent}

【你之前发动的攻击摘要】
{round_1_result}

【对方刚刚的反驳】
{current_attack}

面对对方的反驳，你需要：
1. 承认合理的反驳点
2. 坚守核心攻击点
3. 寻找新的攻击角度
4. 提出更有力的证据

# 第{round_num}轮：对手反扑"""
            }], model="qwen-plus")

            if not opponent_response or len(opponent_response) < 100:
                debate_record += f"\n**第{round_num}轮：对手已无牌可打**\n"
                break

            debate_record += f"""
---

# 第{round_num}轮：对手反扑

{opponent_response}

"""

            our_response = self.llm.chat([{
                "role": "user",
                "content": f"""{system_our_side}

【案件背景】
{case_info}

【我方证据】
{our_evidence}

【对手最新攻击】
{opponent_response}

# 第{round_num}轮：我方应对"""
            }], model="qwen-plus")

            if our_response:
                debate_record += f"""
## {round_num}.2 我方回应

{our_response}

"""
                current_attack = our_response
            else:
                break

        # 综合
        final_handbook = self.llm.chat([{
            "role": "user",
            "content": f"""{system_synthesizer}

【案件背景】
{case_info}

【完整辩论记录】
{debate_record}

请将上述多轮辩论综合成一份实战抗辩手册。

*本手册由AI沙盘推演系统生成*
*通过{max_rounds}轮对抗推演*"""
        }], model="qwen-plus")

        if final_handbook:
            return final_handbook
        else:
            return debate_record + "\n\n[综合失败，已生成辩论记录]"

    # ==================== 我方防守分析 ====================

    def our_side_analysis(
        self,
        case_info: str,
        opponent_attack: str,
        our_evidence: str = ""
    ) -> str:
        """我方视角分析 - 防守反击"""
        system_prompt = f"""{self.EVIDENCE_ANALYSIS_RULE}

你是一位经验丰富的诉讼代理律师，专门负责防守和反击。

你的任务是：**针对对手的攻击，制定滴水不漏的防守策略，并寻找反击机会**。"""

        user_content = f"""【案件信息】
{case_info}

【对手刚刚发动的攻击】
{opponent_attack}

【我方已有证据】
{our_evidence}

请逐一反驳，并制定反击策略。"""

        return self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ], model="qwen-plus")

    # ==================== 法官评估 ====================

    def judge_evaluation(
        self,
        case_info: str,
        opponent_attack: str,
        our_defense: str
    ) -> str:
        """裁判视角评估 - 模拟法官思维"""
        system_prompt = """你是一位资深的民事法官，审案无数，思维冷静客观。

你的任务是：**模拟法官的思维方式，评估双方论点的说服力，预测法官可能的判决方向**。"""

        user_content = f"""【案件信息】
{case_info}

【对手的攻击策略】
{opponent_attack}

【我方的防守策略】
{our_defense}

请从法官视角评估。"""

        return self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ], model="qwen-plus")

    # ==================== 战略综合 ====================

    def strategy_synthesis(
        self,
        case_info: str,
        all_analysis: str
    ) -> str:
        """战略综合 - 整合所有分析"""
        system_prompt = """你是一位顶级的法律战略专家，需要将多轮分析综合成一份完整的战略方案。

你的任务是：**整合所有分析，形成一份实战指南，让当事人在诉讼中始终占据主动**。"""

        user_content = f"""【案件信息】
{case_info}

【所有分析结果】
{all_analysis}

请综合成一份完整的战略方案。"""

        return self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ], model="qwen-plus")

    # ==================== 严谨法律分析 ====================

    def legal_analysis_for_adversarial(
        self,
        case_info: str,
        question: str = "",
        analysis_depth: str = "标准分析"
    ) -> str:
        """严谨的法律分析 - 仅基于真实资料"""
        system_prompt = f"""你是一位严谨的法律专家。**核心原则：绝对禁止编造任何信息**。

分析要求：
1. **只陈述事实**：基于提供的真实信息
2. **明确标注未知**：不清楚的信息必须标注"未知"
3. **禁止推测**：没有证据支撑的推断必须明确说明
4. **区分事实与观点**：事实用"已核实"，观点用"推测"

分析深度：{analysis_depth}"""

        user_content = f"""【案件信息】
{case_info}

【分析要求】
{question}

请仅基于以上信息进行分析，不要添加任何未提供的事实。"""

        return self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ], model="qwen-plus")

    # ==================== 用户交互 ====================

    def user_interaction(
        self,
        case_info: str,
        debate_context: str,
        user_question: str
    ) -> str:
        """用户交互 - 回应用户问题"""
        system_prompt = """你是一位资深法律顾问，正在参与一场多角色的诉讼对抗分析。

用户提出了问题或发表意见，你需要：
1. 理解用户的问题/意见
2. 结合当前辩论上下文给出专业回答
3. 必要时可以质疑当前分析
4. 给出建设性的建议

回答要：专业但易懂、直接回答问题、必要时提供多种选择、鼓励用户思考"""

        user_content = f"""【案件信息】
{case_info}

【当前辩论进展】
{debate_context}

【用户的问题/意见】
{user_question}

请回应用户。"""

        return self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ], model="qwen-plus")


# 单例
adversarial_service = AdversarialAnalysisService()
