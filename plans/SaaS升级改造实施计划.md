# 法律大模型 SaaS 升级改造计划

> 文档版本：v1.0
> 创建日期：2026-05-07
> 状态：规划中

---

## 一、背景与目标

### 1.1 项目背景

本系统（法律案件追踪系统）在设计之初即规划了三项核心能力：

1. **本地法律大模型融合** — 全部下载开源法律大模型，完善改造，融入系统
2. **SaaS 多租户部署** — 支持多律所/多企业同时使用的 SaaS 模式
3. **用户分群差异化** — 按"律所"和"企业"两种用户类型提供差异化前端展示

当前系统已具备完整的业务功能（案件管理、证据管理、AI分析、文书生成等），但尚未实现上述三项设计目标。

### 1.2 现状分析

#### 1.2.1 系统现状

| 维度 | 当前状态 | 问题 |
|------|---------|------|
| **多租户** | 无 — 所有用户共用同一数据库和代码实例 | 无法支持多律所/企业隔离，数据无隔离 |
| **用户认证** | `auth_service.py` 已设计但**未激活** — 内存存储，未接入任何路由 | 任何API无权限验证 |
| **用户体系** | 无用户/租户概念，`Case` 模型无 `tenant_id`/`user_id` | 无法区分不同机构的案件 |
| **LLM 架构** | 仅 Ollama（本地 Gemma）+ DashScope（通义千问云端） | 无法律领域专项模型，无模型融合 |
| **前端** | 单一界面，无用户类型区分 | 律所用户和企业用户看到相同内容 |
| **数据库** | SQLite 开发 / PostgreSQL 生产（均单库） | 无租户隔离机制 |
| **部署** | Docker 单实例部署 | 无 SaaS 伸缩能力 |

#### 1.2.2 已有资产（可复用）

- `app/services/auth_service.py` — JWT 鉴权框架完整（需改造为数据库持久化）
- `app/models/` — 所有业务模型完整，扩展成本低
- `app/` 已有 40+ API 路由，业务逻辑完善
- `frontend/` React + TypeScript + Tailwind + shadcn/ui 基础设施完备
- `docker-compose.prod.yml` — 已有 PostgreSQL + Redis + Nginx 生产架构
- `DEVELOPMENT_CONSTITUTION.md` — 证据完整性原则必须继承
- `plans/` 中已有的前端重设计 v3.0、法律数据 API 集成等计划可复用

---

## 二、法律大模型选型与融合方案

### 2.1 当前 LLM 架构

```
用户请求 → LLM Router → [Ollama(Gemma)] + [DashScope(Qwen)]
```

- **本地 Ollama**：Gemma 系列（通用模型）
- **云端 DashScope**：Qwen 通义千问（通用模型）
- **问题**：无法律专项能力，法律推理、条文记忆、案例分析依赖通用模型，效果有限

### 2.2 法律大模型选型

#### 2.2.1 候选模型对比

| 模型 | 机构 | 基座 | 参数量 | 法律能力 | 适用场景 | 部署难度 | 推荐 |
|------|------|------|--------|---------|---------|---------|------|
| **LegalOne-R1** | 清华大学 | Qwen3 | 1.7B/4B/8B | 极强（2026最新） | 法律推理/文书/咨询 | 中（已开源） | **首选** |
| **DISC-LawLLM** | 复旦大学 | Qwen2.5 | 7B | 极强（LawBench第二） | 通用法律任务 | 低（已开源） | **备选** |
| **InternLM-Law** | 上海AI Lab | InternLM2 | 7B | 强（67% on LawBench） | 法律咨询/问答 | 低 | 备选 |
| **LexiLaw** | 个人开源 | ChatGLM | 6B | 中等 | 法律咨询 | 低 | 参考 |
| DeepSeek-R1 | DeepSeek | DeepSeek | 671B MoE | 通用强，法律中等 | 复杂推理（云端） | 高（资源需求大） | 云端补充 |
| Qwen3-235B | 阿里 | Qwen | 235B | 通用强 | 通用场景（云端） | — | 云端主力 |

#### 2.2.2 推荐方案：三层模型融合

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Router（智能路由）                 │
├─────────────┬──────────────────┬─────────────────────┤
│   Layer 1   │     Layer 2       │      Layer 3        │
│  法律专项模型  │   本地通用大模型    │     云端通用模型      │
│  (Ollama)   │   (Ollama)       │   (DashScope)       │
├─────────────┼──────────────────┼─────────────────────┤
│ LegalOne-R1 │  DeepSeek-R1     │   Qwen3-235B        │
│ 8B 或 4B    │  (或 Qwen2.5-72B) │   (DashScope)       │
│             │                  │                     │
│ 场景:       │  场景:            │  场景:               │
│ · 法律推理   │  · 长文本分析      │  · 复杂推理           │
│ · 条文引用   │  · 证据分析        │  · 超长上下文          │
│ · 判决预测   │  · 文书生成        │  · 多语言             │
│ · 咨询问答   │  · RAG 检索       │  · 高精度要求          │
└─────────────┴──────────────────┴─────────────────────┘
```

#### 2.2.3 模型部署规格

| 模型 | 参数量 | GPU 需求 | 内存需求 | 用途 |
|------|--------|---------|---------|------|
| LegalOne-R1 | 8B | 1× RTX 3090/4090 或 A10G | ~20GB VRAM | 法律推理主力 |
| LegalOne-R1 | 4B | 1× RTX 3060 及以上 | ~10GB VRAM | 轻量备选 |
| DeepSeek-R1-distill | 7B | 1× RTX 3080 及以上 | ~18GB VRAM | 通用推理（可选） |

**说明**：
- LegalOne-R1 4B 版本可在消费级 GPU 上运行（RTX 3060 12GB 即可）
- 推荐先部署 4B 版本验证，条件允许后升级到 8B
- 云端 DashScope Qwen 作为降级和复杂场景补充

### 2.3 Ollama 服务扩展

当前 `ollama_service.py` 需扩展以支持多模型：

```python
# 扩展后的模型配置
MODELS = {
    "legal": {
        "model": "legalone-r1:8b",      # 或 4b
        "ollama_url": "http://localhost:11434",
        "temperature": 0.3,
        "max_tokens": 8192,
    },
    "general": {
        "model": "deepseek-r1:7b",
        "ollama_url": "http://localhost:11436",  # 多实例或单实例多模型
        "temperature": 0.7,
        "max_tokens": 16384,
    },
    "fast": {
        "model": "qwen2.5:7b",           # 快速响应场景
        "ollama_url": "http://localhost:11434",
        "temperature": 0.5,
        "max_tokens": 4096,
    }
}
```

### 2.4 法律模型 Prompt 工程

针对 LegalOne-R1 优化提示词模板：

- **法律推理提示**：融合 IRAC 框架（Issue/Rule/Application/Conclusion）
- **文书生成提示**：引入法律文书格式约束
- **证据分析提示**：继承"证据完整性最高原则"（`DEVELOPMENT_CONSTITUTION.md` 第1-8章）
- **条文引用提示**：强制要求提供法条依据和来源

---

## 三、SaaS 多租户架构方案

### 3.1 架构设计原则

1. **渐进式演进** — 从当前单租户平滑升级，不破坏现有业务
2. **行级隔离优先** — `tenant_id` 字段隔离，运营成本最低
3. **数据可迁移** — 现有数据可导入到多租户框架
4. **模型共享** — AI 模型服务所有租户共享（成本最优）

### 3.2 租户隔离策略选择

| 策略 | 隔离级别 | 运维成本 | 适用规模 | 推荐 |
|------|---------|---------|---------|------|
| 行级隔离（`tenant_id`） | 中 | 低 | <1000 租户 | **推荐** |
| Schema 级隔离 | 高 | 中 | 100-10000 租户 | 后期可选 |
| 数据库级隔离 | 最高 | 高 | >10000 或高价值客户 | 后期可选 |

**本计划选择：行级隔离（`tenant_id`）作为一期方案**

### 3.3 数据模型改造

#### 3.3.1 核心改造：添加 `tenant_id`

```python
# app/models/tenant.py（新增）

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from app.db.database import Base
from datetime import datetime


class Tenant(Base):
    """租户（律所/企业）"""
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(200), nullable=False)  # 租户名称
    tenant_type = Column(String(20), nullable=False)  # "law_firm" | "enterprise"
    slug = Column(String(100), unique=True, nullable=False)  # URL友好标识
    logo_url = Column(String(500), nullable=True)

    # 订阅信息
    plan = Column(String(50), default="free")  # free/trial/pro/enterprise
    subscription_status = Column(String(20), default="active")
    subscription_expires_at = Column(DateTime, nullable=True)
    max_users = Column(Integer, default=3)
    max_cases = Column(Integer, default=10)
    max_storage_gb = Column(Integer, default=5)

    # 域配置
    custom_domain = Column(String(255), nullable=True)
    allowed_email_domains = Column(Text, nullable=True)  # JSON: ["lawfirm.com", "*.inc.com"]

    # 状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # 计费
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)

    # AI 配置
    ai_model_preference = Column(String(50), default="legalone-r1:4b")
    ai_daily_quota = Column(Integer, default=100)  # 每日AI调用限制
    ai_monthly_usage = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class User(Base):
    """用户（继承并扩展现有 auth_service 的 User 模型）"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)

    role = Column(String(20), default="assistant")  # admin/lawyer/assistant/client/viewer
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)

    last_login_at = Column(DateTime, nullable=True)
    last_active_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

#### 3.3.2 现有模型扩展 `tenant_id`

```python
# app/models/case.py（扩展）
class Case(Base):
    # ... 现有字段 ...
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    # 原有索引保留，新增 tenant_id 索引

# 其他需要隔离的模型（统一加 tenant_id）：
# - Party, Document, EvidenceItem, Letter, LegalDeadline
# - HearingRecord, AppealRecord, ExecutionTracking, Reminder
# - ChatMessage, ConversationSession, Project
# - GeneratedDocument, DocumentTemplate
```

#### 3.3.3 无需 `tenant_id` 的模型（全局共享资源）

- `LegalKnowledge`（法律知识库 — 公共数据）
- `DocumentTemplate`（公共模板库）
- `SystemConfig`（系统配置）
- `MilestoneTemplate`（流程节点模板）

### 3.4 多租户中间件设计

```python
# app/core/tenant.py

from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import uuid

# Request 级别的租户上下文（线程/协程安全）
class TenantContext:
    _tenant_id: Optional[str] = None
    _user_id: Optional[str] = None

    @classmethod
    def set_tenant(cls, tenant_id: str, user_id: str):
        cls._tenant_id = tenant_id
        cls._user_id = user_id

    @classmethod
    def get_tenant_id(cls) -> Optional[str]:
        return cls._tenant_id

    @classmethod
    def get_user_id(cls) -> Optional[str]:
        return cls._user_id

    @classmethod
    def clear(cls):
        cls._tenant_id = None
        cls._user_id = None


# 依赖注入：解析租户上下文
async def get_current_tenant(request: Request) -> str:
    """从 JWT Token 或 Subdomain 解析当前租户"""
    # 方案1: JWT Token 中包含 tenant_id
    # 方案2: 子域名解析 (lawfirm.legalsystem.com)
    # 方案3: Header 传递 (X-Tenant-ID)

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        tenant_id = payload.get("tenant_id")
        if tenant_id:
            TenantContext.set_tenant(tenant_id, payload.get("user_id"))
            return tenant_id

    # 子域名解析（备选）
    host = request.headers.get("host", "")
    if "." in host and not host.startswith("www."):
        slug = host.split(".")[0]
        # 查询 tenant by slug
        ...

    raise HTTPException(401, "无法确定租户")


# 全局过滤器：在每个请求中自动注入 tenant_id 过滤条件
class TenantFilter:
    @staticmethod
    def apply(query, model_class):
        """自动为所有查询添加 tenant_id 过滤"""
        if hasattr(model_class, 'tenant_id'):
            tenant_id = TenantContext.get_tenant_id()
            if tenant_id:
                return query.filter(model_class.tenant_id == tenant_id)
        return query
```

### 3.5 订阅计费方案

#### 3.5.1 订阅套餐设计

| 套餐 | 价格 | 用户数 | 案件数 | 存储 | AI 额度 | 适用对象 |
|------|------|--------|--------|------|---------|---------|
| **Free** | ¥0/月 | 3人 | 10个 | 5GB | 50次/天 | 个人/试用 |
| **Pro** | ¥299/月 | 10人 | 无限 | 50GB | 200次/天 | 小型律所 |
| **Enterprise** | ¥999/月 | 无限 | 无限 | 200GB | 1000次/天 | 中型律所/企业法务 |
| **定制** | 议价 | 定制 | 定制 | 定制 | 无限 | 大型律所/集团 |

#### 3.5.2 计费维度

- **按席位数**（用户数上限）
- **按案件数**（Pro 及以上不限）
- **按 AI 调用量**（Enterprise 可选按量计费）
- **按存储量**（超出配额按 GB 计费）

#### 3.5.3 Stripe 集成要点

```python
# app/services/billing_service.py

class BillingService:
    # 1. 创建 Stripe Customer（注册时）
    # 2. 创建 Subscription（选择套餐时）
    # 3. 处理 Webhook：customer.subscription.created/updated/deleted
    # 4. 用量追踪：每日 AI 调用次数写入 tenant.ai_monthly_usage
    # 5. 配额检查：API 请求时检查 tenant.max_cases / max_users / ai_daily_quota
```

### 3.6 初始化数据迁移

现有数据全部迁移到"默认租户"（tenant_id = "default"）：

```python
# migrations/add_tenant_support.py

# 1. 创建 default tenant
# 2. 为所有现有数据添加 tenant_id = "default"
# 3. 创建 admin 用户（迁移现有"管理"账号）
# 4. 验证数据完整性
```

---

## 四、用户分群（律所/企业）前端差异化方案

### 4.1 用户类型定义

| 类型 | 标识 | 核心用户 | 核心需求 |
|------|------|---------|---------|
| **律所** (`law_firm`) | `tenant.tenant_type = "law_firm"` | 执业律师、律所助理 | 案件管理、证据分析、文书生成、团队协作、庭审辅助 |
| **企业** (`enterprise`) | `tenant.tenant_type = "enterprise"` | 企业法务、合规人员 | 合同审查、风险预警、合规管理、简易咨询、知识库 |

### 4.2 差异化设计方案

#### 4.2.1 导航与首页差异

```
律所用户首页
┌──────────────────────────────────────────────┐
│  案件追踪  │  证据管理  │  文书生成  │  庭审辅助  │  团队  │  报表  │
├──────────────────────────────────────────────┤
│  我的案件 (按状态分组: 进行中/待归档/已归档)       │
│  今日待办 (期限提醒)                            │
│  AI 分析概览                                   │
│  团队成员动态                                   │
└──────────────────────────────────────────────┘

企业用户首页
┌──────────────────────────────────────────────┐
│  合同管理  │  风险预警  │  合规检查  │  法律咨询  │  知识库  │
├──────────────────────────────────────────────┤
│  我的合同 (按状态: 起草中/审核中/履行中/到期)     │
│  合规待办                                        │
│  风险预警看板                                    │
│  法规更新推送                                    │
└──────────────────────────────────────────────┘
```

#### 4.2.2 功能模块差异

| 功能模块 | 律所视角 | 企业视角 |
|---------|---------|---------|
| **案件管理** | 完整案件管理（原告/被告/第三人）、诉讼策略 | 简化版：法务案件、内部纠纷 |
| **证据管理** | 完整证据系统 V2（含证据册生成） | 简化版：合同附件管理 |
| **文书生成** | 全套文书模板（起诉状/答辩状/上诉状等） | 侧重：合同审查意见、律师函 |
| **庭审辅助** | 完整：庭审记录、对抗分析、质证意见 | 无（企业不参与庭审）|
| **合同管理** | 可选：律所代管客户合同 | **核心**：合同起草/审查/履行跟踪 |
| **风险管理** | 可选：案件风险评估 | **核心**：合同风险、供应商风险 |
| **知识库** | 判例库、法规库 | 内部合规知识库 + 外部法规 |
| **AI 分析** | 对抗分析、策略生成、文书生成 | 合同风险分析、合规检查 |
| **团队协作** | 多律师 + 助理 + 客户共享 | 多法务 + 部门协同 |
| **报表** | 案件统计、胜率分析、工作量统计 | 合规统计、风险趋势、合同履行 |

#### 4.2.3 案件类型差异

```
律所案件类型：
- 民事诉讼（合同纠纷/侵权/婚姻家庭/劳动争议...）
- 刑事辩护
- 行政诉讼
- 仲裁案件
- 执行案件
- 非诉业务

企业案件类型：
- 合同纠纷（采购/销售/租赁/服务/劳动）
- 知识产权维权
- 合规调查
- 行政处罚应对
- 内部纪律处分
- 合规审查
```

### 4.3 前端实现方案

#### 4.3.1 主题/皮肤系统

```typescript
// src/types/user.types.ts
interface Tenant {
  id: string;
  name: string;
  tenant_type: "law_firm" | "enterprise";
  plan: "free" | "pro" | "enterprise" | "custom";
  features: string[];  // 启用的功能模块
  logo_url?: string;
}

// src/stores/tenant.store.ts
interface TenantStore {
  tenant: Tenant | null;
  setTenant(tenant: Tenant): void;
  isLawFirm: () => boolean;
  isEnterprise: () => boolean;
  hasFeature: (feature: string) => boolean;
}

// src/hooks/useTenant.ts
function useTenant() {
  const { tenant } = useTenantStore();
  return {
    isLawFirm: tenant?.tenant_type === "law_firm",
    isEnterprise: tenant?.tenant_type === "enterprise",
    features: tenant?.features || [],
    branding: {
      name: tenant?.name,
      logo: tenant?.logo_url,
      primaryColor: tenant?.tenant_type === "law_firm" ? "blue" : "green",
    }
  };
}
```

#### 4.3.2 路由与导航差异

```typescript
// 根据 tenant_type 返回不同导航配置
const getNavigation = (tenantType: string) => {
  if (tenantType === "law_firm") {
    return lawFirmNavigation;  // 案件/证据/文书/庭审/团队/报表
  } else {
    return enterpriseNavigation; // 合同/风险/合规/咨询/知识库
  }
};

// 动态路由前缀
const getRoutePrefix = (tenantType: string) => {
  return tenantType === "law_firm" ? "/lawyer" : "/enterprise";
};
```

#### 4.3.3 组件差异化

```typescript
// 通用组件按用户类型渲染不同内容
<FeatureGate feature="court_defense">
  {/* 仅律所可见 */}
  <CourtDefensePanel />
</FeatureGate>

<FeatureGate feature="contract_review">
  {/* 仅企业可见 */}
  <ContractReviewPanel />
</FeatureGate>

// Dashboard 动态渲染
<Dashboard widgets={getDashboardWidgets(tenantType)} />
```

### 4.4 公共模块（两类型均可用）

以下模块对律所和企业均开放，只是展示深度不同：

- **首页 Dashboard** — 组件相同，数据不同（案件看板 vs 合同看板）
- **聊天/AI 助手** — 基础功能相同，法律专项提示词不同
- **日程/期限提醒** — UI相同，事件类型不同
- **搜索** — 底层相同，搜索范围和结果排序不同
- **个人设置** — 相同
- **用户管理** — 相同（租户内用户管理）

---

## 五、实施计划

### 5.1 整体路线图

```
第1阶段（周1-2）：基础层改造        ██░░░░░░░░░░░░░░░░░░ 14天
第2阶段（周3-5）：多租户核心        ░░░░░░░░░░░░░░░░░░░░  21天
第3阶段（周6-8）：前端差异化         ░░░░░░░░░░░░░░░░░░░░  21天
第4阶段（周9-11）：法律模型融合      ░░░░░░░░░░░░░░░░░░░░  21天
第5阶段（周12-14）：SaaS 上线       ░░░░░░░░░░░░░░░░░░░░  21天
────────────────────────────────────────────────
累计                                      14周 / 98天
```

### 5.2 第一阶段：基础层改造（14天）

| 任务 | 工期 | 负责 | 详情 |
|------|------|------|------|
| 1.1 数据库迁移框架搭建 | 3天 | 后端 | 引入 Alembic，编写初始迁移脚本 |
| 1.2 创建 Tenant/User 模型 | 2天 | 后端 | 新增 `tenant.py` 和 `user.py` 模型 |
| 1.3 JWT 认证服务数据库化 | 3天 | 后端 | 将 `auth_service` 改造为数据库持久化，重构密码存储 |
| 1.4 认证 API 路由开发 | 2天 | 后端 | `/api/auth/register`, `/login`, `/logout`, `/refresh`, `/me` |
| 1.5 前端认证层开发 | 2天 | 前端 | `useAuth` hook, 登录/注册页面, token 管理, ProtectedRoute 升级 |
| 1.6 租户中间件开发 | 2天 | 后端 | `TenantContext`, `get_current_tenant` 依赖, 全局过滤器 |

**交付物**：
- Alembic 迁移脚本：`add_tenant_support`
- Tenant/User 模型
- 完整的用户注册/登录/登出 API
- 前端登录页面（可注册新租户）

### 5.3 第二阶段：多租户核心（21天）

| 任务 | 工期 | 负责 | 详情 |
|------|------|------|------|
| 2.1 为 Case 模型添加 tenant_id | 1天 | 后端 | 迁移脚本 + 模型扩展 |
| 2.2 为所有业务模型添加 tenant_id | 3天 | 后端 | Party, Document, Evidence, Letter, Reminder 等 20+ 模型 |
| 2.3 全局 TenantFilter 改造 | 3天 | 后端 | 为所有 SQLAlchemy 查询自动注入 tenant_id |
| 2.4 租户注册流程 | 2天 | 全栈 | 注册页面 → 创建 Tenant → 创建 Admin User → JWT 登录 |
| 2.5 邀请团队成员 | 2天 | 全栈 | 邀请链接 → 注册/加入 → 角色分配 |
| 2.6 角色权限系统激活 | 3天 | 后端 | 激活 `auth_service` 的权限检查，为所有 API 添加权限验证 |
| 2.7 订阅计费基础 | 3天 | 后端 | Tenant.plan 字段，套餐检查逻辑，Stripe Customer 创建 |
| 2.8 现有数据迁移 | 2天 | 后端 | 创建 default tenant，所有现有数据迁移 |
| 2.9 API 权限测试 | 2天 | 后端 | 全 API 权限回归测试 |

**交付物**：
- 所有业务模型支持 `tenant_id` 隔离
- 完整的租户注册/邀请/角色管理流程
- Stripe 订阅集成（基础）
- 现有数据完整迁移

### 5.4 第三阶段：前端差异化（21天）

| 任务 | 工期 | 负责 | 详情 |
|------|------|------|------|
| 3.1 TenantStore 和 useTenant | 2天 | 前端 | 全局租户状态管理 |
| 3.2 动态导航系统 | 3天 | 前端 | 根据 tenant_type 动态渲染侧边栏/顶部导航 |
| 3.3 动态首页 Dashboard | 3天 | 前端 | 律所版（案件看板）vs 企业版（合同看板）|
| 3.4 律所专属页面 | 4天 | 前端 | 庭审辅助、对抗分析、证据册生成（FeatureGate 保护）|
| 3.5 企业专属页面 | 4天 | 前端 | 合同管理（起草/审查/履行跟踪）、合规检查 |
| 3.6 品牌定制 | 2天 | 前端 | Logo、主题色（tenant.logo_url, tenant.primary_color）|
| 3.7 用户管理页面 | 2天 | 前端 | 团队成员管理、角色分配、邀请管理 |
| 3.8 订阅管理页面 | 1天 | 前端 | 当前套餐查看、升级/降级入口 |

**交付物**：
- 完整的律所版前端界面
- 完整的企业版前端界面
- 动态导航和首页
- 品牌定制能力

### 5.5 第四阶段：法律模型融合（21天）

| 任务 | 工期 | 负责 | 详情 |
|------|------|------|------|
| 4.1 Ollama 多模型支持 | 3天 | 后端 | 扩展 `ollama_service.py` 支持多个模型并行 |
| 4.2 LegalOne-R1 部署 | 2天 | 运维 | Ollama 拉取 LegalOne-R1 4B/8B 模型 |
| 4.3 LLM Router 升级 | 4天 | 后端 | 智能路由：法律任务 → LegalOne，法律推理 → DeepSeek，通用 → Qwen |
| 4.4 法律专项 Prompt 优化 | 3天 | 后端 | IRAC 框架提示词、法律文书格式提示词、条文引用提示词 |
| 4.5 证据完整性原则继承 | 2天 | 后端 | 确认所有法律模型调用路径遵循 `DEVELOPMENT_CONSTITUTION.md` |
| 4.6 模型降级策略 | 2天 | 后端 | 本地模型不可用时自动降级到 DashScope |
| 4.7 融合效果测试 | 3天 | 测试 | 对比通用模型 vs 法律模型在法律任务上的效果差异 |
| 4.8 模型用量统计 | 2天 | 后端 | 记录每个租户对各模型的调用量，支持计费 |

**交付物**：
- LegalOne-R1 模型生产可用
- 智能 LLM Router 上线
- 法律任务路由到专项模型
- 模型用量追踪

### 5.6 第五阶段：SaaS 上线准备（21天）

| 任务 | 工期 | 负责 | 详情 |
|------|------|------|------|
| 5.1 Docker SaaS 架构 | 3天 | 运维 | 多容器编排，健康检查，SaaS 特定配置 |
| 5.2 Stripe 订阅完整集成 | 4天 | 全栈 | Webhook 处理（创建/更新/取消/续费），配额强制执行 |
| 5.3 SaaS Landing Page | 3天 | 前端 | 产品官网 + 定价页 + 试用注册入口 |
| 5.4 邮件服务集成 | 2天 | 后端 | 邀请邮件、密码重置、订阅到期提醒（SendGrid/SMTP）|
| 5.5 监控和告警 | 2天 | 运维 | 日志聚合、API 错误率、模型响应时间、配额告警 |
| 5.6 安全加固 | 2天 | 后端 | HTTPS、TLS、Rate Limit 租户级隔离、SQL 注入防护 |
| 5.7 性能测试 | 2天 | 测试 | 多租户并发压测，模型响应时间 benchmark |
| 5.8 上线检查清单 | 1天 | 全栈 | 功能回归、权限测试、数据隔离验证、备份恢复演练 |
| 5.9 灰度发布 | 2天 | 运维 | 新功能开关、租户分组灰度、回滚机制 |

**交付物**：
- 生产级 SaaS 部署架构
- 完整 Stripe 计费系统
- 产品官网
- 监控告警体系

---

## 六、工作量估算

### 6.1 人力估算（按任务类型）

| 角色 | 任务 | 估算工时 |
|------|------|---------|
| 后端 | 数据库迁移、租户模型、认证 API | 80小时 |
| 后端 | 多租户隔离、全局过滤器、权限系统 | 100小时 |
| 后端 | Stripe 计费、Webhook、用量统计 | 60小时 |
| 后端 | LLM Router、法律模型融合、Prompt 工程 | 80小时 |
| 前端 | 认证层、租户状态、登录注册 | 40小时 |
| 前端 | 动态导航、Dashboard 差异化 | 60小时 |
| 前端 | 律所/企业专属页面开发 | 120小时 |
| 前端 | SaaS Landing Page、订阅管理 | 40小时 |
| 运维 | Docker SaaS 架构、监控、安全 | 60小时 |
| 测试 | 权限测试、租户隔离测试、回归测试 | 60小时 |
| **合计** | | **700小时** |

### 6.2 基础设施成本估算（月度）

| 资源 | 配置 | 月费用估算 |
|------|------|---------|
| 云服务器（主） | 4核8G / 50GB SSD | ¥200-400 |
| GPU 服务器（模型） | RTX 4090 24G / 64G RAM | ¥1500-3000 |
| PostgreSQL（RDS） | 2核4G / 100GB | ¥300-500 |
| Redis | 1G | ¥50-100 |
| 对象存储（文件） | 100GB | ¥30 |
| Stripe 交易费 | 2.9% + ¥0.3/笔 | 按收入 |
| 域名 + SSL | | ¥50-100 |
| 邮件服务 | SendGrid | ¥100-300 |
| **合计（不含 GPU）** | | ¥730-1430/月 |
| **合计（含 GPU）** | | ¥2230-4430/月 |

---

## 七、技术风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| LegalOne-R1 部署不稳定 | 中 | 高 | 准备 DeepSeek-R1 7B 作为降级，保持 DashScope 作为兜底 |
| 多租户隔离不完整导致数据泄露 | 低 | 极高 | 自动化测试 + CI 强制租户隔离测试用例 |
| SQLite 迁移 PostgreSQL 性能问题 | 低 | 中 | 保留 SQLite 选项作为小型部署（<10用户），PostgreSQL 作为 SaaS 默认 |
| 模型推理延迟影响用户体验 | 中 | 中 | 流式输出（Streaming），异步任务队列（Celery），超时降级 |
| Stripe Webhook 可靠性 | 低 | 中 | 幂等处理 + 失败重试 + 人工对账流程 |
| 用户分群设计过重 | 中 | 中 | MVP 只做导航和首页差异化，细节功能在 V2 实现 |

---

## 八、优先级建议

鉴于资源有限，建议按以下优先级分批实施：

### P0（必须先做 — 基础门槛）
1. 租户注册/登录（多租户基础）
2. Case + 核心模型 tenant_id 隔离
3. JWT 认证激活（替代当前假token）
4. SaaS Landing Page + 试用注册

### P1（核心价值 — 差异化竞争力）
5. 律所/企业首页差异化
6. 动态导航
7. LegalOne-R1 融合
8. Stripe 订阅计费

### P2（完善体验）
9. 律所专属功能（庭审辅助等）
10. 企业专属功能（合同管理等）
11. 品牌定制
12. 团队管理/邀请

### P3（可选）
13. 邮件服务
14. 高级监控
15. 灰度发布

---

## 九、附录

### 9.1 参考文档

- `DEVELOPMENT_CONSTITUTION.md` — 证据完整性最高原则（所有法律模型调用必须遵循）
- `plans/法律案件追踪系统_前端重设计_v3.0.md` — 前端重设计详细规范（可复用）
- `plans/法律专业数据_API_集成方案.md` — 法律数据 API（可作为法律知识库增强）
- `app/services/auth_service.py` — 现有 JWT 认证框架（需改造）
- `docker-compose.prod.yml` — 现有生产架构（需扩展）

### 9.2 法律模型 HuggingFace 链接

- LegalOne-R1: https://huggingface.co/THUIR/LegalOne-R1
- DISC-LawLLM: https://huggingface.co/ShengbinYue/DISC-LawLLM
- InternLM-Law: https://huggingface.co/internlm/internlm2-law-7b

### 9.3 名词解释

| 术语 | 说明 |
|------|------|
| Tenant（租户） | 在 SaaS 系统中，每个律所/企业是一个独立的租户 |
| Row-Level Security | 行级安全，通过 tenant_id 字段实现数据隔离 |
| Multi-Tenancy | 多租户架构，多个组织共享同一套基础设施但数据隔离 |
| Stripe Subscription | Stripe 订阅计费，支持套餐创建、更新、取消、Webhook |
| Feature Gate | 功能开关，控制不同套餐/用户类型可见的功能 |
| Ollama | 本地运行开源大模型的服务工具 |
| RAG | Retrieval-Augmented Generation，检索增强生成 |
