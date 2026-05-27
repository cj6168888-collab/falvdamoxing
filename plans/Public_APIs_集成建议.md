# 法律案件追踪系统 — Public APIs 集成建议

> 基于 [public-apis/public-apis](https://github.com/public-apis/public-apis) 项目的免费开源 API 分析
> 筛选出可增强法律案件追踪系统能力的 API

---

## 🎯 高价值 API 推荐（按优先级排序）

### 1. 企业信息核查增强

| API | 用途 | 免费额度 | 集成价值 |
|-----|------|---------|---------|
| **[Clearbit Logo](https://clearbit.com/docs#logo-api)** | 获取公司 Logo | 免费 | ⭐⭐⭐⭐⭐ 当事人企业信息可视化 |
| **[ORB Intelligence](https://api.orb-intelligence.com/docs/)** | 公司详细信息查询 | 免费额度 | ⭐⭐⭐⭐⭐ 企业当事人背景调查 |
| **[Domainsdb.info](https://domainsdb.info/)** | 域名注册信息查询 | 免费 | ⭐⭐⭐ 企业域名关联调查 |

**集成场景：**
- 当事人管理模块：输入企业名称 → 自动获取 Logo、工商信息、关联域名
- 证据管理：企业网站截图存证 → 自动获取企业标识
- 报告生成：企业当事人信息自动填充

---

### 2. 电话号码验证

| API | 用途 | 免费额度 | 集成价值 |
|-----|------|---------|---------|
| **[Numverify](https://numverify.com)** | 全球电话号码验证与查询 | 100 次/月 | ⭐⭐⭐⭐⭐ 当事人电话验证 |
| **[Phone Validation (Abstract API)](https://www.abstractapi.com/phone-validation-api)** | 电话号码验证 | 免费额度 | ⭐⭐⭐⭐ 电话号码格式校验 |
| **[Cloudmersive Validate](https://cloudmersive.com/phone-number-validation-API)** | 国际电话号码验证 | 免费额度 | ⭐⭐⭐ 跨国案件电话验证 |

**集成场景：**
- 新建案件：输入当事人电话 → 自动验证有效性 + 识别运营商 + 归属地
- 当事人管理：批量验证电话号码 → 标记无效号码
- 函件管理：发送短信通知前验证号码

---

### 3. 邮箱验证

| API | 用途 | 免费额度 | 集成价值 |
|-----|------|---------|---------|
| **[MailboxValidator](https://www.mailboxvalidator.com/api-email-free)** | 邮箱地址验证 | 300 次/月 | ⭐⭐⭐⭐ 当事人邮箱验证 |
| **[Email Validation (Abstract API)](https://www.abstractapi.com/email-verification-validation-api)** | 邮箱验证 | 免费额度 | ⭐⭐⭐⭐ 邮箱有效性检查 |
| **[Mailcheck.ai](https://www.mailcheck.ai/)** | 检测临时/一次性邮箱 | 免费 | ⭐⭐⭐ 防止虚假邮箱 |

**集成场景：**
- 当事人管理：输入邮箱 → 验证有效性 + 检测临时邮箱
- 函件管理：发送邮件前验证邮箱 → 提高送达率
- 系统注册：防止用户使用一次性邮箱注册

---

### 4. 地址验证与地理编码

| API | 用途 | 免费额度 | 集成价值 |
|-----|------|---------|---------|
| **[Lob.com](https://lob.com/)** | 美国地址验证 | 免费额度 | ⭐⭐⭐ 涉外案件地址验证 |
| **[IPstack](https://ipstack.com)** | IP 地理位置定位 | 10,000 次/月 | ⭐⭐⭐⭐ 电子证据 IP 定位 |
| **[ipapi.com](https://ipapi.com)** | 实时地理位置查询 | 免费额度 | ⭐⭐⭐⭐ IP 地址溯源 |

**集成场景：**
- 证据管理：电子证据 IP 地址 → 自动定位地理位置
- 当事人管理：地址标准化验证
- 出庭抗辩：电子证据来源地分析

---

### 5. 文档处理与转换

| API | 用途 | 免费额度 | 集成价值 |
|-----|------|---------|---------|
| **[apilayer pdflayer](https://pdflayer.com)** | HTML/URL 转 PDF | 免费额度 | ⭐⭐⭐⭐⭐ 网页证据固定存证 |
| **[CloudConvert](https://cloudconvert.com/api)** | 文件格式转换 | 25 次/天 | ⭐⭐⭐⭐ 证据文件格式统一 |
| **[PDFEndpoint](https://pdfendpoint.com)** | HTML/URL 转 PDF/PNG | 免费 | ⭐⭐⭐⭐ 网页截图存证 |

**集成场景：**
- 证据管理：网页证据 → 自动转换为 PDF 存证
- 导出功能：文书导出为 PDF
- 证据转换：各种格式证据 → 统一 PDF 格式

---

### 6. 文本分析与自然语言处理

| API | 用途 | 免费额度 | 集成价值 |
|-----|------|---------|---------|
| **[Aylien Text Analysis](https://docs.aylien.com/textapi/)** | 文本分析、信息提取 | 1,000 次/天 | ⭐⭐⭐⭐ 合同文本自动分析 |
| **[Cloudmersive NLP](https://www.cloudmersive.com/nlp-api)** | 自然语言处理 | 免费额度 | ⭐⭐⭐⭐ 法律文书语义分析 |
| **[languagelayer](https://languagelayer.com/)** | 语言检测（173 种语言） | 免费额度 | ⭐⭐⭐ 涉外案件语言识别 |

**集成场景：**
- 证据管理：上传文档 → 自动检测语言 + 提取关键信息
- 文书生成：合同文本分析 → 自动识别关键条款
- 对话 V2：多语言当事人交流 → 自动识别语言

---

### 7. 日历与节假日

| API | 用途 | 免费额度 | 集成价值 |
|-----|------|---------|---------|
| **[Calendarific](https://calendarific.com/)** | 全球节假日查询 | 1,000 次/月 | ⭐⭐⭐⭐ 期限计算考虑节假日 |
| **[Nager.Date](https://date.nager.at)** | 全球公共假日 API | 完全免费 | ⭐⭐⭐⭐⭐ 期限计算节假日排除 |

**集成场景：**
- 时间把控：期限计算 → 自动排除节假日
- 出庭抗辩：开庭日期选择 → 避开节假日
- 提醒系统：提醒时间调整 → 考虑节假日

---

### 8. 汇率与货币

| API | 用途 | 免费额度 | 集成价值 |
|-----|------|---------|---------|
| **[Fixer](https://fixer.io)** | 外汇汇率 API | 100 次/月 | ⭐⭐⭐ 涉外案件金额换算 |
| **[Exchangerate Host](https://exchangerate.host)** | 实时汇率 | 免费 | ⭐⭐⭐ 多币种案件财务 |

**集成场景：**
- 案件财务：涉外案件 → 自动汇率换算
- 报告生成：多币种金额统一显示
- 执行跟踪：跨境执行金额换算

---

### 9. 天气数据

| API | 用途 | 免费额度 | 集成价值 |
|-----|------|---------|---------|
| **[Open-Meteo](https://open-meteo.com)** | 天气预报（免费无限制） | 完全免费 | ⭐⭐⭐ 出庭天气参考 |

**集成场景：**
- 出庭抗辩：开庭日期 → 显示天气预报
- 证据管理：天气相关证据（如交通事故）→ 获取历史天气数据

---

### 10. 安全与反欺诈

| API | 用途 | 免费额度 | 集成价值 |
|-----|------|---------|---------|
| **[AbuseIPDB](https://docs.abuseipdb.com/)** | IP 信誉检查 | 1,000 次/天 | ⭐⭐⭐ 电子证据 IP 信誉 |
| **[NoPhishy](https://rapidapi.com/Amiichu/api/exerra-phishing-check/)** | 钓鱼链接检测 | 免费 | ⭐⭐⭐ 证据链接安全检查 |
| **[URLScan.io](https://urlscan.io/about-api/)** | URL 安全扫描 | 免费 | ⭐⭐⭐⭐ 证据链接安全分析 |

**集成场景：**
- 证据管理：电子证据中的链接 → 安全检查
- 系统安全：用户输入 URL → 钓鱼检测
- 证据分析：可疑 IP 地址 → 信誉检查

---

## 📊 集成优先级矩阵

| 优先级 | API 类别 | 推荐 API | 预计开发时间 | 价值评分 |
|--------|---------|---------|------------|---------|
| **P0 - 立即集成** | 企业信息核查 | Clearbit Logo, ORB Intelligence | 1-2 天 | ⭐⭐⭐⭐⭐ |
| **P0 - 立即集成** | 电话/邮箱验证 | Numverify, MailboxValidator | 1 天 | ⭐⭐⭐⭐⭐ |
| **P0 - 立即集成** | 节假日 API | Nager.Date | 0.5 天 | ⭐⭐⭐⭐⭐ |
| **P1 - 近期集成** | 文档转换 | pdflayer, CloudConvert | 2-3 天 | ⭐⭐⭐⭐ |
| **P1 - 近期集成** | IP 地理定位 | IPstack, ipapi.com | 1-2 天 | ⭐⭐⭐⭐ |
| **P1 - 近期集成** | 文本分析 | Aylien, Cloudmersive NLP | 2-3 天 | ⭐⭐⭐⭐ |
| **P2 - 后续集成** | URL 安全扫描 | URLScan.io, NoPhishy | 1-2 天 | ⭐⭐⭐ |
| **P2 - 后续集成** | 汇率 API | Fixer, Exchangerate Host | 1 天 | ⭐⭐⭐ |
| **P3 - 可选集成** | 天气 API | Open-Meteo | 1 天 | ⭐⭐ |
| **P3 - 可选集成** | 安全 API | AbuseIPDB | 1 天 | ⭐⭐ |

---

## 🔧 集成架构建议

```
frontend/
├── src/
│   ├── api/
│   │   ├── external/                    # 第三方 API 客户端
│   │   │   ├── clearbit.api.ts         # Clearbit Logo API
│   │   │   ├── numverify.api.ts        # 电话验证 API
│   │   │   ├── mailboxvalidator.api.ts # 邮箱验证 API
│   │   │   ├── nager-date.api.ts       # 节假日 API
│   │   │   ├── pdflayer.api.ts         # PDF 转换 API
│   │   │   ├── ipstack.api.ts          # IP 地理定位
│   │   │   ├── aylien.api.ts           # 文本分析 API
│   │   │   └── urlscan.api.ts          # URL 安全扫描
│   │   └── ...
│   ├── hooks/
│   │   ├── use-company-info.ts         # 企业信息查询 Hook
│   │   ├── use-phone-validation.ts     # 电话验证 Hook
│   │   ├── use-email-validation.ts     # 邮箱验证 Hook
│   │   ├── use-holiday-calendar.ts     # 节假日查询 Hook
│   │   └── use-document-conversion.ts  # 文档转换 Hook
│   └── lib/
│       └── external-api-config.ts      # 第三方 API 配置
```

---

## 💰 成本估算

| API | 免费额度 | 超出费用 | 月预估用量 | 月预估费用 |
|-----|---------|---------|-----------|-----------|
| Clearbit Logo | 无限 | - | 500 次 | $0 |
| Numverify | 100 次/月 | $29/月 | 200 次 | $0-29 |
| MailboxValidator | 300 次/月 | $10/月 | 500 次 | $0-10 |
| Nager.Date | 无限 | - | 1,000 次 | $0 |
| pdflayer | 100 次/月 | $19.99/月 | 200 次 | $0-20 |
| IPstack | 10,000 次/月 | $29/月 | 5,000 次 | $0 |
| Aylien | 1,000 次/天 | $199/月 | 500 次 | $0 |
| **总计** | | | | **$0-59/月** |

---

## ✅ 实施建议

### 第一阶段（第 1 周）
1. 集成 Nager.Date 节假日 API（最简单，立竿见影）
2. 集成 Numverify 电话验证 API
3. 集成 MailboxValidator 邮箱验证 API
4. 集成 Clearbit Logo API

### 第二阶段（第 2-3 周）
1. 集成 pdflayer 文档转换 API
2. 集成 IPstack IP 地理定位
3. 集成 Aylien 文本分析 API

### 第三阶段（第 4 周+）
1. 集成 URLScan.io 安全扫描
2. 集成汇率 API
3. 集成天气 API（可选）

---

*分析完成时间: 2026-04-02*
*数据来源: public-apis/public-apis GitHub 仓库*
