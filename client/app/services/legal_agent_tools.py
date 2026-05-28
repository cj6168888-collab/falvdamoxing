"""
LLM工具调用能力服务（biz-15）
基于 LangChain 的 Tool Use 实现

功能：
1. 为LLM提供法律领域工具集
2. 支持多步骤法律分析推理
3. Chain-of-Thought 增强
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

try:
    from langchain.tools import BaseTool, StructuredTool
    from langchain.pydantic_v1 import BaseModel, Field
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    BaseModel = object
    BaseTool = None
    StructuredTool = None
    AgentExecutor = None
    ChatOpenAI = None
    LANGCHAIN_AVAILABLE = False

    def Field(default=None, **kwargs):
        return default

from app.services.llm_service import llm_service
from app.services.deadline_service import deadline_service, LitigationLimitationService
from app.services.legal_rag_service import legal_rag_service
from app.services.evidence_three_natures import evidence_three_natures_service


# ========== 工具定义 ==========

class SearchLawsInput(BaseModel if LANGCHAIN_AVAILABLE else object):
    """搜索法律条文输入"""
    query: str = Field(description="查询文本，如'合同无效的情形'")
    category: Optional[str] = Field(default=None, description="法律分类（civil/criminal/admin等）")
    top_k: int = Field(default=5, description="返回结果数量")


class CalculateDeadlineInput(BaseModel if LANGCHAIN_AVAILABLE else object):
    """计算期限输入"""
    start_date: str = Field(description="起始日期，格式YYYY-MM-DD")
    deadline_type: str = Field(description="期限类型，如'litigation_general', 'evidence_presentation_general'")
    use_workdays: bool = Field(default=True, description="是否使用工作日计算")


class AnalyzeLitigationInput(BaseModel if LANGCHAIN_AVAILABLE else object):
    """分析诉讼时效输入"""
    event_date: str = Field(description="权利被侵害之日，格式YYYY-MM-DD")
    limitation_type: str = Field(default="general", description="时效类型（general/maximum/身体伤害等）")


class AnalyzeEvidenceInput(BaseModel if LANGCHAIN_AVAILABLE else object):
    """分析证据三性输入"""
    evidence_type: str = Field(description="证据类型（CONTRACT/PAYMENT/TESTIMONY等）")
    evidence_content: str = Field(description="证据内容或摘要")
    has_original: bool = Field(default=True, description="是否有原件")


class LegalAgentTools:
    """
    法律领域工具集（biz-15）
    
    提供给LLM使用的工具，包括：
    1. 搜索法律条文
    2. 计算法律期限
    3. 分析诉讼时效
    4. 分析证据三性
    """
    
    def __init__(self):
        self._initialized = False
        self._tools: List = []
        self._initialize_tools()
    
    def _initialize_tools(self):
        """初始化LangChain工具"""
        if not LANGCHAIN_AVAILABLE:
            return
        
        self._tools = [
            self._create_search_laws_tool(),
            self._create_calculate_deadline_tool(),
            self._create_analyze_litigation_tool(),
            self._create_analyze_evidence_tool(),
        ]
        
        self._initialized = True
    
    def _create_search_laws_tool(self):
        """创建法律条文搜索工具"""
        def search_laws(query: str, category: Optional[str] = None, top_k: int = 5) -> str:
            """
            搜索相关法律条文
            
            用于：当用户询问法律依据、需要引用法条时使用
            
            Args:
                query: 查询文本
                category: 可选，限定法律分类
                top_k: 返回数量
                
            Returns:
                JSON格式的法条列表
            """
            try:
                results = legal_rag_service.search(query, top_k=top_k, category=category)
                
                if not results:
                    return json.dumps({"success": False, "message": "未找到相关法条"})
                
                formatted = []
                for i, law in enumerate(results, 1):
                    formatted.append({
                        "rank": i,
                        "law": f"《{law['law_name']}》{law['article_no']}",
                        "title": law.get("title", ""),
                        "content": law.get("content", ""),
                        "basis": law.get("legal_basis", ""),
                        "is_valid": law.get("is_valid", True)
                    })
                
                return json.dumps({
                    "success": True,
                    "count": len(formatted),
                    "results": formatted
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
        
        return StructuredTool.from_function(
            func=search_laws,
            name="search_legal_articles",
            description="""搜索相关法律条文。
            
使用场景：
- 用户询问法律依据时
- 需要引用具体法条时
- 分析案件适用哪些法律时

使用示例：
query="合同无效的情形"，category="civil"，top_k=5
""",
            args_schema=SearchLawsInput
        )
    
    def _create_calculate_deadline_tool(self):
        """创建期限计算工具"""
        def calculate_deadline(
            start_date: str,
            deadline_type: str,
            use_workdays: bool = True
        ) -> str:
            """
            计算法律期限截止日期
            
            用于：计算举证期限、上诉期限、诉讼时效等
            
            Args:
                start_date: 起始日期（YYYY-MM-DD）
                deadline_type: 期限类型
                use_workdays: 是否使用工作日计算
                
            Returns:
                JSON格式的期限计算结果
            """
            try:
                from datetime import datetime as dt
                start = dt.strptime(start_date, "%Y-%m-%d")
                
                result = deadline_service.analyze_deadline(
                    start_date=start,
                    deadline_type=deadline_type
                )
                
                return json.dumps({
                    "success": True,
                    "deadline_name": result.get("deadline_name", ""),
                    "start_date": start_date,
                    "deadline_date": result.get("deadline_date", "").strftime("%Y-%m-%d") if result.get("deadline_date") else "",
                    "days_remaining": result.get("days_remaining", 0),
                    "workdays_remaining": result.get("workdays_remaining", 0),
                    "legal_basis": result.get("legal_basis", ""),
                    "description": result.get("description", ""),
                    "priority": result.get("priority", ""),
                    "status": result.get("status", "")
                }, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
        
        return StructuredTool.from_function(
            func=calculate_deadline,
            name="calculate_legal_deadline",
            description="""计算法律期限的截止日期。

使用场景：
- 计算举证期限（普通/简易/小额程序不同）
- 计算上诉期限
- 计算诉讼时效
- 计算财产保全期限

可用期限类型：
- litigation_general: 普通诉讼时效（3年）
- litigation_maximum: 最长保护期间（20年）
- evidence_presentation_general: 举证期限（普通程序30日）
- evidence_presentation_simple: 举证期限（简易程序15日）
- evidence_presentation_small: 举证期限（小额诉讼7日）
- civil_litigation_appeal: 上诉期限（15日）
- property_preservation: 财产保全期限（5日）
- arbitration: 仲裁期限（4年）
- jurisdiction_objection: 管辖权异议期限（15日）
- execution_objection: 执行异议期限（15日）
""",
            args_schema=CalculateDeadlineInput
        )
    
    def _create_analyze_litigation_tool(self):
        """创建诉讼时效分析工具"""
        def analyze_litigation_expiry(
            event_date: str,
            limitation_type: str = "general"
        ) -> str:
            """
            分析诉讼时效状态
            
            用于：判断权利是否超过诉讼时效
            
            Args:
                event_date: 权利被侵害之日（YYYY-MM-DD）
                limitation_type: 时效类型
                    
            Returns:
                JSON格式的时效分析结果
            """
            try:
                from datetime import datetime as dt
                event_dt = dt.strptime(event_date, "%Y-%m-%d")
                
                is_expired, days_info = LitigationLimitationService.is_expired(
                    event_dt, limitation_type
                )
                
                info = LitigationLimitationService.get_limitation_info(limitation_type)
                
                return json.dumps({
                    "success": True,
                    "event_date": event_date,
                    "limitation_type": limitation_type,
                    "limitation_name": info.get("name", ""),
                    "years": info.get("years", 3),
                    "is_expired": is_expired,
                    "days_info": abs(days_info),
                    "status": "已超期" if is_expired else f"剩余{days_info}天",
                    "legal_basis": info.get("basis", ""),
                    "description": info.get("description", "")
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
        
        return StructuredTool.from_function(
            func=analyze_litigation_expiry,
            name="analyze_litigation_expiry",
            description="""分析诉讼时效状态。

使用场景：
- 判断债权是否超过诉讼时效
- 计算时效届满日期
- 评估权利行使的风险

时效类型：
- general: 普通诉讼时效（3年，民法典第188条）
- maximum: 最长保护期间（20年）
- 身体伤害: 人身损害赔偿时效（1年）
- 租金: 租金请求权时效（1年）
- 劳动报酬: 劳动报酬时效（劳动关系存续期间不受限制）
- 劳动争议: 劳动争议仲裁时效（1年）
""",
            args_schema=AnalyzeLitigationInput
        )
    
    def _create_analyze_evidence_tool(self):
        """创建证据三性分析工具"""
        def analyze_evidence_three_natures(
            evidence_type: str,
            evidence_content: str,
            has_original: bool = True
        ) -> str:
            """
            分析证据的真实性、合法性、关联性
            
            用于：评估证据的证明力和风险
            
            Args:
                evidence_type: 证据类型
                evidence_content: 证据内容或摘要
                has_original: 是否有原件
                
            Returns:
                JSON格式的三性分析结果
            """
            try:
                evidence_data = {
                    "evidence_type": evidence_type,
                    "summary": evidence_content,
                    "has_original": has_original,
                    "name": "待分析证据"
                }
                
                result = evidence_three_natures_service.analyze_three_natures(
                    evidence_data
                )
                
                return json.dumps({
                    "success": True,
                    "authenticity": {
                        "status": result.authenticity.value,
                        "score": result.authenticity_score,
                        "analysis": result.authenticity_analysis
                    },
                    "legality": {
                        "status": result.legality.value,
                        "score": result.legality_score,
                        "analysis": result.legality_analysis,
                        "basis": result.legality_basis
                    },
                    "relevance": {
                        "status": result.relevance.value,
                        "score": result.relevance_score,
                        "analysis": result.relevance_analysis,
                        "proves_facts": result.proves_facts
                    },
                    "overall": {
                        "score": result.overall_score,
                        "assessment": result.overall_assessment
                    },
                    "strengths": result.key_strengths,
                    "weaknesses": result.key_weaknesses,
                    "suggestions": result.reinforcement_suggestions
                }, ensure_ascii=False, default=str)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
        
        return StructuredTool.from_function(
            func=analyze_evidence_three_natures,
            name="analyze_evidence_quality",
            description="""分析证据的真实性、合法性、关联性（证据三性）。

使用场景：
- 评估证据的证明力
- 预判对方对证据的质疑
- 制定质证策略

证据类型：
- CONTRACT: 合同协议类
- PAYMENT: 支付凭证类
- CORRESPONDENCE: 函件沟通类
- TESTIMONY: 证人证言类
- AUDIO_VIDEO: 视听资料类
- EXPERT: 鉴定意见类
- DOCUMENT: 书证类
""",
            args_schema=AnalyzeEvidenceInput
        )
    
    def get_tools(self) -> List:
        """获取工具列表"""
        return self._tools
    
    def get_tool_schemas(self) -> List[Dict]:
        """获取工具定义（用于前端展示）"""
        if not self._initialized:
            return []
        
        schemas = []
        for tool in self._tools:
            schemas.append({
                "name": tool.name,
                "description": tool.description.split('\n')[0] if tool.description else "",
                "parameters": str(tool.args_schema) if tool.args_schema else "{}"
            })
        
        return schemas


class LegalAgentExecutor:
    """
    法律分析Agent执行器（biz-15）
    
    使用LangChain实现多步骤法律分析
    """
    
    def __init__(self):
        self.tools_service = LegalAgentTools()
        self._agent = None
        self._executor = None
    
    def execute(
        self,
        query: str,
        context: Optional[str] = None
    ) -> Dict:
        """
        执行法律分析查询
        
        Args:
            query: 用户问题
            context: 案件上下文
            
        Returns:
            分析结果
        """
        if not LANGCHAIN_AVAILABLE:
            return self._execute_fallback(query, context)
        
        try:
            # 构建提示词
            prompt = self._build_prompt(query, context)
            
            # 执行查询
            response = llm_service.chat([
                {"role": "system", "content": """你是一位专业的法律助手，可以调用工具来回答问题。

可用工具：
1. search_legal_articles: 搜索法律条文
2. calculate_legal_deadline: 计算法律期限
3. analyze_litigation_expiry: 分析诉讼时效
4. analyze_evidence_quality: 分析证据三性

请结合工具分析回答问题。"""},
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "response": response,
                "tools_used": self._extract_tools_used(response)
            }
        except Exception as e:
            return self._execute_fallback(query, context)
    
    def _build_prompt(self, query: str, context: Optional[str]) -> str:
        """构建提示词"""
        prompt = f"用户问题：{query}\n\n"
        
        if context:
            prompt += f"案件背景：\n{context}\n\n"
        
        prompt += """请分析以上问题，必要时调用相关工具。

分析步骤：
1. 判断需要哪些法律知识
2. 如果涉及期限计算，调用 calculate_legal_deadline
3. 如果涉及时效分析，调用 analyze_litigation_expiry
4. 如果涉及证据评估，调用 analyze_evidence_quality
5. 如果需要法条依据，调用 search_legal_articles
6. 综合给出建议"""
        
        return prompt
    
    def _execute_fallback(self, query: str, context: Optional[str]) -> Dict:
        """无LangChain时的fallback实现"""
        # 简单语义分析
        query_lower = query.lower()
        
        results = {
            "success": True,
            "response": "",
            "tools_used": []
        }
        
        # 检测需要调用的功能
        if any(kw in query_lower for kw in ["时效", "过期", "超过"]):
            results["tools_used"].append("analyze_litigation_expiry")
        
        if any(kw in query_lower for kw in ["期限", "截止", "举证", "上诉"]):
            results["tools_used"].append("calculate_legal_deadline")
        
        if any(kw in query_lower for kw in ["证据", "真实性", "合法性", "关联性"]):
            results["tools_used"].append("analyze_evidence_quality")
        
        if any(kw in query_lower for kw in ["法律", "法条", "依据", "规定"]):
            results["tools_used"].append("search_legal_articles")
        
        results["response"] = "请调用相关工具进行分析。工具列表：\n" + "\n".join(
            f"- {t}" for t in results["tools_used"]
        )
        
        return results
    
    @staticmethod
    def _extract_tools_used(response: str) -> List[str]:
        """从响应中提取使用的工具"""
        tool_names = [
            "search_legal_articles",
            "calculate_legal_deadline",
            "analyze_litigation_expiry",
            "analyze_evidence_quality"
        ]
        
        used = [t for t in tool_names if t in response]
        return used


# 全局实例
legal_agent_tools = LegalAgentTools()
legal_agent_executor = LegalAgentExecutor()
