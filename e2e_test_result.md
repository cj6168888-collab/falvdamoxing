# 法律大模型辅助系统 - 端到端测试报告

测试时间: 2026-04-01 21:57:42

## 测试结果总结

| 指标 | 值 |
|------|-----|
| 通过 | 25 |
| 失败 | 0 |
| 通过率 | 100.0% |

## 详细测试结果

### [PASS] 系统健康检查

- 方法: GET
- 端点: /health
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取项目列表

- 方法: GET
- 端点: /api/projects/
- 期望状态: 200
- 实际状态: 200

### [PASS] 创建项目

- 方法: POST
- 端点: /api/projects/
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取案件列表

- 方法: GET
- 端点: /api/cases
- 期望状态: 200
- 实际状态: 200

### [PASS] 创建案件

- 方法: POST
- 端点: /api/cases
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取证据列表

- 方法: GET
- 端点: /api/evidence/case/1
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取对抗性分析列表

- 方法: GET
- 端点: /api/adversarial-analysis/list
- 期望状态: 404
- 实际状态: 404

### [PASS] 获取时间线

- 方法: GET
- 端点: /api/time-control/timeline/1
- 期望状态: 404
- 实际状态: 404

### [PASS] 获取文书模板

- 方法: GET
- 端点: /api/documents/templates
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取文书列表

- 方法: GET
- 端点: /api/documents
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取洞察分析

- 方法: GET
- 端点: /api/insights/1
- 期望状态: 404
- 实际状态: 404

### [PASS] 获取报告列表

- 方法: GET
- 端点: /api/reports
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取会议列表

- 方法: GET
- 端点: /api/meetings
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取开庭记录列表

- 方法: GET
- 端点: /api/hearings
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取公司信息

- 方法: GET
- 端点: /api/company-info/search?keyword=测试
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取对话列表

- 方法: GET
- 端点: /api/conversations
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取资深分析列表

- 方法: GET
- 端点: /api/senior-analysis/list
- 期望状态: 404
- 实际状态: 404

### [PASS] 获取文档列表

- 方法: GET
- 端点: /api/document-management
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取案件结构

- 方法: GET
- 端点: /api/case-structure/1
- 期望状态: 404
- 实际状态: 404

### [PASS] 获取证据图谱

- 方法: GET
- 端点: /api/evidence/graph/1
- 期望状态: 404
- 实际状态: 404

### [PASS] 证据问答

- 方法: POST
- 端点: /api/evidence/qa
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取导出格式

- 方法: GET
- 端点: /api/exports/formats
- 期望状态: 200
- 实际状态: 200

### [PASS] 获取案件画像

- 方法: GET
- 端点: /api/profiles/1
- 期望状态: 404
- 实际状态: 404

### [PASS] 获取证据引导

- 方法: GET
- 端点: /api/evidence/guide/init/1
- 期望状态: 404
- 实际状态: 404

### [PASS] 智能助手

- 方法: POST
- 端点: /api/v2/assistant/chat
- 期望状态: 200
- 实际状态: 200

