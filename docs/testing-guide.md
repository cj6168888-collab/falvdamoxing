# 法律案件追踪系统测试规范

> **创建日期**: 2026-04-02
> **最后更新**: 2026-04-02
> **版本**: v1.0

---

## 一、测试覆盖率目标

### 1.1 分层覆盖率要求

| 层级 | 目标覆盖率 | 说明 |
|------|-----------|------|
| 前端组件 | >70% | 关键业务组件优先覆盖 |
| 前端Hooks | >80% | 所有自定义Hook需覆盖 |
| 前端Utils | >90% | 工具函数需高覆盖率 |
| 后端API | >80% | 所有endpoint需覆盖 |
| 后端Service | >85% | 业务逻辑服务 |
| 核心模块 | >90% | LLM路由、法律检索等 |

### 1.2 关键指标

| 指标 | 目标 | 说明 |
|------|------|------|
| 测试通过率 | 100% | 所有测试必须通过 |
| 代码覆盖率 | >75% | 整体覆盖率 |
| 新功能覆盖率 | 100% | 新增代码必须有测试 |

---

## 二、测试类型

### 2.1 单元测试

**前端 - Jest/Vitest**

```typescript
// 文件: src/__tests__/utils/case-template.test.ts

import { describe, it, expect } from 'vitest'
import { fillFromTemplate, getTemplate } from '@/utils/case-template'

describe('CaseTemplate', () => {
  describe('getTemplate', () => {
    it('should return debt_dispute template when type is debt', () => {
      const template = getTemplate('debt_dispute')
      expect(template).toBeDefined()
      expect(template.type).toBe('debt_dispute')
    })

    it('should return null for unknown template type', () => {
      const template = getTemplate('unknown_type')
      expect(template).toBeNull()
    })
  })

  describe('fillFromTemplate', () => {
    it('should fill case info from template', () => {
      const template = getTemplate('debt_dispute')
      const parties = {
        plaintiff: '张三',
        defendant: '李四'
      }
      const result = fillFromTemplate(template!, parties)

      expect(result.type).toBe('debt_dispute')
      expect(result.parties).toEqual(parties)
    })

    it('should include recommended evidence list', () => {
      const template = getTemplate('debt_dispute')
      const result = fillFromTemplate(template!, {})

      expect(result.evidenceList).toBeDefined()
      expect(result.evidenceList.length).toBeGreaterThan(0)
    })
  })
})
```

**后端 - pytest**

```python
# 文件: tests/unit/test_deadline_calculator.py

import pytest
from datetime import date, timedelta
from app.services.deadline_calculator import calculate_deadline, is_workday

class TestDeadlineCalculator:
    """测试期限计算器"""

    def test_is_workday(self):
        """测试工作日判断"""
        assert is_workday(date(2026, 4, 7))  # 周一
        assert is_workday(date(2026, 4, 8))  # 周二
        assert not is_workday(date(2026, 4, 12))  # 周日

    def test_calculate_deadline_simple(self):
        """测试简单期限计算（无节假日）"""
        # 2026-04-01(周三) + 5个工作日 = 2026-04-08(周三)
        result = calculate_deadline(date(2026, 4, 1), 5)
        assert result == date(2026, 4, 8)

    def test_calculate_deadline_with_weekend(self):
        """测试包含周末的期限计算"""
        # 2026-04-03(周五) + 3个工作日 = 2026-04-09(周四)
        result = calculate_deadline(date(2026, 4, 3), 3)
        assert result == date(2026, 4, 9)

    def test_calculate_deadline_negative_days(self):
        """测试负数天数应抛出异常"""
        with pytest.raises(ValueError, match="days must be non-negative"):
            calculate_deadline(date(2026, 4, 1), -1)
```

### 2.2 集成测试

**前端 - MSW (Mock Service Worker)**

```typescript
// 文件: src/__tests__/integrations/case.api.test.ts

import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { useCase } from '@/hooks/use-case'

// Mock数据
const mockCase = {
  id: 'case-001',
  title: '民间借贷纠纷案',
  status: 'active',
  type: 'debt_dispute'
}

describe('Case API Integration', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false }
    }
  })

  it('should fetch case data successfully', async () => {
    server.use(
      http.get('/api/case/:id', () => {
        return HttpResponse.json(mockCase)
      })
    )

    const { result } = renderHook(() => useCase('case-001'), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(mockCase)
  })

  it('should handle API error', async () => {
    server.use(
      http.get('/api/case/:id', () => {
        return HttpResponse.json({ error: 'Not found' }, { status: 404 })
      })
    )

    const { result } = renderHook(() => useCase('case-001'), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
```

**后端 - Supertest**

```python
# 文件: tests/integration/test_appeal_api.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAppealAPI:
    """上诉追踪API集成测试"""

    def test_create_appeal(self, test_db):
        """测试创建上诉记录"""
        # 先创建一个案件
        case_response = client.post('/api/cases', json={
            'title': '测试案件',
            'type': 'debt_dispute'
        })
        case_id = case_response.json()['id']

        # 创建上诉
        response = client.post(
            f'/api/case/{case_id}/appeal',
            json={
                'reason': '事实认定错误',
                'target_court': '中级人民法院'
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data['reason'] == '事实认定错误'
        assert 'deadline' in data
        assert data['status'] == 'pending'

    def test_get_appeal_with_deadline(self, test_db):
        """测试获取上诉详情包含期限倒计时"""
        appeal = create_test_appeal()
        response = client.get(f'/api/appeal/{appeal.id}')

        assert response.status_code == 200
        data = response.json()
        assert 'countdown_days' in data
        assert data['countdown_days'] >= 0

    def test_update_appeal_status(self, test_db):
        """测试更新上诉状态"""
        appeal = create_test_appeal()
        response = client.put(
            f'/api/appeal/{appeal.id}/status',
            json={'status': 'approved'}
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'approved'

    @pytest.mark.parametrize('status', ['pending', 'approved', 'rejected', 'withdrawn'])
    def test_appeal_status_values(self, test_db, status):
        """测试上诉状态枚举值"""
        appeal = create_test_appeal()
        response = client.put(
            f'/api/appeal/{appeal.id}/status',
            json={'status': status}
        )
        assert response.status_code == 200
```

### 2.3 E2E测试

**Playwright**

```typescript
// 文件: e2e/cases.spec.ts

import { test, expect } from '@playwright/test'

test.describe('案件管理流程', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[name="email"]', 'test@example.com')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await page.waitForURL('/dashboard')
  })

  test('创建案件并生成上诉状', async ({ page }) => {
    // 1. 进入新建案件页面
    await page.goto('/cases/new')

    // 2. 选择案件模板
    await page.click('text=借贷纠纷')
    await page.waitForSelector('.template-selected')

    // 3. 填写案件信息
    await page.fill('[name="title"]', '张三诉李四民间借贷纠纷案')
    await page.fill('[name="plaintiff"]', '张三')
    await page.fill('[name="defendant"]', '李四')
    await page.fill('[name="amount"]', '100000')

    // 4. 提交案件
    await page.click('button[type="submit"]')
    await page.waitForSelector('.case-created-message')

    // 5. 生成上诉状
    await page.click('text=生成上诉状')
    await page.waitForSelector('.appeal-document')
    await expect(page.locator('.appeal-document h1')).toContainText('上诉状')
  })

  test('批量操作案件', async ({ page }) => {
    await page.goto('/cases')

    // 1. 选择多个案件
    await page.check('[data-case-id="case-1"]')
    await page.check('[data-case-id="case-2"]')
    await page.check('[data-case-id="case-3"]')

    // 2. 验证选中数量
    await expect(page.locator('.selected-count')).toContainText('已选择 3 项')

    // 3. 批量归档
    await page.click('text=批量归档')
    await page.click('text=确认归档')
    await page.waitForSelector('.toast-message:has-text("归档成功")')

    // 4. 验证归档结果
    await expect(page.locator('[data-case-id="case-1"]')).toHaveClass(/archived/)
  })

  test('案件模板预填功能', async ({ page }) => {
    await page.goto('/cases/new')

    // 选择合同纠纷模板
    await page.click('text=合同纠纷')

    // 验证自动填充
    await expect(page.locator('[name="type"]')).toHaveValue('contract_dispute')
    await expect(page.locator('.evidence-recommendation')).toContainText('合同原件')
    await expect(page.locator('.document-recommendation')).toContainText('合同变更协议')
  })
})

test.describe('LLM路由功能', () => {
  test('ModelRouter正确路由到本地模型', async ({ page }) => {
    await page.goto('/cases/case-001')

    // 生成文书（应使用本地模型）
    await page.click('text=生成文书')
    await page.waitForSelector('.document-content')

    // 验证使用本地模型
    const badge = page.locator('.model-badge')
    await expect(badge).toContainText('本地模型')
  })

  test('ModelRouter降级到云端模型', async ({ page }) => {
    // 模拟本地模型不可用
    await page.route('**/api/llm/local*', route => route.abort())

    await page.goto('/cases/case-001')
    await page.click('text=生成文书')

    // 等待并验证降级
    await page.waitForSelector('.fallback-indicator')
    const badge = page.locator('.model-badge')
    await expect(badge).toContainText('云端模型')
  })
})
```

---

## 三、测试用例命名规范

### 3.1 命名格式

```typescript
// 格式: [操作] should [预期结果] when [条件]
//       given [前置条件] should [预期] when [触发]

describe('ComponentName', () => {
  it('should render correctly when data is loaded', () => {
    // ...
  })

  it('should show error message when API fails', () => {
    // ...
  })

  it('should disable submit button when form is invalid', () => {
    // ...
  })

  describe('edge cases', () => {
    it('should handle empty array gracefully', () => {
      // ...
    })

    it('should handle null values without crashing', () => {
      // ...
    })
  })
})
```

### 3.2 BDD风格

```python
class TestModelRouter:
    """BDD风格测试"""

    def test_routes_to_local_for_simple_task(self):
        """给定简单任务，应该路由到本地模型"""
        # given
        task = {"type": "document_generation", "complexity": "low"}

        # when
        model = router.select_model(task)

        # then
        assert model == "local_gemma"

    def test_routes_to_cloud_for_complex_task(self):
        """给定复杂任务，应该路由到云端模型"""
        # given
        task = {"type": "prediction", "complexity": "high"}

        # when
        model = router.select_model(task)

        # then
        assert model == "cloud_qwen"

    def test_fallback_when_local_unavailable(self):
        """当本地模型不可用时，应该降级到云端"""
        # given
        router._local_available = False

        # when
        model = router.select_model(task)

        # then
        assert model == "cloud_qwen"
```

---

## 四、Mock策略

### 4.1 LLM服务Mock

```typescript
// 文件: src/__tests__/mocks/llm-service.ts

export const mockLLMService = {
  chat: jest.fn().mockResolvedValue({
    content: '这是Mock的LLM响应',
    model: 'mock-model',
    usage: { tokens: 100 }
  }),

  chatStream: jest.fn().mockReturnValue({
    async *[Symbol.asyncIterator]() {
      yield { content: 'Mock ', done: false }
      yield { content: 'streaming ', done: false }
      yield { content: 'response', done: true }
    }
  }),

  generateDocument: jest.fn().mockResolvedValue({
    title: '上诉状',
    content: 'Mock生成的文书内容...',
    format: 'docx'
  })
}

// 在测试中使用
jest.mock('@/services/llm-service', () => ({
  LLMService: jest.fn().mockImplementation(() => mockLLMService)
}))
```

### 4.2 API Mock (MSW)

```typescript
// 文件: src/__tests__/mocks/handlers.ts

import { http, HttpResponse } from 'msw'

export const handlers = [
  // 成功响应
  http.get('/api/cases', () => {
    return HttpResponse.json([
      { id: '1', title: '案件1', status: 'active' },
      { id: '2', title: '案件2', status: 'pending' }
    ])
  }),

  http.get('/api/cases/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      title: '测试案件',
      status: 'active'
    })
  }),

  // 错误响应
  http.post('/api/cases', () => {
    return HttpResponse.json(
      { error: '创建失败' },
      { status: 400 }
    )
  }),

  // 延迟响应
  http.get('/api/slow', async () => {
    await new Promise(resolve => setTimeout(resolve, 2000))
    return HttpResponse.json({ data: 'delayed' })
  })
]

// 错误场景handlers
export const errorHandlers = [
  http.get('/api/cases', () => {
    return HttpResponse.json('服务器错误', { status: 500 })
  }),

  http.get('/api/cases/:id', ({ params }) => {
    return HttpResponse.json({ error: 'Not found' }, { status: 404 })
  })
]
```

### 4.3 数据库Mock (后端)

```python
# 文件: tests/mocks/mock_db.py

import pytest
from unittest.mock import Mock, MagicMock
from datetime import date

@pytest.fixture
def mock_db():
    """Mock数据库fixture"""
    db = Mock()
    db.query = Mock(return_value=[
        {
            'id': 'case-001',
            'title': '测试案件',
            'status': 'active',
            'deadline': date(2026, 5, 1)
        }
    ])
    db.insert = Mock(return_value='case-002')
    db.update = Mock(return_value=True)
    db.delete = Mock(return_value=True)
    return db


@pytest.fixture
def mock_holiday_service():
    """Mock节假日服务"""
    holidays = Mock()
    holidays.is_holiday = Mock(side_effect=lambda d: d.weekday() >= 5)
    holidays.get_holidays_in_range = Mock(return_value=[
        date(2026, 4, 4),
        date(2026, 4, 5),
        date(2026, 4, 6)
    ])
    return holidays
```

---

## 五、测试环境配置

### 5.1 前端测试配置

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        functions: 80,
        branches: 70,
        lines: 75,
        type: 100
      },
      exclude: [
        'node_modules/**',
        '**/*.d.ts',
        '**/*.test.ts',
        '**/mocks/**'
      ]
    },
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist']
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
```

### 5.2 后端测试配置

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers --tb=short
markers =
    unit: 单元测试
    integration: 集成测试
    e2e: E2E测试
    slow: 慢速测试
filterwarnings =
    ignore::DeprecationWarning
```

---

## 六、每周测试检查

### 6.1 周五检查清单

```markdown
## 每周五测试检查

### 代码检查
- [ ] 所有新增代码有测试覆盖
- [ ] 测试通过率 100%
- [ ] 覆盖率报告已生成
- [ ] 新增测试符合命名规范

### 回归测试
- [ ] 现有功能未受影响
- [ ] 跨模块集成正常
- [ ] API兼容性检查通过

### 性能基准
- [ ] API响应时间 < 500ms
- [ ] 前端测试执行时间 < 30s
- [ ] LLM响应时间 < 10s

### 安全检查
- [ ] 无敏感信息泄露
- [ ] SQL注入测试通过
- [ ] XSS测试通过
```

### 6.2 覆盖率报告生成

```bash
# 前端
npm run test:coverage

# 后端
pytest --cov=app --cov-report=html tests/

# 生成HTML报告
open coverage/index.html
```

---

## 七、测试工具清单

| 工具 | 用途 | 安装 |
|------|------|------|
| Jest/Vitest | 前端单元测试 | `npm i -D vitest` |
| React Testing Library | React组件测试 | `npm i -D @testing-library/react` |
| MSW | API Mock | `npm i -D msw` |
| Playwright | E2E测试 | `npm i -D @playwright/test` |
| pytest | 后端单元测试 | `pip install pytest` |
| pytest-cov | 覆盖率报告 | `pip install pytest-cov` |
| Factory Boy | 测试数据工厂 | `pip install factory-boy` |
| Faker | 假数据生成 | `pip install faker` |

---

*文档版本: v1.0*
*最后更新: 2026-04-02*
