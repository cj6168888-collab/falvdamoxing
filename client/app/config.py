from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Mapping, Optional
import os
from app.services.runtime_config import get_config_value


class Settings(BaseSettings):
    # 通义千问 API
    dashscope_api_key: str = ""
    dashscope_api_key_alias: str = ""  # 兼容别名

    # 数据库
    database_url: str = "sqlite:///./legal_system.db"
    db_pool_size: int = 20
    db_max_overflow: int = 40
    db_pool_timeout: int = 30
    db_pool_recycle_seconds: int = 1800
    db_pool_pre_ping: bool = True

    # 向量数据库
    chroma_persist_directory: str = "./data/chroma"

    # 文件存储
    file_storage_path: str = "./data/files"

    # 日志
    log_level: str = "INFO"
    app_env: str = "development"

    # API 配置
    api_title: str = "法律大模型辅助系统 API"
    api_version: str = "1.0.0"

    # 文件上传限制（单位：MB）- 不限制大小，支持大型法律文档
    max_file_size_mb: int = 500  # 500MB，足够处理任何法律文档

    # JWT 认证
    jwt_secret: str = ""  # 生产环境必须设置，建议: openssl rand -hex 32
    auth_context_cache_seconds: int = 10

    # 短信验证码
    sms_provider: str = "console"  # console / http
    sms_http_endpoint: str = ""
    sms_http_token: str = ""
    sms_code_ttl_minutes: int = 5
    sms_code_length: int = 6
    sms_code_resend_seconds: int = 60
    sms_code_max_attempts: int = 5
    sms_debug_return_code: Optional[bool] = None

    auto_create_tables: Optional[bool] = None

    def get_api_key(self) -> str:
        """获取API密钥，支持多种环境变量名"""
        return (
            get_config_value("DASHSCOPE_API_KEY")
            or get_config_value("DASHSCOPE_API_KEY_ALIAS")
            or self.dashscope_api_key
            or self.dashscope_api_key_alias
            or ""
        )

    model_config = SettingsConfigDict(
        env_file=".env.legal",
        case_sensitive=False,
        extra="allow",
    )


settings = Settings()


_PLACEHOLDER_TOKENS = (
    "change_me",
    "your_",
    "your-",
    "example.com",
    "your-domain.com",
)


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return not lowered or any(token in lowered for token in _PLACEHOLDER_TOKENS)


def _parse_positive_int(
    env: Mapping[str, str],
    name: str,
    errors: list[str],
    *,
    default: Optional[int] = None,
    minimum: int = 1,
) -> Optional[int]:
    raw_value = env.get(name)
    if raw_value is None or raw_value == "":
        return default
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        errors.append(f"{name} must be set to an integer in production")
        return default
    if parsed < minimum:
        errors.append(f"{name} must be at least {minimum} in production")
    return parsed


def validate_production_settings(
    settings_obj: Settings = settings,
    environ: Optional[Mapping[str, str]] = None,
) -> list[str]:
    """Return production configuration errors without affecting development."""
    env = environ or os.environ
    if settings_obj.app_env.lower() != "production":
        return []

    errors: list[str] = []
    required_values = {
        "DATABASE_URL": settings_obj.database_url,
        "JWT_SECRET": settings_obj.jwt_secret,
        "SECRET_KEY": env.get("SECRET_KEY", ""),
        "FILE_STORAGE_PATH": settings_obj.file_storage_path,
    }

    for name, value in required_values.items():
        if _is_placeholder(value):
            errors.append(f"{name} must be set to a non-placeholder value")

    if settings_obj.database_url.strip().lower().startswith("sqlite"):
        errors.append("DATABASE_URL must use PostgreSQL or another production database, not SQLite")

    cors_origins = env.get("CORS_ORIGINS", "")
    if _is_placeholder(cors_origins):
        errors.append("CORS_ORIGINS must be set to production origins")
    else:
        origins = [origin.strip().lower() for origin in cors_origins.split(",") if origin.strip()]
        if "*" in origins:
            errors.append("CORS_ORIGINS must not contain '*' in production")
        if any("localhost" in origin or "127.0.0.1" in origin for origin in origins):
            errors.append("CORS_ORIGINS must not contain localhost origins in production")

    use_redis = env.get("USE_REDIS_RATE_LIMIT", "").lower() in ("1", "true", "yes")
    if not use_redis:
        errors.append("USE_REDIS_RATE_LIMIT must be enabled in production")

    redis_url = env.get("REDIS_URL", "")
    redis_password = env.get("REDIS_PASSWORD", "")
    if _is_placeholder(redis_url):
        errors.append("REDIS_URL must be set when USE_REDIS_RATE_LIMIT is enabled")
    if _is_placeholder(redis_password):
        errors.append("REDIS_PASSWORD must be set when USE_REDIS_RATE_LIMIT is enabled")

    web_concurrency = _parse_positive_int(env, "WEB_CONCURRENCY", errors, minimum=2)

    if settings_obj.sms_provider.lower() != "http":
        errors.append("SMS_PROVIDER must be http in production")
    if _is_placeholder(settings_obj.sms_http_endpoint):
        errors.append("SMS_HTTP_ENDPOINT must be set when SMS_PROVIDER=http")
    if _is_placeholder(settings_obj.sms_http_token):
        errors.append("SMS_HTTP_TOKEN must be set when SMS_PROVIDER=http")
    if settings_obj.sms_debug_return_code is not False:
        errors.append("SMS_DEBUG_RETURN_CODE must be disabled in production")

    if settings_obj.db_pool_size <= 0:
        errors.append("DB_POOL_SIZE must be greater than 0")
    if settings_obj.db_max_overflow < 0:
        errors.append("DB_MAX_OVERFLOW must not be negative")
    if settings_obj.db_pool_timeout <= 0:
        errors.append("DB_POOL_TIMEOUT must be greater than 0")

    expected_app_replicas = _parse_positive_int(
        env,
        "EXPECTED_APP_REPLICAS",
        errors,
        default=1,
        minimum=1,
    )
    postgres_reserved_connections = _parse_positive_int(
        env,
        "POSTGRES_RESERVED_CONNECTIONS",
        errors,
        default=20,
        minimum=0,
    )
    postgres_max_connections = _parse_positive_int(
        env,
        "POSTGRES_MAX_CONNECTIONS",
        errors,
        minimum=1,
    )
    database_url = settings_obj.database_url.strip().lower()
    if database_url.startswith(("postgresql://", "postgres://")) and postgres_max_connections is None:
        errors.append("POSTGRES_MAX_CONNECTIONS must be set for production PostgreSQL deployments")

    if (
        web_concurrency is not None
        and expected_app_replicas is not None
        and postgres_reserved_connections is not None
        and postgres_max_connections is not None
        and settings_obj.db_pool_size > 0
        and settings_obj.db_max_overflow >= 0
    ):
        per_worker_connections = settings_obj.db_pool_size + settings_obj.db_max_overflow
        possible_app_connections = web_concurrency * expected_app_replicas * per_worker_connections
        usable_postgres_connections = postgres_max_connections - postgres_reserved_connections
        pgbouncer_enabled = env.get("PGBOUNCER_ENABLED", "").lower() in ("1", "true", "yes")
        if usable_postgres_connections <= 0:
            errors.append(
                "POSTGRES_MAX_CONNECTIONS must be greater than POSTGRES_RESERVED_CONNECTIONS"
            )
        elif pgbouncer_enabled:
            pgbouncer_max_client_conn = _parse_positive_int(
                env,
                "PGBOUNCER_MAX_CLIENT_CONN",
                errors,
                minimum=1,
            )
            pgbouncer_default_pool_size = _parse_positive_int(
                env,
                "PGBOUNCER_DEFAULT_POOL_SIZE",
                errors,
                minimum=1,
            )
            pgbouncer_reserve_pool_size = _parse_positive_int(
                env,
                "PGBOUNCER_RESERVE_POOL_SIZE",
                errors,
                default=0,
                minimum=0,
            )
            if (
                pgbouncer_max_client_conn is not None
                and possible_app_connections > pgbouncer_max_client_conn
            ):
                errors.append(
                    "PgBouncer client capacity is unsafe: "
                    f"WEB_CONCURRENCY({web_concurrency}) * "
                    f"EXPECTED_APP_REPLICAS({expected_app_replicas}) * "
                    f"(DB_POOL_SIZE + DB_MAX_OVERFLOW)({per_worker_connections}) = "
                    f"{possible_app_connections}, exceeding PGBOUNCER_MAX_CLIENT_CONN "
                    f"{pgbouncer_max_client_conn}"
                )
            if (
                pgbouncer_default_pool_size is not None
                and pgbouncer_reserve_pool_size is not None
            ):
                possible_server_connections = (
                    pgbouncer_default_pool_size + pgbouncer_reserve_pool_size
                )
                if possible_server_connections > usable_postgres_connections:
                    errors.append(
                        "PgBouncer server pool is unsafe: "
                        f"PGBOUNCER_DEFAULT_POOL_SIZE({pgbouncer_default_pool_size}) + "
                        f"PGBOUNCER_RESERVE_POOL_SIZE({pgbouncer_reserve_pool_size}) = "
                        f"{possible_server_connections}, exceeding available PostgreSQL "
                        f"connections {usable_postgres_connections}"
                    )
        elif possible_app_connections > usable_postgres_connections:
            errors.append(
                "DB connection capacity is unsafe: "
                f"WEB_CONCURRENCY({web_concurrency}) * "
                f"EXPECTED_APP_REPLICAS({expected_app_replicas}) * "
                f"(DB_POOL_SIZE + DB_MAX_OVERFLOW)({per_worker_connections}) = "
                f"{possible_app_connections}, exceeding available PostgreSQL connections "
                f"{usable_postgres_connections}"
            )

    return errors


def assert_production_settings(settings_obj: Settings = settings) -> None:
    errors = validate_production_settings(settings_obj)
    if errors:
        raise RuntimeError("Invalid production configuration: " + "; ".join(errors))


def should_auto_create_tables(
    settings_obj: Settings = settings,
    environ: Optional[Mapping[str, str]] = None,
) -> bool:
    env = environ or os.environ
    configured = env.get("AUTO_CREATE_TABLES")
    if configured is not None:
        return configured.strip().lower() in ("1", "true", "yes", "on")
    if settings_obj.auto_create_tables is not None:
        return settings_obj.auto_create_tables
    return settings_obj.app_env.lower() != "production"

# 确保目录存在
os.makedirs(settings.chroma_persist_directory, exist_ok=True)
os.makedirs(settings.file_storage_path, exist_ok=True)
os.makedirs("./data", exist_ok=True)
