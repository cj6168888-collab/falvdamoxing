"""
本地LLM服务 - Ollama封装
"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    content: str
    model: str
    latency: float
    tokens_used: Optional[int] = None

class OllamaService:
    """Ollama本地LLM服务封装"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "gemma4:e2b",
        timeout: int = 120
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._health_cache = None
        self._health_cache_time = 0
    
    async def is_available(self) -> bool:
        """检查服务是否可用"""
        import time
        current_time = time.time()
        
        # 缓存5秒
        if self._health_cache is not None and current_time - self._health_cache_time < 5:
            return self._health_cache
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                self._health_cache = response.status_code == 200
                self._health_cache_time = current_time
                return self._health_cache
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            self._health_cache = False
            self._health_cache_time = current_time
            return False
    
    async def list_models(self) -> List[str]:
        """列出可用模型"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []
    
    async def pull_model(self, model: str) -> bool:
        """拉取模型"""
        try:
            async with httpx.AsyncClient(timeout=3600) as client:  # 1小时超时
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/pull",
                    json={"name": model}
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            logger.info(f"Ollama pull: {line}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> LLMResponse:
        """发送对话请求"""
        import time
        start_time = time.time()
        
        model = model or self.model
        
        if model and "gemma" in model.lower():
            system_msg = {"role": "system", "content": "You are a helpful legal assistant. Answer directly without showing your thinking process. Use Chinese language."}
            if messages and messages[0].get("role") != "system":
                messages = [system_msg] + messages
            elif not messages:
                messages = [system_msg]
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            latency = time.time() - start_time
            message = data.get("message", {})
            content = message.get("content", "") or ""
            thinking = message.get("thinking", "") or ""
            if thinking and not content:
                content = "[思考过程]: " + thinking[:500]
            
            return LLMResponse(
                content=content,
                model=model,
                latency=latency,
                tokens_used=data.get("eval_count")
            )
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> LLMResponse:
        """生成文本"""
        import time
        start_time = time.time()
        
        model = model or self.model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            latency = time.time() - start_time
            
            return LLMResponse(
                content=data.get("response", ""),
                model=model,
                latency=latency,
                tokens_used=data.get("eval_count")
            )
    
    async def embeddings(self, text: str, model: Optional[str] = None) -> List[float]:
        """获取文本嵌入向量"""
        model = model or self.model
        
        payload = {
            "model": model,
            "prompt": text
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("embedding", [])
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "available": self._health_cache,
            "base_url": self.base_url,
            "model": self.model,
            "timeout": self.timeout
        }


# 全局单例
_ollama_service: Optional[OllamaService] = None

def get_ollama_service() -> OllamaService:
    """获取Ollama服务实例"""
    global _ollama_service
    if _ollama_service is None:
        import os
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
        _ollama_service = OllamaService(base_url=base_url, model=model)
    return _ollama_service
