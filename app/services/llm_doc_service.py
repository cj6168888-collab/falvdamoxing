"""
LLM 服务 - 法律文书生成模块
============================
提供法律文书生成能力（起诉状/答辩状/代理词/上诉状等）
本模块由 llm_service.py 拆分导出
"""

from typing import Optional, List, Dict, Any

from app.services.llm_service import LLMService


class LegalDocService:
    """
    法律文书生成服务

    提供标准法律文书的 LLM 生成能力
    """

    # 文书模板定义
    DOCUMENT_TEMPLATES = {
        "起诉状": """你是一位专业的民事诉讼律师，请根据以下案件信息，起草一份民事起诉状。

要求：
1. 格式规范，符合《民事诉讼法》规定
2. 事实陈述清晰、简洁
3. 诉讼请求明确、具体
4. 法律依据充分

请输出完整的起诉状文本。""",

        "答辩状": """你是一位专业的民事诉讼律师，请根据以下案件信息和原告起诉内容，起草一份答辩状。

要求：
1. 格式规范，符合《民事诉讼法》规定
2. 答辩理由充分、有力
3. 针对原告的诉讼请求逐一回应
4. 提出明确的答辩意见

请输出完整的答辩状文本。""",

        "代理词": """你是一位专业的民事诉讼律师，请根据以下案件信息和庭审情况，起草一份代理词。

要求：
1. 逻辑严密，说理充分
2. 围绕争议焦点展开
3. 引用的证据和法律要准确
4. 结语要有力

请输出完整的代理词文本。""",

        "上诉状": """你是一位专业的民事诉讼律师，请根据以下案件信息和一审判决，起草一份上诉状。

要求：
1. 明确上诉请求
2. 详述上诉理由
3. 针对一审判决的错误进行论证

请输出完整的上诉状文本。""",
    }

    def __init__(self, llm_service: Optional[LLMService] = None):
        self._llm = llm_service

    @property
    def llm(self) -> LLMService:
        if self._llm is None:
            from app.services.llm_service import llm_service as _llm
            self._llm = _llm
        return self._llm

    def generate(
        self,
        document_type: str,
        case_info: str,
        specific_requirements: str = ""
    ) -> str:
        """
        生成法律文书

        Args:
            document_type: 文书类型（起诉状/答辩状/代理词/上诉状等）
            case_info: 案件信息
            specific_requirements: 特殊要求

        Returns:
            生成的文书内容
        """
        system_prompt = self.DOCUMENT_TEMPLATES.get(
            document_type,
            "你是一位专业的法律文书撰写专家。"
        )
        user_content = f"【案件信息】\n{case_info}\n\n"
        if specific_requirements:
            user_content += f"【特殊要求】\n{specific_requirements}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        return self.llm.chat(messages, model="qwen-plus")

    def generate_plaint(self, case_info: str, claims: str = "") -> str:
        """生成起诉状"""
        reqs = f"诉讼请求：{claims}" if claims else ""
        return self.generate("起诉状", case_info, reqs)

    def generate_defense(self, case_info: str, plaint_content: str = "") -> str:
        """生成答辩状"""
        reqs = f"原告起诉内容：{plaint_content}" if plaint_content else ""
        return self.generate("答辩状", case_info, reqs)

    def generate_agent_letter(
        self,
        case_info: str,
        trial_summary: str = ""
    ) -> str:
        """生成代理词"""
        reqs = f"庭审情况：{trial_summary}" if trial_summary else ""
        return self.generate("代理词", case_info, reqs)

    def generate_appeal(
        self,
        case_info: str,
        first_instance_judgment: str = ""
    ) -> str:
        """生成上诉状"""
        reqs = f"一审判决：{first_instance_judgment}" if first_instance_judgment else ""
        return self.generate("上诉状", case_info, reqs)

    @property
    def available_types(self) -> List[str]:
        """支持的文书类型列表"""
        return list(self.DOCUMENT_TEMPLATES.keys())


# 单例
legal_doc_service = LegalDocService()
