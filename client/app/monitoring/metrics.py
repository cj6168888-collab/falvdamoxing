"""
Prometheus 指标收集模块

提供系统级和业务级指标，用于性能监控和告警。
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
from functools import wraps
from typing import Callable


# ==================== 系统级指标 ====================

# 应用信息
APP_INFO = Info("legal_ai", "法律大模型辅助系统信息")
APP_INFO.info({
    "version": "2.0.0",
    "environment": "production"
})

# API 请求计数
REQUEST_COUNT = Counter(
    "legal_ai_api_requests_total",
    "API 请求总数",
    ["method", "endpoint", "status_code"]
)

# API 请求延迟
REQUEST_LATENCY = Histogram(
    "legal_ai_api_request_duration_seconds",
    "API 请求延迟（秒）",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# LLM 调用计数
LLM_CALLS = Counter(
    "legal_ai_llm_calls_total",
    "LLM 调用总数",
    ["model", "call_type"]
)

# LLM 调用延迟
LLM_LATENCY = Histogram(
    "legal_ai_llm_call_duration_seconds",
    "LLM 调用延迟（秒）",
    ["model", "call_type"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0]
)

# LLM Token 使用
LLM_TOKENS = Counter(
    "legal_ai_llm_tokens_total",
    "LLM Token 使用总数",
    ["model", "token_type"]
)

# LLM 调用错误
LLM_ERRORS = Counter(
    "legal_ai_llm_errors_total",
    "LLM 调用错误总数",
    ["model", "error_type"]
)

# 数据库连接池
DB_POOL_SIZE = Gauge(
    "legal_ai_db_pool_size",
    "数据库连接池大小",
    ["pool_name"]
)

DB_POOL_CONNECTIONS = Gauge(
    "legal_ai_db_pool_connections",
    "数据库活跃连接数",
    ["pool_name", "state"]
)

# Redis 连接状态
REDIS_CONNECTIONS = Gauge(
    "legal_ai_redis_connections",
    "Redis 连接数",
    ["state"]
)

# 向量数据库指标
VECTOR_DB_OPERATIONS = Counter(
    "legal_ai_vector_db_operations_total",
    "向量数据库操作总数",
    ["operation", "collection"]
)

VECTOR_DB_LATENCY = Histogram(
    "legal_ai_vector_db_operation_duration_seconds",
    "向量数据库操作延迟（秒）",
    ["operation", "collection"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# 文件上传
FILE_UPLOADS = Counter(
    "legal_ai_file_uploads_total",
    "文件上传总数",
    ["file_type", "status"]
)

FILE_UPLOAD_SIZE = Histogram(
    "legal_ai_file_upload_size_bytes",
    "文件上传大小（字节）",
    ["file_type"],
    buckets=[1024, 10240, 102400, 1048576, 10485760, 52428800]  # 1KB - 50MB
)

# 案件相关指标
CASES_CREATED = Counter(
    "legal_ai_cases_created_total",
    "新建案件数",
    ["case_type"]
)

CASES_STATUS = Gauge(
    "legal_ai_cases_by_status",
    "各状态案件数",
    ["status"]
)

# 证据相关指标
EVIDENCE_SUBMITTED = Counter(
    "legal_ai_evidence_submitted_total",
    "证据提交数",
    ["evidence_type"]
)

# 期限预警
DEADLINE_ALERTS = Counter(
    "legal_ai_deadline_alerts_total",
    "期限预警数",
    ["alert_type", "urgency"]
)

# ==================== 辅助函数 ====================

def track_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """记录请求指标"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)


def track_llm_call(model: str, call_type: str, duration: float, tokens: int = None, error: str = None):
    """记录 LLM 调用指标"""
    if error:
        LLM_ERRORS.labels(model=model, error_type=error).inc()
        return

    LLM_CALLS.labels(model=model, call_type=call_type).inc()
    LLM_LATENCY.labels(model=model, call_type=call_type).observe(duration)

    if tokens:
        LLM_TOKENS.labels(model=model, token_type="total").inc(tokens)


def track_vector_operation(operation: str, collection: str, duration: float):
    """记录向量数据库操作指标"""
    VECTOR_DB_OPERATIONS.labels(operation=operation, collection=collection).inc()
    VECTOR_DB_LATENCY.labels(operation=operation, collection=collection).observe(duration)


def track_file_upload(file_type: str, status: str, size: int):
    """记录文件上传指标"""
    FILE_UPLOADS.labels(file_type=file_type, status=status).inc()
    FILE_UPLOAD_SIZE.labels(file_type=file_type).observe(size)


def get_metrics() -> Response:
    """获取 Prometheus 指标"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ==================== 装饰器 ====================

def monitor_endpoint(func: Callable) -> Callable:
    """API 端点监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            status_code = getattr(result, "status_code", 200)
            return result
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            # 从函数名提取端点路径
            endpoint = func.__name__
            track_request_metrics("POST", endpoint, status_code, duration)
    return wrapper


def monitor_llm(model: str, call_type: str = "inference"):
    """LLM 调用监控装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            tokens = None
            try:
                result = await func(*args, **kwargs)
                # 尝试从结果中提取 token 使用量
                if isinstance(result, dict) and "usage" in result:
                    tokens = result.get("usage", {}).get("total_tokens", 0)
                return result
            except Exception as e:
                error = type(e).__name__
                raise
            finally:
                duration = time.time() - start_time
                track_llm_call(model, call_type, duration, tokens, error)
        return wrapper
    return decorator
