# 法律资料库API文档

> 法律资料库检索相关API端点详细说明

---

## 一、概述

法律资料库包含：
- **法律条文**: 民法典、刑法、诉讼法等
- **司法解释**: 最高人民法院司法解释
- **指导性案例**: 最高人民法院指导案例
- **典型案例**: 各省高院典型案例

**数据源**:
- 北大法宝 (PKULAW)
- 最高人民法院官网
- 法律出版社

---

## 二、搜索法条

### GET /api/legal/articles

搜索法律条文。

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| q | string | 是 | - | 搜索关键词 |
| category | string | 否 | - | 法律类别 |
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |

**category 可选值**:

| 值 | 说明 |
|------|------|
| civil | 民法典 |
| criminal | 刑法 |
| civil_procedure | 民事诉讼法 |
| criminal_procedure | 刑事诉讼法 |
| labor | 劳动法 |
| company | 公司法 |
| admin | 行政法 |

**响应示例**

```json
{
  "items": [
    {
      "id": "article-001",
      "title": "《中华人民共和国民法典》第六百七十五条",
      "law_name": "民法典",
      "chapter": "借款合同",
      "section": "第三节",
      "article_number": "第六百七十五条",
      "content": "借款人应当按照约定的期限支付利息。对支付利息的期限没有约定或者约定不明确，依据本法第五百一十条的规定仍不能确定，借款期间不满一年的，应当在返还借款时一并支付；借款期间一年以上的，应当在每届满一年时支付，剩余期间不满一年的，应当在返还借款时一并支付。",
      "effective_date": "2021-01-01",
      "status": "effective",
      "relevance_score": 0.95
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "search_time_ms": 45
}
```

---

## 三、法条详情

### GET /api/legal/articles/{article_id}

获取法条详情。

**Path参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| article_id | string | 是 | 法条ID |

**响应示例**

```json
{
  "id": "article-001",
  "title": "《中华人民共和国民法典》第六百七十五条",
  "law_name": "民法典",
  "law_id": "civil_code",
  "chapter": "借款合同",
  "section": "第三节",
  "article_number": "第六百七十五条",
  "content": "借款人应当按照约定的期限支付利息...",
  "effective_date": "2021-01-01",
  "status": "effective",
  "amendments": [
    {
      "date": "2021-01-01",
      "description": "首次发布"
    }
  ],
  "related_articles": [
    {
      "id": "article-002",
      "title": "第六百七十四条",
      "description": "借款利息的预扣"
    },
    {
      "id": "article-003",
      "title": "第六百七十六条",
      "description": "逾期利息"
    }
  ],
  "related_interpretations": [
    {
      "id": "interp-001",
      "title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定",
      "article_ref": "第二十五条"
    }
  ],
  "related_cases": [
    {
      "id": "case-001",
      "title": "指导案例57号",
      "case_number": "（2017）最高法民终123号"
    }
  ],
  "view_count": 15600,
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## 四、搜索司法解释

### GET /api/legal/interpretations

搜索司法解释。

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| q | string | 是 | - | 搜索关键词 |
| issuing_authority | string | 否 | - | 发布机关 |
| year | int | 否 | - | 发布年份 |
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |

**issuing_authority 可选值**:

| 值 | 说明 |
|------|------|
| supreme_court | 最高人民法院 |
| supreme_prosecutor | 最高人民检察院 |
| joint | 联合发布 |

**响应示例**

```json
{
  "items": [
    {
      "id": "interp-001",
      "title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定",
      "issuing_authority": "最高人民法院",
      "document_number": "法释〔2020〕17号",
      "effective_date": "2020-08-20",
      "summary": "为正确审理民间借贷案件，依法保护当事人合法权益...",      
      "article_count": 32,
      "status": "effective",
      "relevance_score": 0.92
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "search_time_ms": 38
}
```

---

## 五、司法解释详情

### GET /api/legal/interpretations/{interp_id}

获取司法解释详情。

**响应示例**

```json
{
  "id": "interp-001",
  "title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定",
  "issuing_authority": "最高人民法院",
  "document_number": "法释〔2020〕17号",
  "effective_date": "2020-08-20",
  "summary": "为正确审理民间借贷案件...",
  "articles": [
    {
      "number": "第一条",
      "content": "本规定所称的民间借贷，是指自然人、法人和非法人组织之间进行资金融通的行为。"
    },
    {
      "number": "第二条",
      "content": "借贷合同成立于2019年8月20日之前的，可以原告合同成立时一年期贷款市场报价利率四倍为标准计算利息。"
    }
  ],
  "related_laws": [
    {
      "id": "article-001",
      "title": "民法典第六百七十五条"
    }
  ],
  "view_count": 23400,
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## 六、搜索指导案例

### GET /api/legal/cases

搜索指导性案例。

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| q | string | 是 | - | 搜索关键词 |
| case_type | string | 否 | - | 案例类型 |
| year | int | 否 | - | 发布年份 |
| court_level | string | 否 | - | 法院级别 |
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |

**响应示例**

```json
{
  "items": [
    {
      "id": "case-001",
      "case_number": "（2017）最高法民终123号",
      "title": "上海某某公司与北京某某公司借款合同纠纷案",
      "case_type": "民间借贷",
      "court": "最高人民法院",
      "judge_date": "2017-06-15",
      "summary": "本案涉及民间借贷利息计算标准问题...",
      "key_points": [
        "借贷合同约定的利率超过法定上限的部分无效",
        "已支付的超过法定上限的利息应抵扣本金"
      ],
      "ruling": "撤销一审判决，改判被告偿还本金及法定利息",
      "is_published": true,
      "relevance_score": 0.88
    }
  ],
  "total": 234,
  "page": 1,
  "page_size": 20,
  "search_time_ms": 52
}
```

---

## 七、案例详情

### GET /api/legal/cases/{case_id}

获取案例详情。

**响应示例**

```json
{
  "id": "case-001",
  "case_number": "（2017）最高法民终123号",
  "title": "上海某某公司与北京某某公司借款合同纠纷案",
  "case_type": "民间借贷",
  "court": "最高人民法院",
  "judge_date": "2017-06-15",
  "judges": ["张三", "李四", "王五"],
  "plaintiff": "上海某某公司",
  "defendant": "北京某某公司",
  "third_party": null,
  "summary": "本案涉及民间借贷利息计算标准问题...",
  "case_facts": "2015年3月，被告因资金周转需要向原告借款...",
  "key_points": [
    "借贷合同约定的利率超过法定上限的部分无效",
    "已支付的超过法定上限的利息应抵扣本金"
  ],
  "legal_basis": [
    "《民法典》第六百七十五条",
    "《最高人民法院关于审理民间借贷案件适用法律若干问题的规定》第二条"
  ],
  "ruling": "撤销一审判决，改判被告偿还本金及法定利息",
  "dissenting_opinion": null,
  "effect": "为指导性案例，各级法院应当参照",
  "source_url": "https://www.court.gov.cn/...",
  "view_count": 15600,
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## 八、综合搜索

### POST /api/legal/search

综合搜索法律资料库（法条、解释、案例）。

**请求体**

```json
{
  "query": "民间借贷 利息计算",
  "types": ["articles", "interpretations", "cases"],
  "category": "civil",
  "date_range": {
    "start": "2020-01-01",
    "end": "2026-04-01"
  },
  "page": 1,
  "page_size": 20
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索关键词 |
| types | array | 否 | 搜索类型，默认全部 |
| category | string | 否 | 法律类别 |
| date_range | object | 否 | 日期范围 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应示例**

```json
{
  "query": "民间借贷 利息计算",
  "results": {
    "articles": {
      "items": [...],
      "total": 45
    },
    "interpretations": {
      "items": [...],
      "total": 12
    },
    "cases": {
      "items": [...],
      "total": 89
    }
  },
  "total": 146,
  "page": 1,
  "page_size": 20,
  "search_time_ms": 125
}
```

---

## 九、RAG检索生成

### POST /api/legal/rag

基于检索增强的法律问答。

**请求体**

```json
{
  "question": "民间借贷中，超过法定利率上限的利息如何处理？",
  "case_context": {
    "case_id": "550e8400-e29b-41d4-a716-446655440000",
    "case_type": "debt_dispute",
    "amount": 100000,
    "interest_rate": "24%",
    "actual_rate": "年化36%"
  },
  "include_sources": true,
  "max_sources": 5
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 问题 |
| case_context | object | 否 | 案件上下文 |
| include_sources | boolean | 否 | 是否包含来源 |
| max_sources | int | 否 | 最大来源数量 |

**响应示例**

```json
{
  "question": "民间借贷中，超过法定利率上限的利息如何处理？",
  "answer": "根据《最高人民法院关于审理民间借贷案件适用法律若干问题的规定》第二十五条，借贷合同约定的利率超过法定上限的部分无效。已支付的超过法定上限的利息应当抵扣本金。\n\n具体到本案：根据您提供的材料，约定的年化利率为36%，超过了法定上限（目前为LPR四倍），超出部分利息应当抵扣本金。",
  "sources": [
    {
      "type": "interpretation",
      "id": "interp-001",
      "title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定",
      "article": "第二十五条",
      "content": "借贷合同约定的利率超过法定上限的，超出部分无效...",
      "relevance": 0.95
    },
    {
      "type": "case",
      "id": "case-001",
      "title": "指导案例57号",
      "content": "约定利率超过法定上限的部分无效...",
      "relevance": 0.88
    }
  ],
  "model": "local_gemma",
  "tokens_used": 2500,
  "processing_time_ms": 3200
}
```

---

## 十、批量获取

### POST /api/legal/batch

批量获取法律资料。

**请求体**

```json
{
  "articles": ["article-001", "article-002"],
  "interpretations": ["interp-001"],
  "cases": ["case-001"]
}
```

**响应示例**

```json
{
  "articles": [
    { "id": "article-001", "title": "...", "content": "..." },
    { "id": "article-002", "title": "...", "content": "..." }
  ],
  "interpretations": [
    { "id": "interp-001", "title": "...", "content": "..." }
  ],
  "cases": [
    { "id": "case-001", "title": "...", "content": "..." }
  ]
}
```

---

## 十一、错误响应

### 400 Bad Request

```json
{
  "error": "VALIDATION_ERROR",
  "message": "搜索关键词不能为空"
}
```

### 503 Service Unavailable

```json
{
  "error": "SERVICE_UNAVAILABLE",
  "message": "法律资料库服务暂时不可用",
  "retry_after": 30
}
```

---

## 十二、向量检索状态

### GET /api/legal/vector/status

获取向量数据库状态。

**响应示例**

```json
{
  "status": "healthy",
  "total_vectors": 125000,
  "collections": {
    "legal_articles": 25000,
    "legal_interpretations": 8000,
    "legal_cases": 92000
  },
  "last_sync": "2026-04-02T00:00:00Z",
  "index_size_mb": 450
}
```

---

*文档版本: v2.1.0*
*最后更新: 2026-04-02*
