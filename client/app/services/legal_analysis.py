"""
法律分析服务 - 整合防护系统的法律分析
"""

from typing import Dict, List, Optional
from app.services.legal_protection import LegalAIProtectionSystem, LegalSource
from app.services.legal_knowledge import search_legal_knowledge, verify_citation
from app.services.legal_prompts import (
    LEGAL_SYSTEM_PROMPT,
    CITATION_VERIFICATION_PROMPT,
    FACT_EXTRACTION_PROMPT,
    RISK_ASSESSMENT_PROMPT,
    get_system_prompt_with_facts,
    get_direction_prompt,
    CASE_DIRECTION_OPTIONS
)
from app.services.llm_service import llm_service


class LegalAnalysisService:
    """
    法律分析服务 - 整合防护系统的法律分析

    特点：
    1. 基于 RAG 检索增强生成
    2. 每个结论必须有法律依据
    3. 明确表达不确定性
    4. 像侦探一样提取关键事实
    """

    def __init__(self):
        self.protection = LegalAIProtectionSystem()

    def analyze_case(self,
                    query: str,
                    case_facts: str,
                    case_type: str = "合同纠纷",
                    user_position: str = "有利",
                    case_direction: str = "mediate") -> Dict:
        """
        案件法律分析

        Args:
            query: 用户问题
            case_facts: 案件事实描述
            case_type: 案件类型
            user_position: 用户立场（有利/不利）
            case_direction: 案件处理方向
                - negotiate: 友好协商
                - mediate: 调解优先
                - litigate: 诉讼解决
                - contain: 战略防守
                - retreat: 适时退让

        Returns:
            包含完整防护的法律分析结果
        """
        result = {
            "query": query,
            "case_type": case_type,
            "user_position": user_position,
            "case_direction": case_direction,
            "retrieved_sources": [],
            "analysis": "",
            "confidence": {},
            "risks": [],
            "warnings": [],
            "missing_facts": [],
            "reasoning_chain": ""
        }

        # Step 1: 检索相关法律条文（RAG）
        retrieved_laws = search_legal_knowledge(query)
        result["retrieved_sources"] = retrieved_laws

        # Step 2: 提取关键事实（侦探模式）
        protection_result = self.protection.process_query(
            query=query,
            user_case_facts=case_facts,
            user_position=user_position
        )
        result["extracted_facts"] = protection_result["data"].get("extracted_facts", {})
        result["missing_facts"] = protection_result["data"].get("missing_facts_warning", [])

        # Step 3: 获取定制化提示词（包含案件处理方向）
        system_prompt = get_system_prompt_with_facts(case_type, user_position, case_direction)

        # Step 4: 构建分析提示
        analysis_prompt = self._build_analysis_prompt(
            query=query,
            case_facts=case_facts,
            retrieved_laws=retrieved_laws,
            user_position=user_position,
            case_direction=case_direction
        )

        # Step 5: 调用 LLM 生成分析（使用防护系统提示词）
        analysis = llm_service.chat(system_prompt + "\n\n" + analysis_prompt)
        result["analysis"] = analysis

        # Step 6: 验证引用
        citation_result = self._verify_citations(analysis)
        result["citation_verification"] = citation_result

        # Step 7: 风险评估
        risk_assessment = self._assess_risks(
            analysis=analysis,
            case_facts=case_facts,
            user_position=user_position
        )
        result["risks"] = risk_assessment["risks"]
        result["recommendations"] = risk_assessment["recommendations"]

        # Step 8: 生成确定性评估
        confidence = self._calculate_confidence(
            retrieved_sources=retrieved_laws,
            citation_verified=len(citation_result["verified"]) > 0,
            missing_facts=len(result["missing_facts"]) > 0
        )
        result["confidence"] = confidence

        # Step 9: 生成推理链
        result["reasoning_chain"] = self._generate_reasoning_chain(
            facts=result["extracted_facts"],
            sources=retrieved_laws,
            analysis=analysis,
            user_position=user_position,
            case_direction=case_direction
        )

        return result

    def _build_analysis_prompt(self,
                              query: str,
                              case_facts: str,
                              retrieved_laws: List[Dict],
                              user_position: str,
                              case_direction: str = "mediate") -> str:
        """构建分析提示"""
        prompt_parts = []

        # 方向名称映射
        direction_names = {
            "negotiate": "🤝 友好协商",
            "mediate": "⚖️ 调解优先",
            "litigate": "⚔️ 诉讼解决",
            "contain": "🛡️ 战略防守",
            "retreat": "🔙 适时退让"
        }

        # 用户问题
        prompt_parts.append(f"## 用户问题\n{query}\n")

        # 案件事实
        prompt_parts.append(f"## 案件事实\n{case_facts}\n")

        # 相关法律依据（RAG 检索结果）
        if retrieved_laws:
            prompt_parts.append("## 相关法律依据（已检索）\n")
            for i, law in enumerate(retrieved_laws, 1):
                prompt_parts.append(
                    f"### {i}. {law['title']}{law['article']}\n"
                    f"- 关键词：{', '.join(law['keywords'])}\n"
                    f"- 内容：{law['content']}\n"
                    f"- 有效性：{'✅ 现行有效' if law['is_valid'] else '⚠️ 已失效'}\n"
                )
        else:
            prompt_parts.append("## ⚠️ 重要提示\n未检索到直接相关的法律依据，分析结论需要特别谨慎！\n")

        # 用户立场
        position_text = "有利" if user_position == "有利" else "不利"
        prompt_parts.append(f"\n## 用户立场\n当前立场对用户**{position_text}**，请据此调整策略建议。\n")

        # 案件处理方向
        direction_text = direction_names.get(case_direction, "⚖️ 调解优先")
        prompt_parts.append(f"\n## 案件处理方向\n用户选择的处理方向：**{direction_text}**\n")
        prompt_parts.append("请根据此方向调整建议的语气、策略和文书风格。\n")

        # 分析要求
        prompt_parts.append("""
## 分析要求

### 必须包含的内容：

1. **法律适用分析**
   - 适用的具体法条（如：《民法典》第X条）
   - 条文内容摘要
   - 与本案的关联性分析

2. **确定性评估**
   - 高/中/低确定性评级
   - 不确定性的明确表达

3. **策略建议**
   - 根据用户立场（有利/不利）给出针对性建议
   - 有利：最大化利益的策略
   - 不利：将损失降到最低的策略

4. **风险提示**
   - 最坏情况分析
   - 举证风险
   - 执行风险

5. **缺失信息**
   - 需要补充的关键事实
   - 需要核实的重要事项

### 格式要求：
- 每个法律结论必须标注具体法条来源
- 使用表格整理证据状态
- 使用分级标题组织内容
- 明确区分法律分析和策略建议
""")

        return "\n".join(prompt_parts)

    def _verify_citations(self, analysis: str) -> Dict:
        """验证分析中的法律引用"""
        import re
        citation_pattern = re.compile(r'《([^》]+)》第(\d+)条')
        citations = citation_pattern.findall(analysis)

        verified = []
        unverified = []

        for title, article in citations:
            result = verify_citation(title, article)
            if result["is_valid"]:
                verified.append({
                    "title": title,
                    "article": article,
                    "content": result["law"]["content"][:100] + "..."
                })
            else:
                unverified.append({
                    "title": title,
                    "article": article,
                    "warning": result["warning"]
                })

        return {
            "verified": verified,
            "unverified": unverified,
            "has_unverified": len(unverified) > 0
        }

    def _assess_risks(self,
                      analysis: str,
                      case_facts: str,
                      user_position: str) -> Dict:
        """评估风险"""
        risks = []
        recommendations = []

        # 基于分析内容评估风险
        if "不确定" in analysis or "可能" in analysis:
            risks.append("⚠️ 存在不确定性，结论仅供参考")

        if "举证" in case_facts and len(case_facts) < 100:
            risks.append("⚠️ 案件事实描述不完整，可能影响分析准确性")

        if "时效" in analysis:
            risks.append("⚠️ 涉及时效问题，需确认是否超过诉讼时效")

        # 策略建议
        if user_position == "有利":
            recommendations.append("1. 准备充分的证据支撑主张")
            recommendations.append("2. 考虑申请财产保全")
            recommendations.append("3. 设计最优诉讼请求")
        else:
            recommendations.append("1. 审查对方主张的法律依据")
            recommendations.append("2. 寻找减轻责任的事由")
            recommendations.append("3. 评估和解的可能性")

        return {
            "risks": risks,
            "recommendations": recommendations
        }

    def _calculate_confidence(self,
                           retrieved_sources: List[Dict],
                           citation_verified: bool,
                           missing_facts: List[str]) -> Dict:
        """计算确定性"""
        score = 0.5  # 基础分数

        # 有法律依据
        if retrieved_sources:
            score += 0.2 * min(len(retrieved_sources), 3)

        # 引用已验证
        if citation_verified:
            score += 0.15

        # 没有缺失事实
        if not missing_facts:
            score += 0.15

        # 确保分数在 0-1 之间
        score = min(max(score, 0), 1)

        if score > 0.9:
            level = "高"
        elif score > 0.7:
            level = "中"
        else:
            level = "低"

        return {
            "score": score,
            "level": level,
            "human_review_required": score < 0.8
        }

    def _generate_reasoning_chain(self,
                               facts: Dict,
                               sources: List[Dict],
                               analysis: str,
                               user_position: str,
                               case_direction: str = "mediate") -> str:
        """生成推理链"""
        # 方向名称映射
        direction_names = {
            "negotiate": "🤝 友好协商",
            "mediate": "⚖️ 调解优先",
            "litigate": "⚔️ 诉讼解决",
            "contain": "🛡️ 战略防守",
            "retreat": "🔙 适时退让"
        }

        chain = ["## 📋 法律推理链\n"]

        # 事实梳理
        chain.append("### 1️⃣ 关键事实梳理\n")
        if facts:
            for fact_type, values in facts.items():
                chain.append(f"- **{fact_type}**：{', '.join(values)}")
        else:
            chain.append("- 未能提取到结构化事实")

        # 法律适用
        chain.append("\n### 2️⃣ 法律依据\n")
        if sources:
            for source in sources:
                chain.append(f"✅ {source['title']}{source['article']} - {source['keywords'][0] if source['keywords'] else ''}")
        else:
            chain.append("⚠️ 未检索到相关法律依据")

        # 策略
        chain.append("\n### 3️⃣ 策略方向\n")
        if user_position == "有利":
            chain.append("🎯 目标：最大化利益\n")
            chain.append("- 全面主张权利")
            chain.append("- 准备充分证据")
            chain.append("- 优化诉讼请求")
        else:
            chain.append("🛡️ 目标：将损失降到最低\n")
            chain.append("- 审查对方依据")
            chain.append("- 寻找减责事由")
            chain.append("- 评估和解方案")

        # 处理方向
        chain.append("\n### 4️⃣ 处理方向\n")
        direction_text = direction_names.get(case_direction, "⚖️ 调解优先")
        chain.append(f"📌 用户选择：{direction_text}\n")

        return "\n".join(chain)

    def quick_verify(self, citation: str) -> Dict:
        """
        快速验证法律引用
        输入格式：《法律名称》第X条
        """
        import re
        match = re.match(r'《([^》]+)》第(\d+)条', citation)
        if match:
            title, article = match.groups()
            return verify_citation(title, article)
        else:
            return {
                "is_valid": False,
                "warning": "引用格式不正确，应为：《法律名称》第X条"
            }


# 全局实例
legal_analysis_service = LegalAnalysisService()
