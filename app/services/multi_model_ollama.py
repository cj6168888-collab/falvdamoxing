"""
增强版 Ollama 服务 - 支持多模型管理和智能路由
"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ModelPurpose(str, Enum):
    """模型用途分类"""
    LEGAL = "legal"           # 法律专项任务
    GENERAL = "general"       # 通用推理任务
    FAST = "fast"             # 快速响应
    EMBEDDING = "embedding"    # 向量嵌入


@dataclass
class ModelConfig:
    """单个模型的配置"""
    name: str                           # Ollama 中的模型名
    purpose: ModelPurpose               # 用途分类
    ollama_url: str                    # Ollama 服务地址
    temperature: float = 0.3            # 默认温度
    max_tokens: int = 8192             # 最大 token 数
    timeout: int = 180                  # 超时秒数
    enabled: bool = True                # 是否启用
    description: str = ""               # 模型描述


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    latency: float
    tokens_used: Optional[int] = None
    purpose: ModelPurpose = ModelPurpose.GENERAL


class MultiModelOllamaService:
    """
    多模型 Ollama 服务

    支持同时管理多个本地模型，按用途智能选择：
    - 法律专项模型 (LegalOne-R1, DISC-LawLLM)
    - 通用推理模型 (DeepSeek-R1, Qwen2.5)
    - 快速响应模型 (qwen2.5:7b)
    """

    # 默认模型配置（在 D:/www/法律大模型/ 下存储配置）
    DEFAULT_MODELS: List[ModelConfig] = [
        ModelConfig(
            name="legalone-r1:8b",
            purpose=ModelPurpose.LEGAL,
            ollama_url="http://localhost:11434",
            temperature=0.3,
            max_tokens=8192,
            timeout=300,
            enabled=True,
            description="LegalOne-R1 8B - 清华法律专项推理模型（推荐）",
        ),
        ModelConfig(
            name="legalone-r1:4b",
            purpose=ModelPurpose.LEGAL,
            ollama_url="http://localhost:11434",
            temperature=0.3,
            max_tokens=4096,
            timeout=180,
            enabled=True,
            description="LegalOne-R1 4B - 轻量级法律模型（RTX 3060 可用）",
        ),
        ModelConfig(
            name="qwen2.5:14b",
            purpose=ModelPurpose.GENERAL,
            ollama_url="http://localhost:11434",
            temperature=0.7,
            max_tokens=16384,
            timeout=240,
            enabled=True,
            description="Qwen2.5 14B - 通用推理（长文本分析）",
        ),
        ModelConfig(
            name="qwen2.5:7b",
            purpose=ModelPurpose.FAST,
            ollama_url="http://localhost:11434",
            temperature=0.5,
            max_tokens=4096,
            timeout=120,
            enabled=True,
            description="Qwen2.5 7B - 快速响应场景",
        ),
    ]

    def __init__(self, config_override: Optional[List[ModelConfig]] = None):
        self.models: Dict[ModelPurpose, ModelConfig] = {}
        self._health_cache: Dict[str, tuple[bool, float]] = {}

        for mc in (config_override or self.DEFAULT_MODELS):
            if mc.enabled:
                self.models[mc.purpose] = mc

    def get_model(self, purpose: ModelPurpose) -> Optional[ModelConfig]:
        """获取指定用途的模型配置"""
        return self.models.get(purpose)

    def get_legal_model(self) -> Optional[ModelConfig]:
        """获取法律专项模型（优先 8B，其次 4B）"""
        if ModelPurpose.LEGAL in self.models:
            return self.models[ModelPurpose.LEGAL]
        return None

    def _is_available(self, base_url: str, cache_seconds: int = 5) -> bool:
        """检查 Ollama 服务是否可用（带缓存）"""
        current_time = time.time()
        if base_url in self._health_cache:
            available, cached_at = self._health_cache[base_url]
            if current_time - cached_at < cache_seconds:
                return available

        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{base_url}/api/tags")
                available = resp.status_code == 200
        except Exception:
            available = False

        self._health_cache[base_url] = (available, current_time)
        return available

    async def is_available(self) -> bool:
        """检查主服务是否可用"""
        if not self.models:
            return False
        primary = next(iter(self.models.values()))
        return self._is_available(primary.ollama_url)

    async def list_installed_models(self) -> List[Dict[str, Any]]:
        """列出 Ollama 中已安装的模型"""
        if not self.models:
            return []
        primary = next(iter(self.models.values()))
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{primary.ollama_url}/api/tags")
                if resp.status_code == 200:
                    return resp.json().get("models", [])
        except Exception as e:
            logger.error(f"列出模型失败: {e}")
        return []

    async def pull_model(self, model_name: str, base_url: str = "http://localhost:11434") -> bool:
        """
        拉取模型（流式输出日志）

        LegalOne-R1 8B 约 5-8GB，4B 约 2.5GB
        Disc-LawLLM 7B 约 4GB
        建议确保磁盘空间 > 15GB
        """
        logger.info(f"开始拉取模型: {model_name} (预计需要 5-15 分钟)")
        try:
            async with httpx.AsyncClient(timeout=3600) as client:
                async with client.stream(
                    "POST",
                    f"{base_url}/api/pull",
                    json={"name": model_name}
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            import json
                            try:
                                data = json.loads(line)
                                status = data.get("status", "")
                                if status == "pulling manifest":
                                    logger.info(f"[Pull] 拉取中: {model_name}")
                                elif "progress" in data:
                                    total = data.get("total", 0)
                                    completed = data.get("completed", 0)
                                    if total > 0:
                                        pct = completed / total * 100
                                        logger.info(f"[Pull] {model_name}: {pct:.1f}%")
                                else:
                                    logger.info(f"[Pull] {status}")
                            except json.JSONDecodeError:
                                logger.info(f"[Pull] {line}")
            logger.info(f"模型拉取完成: {model_name}")
            self._health_cache.clear()
            return True
        except Exception as e:
            logger.error(f"拉取模型失败: {e}")
            return False

    async def chat(
        self,
        messages: List[Dict[str, str]],
        purpose: ModelPurpose = ModelPurpose.GENERAL,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """发送对话请求"""
        if model_name:
            mc = next(
                (m for m in self.models.values() if m.name == model_name),
                self.models.get(purpose)
            )
        else:
            mc = self.models.get(purpose)

        if not mc:
            return LLMResponse(
                content="错误：无可用模型",
                model="none",
                latency=0,
                purpose=purpose,
            )

        if not self._is_available(mc.ollama_url):
            return LLMResponse(
                content=f"错误：Ollama 服务不可用 ({mc.ollama_url})。请确保 Ollama 已启动。",
                model=mc.name,
                latency=0,
                purpose=purpose,
            )

        temp = temperature if temperature is not None else mc.temperature
        maxtk = max_tokens if max_tokens is not None else mc.max_tokens

        payload = {
            "model": mc.name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": maxtk,
                **kwargs
            }
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=mc.timeout) as client:
                resp = await client.post(
                    f"{mc.ollama_url}/api/chat",
                    json=payload
                )
                resp.raise_for_status()
                data = resp.json()

                latency = time.time() - start_time
                msg = data.get("message", {})
                content = msg.get("content", "") or ""
                thinking = msg.get("thinking", "") or ""
                if thinking and not content:
                    content = f"[思考]: {thinking[:500]}\n\n[回答]: (无内容)"

                return LLMResponse(
                    content=content,
                    model=mc.name,
                    latency=latency,
                    tokens_used=data.get("eval_count"),
                    purpose=mc.purpose,
                )
        except httpx.TimeoutException:
            return LLMResponse(
                content=f"错误：模型响应超时（{mc.timeout}秒）。请尝试更小的上下文或更短的 max_tokens。",
                model=mc.name,
                latency=time.time() - start_time,
                purpose=purpose,
            )
        except Exception as e:
            logger.error(f"Chat 请求失败: {e}")
            return LLMResponse(
                content=f"错误：请求失败 - {str(e)}",
                model=mc.name,
                latency=time.time() - start_time,
                purpose=purpose,
            )

    async def generate(
        self,
        prompt: str,
        purpose: ModelPurpose = ModelPurpose.GENERAL,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本"""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(
            messages=messages,
            purpose=purpose,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    def get_status(self) -> Dict[str, Any]:
        """获取所有模型状态"""
        status = {
            "services": {},
            "legal_model": None,
            "available_purposes": [],
        }
        for purpose, mc in self.models.items():
            available = self._is_available(mc.ollama_url)
            status["services"][mc.name] = {
                "url": mc.ollama_url,
                "available": available,
                "purpose": purpose.value,
                "description": mc.description,
            }
            if purpose == ModelPurpose.LEGAL:
                status["legal_model"] = mc.name

        status["available_purposes"] = [
            p.value for p in self.models if self._is_available(self.models[p].ollama_url)
        ]
        return status


# 全局单例
_multi_ollama: Optional[MultiModelOllamaService] = None


def get_multi_ollama() -> MultiModelOllamaService:
    global _multi_ollama
    if _multi_ollama is None:
        _multi_ollama = MultiModelOllamaService()
    return _multi_ollama
