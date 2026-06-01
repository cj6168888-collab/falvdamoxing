"""
LLM智能路由配置
"""
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class TaskType(str, Enum):
    """任务类型枚举"""
    # 低复杂度 - 本地模型
    DOC_DRAFT = "doc_draft"           # 文书初稿
    DOC_POLISH = "doc_polish"         # 文书润色
    CONTRACT_REVIEW = "contract_review" # 合同审查
    QA = "qa"                         # 智能问答
    DEFINITION = "definition"          # 术语解释
    CASE_SUMMARY = "case_summary"      # 案情摘要
    
    # 中等复杂度 - 本地优先
    EVIDENCE_ANALYSIS = "evidence_analysis" # 证据分析
    LAW_RETRIEVAL = "law_retrieval"    # 法条检索
    DEFENSE_SUGGEST = "defense_suggest" # 抗辩建议
    DOCUMENT_SUGGESTION = "document_suggestion" # 文书建议
    
    # 高复杂度 - 云端模型
    ADVERSARIAL = "adversarial"        # 对抗性推演
    PREDICTION = "prediction"          # 案件预测
    JUDGE_PERSPECTIVE = "judge_perspective" # 法官视角
    STRATEGY_SYNTHESIS = "strategy_synthesis" # 策略综合
    WIN_PROBABILITY = "win_probability" # 胜诉评估


class ModelType(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    CACHE = "cache"


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RoutingRule:
    """路由规则"""
    task_type: TaskType
    complexity: Complexity
    primary_model: str
    fallback_model: Optional[str]
    local_priority: int  # 优先级，数字越小越高
    description: str


# 路由规则表
ROUTING_RULES: Dict[TaskType, RoutingRule] = {
    # 低复杂度任务 - 仅本地（快速响应、无需推理）
    TaskType.DOC_POLISH: RoutingRule(
        task_type=TaskType.DOC_POLISH,
        complexity=Complexity.LOW,
        primary_model="local",
        fallback_model="cloud",
        local_priority=1,
        description="法律文书润色修改（本地快速处理）"
    ),
    TaskType.QA: RoutingRule(
        task_type=TaskType.QA,
        complexity=Complexity.LOW,
        primary_model="local",
        fallback_model="cloud",
        local_priority=1,
        description="简单法律问答（本地快速响应）"
    ),
    TaskType.DEFINITION: RoutingRule(
        task_type=TaskType.DEFINITION,
        complexity=Complexity.LOW,
        primary_model="local",
        fallback_model="cloud",
        local_priority=1,
        description="专业术语解释（本地快速响应）"
    ),
    
    # 中/高复杂度任务 - 云端推理
    TaskType.DOC_DRAFT: RoutingRule(
        task_type=TaskType.DOC_DRAFT,
        complexity=Complexity.MEDIUM,
        primary_model="cloud",
        fallback_model="local",
        local_priority=2,
        description="法律文书初稿生成（需云端推理）"
    ),
    TaskType.CONTRACT_REVIEW: RoutingRule(
        task_type=TaskType.CONTRACT_REVIEW,
        complexity=Complexity.MEDIUM,
        primary_model="cloud",
        fallback_model="local",
        local_priority=2,
        description="合同条款审查（需云端推理）"
    ),
    TaskType.CASE_SUMMARY: RoutingRule(
        task_type=TaskType.CASE_SUMMARY,
        complexity=Complexity.MEDIUM,
        primary_model="cloud",
        fallback_model="local",
        local_priority=2,
        description="案件信息摘要（需云端推理）"
    ),
    TaskType.EVIDENCE_ANALYSIS: RoutingRule(
        task_type=TaskType.EVIDENCE_ANALYSIS,
        complexity=Complexity.MEDIUM,
        primary_model="cloud",
        fallback_model="local",
        local_priority=2,
        description="证据三性分析（需云端推理）"
    ),
    TaskType.LAW_RETRIEVAL: RoutingRule(
        task_type=TaskType.LAW_RETRIEVAL,
        complexity=Complexity.MEDIUM,
        primary_model="cloud",
        fallback_model="local",
        local_priority=2,
        description="法条检索引用（需云端推理）"
    ),
    TaskType.DEFENSE_SUGGEST: RoutingRule(
        task_type=TaskType.DEFENSE_SUGGEST,
        complexity=Complexity.MEDIUM,
        primary_model="cloud",
        fallback_model="local",
        local_priority=2,
        description="抗辩建议生成（需云端推理）"
    ),
    TaskType.DOCUMENT_SUGGESTION: RoutingRule(
        task_type=TaskType.DOCUMENT_SUGGESTION,
        complexity=Complexity.MEDIUM,
        primary_model="cloud",
        fallback_model="local",
        local_priority=2,
        description="文书建议（需云端推理）"
    ),
    
    # 高复杂度任务 - 仅云端
    TaskType.ADVERSARIAL: RoutingRule(
        task_type=TaskType.ADVERSARIAL,
        complexity=Complexity.HIGH,
        primary_model="cloud",
        fallback_model=None,
        local_priority=3,
        description="对抗性推演（仅云端）"
    ),
    TaskType.PREDICTION: RoutingRule(
        task_type=TaskType.PREDICTION,
        complexity=Complexity.HIGH,
        primary_model="cloud",
        fallback_model=None,
        local_priority=3,
        description="案件结果预测（仅云端）"
    ),
    TaskType.JUDGE_PERSPECTIVE: RoutingRule(
        task_type=TaskType.JUDGE_PERSPECTIVE,
        complexity=Complexity.HIGH,
        primary_model="cloud",
        fallback_model=None,
        local_priority=3,
        description="法官视角评估（仅云端）"
    ),
    TaskType.STRATEGY_SYNTHESIS: RoutingRule(
        task_type=TaskType.STRATEGY_SYNTHESIS,
        complexity=Complexity.HIGH,
        primary_model="cloud",
        fallback_model=None,
        local_priority=3,
        description="策略综合合成（仅云端）"
    ),
    TaskType.WIN_PROBABILITY: RoutingRule(
        task_type=TaskType.WIN_PROBABILITY,
        complexity=Complexity.HIGH,
        primary_model="cloud",
        fallback_model=None,
        local_priority=3,
        description="诉讼风险评估（仅云端）"
    ),
}


# 降级配置
FALLBACK_CONFIG = {
    "local_model": {
        "response_time_threshold": 10.0,  # 响应超过10秒
        "error_rate_threshold": 0.1,       # 错误率超过10%
        "consecutive_errors": 3,           # 连续失败3次
    },
    "cloud_model": {
        "rate_limit_threshold": True,      # 触发限流
        "quota_exhausted": True,           # 配额用尽
        "timeout": 30.0,                   # 超时30秒
    }
}

# 缓存配置
CACHE_CONFIG = {
    "ttl": {
        "qa": 3600,              # 问答1小时
        "law_retrieval": 7200,   # 法条2小时
        "case_summary": 1800,     # 摘要30分钟
        "doc_draft": 300,         # 文书5分钟
        "default": 1800,          # 默认30分钟
    },
    "max_size": 10000,
}

# 本地模型配置
LOCAL_MODEL_CONFIG = {
    "provider": "ollama",
    "base_url": "http://localhost:11434",
    "default_model": "gemma4:e2b",
    "supported_models": ["gemma4:e2b"],
    "timeout": 120,
    "max_retries": 3,
}

# 云端模型配置
CLOUD_MODEL_CONFIG = {
    "provider": "dashscope",
    "api_key_env": "DASHSCOPE_API_KEY",
    "default_model": "qwen_plus",
    "models": {
        "qwen_plus": {
            "name": "qwen-plus",
            "max_tokens": 8192,
            "temperature": 0.7,
            "use_for": ["reasoning", "analysis", "draft"],
        },
        "qwen_max": {
            "name": "qwen-max",
            "max_tokens": 8192,
            "temperature": 0.5,
            "use_for": ["complex_reasoning"],
        },
        "qwen_long": {
            "name": "qwen-long",
            "max_tokens": 30000,
            "temperature": 0.7,
            "use_for": ["long_context", "document_analysis"],
        }
    },
    "timeout": 60,
    "rate_limit": {
        "requests_per_minute": 60,
        "tokens_per_minute": 100000,
    }
}

# Embedding配置
EMBEDDING_CONFIG = {
    "local": {
        "provider": "sentence-transformers",
        "model": "paraphrase-multilingual-MiniLM-L12-v2",
        "dimension": 384,
    },
    "cloud": {
        "provider": "dashscope",
        "model": "text-embedding-v2",
        "dimension": 1536,
    }
}


def get_routing_rule(task_type: TaskType) -> RoutingRule:
    """获取任务的路由规则"""
    return ROUTING_RULES.get(task_type, RoutingRule(
        task_type=task_type,
        complexity=Complexity.MEDIUM,
        primary_model="local",
        fallback_model="cloud",
        local_priority=2,
        description="默认任务"
    ))


def should_use_local(task_type: TaskType) -> bool:
    """判断是否应该使用本地模型"""
    rule = get_routing_rule(task_type)
    return rule.primary_model == "local"
