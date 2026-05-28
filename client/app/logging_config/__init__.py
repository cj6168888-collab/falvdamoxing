"""
app/logging_config/__init__.py
日志配置模块
"""
from .setup import setup_logging, get_logger, log_access, access_logger

__all__ = [
    "setup_logging",
    "get_logger",
    "log_access",
    "access_logger",
]
