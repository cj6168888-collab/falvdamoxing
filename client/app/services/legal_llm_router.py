"""
智能 LLM 路由服务 - 根据任务类型自动选择最佳模型
"""
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import re

from app.services.multi_model_ollama import (
    MultiModelOllamaService, get_multi_ollama, ModelPurpose, LLMResponse
)
from app.services.llm_service import LLMService
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TaskClassification:
    """任务分类结果"""
    purpose: ModelPurpose          # 模型用途
    confidence: float             # 置信度 0-1
    reasoning: str                # 分类理由
    requires_legal_model: bool    # 是否需要法律专项模型


class TaskRouter:
    """
    智能任务路由

    分析用户请求，判断任务类型，自动路由到最合适的模型：
    - 法律专项模型：法律推理、条文引用、判决预测、诉讼策略
    - 通用推理模型：长文本分析、复杂推理、文书生成
    - 快速模型：简单问答、格式化输出
    - 云端降级：本地模型不可用时的兜底
    """

    # 法律专项关键词（优先级高）
    LEGAL_KEYWORDS = [
        # 法律领域
        "法律", "法条", "法律分析", "法律推理", "法律咨询", "法律意见",
        "诉讼", "仲裁", "调解", "判决", "裁定", "裁决",
        "合同", "协议", "条款", "违约", "侵权", "赔偿",
        "民事", "刑事", "行政", "商事",
        "原告", "被告", "第三人", "上诉人", "被上诉人",
        "证据", "举证", "质证", "证人", "鉴定",
        "代理", "授权", "委托",
        "法院", "法官", "律师", "当事人",
        "立案", "开庭", "审理", "执行",
        "追诉", "时效", "期限", "管辖",
        "权利", "义务", "责任",
        # 法律文书
        "起诉状", "答辩状", "上诉状", "申诉状",
        "代理词", "辩护词", "法律意见书",
        "律师函", "催告函", "告知函",
        "调解协议", "和解协议",
        # 法律分析
        "案件分析", "法律分析", "风险评估", "诉讼策略",
        "法律关系", "构成要件", "举证责任",
        "胜诉", "败诉", "胜率",
    ]

    # 通用推理关键词（优先级中）
    GENERAL_KEYWORDS = [
        "分析", "解释", "总结", "概括", "对比",
        "推理", "论证", "评估", "建议",
        "阅读", "理解", "提取", "整理",
        "比较", "判断", "预测", "推算",
        "改写", "润色", "翻译", "扩写",
    ]

    def __init__(self):
        self._ollama = get_multi_ollama()
        self._cloud = LLMService()

    def classify_task(self, query: str, context: Optional[Dict] = None) -> TaskClassification:
        """
        分析任务类型

        Args:
            query: 用户查询
            context: 额外上下文（案件类型、证据内容等）

        Returns:
            TaskClassification 包含用途、置信度和理由
        """
        query_lower = query.lower()
        query_no_punct = re.sub(r"[^\w]", "", query_lower)

        legal_score = 0
        general_score = 0

        for kw in self.LEGAL_KEYWORDS:
            if kw in query_lower or kw in query_no_punct:
                legal_score += 1

        for kw in self.GENERAL_KEYWORDS:
            if kw in query_lower or kw in query_no_punct:
                general_score += 1

        # 上下文强化
        if context:
            if context.get("case_type"):
                legal_score += 2
            if context.get("has_evidence"):
                legal_score += 1
            if context.get("document_type") in ["contract", "agreement", "letter"]:
                legal_score += 1

        total = legal_score + general_score
        if total == 0:
            return TaskClassification(
                purpose=ModelPurpose.FAST,
                confidence=0.5,
                reasoning="无法判断任务类型，使用快速模型",
                requires_legal_model=False,
            )

        legal_pct = legal_score / total

        if legal_pct >= 0.4:
            return TaskClassification(
                purpose=ModelPurpose.LEGAL,
                confidence=min(legal_pct * 1.5, 0.95),
                reasoning=f"法律关键词命中 {legal_score} 次，通用 {general_score} 次",
                requires_legal_model=True,
            )
        elif general_score > legal_score:
            return TaskClassification(
                purpose=ModelPurpose.GENERAL,
                confidence=min(general_score * 0.3, 0.8),
                reasoning=f"通用关键词命中 {general_score} 次，法律 {legal_score} 次",
                requires_legal_model=False,
            )
        else:
            return TaskClassification(
                purpose=ModelPurpose.FAST,
                confidence=0.6,
                reasoning="任务类型不明显，使用快速模型",
                requires_legal_model=False,
            )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        query: str = "",
        context: Optional[Dict] = None,
        prefer_legal: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        智能聊天路由

        1. 分析任务类型
        2. 尝试本地模型
        3. 不可用时降级到云端
        """
        classification = self.classify_task(query, context)
        logger.info(
            f"[LLMRouter] 任务分类: purpose={classification.purpose.value}, "
            f"confidence={classification.confidence:.2f}, reason={classification.reasoning}"
        )

        # 强制使用法律模型
        if prefer_legal:
            classification.purpose = ModelPurpose.LEGAL
            classification.requires_legal_model = True

        # 优先尝试本地模型
        local_resp = await self._try_local(messages, classification, **kwargs)
        if local_resp and local_resp.content and not local_resp.content.startswith("错误"):
            return local_resp

        # 降级到云端
        logger.info("[LLMRouter] 本地模型不可用，降级到云端 DashScope")
        return await self._fallback_cloud(messages, classification, **kwargs)

    async def _try_local(
        self,
        messages: List[Dict[str, str]],
        classification: TaskClassification,
        **kwargs
    ) -> Optional[LLMResponse]:
        """尝试本地模型"""
        mc = self._ollama.get_model(classification.purpose)
        if not mc:
            if classification.requires_legal_model:
                mc = self._ollama.get_legal_model()
                if not mc:
                    return None
                classification.purpose = ModelPurpose.LEGAL
            else:
                return None

        return await self._ollama.chat(messages, purpose=classification.purpose, **kwargs)

    async def _fallback_cloud(
        self,
        messages: List[Dict[str, str]],
        classification: TaskClassification,
        **kwargs
    ) -> LLMResponse:
        """云端降级（DashScope 通义千问）"""
        import time
        start = time.time()

        api_key = settings.get_api_key()
        if not api_key:
            return LLMResponse(
                content="错误：本地模型不可用，且未配置 DashScope API Key",
                model="none",
                latency=0,
                purpose=classification.purpose,
            )

        try:
            content = self._cloud.chat(
                messages=messages,
                model="qwen-plus",
                temperature=kwargs.get("temperature", 0.3),
            )
            return LLMResponse(
                content=content,
                model="qwen-plus",
                latency=time.time() - start,
                purpose=ModelPurpose.GENERAL,
            )
        except Exception as e:
            logger.error(f"云端降级失败: {e}")
            return LLMResponse(
                content=f"错误：所有模型均不可用 - {str(e)}",
                model="dashscope",
                latency=time.time() - start,
                purpose=classification.purpose,
            )

    async def legal_analysis(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """
        法律分析专用路由（强制使用法律模型）

        直接路由到 LegalOne-R1 或等效法律专项模型
        """
        return await self.chat(
            messages=messages,
            query=messages[-1]["content"] if messages else "",
            prefer_legal=True,
            **kwargs
        )


# 全局单例
_task_router: Optional[TaskRouter] = None


def get_task_router() -> TaskRouter:
    global _task_router
    if _task_router is None:
        _task_router = TaskRouter()
    return _task_router
