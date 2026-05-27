# 真实短信和 API Key 验收流程

更新日期：2026-05-17

本流程只记录路径和命令，不记录任何密钥值。

当前状态：

- `data/config/api-keys.env` 已由本机“摘要”文档导入 DashScope key，并已推送到 staging 运行时配置。
- `.env.sms.local` 已由桌面短信配置文件生成；2026-05-17 已再次从 `C:\Users\LENOVO\Desktop\aliyun-sms.env` 刷新并强制重建阿里云短信适配器，overlay 已启动并通过健康检查。
- 2026-05-17 使用测试手机号 `130****4999` 触发注册验证码时，应用已请求到阿里云适配器，但阿里云返回 `isv.BUSINESS_LIMIT_CONTROL`，本次真实短信闭环被供应商业务限流/风控阻断，未进入验证码校验步骤。
- 真实短信注册/找回的最后一步还需要专用测试手机号和收到的验证码；运行该步骤会实际发送短信并可能产生费用。

## 1. 固化测试环境

本地运行：

```powershell
C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install -r requirements-dev.txt
C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest
```

容器运行：

```powershell
docker compose -f docker-compose.test.yml build test
docker compose -f docker-compose.test.yml run --rm test
```

## 2. 导入 API Key 摘要

默认读取 `C:\Users\LENOVO\Documents\摘要.txt`，写入 `data/config/api-keys.env`。该文件被 `.gitignore` 忽略。

```powershell
python scripts/import_runtime_api_keys.py --dry-run
python scripts/import_runtime_api_keys.py
```

脚本支持 `DASHSCOPE_API_KEY=value`、`DASHSCOPE_API_KEY: value`，也兼容本机摘要文档中“通义千问”下一行是 DashScope key 的格式。脚本只打印 key 名和长度，不打印密钥值。

推送到正在运行的 staging：

```powershell
python scripts/push_runtime_api_keys.py --base-url http://127.0.0.1:8080 --source data/config/api-keys.env --username loadtest-admin --password loadtest-password-123456
```

## 3. 准备阿里云短信配置

桌面短信配置文件路径：

```text
C:\Users\LENOVO\Desktop\aliyun-sms.env
```

将该文件复制为仓库本地私有文件：

```powershell
Copy-Item C:\Users\LENOVO\Desktop\aliyun-sms.env .env.sms.local
```

`.env.sms.local` 被 `.gitignore` 忽略，不提交。它至少需要包含：

```text
ALIYUN_SMS_ACCESS_KEY_ID=...
ALIYUN_SMS_ACCESS_KEY_SECRET=...
ALIYUN_SMS_SIGN_NAME=...
ALIYUN_SMS_TEMPLATE_CODE=...
ALIYUN_SMS_REGION_ID=cn-hangzhou
```

可选项：

```text
ALIYUN_SMS_REGISTER_TEMPLATE_CODE=...
ALIYUN_SMS_PASSWORD_RESET_TEMPLATE_CODE=...
ALIYUN_SMS_TEMPLATE_PARAM_NAME=code
ALIYUN_SMS_DRY_RUN=0
```

## 4. 使用阿里云短信适配器替换 staging mock

```powershell
$env:COMPOSE_BAKE='false'
$env:DOCKER_BUILDKIT='0'
docker compose --env-file .env.staging.example -f docker-compose.staging.yml -f docker-compose.staging.aliyun-sms.yml up -d sms-mock app nginx
```

验证适配器健康：

```powershell
docker compose --env-file .env.staging.example -f docker-compose.staging.yml -f docker-compose.staging.aliyun-sms.yml exec -T sms-mock wget -qO- http://127.0.0.1:8088/health
```

## 5. 跑真实短信注册和找回验收

准备一台专用测试手机号。不要使用客户手机号。

```powershell
python scripts/smoke_real_sms_auth.py --base-url http://127.0.0.1:8080 --phone 13xxxxxxxxx --prompt-codes
```

脚本会：

1. 触发注册验证码。
2. 等操作者输入手机收到的验证码。
3. 完成手机号注册并登录。
4. 触发找回密码验证码。
5. 等操作者输入手机收到的验证码。
6. 重置密码，确认旧密码失败、新密码成功。

若只验收已注册手机号的找回密码：

```powershell
python scripts/smoke_real_sms_auth.py --base-url http://127.0.0.1:8080 --phone 13xxxxxxxxx --mode password-reset --password 当前旧密码 --prompt-codes
```

## 6. 复跑真实 AI 审计

确认 `data/config/api-keys.env` 已包含 DashScope key 后，重启 app 或通过配置 API 保存 key，再运行：

```powershell
node scripts\bokai-function-audit.mjs --mode=ai --skip-browser --include-expensive --include-debate --timeout-ms=30000 --ai-timeout-ms=240000 --expensive-timeout-ms=900000 --request-delay-ms=600
```

验收通过标准：

- `FAIL=0`
- 关键 AI 输出非空、非模板错误、没有跨案件/跨租户内容
- 报告中保留 `summary.md`、`manifest.json` 和 `ai-outputs/`
