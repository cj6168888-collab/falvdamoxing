"""
API Key 配置管理 API
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, Optional, List
import logging
from app.services.runtime_config import delete_config_value
from app.services.runtime_config import get_config_value
from app.services.runtime_config import read_runtime_config
from app.services.runtime_config import save_config_values

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/config", tags=["配置管理"])


class ApiKeyConfig(BaseModel):
    """API Key 配置项"""
    key: str
    value: str
    masked: bool = False  # 是否已掩码
    source: Optional[str] = None  # 申请来源地址


class ApiKeyConfigRequest(BaseModel):
    """API Key 配置请求"""
    configs: Dict[str, str]


class ApiKeyConfigResponse(BaseModel):
    """API Key 配置响应"""
    configs: Dict[str, str]
    sources: Dict[str, str] = {}
    total: int
    configured: int


class ApiKeyInfo(BaseModel):
    """API Key 信息"""
    key: str
    name: str
    description: str
    required: bool
    category: str
    has_value: bool
    masked_value: Optional[str] = None
    source: Optional[str] = None  # 申请来源地址


# API Key 配置定义
API_KEY_DEFINITIONS = {
    # 大模型配置
    "DASHSCOPE_API_KEY": {
        "name": "阿里云通义千问 API Key",
        "description": "用于调用通义千问大语言模型",
        "required": True,
        "category": "llm",
    },
    "OLLAMA_BASE_URL": {
        "name": "Ollama 服务地址",
        "description": "本地 Ollama 服务地址",
        "required": False,
        "category": "llm",
    },
    "OLLAMA_MODEL": {
        "name": "Ollama 模型名称",
        "description": "本地部署的大模型名称",
        "required": False,
        "category": "llm",
    },
    "LOCAL_EMBEDDING_MODEL": {
        "name": "本地 Embedding 模型",
        "description": "用于文本向量化的本地模型",
        "required": False,
        "category": "llm",
    },
    # 法律数据 API
    "LAW_API_KEY": {
        "name": "法研开放平台 API Key",
        "description": "用于裁判文书查询、律师信息检索",
        "required": False,
        "category": "law",
    },
    "BAITEN_API_KEY": {
        "name": "佰腾大数据 API Key",
        "description": "用于法律法规大数据检索",
        "required": False,
        "category": "law",
    },
    "YILIAN_API_KEY": {
        "name": "易连数据 API Key",
        "description": "用于司法综合数据查询",
        "required": False,
        "category": "law",
    },
    # 节假日 API
    "HOLIDAY_API_KEY": {
        "name": "节假日 API Key",
        "description": "用于法定期限计算",
        "required": False,
        "category": "calendar",
    },
    # 企业信息验证
    "COMPANY_INFO_API_BASE_URL": {
        "name": "企业工商信息 API 地址",
        "description": "用于企业工商信息查询的服务地址，例如 https://provider.example.com/api",
        "required": False,
        "category": "verification",
    },
    "COMPANY_INFO_API_KEY": {
        "name": "企业工商信息 API Key",
        "description": "用于企业名称、统一社会信用代码、法定代表人等工商信息查询",
        "required": False,
        "category": "verification",
    },
    "CLEARBIT_API_KEY": {
        "name": "Clearbit API Key",
        "description": "用于自动获取企业 Logo",
        "required": False,
        "category": "verification",
    },
    "NUMVERIFY_API_KEY": {
        "name": "Numverify API Key",
        "description": "用于电话号码验证",
        "required": False,
        "category": "verification",
    },
    "MAILBOX_VALIDATOR_API_KEY": {
        "name": "MailboxValidator API Key",
        "description": "用于邮箱地址验证",
        "required": False,
        "category": "verification",
    },
    # 工具类 API
    "PDFLAYER_API_KEY": {
        "name": "pdflayer API Key",
        "description": "用于文档转 PDF",
        "required": False,
        "category": "utility",
    },
    "OCR_SPACE_API_KEY": {
        "name": "OCR.space API Key",
        "description": "用于云端 OCR 文字识别",
        "required": False,
        "category": "utility",
    },
}


def mask_api_key(key: str) -> str:
    """掩码 API Key"""
    if not key or len(key) < 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def is_sensitive_key(key: str) -> bool:
    return key.endswith("_KEY") or key.endswith("_SECRET") or "TOKEN" in key


def display_config_value(key: str, value: str) -> str:
    if not value:
        return ""
    return mask_api_key(value) if is_sensitive_key(key) else value


def is_masked_value(value: str) -> bool:
    return "****" in value


@router.get("/api-keys", response_model=ApiKeyConfigResponse)
async def get_api_keys():
    """
    获取所有 API Key 配置状态（掩码形式）
    """
    configs: Dict[str, str] = {}
    sources: Dict[str, str] = {}
    configured = 0
    all_values = read_runtime_config()

    for key in API_KEY_DEFINITIONS.keys():
        value = all_values.get(key, "")
        source = all_values.get(f"{key}_SOURCE", "")
        if value:
            configs[key] = display_config_value(key, value)
            sources[key] = source
            configured += 1
        else:
            configs[key] = ""
            sources[key] = ""

    return ApiKeyConfigResponse(
        configs=configs,
        sources=sources,
        total=len(API_KEY_DEFINITIONS),
        configured=configured,
    )


@router.get("/api-keys/info")
async def get_api_key_info() -> List[ApiKeyInfo]:
    """
    获取所有 API Key 的详细信息
    """
    result = []
    all_values = read_runtime_config()
    for key, info in API_KEY_DEFINITIONS.items():
        value = all_values.get(key, "")
        source = all_values.get(f"{key}_SOURCE", "")
        result.append(ApiKeyInfo(
            key=key,
            name=info["name"],
            description=info["description"],
            required=info["required"],
            category=info["category"],
            has_value=bool(value),
            masked_value=display_config_value(key, value) if value else None,
            source=source or None,
        ))
    return result


@router.post("/api-keys")
async def save_api_keys(request: ApiKeyConfigRequest, req: Request):
    """
    保存 API Key 配置。

    配置会写入当前进程环境变量，并持久化到 data/config/api-keys.env。
    自动记录申请来源（域名/IP）。
    """
    try:
        saved = []
        updates = {}
        sources = {}
        # Detect source from request
        origin = req.headers.get("origin", "") or req.headers.get("referer", "")
        if not origin:
            origin = req.client.host if req.client else "unknown"
        for key, value in request.configs.items():
            if key in API_KEY_DEFINITIONS:
                if is_masked_value(value):
                    continue
                updates[key] = value
                sources[key] = origin[:500]

        if updates:
            saved = save_config_values(updates, sources=sources)
            for key in saved:
                logger.info(f"API Key 配置已更新: {key} (来源: {sources.get(key, '')})")

        return {
            "success": True,
            "message": f"成功保存 {len(saved)} 项配置",
            "saved_keys": saved,
        }
    except Exception as e:
        logger.error(f"保存 API Key 配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-keys/validate/{key}")
async def validate_api_key(key: str, value: str):
    """
    验证 API Key 是否有效
    """
    if key not in API_KEY_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"未知的 API Key: {key}")

    # 根据不同的 API Key 类型进行验证
    # 这里只是示例，实际应该调用相应的 API 进行验证

    # 模拟验证
    is_valid = bool(value and len(value) > 0)

    return {
        "key": key,
        "valid": is_valid,
        "message": "验证通过" if is_valid else "验证失败",
    }


@router.delete("/api-keys/{key}")
async def delete_api_key(key: str):
    """
    删除某个 API Key 配置
    """
    if key not in API_KEY_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"未知的 API Key: {key}")

    try:
        delete_config_value(key)
        logger.info(f"API Key 配置已删除: {key}")

        return {
            "success": True,
            "message": f"API Key 已删除: {key}",
        }
    except Exception as e:
        logger.error(f"删除 API Key 配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
