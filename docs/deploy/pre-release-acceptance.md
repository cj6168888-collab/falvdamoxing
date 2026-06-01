# 部署前验收与发布清单

本文档用于当前 Docker 生产栈发布前收口。目标不是证明接口能启动，而是确认“博凯升华违背合作案”这类完整证据链案件在真实用户路径下可用。

## 一、发布结论口径

当前代码达到“可进入预生产/内网试用”的标准。

直接公开生产上线前必须额外完成：

- 配置真实域名和 HTTPS 证书。
- 确认 `.env.prod` 中所有密钥均为生产值，且未提交到代码仓库。
- 建立 PostgreSQL 备份和恢复演练。
- 明确日志、磁盘空间、容器健康和大模型调用失败告警。
- 选定真实试用账号和真实案件数据访问范围。

## 二、当前已验证基线

最近一次完整验收结果：

| 验收项 | 命令 | 结果 | 报告 |
| --- | --- | --- | --- |
| AI 真实功能审计 | `node scripts\bokai-function-audit.mjs --mode=ai --skip-browser --include-expensive --include-debate --timeout-ms=30000 --ai-timeout-ms=240000 --expensive-timeout-ms=900000 --request-delay-ms=600` | `PASS=30 WARN=0 FAIL=0` | `test_output/bokai-audit-2026-05-14T03-20-19-625Z/summary.md` |
| 数据/CRUD 生命周期审计 | `node scripts\bokai-function-audit.mjs --mode=data --skip-browser --timeout-ms=30000 --ai-timeout-ms=240000 --request-delay-ms=800` | `PASS=34 WARN=0 FAIL=0` | `test_output/bokai-audit-2026-05-14T04-07-12-609Z/summary.md` |
| 前端路由浏览器审计 | `node scripts\bokai-function-audit.mjs --mode=browser --timeout-ms=30000 --request-delay-ms=300` | `WARN=0 FAIL=0` | `test_output/bokai-audit-2026-05-14T04-23-24-876Z/summary.md` |

数据完整性基线：

- `case_id=3` 证据链：177 条。
- `case_id=3` 函件：64 封。
- 审计临时案件、审计临时函件、审计临时提醒、审计临时对抗分析残留：0。

已验证的关键法律 AI 工作底稿能力：

- 智能聊天全案分析和案件内问答。
- 智能助手上传后追问。
- 资深律师分析。
- 对方画像、证据攻防矩阵、场景预测、自动行动方案。
- 证据驱动分析。
- 起诉状、证据目录、智能文书生成。
- 庭审开场陈述、交叉询问、实时分析、陷阱识别、谈判脚本。
- 函件回复生成和回函 AI 分析。
- 报告快速分析和大案稳定报告生成。
- 执行申请书生成。
- 同步对抗全案分析。
- 真实 4 轮模拟辩论和继续辩论。

## 三、部署前阻断项

以下任一项未通过，不发布到公网生产：

- `scripts\production-preflight.ps1 -RequireExternalApis -RequireTls` 返回失败。
- `docker compose --env-file .env.prod -f docker-compose.prod.yml config --quiet` 返回失败。
- `docker compose --env-file .env.prod -f docker-compose.prod.yml --profile migrate run --rm migrate` 返回失败。
- `docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm app python -m app.db.migrate_all --check` 返回失败。
- `/health` 或 `/ready` 非 200。
- AI、Data、Browser 三类审计任一 `FAIL > 0`。
- 生产数据库没有发布前备份。
- `.env.prod` 中仍存在 `change_me`、`your_`、`example.com`、`your-domain.com`、`localhost` 生产 CORS。
- `config/nginx/ssl/fullchain.pem` 或 `config/nginx/ssl/privkey.pem` 缺失。

## 四、推荐发布流程

1. 备份数据库。

```powershell
powershell -ExecutionPolicy Bypass -File scripts\production-backup.ps1
```

2. 执行部署前检查。

```powershell
powershell -ExecutionPolicy Bypass -File scripts\production-preflight.ps1 -RequireExternalApis -RequireTls
```

3. 构建并迁移。

```powershell
docker compose --env-file .env.prod -f docker-compose.prod.yml build app frontend
docker compose --env-file .env.prod -f docker-compose.prod.yml --profile migrate run --rm migrate
docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm app python -m app.db.migrate_all --check
```

4. 启动生产栈。

```powershell
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

5. 运行验收审计。

```powershell
powershell -ExecutionPolicy Bypass -File scripts\production-release-gate.ps1
```

也可以分开运行：

```powershell
node scripts\bokai-function-audit.mjs --mode=data --skip-browser --timeout-ms=30000 --ai-timeout-ms=240000 --request-delay-ms=800
node scripts\bokai-function-audit.mjs --mode=ai --skip-browser --include-expensive --include-debate --timeout-ms=30000 --ai-timeout-ms=240000 --expensive-timeout-ms=900000 --request-delay-ms=600
node scripts\bokai-function-audit.mjs --mode=browser --timeout-ms=30000 --request-delay-ms=300
```

6. 做审计残留核对。

```powershell
docker exec legal-postgres-prod psql -U legal_user -d legal_db -t -A -c "select 'case3_evidence', count(*) from evidence_items_v2 where case_id=3 union all select 'letters', count(*) from letters where case_id=3 union all select 'audit_temp_cases', count(*) from cases where title like 'Bokai Audit Temp Case %' union all select 'audit_leftovers', (select count(*) from reminders where title like 'Bokai Audit Reminder %') + (select count(*) from letters where case_id=3 and title like '%审计临时%') + (select count(*) from adversarial_analyses where case_id=3 and title like '对抗性分析报告 - %') + (select count(*) from legal_deadlines where case_id=3 and deadline_name like 'Bokai Audit Deadline %');"
```

预期：

- `case3_evidence|177`
- `letters|64`
- `audit_temp_cases|0`
- `audit_leftovers|0`

## 五、人工验收脚本

真实用户验收至少走完以下路径：

1. 登录并进入案件 `博凯升华违背合作案`。
2. 打开证据页，确认 177 条证据可检索、可查看。
3. 打开智能聊天，询问“请用证据链总结本案诉讼策略”，检查是否引用博凯升华、陈靖、佛山吉麟、雷天乾、工资社保、保证金、停业责任等案件要素。
4. 生成案件分析报告，检查报告包含《民法典》《公司法》《民事诉讼法》和证据规则方向。
5. 生成对抗全案分析，检查不是泛泛摘要，而是包含对方抗辩、我方攻防矩阵、案件走向、行动方案。
6. 生成庭审交叉询问，检查问题绑定博凯升华案证据和主体。
7. 运行 4 轮模拟辩论，检查确有多轮攻防，不是固定占位文本。
8. 生成执行申请书，检查不会出现“审计临时法院”等测试污染。
9. 生成函件回复和回函分析，检查不虚构案号、法院或未经核验案例。
10. 检查前端路由无白屏、无明显空页面。

## 六、回滚标准

发布后出现以下情况应回滚：

- `/ready` 连续 3 分钟失败。
- 主要 AI 功能返回 500 或超时比例明显升高。
- 报告生成、模拟辩论、证据链读取任一核心路径不可用。
- 数据库迁移后出现表结构缺失或核心数据数量异常。
- 发现用户数据串租户、越权访问或审计临时数据污染正式案件。

回滚优先顺序：

1. 停止新流量或切回旧 Nginx upstream。
2. 回滚应用镜像。
3. 若数据库迁移造成不可逆污染，使用发布前备份恢复到新库再切换。
4. 保留失败版本日志和审计输出，不覆盖现场。

数据库恢复工具：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\production-restore.ps1 -BackupFile backups\legal_db_YYYYMMDD-HHMMSS.dump -ConfirmRestore
```

恢复会删除并重建目标数据库，只能在确认回滚窗口和备份文件后执行。

## 七、暂缓事项

以下不作为本次上线阻断项，但应进入后续开发计划：

- 开源法律大模型本地化整合暂缓。
- SaaS 多租户商业化部署和计费暂缓。
- OCR/ChromaDB/本地向量库属于可选增强能力，当前核心案件流不依赖它们。
- 公网生产前仍需真实短信供应商、监控告警、日志留存策略和安全扫描。
