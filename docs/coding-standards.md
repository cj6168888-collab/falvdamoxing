# 法律案件追踪系统代码规范

> **创建日期**: 2026-04-02
> **最后更新**: 2026-04-02
> **版本**: v1.0

---

## 一、Git提交规范

### 1.1 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**格式说明**:

| 部分 | 格式 | 说明 |
|------|------|------|
| type | feat/fix/docs/style/refactor/test/chore | 提交类型 |
| scope | frontend/backend/api/llm/legal-db/deploy | 影响范围 |
| subject | 简短描述，不超过50字 | 提交主题 |

### 1.2 Type 类型说明

| 类型 | 说明 | 触发场景 |
|------|------|----------|
| feat | 新功能 | 添加新功能 |
| fix | 修复bug | 修复缺陷 |
| docs | 文档更新 | README、注释 |
| style | 格式调整 | 不影响代码逻辑的修改 |
| refactor | 重构 | 既不是修复也不是新功能 |
| test | 测试相关 | 添加/修改测试 |
| chore | 构建/工具 | 构建脚本、依赖更新 |

### 1.3 示例

```bash
# 正确示例
feat(frontend): 添加案件列表批量选择功能
fix(backend): 修复上诉期限计算节假日问题
docs(api): 更新法律资料库API接口文档
refactor(llm): 重构ModelRouter路由选择逻辑
test(legal-db): 添加法条检索边界条件测试

# 错误示例
fix: 修复bug
Update README
WIP
```

---

## 二、分支命名规范

### 2.1 分支类型

| 类型 | 格式 | 示例 | 说明 |
|------|------|------|------|
| 功能分支 | `feature/<issue-id>-<short-desc>` | `feature/P0-F001-panel-layout` | 新功能开发 |
| 修复分支 | `bugfix/<issue-id>-<short-desc>` | `bugfix/P0-B001-appeal-api` | bug修复 |
| 热修复 | `hotfix/<issue-id>-<short-desc>` | `hotfix/critical-auth-bug` | 紧急修复 |
| 发布分支 | `release/v<version>` | `release/v2.1.0` | 版本发布 |
| 开发分支 | `develop` | - | 开发主分支 |
| 主分支 | `main` | - | 生产代码 |

### 2.2 分支操作流程

```bash
# 1. 从develop创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/P0-F001-panel-layout

# 2. 开发完成后，提交PR到develop
git push origin feature/P0-F001-panel-layout

# 3. 合并后删除分支
git branch -d feature/P0-F001-panel-layout
```

---

## 三、前端代码规范

### 3.1 命名规范

```typescript
// ========== 组件命名 (PascalCase) ==========
// Good
UserProfile, CaseList, AppealForm, LegalDocument

// Bad
userProfile, case_list, appeal-form, LegalDocument

// ========== 文件命名 (kebab-case) ==========
// Good
user-profile.tsx, case-list.tsx, appeal-form.tsx

// Bad
UserProfile.tsx, caseList.tsx, AppealForm.tsx, appealForm.tsx

// ========== Hooks命名 (use + camelCase) ==========
// Good
useFetchUserData, useCaseStore, useTextToSpeech

// Bad
fetchUserData, caseStore, CaseStore, use_case_store

// ========== 类型定义 (PascalCase) ==========
// Good - Interface
interface UserProfileT { ... }
interface CaseInfoT { ... }

// Good - Type
type CaseStatusT = 'pending' | 'active' | 'closed'
type ApiResponseT<T> = { data: T; error: string | null }

// Bad
type userProfile, case_info

// ========== 常量 (UPPER_SNAKE_CASE) ==========
// Good
const MAX_RETRY_COUNT = 3
const API_BASE_URL = '/api/v1'
const CASE_STATUS = { ... }

// Bad
const maxRetryCount = 3
const apiBaseUrl = '/api/v1'

// ========== 事件处理函数 ==========
// Good
const handleClick = () => { ... }
const onSubmit = () => { ... }
const handleCaseSelect = (caseId: string) => { ... }

// Bad
const click = () => { ... }
const submit = () => { ... }
```

### 3.2 导入顺序

```typescript
// 1. React/Core
import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

// 2. 第三方库
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { AnimatePresence } from 'framer-motion'

// 3. 内部组件
import { Button } from '@/components/ui/button'
import { CaseCard } from '@/components/case/case-card'

// 4. 内部hooks/utils
import { useAuth } from '@/hooks/use-auth'
import { formatDate } from '@/utils/date'

// 5. 类型定义
import type { CaseInfoT, UserProfileT } from '@/types'

// 6. Assets
import './case-list.css'
```

### 3.3 组件结构

```typescript
// 1. 导入
import React from 'react'
import { Button } from '@/components/ui/button'

// 2. 类型定义
interface CaseCardProps {
  case: CaseInfoT
  onSelect: (id: string) => void
}

// 3. 组件定义
export const CaseCard: React.FC<CaseCardProps> = ({ case: caseData, onSelect }) => {
  // 4. Hooks
  const { user } = useAuth()
  const [isExpanded, setIsExpanded] = useState(false)

  // 5. 事件处理
  const handleClick = () => {
    onSelect(caseData.id)
  }

  // 6. 渲染
  return (
    <div className="case-card" onClick={handleClick}>
      <h3>{caseData.title}</h3>
      <p>{caseData.status}</p>
    </div>
  )
}

// 7. 导出
export default CaseCard
```

### 3.4 其他规范

```typescript
// 1. 条件渲染 - 优先使用三元运算符短形式
{isLoading && <Spinner />}

// Bad
{isLoading ? <Spinner /> : null}

// 2. 回调函数 - 使用useCallback优化
const handleSubmit = useCallback((data: FormData) => {
  submitCase(data)
}, [submitCase])

// 3. Promise处理 - 优先async/await
const fetchCase = async (id: string) => {
  try {
    const data = await api.getCase(id)
    return data
  } catch (error) {
    console.error('Failed to fetch case:', error)
    throw error
  }
}

// 4. 类型断言 - 避免使用any
// Good
const value = data as CaseInfoT

// Bad
const value: any = data

// 5. 空值检查
if (!caseData?.id) return
```

---

## 四、后端代码规范

### 4.1 命名规范

```python
# ========== 类命名 (PascalCase) ==========
class LegalKnowledgeService:
    ...

class ModelRouter:
    ...

# Bad
class legalKnowledgeService:
class legal_knowledge_service:

# ========== 函数命名 (snake_case) ==========
def calculate_deadline():
    ...

def get_case_by_id():
    ...

# Bad
def calculateDeadline():
def GetCaseById():

# ========== 常量 (UPPER_SNAKE_CASE) ==========
MAX_BATCH_SIZE = 100
DEFAULT_TIMEOUT = 30
LEGAL_DB_PATH = '/data/legal'

# Bad
max_batch_size = 100
MAXBATCHSIZE = 100

# ========== 私有成员 ==========
# Good
class LegalService:
    def __init__(self):
        self._cache = {}
        self.__private_cache = {}

# Bad
class LegalService:
    def __init__(self):
        self.cache = {}
```

### 4.2 导入顺序

```python
# 1. 标准库
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from functools import lru_cache
import json

# 2. 第三方库
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

# 3. 内部模块
from app.services.llm_router import ModelRouter
from app.db.legal_db import LegalDatabase
from app.models.case import CaseModel

# 4. 相对导入
from .utils import format_date
from ..schemas import CaseSchema
```

### 4.3 类型提示

```python
from typing import Optional, List, Dict, Any, Union
from datetime import date

# 函数参数和返回值
def get_case_by_id(case_id: str) -> Optional[Dict[str, Any]]:
    ...

def calculate_deadline(start_date: date, days: int) -> date:
    ...

def batch_process(items: List[str]) -> List[Dict[str, Any]]:
    ...

def get_user_cases(user_id: str) -> Union[List[Dict], None]:
    ...

# 类属性
class CaseService:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timeout: int = 30
```

### 4.4 文档字符串

```python
def calculate_deadline(start_date: date, days: int) -> date:
    """计算工作日截止日期，自动排除节假日

    根据给定的工作日数，计算不包括周末和法定节假日的截止日期。

    Args:
        start_date: 起始日期
        days: 期限天数（工作日）

    Returns:
        计算后的截止日期

    Raises:
        ValueError: days为负数时
        TypeError: start_date不是date类型时

    Example:
        >>> from datetime import date
        >>> calculate_deadline(date(2026, 4, 1), 15)
        date(2026, 4, 22)
    """
    if days < 0:
        raise ValueError("days must be non-negative")
    if not isinstance(start_date, date):
        raise TypeError("start_date must be a date object")
    ...


class ModelRouter:
    """LLM模型智能路由

    根据任务类型自动选择最优的LLM模型（本地或云端）。

    Attributes:
        local_model: 本地模型配置
        cloud_model: 云端模型配置
        fallback_enabled: 是否启用降级策略
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化路由

        Args:
            config: 路由配置，包含模型参数和路由规则
        """
        ...
```

### 4.5 异常处理

```python
from fastapi import HTTPException
from typing import Optional

# 1. 使用自定义异常
class LegalDBError(Exception):
    """法律资料库操作异常"""
    pass

class ModelRouterError(Exception):
    """模型路由异常"""
    pass

# 2. FastAPI异常处理
@app.get("/api/case/{case_id}")
async def get_case(case_id: str):
    try:
        case = await case_service.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="案件不存在")
        return case
    except LegalDBError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

# 3. 资源清理
def process_large_file(filepath: str):
    file = None
    try:
        file = open(filepath, 'r')
        # 处理文件
    finally:
        if file:
            file.close()

# 推荐使用context manager
def process_large_file_v2(filepath: str):
    with open(filepath, 'r') as file:
        # 处理文件
        pass  # 自动关闭文件
```

### 4.6 日志记录

```python
import logging
from typing import Optional

# 1. 配置logger
logger = logging.getLogger(__name__)

# 2. 日志级别使用
logger.debug("调试信息，仅开发环境")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 3. 结构化日志
logger.info(
    "Case created",
    extra={
        "case_id": case_id,
        "user_id": user_id,
        "case_type": case_type
    }
)

# 4. 异常日志
try:
    result = risky_operation()
except Exception as e:
    logger.error(
        f"Operation failed: {str(e)}",
        exc_info=True,  # 包含堆栈信息
        extra={"context": "case_creation"}
    )
    raise
```

---

## 五、PR审查清单

### 5.1 创建PR前

```markdown
## PR创建前检查

### 代码质量
- [ ] 代码符合本规范的命名和格式要求
- [ ] 无硬编码的敏感信息（密码、密钥等）
- [ ] 无console.log/print/debugger
- [ ] TypeScript类型检查通过: `npm run type-check`
- [ ] Python类型检查通过: `flake8 --extend-ignore=E501`
- [ ] ESLint检查通过: `npm run lint`

### 测试要求
- [ ] 新功能有对应的单元测试
- [ ] 测试覆盖率未下降（前端>70%，后端>80%）
- [ ] 测试用例命名符合规范

### 文档要求
- [ ] API接口有OpenAPI文档注释
- [ ] 复杂业务逻辑有说明
- [ ] README已更新（如需要）

### 功能要求
- [ ] 功能实现符合需求
- [ ] 边界条件已处理
- [ ] 错误处理完善
- [ ] 无明显的性能问题

### Git要求
- [ ] 提交信息符合规范
- [ ] 分支命名符合规范
- [ ] 无不必要的提交（调试提交等）
```

### 5.2 Reviewer检查

```markdown
## 代码审查清单

### 功能正确性
- [ ] 代码逻辑正确
- [ ] 边界条件处理完整
- [ ] 错误处理完善

### 代码质量
- [ ] 符合代码规范
- [ ] 无重复代码
- [ ] 函数/组件职责单一
- [ ] 命名清晰易懂

### 安全性
- [ ] 无安全漏洞（SQL注入、XSS等）
- [ ] 敏感信息处理正确
- [ ] 权限校验完整

### 性能
- [ ] 无明显的性能问题
- [ ] 大数据量场景已考虑
- [ ] 无内存泄漏风险

### 测试
- [ ] 测试用例合理
- [ ] 覆盖率达标
- [ ] 测试可重复执行
```

---

## 六、IDE配置建议

### 6.1 VS Code 设置

```json
{
  // ========== 格式化 ==========
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },

  // ========== ESLint ==========
  "eslint.enable": true,
  "eslint.validate": ["typescript", "typescriptreact"],

  // ========== Python ==========
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",

  // ========== 其他 ==========
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true
  }
}
```

### 6.2 Prettier 配置

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "always"
}
```

---

*文档版本: v1.0*
*最后更新: 2026-04-02*
