# 法律案件追踪系统部署策略

> **创建日期**: 2026-04-02
> **最后更新**: 2026-04-02
> **版本**: v1.0

---

## 一、环境划分

### 1.1 环境定义

| 环境 | 用途 | 部署触发 | 数据 | URL |
|------|------|----------|------|-----|
| development | 本地开发 | 自动 | 模拟数据 | localhost:3000 |
| staging | 预发布测试 | PR合并 | 脱敏数据 | staging.legal-ai.com |
| production | 正式环境 | 手动审批 | 生产数据 | legal-ai.com |

### 1.2 环境配置

```yaml
# docker-compose.yml 结构
services:
  # 开发环境
  dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src
    environment:
      - ENV=development
      - DB_TYPE=sqlite

  # 预发布环境
  staging:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - ENV=staging
      - DB_TYPE=postgresql
      - DB_HOST=staging-db.internal
    deploy:
      replicas: 2

  # 生产环境
  prod:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - ENV=production
      - DB_TYPE=postgresql
      - DB_HOST=prod-db.internal
    deploy:
      replicas: 4
      update_config:
        parallelism: 1
        delay: 10s
```

---

## 二、CI/CD流程

### 2.1 GitHub Actions 工作流

```yaml
# .github/workflows/deploy.yml

name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ========== 代码检查 ==========
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: ESLint
        run: npm run lint

      - name: TypeScript check
        run: npm run type-check

  # ========== 后端检查 ==========
  backend-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install flake8 black

      - name: Flake8
        run: flake8 app/ --max-line-length=120

      - name: Black check
        run: black --check app/

  # ========== 测试 ==========
  test:
    runs-on: ubuntu-latest
    needs: [lint, backend-check]
    steps:
      - uses: actions/checkout@v4

      - name: Frontend tests
        run: npm run test:ci

      - name: Backend tests
        run: pytest tests/ -v --cov=app

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  # ========== 构建 ==========
  build:
    runs-on: ubuntu-latest
    needs: [test]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} .

      - name: Push to Registry
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ${{ env.REGISTRY }} -u ${{ github.actor }} --password-stdin
          docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  # ========== 部署Staging ==========
  deploy-staging:
    runs-on: ubuntu-latest
    needs: [build]
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          kubectl config use-context staging
          kubectl set image deployment/backend backend=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          kubectl rollout status deployment/backend

  # ========== 集成测试 ==========
  e2e-staging:
    runs-on: ubuntu-latest
    needs: [deploy-staging]
    steps:
      - uses: actions/checkout@v4

      - name: Playwright tests
        run: |
          npx playwright test --project=chromium
        env:
          BASE_URL: https://staging.legal-ai.com

  # ========== 部署Production ==========
  deploy-production:
    runs-on: ubuntu-latest
    needs: [e2e-staging]
    environment: production
    steps:
      - name: Deploy to production
        run: |
          kubectl config use-context production
          kubectl set image deployment/backend backend=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          kubectl rollout status deployment/backend
```

---

## 三、分阶段部署

### 3.1 Canary部署策略

```yaml
# canary-deployment.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: backend-rollout
spec:
  replicas: 10
  strategy:
    canary:
      steps:
        - setWeight: 10      # 10% 流量
        - pause: {duration: 30m}
        - analysis:
            templates:
              - templateName: success-rate
            args:
              - name: service-name
                value: backend-rollout
        - setWeight: 50      # 50% 流量
        - pause: {duration: 1h}
        - setWeight: 100     # 全量
      canaryMetadata:
        labels:
          track: canary
      stableMetadata:
        labels:
          track: stable
```

### 3.2 部署检查点

| 阶段 | 流量比例 | 持续时间 | 检查项 | 失败处理 |
|------|----------|----------|--------|----------|
| Canary 10% | 10% | 30分钟 | 错误率<1% | 立即回滚 |
| Canary 50% | 50% | 1小时 | 错误率<0.5%, P99<2s | 暂停分析 |
| Full | 100% | 持续 | 所有指标正常 | 自动告警 |

### 3.3 部署检查脚本

```bash
#!/bin/bash
# scripts/deployment-check.sh

set -e

DEPLOYMENT_NAME=$1
NAMESPACE=$2
THRESHOLD_ERROR_RATE=0.01
THRESHOLD_P99_LATENCY=2000

echo "检查部署: $DEPLOYMENT_NAME"

# 1. 检查Pod状态
kubectl wait --for=condition=available \
  deployment/$DEPLOYMENT_NAME \
  --timeout=300s \
  -n $NAMESPACE

# 2. 检查错误率
ERROR_RATE=$(kubectl exec -n $NAMESPACE \
  deploy/prometheus -- promtool query instant \
  'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])' \
  | tail -1 | awk '{print $2}')

if (( $(echo "$ERROR_RATE > $THRESHOLD_ERROR_RATE" | bc -l) )); then
  echo "错误率过高: $ERROR_RATE"
  exit 1
fi

# 3. 检查延迟
P99_LATENCY=$(kubectl exec -n $NAMESPACE \
  deploy/prometheus -- promtool query instant \
  'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))' \
  | tail -1 | awk '{print $2}')

if (( $(echo "$P99_LATENCY > $THRESHOLD_P99_LATENCY" | bc -l) )); then
  echo "P99延迟过高: ${P99_LATENCY}ms"
  exit 1
fi

echo "部署检查通过"
```

---

## 四、回滚方案

### 4.1 回滚触发条件

| 条件 | 阈值 | 处理方式 |
|------|------|----------|
| 错误率 | >5% | 立即回滚 |
| P99延迟 | >10s | 立即回滚 |
| LLM服务不可用 | >1分钟 | 立即回滚 |
| 核心功能异常 | - | 立即回滚 |
| 监控告警 | Critical | 立即回滚 |

### 4.2 回滚操作

```bash
#!/bin/bash
# scripts/rollback.sh

set -e

NAMESPACE=$1
DEPLOYMENT_NAME=$2

echo "开始回滚: $DEPLOYMENT_NAME"

# 1. 关闭新版本
kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE

# 2. 等待回滚完成
kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE

# 3. 验证服务可用
kubectl exec -n $NAMESPACE deploy/health-check -- curl -s http://localhost:8080/health

echo "回滚完成"
```

```powershell
# Windows PowerShell - 回滚脚本
param(
    [string]$Namespace = "production",
    [string]$DeploymentName = "backend"
)

Write-Host "开始回滚: $DeploymentName"

# 回滚
kubectl rollout undo deployment/$DeploymentName -n $Namespace

# 等待
kubectl rollout status deployment/$DeploymentName -n $Namespace --timeout=300s

# 验证
$health = kubectl exec -n $Namespace deploy/health-check -- curl -s http://localhost:8080/health
if ($health -match "healthy") {
    Write-Host "回滚成功" -ForegroundColor Green
} else {
    Write-Host "健康检查失败" -ForegroundColor Red
    exit 1
}
```

### 4.3 数据库回滚

```sql
-- migrations/rollback_001_add_legal_knowledge.sql

-- 仅用于紧急回滚
BEGIN;

-- 删除新增的表
DROP TABLE IF EXISTS legal_articles_history;
DROP TABLE IF EXISTS legal_interpretations_new;

-- 恢复原表
ALTER TABLE legal_articles RENAME TO legal_articles_backup_old;
ALTER TABLE legal_articles_backup RENAME TO legal_articles;

COMMIT;
```

---

## 五、监控告警配置

### 5.1 Prometheus告警规则

```yaml
# prometheus/alerts.yml

groups:
  - name: legal-llm-alerts
    rules:
      # LLM响应时间告警
      - alert: LLMResponseTimeHigh
        expr: histogram_quantile(0.99, rate(llm_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "LLM响应时间过高"
          description: "P99响应时间超过10秒，当前: {{ $value }}秒"

      # 本地模型命中率低
      - alert: LLMRouteLocalLow
        expr: rate(llm_route_local_total[1h]) / rate(llm_route_total[1h]) < 0.6
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "本地模型命中率低"
          description: "本地模型命中率低于60%，当前: {{ $value | humanizePercentage }}"

      # 法律检索准确率低
      - alert: LegalSearchAccuracyLow
        expr: legal_search_accuracy < 0.7
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "法律检索准确率低"
          description: "检索准确率低于70%，当前: {{ $value | humanizePercentage }}"

      # API成功率低
      - alert: APIErrorRateHigh
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API错误率过高"
          description: "错误率超过1%，当前: {{ $value | humanizePercentage }}"

      # 向量检索延迟高
      - alert: VectorSearchLatencyHigh
        expr: histogram_quantile(0.99, rate(vector_search_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "向量检索延迟高"
          description: "P99检索延迟超过1秒，当前: {{ $value }}秒"
```

### 5.2 Grafana仪表板

```json
{
  "dashboard": {
    "title": "法律案件追踪系统监控",
    "panels": [
      {
        "title": "LLM响应时间",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(llm_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.99, rate(llm_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "模型路由分布",
        "targets": [
          {
            "expr": "rate(llm_route_local_total[1h])",
            "legendFormat": "本地模型"
          },
          {
            "expr": "rate(llm_route_cloud_total[1h])",
            "legendFormat": "云端模型"
          }
        ]
      },
      {
        "title": "法律检索准确率",
        "targets": [
          {
            "expr": "legal_search_accuracy",
            "legendFormat": "准确率"
          }
        ]
      }
    ]
  }
}
```

### 5.3 关键指标汇总

| 指标 | 正常范围 | 告警阈值 | 严重阈值 | 采集间隔 |
|------|----------|----------|----------|----------|
| API成功率 | >99.5% | <99% | <95% | 1m |
| API响应时间P99 | <500ms | >1s | >3s | 1m |
| LLM响应(本地) | <2s | >5s | >10s | 5m |
| LLM响应(云端) | <5s | >10s | >30s | 5m |
| 本地路由命中率 | >80% | <60% | <40% | 1h |
| 法律检索准确率 | >85% | <70% | <50% | 1h |
| 向量检索延迟 | <500ms | >1s | >2s | 5m |
| 前端首屏加载 | <3s | >5s | >8s | 5m |
| 数据库连接池 | <80% | >90% | >95% | 1m |

---

## 六、数据库迁移策略

### 6.1 法律资料库PostgreSQL迁移

#### 阶段1: 准备

```sql
-- 创建迁移脚本
-- migrations/001_migrate_to_postgresql.sql

-- 1. 创建新表结构
CREATE TABLE IF NOT EXISTS legal_articles_pg (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content JSONB NOT NULL,
    category VARCHAR(100),
    effective_date DATE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建索引
CREATE INDEX idx_legal_articles_category ON legal_articles_pg(category);
CREATE INDEX idx_legal_articles_content ON legal_articles_pg USING GIN(content);
CREATE INDEX idx_legal_articles_metadata ON legal_articles_pg USING GIN(metadata);

-- 3. 创建更新触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_legal_articles_pg_updated_at
    BEFORE UPDATE ON legal_articles_pg
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 阶段2: 双写阶段

```python
# app/db/dual_writer.py

class DualWriter:
    """双写器 - 同时写入SQLite和PostgreSQL"""

    def __init__(self, sqlite_db, pg_db):
        self.sqlite = sqlite_db
        self.pg = pg_db

    async def write_article(self, article_data: dict) -> str:
        """写入法律条文 - 双写"""
        # 1. 写入SQLite (原始数据)
        sqlite_id = self.sqlite.insert('legal_articles', article_data)

        # 2. 写入PostgreSQL (新结构)
        pg_id = self.pg.execute('''
            INSERT INTO legal_articles_pg
            (id, title, content, category, effective_date, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            article_data['id'],
            article_data['title'],
            json.dumps(article_data['content']),
            article_data.get('category'),
            article_data.get('effective_date'),
            json.dumps(article_data.get('metadata', {}))
        ))

        # 3. 记录日志
        logger.info(f"Article dual-written: sqlite={sqlite_id}, pg={pg_id}")

        return sqlite_id

    async def read_article(self, article_id: str) -> dict:
        """读取法律条文 - 根据配置选择数据源"""
        if settings.USE_POSTGRESQL:
            return self.pg.fetch_one(
                'SELECT * FROM legal_articles_pg WHERE id = %s',
                (article_id,)
            )
        else:
            return self.sqlite.fetch_one(
                'SELECT * FROM legal_articles WHERE id = %s',
                (article_id,)
            )
```

#### 阶段3: 灰度切换

```python
# app/config/feature_flags.py

FEATURE_FLAGS = {
    'use_postgresql_reads': False,  # 初始为False
    'postgresql_read_percentage': 0,  # 0%
}

# 在nginx或API网关层实现灰度
# upstream backend {
#     server 127.0.0.1:8000 weight=10;  # SQLite (90%)
#     server 127.0.0.1:8001 weight=1;   # PostgreSQL (10%)
# }
```

#### 阶段4: 全量切换

```python
# 一旦PostgreSQL读取稳定100%，执行切换

FEATURE_FLAGS = {
    'use_postgresql_reads': True,
    'postgresql_read_percentage': 100,
}

# 停用双写
# 保留SQLite备份
```

### 6.2 回滚脚本

```sql
-- 回滚到SQLite

BEGIN;

-- 1. 停止应用写入
-- 确保应用已停机

-- 2. 从PostgreSQL导出数据
COPY legal_articles_pg TO '/tmp/legal_articles_backup.csv' CSV HEADER;

-- 3. 恢复到SQLite
-- 使用Python脚本导入

-- 4. 验证数据完整性
SELECT COUNT(*) FROM legal_articles;
-- 应与 PostgreSQL 中数据一致

COMMIT;
```

---

## 七、Docker配置

### 7.1 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 创建非root用户
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=${ENV:-development}
      - DB_HOST=${DB_HOST:-sqlite}
      - REDIS_HOST=redis
    depends_on:
      - redis
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend

volumes:
  redis_data:
```

---

*文档版本: v1.0*
*最后更新: 2026-04-02*
