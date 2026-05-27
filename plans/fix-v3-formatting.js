const fs = require('fs');
const path = 'd:\\www\\法律大模型\\plans\\法律案件追踪系统_前端重设计_v3.0.md';
let content = fs.readFileSync(path, 'utf-8');

// Normalize line endings
content = content.replace(/\r\n/g, '\n');

// Fix 1: Clean up the stray text around line 746-761 (conversation artifacts)
content = content.replace(
  /计划版本: v3\.0 — 模块化深度推演完整版 最后更新: 2026-04-02\n \n文档已完成。.*?请告诉我您的下一步指示。\n复制回复\nPlan · Qwen3\.6 Plus Free · 2分 37秒\n将剩余 15 个模块的完整内容追加到此文档\nPlan · Qwen3\.6 Plus Free\n```\n · \n```\n14:36\n重置到此点\n复制消息\n我注意到系统提醒我当前处于只读模式.*?以下是剩余 15 个模块（模块 7-21）的完整深度推演内容，准备追加到 v3\.0 计划文档：\n \n/g,
  ''
);

// Fix 2: Fix API mapping table (lines 1434-1654 area)
// The table is currently flattened - reconstruct it
const apiTableOld = `前端页面
后端端点
方法
说明
案件列表
/api/cases
GET
列表查询
案件详情
/api/cases/{id}
GET/PUT
CRUD
新建案件
/api/cases
POST
创建
案件分析
/api/cases/{id}/analyze
POST
AI 分析
案件策略
/api/cases/{id}/strategy
POST
策略生成
案件关闭
/api/cases/{id}/close
POST
结案
案件重启
/api/cases/{id}/reopen
POST
重开
案件结构
/api/cases/{id}/structure
GET
完整结构
当事人列表
/api/cases/{id}/parties
GET/POST
当事人管理
当事人更新
/api/cases/parties/{party_id}
PUT/DELETE
当事人操作
线索管理
/api/cases/{id}/threads
GET/POST
线索管理
反诉管理
/api/cases/{id}/counter-claims
GET/POST
反诉管理
对话发送
/api/v2/assistant/chat
POST
流式对话
对话历史
/api/v2/assistant/conversation-history/{case_id}
GET
历史记录
快捷问题
/api/v2/assistant/quick-actions/{case_id}
GET
预设问题
证据列表
/api/v2/evidence-graph/evidence/list
GET
V2 证据列表
证据详情
/api/v2/evidence-graph/evidence/{id}
GET
V2 证据详情
证据更新
/api/v2/evidence-graph/evidence/update
PUT
V2 证据更新
证据纠偏
/api/v2/evidence-graph/evidence/correct
POST
V2 人工纠偏
证据分析
/api/v2/evidence-graph/evidence/analyze
POST
V2 深度分析
证据关系
/api/v2/evidence-graph/relationships/analyze
POST
V2 关系分析
图谱数据
/api/v2/evidence-graph/graph/data
GET
V2 图谱数据
证据引导
/api/v2/evidence-guide/diagnose
POST
诊断证据缺口
引导问答
/api/v2/evidence-guide/question/answer
POST
回答引导问题
文书模板
/api/documents/templates
GET
模板列表
文书生成
/api/documents/generate/enhanced
POST
增强文书生成
文书列表
/api/document-management/case/{id}/generated
GET
生成文书列表
文书建议
/api/document-management/case/{id}/suggestions
GET/POST
文书建议
时间线
/api/时间把控/case/{id}/timeline
GET
完整时间线
截止日期
/api/时间把控/case/{id}/deadlines
GET/POST
截止日期
函件列表
/api/时间把控/case/{id}/letters
GET/POST
函件管理
函件更新
/api/时间把控/letters/{letter_id}
PUT/DELETE
函件操作
邮寄更新
/api/时间把控/letters/{letter_id}/mailing
POST
邮寄信息
送达确认
/api/时间把控/letters/{letter_id}/delivered
POST
确认送达
AI 回复草稿
/api/时间把控/letters/{letter_id}/generate-reply
POST
生成回复
里程碑生成
/api/时间把控/case/{id}/generate-milestones
POST
AI 里程碑
对抗性分析
/api/对抗性分析/case/{id}/analysis
POST
创建分析
完整分析
/api/对抗性分析/case/{id}/full-analysis
POST
一键完整分析
证据矩阵
/api/对抗性分析/case/{id}/evidence-matrix
POST
矩阵生成
情景预测
/api/对抗性分析/case/{id}/scenario-prediction
POST
情景预测
开庭记录
/api/hearings/case/{id}/hearings
GET/POST
庭审记录
庭审发言
/api/hearings/hearing/{id}/statement
POST
记录发言
实时分析
/api/hearings/realtime-analysis
POST
实时分析
陷阱检测
/api/hearings/detect-trap
POST
检测陷阱
资深分析
/api/v2/senior-analysis/analyze
POST
资深律师分析
案件画像
/api/v2/profile/summary/{case_id}
GET
画像摘要
知识图谱
/api/v2/profile/knowledge-graph/{case_id}
GET
知识图谱
报告生成
/api/reports/generate/{case_id}
POST
分段生成
报告状态
/api/reports/status/{case_id}
GET
生成状态
报告取消
/api/reports/cancel/{case_id}
POST
取消生成
企业信息
/api/company-info/{company_name}
GET
企业信息
企业搜索
/api/company-info/search?keyword=
GET
搜索企业
导出功能
/api/exports/*
GET/POST
多格式导出
提醒列表
/api/reminders
GET
提醒管理`;

const apiTableNew = `| 前端页面 | 后端端点 | 方法 | 说明 |
|---------|---------|------|------|
| 案件列表 | \`/api/cases\` | GET | 列表查询 |
| 案件详情 | \`/api/cases/{id}\` | GET/PUT | CRUD |
| 新建案件 | \`/api/cases\` | POST | 创建 |
| 案件分析 | \`/api/cases/{id}/analyze\` | POST | AI 分析 |
| 案件策略 | \`/api/cases/{id}/strategy\` | POST | 策略生成 |
| 案件关闭 | \`/api/cases/{id}/close\` | POST | 结案 |
| 案件重启 | \`/api/cases/{id}/reopen\` | POST | 重开 |
| 案件结构 | \`/api/cases/{id}/structure\` | GET | 完整结构 |
| 当事人列表 | \`/api/cases/{id}/parties\` | GET/POST | 当事人管理 |
| 当事人更新 | \`/api/cases/parties/{party_id}\` | PUT/DELETE | 当事人操作 |
| 线索管理 | \`/api/cases/{id}/threads\` | GET/POST | 线索管理 |
| 反诉管理 | \`/api/cases/{id}/counter-claims\` | GET/POST | 反诉管理 |
| 对话发送 | \`/api/v2/assistant/chat\` | POST | 流式对话 |
| 对话历史 | \`/api/v2/assistant/conversation-history/{case_id}\` | GET | 历史记录 |
| 快捷问题 | \`/api/v2/assistant/quick-actions/{case_id}\` | GET | 预设问题 |
| 证据列表 | \`/api/v2/evidence-graph/evidence/list\` | GET | V2 证据列表 |
| 证据详情 | \`/api/v2/evidence-graph/evidence/{id}\` | GET | V2 证据详情 |
| 证据更新 | \`/api/v2/evidence-graph/evidence/update\` | PUT | V2 证据更新 |
| 证据纠偏 | \`/api/v2/evidence-graph/evidence/correct\` | POST | V2 人工纠偏 |
| 证据分析 | \`/api/v2/evidence-graph/evidence/analyze\` | POST | V2 深度分析 |
| 证据关系 | \`/api/v2/evidence-graph/relationships/analyze\` | POST | V2 关系分析 |
| 图谱数据 | \`/api/v2/evidence-graph/graph/data\` | GET | V2 图谱数据 |
| 证据引导 | \`/api/v2/evidence-guide/diagnose\` | POST | 诊断证据缺口 |
| 引导问答 | \`/api/v2/evidence-guide/question/answer\` | POST | 回答引导问题 |
| 文书模板 | \`/api/documents/templates\` | GET | 模板列表 |
| 文书生成 | \`/api/documents/generate/enhanced\` | POST | 增强文书生成 |
| 文书列表 | \`/api/document-management/case/{id}/generated\` | GET | 生成文书列表 |
| 文书建议 | \`/api/document-management/case/{id}/suggestions\` | GET/POST | 文书建议 |
| 时间线 | \`/api/时间把控/case/{id}/timeline\` | GET | 完整时间线 |
| 截止日期 | \`/api/时间把控/case/{id}/deadlines\` | GET/POST | 截止日期 |
| 函件列表 | \`/api/时间把控/case/{id}/letters\` | GET/POST | 函件管理 |
| 函件更新 | \`/api/时间把控/letters/{letter_id}\` | PUT/DELETE | 函件操作 |
| 邮寄更新 | \`/api/时间把控/letters/{letter_id}/mailing\` | POST | 邮寄信息 |
| 送达确认 | \`/api/时间把控/letters/{letter_id}/delivered\` | POST | 确认送达 |
| AI 回复草稿 | \`/api/时间把控/letters/{letter_id}/generate-reply\` | POST | 生成回复 |
| 里程碑生成 | \`/api/时间把控/case/{id}/generate-milestones\` | POST | AI 里程碑 |
| 对抗性分析 | \`/api/对抗性分析/case/{id}/analysis\` | POST | 创建分析 |
| 完整分析 | \`/api/对抗性分析/case/{id}/full-analysis\` | POST | 一键完整分析 |
| 证据矩阵 | \`/api/对抗性分析/case/{id}/evidence-matrix\` | POST | 矩阵生成 |
| 情景预测 | \`/api/对抗性分析/case/{id}/scenario-prediction\` | POST | 情景预测 |
| 开庭记录 | \`/api/hearings/case/{id}/hearings\` | GET/POST | 庭审记录 |
| 庭审发言 | \`/api/hearings/hearing/{id}/statement\` | POST | 记录发言 |
| 实时分析 | \`/api/hearings/realtime-analysis\` | POST | 实时分析 |
| 陷阱检测 | \`/api/hearings/detect-trap\` | POST | 检测陷阱 |
| 资深分析 | \`/api/v2/senior-analysis/analyze\` | POST | 资深律师分析 |
| 案件画像 | \`/api/v2/profile/summary/{case_id}\` | GET | 画像摘要 |
| 知识图谱 | \`/api/v2/profile/knowledge-graph/{case_id}\` | GET | 知识图谱 |
| 报告生成 | \`/api/reports/generate/{case_id}\` | POST | 分段生成 |
| 报告状态 | \`/api/reports/status/{case_id}\` | GET | 生成状态 |
| 报告取消 | \`/api/reports/cancel/{case_id}\` | POST | 取消生成 |
| 企业信息 | \`/api/company-info/{company_name}\` | GET | 企业信息 |
| 企业搜索 | \`/api/company-info/search?keyword=\` | GET | 搜索企业 |
| 导出功能 | \`/api/exports/*\` | GET/POST | 多格式导出 |
| 提醒列表 | \`/api/reminders\` | GET | 提醒管理 |`;

content = content.replace(apiTableOld, apiTableNew);

// Fix 3: Fix the key features summary table (lines 1703-1790 area)
const featuresTableOld = `五、关键新增功能点总结
#
改进项
价值
1
可调整面板布局 (Resizable Panel)
同时查看多个模块，对比分析
2
证据因果链图谱 (而非力导向图)
符合法律推理逻辑
3
草稿自动保存 + 版本历史 + diff 对比
数据不丢失，支持回溯
4
时间截止「中断/顺延」建模
真实法律期限计算
5
争点驱动对抗性分析
比粗粒度文本更实用
6
案件财务追踪 (成本/收益/胜诉概率)
当事人最关心的决策数据
7
对抗性分析 → 庭审一键导入
减少重复操作
8
完整导出矩阵 (PDF/DOCX/MD/TXT)
真实可用的导出
9
证据 PDF 批注 + 关联管理
深度证据利用
10
智能快捷入口 (案件 + 页面 + 上下文)
从工作台直接定位
11
案件模板快速创建
避免空白表单，提效
12
可配置流程模板
不同案件类型用不同流程
13
当事人管理 (多角色/关系图/企业核查)
复杂案件当事人管理
14
线索与反诉管理
多诉求分支追踪
15
质证意见模块 (三性质证)
庭审核心环节
16
报告生成系统 (分段生成/6 种类型)
完整案件分析报告
17
函件管理 (收发/邮寄跟踪/送达证明)
律师实务核心工作流
18
提醒中心 (多类型统一管理)
不遗漏任何重要事项
19
深色模式
长时间工作护眼
20
打印样式优化
法律文书打印提交
21
键盘快捷键
高频用户提效
22
虚拟滚动
大数据量性能保障
23
对话 V2 澄清机制
精准理解用户意图
24
证据信度评分 (5 维度)
专业证据评估
25
证据人工纠偏
纠正 AI 错误
26
证据引导系统
主动引导收集证据
27
资深律师分析 (3 级深度)
模拟资深律师思维
28
案件画像持续学习
系统越用越懂案件`;

const featuresTableNew = `## 五、关键新增功能点总结

| # | 改进项 | 价值 |
|---|--------|------|
| 1 | **可调整面板布局** (Resizable Panel) | 同时查看多个模块，对比分析 |
| 2 | **证据因果链图谱** (而非力导向图) | 符合法律推理逻辑 |
| 3 | **草稿自动保存 + 版本历史 + diff 对比** | 数据不丢失，支持回溯 |
| 4 | **时间截止「中断/顺延」建模** | 真实法律期限计算 |
| 5 | **争点驱动对抗性分析** | 比粗粒度文本更实用 |
| 6 | **案件财务追踪** (成本/收益/胜诉概率) | 当事人最关心的决策数据 |
| 7 | **对抗性分析 → 庭审一键导入** | 减少重复操作 |
| 8 | **完整导出矩阵** (PDF/DOCX/MD/TXT) | 真实可用的导出 |
| 9 | **证据 PDF 批注 + 关联管理** | 深度证据利用 |
| 10 | **智能快捷入口** (案件 + 页面 + 上下文) | 从工作台直接定位 |
| 11 | **案件模板快速创建** | 避免空白表单，提效 |
| 12 | **可配置流程模板** | 不同案件类型用不同流程 |
| 13 | **当事人管理** (多角色/关系图/企业核查) | 复杂案件当事人管理 |
| 14 | **线索与反诉管理** | 多诉求分支追踪 |
| 15 | **质证意见模块** (三性质证) | 庭审核心环节 |
| 16 | **报告生成系统** (分段生成/6 种类型) | 完整案件分析报告 |
| 17 | **函件管理** (收发/邮寄跟踪/送达证明) | 律师实务核心工作流 |
| 18 | **提醒中心** (多类型统一管理) | 不遗漏任何重要事项 |
| 19 | **深色模式** | 长时间工作护眼 |
| 20 | **打印样式优化** | 法律文书打印提交 |
| 21 | **键盘快捷键** | 高频用户提效 |
| 22 | **虚拟滚动** | 大数据量性能保障 |
| 23 | **对话 V2 澄清机制** | 精准理解用户意图 |
| 24 | **证据信度评分** (5 维度) | 专业证据评估 |
| 25 | **证据人工纠偏** | 纠正 AI 错误 |
| 26 | **证据引导系统** | 主动引导收集证据 |
| 27 | **资深律师分析** (3 级深度) | 模拟资深律师思维 |
| 28 | **案件画像持续学习** | 系统越用越懂案件 |`;

content = content.replace(featuresTableOld, featuresTableNew);

// Fix 4: Fix section headings that are missing ## markers
content = content.replace(/\n三、API 对接方案/g, '\n\n## 三、API 对接方案');
content = content.replace(/\n### 3\.1 API Base URL\nVITE_API_BASE_URL/g, '\n### 3.1 API Base URL\n```\nVITE_API_BASE_URL');
content = content.replace(/\n提醒列表\n\/api\/reminders\nGET\n提醒管理\n \n\n## 四/g, '提醒列表 | `/api/reminders` | GET | 提醒管理 |\n\n---\n\n## 四');

// Fix 5: Fix implementation plan formatting
content = content.replace(/第一阶段：项目基础（1-2 天）\n1\./g, '### 第一阶段：项目基础（1-2 天）\n1.');
content = content.replace(/第二阶段：核心页面（3-4 天）\n1\./g, '\n### 第二阶段：核心页面（3-4 天）\n1.');
content = content.replace(/第三阶段：功能实现（5-8 天）\n1\./g, '\n### 第三阶段：功能实现（5-8 天）\n1.');
content = content.replace(/第四阶段：高级功能（9-12 天）\n1\./g, '\n### 第四阶段：高级功能（9-12 天）\n1.');
content = content.replace(/第五阶段：收尾（13-14 天）\n1\./g, '\n### 第五阶段：收尾（13-14 天）\n1.');

// Fix 6: Fix file清单 formatting
content = content.replace(/需创建的核心文件（约 200 个）：\n配置文件/g, '需创建的核心文件（约 200 个）：\n\n- **配置文件 (7):** ');
content = content.replace(/\.env\.example\n类型定义/g, '.env.example\n- **类型定义 (22):** ');
content = content.replace(/src\/types\/\*\.ts\nAPI 客户端/g, 'src/types/*.ts\n- **API 客户端 (19):** ');
content = content.replace(/src\/api\/\*\.ts\nZustand Store/g, 'src/api/*.ts\n- **Zustand Store (7):** ');
content = content.replace(/src\/stores\/\*\.ts\n自定义 Hooks/g, 'src/stores/*.ts\n- **自定义 Hooks (21):** ');
content = content.replace(/src\/hooks\/\*\.ts\n工具函数/g, 'src/hooks/*.ts\n- **工具函数 (7):** ');
content = content.replace(/src\/lib\/export\/\*\nUI 组件/g, 'src/lib/export/*\n- **UI 组件 (35+):** ');
content = content.replace(/src\/components\/ui\/\*\n业务组件/g, 'src/components/ui/*\n- **业务组件 (70+):** ');
content = content.replace(/src\/components\/\*\/\*\n页面/g, 'src/components/*/*\n- **页面 (24):** ');
content = content.replace(/src\/pages\/\*\/index\.tsx\n样式/g, 'src/pages/*/index.tsx\n- **样式 (3):** ');
content = content.replace(/src\/styles\/dark-mode\.css\n入口/g, 'src/styles/dark-mode.css\n- **入口 (2):** ');

// Fix 7: Fix compatibility section formatting
content = content.replace(/7\.2 暂不覆盖的后端功能/g, '\n### 7.2 暂不覆盖的后端功能');
content = content.replace(/### 7\.3 数据迁移策略/g, '\n### 7.3 数据迁移策略');

// Clean up extra blank lines
content = content.replace(/\n{4,}/g, '\n\n\n');

// Remove any remaining "复制" or "复制回复" text
content = content.replace(/复制回复/g, '');
content = content.replace(/复制消息/g, '');

// Write back
fs.writeFileSync(path, content, 'utf-8');
console.log('All formatting fixes applied successfully!');
