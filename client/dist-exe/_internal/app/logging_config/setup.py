"""
结构化日志配置模块

提供统一的 JSON 格式日志输出，便于日志收集和分析。
支持控制台输出和文件输出两种模式。
"""
import structlog
import logging
import sys
import os
from typing import Any
from logging.handlers import RotatingFileHandler

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件路径
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error.log")
ACCESS_LOG_FILE = os.path.join(LOG_DIR, "access.log")


def add_app_info(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any]
) -> dict[str, Any]:
    """添加应用上下文信息"""
    event_dict["app"] = "legal-ai-assistant"
    event_dict["environment"] = os.environ.get("APP_ENV", "development")
    return event_dict


def add_timestamp(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any]
) -> dict[str, Any]:
    """添加 ISO 格式时间戳"""
    from datetime import datetime
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_request_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any]
) -> dict[str, Any]:
    """添加请求追踪 ID"""
    import uuid
    if "request_id" not in event_dict:
        event_dict["request_id"] = str(uuid.uuid4())[:8]
    return event_dict


def setup_logging(log_level: str = None) -> None:
    """
    配置结构化日志系统

    Args:
        log_level: 日志级别，默认从环境变量 LOG_LEVEL 读取
    """
    # 获取日志级别
    if log_level is None:
        log_level = os.environ.get("LOG_LEVEL", "INFO")

    # 获取处理器列表
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_app_info,
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ]

    # 配置 structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 根日志配置
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器（开发环境）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    root_logger.addHandler(console_handler)

    # JSON 文件处理器（生产环境）
    if os.environ.get("APP_ENV") == "production":
        # 应用日志
        file_handler = RotatingFileHandler(
            APP_LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
                foreign_pre_chain=processors[:-2],  # 排除最后的 JSON 渲染器
            )
        )
        root_logger.addHandler(file_handler)

        # 错误日志
        error_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
                foreign_pre_chain=processors[:-2],
            )
        )
        root_logger.addHandler(error_handler)

        # 访问日志
        access_logger = logging.getLogger("access")
        access_logger.setLevel(logging.INFO)
        access_handler = RotatingFileHandler(
            ACCESS_LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8"
        )
        access_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
                foreign_pre_chain=processors[:-2],
            )
        )
        access_logger.addHandler(access_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    获取结构化日志记录器

    Args:
        name: 日志记录器名称，通常使用模块名

    Returns:
        结构化日志记录器实例
    """
    return structlog.get_logger(name)


# 访问日志记录器
access_logger = get_logger("access")


def log_access(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client_ip: str,
    user_agent: str = None,
    user_id: str = None
) -> None:
    """
    记录 API 访问日志

    Args:
        method: HTTP 方法
        path: 请求路径
        status_code: 响应状态码
        duration_ms: 请求耗时（毫秒）
        client_ip: 客户端 IP
        user_agent: 用户代理字符串
        user_id: 用户 ID（如果已认证）
    """
    access_logger.info(
        "api_access",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
        client_ip=client_ip,
        user_agent=user_agent,
        user_id=user_id
    )


# 初始化默认日志配置（开发环境）
setup_logging()
