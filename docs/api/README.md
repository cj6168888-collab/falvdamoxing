# API文档概览

> 法律案件追踪系统 RESTful API 文档

---

## 一、API概述

### 1.1 基本信息

| 属性 | 值 |
|------|------|
| 版本 | v2.1.0 |
| Base URL | `/api` |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |

### 1.2 认证方式

```
Authorization: Bearer <token>
```

### 1.3 错误响应格式

```json
{
  "error": "VALIDATION_ERROR",
  "message": "请求参数验证失败",
  "details": [
    {
      "field": "title",
      "message": "标题不能为空"
    }
  ],
  "request_id": "req_abc123"
}
```

### 1.4 错误码

| HTTP状态码 | 错误码 | 说明 |
|------------|--------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |
| 400 | INVALID_FORMAT | 数据格式错误 |
| 401 | UNAUTHORIZED | 未授权 |
| 403 | FORBIDDEN | 无权限 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 资源冲突 |
| 422 | UNPROCESSABLE | 无法处理的实体 |
| 429 | RATE_LIMITED | 请求过于频繁 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 |

---

## 二、API模块

### 2.1 案件管理

| 模块 | 端点 | 说明 |
|------|------|------|
| 案件列表 | `GET /cases` | 获取案件列表 |
| 案件详情 | `GET /cases/{id}` | 获取案件详情 |
| 创建案件 | `POST /cases` | 创建新案件 |
| 更新案件 | `PUT /cases/{id}` | 更新案件 |
| 删除案件 | `DELETE /cases/{id}` | 删除案件 |
| 批量操作 | `POST /cases/batch` | 批量操作 |
| 案件模板 | `GET /cases/templates` | 获取模板列表 |
| 案件导出 | `POST /cases/{id}/export` | 导出案件 |

详细文档: [案件API](./cases.md)

### 2.2 当事人管理

| 模块 | 端点 | 说明 |
|------|------|------|
| 当事人列表 | `GET /cases/{id}/parties` | 获取当事人列表 |
| 添加当事人 | `POST /cases/{id}/parties` | 添加当事人 |
| 更新当事人 | `PUT /parties/{id}` | 更新当事人 |
| 删除当事人 | `DELETE /parties/{id}` | 删除当事人 |
| 企业核查 | `GET /companies/search` | 企业信息查询 |
| 企业详情 | `GET /companies/{id}` | 企业详细信息 |

### 2.3 证据管理

| 模块 | 端点 | 说明 |
|------|------|------|
| 证据列表 | `GET /cases/{id}/evidence` | 获取证据列表 |
| 添加证据 | `POST /cases/{id}/evidence` | 添加证据 |
| 更新证据 | `PUT /evidence/{id}` | 更新证据 |
| 删除证据 | `DELETE /evidence/{id}` | 删除证据 |
| 证据分析 | `POST /evidence/{id}/analyze` | AI证据分析 |
| 证据缺口 | `GET /cases/{id}/evidence/gaps` | 获取证据缺口 |
| 证据册导出 | `POST /cases/{id}/evidence/export` | 导出证据册 |

### 2.4 文书管理

| 模块 | 端点 | 说明 |
|------|------|------|
| 文书列表 | `GET /cases/{id}/documents` | 获取文书列表 |
| 生成文书 | `POST /documents/generate` | 生成文书 |
| 文书详情 | `GET /documents/{id}` | 获取文书详情 |
| 更新文书 | `PUT /documents/{id}` | 更新文书 |
| 删除文书 | `DELETE /documents/{id}` | 删除文书 |
| 版本历史 | `GET /documents/{id}/versions` | 获取版本历史 |
| 版本对比 | `GET /documents/{id}/diff` | 对比版本差异 |
| 恢复版本 | `POST /documents/{id}/versions/{vid}/restore` | 恢复版本 |

### 2.5 上诉追踪

| 模块 | 端点 | 说明 |
|------|------|------|
| 上诉列表 | `GET /case/{id}/appeal` | 获取上诉列表 |
| 创建上诉 | `POST /case/{id}/appeal` | 创建上诉 |
| 上诉详情 | `GET /appeal/{id}` | 获取上诉详情 |
| 更新上诉 | `PUT /appeal/{id}` | 更新上诉 |
| 删除上诉 | `DELETE /appeal/{id}` | 删除上诉 |
| 期限倒计时 | `GET /appeal/{id}/countdown` | 获取期限倒计时 |
| 生成上诉状 | `POST /appeal/{id}/generate-document` | 生成上诉状 |
| 更新状态 | `PUT /appeal/{id}/status` | 更新上诉状态 |

详细文档: [上诉API](./appeal.md)

### 2.6 执行跟踪

| 模块 | 端点 | 说明 |
|------|------|------|
| 执行记录列表 | `GET /case/{id}/execution` | 获取执行记录 |
| 创建执行记录 | `POST /case/{id}/execution` | 创建执行记录 |
| 执行详情 | `GET /execution/{id}` | 获取执行详情 |
| 更新执行 | `PUT /execution/{id}` | 更新执行 |
| 删除执行 | `DELETE /execution/{id}` | 删除执行 |
| 执行进度 | `GET /execution/{id}/progress` | 获取执行进度 |
| 更新金额 | `POST /execution/{id}/amount` | 更新执行金额 |
| 执行概况 | `GET /case/{id}/execution/summary` | 获取执行概况 |

### 2.7 提醒中心

| 模块 | 端点 | 说明 |
|------|------|------|
| 提醒列表 | `GET /reminders` | 获取所有提醒 |
| 创建提醒 | `POST /reminders` | 创建提醒 |
| 提醒详情 | `GET /reminders/{id}` | 获取提醒详情 |
| 更新提醒 | `PUT /reminders/{id}` | 更新提醒 |
| 删除提醒 | `DELETE /reminders/{id}` | 删除提醒 |
| 批量操作 | `POST /reminders/batch` | 批量操作 |
| 提醒统计 | `GET /reminders/stats` | 获取提醒统计 |

### 2.8 会议管理

| 模块 | 端点 | 说明 |
|------|------|------|
| 会议列表 | `GET /cases/{id}/meetings` | 获取会议列表 |
| 创建会议 | `POST /cases/{id}/meetings` | 创建会议 |
| 会议详情 | `GET /meetings/{id}` | 获取会议详情 |
| 更新会议 | `PUT /meetings/{id}` | 更新会议 |
| 删除会议 | `DELETE /meetings/{id}` | 删除会议 |
| 会议录音 | `POST /meetings/{id}/recording` | 上传录音 |
| 录音验证 | `POST /meetings/{id}/recording/verify` | 验证录音完整性 |

### 2.9 法律资料库

| 模块 | 端点 | 说明 |
|------|------|------|
| 搜索法条 | `GET /legal/articles` | 搜索法律条文 |
| 法条详情 | `GET /legal/articles/{id}` | 获取法条详情 |
| 搜索解释 | `GET /legal/interpretations` | 搜索司法解释 |
| 解释详情 | `GET /legal/interpretations/{id}` | 获取解释详情 |
| 搜索案例 | `GET /legal/cases` | 搜索指导案例 |
| 案例详情 | `GET /legal/cases/{id}` | 获取案例详情 |
| 综合搜索 | `POST /legal/search` | 综合检索 |
| RAG检索 | `POST /legal/rag` | RAG检索生成 |

详细文档: [法律资料库API](./legal-knowledge.md)

### 2.10 智能对话

| 模块 | 端点 | 说明 |
|------|------|------|
| 发送消息 | `POST /chat` | 发送对话消息 |
| 获取历史 | `GET /chat/history/{case_id}` | 获取对话历史 |
| 意图识别 | `POST /chat/intent` | 识别用户意图 |
| 澄清问题 | `POST /chat/clarify` | 生成澄清问题 |

### 2.11 LLM服务

| 模块 | 端点 | 说明 |
|------|------|------|
| 生成文书 | `POST /llm/generate-document` | 生成法律文书 |
| 证据分析 | `POST /llm/analyze-evidence` | AI证据分析 |
| 案件预测 | `POST /llm/predict` | 案件结果预测 |
| 路由状态 | `GET /llm/router/status` | 路由状态 |

### 2.12 工作台

| 模块 | 端点 | 说明 |
|------|------|------|
| 案件统计 | `GET /dashboard/stats` | 获取案件统计 |
| 紧急待办 | `GET /dashboard/urgent` | 获取紧急待办 |
| 近期待办 | `GET /dashboard/upcoming` | 获取近期待办 |
| AI建议 | `GET /dashboard/suggestions` | 获取AI建议 |

### 2.13 案件财务

| 模块 | 端点 | 说明 |
|------|------|------|
| 财务汇总 | `GET /case/{id}/finance` | 获取财务汇总 |
| 费用记录 | `GET /case/{id}/fees` | 获取费用记录 |
| 添加费用 | `POST /case/{id}/fees` | 添加费用 |
| 诉讼风险评估 | `POST /case/{id}/estimate` | 裁判支持度参考与成本收益评估 |
| 成本收益 | `GET /case/{id}/cost-benefit` | 成本收益分析 |

---

## 三、公共参数

### 3.1 分页参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |
| max_page_size | int | 100 | 最大每页数量 |

### 3.2 排序参数

| 参数 | 说明 |
|------|------|
| sort | 排序字段 |
| order | asc/desc |

### 3.3 过滤参数

各接口支持不同的过滤参数，详见各模块文档。

---

## 四、速率限制

| 等级 | 限制 | 说明 |
|------|------|------|
| 免费版 | 100次/分钟 | 普通用户 |
| 专业版 | 500次/分钟 | 付费用户 |
| 企业版 | 无限制 | 企业用户 |

---

## 五、Webhook

支持Webhook回调，配置请参阅Webhook文档。

---

## 六、SDK

| 语言 | SDK | 仓库 |
|------|------|------|
| JavaScript | @legal-tracker/sdk | npm |
| Python | legal-tracker-sdk | pip |
| Java | legal-tracker-java | maven |
| Go | legal-tracker-go | github |

---

*文档版本: v2.1.0*
*最后更新: 2026-04-02*
