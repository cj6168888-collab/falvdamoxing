# 智能对话模块 - 完整开发计划

> 核心理念：用户只陈述事实，系统读取全部证据后生成可复核的法律工作底稿，用户确认后再写入案件字段。

---

## 一、用户需求清单

| # | 需求 | 说明 |
|---|------|------|
| 1 | 用户只陈述事实 | 不用懂法律，说清楚发生了什么就行 |
| 2 | 系统先读取全部证据 | 回答任何问题前，必须展示已读取的证据范围和未核验材料 |
| 3 | 系统主动生成工作底稿 | 可主张什么权利、主张多少金额、对方可能提出哪些抗辩，均需标注依据和待复核项 |
| 4 | 用户确认后自动填入 | 点"认可"后，金额/案由等自动更新到案件 |
| 5 | 多轮对话有上下文 | 说"重新回答"时 AI 知道之前聊了什么 |
| 6 | 推荐文书可生成草稿 | 分析后推荐文书类型，点击生成可复核的文书草稿 |
| 7 | 分析结果可导出 | PDF/Word/完整对话记录 导出按钮始终可见 |
| 8 | 排版美观 | 表格、标题、重点高亮，无乱码符号 |
| 9 | 展示已读证据清单 | 让用户知道系统到底看了哪些证据、哪些证据仍缺少原件或页码 |
| 10 | 对话内直接上传证据 | 不用跳转证据管理页面 |
| 11 | 认可的分析结果可视化 | 绿色标记 + 置顶，作为主要脉络参考 |
| 12 | 对话历史可回溯 | 可查看之前所有分析结果 |
| 13 | 案件状态一目了然 | 进入对话时看到当事人/案由/金额/证据数 |
| 14 | 证据缺失结构化提醒 | 不是笼统说"建议补充"，而是具体指出缺什么 |
| 15 | 批量生成文书草稿 | 推荐多份文书时，可批量生成草稿，并在导出前逐项核验当事人、金额、事实、证据、法条、管辖和签章 |

---

## 二、响应式适配策略

| 设备 | 断点 | 适配要点 |
|------|------|---------|
| 手机竖屏 | < 640px | 单列布局，操作栏折叠为 `⋯` 更多菜单，输入框固定底部 |
| 手机横屏/平板竖屏 | 640-1024px | 双列布局（左侧消息/右侧建议卡片），操作栏平铺 |
| 平板横屏/桌面 | 1024-1440px | 三列布局（左侧证据面板/中间对话/右侧建议卡片） |
| 大屏桌面 | > 1440px | 最大宽度限制，内容居中，两侧留白 |

### 关键适配规则

| 组件 | 手机 (<640px) | 平板 (640-1024px) | 桌面 (>1024px) |
|------|---------------|-------------------|----------------|
| 证据面板 | 隐藏，点击按钮抽屉弹出 | 可收起/展开的侧栏 | 固定左侧栏 |
| 推荐文书 | 纵向堆叠 | 横向排列（2列） | 横向排列（多列） |
| 操作按钮 | 折叠进 `⋯` 菜单 | 全部平铺 | 全部平铺 |
| 输入框 | 固定底部（类似微信） | 跟随页面滚动 | 跟随页面滚动 |
| Markdown 表格 | 横向滚动 | 正常显示 | 正常显示 |
| 引导页 | 全宽 | 居中 max-w-3xl | 居中 max-w-3xl |
| 建议卡片 | 纵向堆叠 | 纵向堆叠 | 纵向堆叠 |
| 金额计算器 | 全宽 | 正常 | 正常 |

---

## 三、开发阶段

### 阶段 1：核心重写（必须）

- [ ] 删除现有 `frontend/src/pages/smart-chat/[caseId].tsx`
- [ ] 从头重写：`useState` 管理消息，不用 `useQuery`，彻底解决闪烁
- [ ] 引导页 → 进度条 → 对话页，原地切换不跳转
- [ ] 进度条 7 步实时推进（前端模拟 + 后端完成时同步）
- [ ] 参数兼容 `caseId` 和 `id`
- [ ] 响应式：手机单列 / 平板双列 / 桌面三列

### 阶段 2：证据感知（关键）

- [ ] 对话页顶部显示"已读取 X 份证据"徽章
- [ ] 点击展开证据清单 + AI 对每份证据的理解摘要
- [ ] 证据缺失时显示红色警告卡片
- [ ] 对话内直接上传新证据按钮
- [ ] 响应式：手机证据面板为抽屉式弹出 / 桌面为固定侧栏

### 阶段 3：交互完善

- [ ] 推荐文书区域始终可见 + "一键全部生成"按钮
- [ ] 导出按钮始终可见（PDF / Word / 完整对话记录）
- [ ] 认可的分析结果带绿色标记 + 置顶显示
- [ ] 重答按钮携带完整上下文
- [ ] 金额建议显示可交互计算器
- [ ] 响应式：手机操作栏折叠为 `⋯` 菜单 / 桌面全部平铺

### 阶段 4：入口和体验

- [ ] 引导页增加案件状态概览（当事人 / 案由 / 当前金额 / 证据数）
- [ ] 侧边栏和案件详情页统一入口
- [ ] 空证据列表时引导用户先上传证据
- [ ] 错误提示明确（后端未运行 / 案件不存在 / 分析失败）
- [ ] 响应式：引导页手机全宽 / 桌面居中最大宽度 3xl

### 阶段 5：后端确认

- [ ] `_build_complete_case_dossier()` 返回所有证据完整内容
- [ ] `follow-up` 携带完整案件档案 + 对话历史
- [ ] 所有 API 错误返回格式统一
- [ ] 新增：对话内证据上传 API 可用

---

## 四、文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/pages/smart-chat/[caseId].tsx` | **删除重写** | 主页面，包含所有状态管理和布局 |
| `frontend/src/components/smart-chat/message-bubble.tsx` | **新建** | 消息气泡组件（含响应式操作栏） |
| `frontend/src/components/smart-chat/evidence-panel.tsx` | **新建** | 证据感知面板（手机抽屉/桌面侧栏） |
| `frontend/src/components/smart-chat/suggestion-cards.tsx` | **新建** | 结构化建议卡片（权利/金额/风险/防守） |
| `frontend/src/components/smart-chat/document-recommendations.tsx` | **新建** | 推荐文书（手机纵向/桌面横向） |
| `frontend/src/components/smart-chat/progress-view.tsx` | **新建** | 进度条组件（7步分析流程） |
| `frontend/src/components/smart-chat/case-overview-bar.tsx` | **新建** | 引导页案件概览 |
| `app/api/smart_chat.py` | **确认** | 无需大改，确认 API 正常 |

---

## 五、架构设计

```
SmartChatPage (主页面)
├── 状态管理（useState，不依赖 useQuery）
│   ├── messages: ChatMessage[]
│   ├── isAnalyzing: boolean
│   ├── progress: { step, percent }
│   ├── hasStarted: boolean
│   └── caseInfo: CaseInfo | null
│
├── 引导页（hasStarted=false）
│   ├── CaseOverviewBar - 案件状态概览
│   ├── 事实描述 Textarea
│   ├── 角色选择（原告/被告/第三方）
│   ├── 预期输入（可选）
│   └── "开始案情分析" 按钮
│
├── 分析中（isAnalyzing=true）
│   ├── ProgressView - 7步进度条
│   └── 步骤文字提示
│
├── 对话页（hasStarted=true && !isAnalyzing）
│   ├── EvidencePanel - 证据感知面板（响应式）
│   ├── 消息列表
│   │   └── MessageBubble - 每条消息
│   │       ├── 用户消息（蓝色背景）
│   │       └── AI 消息
│   │           ├── 操作栏（展开/认可/重答/删除/导出）
│   │           ├── SuggestionCards - 结构化建议
│   │           ├── DocumentRecommendations - 推荐文书
│   │           └── MarkdownContent - 完整分析
│   └── 底部输入框（补充/纠正/提问）
│
└── API 调用
    ├── globalAnalysis → POST /api/smart-chat/global-analysis
    ├── followUp → POST /api/smart-chat/follow-up
    ├── approve → POST /api/smart-chat/approve
    ├── delete → POST /api/smart-chat/delete
    ├── export → POST /api/exports
    ├── generateDoc → POST /api/smart-chat/generate-document
    └── uploadEvidence → POST /api/evidence/upload
```

---

## 六、API 端点清单

| 端点 | 方法 | 用途 | 状态 |
|------|------|------|------|
| `/api/smart-chat/global-analysis` | POST | 全局案情分析 | ✅ 已有 |
| `/api/smart-chat/follow-up` | POST | 后续对话 | ✅ 已有 |
| `/api/smart-chat/approve` | POST | 认可分析结果 | ✅ 已有 |
| `/api/smart-chat/delete` | POST | 删除分析结果 | ✅ 已有 |
| `/api/smart-chat/confirm-suggestion` | POST | 确认建议并填入案件 | ✅ 已有 |
| `/api/smart-chat/analyses/{case_id}` | GET | 获取分析历史 | ✅ 已有 |
| `/api/smart-chat/generate-document` | POST | 生成推荐文书 | ✅ 已有 |
| `/api/exports` | POST | 导出内容 | ✅ 已有 |
| `/api/evidence/upload` | POST | 上传证据 | ✅ 已有 |

---

## 七、响应式断点定义

```typescript
// Tailwind 默认断点
// sm: 640px   - 手机横屏
// md: 768px   - 平板竖屏
// lg: 1024px  - 平板横屏/小桌面
// xl: 1280px  - 桌面
// 2xl: 1536px - 大屏桌面
```

### 布局示例

```tsx
// 主容器
<div className="flex h-screen">
  {/* 证据面板 - 手机隐藏，桌面显示 */}
  <div className="hidden lg:block w-64 border-r">
    <EvidencePanel />
  </div>

  {/* 对话区域 - 始终显示 */}
  <div className="flex-1 flex flex-col min-w-0">
    <MessageList />
    <InputBar />
  </div>

  {/* 建议卡片 - 手机隐藏，平板以上显示 */}
  <div className="hidden md:block w-80 border-l">
    <SuggestionCards />
  </div>
</div>
```

---

生成时间：2026-04-05
更新时间：2026-04-05
状态：✅ 全部功能已完成

## 八、实现状态总结（2026-04-05）

### 新增组件

| 文件 | 说明 | 状态 |
|------|------|------|
| `suggestion-cards.tsx` | 结构化建议卡片组件 | ✅ 已创建 |
| `document-recommendations.tsx` | 推荐文书组件 | ✅ 已创建 |
| `amount-calculator.tsx` | 金额计算器组件 | ✅ 已创建 |
| `evidence-warning.tsx` | 证据缺失警告卡片 | ✅ 已创建 |
| `evidence-uploader.tsx` | 证据上传组件 | ✅ 已创建 |
| `evidence-summary.tsx` | 证据理解摘要组件 | ✅ 已创建 |
| `action-bar.tsx` | 操作按钮折叠组件 | ✅ 已创建 |

### 核心功能完成情况

| 需求 | 状态 |
|------|------|
| 对话内直接上传证据 | ✅ 已实现 |
| 金额建议显示可交互计算器 | ✅ 已实现 |
| 证据缺失红色警告卡片 | ✅ 已实现 |
| 认可分析结果置顶 | ✅ 已实现 |
| AI 证据理解摘要 | ✅ 已实现 |
| 手机端操作按钮折叠 | ✅ 已实现 |

### 优化功能（第二轮）

| 功能 | 状态 |
|------|------|
| 金额计算器确认后调用 API 更新案件 | ✅ 已实现 |
| 证据上传后提示重新分析 | ✅ 已实现 |
| 完整对话记录导出 | ✅ 已实现 |
| 证据面板集成 AI 摘要展示（可展开） | ✅ 已实现 |

### 技术优化

| 项目 | 状态 |
|------|------|
| 使用 axiosInstance 替代直接 axios | ✅ 已修复 |
| 类型安全强化（ActionButton 接口） | ✅ 已修复 |
| 无 lint 错误 | ✅ 检查通过 |
