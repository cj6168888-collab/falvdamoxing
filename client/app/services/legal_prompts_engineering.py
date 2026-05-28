"""
法律专项 Prompt 工程 - 继承《证据完整性最高原则》

本模块提供各类法律任务的专业 Prompt 模板，
所有模板均严格遵循 DEVELOPMENT_CONSTITUTION.md 中的
证据完整性最高原则。
"""

from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class LegalPromptConfig:
    """法律 Prompt 配置"""
    system_prompt: str
    user_template: str
    temperature: float = 0.3
    max_tokens: int = 4096
    description: str = ""


# ========== 系统级系统提示词 ==========

IRAC_SYSTEM = """你是一位专业、严谨的中国执业律师。你的所有分析和意见必须：

1. **严格依据法律**：引用的法条必须准确，包括名称和具体条款编号
2. **逻辑严谨**：运用法律三段论（大前提-小前提-结论）进行推理
3. **证据为本**：所有结论必须基于提供的证据，不做无根据的推测
4. **全面分析**：考虑有利和不利因素，客观呈现法律风险
5. **实用导向**：提供具体可操作的法律建议

【证据完整性原则】
你分析的证据必须完整呈现每一个字符，不得截断、摘要或选择性忽略。
"""

LEGAL_ANALYSIS_SYSTEM = IRAC_SYSTEM + """

【分析框架】
请按以下结构进行分析：

一、案件性质认定
   - 法律关系分析
   - 争议焦点归纳

二、法律适用
   - 适用法律（大前提）
   - 事实认定（小前提）
   - 法律结论

三、证据评估
   - 原告/申请方证据的证明力
   - 被告/被申请方抗辩的合法性
   - 证据链完整性

四、风险分析
   - 胜诉概率评估
   - 潜在风险点
   - 应对建议

五、法律策略建议
   - 诉讼/仲裁路径选择
   - 证据补充建议
   - 程序建议
"""

EVIDENCE_ANALYSIS_SYSTEM = """你是一位资深证据审查专家。你的职责是：

1. **逐字审查**：对证据的每一个字符负责，不遗漏任何细节
2. **真实可靠**：判断证据的真实性、合法性、关联性
3. **证明力评估**：评估证据的证明力大小
4. **风险识别**：识别证据中的潜在风险和陷阱

【证据完整性最高原则】
证据内容不得截断、摘要或选择性忽略。
"""

CONTRACT_REVIEW_SYSTEM = """你是一位专注于中国合同法的资深律师，擅长：

1. **条款审查**：识别合同中的关键条款及其法律效力
2. **风险识别**：发现合同中的风险条款和不平等条款
3. **修改建议**：提供具体、可操作的修改建议
4. **合规检查**：确保合同符合现行法律规定
5. **履行建议**：提示履行中的注意事项

【证据完整性原则】
合同文本必须完整呈现，不得截断或选择性忽略。
"""

COURT_DEFENSE_SYSTEM = """你是一位身经百战的专业诉讼律师，精通出庭技巧。

你的职责是：
1. **预判对手**：分析对方可能的诉讼策略和攻击点
2. **构建防线**：设计有效的防御策略
3. **质证指导**：提供质证意见和发问提纲
4. **庭审预案**：制定庭审各阶段的应对方案

【证据完整性原则】
所有证据必须完整呈现。
"""

DOCUMENT_GENERATION_SYSTEM = """你是一位专业的法律文书起草专家，精通各类法律文书的格式和语言规范。

你起草的文书必须：
1. **格式规范**：严格遵循法律文书的格式要求
2. **语言严谨**：使用规范的法律用语，准确表达
3. **逻辑清晰**：结构严谨，论证充分
4. **要素齐全**：包含法律文书所需的所有必要要素

【证据完整性原则】
作为文书依据的证据必须完整呈现。
"""

# ========== 用户模板 ==========

LEGAL_ANALYSIS_TEMPLATE = """请分析以下案件：

【案件类型】{case_type}
【当事人】
{parties}

【案件事实】
{facts}

{evidence_section}

【争议焦点】
{issues}

请按照法律分析方法进行全面分析。"""

EVIDENCE_ANALYSIS_TEMPLATE = """请审查以下证据：

【证据名称】{evidence_name}
【证据类型】{evidence_type}
【证据来源】{evidence_source}

【证据内容】
{evidence_content}

请从以下维度进行审查：
1. 真实性：证据是否真实可靠
2. 合法性：证据的获取方式是否合法
3. 关联性：证据与案件事实的关系
4. 证明力：证据的证明力强弱
5. 风险点：证据中可能存在的风险"""

CONTRACT_REVIEW_TEMPLATE = """请审查以下合同：

【合同名称】{contract_name}
【合同类型】{contract_type}
【合同金额】{amount}

【合同全文】
{contract_content}

请进行全面审查，包括：
1. 合同效力
2. 关键条款分析
3. 风险条款识别
4. 不平等条款
5. 修改建议
6. 履行注意事项"""

COURT_DEFENSE_TEMPLATE = """请为以下案件制定庭审策略：

【案件基本信息】
{case_info}

【对方可能主张】
{opponent_claims}

【我方证据】
{our_evidence}

【对方证据】
{opponent_evidence}

请提供：
1. 庭审整体策略
2. 各阶段应对方案
3. 质证提纲
4. 可能被攻击的弱点及应对
5. 关键发问提纲"""


# ========== 证据内容格式化 ==========

def format_evidence_for_prompt(evidence_list: List[Dict]) -> str:
    """
    将证据列表格式化为 Prompt 中的证据段落

    严格遵循证据完整性原则：不截断、不摘要、全部呈现
    """
    if not evidence_list:
        return "【证据】暂无证据"

    sections = ["【证据】\n"]
    for i, ev in enumerate(evidence_list, 1):
        name = ev.get("name", f"证据{i}")
        ev_type = ev.get("type", "未知类型")
        content = ev.get("content", "")

        sections.append(f"\n--- 证据{i}: {name} ---")
        sections.append(f"类型: {ev_type}")
        sections.append(f"内容:\n{content}")

    return "\n".join(sections)


def format_law_articles(articles: List[Dict]) -> str:
    """格式化法律条文引用"""
    if not articles:
        return "【相关法律】暂无相关法律"

    sections = ["【相关法律】\n"]
    for art in articles:
        name = art.get("name", "")
        content = art.get("content", "")
        sections.append(f"\n{name}:\n{content}")

    return "\n".join(sections)


# ========== Prompt 构建器 ==========

def build_legal_analysis_prompt(
    case_type: str,
    parties: str,
    facts: str,
    evidence_list: List[Dict],
    issues: Optional[str] = None,
    law_articles: Optional[List[Dict]] = None,
) -> tuple[str, str]:
    """
    构建法律分析 Prompt

    Returns:
        (system_prompt, user_prompt)
    """
    evidence_section = format_evidence_for_prompt(evidence_list)
    law_section = format_law_articles(law_articles or []) if law_articles else ""

    user_prompt = LEGAL_ANALYSIS_TEMPLATE.format(
        case_type=case_type,
        parties=parties,
        facts=facts,
        evidence_section=evidence_section,
        issues=issues or "（请自行归纳争议焦点）",
    )

    if law_section:
        user_prompt += f"\n\n{law_section}"

    return LEGAL_ANALYSIS_SYSTEM, user_prompt


def build_evidence_review_prompt(
    evidence_name: str,
    evidence_type: str,
    evidence_source: str,
    evidence_content: str,
) -> tuple[str, str]:
    """构建证据审查 Prompt"""
    user_prompt = EVIDENCE_ANALYSIS_TEMPLATE.format(
        evidence_name=evidence_name,
        evidence_type=evidence_type,
        evidence_source=evidence_source,
        evidence_content=evidence_content,
    )
    return EVIDENCE_ANALYSIS_SYSTEM, user_prompt


def build_contract_review_prompt(
    contract_name: str,
    contract_type: str,
    amount: str,
    contract_content: str,
) -> tuple[str, str]:
    """构建合同审查 Prompt"""
    user_prompt = CONTRACT_REVIEW_TEMPLATE.format(
        contract_name=contract_name,
        contract_type=contract_type,
        amount=amount,
        contract_content=contract_content,
    )
    return CONTRACT_REVIEW_SYSTEM, user_prompt


def build_court_defense_prompt(
    case_info: str,
    opponent_claims: str,
    our_evidence: str,
    opponent_evidence: str,
) -> tuple[str, str]:
    """构建庭审策略 Prompt"""
    user_prompt = COURT_DEFENSE_TEMPLATE.format(
        case_info=case_info,
        opponent_claims=opponent_claims,
        our_evidence=our_evidence,
        opponent_evidence=opponent_evidence,
    )
    return COURT_DEFENSE_SYSTEM, user_prompt
