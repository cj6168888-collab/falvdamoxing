# 案件API文档

> 案件管理相关API端点详细说明

---

## 一、案件列表

### GET /api/cases

获取当前用户的案件列表。

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量，最大100 |
| status | string | 否 | - | 状态过滤: pending/active/closed |
| type | string | 否 | - | 案件类型过滤 |
| search | string | 否 | - | 关键词搜索 |
| sort | string | 否 | created_at | 排序字段 |
| order | string | 否 | desc | 排序方向: asc/desc |

**响应示例**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "张三诉李四民间借贷纠纷案",
      "type": "debt_dispute",
      "status": "active",
      "plaintiff": "张三",
      "defendant": "李四",
      "amount": 100000.00,
      "court": "北京市朝阳区人民法院",
      "judge": "王法官",
      "filing_date": "2026-01-15",
      "next_hearing": "2026-04-20",
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-04-02T09:15:00Z"
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

## 二、案件详情

### GET /api/cases/{case_id}

获取指定案件的详细信息。

**Path参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string (UUID) | 是 | 案件ID |

**响应示例**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "张三诉李四民间借贷纠纷案",
  "type": "debt_dispute",
  "type_name": "民间借贷纠纷",
  "status": "active",
  "priority": "high",
  "plaintiff": "张三",
  "plaintiff_id": "party-001",
  "defendant": "李四",
  "defendant_id": "party-002",
  "amount": 100000.00,
  "court": "北京市朝阳区人民法院",
  "case_number": "(2026)朝民初字第1234号",
  "judge": "王法官",
  "lawyer": "赵律师",
  "filing_date": "2026-01-15",
  "next_hearing": "2026-04-20",
  "description": "被告李四于2025年6月向原告张三借款10万元...",
  "milestones": [
    {
      "id": "ms-001",
      "name": "立案",
      "status": "completed",
      "date": "2026-01-15"
    },
    {
      "id": "ms-002",
      "name": "送达",
      "status": "completed",
      "date": "2026-01-20"
    },
    {
      "id": "ms-003",
      "name": "开庭",
      "status": "upcoming",
      "date": "2026-04-20"
    }
  ],
  "tags": ["借贷", "民间", "紧急"],
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-04-02T09:15:00Z"
}
```

---

## 三、创建案件

### POST /api/cases

创建新案件。

**请求体**

```json
{
  "title": "张三诉李四民间借贷纠纷案",
  "type": "debt_dispute",
  "plaintiff": "张三",
  "plaintiff_contacts": {
    "phone": "13800138000",
    "email": "zhangsan@example.com",
    "address": "北京市朝阳区xxx"
  },
  "defendant": "李四",
  "defendant_contacts": {
    "phone": "13900139000",
    "address": "北京市海淀区xxx"
  },
  "amount": 100000.00,
  "court": "北京市朝阳区人民法院",
  "case_number": "(2026)朝民初字第1234号",
  "judge": "王法官",
  "filing_date": "2026-01-15",
  "description": "被告李四于2025年6月向原告张三借款10万元...",
  "template_id": "template-debt"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 案件标题，最大200字 |
| type | string | 是 | 案件类型代码 |
| plaintiff | string | 是 | 原告姓名 |
| defendant | string | 是 | 被告姓名 |
| plaintiff_contacts | object | 否 | 原告联系方式 |
| defendant_contacts | object | 否 | 被告联系方式 |
| amount | float | 否 | 诉讼金额 |
| court | string | 否 | 受理法院 |
| case_number | string | 否 | 案号 |
| judge | string | 否 | 审判法官 |
| filing_date | string | 否 | 立案日期，格式YYYY-MM-DD |
| description | string | 否 | 案件描述，最大5000字 |
| template_id | string | 否 | 使用模板ID |

**响应**: 201 Created

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "title": "张三诉李四民间借贷纠纷案",
  "status": "pending",
  "created_at": "2026-04-02T10:30:00Z",
  "message": "案件创建成功"
}
```

---

## 四、更新案件

### PUT /api/cases/{case_id}

更新案件信息。

**请求体**

```json
{
  "title": "张三诉李四民间借贷纠纷案（补充）",
  "status": "active",
  "plaintiff": "张三",
  "defendant": "李四",
  "amount": 120000.00,
  "next_hearing": "2026-05-15",
  "description": "补充描述..."
}
```

**响应**: 200 OK

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "张三诉李四民间借贷纠纷案（补充）",
  "updated_at": "2026-04-02T11:00:00Z",
  "message": "案件更新成功"
}
```

---

## 五、删除案件

### DELETE /api/cases/{case_id}

删除案件（软删除）。

**Path参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string (UUID) | 是 | 案件ID |

**响应**: 200 OK

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "deleted": true,
  "message": "案件已删除"
}
```

---

## 六、批量操作

### POST /api/cases/batch

批量操作案件。

**请求体**

```json
{
  "action": "archive",
  "case_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ]
}
```

| action | 说明 |
|--------|------|
| archive | 批量归档 |
| delete | 批量删除 |
| export | 批量导出 |
| tag | 批量添加标签 |

**响应**: 200 OK

```json
{
  "success": true,
  "processed": 3,
  "failed": 0,
  "results": [
    { "id": "case-001", "status": "success" },
    { "id": "case-002", "status": "success" },
    { "id": "case-003", "status": "success" }
  ]
}
```

---

## 七、案件模板

### GET /api/cases/templates

获取可用的案件模板列表。

**响应示例**

```json
{
  "items": [
    {
      "id": "template-debt",
      "name": "民间借贷纠纷",
      "description": "适用于自然人之间的借贷纠纷案件",
      "icon": "💰",
      "fields": {
        "plaintiff": {"required": true, "type": "text"},
        "defendant": {"required": true, "type": "text"},
        "amount": {"required": true, "type": "number"},
        "loan_date": {"required": true, "type": "date"},
        "due_date": {"required": true, "type": "date"}
      },
      "recommended_evidence": [
        "借条/欠条",
        "转账记录",
        "聊天记录",
        "证人证言"
      ],
      "recommended_documents": [
        "起诉状",
        "证据清单",
        "当事人身份证明"
      ]
    },
    {
      "id": "template-contract",
      "name": "合同纠纷",
      "description": "适用于各类合同争议案件",
      "icon": "📄",
      "fields": {...},
      "recommended_evidence": [...],
      "recommended_documents": [...]
    }
  ]
}
```

---

## 八、导出案件

### POST /api/cases/{case_id}/export

导出案件为指定格式。

**请求体**

```json
{
  "format": "zip",
  "include": [
    "case_info",
    "parties",
    "evidence",
    "documents",
    "meetings",
    "chat_history"
  ],
  "document_format": "docx"
}
```

| format | 说明 |
|--------|------|
| zip | 打包ZIP文件 |
| pdf | PDF格式 |
| json | JSON格式 |

**响应**: 200 OK (文件流)

```
Content-Type: application/zip
Content-Disposition: attachment; filename="case-001-export.zip"
```

---

## 九、错误响应

### 400 Bad Request

```json
{
  "error": "VALIDATION_ERROR",
  "message": "请求参数验证失败",
  "details": [
    {
      "field": "title",
      "message": "标题不能为空"
    },
    {
      "field": "amount",
      "message": "金额必须为正数"
    }
  ]
}
```

### 404 Not Found

```json
{
  "error": "NOT_FOUND",
  "message": "案件不存在",
  "case_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

*文档版本: v2.1.0*
*最后更新: 2026-04-02*
