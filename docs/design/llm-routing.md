# LLM智能路由设计文档

> 法律案件追踪系统 LLM ModelRouter 详细设计

---

## 一、概述

### 1.1 目的

ModelRouter 是系统的智能LLM路由组件，负责：
- 分析用户请求的任务类型
- 根据任务复杂度、模型能力、成本等因素选择最优模型
- 实现本地模型与云端模型的智能切换
- 提供降级策略保证服务可用性

### 1.2 设计目标

| 目标 | 指标 |
|------|------|
| 本地模型命中率 | >80% |
| 平均响应时间 | <3s |
| 服务可用性 | >99.5% |
| 成本优化 | 降低60%云端调用 |

---

## 二、路由策略

### 2.1 任务分类

| 任务类型 | 代码 | 复杂度 | 默认路由 | 说明 |
|----------|------|--------|----------|------|
| 文书初稿生成 | `doc_draft` | low | 本地 | 法律文书初稿 |
| 文书润色修改 | `doc_polish` | low | 本地 | 文书修改润色 |
| 合同格式审查 | `contract_review` | low | 本地 | 合同格式检查 |
| 案情摘要提取 | `case_summary` | medium | 本地 | 案件信息摘要 |
| 证据三性分析 | `evidence_analysis` | medium | 本地 | 证据分析 |
| 法条检索引用 | `law_retrieval` | medium | 本地 | 法条查询 |
| 智能问答 | `qa` | low | 本地 | 常规法律问答 |
| 术语解释 | `definition` | low | 本地 | 专业术语解释 |
| 抗辩建议生成 | `defense_suggest` | medium | 本地 | 抗辩建议 |
| **对抗性推演** | `adversarial` | high | 云端 | 复杂对抗分析 |
| **案件结果预测** | `prediction` | high | 云端 | 结果预测 |
| **法官视角评估** | `judge_perspective` | high | 云端 | 法官思维分析 |
| **策略综合合成** | `strategy_synthesis` | high | 云端 | 多策略整合 |
| **胜诉概率评估** | `win_probability` | high | 云端 | 胜诉评估 |

### 2.2 路由决策矩阵

```
┌─────────────────────────────────────────────────────────────────────┐
│                          路由决策流程                                 │
│                                                                      │
│  用户请求                                                              │
│     │                                                                  │
│     ▼                                                                  │
│  ┌──────────────┐                                                     │
│  │  任务分析     │  • 提取任务类型                                      │
│  │  TaskParser  │  • 评估复杂度                                        │
│  └──────┬───────┘  • 提取关键参数                                      │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────┐                                                     │
│  │  规则匹配     │  • 查表匹配路由规则                                  │
│  │  RuleMatch   │  • 考虑用户级别                                      │
│  └──────┬───────┘  • 考虑上下文                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────┐                                                     │
│  │  模型可用性   │  • 检查本地模型状态                                   │
│  │  ModelCheck  │  • 检查云端API配额                                    │
│  └──────┬───────┘  • 检查网络状况                                      │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────┐                                                     │
│  │  最终路由决策 │  • 优先级: 规则 > 可用性 > 成本                       │
│  │  RouteDecide │  • 记录路由原因                                       │
│  └──────┬───────┘  • 记录备选方案                                      │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────┐                                                     │
│  │  执行并返回   │  • 调用选定模型                                       │
│  │  Execute     │  • 记录执行指标                                       │
│  └──────────────┘  • 处理降级                                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 路由规则表

```python
# 路由规则配置
ROUTING_RULES = {
    # 任务类型: (首选模型, 备选模型, 复杂度阈值)
    "doc_draft": ("local_gemma", "cloud_qwen_plus", "low"),
    "doc_polish": ("local_gemma", "cloud_qwen_plus", "low"),
    "contract_review": ("local_gemma", "cloud_qwen_plus", "low"),
    "case_summary": ("local_gemma", "cloud_qwen_plus", "medium"),
    "evidence_analysis": ("local_gemma", "cloud_qwen_plus", "medium"),
    "law_retrieval": ("local_gemma", "cloud_qwen_plus", "medium"),
    "qa": ("local_gemma", "cloud_qwen_plus", "low"),
    "defense_suggest": ("local_gemma", "cloud_qwen_plus", "medium"),
    "adversarial": ("cloud_qwen_max", None, "high"),
    "prediction": ("cloud_qwen_max", None, "high"),
    "judge_perspective": ("cloud_qwen_max", None, "high"),
    "strategy_synthesis": ("cloud_qwen_max", None, "high"),
    "win_probability": ("cloud_qwen_max", None, "high"),
}

# 用户级别路由覆盖
USER_OVERRIDES = {
    "premium": {
        "qa": "cloud_qwen_plus",  # 高级用户使用云端
    },
    "enterprise": {
        "default": "cloud_qwen_max",  # 企业用户默认云端
    }
}
```

---

## 三、模型配置

### 3.1 本地模型配置

```yaml
# Ollama 配置
ollama:
  base_url: "http://localhost:11434"
  model: "gemma:4b"
  timeout: 120
  retry: 3
  retry_delay: 2

# 模型参数
model_params:
  temperature: 0.7
  top_p: 0.9
  top_k: 40
  num_predict: 2048
  stop:
    - "\n\n"
    - "Human:"
```

### 3.2 云端模型配置

```yaml
# DashScope 配置
dashscope:
  api_key: "${DASHSCOPE_API_KEY}"
  base_url: "https://dashscope.aliyuncs.com/api/v1"
  
  # 模型列表
  models:
    qwen_plus:
      name: "qwen-plus"
      max_tokens: 8192
      temperature: 0.7
      
    qwen_max:
      name: "qwen-max"
      max_tokens: 8192
      temperature: 0.5
      
    qwen_long:
      name: "qwen-long"
      max_tokens: 30000
      temperature: 0.7

  # 限流配置
  rate_limit:
    requests_per_minute: 60
    tokens_per_minute: 100000
```

### 3.3 Embedding配置

```yaml
# Embedding 配置
embedding:
  # 优先使用本地
  local:
    provider: "sentence-transformers"
    model: "paraphrase-multilingual-MiniLM-L12-v2"
    dimension: 384
    
  # 降级到云端
  cloud:
    provider: "dashscope"
    model: "text-embedding-v2"
    dimension: 1536
```

---

## 四、降级策略

### 4.1 降级链路

```
┌─────────────────────────────────────────────────────────────────────┐
│                          降级链路                                     │
│                                                                      │
│  请求 ──► 本地模型 ──► 云端模型 ──► 缓存 ──► 错误响应                 │
│    │         │            │           │                             │
│    │         ▼            ▼           ▼                             │
│    │      失败?         失败?        无?                             │
│    │         │            │           │                             │
│    │         └────────────┴───────────┘                             │
│    │                   │                                           │
│    │                   ▼                                           │
│    │              降级到下一个                                       │
│    │                   │                                           │
│    │                   └──────────────────────────────────────────►│
│    │                                     记录降级日志                 │
│    │                                                                   │
│    └────────────────────────────────────────────────────────────────►│
│                                   返回降级响应                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 降级触发条件

```python
# 降级触发条件
FALLBACK_TRIGGERS = {
    # 本地模型降级条件
    "local_model": {
        "response_time_exceed": 10.0,      # 响应超过10秒
        "error_rate_exceed": 0.1,          # 错误率超过10%
        "consecutive_errors": 3,            # 连续失败3次
        "service_unavailable": True,        # 服务不可用
    },
    
    # 云端模型降级条件
    "cloud_model": {
        "rate_limit_exceed": True,          # 触发限流
        "quota_exhausted": True,            # 配额用尽
        "network_error": True,              # 网络错误
        "timeout": 30.0,                    # 超时30秒
    }
}
```

### 4.3 降级缓存

```python
# 缓存策略
CACHE_CONFIG = {
    # 缓存key格式
    "key_format": "llm:response:{task_type}:{content_hash}",
    
    # TTL配置
    "ttl": {
        "qa": 3600,           # 问答1小时
        "law_retrieval": 7200, # 法条2小时
        "doc_draft": 300,     # 文书5分钟
        "default": 1800,       # 默认30分钟
    },
    
    # 缓存大小限制
    "max_size": 10000,
    "max_memory": "256mb",
}
```

---

## 五、性能优化

### 5.1 响应时间目标

| 场景 | P50 | P95 | P99 | 路由目标 |
|------|-----|-----|-----|----------|
| 本地模型推理 | <1s | <2s | <3s | 80% |
| 云端模型推理 | <3s | <5s | <8s | 20% |
| 含向量检索 | <2s | <4s | <6s | - |

### 5.2 并发控制

```python
# 并发配置
CONCURRENCY_CONFIG = {
    "local_model": {
        "max_concurrent": 10,
        "queue_size": 50,
        "timeout": 120,
    },
    "cloud_model": {
        "max_concurrent": 5,
        "queue_size": 20,
        "timeout": 60,
        "rate_limit": {
            "requests_per_minute": 30,
            "tokens_per_minute": 50000,
        }
    }
}
```

### 5.3 批处理

```python
# 批处理配置
BATCH_CONFIG = {
    "enabled": True,
    "max_batch_size": 10,
    "max_wait_time": 0.5,  # 秒
    "min_batch_size": 3,
}
```

---

## 六、监控指标

### 6.1 核心指标

```yaml
# Prometheus 指标
metrics:
  # 路由统计
  llm_route_total:
    labels: [task_type, model, status]
    description: "路由请求总数"
    
  llm_route_local_ratio:
    description: "本地模型命中率"
    
  # 响应时间
  llm_request_duration_seconds:
    labels: [model, task_type]
    buckets: [0.5, 1, 2, 3, 5, 10, 30]
    description: "LLM响应时间"
    
  # 模型健康
  model_health:
    labels: [model]
    description: "模型健康状态 (1=健康, 0=不健康)"
    
  # 降级统计
  llm_fallback_total:
    labels: [from_model, to_model, reason]
    description: "降级次数"
    
  # Token使用
  llm_token_usage:
    labels: [model, task_type]
    description: "Token消耗量"
```

### 6.2 告警规则

```yaml
alerts:
  # 本地命中率低
  - name: LLMLocalHitRateLow
    condition: local_hit_rate < 0.6
    duration: 30m
    severity: warning
    message: "本地模型命中率低于60%"
    
  # 模型响应慢
  - name: LLMResponseSlow
    condition: p99_duration > 10
    duration: 5m
    severity: critical
    message: "LLM P99响应时间超过10秒"
    
  # 降级率高
  - name: LLMFallbackRateHigh
    condition: fallback_rate > 0.2
    duration: 1h
    severity: warning
    message: "降级率超过20%"
```

---

## 七、API接口

### 7.1 路由状态

```
GET /api/llm/router/status
```

**响应**

```json
{
  "status": "healthy",
  "models": {
    "local": {
      "name": "gemma:4b",
      "status": "available",
      "load": 0.3,
      "avg_response_time": 1.2
    },
    "cloud": {
      "name": "qwen-plus",
      "status": "available",
      "quota_remaining": 45000,
      "avg_response_time": 2.8
    }
  },
  "stats": {
    "total_requests_24h": 15000,
    "local_hit_rate": 0.82,
    "avg_response_time": 1.5,
    "fallback_rate": 0.05
  }
}
```

### 7.2 手动路由指定

```
POST /api/llm/generate
```

**请求体**

```json
{
  "task_type": "doc_draft",
  "content": "生成一份借款合同...",
  "force_model": "cloud_qwen_plus",  // 可选，强制使用指定模型
  "options": {
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

---

## 八、实现代码

### 8.1 ModelRouter 类

```python
# app/services/model_router.py

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
import asyncio
import time

class ModelType(Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    CACHE = "cache"

@dataclass
class RouteResult:
    model_type: ModelType
    model_name: str
    response: str
    latency: float
    fallback_used: bool
    fallback_reason: Optional[str] = None

class ModelRouter:
    """LLM智能路由器"""
    
    def __init__(
        self,
        local_service: "LocalLLMService",
        cloud_service: "CloudLLMService",
        cache_service: "CacheService"
    ):
        self.local = local_service
        self.cloud = cloud_service
        self.cache = cache_service
        self.rules = ROUTING_RULES
        
    async def route(self, task_type: str, content: str) -> RouteResult:
        """执行路由决策"""
        start_time = time.time()
        
        # 1. 获取路由规则
        rule = self.rules.get(task_type, self.rules["qa"])
        primary_model = rule[0]
        
        # 2. 尝试主模型
        if primary_model.startswith("local"):
            result = await self._try_local(task_type, content)
            if result:
                return result
                
            # 降级到云端
            result = await self._try_cloud(task_type, content)
            if result:
                return result
        else:
            result = await self._try_cloud(task_type, content)
            if result:
                return result
                
            # 降级到本地
            result = await self._try_local(task_type, content)
            if result:
                return result
        
        # 3. 尝试缓存
        cached = self.cache.get(task_type, content)
        if cached:
            return RouteResult(
                model_type=ModelType.CACHE,
                model_name="cache",
                response=cached,
                latency=time.time() - start_time,
                fallback_used=True,
                fallback_reason="primary_models_unavailable"
            )
        
        # 4. 返回错误
        raise ModelRouterError("All models unavailable")
    
    async def _try_local(self, task_type: str, content: str) -> Optional[RouteResult]:
        """尝试本地模型"""
        try:
            response = await self.local.chat(task_type, content)
            return RouteResult(
                model_type=ModelType.LOCAL,
                model_name="gemma:4b",
                response=response,
                latency=self.local.last_latency,
                fallback_used=False
            )
        except Exception as e:
            logger.warning(f"Local model failed: {e}")
            return None
    
    async def _try_cloud(self, task_type: str, content: str) -> Optional[RouteResult]:
        """尝试云端模型"""
        try:
            response = await self.cloud.chat(task_type, content)
            return RouteResult(
                model_type=ModelType.CLOUD,
                model_name="qwen-plus",
                response=response,
                latency=self.cloud.last_latency,
                fallback_used=False
            )
        except RateLimitError:
            logger.warning("Cloud model rate limited")
            return None
        except Exception as e:
            logger.warning(f"Cloud model failed: {e}")
            return None
```

---

## 九、测试策略

### 9.1 单元测试

```python
def test_routing_rules():
    """测试路由规则"""
    router = ModelRouter(...)
    
    # 文书生成应路由到本地
    result = asyncio.run(router.route("doc_draft", "生成借款合同"))
    assert result.model_type == ModelType.LOCAL
    
    # 预测应路由到云端
    result = asyncio.run(router.route("prediction", "预测案件结果"))
    assert result.model_type == ModelType.CLOUD

def test_fallback_chain():
    """测试降级链路"""
    router = ModelRouter(...)
    router.local.set_unavailable()
    
    # 应自动降级到云端
    result = asyncio.run(router.route("doc_draft", "生成内容"))
    assert result.model_type == ModelType.CLOUD
    assert result.fallback_used == True
```

### 9.2 集成测试

```python
def test_end_to_end_routing():
    """端到端路由测试"""
    # 1. 启动服务
    # 2. 发送各类请求
    # 3. 验证路由正确性
    # 4. 验证降级机制
    # 5. 验证指标记录
```

---

*文档版本: v1.0*
*最后更新: 2026-04-02*
