# 法律案件追踪系统文档管理规范

> **创建日期**: 2026-04-02
> **最后更新**: 2026-04-02
> **版本**: v1.0

---

## 一、文档分类

### 1.1 文档类型

| 类型 | 说明 | 位置 | 更新频率 |
|------|------|------|----------|
| 项目文档 | 项目整体说明 | `/docs/` | 按需 |
| API文档 | 接口说明 | `/docs/api/` | 变更时 |
| 组件文档 | 前端组件 | `/docs/components/` | 变更时 |
| 部署文档 | 部署配置 | `/docs/deploy/` | 变更时 |
| 设计文档 | 架构设计 | `/docs/design/` | 按需 |
| 规范文档 | 开发规范 | `/docs/` | 重大变更时 |

### 1.2 必需文档清单

| 文档 | 创建者 | 审批者 | 更新触发 |
|------|--------|--------|----------|
| README.md | 所有开发者 | Tech Lead | 任何变更 |
| API文档 | 后端开发者 | Tech Lead | API变更 |
| 部署文档 | DevOps | Tech Lead | 部署变更 |
| CHANGELOG.md | 所有开发者 | Tech Lead | 版本发布 |

---

## 二、README模板

```markdown
# 法律案件追踪系统

> 智能法律案件管理系统，支持案件追踪、文书生成、LLM辅助分析

## 功能特性

- [ ] 案件管理
- [ ] 文书生成
- [ ] 智能对话
- [ ] 出庭抗辩辅助
- [ ] 法律资料库

## 技术栈

### 前端
- React 18
- TypeScript
- Tailwind CSS
- React Query

### 后端
- FastAPI
- Python 3.11
- PostgreSQL
- ChromaDB

### AI
- Ollama (本地模型)
- DashScope (云端模型)
- ModelRouter (智能路由)

## 快速开始

### 前置要求
- Node.js 18+
- Python 3.11+
- Docker (可选)

### 安装

```bash
# 克隆项目
git clone https://github.com/your-org/legal-case-tracker.git
cd legal-case-tracker

# 前端
cd frontend
npm install
npm run dev

# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 开发

```bash
# 前端测试
npm run test

# 后端测试
pytest tests/

# 代码检查
npm run lint
flake8 app/
```

## 部署

详见 [部署文档](./docs/deployment-strategy.md)

## API文档

详见 [API文档](./docs/api/)

## 贡献指南

1. 创建分支 `git checkout -b feature/xxx`
2. 提交代码 `git commit -m 'feat: add xxx'`
3. 推送分支 `git push`
4. 创建PR

## 许可证

MIT License
```

---

## 三、API文档规范

### 3.1 OpenAPI 3.0 格式

```yaml
# docs/api/openapi.yaml
openapi: 3.0.0
info:
  title: 法律案件追踪系统 API
  description: |
    法律案件追踪系统RESTful API
    
    ## 认证
    使用Bearer Token认证
    
    ## 错误码
    - 400: 请求参数错误
    - 401: 未授权
    - 404: 资源不存在
    - 500: 服务器错误
  version: 2.1.0
  contact:
    email: support@legal-ai.com

servers:
  - url: https://api.legal-ai.com
    description: 生产环境
  - url: https://staging.legal-ai.com
    description: 预发布环境

paths:
  /api/cases:
    get:
      summary: 获取案件列表
      description: 获取当前用户的案件列表，支持分页和过滤
      tags: [案件管理]
      operationId: getCases
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
        - name: status
          in: query
          schema:
            type: string
            enum: [pending, active, closed]
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CaseList'
        '401':
          $ref: '#/components/responses/Unauthorized'

  /api/cases/{case_id}:
    get:
      summary: 获取案件详情
      tags: [案件管理]
      operationId: getCaseById
      parameters:
        - $ref: '#/components/parameters/CaseId'
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Case'
        '404':
          $ref: '#/components/responses/NotFound'

    put:
      summary: 更新案件
      tags: [案件管理]
      operationId: updateCase
      parameters:
        - $ref: '#/components/parameters/CaseId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CaseUpdate'
      responses:
        '200':
          description: 更新成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Case'

  /api/appeal:
    post:
      summary: 创建上诉记录
      tags: [上诉追踪]
      operationId: createAppeal
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [case_id, reason]
              properties:
                case_id:
                  type: string
                  format: uuid
                reason:
                  type: string
                  maxLength: 2000
                target_court:
                  type: string
      responses:
        '201':
          description: 创建成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Appeal'

components:
  parameters:
    CaseId:
      name: case_id
      in: path
      required: true
      schema:
        type: string
        format: uuid

  schemas:
    Case:
      type: object
      properties:
        id:
          type: string
          format: uuid
        title:
          type: string
        status:
          type: string
          enum: [pending, active, closed]
        type:
          type: string
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    CaseList:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Case'
        total:
          type: integer
        page:
          type: integer
        page_size:
          type: integer

    Appeal:
      type: object
      properties:
        id:
          type: string
          format: uuid
        case_id:
          type: string
          format: uuid
        reason:
          type: string
        deadline:
          type: string
          format: date
        countdown_days:
          type: integer
        status:
          type: string
          enum: [pending, approved, rejected, withdrawn]

  responses:
    Unauthorized:
      description: 未授权
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    NotFound:
      description: 资源不存在
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    Error:
      type: object
      properties:
        error:
          type: string
        message:
          type: string
        code:
          type: string

security:
  - BearerAuth: []
```

### 3.2 API端点注释示例

```python
# app/api/cases.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/cases", tags=["案件管理"])


class CaseCreate(BaseModel):
    """创建案件请求"""
    title: str = Field(..., min_length=1, max_length=200, description="案件标题")
    type: str = Field(..., description="案件类型")
    description: Optional[str] = Field(None, max_length=5000, description="案件描述")
    plaintiff: str = Field(..., description="原告")
    defendant: str = Field(..., description="被告")
    amount: Optional[float] = Field(None, ge=0, description="诉讼金额")


class CaseResponse(BaseModel):
    """案件响应"""
    id: str
    title: str
    type: str
    status: str
    plaintiff: str
    defendant: str
    amount: Optional[float]
    created_at: str
    updated_at: str


@router.get("", response_model=List[CaseResponse], summary="获取案件列表")
async def get_cases(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="案件状态过滤")
) -> List[CaseResponse]:
    """获取当前用户的案件列表

    支持分页和状态过滤

    Args:
        page: 页码，从1开始
        page_size: 每页返回的数量，最大100
        status: 可选，按案件状态过滤

    Returns:
        案件列表

    Raises:
        HTTPException: 获取失败时抛出500错误
    """
    try:
        cases = await case_service.get_cases(
            page=page,
            page_size=page_size,
            status=status
        )
        return cases
    except Exception as e:
        logger.error(f"Failed to get cases: {e}")
        raise HTTPException(status_code=500, detail="获取案件列表失败")


@router.post("", response_model=CaseResponse, status_code=201, summary="创建案件")
async def create_case(case_data: CaseCreate) -> CaseResponse:
    """创建新案件

    根据提供的信息创建新案件，包括基本信息、当事人和诉讼金额

    Args:
        case_data: 案件创建数据

    Returns:
        创建的案件信息

    Raises:
        HTTPException: 创建失败时抛出400或500错误
    """
    try:
        case = await case_service.create_case(case_data.dict())
        return case
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create case: {e}")
        raise HTTPException(status_code=500, detail="创建案件失败")
```

---

## 四、组件文档规范

### 4.1 Storybook组件

```tsx
// components/CaseCard/CaseCard.stories.tsx

import type { Meta, StoryObj } from '@storybook/react'
import { CaseCard } from './CaseCard'

const meta: Meta<typeof CaseCard> = {
  title: 'Components/CaseCard',
  component: CaseCard,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'compact', 'detailed'],
      description: '卡片变体'
    },
    status: {
      control: 'select',
      options: ['pending', 'active', 'closed'],
      description: '案件状态'
    }
  }
}

export default meta
type Story = StoryObj<typeof CaseCard>

// 默认状态
export const Default: Story = {
  args: {
    caseData: {
      id: 'case-001',
      title: '张三诉李四民间借贷纠纷案',
      type: 'debt_dispute',
      status: 'active',
      plaintiff: '张三',
      defendant: '李四',
      amount: 100000,
      deadline: '2026-05-01'
    }
  }
}

// 待处理状态
export const Pending: Story = {
  args: {
    caseData: {
      ...Default.args.caseData,
      status: 'pending'
    }
  }
}

// 已关闭状态
export const Closed: Story = {
  args: {
    caseData: {
      ...Default.args.caseData,
      status: 'closed'
    }
  }
}

// 紧凑模式
export const Compact: Story = {
  args: {
    ...Default.args,
    variant: 'compact'
  }
}

// 加载状态
export const Loading: Story = {
  args: {
    isLoading: true
  }
}

// 错误状态
export const Error: Story = {
  args: {
    error: '无法加载案件信息'
  }
}
```

---

## 五、CHANGELOG规范

### 5.1 CHANGELOG格式

```markdown
# Changelog

所有重要的项目变更将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

## [2.1.0] - 2026-04-02

### 新增
- 添加案件批量操作功能
- 添加案件模板库
- 添加文书版本diff对比
- 添加ModelRouter智能路由

### 优化
- 优化面板布局交互
- 优化LLM响应速度

### 修复
- 修复上诉期限计算错误
- 修复批量导出数据丢失问题

### 安全
- 更新依赖包版本

## [2.0.0] - 2026-03-01

### 新增
- 全新前端UI设计
- LLM辅助对话功能
- 出庭抗辩辅助系统

### 重大变更
- 重构数据库模型
- 迁移到FastAPI
```

### 5.2 提交信息转CHANGELOG

使用 `conventional-changelog` 自动生成：

```bash
# 安装
npm install -D conventional-changelog conventional-commits-detector

# 生成CHANGELOG
npm run changelog

# 或指定版本
npm run changelog -- --release-count 2
```

---

## 六、文档目录结构

```
docs/
├── README.md                          # 文档首页
├── coding-standards.md               # 代码规范
├── testing-guide.md                  # 测试规范
├── deployment-strategy.md            # 部署策略
├── documentation-standards.md        # 文档规范
│
├── api/                              # API文档
│   ├── README.md                     # API概览
│   ├── openapi.yaml                  # OpenAPI规范
│   ├── cases.md                      # 案件API
│   ├── appeal.md                     # 上诉API
│   ├── legal-knowledge.md            # 法律资料库API
│   └── llm.md                        # LLM API
│
├── components/                       # 组件文档
│   ├── CaseCard.md
│   ├── CaseList.md
│   └── ...
│
├── deploy/                           # 部署文档
│   ├── docker.md                     # Docker部署
│   ├── kubernetes.md                  # K8s部署
│   ├── monitoring.md                 # 监控配置
│   └── troubleshooting.md            # 故障排查
│
└── design/                           # 设计文档
    ├── architecture.md               # 架构设计
    ├── database.md                   # 数据库设计
    ├── llm-routing.md                # LLM路由设计
    └── legal-knowledge.md            # 法律资料库设计
```

---

## 七、文档编写规范

### 7.1 标题层级

```markdown
# 一级标题 - 文档标题
## 二级标题 - 主要章节
### 三级标题 - 子章节
#### 四级标题 - 小节
```

### 7.2 表格格式

```markdown
| 列1 | 列2 | 列3 |
|------|------|------|
| 内容 | 内容 | 内容 |
| 内容 | 内容 | 内容 |
```

### 7.3 代码块

```markdown
```语言
代码内容
```
```

### 7.4 文档检查清单

```markdown
## 文档更新检查清单

- [ ] 文档格式正确
- [ ] 无错别字
- [ ] 代码示例可执行
- [ ] 链接有效
- [ ] 相关文档已更新
- [ ] 已通过Review
```

---

*文档版本: v1.0*
*最后更新: 2026-04-02*
