# 法律案件追踪系统

> 智能法律案件管理系统，支持案件追踪、文书生成、LLM辅助分析、出庭抗辩

---

## 功能特性

### 核心功能
- [x] 案件管理 - 创建、编辑、归档、导出
- [x] 当事人管理 - 原告/被告信息、企业核查
- [x] 证据管理 - 证据清单、上传、缺口分析
- [x] 文书管理 - 模板生成、版本管理、diff对比
- [x] 会议管理 - 会议记录、录音存证
- [x] 资深分析 - AI案件分析、策略建议

### 智能功能
- [x] 智能对话 - 意图识别、澄清机制
- [x] 出庭抗辩 - 三种模式、紧急接管、TTS语音
- [x] 法律资料库 - 法条检索、司法解释、指导案例
- [ ] LLM混合路由 - 本地+云端智能切换
- [ ] 胜诉评估 - 基于历史案例的概率评估

### 企业功能
- [x] 上诉追踪 - 期限倒计时、上诉状生成
- [x] 执行跟踪 - 执行进度、金额管理
- [ ] 提醒中心 - 智能提醒、批量操作
- [ ] 工作台 - 统计聚合、待办事项

---

## 技术栈

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18+ | UI框架 |
| TypeScript | 5.0+ | 类型安全 |
| Tailwind CSS | 3.4+ | 样式框架 |
| React Query | 5.0+ | 数据请求 |
| React Router | 6.0+ | 路由管理 |
| Zustand | 4.0+ | 状态管理 |

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.110+ | Web框架 |
| Python | 3.11+ | 运行环境 |
| SQLite | 3.x | 业务数据库 |
| PostgreSQL | 15+ | 法律资料库 |
| ChromaDB | 0.4+ | 向量数据库 |
| SQLAlchemy | 2.0+ | ORM |

### AI/ML
| 技术 | 用途 |
|------|------|
| Ollama | 本地LLM |
| Gemma 4 | 本地模型 |
| DashScope | 云端LLM |
| ModelRouter | 智能路由 |
| sentence-transformers | 本地Embedding |

---

## 项目结构

```
legal-case-tracker/
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── components/         # React组件
│   │   ├── pages/             # 页面
│   │   ├── hooks/             # 自定义Hooks
│   │   ├── stores/            # 状态管理
│   │   ├── api/               # API客户端
│   │   └── types/             # 类型定义
│   └── public/
│
├── backend/                     # 后端项目
│   ├── app/
│   │   ├── api/               # API路由
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 业务服务
│   │   ├── db/                # 数据库
│   │   └── core/              # 核心配置
│   └── tests/
│
├── docs/                        # 文档
│   ├── api/                    # API文档
│   ├── design/                 # 设计文档
│   ├── components/             # 组件文档
│   └── deploy/                 # 部署文档
│
├── docker-compose.yml           # Docker编排
├── Dockerfile                  # 构建文件
└── README.md                   # 项目说明
```

---

## 快速开始

### 前置要求

| 要求 | 版本 | 说明 |
|------|------|------|
| Node.js | 18+ | 前端运行 |
| Python | 3.11+ | 后端运行 |
| Git | 2.0+ | 版本控制 |
| Docker | 24+ | 可选，容器化部署 |

### 安装

```bash
# 克隆项目
git clone https://github.com/your-org/legal-case-tracker.git
cd legal-case-tracker

# 前端安装
cd frontend
npm install
npm run dev

# 后端安装
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## 开发

### 前端开发

```bash
cd frontend

# 开发服务器
npm run dev

# 类型检查
npm run type-check

# 代码检查
npm run lint

# 测试
npm run test

# 测试覆盖率
npm run test:coverage

# 构建
npm run build
```

### 后端开发

```bash
cd backend

# 开发服务器
uvicorn app.main:app --reload

# 代码检查
flake8 app/ --max-line-length=120

# 格式化
black app/

# 测试
pytest tests/ -v

# 测试覆盖率
pytest tests/ --cov=app --cov-report=html
```

---

## 环境变量

### 前端 (.env)

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=法律案件追踪系统
VITE_ENABLE_ANALYTICS=false
```

### 后端 (.env)

```env
# 数据库
DB_TYPE=sqlite
# DB_TYPE=postgresql
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=legal_tracker
# DB_USER=postgres
# DB_PASSWORD=secret

# LLM配置
LLM_PROVIDER=local
# LLM_PROVIDER=cloud
# DASHSCOPE_API_KEY=sk-xxx

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma:4b

# 法律资料库
LEGAL_DB_PATH=./data/legal.db
VECTOR_DB_PATH=./data/chroma

# 服务器
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

---

## API文档

### 本地API文档

启动后端后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI: http://localhost:8000/openapi.json

### 在线文档

- [API文档](./docs/api/README.md)
- [部署文档](./docs/deployment-strategy.md)
- [代码规范](./docs/coding-standards.md)

---

## 测试

### 测试策略

| 层级 | 工具 | 覆盖率目标 |
|------|------|-----------|
| 单元测试 | Jest/Vitest | >70% |
| 集成测试 | Supertest | >80% |
| E2E测试 | Playwright | 核心流程 |

详见: [测试规范](./docs/testing-guide.md)

### 运行测试

```bash
# 前端
npm run test:ci

# 后端
pytest tests/ -v --cov=app

# E2E
npx playwright test
```

---

## 部署

### 部署模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 开发模式 | SQLite + 单机 | 本地开发 |
| 生产模式 | PostgreSQL + Docker | 正式环境 |
| 混合模式 | Ollama + DashScope | LLM混合 |

详见: [部署策略](./docs/deployment-strategy.md)

### Kubernetes部署

```bash
# 部署到K8s
kubectl apply -f k8s/

# 检查状态
kubectl get pods -n legal-tracker

# 查看日志
kubectl logs -f deployment/backend -n legal-tracker
```

---

## 贡献指南

### 分支命名

```bash
feature/P0-F001-panel-layout     # 新功能
bugfix/P0-B001-appeal-api        # Bug修复
hotfix/critical-auth             # 紧急修复
release/v2.1.0                  # 版本发布
```

### 提交规范

```
feat(frontend): 添加案件列表批量操作
fix(backend): 修复上诉期限计算错误
docs(api): 更新法律资料库API文档
refactor(llm): 重构ModelRouter路由逻辑
test(legal-db): 添加法条检索测试
```

详见: [代码规范](./docs/coding-standards.md)

### Pull Request流程

1. Fork仓库并创建分支
2. 提交代码并通过所有测试
3. 创建PR并描述变更
4. 通过Code Review
5. 合并到develop分支

---

## 路线图

### v2.1.0 (当前)
- [x] 前端功能升级
- [x] 后端API完善
- [x] 第三方API集成
- [ ] LLM混合路由

### v2.2.0 (计划)
- [ ] 胜诉概率评估
- [ ] 智能提醒系统
- [ ] 移动端适配

### v3.0.0 (计划)
- [ ] 插件系统
- [ ] 多租户支持
- [ ] 高级分析报表

---

## 许可证

MIT License

---

## 联系方式

- 邮箱: support@legal-ai.com
- GitHub: https://github.com/your-org/legal-case-tracker
- 文档: https://docs.legal-ai.com
