# 上诉追踪API文档

> 上诉相关API端点详细说明

---

## 一、概述

上诉追踪模块提供以下功能：
- 创建和管理上诉记录
- 跟踪上诉期限
- 生成上诉状文书
- 监控上诉状态

---

## 二、获取上诉列表

### GET /api/case/{case_id}/appeal

获取指定案件的上诉列表。

**Path参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string (UUID) | 是 | 案件ID |

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |

**响应示例**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "case_id": "550e8400-e29b-41d4-a716-446655440000",
      "appeal_type": "一审上诉",
      "reason": "事实认定错误",
      "target_court": "中级人民法院",
      "filing_date": "2026-03-01",
      "deadline": "2026-03-16",
      "countdown_days": 12,
      "status": "pending",
      "progress": 30,
      "created_at": "2026-03-01T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

## 三、创建上诉

### POST /api/case/{case_id}/appeal

为指定案件创建上诉记录。

**Path参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string (UUID) | 是 | 案件ID |

**请求体**

```json
{
  "appeal_type": "一审上诉",
  "reason": "事实认定错误",
  "target_court": "中级人民法院",
  "filing_date": "2026-03-01",
  "arguments": [
    {
      "title": "争议焦点一",
      "content": "关于借款事实的认定",
      "evidence_refs": ["evidence-001", "evidence-002"]
    }
  ],
  "notes": "需要补充银行转账记录"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| appeal_type | string | 是 | 上诉类型: 一审上诉/二审上诉/再审 |
| reason | string | 是 | 上诉理由，最大2000字 |
| target_court | string | 是 | 目标法院 |
| filing_date | string | 是 | 上诉日期，格式YYYY-MM-DD |
| arguments | array | 否 | 论证点列表 |
| notes | string | 否 | 备注 |

**响应**: 201 Created

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "appeal_type": "一审上诉",
  "reason": "事实认定错误",
  "target_court": "中级人民法院",
  "filing_date": "2026-03-01",
  "deadline": "2026-03-16",
  "countdown_days": 15,
  "status": "pending",
  "created_at": "2026-04-02T10:30:00Z",
  "message": "上诉记录创建成功"
}
```

---

## 四、获取上诉详情

### GET /api/appeal/{appeal_id}

获取上诉详情，包含期限倒计时。

**Path参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| appeal_id | string (UUID) | 是 | 上诉ID |

**响应示例**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "appeal_type": "一审上诉",
  "reason": "事实认定错误",
  "target_court": "中级人民法院",
  "filing_date": "2026-03-01",
  "deadline": "2026-03-16",
  "countdown_days": 12,
  "countdown_hours": 288,
  "is_urgent": true,
  "status": "pending",
  "progress": 30,
  "arguments": [
    {
      "id": "arg-001",
      "title": "争议焦点一",
      "content": "关于借款事实的认定",
      "evidence_refs": ["evidence-001", "evidence-002"],
      "status": "draft"
    }
  ],
  "documents": [
    {
      "id": "doc-001",
      "title": "上诉状",
      "status": "generated",
      "created_at": "2026-03-02T10:00:00Z"
    }
  ],
  "timeline": [
    {
      "action": "创建上诉",
      "date": "2026-03-01T10:00:00Z"
    },
    {
      "action": "生成上诉状",
      "date": "2026-03-02T10:00:00Z"
    }
  ],
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-04-02T09:00:00Z"
}
```

---

## 五、更新上诉

### PUT /api/appeal/{appeal_id}

更新上诉信息。

**请求体**

```json
{
  "reason": "事实认定错误、法律适用错误",
  "target_court": "高级人民法院",
  "notes": "已补充银行转账记录"
}
```

**响应**: 200 OK

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "updated_at": "2026-04-02T11:00:00Z",
  "message": "上诉更新成功"
}
```

---

## 六、删除上诉

### DELETE /api/appeal/{appeal_id}

删除上诉记录。

**响应**: 200 OK

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "deleted": true,
  "message": "上诉已删除"
}
```

---

## 七、上诉期限倒计时

### GET /api/appeal/{appeal_id}/countdown

获取上诉期限倒计时信息。

**Path参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| appeal_id | string (UUID) | 是 | 上诉ID |

**响应示例**

```json
{
  "appeal_id": "550e8400-e29b-41d4-a716-446655440001",
  "filing_date": "2026-03-01",
  "deadline": "2026-03-16",
  "countdown_days": 12,
  "countdown_hours": 288,
  "countdown_minutes": 17280,
  "is_overdue": false,
  "is_urgent": true,
  "holidays_excluded": 2,
  "weekends_excluded": 4,
  "working_days_remaining": 12,
  "warning_level": "warning"
}
```

| warning_level | 说明 |
|---------------|------|
| normal | 剩余时间 > 7 天 |
| warning | 剩余时间 3-7 天 |
| urgent | 剩余时间 1-3 天 |
| critical | 剩余时间 < 1 天 |

---

## 八、生成上诉状

### POST /api/appeal/{appeal_id}/generate-document

使用AI生成上诉状文书。

**Path参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| appeal_id | string (UUID) | 是 | 上诉ID |

**请求体**

```json
{
  "template": "standard",
  "include_evidence": true,
  "include_arguments": true,
  "tone": "formal"
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| template | string | 否 | standard | 模板: standard/custom |
| include_evidence | boolean | 否 | true | 是否包含证据引用 |
| include_arguments | boolean | 否 | true | 是否包含论证点 |
| tone | string | 否 | formal | 文书语气: formal/moderate |

**响应**: 200 OK

```json
{
  "document_id": "doc-001",
  "appeal_id": "550e8400-e29b-41d4-a716-446655440001",
  "title": "民事上诉状",
  "content": "上诉人张三（一审原告）...（完整文书内容）",
  "format": "docx",
  "status": "generated",
  "tokens_used": 1500,
  "model": "local_gemma",
  "generated_at": "2026-04-02T10:30:00Z"
}
```

---

## 九、更新上诉状态

### PUT /api/appeal/{appeal_id}/status

更新上诉状态。

**Path参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| appeal_id | string (UUID) | 是 | 上诉ID |

**请求体**

```json
{
  "status": "filed",
  "filed_date": "2026-03-10",
  "case_number": "(2026)中民上字第1234号",
  "notes": "已缴纳上诉费"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 新状态 |
| filed_date | string | 否 | 递交日期 |
| case_number | string | 否 | 上诉案号 |
| notes | string | 否 | 备注 |

**status 可选值**:

| 值 | 说明 |
|------|------|
| pending | 待递交 |
| filed | 已递交 |
| accepted | 已受理 |
| hearing | 审理中 |
| decided | 已裁决 |
| withdrawn | 已撤回 |
| rejected | 驳回 |

**响应**: 200 OK

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "filed",
  "filed_date": "2026-03-10",
  "case_number": "(2026)中民上字第1234号",
  "updated_at": "2026-04-02T11:00:00Z",
  "message": "状态更新成功"
}
```

---

## 十、论证点管理

### GET /api/appeal/{appeal_id}/arguments

获取上诉论证点列表。

### POST /api/appeal/{appeal_id}/arguments

添加论证点。

**请求体**

```json
{
  "title": "争议焦点二",
  "content": "关于利息计算的认定",
  "evidence_refs": ["evidence-003"]
}
```

### PUT /api/appeal/{appeal_id}/arguments/{arg_id}

更新论证点。

### DELETE /api/appeal/{appeal_id}/arguments/{arg_id}

删除论证点。

---

## 十一、错误响应

### 400 Bad Request

```json
{
  "error": "VALIDATION_ERROR",
  "message": "上诉期限已过",
  "details": [
    {
      "field": "filing_date",
      "message": "上诉日期必须在判决生效后15日内"
    }
  ]
}
```

### 404 Not Found

```json
{
  "error": "NOT_FOUND",
  "message": "上诉记录不存在",
  "appeal_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

---

*文档版本: v2.1.0*
*最后更新: 2026-04-02*
