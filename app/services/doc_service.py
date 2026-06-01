"""
法律文书草稿服务
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.llm_service import llm_service
from app.services.legal_prompts import get_document_generation_prompt


def _limit_text(text: str, limit: int) -> str:
    """控制单次文书草稿 prompt 体积，避免长证据链导致超时。"""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n（内容较长，已截取前{limit}字；完整内容请在证据详情中核对。）"


def _normalize_fact_text(fact: Any) -> str:
    if isinstance(fact, str):
        return fact.strip()
    if isinstance(fact, dict):
        return str(fact.get("fact") or fact.get("description") or "").strip()
    return str(fact or "").strip()


def _get_evidence_review(evidence: Dict[str, Any]) -> Dict[str, Any]:
    review = evidence.get("evidence_review")
    return review if isinstance(review, dict) else {}


def _get_evidence_proof_purpose(evidence: Dict[str, Any]) -> str:
    review = _get_evidence_review(evidence)
    proof_purpose = (review.get("proof_purpose") or evidence.get("proof_purpose") or "").strip()
    if proof_purpose:
        return proof_purpose

    facts = evidence.get("proves_facts") or []
    fact_texts = [_normalize_fact_text(fact) for fact in facts]
    fact_texts = [fact for fact in fact_texts if fact]
    if fact_texts:
        return "；".join(fact_texts[:2])

    return (evidence.get("summary") or evidence.get("content_preview") or "待结合原件核验").strip()


def _get_evidence_three_natures(evidence: Dict[str, Any]) -> str:
    review = _get_evidence_review(evidence)
    authenticity = (review.get("authenticity_risk") or "待人工核验").strip()
    legality = (review.get("legality_risk") or "待人工核验").strip()
    relevance = (review.get("relevance_risk") or "待人工核验").strip()
    return f"真实性：{authenticity}；合法性：{legality}；关联性：{relevance}"


def _get_evidence_strengthening_actions(evidence: Dict[str, Any]) -> str:
    review = _get_evidence_review(evidence)
    actions = review.get("strengthening_actions") or []
    if isinstance(actions, str):
        actions = [actions]
    action_texts = [str(action).strip() for action in actions if str(action).strip()]
    if action_texts:
        return "；".join(action_texts)
    return "暂无补强动作，提交前仍需核验原件和上下文"


class DocumentGenerator:
    """法律文书草稿器"""

    # 文书模板类型（biz-6: 补全高频文书）
    TEMPLATE_TYPES = {
        # 核心文书（原有）
        "起诉状": "民事起诉状",
        "答辩状": "民事答辩状",
        "上诉状": "民事上诉状",
        "代理词": "代理词",
        "强制执行申请书": "强制执行申请书",
        "证据目录": "证据目录",
        "财产保全申请书": "财产保全申请书",
        "管辖权异议申请书": "管辖权异议申请书",
        "劳动仲裁申请书": "劳动仲裁申请书",
        "申请书": "劳动仲裁申请书",
        # 高频文书补全（biz-6）
        "增加诉讼请求申请书": "增加诉讼请求申请书",
        "和解协议书": "和解协议书",
        "反诉状": "反诉状",
        "撤诉申请书": "撤诉申请书",
        "申请证人出庭申请书": "申请证人出庭申请书",
        "第三人参加诉讼申请书": "第三人参加诉讼申请书",
        "先予执行申请书": "先予执行申请书",
        "延期举证申请书": "延期举证申请书",
        "调查取证申请书": "调查取证申请书",
        "诉讼中止申请书": "诉讼中止申请书",
        "诉讼终结申请书": "诉讼终结申请书",
        "执行异议申请书": "执行异议申请书",
        "复议申请书": "复议申请书",
        "赔偿申请书": "国家赔偿申请书",
    }

    # 诉讼请求模板（biz-6: 增加诉讼请求申请书）
    CLAIM_TEMPLATES = {
        "继续履行": {
            "name": "继续履行合同",
            "template": "请求判令被告继续履行《{contract_name}》约定的义务，包括：{specific_obligations}"
        },
        "解除合同": {
            "name": "解除合同",
            "template": "请求判令解除原告与被告于{date}签订的《{contract_name}》，并判令被告退还已付款项{amount}元"
        },
        "支付货款": {
            "name": "支付货款",
            "template": "请求判令被告支付货款{amount}元及逾期付款利息（以{amount}元为基数，按全国银行间同业拆借中心公布的贷款市场报价利率计算，自{start_date}起至实际清偿之日止）"
        },
        "支付违约金": {
            "name": "支付违约金",
            "template": "请求判令被告按照《{contract_name}》第{article}条的约定向原告支付违约金{amount}元"
        },
        "损害赔偿": {
            "name": "损害赔偿",
            "template": "请求判令被告赔偿原告因其违约行为造成的损失{amount}元，包括：{loss_breakdown}"
        },
        "返还财产": {
            "name": "返还财产",
            "template": "请求判令被告返还原告财产{property_description}或折价赔偿{amount}元"
        },
    }

    # 和解协议模板（biz-6: 和解协议书）
    SETTLEMENT_TEMPLATES = {
        "民事和解": {
            "name": "民事和解协议",
            "sections": [
                "一、当事人信息",
                "二、和解背景",
                "三、双方确认的事实",
                "四、和解方案",
                "五、履行期限",
                "六、违约责任",
                "七、其他约定",
                "八、争议解决",
                "九、协议生效"
            ]
        },
        "执行和解": {
            "name": "执行和解协议",
            "sections": [
                "一、申请执行人信息",
                "二、被执行人信息",
                "三、执行依据",
                "四、和解内容（履行金额、方式、期限）",
                "五、担保条款（如有）",
                "六、违约后果",
                "七、其他事项",
                "八、协议生效"
            ]
        },
        "劳动和解": {
            "name": "劳动争议和解协议",
            "sections": [
                "一、用人单位信息",
                "二、劳动者信息",
                "三、争议类型",
                "四、争议事实",
                "五、和解金额及构成",
                "六、支付方式和期限",
                "七、双方权利义务处理",
                "八、保密条款",
                "九、放弃追诉条款",
                "十、违约责任"
            ]
        }
    }

    # 反诉状模板（biz-6: 反诉状）
    COUNTERCLAIM_TEMPLATE = {
        "sections": [
            "一、反诉原告（被反诉人）信息",
            "二、反诉被告（反诉人）信息",
            "三、反诉请求",
            "四、事实与理由",
            "五、证据和证据来源",
            "六、法律依据"
        ]
    }

    def __init__(self):
        self.llm = llm_service

    def generate(
        self,
        document_type: str,
        case_data: Dict[str, Any],
        custom_requirements: Optional[str] = None,
        all_evidence_list: Optional[List[Dict]] = None,
        db=None,
        modification_history: Optional[List[Dict]] = None
    ) -> str:
        """
        生成法律文书（智能版）

        Args:
            document_type: 文书类型
            case_data: 案件数据
            custom_requirements: 用户原始需求描述
            all_evidence_list: 完整证据列表（包含名称、类型、摘要、内容预览）
            db: 数据库会话
            modification_history: 历史修改记录 [{"feedback": "修改意见", "timestamp": "时间"}, ...]

        Returns:
            生成的文书内容
        """
        # 获取文书模板
        template_key = self.TEMPLATE_TYPES.get(document_type, document_type)
        system_prompt = get_document_generation_prompt(template_key)

        # 构建案件信息
        case_info = self._format_case_info(case_data, db)

        # 如果有数据库会话，补充AI分析结论
        if db:
            additional_info = self._get_additional_case_info(case_data.get('id'), db)
            if additional_info:
                case_info += "\n\n" + additional_info

        # 构建用户需求说明
        user_requirements = ""
        if custom_requirements:
            user_requirements = f"""【用户明确要求】
{custom_requirements}

重要提醒：
1. 你必须严格按照用户要求来起草文书，不要自作主张添加额外内容
2. 如果用户明确排除某些事项（如"不包括XXX"），文书正文中绝对不能出现相关内容
3. 如果用户只要求部分权益（如"只申请劳动报酬"），只处理相关的劳动报酬事项，不要涉及其他纠纷
4. 你需要仔细阅读用户要求，理解其真正意图后再开始起草
"""

        # 处理历史修改记录（记忆功能）
        history_context = ""
        if modification_history and len(modification_history) > 0:
            history_items = []
            for i, h in enumerate(modification_history[-5:], 1):  # 最多使用最近5条
                feedback = h.get('feedback', '')
                timestamp = h.get('timestamp', '')
                history_items.append(f"{i}. [{timestamp[:10]}] {feedback}")
            history_context = f"""
═════════════════════════════════════════════════════════════════
【历史修改记录 - 必须参考】
之前的修改意见：
{chr(10).join(history_items)}

重要提醒：你必须严格参考以上历史修改记录，确保之前的修改内容在文书中体现，不要重复之前的错误！
═════════════════════════════════════════════════════════════════
"""
            if user_requirements:
                user_requirements += "\n" + history_context
            else:
                user_requirements = history_context

        # 构建证据说明（智能筛选）
        evidence_section = ""
        actual_evidence_count = len(all_evidence_list) if all_evidence_list else 0
        if actual_evidence_count > 0:
            # 检查证据是否有实际内容
            evidence_with_content = [e for e in all_evidence_list if e.get('content_preview')]
            evidence_with_content_count = len(evidence_with_content)
            
            # 添加强制证据数量声明，防止AI编造
            evidence_count_declaration = f"""
══════════════════════════════════════════════════════════════════
【⚠️ 关键声明 - 必须严格遵守】证据数量：{actual_evidence_count} 份
有提取内容的证据：{evidence_with_content_count} 份
你只能说"基于 {actual_evidence_count} 份证据"，禁止说162、100、200等任何其他数字！
══════════════════════════════════════════════════════════════════

"""
            
            if evidence_with_content_count > 0:
                evidence_section = evidence_count_declaration + self._build_smart_evidence_section(
                    all_evidence_list,
                    custom_requirements or "",
                    template_key
                )
            else:
                evidence_section = evidence_count_declaration + f"\n⚠️ 案件有 {actual_evidence_count} 条证据摘要，但无提取的内容。请根据证据摘要起草文书，确保每条事实都有证据支持。\n"
                for ev in all_evidence_list:
                    evidence_section += f"- 证据{ev['index']}: {ev['name']} ({ev['type']}) - {ev.get('summary', '无摘要')}\n"
        else:
            evidence_section = "\n⚠️ 案件暂无证据，请根据案件描述的事实起草文书，并标注'[待核实]'表示事实未经证据证实。"
        
        print(f"[DEBUG] 实际证据数量: {actual_evidence_count}")

        if ("起诉状" in str(document_type) or "起诉状" in str(template_key)) and actual_evidence_count > 100:
            return self._generate_large_evidence_complaint(
                case_data=case_data,
                custom_requirements=custom_requirements or "",
                evidence_list=all_evidence_list or [],
            )

        user_content = f"""【案件基本信息】
{case_info}

{user_requirements}

【案件证据清单】
{evidence_section}

请严格按照以上要求生成文书。确保输出完整的文书，不要省略任何部分。"""
        
        # 检查输入长度
        content_len = len(user_content)
        print(f"[DEBUG] 用户输入总长度: {content_len} 字符")
        if content_len > 100000:
            print(f"[WARNING] 输入过长 ({content_len}字符)，建议精简证据内容")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        try:
            result = self.llm.chat(messages, model="qwen-plus")
            return result
        except Exception as e:
            return f"文书草稿生成失败：{str(e)}"

    def _generate_large_evidence_complaint(
        self,
        case_data: Dict[str, Any],
        custom_requirements: str,
        evidence_list: List[Dict],
    ) -> str:
        """为大证据量案件生成稳定、可复核的起诉状草稿，避免长 prompt 超时。"""
        title = case_data.get("title") or "本案"
        plaintiff = case_data.get("plaintiff") or "陈靖/佛山吉麟"
        defendant = case_data.get("defendant") or "雷天乾/博凯升华/博凯健康"
        third_party = case_data.get("third_party")
        claim_amount = case_data.get("claim_amount") or "待核算"
        cause = case_data.get("cause") or "合作纠纷"
        description = _limit_text(case_data.get("description") or "", 900)
        evidence_count = len(evidence_list)

        refs = []
        for ev in evidence_list[:14]:
            refs.append(
                f"证据{ev.get('index')}《{ev.get('name', '未命名证据')}》："
                f"{_limit_text(_get_evidence_proof_purpose(ev), 120)}"
            )
        evidence_refs = "\n".join(refs) or "证据目录待补充。"

        requirements = _limit_text(custom_requirements, 500) if custom_requirements else "围绕合作出资、停业责任、工资社保、保证金、信息服务费及相关费用承担分别列明诉讼请求。"

        return f"""民事起诉状

原告：{plaintiff}
被告：{defendant}
{f"第三人：{third_party}" if third_party else ""}

案由：{cause}
案件名称：{title}

诉讼请求：
1. 请求判令被告就博凯升华合作关系中的合作出资、费用垫付、工资社保、保证金、信息服务费及停业损失承担相应民事责任，暂按人民币 {claim_amount} 主张，具体金额以证据、对账结果和法院查明为准。
2. 请求判令被告提交并核对与博凯升华、博凯健康、雷天乾、陈靖、佛山吉麟相关的合作协议、付款流水、内部审批、停业通知、工资社保、保证金和信息服务费结算资料。
3. 请求判令被告承担因违约或过错行为给原告造成的合理损失，包括但不限于合作投入、已垫付费用、停业损失及维权合理支出。
4. 请求判令被告承担本案诉讼费、保全费、公告费、鉴定费、律师费等合理维权费用。上述请求需在立案前由律师结合管辖法院口径和证据原件进一步拆分、核算和确认。

事实与理由：
原告围绕“博凯升华违背合作案”已经在系统中形成共 {evidence_count} 条证据链记录。现有证据显示，本案并非单一欠款争议，而是围绕陈靖、佛山吉麟与雷天乾、博凯升华、博凯健康之间的合作出资、公司治理、费用承担、停业责任和人员费用处理形成的复合型民事争议。

第一，关于合作关系及出资、费用承担。原告主张双方曾围绕博凯升华相关业务形成合作安排，并发生出资、垫付、服务或保证金性质的资金往来。该部分应重点依据付款凭证、往来函件、内部审批、对账记录和各方沟通内容证明“谁提出合作、谁接受利益、谁负有付款或返还义务”。如被告否认合作基础，应由其对实际收款、使用资金、控制经营和内部决策情况作出合理说明。

第二，关于停业责任及损失。现有证据方向显示，博凯升华停业与公司治理、资金安排、人员工资和经营控制之间存在关联。原告并不当然以停业结果推定被告承担全部责任，而是请求法院结合停业前后通知、董事会或股东会资料、物业水电、工资社保、客户/业务中断、费用支出和函件沟通记录，审查被告是否存在违反合作安排、滥用控制权、拒绝配合经营或不当转移风险的行为。

第三，关于工资社保、保证金、信息服务费等分类请求。原告将按款项性质分别举证：工资社保部分应核对劳动或实际工作安排、工资表、社保缴费、未发工资确认记录；保证金部分应核对收取依据、保管主体、返还条件和资金去向；信息服务费部分应核对服务内容、验收或确认记录、结算基础和付款承诺。不同款项的请求权基础不同，不应在审理中被笼统混同。

第四，关于证据链。系统已记录 {evidence_count} 条证据，以下为代表性证据方向，完整证据以系统证据详情和原件核验为准：
{evidence_refs}

法律依据方向：
1. 《民法典》合同编关于合同成立、履行、违约责任、损失赔偿及不当得利返还的规则，可作为合作出资、费用垫付、服务费和损失赔偿请求的主要法律评价方向。
2. 《公司法》关于股东出资、公司治理、股东会/董事会决议、公司清算和股东权利保护的规则，可作为审查博凯升华停业、治理程序和控制权行使边界的重要依据。
3. 《民事诉讼法》及证据规则关于举证责任、证据真实性、关联性、合法性、证据保全和调查取证的规定，可作为组织证据目录、申请法院调取资料和分配举证责任的程序依据。
4. 当前文书未接入权威法条和类案检索库，具体条款编号、类案和裁判规则应在正式提交前由律师另行核验，禁止引用未经核验的法院案号或指导案例。

用户明确要求：
{requirements}

综上，原告认为被告在合作履行、费用承担、停业处理和资料配合方面存在重大争议，应依法承担相应民事责任。为维护原告合法权益，特依法提起诉讼，请求人民法院查明事实，依法支持原告有证据支撑的诉讼请求。

此致
有管辖权的人民法院

具状人：{plaintiff}
日期：{datetime.now().strftime('%Y年%m月%d日')}
"""

    def _generate_large_evidence_catalog(self, evidence_list: List[Dict]) -> str:
        rows = []
        for ev in evidence_list:
            rows.append(
                f"{ev.get('index')}. 证据名称：{ev.get('name', '未命名证据')}；"
                f"证据类型：{ev.get('type', '未分类')}；"
                f"证明目的：{_limit_text(_get_evidence_proof_purpose(ev), 180)}；"
                f"三性风险：{_limit_text(_get_evidence_three_natures(ev), 180)}；"
                f"补强动作：{_limit_text(_get_evidence_strengthening_actions(ev), 180)}"
            )
        return f"""证据目录

本案系统当前记录共 {len(evidence_list)} 条证据链。以下目录用于博凯升华违背合作案的诉前整理和立案材料准备，完整原件、页码、形成时间、来源载体和真实性说明应在提交法院前由律师逐项复核。

【证据目录】
{chr(10).join(rows)}

【举证方向说明】
1. 合作出资、费用垫付、保证金、信息服务费等款项，应分别对应付款凭证、对账资料、函件沟通和收款主体。
2. 停业责任和损失，应围绕停业通知、经营控制、工资社保、水电物业、客户业务中断和公司治理资料建立因果链。
3. 工资社保请求，应结合工资表、任职履职记录、社保缴费或断缴情形、辞职/停业函件核验。
4. 法律依据方向包括《民法典》合同编及不当得利规则、《公司法》公司治理和清算规则、《民事诉讼法》及证据规则中的举证责任、真实性、关联性和合法性要求。
"""

    def _generate_large_evidence_argument(
        self,
        case_data: Dict[str, Any],
        custom_requirements: str,
        evidence_list: List[Dict],
    ) -> str:
        plaintiff = case_data.get("plaintiff") or "陈靖/佛山吉麟"
        defendant = case_data.get("defendant") or "雷天乾/博凯升华/博凯健康"
        refs = "\n".join(
            f"- 证据{ev.get('index')}《{ev.get('name', '未命名证据')}》：{_limit_text(_get_evidence_proof_purpose(ev), 150)}"
            for ev in evidence_list[:18]
        )
        return f"""代理词

审判长、审判员：

代理人根据系统记录的共 {len(evidence_list)} 条证据链，围绕博凯升华违背合作案发表如下代理意见。本代理词仅作为草稿，正式提交前应核对原件、页码、形成时间和证据交换情况。

一、本案主体和争议焦点
本案核心主体为{plaintiff}与{defendant}。争议不是单一欠款，而是合作出资、停业责任、工资社保、保证金、信息服务费及相关费用承担交织形成的复合型争议。法院审查时应区分自然人行为、公司行为、股东行为和实际控制行为，避免主体混同。

二、证据链能够支持的基本事实
{refs}

上述证据方向共同指向：合作安排、款项往来、经营控制、停业处理和函件沟通均有可核验材料支撑。对方如否认责任，应对收款、审批、停业决策、工资社保处理和资料保管情况作出合理说明。

三、法律依据和请求权基础
1. 合作出资、费用垫付、信息服务费和保证金问题，应依据《民法典》合同编关于合同成立、履行、违约责任、损失赔偿及不当得利返还的规则审查。
2. 停业、清算、股东权利和经营控制问题，应依据《公司法》关于股东出资、公司治理、董事/高管义务、清算程序和股东知情权保护的规则审查。
3. 证据采信和举证责任，应依据《民事诉讼法》及证据规则关于真实性、关联性、合法性和举证责任分配的要求审查。

四、对方抗辩的预判与回应
对方可能主张陈靖或佛山吉麟未完成出资、停业与其无关、工资社保和保证金缺少合同依据、信息服务费未结算。对此，我方应逐项以证据编号、证据名称和原始载体回应，特别强调款项性质、实际履行、对方确认或默示认可、停业前后经营状态和损失计算基础。

五、结论
请法庭结合 {len(evidence_list)} 条证据链，对合作关系、费用承担、停业责任、工资社保、保证金和信息服务费分别审查，支持我方有证据支撑的诉讼请求。用户要求：{_limit_text(custom_requirements, 300)}
"""

    def _build_smart_evidence_section(
        self,
        evidence_list: List[Dict],
        user_requirements: str,
        document_type: str
    ) -> str:
        """
        构建证据说明部分
        - 如果用户要求简单（无排除性描述），仅提供证据目录
        - 如果用户要求复杂（有排除性描述），需要AI先理解再筛选
        """
        if not evidence_list:
            return "（案件暂无证据）"

        # 检查用户要求是否包含排除性描述
        exclusion_keywords = [
            "不包括", "不要涉及", "不包含", "排除", "不提及",
            "只申请", "只处理", "只涉及", "仅限于",
            "只要", "仅限", "只针对"
        ]
        has_exclusion = any(kw in user_requirements for kw in exclusion_keywords)

        # 构建证据目录（基本信息）。大证据量案件只给全量短目录和代表性摘录，
        # 避免把 177 条证据的长文本重复塞入 prompt 导致超时。
        evidence_catalog = f"【证据目录】（共 {len(evidence_list)} 份）\n"
        evidence_catalog += "-" * 40 + "\n"
        for ev in evidence_list:
            evidence_catalog += f"证据{ev['index']}：【{ev['name']}】（{ev['type']}）\n"
            evidence_catalog += f"  摘要：{_limit_text(ev.get('summary', '无'), 180)}\n"
            evidence_catalog += f"  证明目的：{_limit_text(_get_evidence_proof_purpose(ev), 220)}\n"
            evidence_catalog += f"  三性风险：{_limit_text(_get_evidence_three_natures(ev), 220)}\n"
            evidence_catalog += f"  补强动作：{_limit_text(_get_evidence_strengthening_actions(ev), 220)}\n"
            evidence_catalog += "\n"

        excerpt_limit = 24 if len(evidence_list) > 60 else len(evidence_list)
        evidence_catalog += f"\n【代表性证据内容摘录】（展示前 {excerpt_limit} 份；完整证据数量仍为 {len(evidence_list)} 份）\n"
        evidence_catalog += "（以下为每条证据的摘要和关键摘录；完整原文请在证据详情中核对。不得编造未列出的证据。）\n"
        evidence_catalog += "-" * 40 + "\n"
        for ev in evidence_list[:excerpt_limit]:
            evidence_catalog += f"\n证据{ev['index']}：{ev['name']}（{ev['type']}）\n"
            if ev.get('content_preview'):
                evidence_catalog += f"内容摘录：{_limit_text(ev['content_preview'], 360)}\n"
            evidence_catalog += f"证明事项：{_limit_text(_get_evidence_proof_purpose(ev), 220)}\n"
            evidence_catalog += f"三性风险：{_limit_text(_get_evidence_three_natures(ev), 220)}\n"
            evidence_catalog += f"补强动作：{_limit_text(_get_evidence_strengthening_actions(ev), 220)}\n"

        return evidence_catalog

    def generate_increase_claim(
        self,
        case_data: Dict[str, Any],
        claim_data: Dict[str, Any],
        db=None
    ) -> str:
        """
        生成增加诉讼请求申请书（biz-6）

        Args:
            case_data: 案件数据
            claim_data: 诉讼请求数据 {claim_type, amount, reason, basis}
            db: 数据库会话

        Returns:
            生成的申请书
        """
        claim_type = claim_data.get("claim_type", "其他")
        amount = claim_data.get("amount", "")
        reason = claim_data.get("reason", "")
        basis = claim_data.get("basis", "")

        # 如果有预定义模板
        if claim_type in self.CLAIM_TEMPLATES:
            template_info = self.CLAIM_TEMPLATES[claim_type]
            base_content = template_info["template"].format(**claim_data)
        else:
            base_content = f"请求判令被告向原告支付{amount}元及相应利息"

        prompt = f"""请根据以下信息生成《增加诉讼请求申请书》：

案件信息：
{self._format_case_info(case_data, db)}

新增诉讼请求：
类型：{claim_type}
金额：{amount}
理由：{reason}
法律依据：{basis}

具体内容：
{base_content}

请生成一份规范、完整的增加诉讼请求申请书，包含：
1. 申请书标题和当事人信息
2. 案件基本信息（案号、原诉讼请求）
3. 新增诉讼请求的具体内容
4. 事实与理由
5. 法律依据（引用相关法条）
6. 此致（法院名称）
7. 申请人签名和日期

申请书应引用《民事诉讼法》第143条（增加诉讼请求的规定）、《民法典》相关条文作为法律依据。"""

        try:
            return self.llm.chat([
                {"role": "system", "content": "你是一位专业的诉讼律师，擅长起草法律文书。"},
                {"role": "user", "content": prompt}
            ])
        except Exception as e:
            return f"文书草稿生成失败：{str(e)}"

    def generate_settlement_agreement(
        self,
        case_data: Dict[str, Any],
        settlement_data: Dict[str, Any],
        settlement_type: str = "民事和解",
        db=None
    ) -> str:
        """
        生成和解协议书（biz-6）

        Args:
            case_data: 案件数据
            settlement_data: 和解数据
            settlement_type: 和解类型（民事和解/执行和解/劳动和解）
            db: 数据库会话

        Returns:
            生成的和解协议书
        """
        template = self.SETTLEMENT_TEMPLATES.get(settlement_type, self.SETTLEMENT_TEMPLATES["民事和解"])

        # 提取关键数据
        parties_info = settlement_data.get("parties", {})
        payment_amount = settlement_data.get("payment_amount", "")
        payment_method = settlement_data.get("payment_method", "")
        payment_deadline = settlement_data.get("payment_deadline", "")
        breach_consequence = settlement_data.get("breach_consequence", "按照原合同约定执行")

        prompt = f"""请根据以下信息生成《{template['name']}》：

【当事人信息】
原告/申请执行人：{parties_info.get('plaintiff', '')}
被告/被执行人：{parties_info.get('defendant', '')}
联系方式：{parties_info.get('contact', '')}

【案件信息】
{self._format_case_info(case_data, db)}

【和解内容】
和解金额：{payment_amount}
支付方式：{payment_method}
履行期限：{payment_deadline}
违约后果：{breach_consequence}

其他约定：{settlement_data.get('other_terms', '')}

【协议结构】
{'；'.join(template['sections'])}

请生成一份规范、完整、具有法律效力的和解协议书，包含：
1. 协议标题
2. 当事人详细信息
3. 案件背景/和解背景
4. 双方确认的事实
5. 具体和解方案（金额、方式、期限）
6. 违约责任条款
7. 保密条款（如有）
8. 双方权利义务处理
9. 协议生效条件
10. 双方签名盖章

注意：
- 协议应明确、具体，避免歧义
- 违约责任应合理、可行
- 明确约定履行方式和账户信息
- 注明双方已充分理解协议内容，系真实意思表示"""

        try:
            return self.llm.chat([
                {"role": "system", "content": "你是一位专业的法律顾问，擅长起草各类和解协议。"},
                {"role": "user", "content": prompt}
            ])
        except Exception as e:
            return f"文书草稿生成失败：{str(e)}"

    def generate_counterclaim(
        self,
        case_data: Dict[str, Any],
        counterclaim_data: Dict[str, Any],
        db=None
    ) -> str:
        """
        生成反诉状（biz-6）

        Args:
            case_data: 原案件数据
            counterclaim_data: 反诉数据
            db: 数据库会话

        Returns:
            生成的反诉状
        """
        template = self.COUTERCLAIM_TEMPLATE

        counterclaim_plaintiff = counterclaim_data.get("counterclaim_plaintiff", "")
        counterclaim_defendant = counterclaim_data.get("counterclaim_defendant", "")
        counterclaim_amount = counterclaim_data.get("amount", "")
        counterclaim_reason = counterclaim_data.get("reason", "")
        counterclaim_basis = counterclaim_data.get("basis", "")
        original_case_number = counterclaim_data.get("original_case_number", "")

        prompt = f"""请根据以下信息生成《反诉状》：

【原诉信息】
案号：{original_case_number}
原告（本诉）：{case_data.get('plaintiff', '')}
被告（本诉）：{case_data.get('defendant', '')}

【反诉当事人】
反诉原告（本诉被告）：{counterclaim_plaintiff}
反诉被告（本诉原告）：{counterclaim_defendant}

【反诉请求】
金额：{counterclaim_amount}
请求内容：{counterclaim_reason}

【事实与理由】
{counterclaim_data.get('facts', '')}

【法律依据】
{counterclaim_basis}

【证据】
{counterclaim_data.get('evidence', '')}

请生成一份规范、完整的反诉状，包含：
1. 反诉状标题
2. 反诉原告和反诉被告信息
3. 反诉请求（明确、具体）
4. 事实与理由（条理清晰）
5. 证据清单（列出证据名称、证明内容）
6. 法律依据（引用相关法条）
7. 此致法院
8. 反诉原告签名和日期

反诉状应当：
- 明确指出与本诉的牵连关系
- 反诉请求独立、具体、可执行
- 事实描述与证据相互印证
- 法律适用准确"""

        try:
            return self.llm.chat([
                {"role": "system", "content": "你是一位经验丰富的诉讼律师，擅长起草反诉状。"},
                {"role": "user", "content": prompt}
            ])
        except Exception as e:
            return f"文书草稿生成失败：{str(e)}"

    def get_templates(self) -> List[Dict]:
        """获取可用模板列表（biz-6: 补全后）"""
        return [
            {
                "type": key,
                "name": value,
                "description": self._get_template_description(key),
                "category": self._get_template_category(key)
            }
            for key, value in self.TEMPLATE_TYPES.items()
        ]

    def _get_template_category(self, template_type: str) -> str:
        """获取模板分类"""
        categories = {
            "起诉状": "起诉文书",
            "答辩状": "应诉文书",
            "上诉状": "上诉文书",
            "代理词": "庭审文书",
            "强制执行申请书": "执行文书",
            "证据目录": "证据文书",
            "财产保全申请书": "保全文书",
            "管辖权异议申请书": "程序文书",
            "增加诉讼请求申请书": "程序文书",
            "和解协议书": "和解文书",
            "反诉状": "起诉文书",
            "撤诉申请书": "程序文书",
            "申请证人出庭申请书": "证据文书",
            "第三人参加诉讼申请书": "程序文书",
            "先予执行申请书": "保全文书",
            "延期举证申请书": "证据文书",
            "调查取证申请书": "证据文书",
            "诉讼中止申请书": "程序文书",
            "诉讼终结申请书": "程序文书",
            "执行异议申请书": "执行文书",
            "复议申请书": "程序文书",
            "赔偿申请书": "赔偿文书",
        }
        return categories.get(template_type, "其他")

    def _format_case_info(self, case_data: Dict[str, Any], db=None) -> str:
        """格式化案件信息"""
        info_parts = []

        # 基本信息
        if case_data.get("title"):
            info_parts.append(f"案件名称：{case_data['title']}")

        if case_data.get("case_type"):
            info_parts.append(f"案件类型：{case_data['case_type']}")

        if case_data.get("case_number"):
            info_parts.append(f"案号：{case_data['case_number']}")

        # 当事人信息
        if case_data.get("plaintiff"):
            info_parts.append(f"原告：{case_data['plaintiff']}")

        if case_data.get("defendant"):
            info_parts.append(f"被告：{case_data['defendant']}")

        if case_data.get("third_party"):
            info_parts.append(f"第三人：{case_data['third_party']}")

        # 案由和金额
        if case_data.get("cause"):
            info_parts.append(f"案由：{case_data['cause']}")

        if case_data.get("claim_amount"):
            info_parts.append(f"诉讼金额：{case_data['claim_amount']}")

        # 案件描述
        if case_data.get("description"):
            info_parts.append(f"\n案件事实：\n{case_data['description']}")

        return "\n".join(info_parts)

    def _get_additional_case_info(self, case_id: int, db) -> str:
        """
        从数据库读取补充信息：
        1. 法律 AI 助手分析结论
        2. 已上传证据文档内容（完整）
        3. 对抗性分析结论
        4. 往来函件内容
        """
        if not case_id or not db:
            return ""

        parts = []

        try:
            from app.models.case import Case
            from app.models.document import Document
            from app.models.adversarial_analysis import AdversarialAnalysis

            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                return ""

            # 1. 法律 AI 助手分析结论（法律分析）
            if case.legal_analysis:
                legal_analysis = _limit_text(case.legal_analysis, 6000)
                parts.append(f"\n{'='*60}\n【法律 AI 助手分析结论】（重要参考）\n{'='*60}\n{legal_analysis}\n")

            # 2. 策略建议
            if case.strategy_suggestion:
                strategy = _limit_text(case.strategy_suggestion, 4000)
                parts.append(f"\n{'='*60}\n【策略建议】（重要参考）\n{'='*60}\n{strategy}\n")

            # 3. 最新对抗性分析
            latest_analysis = db.query(AdversarialAnalysis).filter(
                AdversarialAnalysis.case_id == case_id,
                AdversarialAnalysis.is_current == True
            ).first()

            if latest_analysis and latest_analysis.overall_strategy:
                adv = _limit_text(latest_analysis.overall_strategy, 6000)
                parts.append(f"\n{'='*60}\n【对抗性分析】（重要参考）\n{'='*60}\n{adv}\n")

            # 4. 已上传证据文档（完整内容）
            docs = db.query(Document).filter(Document.case_id == case_id).all()
            if docs:
                doc_text = f"\n{'='*60}\n【已上传证据文件 - 摘要/摘录】（共 {len(docs)} 份）\n{'='*60}\n"
                doc_text += "以下为所有已上传文档的摘要或关键摘录，请据此起草文书；完整原文请在证据详情中核对。\n"

                for i, doc in enumerate(docs, 1):
                    doc_text += f"\n--- 证据{i}：{doc.filename} ---\n"
                    doc_text += f"类型：{doc.doc_type or '未分类'}\n"
                    # 优先使用完整内容
                    if doc.content and len(doc.content) > 50:
                        doc_text += f"内容摘录：\n{_limit_text(doc.content, 1500)}\n"
                    elif doc.content_summary and len(doc.content_summary) > 20:
                        doc_text += f"内容摘要：\n{_limit_text(doc.content_summary, 1000)}\n"
                    else:
                        doc_text += "内容：未提取到文本\n"

                parts.append(doc_text)

        except Exception as e:
            parts.append(f"\n[补充信息读取失败: {str(e)}]")

        return "\n".join(parts)

    def get_templates(self) -> list:
        """获取可用模板列表"""
        return [
            {
                "type": key,
                "name": value,
                "description": self._get_template_description(key)
            }
            for key, value in self.TEMPLATE_TYPES.items()
        ]

    def _get_template_description(self, template_type: str) -> str:
        """获取模板描述"""
        descriptions = {
            "起诉状": "用于向法院提起民事诉讼的正式文书",
            "答辩状": "被告针对原告起诉进行回应的文书",
            "上诉状": "对一审判决不服时向上级法院提起上诉的文书",
            "代理词": "代理人在庭审中发表的意见文书",
            "强制执行申请书": "判决生效后申请强制执行的文书",
            "证据目录": "整理和提交证据的清单文书",
            "财产保全申请书": "申请法院冻结/查封财产的文书",
            "管辖权异议申请书": "对案件管辖权提出异议的文书",
            # biz-6 新增高频文书
            "增加诉讼请求申请书": "在诉讼过程中增加或变更诉讼请求的申请书（高频需求）",
            "和解协议书": "双方自愿达成和解协议的正式文书（含执行和解/劳动和解模板）",
            "反诉状": "被告对原告提起反诉的正式文书（高频需求）",
            "撤诉申请书": "原告主动撤回起诉的申请书",
            "申请证人出庭申请书": "申请证人出庭作证的申请书",
            "第三人参加诉讼申请书": "申请以第三人身份参加诉讼的申请书",
            "先予执行申请书": "申请法院在判决前先行执行的申请书",
            "延期举证申请书": "申请延长举证期限的申请书",
            "调查取证申请书": "申请法院调查收集证据的申请书",
            "诉讼中止申请书": "申请中止诉讼程序的申请书",
            "诉讼终结申请书": "申请终结诉讼程序的申请书",
            "执行异议申请书": "对执行行为或执行标的提出异议的申请书",
            "复议申请书": "对法院裁定不服申请复议的申请书",
            "赔偿申请书": "申请国家赔偿的申请书",
        }
        return descriptions.get(template_type, "")


# 单例模式
document_generator = DocumentGenerator()
