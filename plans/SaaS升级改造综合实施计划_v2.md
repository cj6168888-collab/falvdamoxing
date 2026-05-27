# 法律大模型 SaaS 升级改造综合实施计划

> 创建时间：2026-05-07
> 版本：v1.0
> 状态：规划中

---

## 一、现状分析

### 1.1 已有的技术基础

经过对代码库的全面分析，当前系统已有以下基础设施：

#### 多租户架构（已实现）
| 组件 | 状态 | 说明 |
|------|------|------|
| `Tenant` 模型 | ✅ 完整 | 包含租户类型（LAW_FIRM/ENTERPRISE）、订阅计划、Stripe集成字段、配额管理 |
| `User` 模型 | ✅ 完整 | 关联 tenant_id，支持 ADMIN/LAWYER/ASSISTANT/CLIENT/VIEWER 角色 |
| `TenantContext` | ✅ 完整 | 基于 contextvars 的线程/协程安全租户隔离 |
| JWT 认证 | ✅ 完整 | token 包含 tenant_id，支持角色权限 |
| 订阅配额 | ✅ 字段存在 | max_users/max_cases/max_storage_gb/ai_daily_quota 已建模但未校验 |

#### LLM 路由架构（已实现）
| 组件 | 状态 | 说明 |
|------|------|------|
| Ollama 服务 | ✅ 已集成 | multi_model_ollama.py 支持多模型管理 |
| DashScope 云端 | ✅ 已集成 | qwen3.5-plus 等模型 |
| 智能路由器 | ✅ 已实现 | legal_llm_router.py 按任务类型路由 |
| 本地嵌入 | ✅ 已配置 | sentence-transformers |
| 法律专业模型 | ⚠️ 设计中 | legalone-r1:8b/4b 已在配置中定义但未部署 |

#### 前端（部分实现）
| 组件 | 状态 | 说明 |
|------|------|------|
| 案件管理 | ✅ 完整 | 列表/详情/新建等 |
| 证据管理 | ✅ V2已完成 | 证据图谱、引导、问答 |
| 对抗性分析 | ✅ 完整 | 辩论、场景预测 |
| 报告生成 | ✅ 完整 | 流式生成 |
| 法律知识库 | ✅ 基础完成 | 搜索、导入导出 |
| 登录认证 | ⚠️ Mock状态 | 前端登录为模拟，未对接后端 |
| 用户分群展示 | ❌ 不存在 | 无律所/企业差异化界面 |
| SaaS 落地页 | ❌ 不存在 | 无注册/定价页面 |

### 1.2 关键差距

| 优先级 | 差距 | 说明 |
|--------|------|------|
| P0 | 前端登录未对接 | login.tsx 为 mock，存储假 token |
| P0 | 本地法律LLM未部署 | legalone-r1 模型未下载/配置 |
| P0 | 订阅配额未校验 | max_users/cases/ai_quota 有字段无校验 |
| P1 | 用户分群UI | 律所/企业端界面差异 |
| P1 | SaaS 注册/定价页 | 多租户注册流程 |
| P1 | Stripe 集成 | 订阅计费未实现 |
| P2 | 品牌定制 | 自定义域名/Logo/配色 |

---

## 二、整体架构设计

### 2.1 三层 LLM 融合架构

```
用户请求
    │
    ▼
┌─────────────────────────────┐
│   Legal LLM Router          │
│   (智能任务分类)              │
└──────────────┬──────────────┘
               │
       ┌───────┼───────┐
       │       │       │
       ▼       ▼       ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│ 法律专家 │ │ 通识推理  │ │ 云端超大规模 │
│ 本地模型 │ │ 本地模型  │ │ 云端大模型   │
│ (Ollama) │ │ (Ollama) │ │ (DashScope) │
│          │ │          │ │              │
│法律one- R1│ │DeepSeek-  │ │ Qwen3.5-max │
│8B/4B     │ │R1 7B     │ │ /Plus       │
│本地部署  │ │本地部署  │ │API调用      │
└──────────┘ └──────────┘ └──────────────┘
```

**模型部署目录**：`D:\www\法律大模型\models\`

| 模型 | 用途 | 参数量 | 显存需求 | 部署方式 |
|------|------|--------|----------|----------|
| **法律one-R1** (legalone-r1) | 法律专业任务 | 4B / 8B | 6GB / 10GB | Ollama 本地 |
| **DeepSeek-R1 7B** | 通识推理 | 7B | 8GB | Ollama 本地 |
| **Qwen3.5-max** (云端) | 复杂任务兜底 | - | - | DashScope API |

### 2.2 SaaS 多租户架构

```
                    ┌─────────────┐
                    │   Nginx     │
                    │ (TLS + LB)  │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ SaaS 落地 │  │ React    │  │ Streamlit│
      │ 页/注册   │  │ 前端      │  │ 轻量端   │
      └────┬─────┘  └────┬─────┘  └────┬─────┘
           │             │             │
           └─────────────┼─────────────┘
                         │ HTTPS
                         ▼
                 ┌──────────────┐
                 │ FastAPI      │
                 │ (多租户隔离)  │
                 └──────┬───────┘
                        │
     ┌──────────────────┼──────────────────┐
     │                  │                  │
     ▼                  ▼                  ▼
┌──────────┐    ┌──────────────┐   ┌──────────┐
│PostgreSQL│    │   Redis      │   │  Ollama  │
│(多租户DB)│    │ (缓存/限流)  │   │(本地LLM) │
└──────────┘    └──────────────┘   └──────────┘
```

### 2.3 用户分群设计

```
┌──────────────────────────────────────────────┐
│                  用户类型                      │
│         Law Firm (律所)  │  Enterprise (企业) │
├──────────────────────────┼───────────────────┤
│                          │                   │
│ 【功能侧重】               │ 【功能侧重】        │
│ · 诉讼全流程管理           │ · 合同风险管控     │
│ · 证据对抗分析             │ · 合规审查         │
│ · 出庭抗辩辅助             │ · 咨询答复         │
│ · 上诉追踪                 │ · 项目法务顾问     │
│ · 时间把控（法定期限）      │ · 风险预警         │
│                          │                   │
│ 【UI特征】                 │ 【UI特征】         │
│ · 案件列表为主入口         │ · 仪表盘为主入口   │
│ · 左侧：案件树状导航       │ · 左侧：项目列表   │
│ · 证据/文书并列显示        │ · 合同管理突出     │
│ · 出庭抗辩专属Tab          │ · 风险看板         │
│ · 时间轴（司法流程）        │ · 合同时间轴       │
│                          │                   │
│ 【导航结构】               │ 【导航结构】        │
│ · 工作台/案件/项目        │ · 工作台/项目/合同  │
│ · 案件详情(9+子Tab)       │ · 项目详情(替代案件) │
│ · 证据管理(独立)           │ · 合同管理(突出)   │
│ · 出庭抗辩(独立)           │ · 合规咨询(独立)   │
│ · 上诉追踪(独立)           │ · 风险监控(独立)   │
│ · 执行跟踪(独立)           │ · 费用管理(精简)   │
└──────────────────────────┴───────────────────┘
```

---

## 三、实施计划

### 阶段划分概览

| 阶段 | 时间 | 主题 | 核心交付 |
|------|------|------|----------|
| **Phase 0** | 第1周 | 基础设施补全 | 前端登录对接 + 本地LLM部署 |
| **Phase 1** | 第2-3周 | SaaS核心 | 多租户注册 + 订阅配额 + 后台管理 |
| **Phase 2** | 第4-5周 | 用户分群UI | 律所/企业差异化界面 |
| **Phase 3** | 第6-7周 | 计费生态 | Stripe订阅 + 定价页 + 品牌定制 |
| **Phase 4** | 第8周 | 优化上线 | 性能优化 + 监控 + 部署文档 |

**总工期**：约 8 周（可并行压缩至 5-6 周）

---

## 四、Phase 0：基础设施补全（第1周）

### 4.1 前端登录对接后端（5人日）

**现状**：login.tsx 存储假 token `btoa('username:Date.now()')`，未调用任何后端API。

**目标**：对接 `/api/auth/register` 和 `/api/auth/login`。

**需要修改的文件**：

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/api/auth.api.ts` | 新建 | auth 专用 API 模块 |
| `frontend/src/stores/auth.store.ts` | 新建 | auth 状态管理（token/用户信息） |
| `frontend/src/pages/login.tsx` | 修改 | 调用真实登录API |
| `frontend/src/pages/register.tsx` | 新建 | 注册页面（可选：与企业/律所选择联动） |
| `frontend/src/components/layout/AppShell.tsx` | 修改 | 读取auth store渲染用户信息 |
| `frontend/src/components/layout/Header.tsx` | 修改 | 显示用户头像/登出 |
| `frontend/src/api/client.ts` | 修改 | 支持 refresh token |

**API对接**：

```typescript
// frontend/src/api/auth.api.ts
export const authApi = {
  login: (data: { username: string; password: string }) =>
    post<{ access_token: string; refresh_token: string; user: UserProfile }>('/api/auth/login', data),

  register: (data: { username: string; email: string; password: string; tenant_name: string; tenant_type: 'law_firm' | 'enterprise' }) =>
    post<{ access_token: string; user: UserProfile }>('/api/auth/register', data),

  refresh: (data: { refresh_token: string }) =>
    post<{ access_token: string }>('/api/auth/refresh', data),

  getMe: () => get<UserProfile>('/api/auth/me'),
}
```

**注册流程**：
1. 用户填写 username/email/password
2. 选择账户类型：**律所** 或 **企业**（切换 tenant_type）
3. 填写组织名称（tenant_name）
4. 调用 `/api/auth/register` → 自动创建 Tenant + User
5. 获得 token → 跳转工作台

### 4.2 本地法律大模型部署（5人日）

**目标**：在 D:\www\法律大模型\models\ 目录下部署本地LLM，通过 Ollama 运行。

#### 4.2.1 模型选型

| 模型 | 用途 | 大小 | 推荐理由 |
|------|------|------|----------|
| **LegalOne-R1 8B** | 法律专业任务（首选） | ~5GB | 针对中国法律场景微调 |
| **DeepSeek-R1 Distill 7B** | 通识推理（备选） | ~4GB | 高性价比通用推理 |
| **Qwen2.5 7B** | 快速响应（轻量） | ~4.5GB | 响应速度优先 |
| **lawyer-llama3 8B** | 法律问答（可选） | ~5GB | 法律对话专用 |

> **注意**：如 LegalOne-R1 不可获取，使用 DeepSeek-R1 7B 蒸馏版 + 法律指令微调替代。

#### 4.2.2 Ollama 服务配置

**部署路径**：`D:\www\法律大模型\models\ollama\`

```bash
# 1. 下载 Ollama（Windows版）
# https://ollama.com/download/windows

# 2. 设置模型存储目录（环境变量）
OLLAMA_MODELS=D:\www\法律大模型\models\ollama\models

# 3. 拉取模型
ollama pull deepseek-r1:7b
ollama pull qwen2.5:7b
ollama pull legalone-r1:8b   # 如可获取

# 4. 验证
ollama list
ollama run deepseek-r1:7b "你好，解释一下合同解除的法定情形"
```

#### 4.2.3 模型服务更新

修改 `app/services/multi_model_ollama.py` 添加新模型配置：

```python
# 新增模型配置
MODELS = {
    "legalone-r1:8b": {
        "purpose": "legal",
        "min_context_tokens": 1024,
        "max_context_tokens": 32768,
        "timeout": 300,
        "temperature": 0.3,
        "num_ctx": 32768,
    },
    "deepseek-r1:7b": {
        "purpose": "general",
        "min_context_tokens": 512,
        "max_context_tokens": 16384,
        "timeout": 180,
        "temperature": 0.5,
        "num_ctx": 16384,
    },
    "qwen2.5:7b": {
        "purpose": "fast",
        "min_context_tokens": 256,
        "max_context_tokens": 8192,
        "timeout": 60,
        "temperature": 0.7,
        "num_ctx": 8192,
    },
}
```

#### 4.2.4 法律专业 Prompt 优化

创建法律专家模型专用的 prompt 模板：

```python
# app/services/legal_prompts_expert.py

EXPERT_LEGAL_SYSTEM_PROMPT = """你是一位专业的中国执业律师，精通民事、刑事、行政、仲裁等各类法律实务。你的回答应当：
1. 严格依据现行法律法规（《民法典》《民事诉讼法》等）
2. 结合司法实践和最高人民法院指导案例
3. 语言严谨专业，引用法条时标注具体条款编号
4. 区分"法律规定"与"司法实践中的通常做法"
5. 明确告知不确定之处

[相关法律规定]
{relevant_laws}

[案件背景]
{case_background}

[证据材料]
{evidence_summary}

请基于以上信息给出专业的法律分析。"""
```

#### 4.2.5 健康检查与自动切换

```python
# app/services/multi_model_ollama.py 修改
class MultiModelOllama:
    def __init__(self):
        self.models = MODELS
        self._health_cache = {}  # {model: {"available": bool, "latency": float}}

    async def check_health(self, model: str) -> bool:
        """检查模型可用性，带缓存"""
        if model in self._health_cache:
            cache = self._health_cache[model]
            if time.time() - cache["check_time"] < 30:
                return cache["available"]
        # ... 实际检查逻辑
```

### 4.3 订阅配额校验（2人日）

**目标**：在现有 Tenant 字段基础上，实现配额的强制校验。

**需要修改的服务**：

| 服务 | 校验点 |
|------|--------|
| `case_service.py`（新建） | 创建案件时校验 `tenant.max_cases` |
| `user_service.py`（新建） | 创建用户时校验 `tenant.max_users` |
| `llm_service.py` | 调用时校验 `tenant.ai_daily_quota` 和 `ai_monthly_usage` |
| 文件存储服务 | 上传时校验 `tenant.max_storage_gb` |

**实现方案**：

```python
# app/services/tenant_quota_service.py
class TenantQuotaService:
    @staticmethod
    def check_case_limit(tenant_id: str) -> tuple[bool, str]:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        current_count = db.query(Case).filter(Case.tenant_id == tenant_id).count()
        if current_count >= tenant.max_cases:
            return False, f"已达案件数量上限({tenant.max_cases})，请升级套餐"
        return True, ""

    @staticmethod
    def check_user_limit(tenant_id: str) -> tuple[bool, str]:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        current_count = db.query(User).filter(User.tenant_id == tenant_id).count()
        if current_count >= tenant.max_users:
            return False, f"已达用户数量上限({tenant.max_users})，请升级套餐"
        return True, ""

    @staticmethod
    def check_ai_quota(tenant_id: str, increment: int = 1) -> tuple[bool, str]:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant.ai_daily_quota and (tenant.ai_daily_usage or 0) + increment > tenant.ai_daily_quota:
            return False, "今日AI调用配额已用尽，请明天重试或升级套餐"
        return True, ""
```

---

## 五、Phase 1：SaaS 核心（第2-3周）

### 5.1 多租户注册与登录流程（5人日）

**API 扩展**：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 注册（自动创建 Tenant） |
| `/api/auth/login` | POST | 登录 |
| `/api/auth/refresh` | POST | 刷新 token |
| `/api/auth/logout` | POST | 登出 |
| `/api/tenants/me` | GET | 获取当前租户信息 |
| `/api/tenants/me` | PUT | 更新租户信息 |
| `/api/tenants/invite` | POST | 邀请团队成员 |

**注册流程设计**：

```
用户注册
    │
    ▼
┌─────────────────┐     ┌──────────────────┐
│ 1. 验证用户名    │────▶│ 2. 验证邮箱唯一性 │
│    唯一性检查    │     │   email 唯一检查  │
└────────┬────────┘     └─────────┬────────┘
         │                       │
         ▼                       ▼
┌────────────────────────────────────────┐
│     3. 创建 Tenant 记录                  │
│     · tenant_type = 用户选择             │
│     · plan = 根据选择（Free/Trial）      │
│     · subscription_expires_at           │
│     · 生成唯一 slug                      │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│     4. 创建 User 记录                   │
│     · role = ADMIN (第一个用户)         │
│     · tenant_id 关联                    │
│     · 发送邮箱验证（可延迟）             │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│     5. 返回 JWT token                   │
│     · access_token (7天)               │
│     · refresh_token (30天)             │
│     · user + tenant 信息                │
└────────────────────────────────────────┘
```

### 5.2 SaaS 后台管理（8人日）

**管理后台页面**（仅 ADMIN 可访问）：

| 页面 | 功能 |
|------|------|
| `/admin/dashboard` | 全局统计（租户数/用户数/案件数/AI调用量） |
| `/admin/tenants` | 租户列表（搜索/筛选/查看/禁用） |
| `/admin/tenant/:id` | 租户详情（用户/案件/配额使用） |
| `/admin/users` | 用户管理 |
| `/admin/ai-usage` | AI 调用统计 |
| `/admin/billing` | 计费管理（可选） |

**关键 API**：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/admin/tenants` | GET | 租户列表（分页） |
| `/api/admin/tenants/:id` | GET/PUT | 租户详情/更新 |
| `/api/admin/tenants/:id/reset-quota` | POST | 重置配额 |
| `/api/admin/tenants/:id/suspend` | POST | 暂停租户 |
| `/api/admin/tenants/:id/users` | GET | 租户下的用户列表 |
| `/api/admin/ai-stats` | GET | AI 使用统计 |

### 5.3 团队成员管理（3人日）

**功能**：
- 租户管理员邀请团队成员（输入邮箱）
- 成员角色分配（ADMIN/LAWYER/ASSISTANT/CLIENT/VIEWER）
- 权限矩阵展示
- 成员列表和活跃状态

### 5.4 邮件服务集成（2人日）

**集成 SendGrid / Resend / 阿里云邮件**：

| 邮件类型 | 触发时机 |
|----------|----------|
| 注册欢迎邮件 | 注册成功后 |
| 邮箱验证 | 注册时 |
| 邀请团队成员 | 管理员邀请时 |
| 密码重置 | 请求重置时 |
| 套餐到期提醒 | 订阅到期前7/3/1天 |
| 配额警告 | 使用量达 80% 时 |
| 暂停通知 | 租户被暂停时 |

---

## 六、Phase 2：用户分群 UI（第4-5周）

### 6.1 设计原则

律所用户和企业用户的核心差异：

| 维度 | 律所用户 | 企业用户 |
|------|---------|---------|
| **主视图** | 案件列表（按状态分组） | 项目/仪表盘（风险概览） |
| **核心实体** | 案件 (Case) | 项目 (Project) |
| **工作流** | 诉讼流程（立案→审理→判决→执行） | 合同流程（起草→签署→履行→归档） |
| **时间管理** | 法定期限（上诉期15日等） | 合同约定期限 |
| **证据管理** | 强调对抗性（己方/对方证据） | 强调完整性（合同履行证据） |
| **分析重点** | 胜诉策略、对方弱点 | 风险防控、合规审查 |
| **导航结构** | 案件驱动（多层级Tab） | 项目驱动（卡片式看板） |

### 6.2 导航结构差异

#### 律所端侧边栏

```
┌─────────────────────┐
│ 🏛 法律大模型        │
│ [律所] 甲鼎律师事务所 │
├─────────────────────┤
│ 📊 工作台            │
├─────────────────────┤
│ 📁 案件管理    ●    │
│  ├─ 全部案件         │
│  ├─ 进行中          │
│  ├─ 已结案          │
│  └─ 归档            │
├─────────────────────┤
│ 📋 项目管理          │
├─────────────────────┤
│ 📑 文书管理          │
├─────────────────────┤
│ ⚖️  出庭抗辩    🆕   │
├─────────────────────┤
│ 📈 对抗性分析        │
├─────────────────────┤
│ ⏱️  时间把控         │
├─────────────────────┤
│ 📮 上诉追踪    🆕   │
├─────────────────────┤
│ 🎯 执行跟踪    🆕   │
├─────────────────────┤
│ 📚 法律知识库        │
├─────────────────────┤
│ ⏰ 提醒中心    ●    │
├─────────────────────┤
│ 👥 团队管理          │
├─────────────────────┤
│ ⚙️  设置              │
└─────────────────────┘
```

#### 企业端侧边栏

```
┌─────────────────────┐
│ 🏛 法律大模型        │
│ [企业] XX科技公司    │
├─────────────────────┤
│ 📊 工作台            │
├─────────────────────┤
│ 📁 项目管理    ●    │
│  ├─ 全部项目         │
│  ├─ 合同项目         │
│  ├─ 合规项目         │
│  └─ 争议项目         │
├─────────────────────┤
│ 📄 合同管理          │
├─────────────────────┤
│ 🛡️  风险监控    🆕  │
├─────────────────────┤
│ 📋 合规咨询    🆕   │
├─────────────────────┤
│ 📊 费用管理          │
├─────────────────────┤
│ 📑 文书管理          │
├─────────────────────┤
│ 🔍 证据管理          │
├─────────────────────┤
│ 📚 法律知识库        │
├─────────────────────┤
│ ⏰ 提醒中心          │
├─────────────────────┤
│ 👥 团队管理          │
├─────────────────────┤
│ ⚙️  设置              │
└─────────────────────┘
```

### 6.3 工作台差异化

#### 律所工作台

```
┌────────────────────────────────────────────────────────┐
│ 工作台                              [甲鼎律师事务所]     │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │  12     │ │   8      │ │   3     │ │   2     │      │
│  │ 进行中  │ │ 待开庭  │ │ 上诉中  │ │ 执行中  │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│                                                        │
│  ⚠️ 紧急事项                          [查看全部]        │
│  ┌──────────────────────────────────────────────┐     │
│  │ 🔴 上诉期限   王五诉李四案   剩余 5 天         │     │
│  │ 🟠 证据补充   合同纠纷案     剩余 10 天        │     │
│  │ 🔴 开庭通知   借款纠纷案     明天 9:00         │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
│  📋 近期案件                                            │
│  ┌──────────┬──────────┬──────────┬──────────┐        │
│  │ 王五诉李四 │ 合同纠纷  │ 劳动争议  │ 房产纠纷  │        │
│  │ 🔴 进行中 │ 🟡 审理中 │ 🟢 立案  │ 🔴 进行中 │        │
│  └──────────┴──────────┴──────────┴──────────┘        │
│                                                        │
│  🤖 AI 助手                                            │
│  ┌──────────────────────────────────────────────┐     │
│  │  建议对"王五诉李四案"进行对抗性分析            │     │
│  │  [立即分析]  [查看详情]                        │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### 企业工作台

```
┌────────────────────────────────────────────────────────┐
│ 工作台                              [XX科技有限公司]     │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │  5      │ │   2      │ │   1     │ │   8     │      │
│  │ 在运行  │ │ 高风险  │ │ 即将到期│ │ 待审合同 │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│                                                        │
│  🛡️ 风险预警                          [查看全部]        │
│  ┌──────────────────────────────────────────────┐     │
│  │ 🔴 合同超期   供应商采购合同   已超 3 天       │     │
│  │ 🟠 合规风险   人事合规审查     待处理          │     │
│  │ 🟡 续约提醒   IT服务合同       剩余 30 天      │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
│  📊 项目总览                                            │
│  ┌─────────────────────────────────────────────┐       │
│  │ ████████████░░░░░░░░░░░░░░░░░░  采购合规   │       │
│  │ ██████████████████░░░░░░░░░░░░░░  人事合规   │       │
│  │ ████████████████████████░░░░░░░░  供应商合同 │       │
│  └─────────────────────────────────────────────┘       │
│                                                        │
│  📄 待审合同 (8)                    [查看全部]          │
│  ┌──────────────────────────────────────────────┐     │
│  │ · XX采购合同_v3.docx   [技术部]  待法务审核  │     │
│  │ · 租赁合同补充协议.docx [财务部]  待法务审核  │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 6.4 案件详情页面差异

#### 律所端案件详情

保留现有 9+ Tab 结构（概述/当事人/证据/文书/分析/画像/报告/时间轴/出庭/上诉/执行/函件）。

#### 企业端案件详情（重命名为"项目详情"）

```
项目详情
├── 📋 概况（基本信息、对手方、风险评级）
├── 📄 合同（合同列表、条款审查、版本对比）
├── 🔍 证据（履行证据、往来函件、凭证）
├── 📊 财务（费用记录、收益预估）
├── 📝 文书（往来文书、往来函件）
├── 💬 咨询（法律咨询记录、AI 问答）
├── ⏰ 时间轴（关键节点、时间线）
├── 📎 附件（所有上传文件）
└── 🤖 AI 助手（风险分析、合规建议）
```

### 6.5 技术实现方案

**方案**：基于 `tenant_type` 动态渲染界面。

```typescript
// frontend/src/stores/tenant.store.ts
interface TenantStore {
  tenant: Tenant | null;
  tenantType: 'law_firm' | 'enterprise' | null;
  isLawFirm: boolean;
  isEnterprise: boolean;
}

// 从 JWT token 或 /api/tenants/me 获取
const useTenantStore = create<TenantStore>((set, get) => ({
  tenant: null,
  tenantType: null,
  get isLawFirm() { return get().tenantType === 'law_firm' },
  get isEnterprise() { return get().tenantType === 'enterprise' },
}));
```

**动态导航**：

```typescript
// frontend/src/components/layout/Sidebar.tsx
const lawFirmNav = [
  { label: '案件管理', icon: CaseIcon, path: '/cases', badge: caseCount },
  { label: '出庭抗辩', icon: GavelIcon, path: '/cases/:id/hearing', new: true },
  { label: '上诉追踪', icon: AppealIcon, path: '/cases/:id/appeal', new: true },
  // ...
];

const enterpriseNav = [
  { label: '项目管理', icon: ProjectIcon, path: '/projects', badge: projectCount },
  { label: '风险监控', icon: ShieldIcon, path: '/risk', badge: riskCount, new: true },
  { label: '合规咨询', icon: CheckIcon, path: '/compliance', new: true },
  // ...
];

// 根据 tenantType 选择导航
const navItems = isLawFirm ? lawFirmNav : enterpriseNav;
```

**Tab 动态渲染**：

```typescript
// frontend/src/pages/cases/[id]/index.tsx
const lawFirmTabs = ['overview', 'parties', 'evidence', 'documents',
  'analysis', 'profile', 'reports', 'timeline', 'hearing', 'appeal',
  'execution', 'letters', 'finance'];

const enterpriseTabs = ['overview', 'contract', 'evidence', 'finance',
  'documents', 'chat', 'timeline', 'attachments', 'ai'];

const tabs = tenantType === 'law_firm' ? lawFirmTabs : enterpriseTabs;
```

**Dashboard 动态组件**：

```typescript
// frontend/src/pages/dashboard/index.tsx
{isLawFirm ? (
  <>
    <LawFirmQuickStats />
    <UrgentDeadlineAlert />
    <ActiveCasesList />
    <CaseAISuggestions />
  </>
) : (
  <>
    <EnterpriseRiskOverview />
    <ProjectProgressCards />
    <PendingContractReviews />
    <ComplianceAlerts />
  </>
)}
```

### 6.6 前端文件新增清单

| 文件路径 | 类型 | 说明 |
|----------|------|------|
| `frontend/src/api/tenant.api.ts` | 新建 | 租户管理 API |
| `frontend/src/api/admin.api.ts` | 新建 | 管理后台 API |
| `frontend/src/api/auth.api.ts` | 新建 | 认证 API |
| `frontend/src/stores/auth.store.ts` | 新建 | 认证状态 |
| `frontend/src/stores/tenant.store.ts` | 新建 | 租户状态 |
| `frontend/src/pages/login.tsx` | 修改 | 对接后端 |
| `frontend/src/pages/register.tsx` | 新建 | 注册页面 |
| `frontend/src/pages/admin/*` | 新建 | 管理后台页面 |
| `frontend/src/pages/landing.tsx` | 新建 | SaaS 落地页 |
| `frontend/src/pages/pricing.tsx` | 新建 | 定价页 |
| `frontend/src/components/layout/Sidebar.tsx` | 修改 | 动态导航 |
| `frontend/src/components/layout/Header.tsx` | 修改 | 显示租户信息 |
| `frontend/src/components/layout/AppShell.tsx` | 修改 | 整合 auth store |
| `frontend/src/components/dashboard/LawFirm/*` | 新建 | 律所仪表盘组件 |
| `frontend/src/components/dashboard/Enterprise/*` | 新建 | 企业仪表盘组件 |
| `frontend/src/components/case/*` | 修改 | 律所案件详情Tab |
| `frontend/src/components/project/*` | 新建 | 企业项目详情Tab |
| `frontend/src/hooks/useAuth.ts` | 新建 | 认证 hook |
| `frontend/src/hooks/useTenant.ts` | 新建 | 租户 hook |
| `frontend/src/types/auth.ts` | 新建 | 认证类型定义 |
| `frontend/src/types/tenant.ts` | 新建 | 租户类型定义 |

---

## 七、Phase 3：计费生态（第6-7周）

### 7.1 订阅套餐设计

| 套餐 | 价格 | 用户数 | 案件/项目 | 存储 | AI 每日配额 | 法律LLM |
|------|------|--------|-----------|------|-------------|---------|
| **Free** | ¥0 | 3人 | 10个 | 5GB | 50次 | ❌ |
| **Pro** | ¥299/月 | 10人 | 100个 | 50GB | 500次 | ✅ 本地 |
| **Enterprise** | ¥999/月 | 不限 | 不限 | 500GB | 2000次 | ✅ 本地+云端 |
| **Custom** | 定制 | 不限 | 不限 | 不限 | 不限 | ✅ 全功能 |

### 7.2 Stripe 订阅集成

**需要的 Stripe 资源**：

| 资源 | 说明 |
|------|------|
| Stripe Customer | 每个 Tenant 对应一个 Customer |
| Stripe Subscription | 每个活跃订阅对应一个 Subscription |
| Stripe Product/Price | 4 个订阅产品（Free/Pro/Enterprise/Custom） |
| Stripe Webhook | 订阅状态变更同步 |

**API 扩展**：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/billing/plans` | GET | 获取订阅套餐列表 |
| `/api/billing/checkout` | POST | 创建 Stripe Checkout Session |
| `/api/billing/portal` | POST | 创建 Stripe Customer Portal |
| `/api/billing/webhook` | POST | Stripe Webhook 回调 |
| `/api/billing/status` | GET | 当前订阅状态 |

**核心服务**：

```python
# app/services/stripe_service.py
class StripeService:
    def create_customer(self, tenant: Tenant, user: User) -> str:
        """创建 Stripe Customer"""

    def create_subscription(self, customer_id: str, price_id: str) -> str:
        """创建订阅"""

    def create_checkout_session(self, tenant_id: str, price_id: str) -> str:
        """创建结账会话 URL"""

    def create_portal_session(self, customer_id: str) -> str:
        """创建客户门户 URL"""

    def handle_webhook(self, payload: bytes, sig: str) -> None:
        """处理 Stripe Webhook"""
        # customer.subscription.created  -> 更新 subscription_status = ACTIVE
        # customer.subscription.updated   -> 套餐升级/降级
        # customer.subscription.deleted  -> subscription_status = CANCELLED
        # invoice.payment_failed         -> subscription_status = PAST_DUE
```

### 7.3 定价页面设计

**定价页关键要素**：
- 套餐对比表格（功能矩阵）
- "当前套餐" vs "推荐套餐"高亮
- 年付折扣（8折）
- 免费试用（14天 Trial）
- FAQ / 咨询联系

---

## 八、Phase 4：优化上线（第8周）

### 8.1 性能优化

| 优化项 | 目标 | 方案 |
|--------|------|------|
| 首屏加载 | < 2s | Code Splitting、骨架屏、预加载 |
| API 响应 | < 500ms | Redis 缓存热点数据 |
| LLM 冷启动 | < 5s | Ollama 模型常驻内存 (OLLAMA_KEEP_ALIVE=5m) |
| 数据库查询 | < 100ms | 索引优化、查询缓存 |
| 向量检索 | < 200ms | ChromaDB 批量预热 |

### 8.2 监控体系

```
┌─────────────────────────────────────────────────────┐
│                   监控指标看板                        │
├──────────────┬──────────────┬───────────────────────┤
│   业务指标    │   系统指标    │    AI 指标             │
├──────────────┼──────────────┼───────────────────────┤
│ 活跃租户数    │ CPU/内存     │ 模型命中率            │
│ 新增注册数    │ API QPS      │ 平均响应时间          │
│ 案件创建数    │ DB 连接池    │ Token 消耗量          │
│ AI 调用量    │ 错误率       │ 本地 vs 云端比例      │
│ 订阅转化率    │ P99 延迟     │ 模型健康状态          │
└──────────────┴──────────────┴───────────────────────┘
```

### 8.3 Docker 部署更新

更新 `docker-compose.prod.yml` 增加：
- Ollama 服务（GPU 支持）
- Redis 持久化
- Nginx SSL 配置
- 定时任务（Celery Beat）
- 备份策略

---

## 九、部署计划

### 9.1 本地开发环境

```bash
# D:\www\法律大模型\models\ollama\
# 1. 安装 Ollama (Windows)
# 2. 设置环境变量
set OLLAMA_MODELS=D:\www\法律大模型\models\ollama\models
set OLLAMA_HOST=0.0.0.0:11434

# 3. 拉取模型
ollama pull deepseek-r1:7b
ollama pull qwen2.5:7b
ollama pull nomic-embed-text  # 嵌入模型

# 4. 启动后端
python run.py

# 5. 启动前端
cd frontend && npm run dev
```

### 9.2 生产环境（单服务器）

```yaml
# docker-compose.prod.yml 新增服务
services:
  ollama:
    image: ollama/ollama:latest
    container_name: legal-ollama
    ports:
      - "11434:11434"
    volumes:
      - ./models/ollama:/root/.ollama
    environment:
      OLLAMA_MODELS: /root/.ollama/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 5
```

### 9.3 生产环境（多服务器/K8s）

| 组件 | 推荐配置 |
|------|----------|
| API 服务器 | 2核4G × 2副本 |
| PostgreSQL | 4核8G + 100GB SSD |
| Redis | 2核4G |
| Ollama (GPU) | 8核16G + RTX 4090 / A100 |
| Nginx | 2核2G |
| 前端 CDN | 静态资源分离 |

---

## 十、人力估算

| 任务 | 估算 | 说明 |
|------|------|------|
| 前端登录对接 | 5人日 | API + Store + 页面 |
| 本地LLM部署 | 5人日 | Ollama + 模型 + 路由 |
| 配额校验 | 2人日 | 服务层校验 |
| 多租户注册登录 | 5人日 | API + 流程 |
| SaaS后台管理 | 8人日 | 页面 + API |
| 团队成员管理 | 3人日 | 邀请 + 角色 |
| 邮件服务集成 | 2人日 | SendGrid/Resend |
| 律所端UI | 8人日 | 导航 + 仪表盘 |
| 企业端UI | 8人日 | 导航 + 仪表盘 |
| 案件详情分群 | 5人日 | Tab动态渲染 |
| Stripe订阅集成 | 5人日 | 后端 + 前端 |
| 定价页/落地页 | 3人日 | 页面设计 |
| Docker/部署 | 3人日 | 容器化 |
| 测试与修Bug | 5人日 | 全流程测试 |
| **合计** | **67人日** | 约 3.5 人周 |

---

## 十一、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| LegalOne-R1 模型不可获取 | 高 | 改用 DeepSeek-R1 7B + 法律SFT数据自行微调 |
| 前端登录 Mock 代码广泛 | 高 | 一次性重构 auth 流程，后续改动可控 |
| 多租户数据隔离不完整 | 高 | Phase 0 必须完成配额校验测试 |
| Stripe 在中国支付受限 | 中 | 支持支付宝/微信支付（推荐Ping++） |
| 本地LLM显存不足 | 中 | 使用 4B 轻量模型，限制并发 |
| 向量检索质量不足 | 中 | 结合关键词检索，混合搜索 |
| 法律数据准确性 | 高 | 严格遵守 DEVELOPMENT_CONSTITUTION 的证据完整性原则 |

---

## 十二、参考文档

- `DEVELOPMENT_CONSTITUTION.md` - 证据完整性最高原则
- `plans/SaaS升级改造实施计划.md` - 已有计划参考
- `docs/design/llm-routing.md` - LLM 路由详细设计
- `docs/deployment-strategy.md` - 部署策略
- `docs/design/architecture.md` - 系统架构设计
- `app/models/tenant.py` - 租户模型定义
- `app/models/user.py` - 用户模型定义
- `app/services/jwt_auth_service.py` - JWT 认证服务
- `app/services/multi_model_ollama.py` - Ollama 多模型管理
- `app/services/legal_llm_router.py` - 法律 LLM 路由

