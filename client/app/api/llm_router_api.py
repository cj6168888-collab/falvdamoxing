"""
LLM智能路由API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.ollama_service import get_ollama_service, OllamaService
from app.config import settings
from app.services.llm_service import LLMService
from app.services.llm_config import (
    TaskType, ModelType, get_routing_rule, 
    LOCAL_MODEL_CONFIG, CLOUD_MODEL_CONFIG
)

router = APIRouter(prefix="/api/llm", tags=["LLM路由"])

class GenerateRequest(BaseModel):
    task_type: str = "qa"
    content: str
    messages: Optional[List[Dict[str, str]]] = None
    force_model: Optional[str] = None  # 强制使用指定模型
    temperature: float = 0.7
    max_tokens: int = 2048

class GenerateResponse(BaseModel):
    content: str
    model: str
    model_type: str  # local/cloud/cache
    latency: float
    tokens_used: Optional[int] = None
    task_type: str
    cached: bool = False

class RouterStatus(BaseModel):
    status: str
    local_model: Dict[str, Any]
    cloud_model: Dict[str, Any]
    stats: Dict[str, Any]


def _cloud_api_key_set() -> bool:
    return bool(settings.get_api_key())


def _resolve_cloud_model(task_type: TaskType) -> str:
    if task_type in {TaskType.ADVERSARIAL, TaskType.PREDICTION, TaskType.JUDGE_PERSPECTIVE, TaskType.STRATEGY_SYNTHESIS, TaskType.WIN_PROBABILITY}:
        return "qwen-max"
    return "qwen-plus"


async def _generate_cloud_response(
    request: GenerateRequest,
    task_type: TaskType,
    start_time: float,
) -> GenerateResponse:
    if not _cloud_api_key_set():
        raise HTTPException(status_code=503, detail="Cloud model is not configured: DASHSCOPE_API_KEY is missing")

    messages = request.messages or [{"role": "user", "content": request.content}]
    model = _resolve_cloud_model(task_type)
    service = LLMService()
    content = service.chat(
        messages=messages,
        model=model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    unavailable_markers = (
        "错误：请先配置通义千问 API Key",
        "AI 服务暂时不可用",
        "请求出错",
    )
    if any(marker in content for marker in unavailable_markers):
        raise HTTPException(status_code=502, detail="Cloud model request failed")

    import time

    return GenerateResponse(
        content=content,
        model=model,
        model_type="cloud",
        latency=time.time() - start_time,
        tokens_used=None,
        task_type=request.task_type,
    )

async def _build_router_status() -> RouterStatus:
    """获取LLM路由状态"""
    ollama = get_ollama_service()
    
    local_available = await ollama.is_available()
    local_models = await ollama.list_models() if local_available else []
    
    cloud_available = _cloud_api_key_set()

    return RouterStatus(
        status="healthy" if local_available or cloud_available else "degraded",
        local_model={
            "available": local_available,
            "models": local_models,
            "default_model": LOCAL_MODEL_CONFIG.get("default_model"),
        },
        cloud_model={
            "available": cloud_available,
            "provider": CLOUD_MODEL_CONFIG.get("provider"),
            "api_key_env": CLOUD_MODEL_CONFIG.get("api_key_env"),
            "api_key_set": cloud_available,
            "default_model": CLOUD_MODEL_CONFIG.get("models", {}).get(CLOUD_MODEL_CONFIG.get("default_model"), {}).get("name"),
        },
        stats={
            "total_requests_24h": 0,
            "local_hit_rate": 0.0,
            "avg_response_time": 0.0,
        }
    )


@router.get("/status", response_model=RouterStatus)
async def get_router_status():
    """获取LLM路由状态"""
    return await _build_router_status()


@router.get("/router/status", response_model=RouterStatus)
async def get_router_status_compat():
    """兼容 API 文档中的 LLM 路由状态路径。"""
    return await _build_router_status()

@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """LLM生成接口"""
    import time
    import os
    
    start_time = time.time()
    
    # 解析任务类型
    try:
        task_type = TaskType(request.task_type)
    except ValueError:
        task_type = TaskType.QA
    
    # 获取路由规则
    rule = get_routing_rule(task_type)
    
    # 决定使用哪个模型
    use_local = True
    if request.force_model:
        use_local = request.force_model == "local"
    else:
        use_local = rule.primary_model == "local"
    
    ollama = get_ollama_service()
    model_type = "local"
    
    try:
        if use_local and await ollama.is_available():
            # 使用本地模型
            messages = request.messages or [{"role": "user", "content": request.content}]
            response = await ollama.chat(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            return GenerateResponse(
                content=response.content,
                model=response.model,
                model_type="local",
                latency=time.time() - start_time,
                tokens_used=response.tokens_used,
                task_type=request.task_type,
            )
        return await _generate_cloud_response(request, task_type, start_time)
            
    except HTTPException:
        raise
    except Exception as e:
        # 如果本地失败，尝试云端
        if use_local:
            return await _generate_cloud_response(request, task_type, start_time)
        
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")

@router.post("/chat", response_model=GenerateResponse)
async def chat(request: GenerateRequest):
    """LLM对话接口"""
    return await generate(request)

@router.get("/models")
async def list_models():
    """列出可用模型"""
    ollama = get_ollama_service()
    
    local_models = []
    if await ollama.is_available():
        local_models = await ollama.list_models()
    
    return {
        "local": local_models,
        "cloud": list(CLOUD_MODEL_CONFIG.get("models", {}).keys()),
    }

@router.post("/models/pull")
async def pull_model(model: str):
    """拉取模型"""
    ollama = get_ollama_service()
    
    if not await ollama.is_available():
        raise HTTPException(status_code=503, detail="Ollama service not available")
    
    # 检查模型是否已存在
    available_models = await ollama.list_models()
    if model in available_models:
        return {"status": "already_exists", "model": model}
    
    # 拉取模型
    success = await ollama.pull_model(model)
    if success:
        return {"status": "downloaded", "model": model}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to pull model: {model}")

@router.get("/health")
async def health_check():
    """健康检查"""
    ollama = get_ollama_service()
    available = await ollama.is_available()
    
    return {
        "status": "ok" if available else "degraded",
        "local_llm": available,
        "message": "Local LLM is running" if available else "Local LLM is not available"
    }
