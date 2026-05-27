# 法律资料库设计文档

> 法律案件追踪系统法律资料库架构设计

---

## 一、概述

### 1.1 目的

法律资料库是系统的核心知识组件，提供：
- 法律法规检索
- 司法解释查询
- 指导性案例参考
- RAG智能问答

### 1.2 数据规模

| 数据类型 | 当前规模 | 目标规模 | 数据来源 |
|----------|----------|----------|----------|
| 法律条文 | 258条 | 2500+条 | 民法典、刑法等 |
| 司法解释 | 12部 | 28000+篇 | 最高法解释 |
| 指导案例 | 10个 | 200+批 | 最高法案例 |
| 典型案例 | 0 | 1000+ | 各省高院 |

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          法律资料库架构                                │
│                                                                      │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐         │
│  │   前端应用   │      │   API层     │      │   服务层     │         │
│  │             │◄────►│             │◄────►│             │         │
│  │  检索界面    │      │ /legal/*   │      │ 检索服务    │         │
│  │  RAG问答    │      │             │      │ RAG服务     │         │
│  │  文档展示    │      │             │      │ 同步服务    │         │
│  └─────────────┘      └─────────────┘      └──────┬──────┘         │
│                                                      │               │
│         ┌────────────────────┬─────────────────────┼───────────┐   │
│         │                    │                     │           │   │
│         ▼                    ▼                     ▼           ▼   │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ ┌───────┐│
│  │ PostgreSQL │      │  ChromaDB   │      │   数据源     │ │ Redis ││
│  │  (结构化)   │      │  (向量库)   │      │  (外部API)  │ │(缓存) ││
│  │             │      │             │      │             │ │       ││
│  │ • 法条表    │      │ • 法条向量  │      │ • 北大法宝  │ │热数据 ││
│  │ • 解释表    │      │ • 解释向量  │      │ • 最高法    │ │       ││
│  │ • 案例表    │      │ • 案例向量  │      │ • 法律出版社 │ │       ││
│  └─────────────┘      └─────────────┘      └─────────────┘ └───────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流向

```
┌─────────────────────────────────────────────────────────────────────┐
│                          数据流向                                     │
│                                                                      │
│  ┌──────────────┐                                                    │
│  │   数据源      │                                                    │
│  │  • LawRefBook│  Pull/定时                                         │
│  │  • 北大法宝API│ ─────────────────────────────────────────────────►│
│  │  • 最高法官网 │                                                    │
│  └──────────────┘                                                    │
│                              │                                       │
│                              ▼                                       │
│                    ┌─────────────────┐                               │
│                    │   爬虫/导入器    │                               │
│                    │                 │                               │
│                    │ • 数据抓取       │                               │
│                    │ • 格式转换       │                               │
│                    │ • 清洗去重       │                               │
│                    └────────┬────────┘                               │
│                             │                                        │
│              ┌──────────────┼──────────────┐                        │
│              │              │              │                         │
│              ▼              ▼              ▼                          │
│       ┌───────────┐  ┌───────────┐  ┌───────────┐                   │
│       │ PostgreSQL│  │ ChromaDB  │  │   Redis   │                   │
│       │  (原始数据)│  │  (向量)   │  │  (热点)   │                   │
│       └───────────┘  └───────────┘  └───────────┘                   │
│              │              │              │                        │
│              └──────────────┼──────────────┘                        │
│                             │                                        │
│                             ▼                                        │
│                    ┌─────────────────┐                               │
│                    │   检索服务       │                               │
│                    │                 │                               │
│                    │ • 关键词检索     │                               │
│                    │ • 向量相似度    │                               │
│                    │ • 混合检索      │                               │
│                    └─────────────────┘                               │
│                             │                                        │
│                             ▼                                        │
│                    ┌─────────────────┐                               │
│                    │   API层         │                               │
│                    │                 │                               │
│                    │ GET /legal/*    │                               │
│                    │ POST /legal/rag │                               │
│                    └─────────────────┘                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、数据库设计

### 3.1 PostgreSQL Schema

```sql
-- 法律条文表
CREATE TABLE legal_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_code VARCHAR(100) NOT NULL,      -- 法条编号，如 "第67条"
    law_code VARCHAR(50) NOT NULL,            -- 法律编号，如 "civil_code"
    law_name VARCHAR(200) NOT NULL,            -- 法律名称
    chapter VARCHAR(200),                     -- 章节
    section VARCHAR(200),                     -- 小节
    title VARCHAR(500) NOT NULL,              -- 标题
    content TEXT NOT NULL,                    -- 法条内容
    effective_date DATE,                      -- 生效日期
    expiration_date DATE,                     -- 失效日期
    status VARCHAR(20) DEFAULT 'effective',  -- effective/amended/repealed
    metadata JSONB DEFAULT '{}',              -- 扩展字段
    source_url VARCHAR(500),                  -- 来源URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_articles_law_code ON legal_articles(law_code);
CREATE INDEX idx_articles_status ON legal_articles(status);
CREATE INDEX idx_articles_content ON legal_articles USING GIN(to_tsvector('chinese', content));

-- 司法解释表
CREATE TABLE legal_interpretations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_number VARCHAR(100) NOT NULL,    -- 文号，如 "法释〔2020〕17号"
    title VARCHAR(500) NOT NULL,              -- 标题
    issuing_authority VARCHAR(100) NOT NULL,  -- 发布机关
    issuing_date DATE NOT NULL,               -- 发布日期
    effective_date DATE,                      -- 生效日期
    content TEXT NOT NULL,                    -- 全文内容
    summary TEXT,                             -- 摘要
    article_count INT,                        -- 条文数
    status VARCHAR(20) DEFAULT 'effective',  -- 状态
    metadata JSONB DEFAULT '{}',
    source_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_interps_authority ON legal_interpretations(issuing_authority);
CREATE INDEX idx_interps_date ON legal_interpretations(issuing_date);
CREATE INDEX idx_interps_content ON legal_interpretations USING GIN(to_tsvector('chinese', content));

-- 指导案例表
CREATE TABLE legal_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number VARCHAR(100) NOT NULL,        -- 案号
    title VARCHAR(500) NOT NULL,             -- 案例标题
    case_type VARCHAR(100),                  -- 案件类型
    court VARCHAR(200),                      -- 法院
    judge_date DATE,                         -- 裁判日期
    judges JSONB,                            -- 审判人员
    parties JSONB,                           -- 当事人
    case_facts TEXT,                         -- 案件事实
    summary TEXT,                             -- 裁判摘要
    key_points JSONB,                        -- 裁判要点
    legal_basis JSONB,                        -- 法律依据
    ruling TEXT,                             -- 裁判结果
    effect TEXT,                              -- 效力说明
    is_published BOOLEAN DEFAULT FALSE,      -- 是否公开
    relevance_tags TEXT[],                    -- 相关标签
    metadata JSONB DEFAULT '{}',
    source_url VARCHAR(500),
    view_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_cases_court ON legal_cases(court);
CREATE INDEX idx_cases_type ON legal_cases(case_type);
CREATE INDEX idx_cases_date ON legal_cases(judge_date);
CREATE INDEX idx_cases_tags ON legal_cases USING GIN(relevance_tags);
CREATE INDEX idx_cases_content ON legal_cases USING GIN(to_tsvector('chinese', summary || ' ' || case_facts));

-- 更新触发器
CREATE TRIGGER update_legal_tables_updated_at
    BEFORE UPDATE ON legal_articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interps_updated_at
    BEFORE UPDATE ON legal_interpretations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cases_updated_at
    BEFORE UPDATE ON legal_cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3.2 ChromaDB Collection

```python
# 向量数据库配置
COLLECTIONS = {
    "legal_articles": {
        "name": "legal_articles",
        "description": "法律条文向量库",
        "dimension": 384,  # MiniLM dimension
        "metadata": {
            "law_code": "str",
            "article_code": "str",
            "status": "str"
        }
    },
    "legal_interpretations": {
        "name": "legal_interpretations", 
        "description": "司法解释向量库",
        "dimension": 384,
        "metadata": {
            "issuing_authority": "str",
            "document_number": "str"
        }
    },
    "legal_cases": {
        "name": "legal_cases",
        "description": "指导案例向量库",
        "dimension": 384,
        "metadata": {
            "case_number": "str",
            "case_type": "str",
            "court": "str"
        }
    },
    "litigation_rules": {
        "name": "litigation_rules",
        "description": "诉讼规则向量库",
        "dimension": 384,
        "metadata": {
            "rule_type": "str"
        }
    }
}
```

---

## 四、Embedding模型

### 4.1 本地Embedding

```python
# 本地向量模型配置
LOCAL_EMBEDDING = {
    "provider": "sentence-transformers",
    "model": "paraphrase-multilingual-MiniLM-L12-v2",
    "dimension": 384,
    "max_seq_length": 256,
    "device": "cuda"  # or "cpu"
}
```

### 4.2 向量化策略

```python
# 向量化策略
def get_embedding_text(record_type: str, record: dict) -> str:
    """生成适合向量化的文本"""
    
    if record_type == "article":
        # 法条: 标题 + 内容摘要
        return f"{record['title']} {record['content'][:500]}"
    
    elif record_type == "interpretation":
        # 解释: 标题 + 摘要 + 要点
        key_points = " ".join([
            f"第{a['number']}条: {a['content'][:100]}" 
            for a in record.get('articles', [])[:5]
        ])
        return f"{record['title']} {record.get('summary', '')} {key_points}"
    
    elif record_type == "case":
        # 案例: 标题 + 摘要 + 要点
        key_points = " ".join(record.get('key_points', []))
        return f"{record['title']} {record.get('summary', '')} {key_points}"
    
    else:
        return record.get('content', '')[:500]
```

---

## 五、检索策略

### 5.1 检索流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                          检索流程                                     │
│                                                                      │
│  用户查询 "民间借贷 利息计算"                                          │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                     │
│  │  查询预处理    │                                                     │
│  │               │                                                     │
│  │ • 分词         │                                                     │
│  │ • 同义词扩展   │                                                     │
│  │ • 纠错         │                                                     │
│  └──────┬───────┘                                                     │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                     │
│  │  混合检索     │                                                     │
│  │               │                                                     │
│  │ • 关键词检索   │ ───► PostgreSQL full-text search                   │
│  │ • 向量检索    │ ───► ChromaDB similarity search                     │
│  │ • 重排序      │ ───► RRF融合                                       │
│  └──────┬───────┘                                                     │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                     │
│  │  结果处理     │                                                     │
│  │               │                                                     │
│  │ • 去重         │                                                     │
│  │ • 过滤         │                                                     │
│  │ • 高亮         │                                                     │
│  │ • 分页         │                                                     │
│  └──────┬───────┘                                                     │
│         │                                                             │
│         ▼                                                             │
│  返回检索结果 + 相似度分数                                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 RRF融合算法

```python
def reciprocal_rank_fusion(results_list: list, k: int = 60) -> list:
    """RRF融合算法
    
    RRF分数 = Σ(1 / (k + rank))
    
    Args:
        results_list: 多个检索结果列表
        k: 融合参数，默认60
        
    Returns:
        融合后的排序结果
    """
    scores = {}
    
    for results in results_list:
        for rank, item in enumerate(results, start=1):
            item_id = item['id']
            rrf_score = 1 / (k + rank)
            scores[item_id] = scores.get(item_id, 0) + rrf_score
    
    # 按RRF分数排序
    sorted_items = sorted(
        scores.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    return [item_id for item_id, score in sorted_items]
```

---

## 六、RAG实现

### 6.1 RAG流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                          RAG流程                                     │
│                                                                      │
│  用户问题 "民间借贷超过法定利率如何处理？"                               │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                     │
│  │  问题向量化   │  embedding(question)                               │
│  └──────┬───────┘                                                     │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                     │
│  │  相似度检索   │  top_k=10                                          │
│  │               │                                                     │
│  │ ChromaDB ─────┼──► 相关法条、解释、案例                             │
│  │ PostgreSQL ───┘──► 结构化匹配                                      │
│  └──────┬───────┘                                                     │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                     │
│  │  上下文构建   │                                                     │
│  │               │                                                     │
│  │ • 选取Top-5  │                                                     │
│  │ • 格式化为   │                                                     │
│  │   Prompt    │                                                     │
│  └──────┬───────┘                                                     │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                     │
│  │  LLM生成     │  ModelRouter选择模型                                 │
│  │               │                                                     │
│  │ • 生成回答   │                                                     │
│  │ • 引用来源   │                                                     │
│  │ • 标注置信度 │                                                     │
│  └──────┬───────┘                                                     │
│         │                                                             │
│         ▼                                                             │
│  返回回答 + 来源引用                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Prompt模板

```python
# RAG Prompt模板
RAG_PROMPT_TEMPLATE = """
你是一个专业的法律助手。请根据以下参考信息回答用户的问题。

## 参考信息

{context}

---

## 用户问题

{question}

---

## 回答要求

1. 准确引用参考信息中的法条、解释或案例
2. 结合具体案例进行说明
3. 如参考信息不足以回答，请明确说明
4. 回答应当准确、专业、易懂

## 回答格式

{answer_format}

"""

# 回答格式
ANSWER_FORMAT = """
根据参考资料：

[综合分析]

参考依据：
1. {reference_1}
2. {reference_2}
3. {reference_3}

置信度：{confidence}
"""
```

---

## 七、数据同步

### 7.1 同步策略

```python
# 数据同步配置
SYNC_CONFIG = {
    # LawRefBook 仓库同步
    "lawrefbook": {
        "enabled": True,
        "schedule": "0 2 * * *",  # 每天凌晨2点
        "source": "https://github.com/LawRefBook/Laws.git",
        "target": "legal_articles"
    },
    
    # 司法解释同步
    "interpretations": {
        "enabled": True,
        "schedule": "0 3 * * 0",  # 每周日凌晨3点
        "source": "北大法宝API",
        "incremental": True
    },
    
    # 指导案例同步
    "cases": {
        "enabled": True,
        "schedule": "0 4 * * 0",  # 每周日凌晨4点
        "source": "最高人民法院官网",
        "incremental": True
    }
}
```

### 7.2 增量更新

```python
async def incremental_sync():
    """增量同步"""
    
    # 1. 获取上次同步时间
    last_sync = await get_last_sync_time("interpretations")
    
    # 2. 获取更新的数据
    new_items = await fetch_updates(
        source="北大法宝",
        since=last_sync
    )
    
    # 3. 去重判断
    for item in new_items:
        existing = await check_exists(item)
        if existing:
            # 更新
            await update_record(item)
        else:
            # 新增
            await insert_record(item)
            
            # 同时向量化
            await add_to_vector_db(item)
    
    # 4. 记录同步时间
    await update_last_sync_time("interpretations")
```

---

## 八、性能指标

### 8.1 检索性能

| 指标 | 目标 | 说明 |
|------|------|------|
| P50延迟 | <100ms | 简单检索 |
| P95延迟 | <500ms | 混合检索 |
| P99延迟 | <1s | 含向量检索 |
| RAG延迟 | <3s | 端到端RAG |
| 向量检索 | <200ms | ChromaDB |

### 8.2 数据质量

| 指标 | 目标 | 说明 |
|------|------|------|
| 检索准确率 | >85% | Top-10准确率 |
| 召回率 | >90% | 相关文档召回 |
| 完整性 | >95% | 字段完整率 |

---

## 九、监控指标

```yaml
# 法律资料库监控
metrics:
  # 检索统计
  legal_search_total:
    labels: [type, status]
    description: "检索请求总数"
    
  legal_search_duration_seconds:
    description: "检索耗时"
    
  # 同步统计
  legal_sync_total:
    labels: [type, status]
    description: "同步任务数"
    
  legal_sync_records:
    labels: [type]
    description: "同步记录数"
    
  # RAG指标
  rag_generation_total:
    labels: [model, status]
    description: "RAG生成总数"
    
  rag_source_count:
    description: "RAG引用来源数量"
    
  rag_relevance_score:
    description: "RAG来源相关性分数"
```

---

*文档版本: v1.0*
*最后更新: 2026-04-02*
