"""
Redis 限流器
=============
基于 Redis 的分布式限流实现，支持：
1. 滑动窗口算法（精确限流）
2. 多维度限流（IP / 用户 / API Key）
3. 自动降级（Redis 不可用时回退到内存限流）

使用方法：
    # 开发/单实例：使用内存限流（默认）
    rate_limiter = InMemoryRateLimiter()

    # 生产/多实例：使用 Redis 限流
    rate_limiter = RedisRateLimiter(redis_url="redis://localhost:6379/0")
"""

import os
import time
import threading
from itertools import count
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Tuple
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


_REDIS_RATE_LIMIT_SCRIPT = """
local minute_key = KEYS[1]
local hour_key = KEYS[2]
local now_ms = tonumber(ARGV[1])
local rpm = tonumber(ARGV[2])
local rph = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZREMRANGEBYSCORE', minute_key, 0, now_ms - 60000)
redis.call('ZREMRANGEBYSCORE', hour_key, 0, now_ms - 3600000)

local minute_count = redis.call('ZCARD', minute_key)
if minute_count >= rpm then
    return {0, 1}
end

local hour_count = redis.call('ZCARD', hour_key)
if hour_count >= rph then
    return {0, 2}
end

redis.call('ZADD', minute_key, now_ms, member)
redis.call('EXPIRE', minute_key, 120)
redis.call('ZADD', hour_key, now_ms, member)
redis.call('EXPIRE', hour_key, 3700)

return {1, 0}
"""
_RATE_LIMIT_MEMBER_COUNTER = count()


# ==================== 接口定义 ====================

class BaseRateLimiter:
    """限流器基类"""

    def __init__(self, rpm: int = 600, rph: int = 10000):
        self.rpm = rpm
        self.rph = rph

    def is_allowed(self, client_id: str) -> Tuple[bool, str]:
        """
        检查是否允许请求

        Args:
            client_id: 客户端标识（通常是 IP + User-Agent 哈希）

        Returns:
            (是否允许, 拒绝消息)
        """
        raise NotImplementedError

    def record_request(self, client_id: str) -> None:
        """记录一次请求"""
        raise NotImplementedError

    def reset(self, client_id: str) -> None:
        """重置某个客户端的限流状态"""
        raise NotImplementedError


# ==================== 内存限流器（单实例） ====================

class InMemoryRateLimiter(BaseRateLimiter):
    """
    简单的内存限流器（单实例内有效）

    适用于：开发环境、单实例部署
    不适用于：多实例/容器化部署（请使用 RedisRateLimiter）
    """

    def __init__(self, rpm: int = 600, rph: int = 10000):
        super().__init__(rpm, rph)
        self._minute: dict[str, list[datetime]] = defaultdict(list)
        self._hour: dict[str, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, client_id: str) -> Tuple[bool, str]:
        now = datetime.now()
        cutoff_minute = now - timedelta(minutes=1)
        cutoff_hour = now - timedelta(hours=1)

        with self._lock:
            # 清理过期记录
            self._minute[client_id] = [t for t in self._minute[client_id] if t > cutoff_minute]
            self._hour[client_id] = [t for t in self._hour[client_id] if t > cutoff_hour]

            # 检查每分钟限制
            if len(self._minute[client_id]) >= self.rpm:
                return False, "请求过于频繁，请稍后再试（1分钟内限制）"
            # 检查每小时限制
            if len(self._hour[client_id]) >= self.rph:
                return False, "请求过于频繁，请稍后再试（1小时内限制）"

            # 记录本次请求
            self._minute[client_id].append(now)
            self._hour[client_id].append(now)
            return True, ""

    def record_request(self, client_id: str) -> None:
        """内存版无额外操作（is_allowed 已包含记录）"""
        pass

    def reset(self, client_id: str) -> None:
        with self._lock:
            self._minute.pop(client_id, None)
            self._hour.pop(client_id, None)


# ==================== Redis 限流器（分布式） ====================

class RedisRateLimiter(BaseRateLimiter):
    """
    基于 Redis 的分布式限流器

    算法：滑动窗口日志（Sliding Window Log）
    - 使用 Redis ZSET 存储时间戳，精确计数
    - 自动过期清理，无需额外维护线程

    适用于：多实例/容器化/Kubernetes 部署
    """

    def __init__(
        self,
        rpm: int = 60,
        rph: int = 1000,
        redis_url: Optional[str] = None,
        redis_password: Optional[str] = None,
        redis_db: int = 0,
        allow_fallback: bool = True,
    ):
        super().__init__(rpm, rph)

        self._redis_url = redis_url
        self._redis_password = redis_password
        self._redis_db = redis_db
        self._allow_fallback = allow_fallback
        self._client: Optional[redis.Redis] = None
        self._rate_limit_script: Optional[object] = None
        self._fallback = InMemoryRateLimiter(rpm, rph)
        self._use_fallback = False

        # 连接 Redis
        self._connect()

    def _connect(self) -> None:
        """连接 Redis"""
        if not REDIS_AVAILABLE:
            if not self._allow_fallback:
                raise RuntimeError("redis-py 未安装，生产限流不能降级到内存模式")
            print("[RateLimiter] redis-py 未安装，切换到内存限流模式")
            self._use_fallback = True
            return

        try:
            url = self._redis_url or os.environ.get(
                "REDIS_URL",
                os.environ.get("REDIS_URL_1", "redis://localhost:6379/0")
            )
            password = self._redis_password or os.environ.get("REDIS_PASSWORD")

            self._client = redis.from_url(
                url,
                password=password,
                db=self._redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # 测试连接
            self._client.ping()
            self._rate_limit_script = self._client.register_script(_REDIS_RATE_LIMIT_SCRIPT)
            self._use_fallback = False
            print(f"[RateLimiter] Redis 连接成功: {url}")
        except redis.ConnectionError as e:
            if not self._allow_fallback:
                raise RuntimeError(f"Redis 连接失败，生产限流不能降级到内存模式: {e}") from e
            print(f"[RateLimiter] Redis 连接失败: {e}，切换到内存限流模式")
            self._use_fallback = True
        except Exception as e:
            if not self._allow_fallback:
                raise RuntimeError(f"Redis 初始化失败，生产限流不能降级到内存模式: {e}") from e
            print(f"[RateLimiter] Redis 初始化失败: {e}，切换到内存限流模式")
            self._use_fallback = True

    def is_allowed(self, client_id: str) -> Tuple[bool, str]:
        """使用 Redis 滑动窗口日志算法检查限流"""
        if self._use_fallback or self._client is None:
            return self._fallback.is_allowed(client_id)

        now_ms = int(time.time() * 1000)
        minute_key = f"ratelimit:minute:{client_id}"
        hour_key = f"ratelimit:hour:{client_id}"
        member = f"{now_ms}:{next(_RATE_LIMIT_MEMBER_COUNTER)}"

        try:
            if self._rate_limit_script is None:
                self._rate_limit_script = self._client.register_script(_REDIS_RATE_LIMIT_SCRIPT)

            allowed, reason = self._rate_limit_script(
                keys=[minute_key, hour_key],
                args=[now_ms, self.rpm, self.rph, member],
            )

            if int(allowed) == 1:
                return True, ""
            if int(reason) == 1:
                return False, "请求过于频繁，请稍后再试（1分钟内限制）"
            if int(reason) == 2:
                return False, "请求过于频繁，请稍后再试（1小时内限制）"
            return False, "请求过于频繁，请稍后再试"

        except redis.RedisError as e:
            if not self._allow_fallback:
                return False, "限流服务暂不可用，请稍后再试"
            print(f"[RateLimiter] Redis 限流失败: {e}，切换到内存限流")
            self._use_fallback = True
            return self._fallback.is_allowed(client_id)

    def record_request(self, client_id: str) -> None:
        """记录请求（已合并到 is_allowed）"""
        pass

    def reset(self, client_id: str) -> None:
        """重置限流状态"""
        if self._use_fallback or self._client is None:
            self._fallback.reset(client_id)
            return

        try:
            pipe = self._client.pipeline()
            pipe.delete(f"ratelimit:minute:{client_id}")
            pipe.delete(f"ratelimit:hour:{client_id}")
            pipe.execute()
        except redis.RedisError:
            pass


# ==================== 工厂函数 ====================

def create_rate_limiter() -> BaseRateLimiter:
    """
    根据环境自动选择限流器

    优先级：
    1. 环境变量 USE_REDIS_RATE_LIMIT=1 → RedisRateLimiter
    2. 环境变量 REDIS_URL 已配置 → RedisRateLimiter
    3. 其他情况 → InMemoryRateLimiter
    """
    use_redis = os.environ.get("USE_REDIS_RATE_LIMIT", "").lower() in ("1", "true", "yes")
    redis_url = os.environ.get("REDIS_URL", "")
    app_env = os.environ.get("APP_ENV", "").lower()

    if use_redis or (redis_url and app_env == "production"):
        rpm = int(os.environ.get("RATE_LIMIT_RPM", "600"))
        rph = int(os.environ.get("RATE_LIMIT_RPH", "10000"))
        allow_fallback = os.environ.get("REDIS_RATE_LIMIT_ALLOW_FALLBACK", "").lower() in (
            "1",
            "true",
            "yes",
        )
        if app_env != "production" and not use_redis:
            allow_fallback = True
        return RedisRateLimiter(rpm=rpm, rph=rph, allow_fallback=allow_fallback)
    else:
        return InMemoryRateLimiter(
            rpm=int(os.environ.get("RATE_LIMIT_RPM", "600")),
            rph=int(os.environ.get("RATE_LIMIT_RPH", "10000")),
        )


# ==================== FastAPI 中间件兼容 ====================

class RateLimiterWrapper:
    """
    限流器包装器，兼容 FastAPI 中间件调用方式

    使用方式：
        limiter = create_rate_limiter()  # 或 RateLimiterWrapper() 自动选择
        allowed, msg = limiter.is_allowed(client_id)
    """

    def __init__(
        self,
        rpm: int = 60,
        rph: int = 1000,
        use_redis: bool = None
    ):
        if use_redis is None:
            use_redis = os.environ.get("APP_ENV") == "production"

        if use_redis and REDIS_AVAILABLE:
            self._limiter = RedisRateLimiter(rpm=rpm, rph=rph)
        else:
            self._limiter = InMemoryRateLimiter(rpm=rpm, rph=rph)

    def is_allowed(self, client_id: str) -> Tuple[bool, str]:
        return self._limiter.is_allowed(client_id)

    def reset(self, client_id: str) -> None:
        self._limiter.reset(client_id)


# 单例（延迟初始化）
_rate_limiter: Optional[BaseRateLimiter] = None


def get_rate_limiter() -> BaseRateLimiter:
    """获取限流器单例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = create_rate_limiter()
    return _rate_limiter
