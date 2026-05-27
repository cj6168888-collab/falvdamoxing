#!/usr/bin/env node
import { createRequire } from 'node:module';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const frontendRequire = createRequire(resolve(repoRoot, 'frontend', 'package.json'));
const execFileAsync = promisify(execFile);

const DEFAULT_BASE_URL = 'http://localhost';
const DEFAULT_CASE_ID = 3;
const DEFAULT_TIMEOUT_MS = 20000;
const DEFAULT_AI_TIMEOUT_MS = 180000;
const DEFAULT_EXPENSIVE_TIMEOUT_MS = 900000;
const BROWSER_TIMEOUT_MS = 45000;

const CASE_SIGNALS = [
  '博凯升华',
  '博凯健康',
  '佛山吉麟',
  '陈靖',
  '雷天乾',
  '许阳',
  '出资',
  '股东',
  '停业',
  '审计',
  '工资',
  '保证金',
  '合作协议',
  '信息服务',
];

const LEGAL_SIGNALS = [
  '民法典',
  '公司法',
  '民事诉讼法',
  '劳动合同法',
  '劳动法',
  '最高人民法院',
  '司法解释',
  '举证责任',
];

const EVIDENCE_SIGNAL_RE = /(证据\s*\d+|证据编号|证据名称|附件\s*\d+|evidence|display_name|original_filename|《[^》]{2,80}》)/i;
const ERROR_RE = /(AI 服务暂时不可用|请求出错|请先配置|错误：|Traceback|Internal Server Error|Not Found|Method Not Allowed|Bad Gateway|Gateway Timeout)/;
const OVERCONFIDENT_RE = /(必胜|稳赢|一定胜诉|必然胜诉|百分之百|100%胜诉|毫无风险|无可辩驳|铁证如山|必然构成犯罪)/;
const FABRICATED_CASE_RE = /（20\d{2}）(?:(?:最高法|[\u4e00-\u9fa5]{1,8})(?:民|商|执|行|刑|知|申|终|再|初|辖)[^\s，。；：、\n]{0,25}|[\u4e00-\u9fa5]{1,4}\d{2}(?:民|商|执|行|刑|知|申|终|再|初|辖)[^\s，。；：、\n]{0,25})(?:\d+|X{2,}|x{2,})号|指导案例\d+号|典型案例[-\d]+/g;
const MOJIBAKE_RE = /([ÃÂ�]{1,}|[åæçèä]{2,}|\\u00[a-f0-9]{2})/i;

function parseArgs(argv) {
  const options = {
    baseUrl: process.env.BOKAI_AUDIT_BASE_URL || DEFAULT_BASE_URL,
    caseId: Number(process.env.BOKAI_AUDIT_CASE_ID || DEFAULT_CASE_ID),
    outputDir: process.env.BOKAI_AUDIT_OUTPUT_DIR || '',
    username: process.env.BOKAI_AUDIT_USERNAME || '',
    password: process.env.BOKAI_AUDIT_PASSWORD || '',
    mode: process.env.BOKAI_AUDIT_MODE || 'full',
    includeExpensive: flagFromEnv('BOKAI_AUDIT_INCLUDE_EXPENSIVE'),
    includeDebate: flagFromEnv('BOKAI_AUDIT_INCLUDE_DEBATE'),
    skipBrowser: flagFromEnv('BOKAI_AUDIT_SKIP_BROWSER'),
    timeoutMs: numberFromEnv('BOKAI_AUDIT_TIMEOUT_MS', DEFAULT_TIMEOUT_MS),
    aiTimeoutMs: numberFromEnv('BOKAI_AUDIT_AI_TIMEOUT_MS', DEFAULT_AI_TIMEOUT_MS),
    expensiveTimeoutMs: numberFromEnv('BOKAI_AUDIT_EXPENSIVE_TIMEOUT_MS', DEFAULT_EXPENSIVE_TIMEOUT_MS),
    requestDelayMs: numberFromEnv('BOKAI_AUDIT_REQUEST_DELAY_MS', 1100),
  };

  for (const arg of argv) {
    if (arg === '--include-expensive') options.includeExpensive = true;
    else if (arg === '--include-debate') options.includeDebate = true;
    else if (arg === '--skip-browser') options.skipBrowser = true;
    else if (arg.startsWith('--base-url=')) options.baseUrl = arg.slice('--base-url='.length);
    else if (arg.startsWith('--case-id=')) options.caseId = Number(arg.slice('--case-id='.length));
    else if (arg.startsWith('--output-dir=')) options.outputDir = arg.slice('--output-dir='.length);
    else if (arg.startsWith('--username=')) options.username = arg.slice('--username='.length);
    else if (arg.startsWith('--password=')) options.password = arg.slice('--password='.length);
    else if (arg.startsWith('--mode=')) options.mode = arg.slice('--mode='.length);
    else if (arg.startsWith('--timeout-ms=')) options.timeoutMs = Number(arg.slice('--timeout-ms='.length));
    else if (arg.startsWith('--ai-timeout-ms=')) options.aiTimeoutMs = Number(arg.slice('--ai-timeout-ms='.length));
    else if (arg.startsWith('--expensive-timeout-ms=')) options.expensiveTimeoutMs = Number(arg.slice('--expensive-timeout-ms='.length));
    else if (arg.startsWith('--request-delay-ms=')) options.requestDelayMs = Number(arg.slice('--request-delay-ms='.length));
    else if (arg === '--help' || arg === '-h') {
      printUsage();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  options.baseUrl = options.baseUrl.replace(/\/+$/, '');
  if (!Number.isFinite(options.caseId) || options.caseId <= 0) {
    throw new Error('case id must be a positive number');
  }
  if (!['full', 'data', 'ai', 'browser'].includes(options.mode)) {
    throw new Error('mode must be one of: full, data, ai, browser');
  }
  return options;
}

function flagFromEnv(name) {
  return ['1', 'true', 'yes', 'on'].includes(String(process.env[name] || '').toLowerCase());
}

function numberFromEnv(name, fallback) {
  const value = Number(process.env[name] || fallback);
  return Number.isFinite(value) ? value : fallback;
}

function printUsage() {
  console.log(`Bokai full-function audit

Usage:
  node scripts/bokai-function-audit.mjs [options]

Options:
  --base-url=http://localhost
  --case-id=3
  --mode=full|data|ai|browser
  --include-expensive          Run long LLM/report/senior analysis endpoints
  --include-debate             Run real multi-round simulated debate
  --skip-browser               Skip frontend route walkthrough
  --ai-timeout-ms=180000
  --expensive-timeout-ms=900000
  --request-delay-ms=1100      Delay between API requests to respect production rate limits
`);
}

const options = parseArgs(process.argv.slice(2));
const runId = new Date().toISOString().replace(/[:.]/g, '-');
const outputDir = resolve(options.outputDir || join(repoRoot, 'test_output', `bokai-audit-${runId}`));
const artifactsDir = join(outputDir, 'artifacts');
const aiDir = join(outputDir, 'ai-outputs');
const browserDir = join(outputDir, 'browser');

const records = [];
const defects = [];
const coveredOperations = new Set();
let openapiPaths = {};
let lastRequestAt = 0;
let defaultAuthToken = '';

function log(status, name, detail = '') {
  const prefix = status.padEnd(4);
  console.log(`${prefix} ${name}${detail ? ` - ${detail}` : ''}`);
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function slug(input) {
  return String(input)
    .replace(/[^a-zA-Z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 120) || 'artifact';
}

function shortJson(value, max = 320) {
  const text = typeof value === 'string' ? value : JSON.stringify(value);
  if (!text) return '';
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

function formatError(error) {
  if (error instanceof Error) return error.message;
  return String(error);
}

function recordDefect(step, severity, message, evidence = '') {
  defects.push({ step, severity, message, evidence });
}

async function writeJson(filePath, value) {
  await writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

async function request(path, init = {}) {
  const {
    method = 'GET',
    body,
    expected = [200],
    timeoutMs = options.timeoutMs,
    token,
    headers = {},
    skipBody = false,
  } = init;

  const url = `${options.baseUrl}${path}`;
  const effectiveToken = token || defaultAuthToken;
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await waitForRateSlot(path);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
    const response = await fetch(url, {
      method,
      headers: {
        Accept: 'application/json',
        ...(body === undefined || isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...(effectiveToken ? { Authorization: `Bearer ${effectiveToken}` } : {}),
        ...headers,
      },
      body: body === undefined ? undefined : (isFormData ? body : JSON.stringify(body)),
      signal: controller.signal,
    });
    const text = skipBody ? '' : await response.text();
    const data = parseJson(text);
    if (response.status === 429 && !expected.includes(429) && attempt < 2) {
      const waitMs = 61000;
      console.log(`INFO rate-limit-backoff - ${method} ${path} returned 429; waiting ${waitMs}ms`);
      clearTimeout(timeout);
      await sleep(waitMs);
      continue;
    }
    if (!expected.includes(response.status)) {
      throw new Error(`${method} ${path} returned ${response.status}: ${shortJson(data ?? text)}`);
    }
    coveredOperations.add(`${method.toUpperCase()} ${pathToOpenapiShape(path)}`);
    return { response, data, text, url };
    } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`${method} ${path} timed out after ${timeoutMs}ms`);
    }
    throw error;
    } finally {
    clearTimeout(timeout);
    }
  }
  throw new Error(`${method} ${path} failed after rate-limit retries`);
}

async function waitForRateSlot(path) {
  if (path === '/openapi.json' || path === '/health' || path === '/ready') return;
  const delay = Math.max(0, Number(options.requestDelayMs) || 0);
  const elapsed = Date.now() - lastRequestAt;
  if (elapsed < delay) {
    await sleep(delay - elapsed);
  }
  lastRequestAt = Date.now();
}

function parseJson(text) {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function pathToOpenapiShape(path) {
  const clean = path.split('?')[0];
  const candidates = Object.keys(openapiPaths);
  const exact = candidates.find((candidate) => candidate === clean);
  if (exact) return exact;
  const matched = candidates.find((candidate) => {
    const re = new RegExp(`^${candidate.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\\\{[^}]+\\\}/g, '[^/]+')}$`);
    return re.test(clean);
  });
  return matched || clean;
}

async function step(name, category, fn, optionsForStep = {}) {
  const startedAt = Date.now();
  const record = {
    name,
    category,
    status: 'PASS',
    started_at: new Date(startedAt).toISOString(),
    duration_ms: 0,
    detail: '',
    warnings: [],
    artifact: null,
  };
  try {
    const result = await fn();
    const payload = result?.payload ?? result;
    record.detail = result?.detail || describePayload(payload);
    if (result?.warnings) record.warnings.push(...result.warnings);
    if (payload !== undefined) {
      const file = join(artifactsDir, `${slug(name)}.json`);
      await writeJson(file, payload);
      record.artifact = file;
    }
    if (record.warnings.length > 0) {
      record.status = optionsForStep.warningAsPass ? 'PASS' : 'WARN';
      for (const warning of record.warnings) recordDefect(name, 'P2', warning);
    }
    log(record.status, name, record.detail);
  } catch (error) {
    record.status = 'FAIL';
    record.detail = formatError(error);
    recordDefect(name, 'P1', record.detail);
    log('FAIL', name, record.detail);
  } finally {
    record.duration_ms = Date.now() - startedAt;
    records.push(record);
  }
  return record;
}

async function aiStep(name, category, requestFn, assessment = {}) {
  return step(name, category, async () => {
    const result = await requestFn();
    const payload = result?.data ?? result;
    const text = extractMainText(payload);
    const analysis = assessAiText(name, text, assessment);
    const mdFile = join(aiDir, `${slug(name)}.md`);
    await writeFile(mdFile, `# ${name}\n\n${text || '(empty output)'}\n`, 'utf8');
    return {
      payload: {
        response: payload,
        quality_review: analysis,
        saved_markdown: mdFile,
      },
      detail: `chars=${text.length} quality=${analysis.score}/100 warnings=${analysis.warnings.length}`,
      warnings: analysis.warnings,
    };
  }, { warningAsPass: false });
}

function describePayload(payload) {
  if (payload === undefined || payload === null) return '';
  if (Array.isArray(payload)) return `items=${payload.length}`;
  if (typeof payload === 'object') {
    if (payload.id) return `id=${payload.id}`;
    if (payload.case_id && payload.total !== undefined) return `case_id=${payload.case_id} total=${payload.total}`;
    if (payload.total !== undefined) return `total=${payload.total}`;
    if (payload.status) return `status=${payload.status}`;
    if (payload.success !== undefined) return `success=${payload.success}`;
  }
  return shortJson(payload);
}

function extractMainText(payload) {
  if (payload == null) return '';
  if (typeof payload === 'string') return payload;
  const preferredKeys = [
    'response',
    'answer',
    'content',
    'analysis',
    'analysis_result',
    'result',
    'report',
    'strategy',
    'document',
    'petition',
    'text',
    'message',
  ];
  const parts = [];
  collectPreferredStrings(payload, preferredKeys, parts, new Set());
  if (parts.join('').length < 200) collectAllStrings(payload, parts, new Set());
  return [...new Set(parts.map((part) => part.trim()).filter(Boolean))].join('\n\n').slice(0, 240000);
}

function collectPreferredStrings(value, keys, parts, seen) {
  if (!value || typeof value !== 'object') return;
  if (seen.has(value)) return;
  seen.add(value);
  for (const key of keys) {
    const item = value[key];
    if (typeof item === 'string') parts.push(item);
    else if (item && typeof item === 'object') collectAllStrings(item, parts, seen);
  }
  for (const item of Object.values(value)) {
    if (item && typeof item === 'object') collectPreferredStrings(item, keys, parts, seen);
  }
}

function collectAllStrings(value, parts, seen) {
  if (value == null) return;
  if (typeof value === 'string') {
    if (value.length > 8) parts.push(value);
    return;
  }
  if (typeof value !== 'object') return;
  if (seen.has(value)) return;
  seen.add(value);
  if (Array.isArray(value)) {
    for (const item of value.slice(0, 200)) collectAllStrings(item, parts, seen);
    return;
  }
  for (const item of Object.values(value)) collectAllStrings(item, parts, seen);
}

function assessAiText(name, text, requirements) {
  const warnings = [];
  let score = 100;
  const minChars = requirements.minChars ?? 600;

  if (!text || text.trim().length < 20) {
    warnings.push('AI 输出为空或近似为空。');
    score -= 45;
  }
  if (ERROR_RE.test(text)) {
    warnings.push('AI 输出包含服务错误、配置错误或异常信息。');
    score -= 45;
  }
  if (text.length < minChars) {
    warnings.push(`AI 输出过短，无法满足深度审查要求：${text.length}/${minChars} 字符。`);
    score -= 18;
  }
  if (requirements.caseSpecific !== false) {
    const signalHits = CASE_SIGNALS.filter((signal) => text.includes(signal));
    if (signalHits.length < 3) {
      warnings.push(`AI 输出与博凯升华案绑定不足，只命中 ${signalHits.length} 个案件特征。`);
      score -= 16;
    }
  }
  if (requirements.evidenceRefs !== false && !EVIDENCE_SIGNAL_RE.test(text)) {
    warnings.push('AI 输出未清楚引用证据编号、证据名称或附件来源。');
    score -= 18;
  }
  if (requirements.legalBasis !== false) {
    const legalHits = LEGAL_SIGNALS.filter((signal) => text.includes(signal));
    if (legalHits.length === 0) {
      warnings.push('AI 输出缺少法律依据或法条/司法解释信号。');
      score -= 14;
    }
  }
  if (MOJIBAKE_RE.test(text)) {
    warnings.push('AI 输出或输入透传中出现疑似乱码。');
    score -= 14;
  }
  const caseNumbers = text.match(FABRICATED_CASE_RE) || [];
  if (caseNumbers.length > 0 && !/(检索|来源|裁判文书网|数据库|需核验|核实)/.test(text)) {
    warnings.push(`AI 输出出现具体案号但未说明来源/核验状态：${caseNumbers.slice(0, 3).join('、')}`);
    score -= 20;
  }
  if (requirements.expectedEvidenceCount) {
    const countMatches = [...text.matchAll(/(?:全部|共|已上传|提供了?)\s*(\d+)\s*(?:份|条)(?:证据|文档|材料)?/g)]
      .map((match) => Number(match[1]))
      .filter(Number.isFinite);
    const wrongCounts = [...new Set(countMatches.filter((count) => count !== requirements.expectedEvidenceCount))];
    if (wrongCounts.length > 0) {
      warnings.push(`AI 输出的证据数量与系统记录不一致：输出 ${wrongCounts.join('、')}，系统记录 ${requirements.expectedEvidenceCount}。`);
      score -= 12;
    }
  }
  if (OVERCONFIDENT_RE.test(text)) {
    warnings.push('AI 输出存在过度确定性表达，法律风险提示不足。');
    score -= 15;
  }
  if (/相关法律规定/.test(text) && !/(第[一二三四五六七八九十百\d]+条|条款内容|依据《)/.test(text)) {
    warnings.push('AI 输出使用“相关法律规定”但未落到具体条文。');
    score -= 10;
  }
  return {
    score: Math.max(0, score),
    warnings,
    chars: text.length,
    case_signal_hits: CASE_SIGNALS.filter((signal) => text.includes(signal)),
    legal_signal_hits: LEGAL_SIGNALS.filter((signal) => text.includes(signal)),
    suspicious_case_numbers: caseNumbers,
  };
}

function normalizeList(payload) {
  if (Array.isArray(payload)) return payload;
  for (const key of ['items', 'data', 'cases', 'documents', 'reports', 'records', 'evidence_list', 'letters', 'appeals', 'arguments', 'expenses', 'assets', 'tasks', 'milestones', 'deadlines']) {
    if (Array.isArray(payload?.[key])) return payload[key];
  }
  return [];
}

async function loadOpenapi() {
  const spec = await request('/openapi.json', { timeoutMs: 60000 });
  openapiPaths = spec.data?.paths || {};
  await writeJson(join(outputDir, 'openapi.json'), spec.data);
  const paths = Object.keys(openapiPaths).sort();
  await writeFile(join(outputDir, 'openapi-paths.txt'), `${paths.join('\n')}\n`, 'utf8');
  return spec.data;
}

async function ensureAuth() {
  let username = options.username;
  let password = options.password;
  if ((username && !password) || (!username && password)) {
    throw new Error('username and password must be provided together');
  }
  if (!username) {
    const suffix = Date.now();
    username = `bokai_audit_${suffix}`;
    password = `Bokai-${suffix}!`;
    await request('/api/auth/register', {
      method: 'POST',
      expected: [200, 201],
      body: {
        username,
        email: `${username}@codexaudit.dev`,
        password,
        full_name: 'Bokai Audit User',
        tenant_name: `Bokai Audit Tenant ${suffix}`,
        tenant_type: 'law_firm',
        role: 'lawyer',
      },
    });
    if (/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) {
      const caseTenantId = String(await queryLocalAuditSql(`select tenant_id from cases where id = ${Number(options.caseId)} limit 1;`)).trim();
      if (caseTenantId) {
        const safeUsername = username.replace(/'/g, "''");
        const safeTenant = caseTenantId.replace(/'/g, "''");
        await runLocalAuditSql(`update users set tenant_id = '${safeTenant}' where username = '${safeUsername}';`);
      }
    }
  }
  const login = await request('/api/auth/login', {
    method: 'POST',
    body: { username, password },
  });
  const token = login.data?.tokens?.access_token;
  assert(token, 'login did not return access token');
  return { username, password, token, generated: !options.username };
}

async function buildContext(caseId) {
  const caseResult = await request(`/api/cases/${caseId}`, { timeoutMs: 60000 });
  const evidenceResult = await request(`/api/v2/evidence-graph/evidence/list?case_id=${caseId}`, { timeoutMs: 60000 });
  const letterResult = await request(`/api/time-control/case/${caseId}/letters`, { timeoutMs: 60000 });
  const evidence = normalizeList(evidenceResult.data);
  const letters = normalizeList(letterResult.data);
  const usefulEvidence = evidence.filter((item) => {
    const text = `${item.display_name || ''} ${item.original_filename || ''} ${item.summary || ''} ${item.raw_content || item.extracted_content || ''}`;
    return /[\u4e00-\u9fa5]/.test(text) && !/解析失败/.test(text) && text.length > 100;
  });
  return {
    case: caseResult.data,
    evidence,
    evidenceCount: evidence.length,
    usefulEvidence,
    representativeEvidence: usefulEvidence[0] || evidence[0],
    letters,
    representativeLetter: letters.find((letter) => JSON.stringify(letter).length > 200) || letters[0],
  };
}

async function runSystemAndDataSuite(ctx, auth) {
  const caseId = options.caseId;

  await step('system-health', 'system', async () => {
    const health = await request('/health');
    const ready = await request('/ready');
    return { payload: { health: health.data, ready: ready.data }, detail: `health=${health.data?.status} ready=${ready.data?.status}` };
  });
  await step('llm-router-status', 'system', async () => (await request('/api/llm/router/status', { expected: [200, 503] })).data);
  await step('third-party-health', 'system', async () => (await request('/api/third-party/health', { expected: [200, 503] })).data);
  await step('auth-me-refresh', 'auth', async () => {
    const me = await request('/api/auth/me', { token: auth.token });
    const refresh = await request('/api/auth/refresh', { method: 'POST', body: { refresh_token: 'not-used' }, expected: [200, 401, 422] });
    return { payload: { me: me.data, refresh_status: refresh.response.status }, detail: `user=${me.data?.user?.username || auth.username}` };
  });

  await step('case-list-detail-structure', 'case', async () => {
    const list = await request('/api/cases');
    const detail = await request(`/api/cases/${caseId}`);
    const structure = await request(`/api/cases/${caseId}/structure`);
    const nodes = await request(`/api/cases/${caseId}/nodes`);
    return {
      payload: { list: list.data, detail: detail.data, structure: structure.data, nodes: nodes.data },
      detail: `title=${detail.data?.title || ''} evidence=${ctx.evidence.length}`,
    };
  });
  await runIsolatedCaseMutationSuite();
  await runCaseCrudSuite(caseId);
  await runClaimSuite(caseId, ctx);

  await step('dashboard-family', 'tracking', async () => {
    const dashboard = await request('/api/dashboard');
    const stats = await request('/api/dashboard/stats');
    const urgent = await request('/api/dashboard/urgent');
    const upcoming = await request('/api/dashboard/upcoming');
    const recentCases = await request('/api/dashboard/recent-cases');
    const aiSuggestions = await request('/api/dashboard/ai-suggestions');
    const activity = await request('/api/dashboard/activity');
    return { payload: { dashboard: dashboard.data, stats: stats.data, urgent: urgent.data, upcoming: upcoming.data, recentCases: recentCases.data, aiSuggestions: aiSuggestions.data, activity: activity.data } };
  });
  await runReminderSuite(caseId);
  await runReminderExtensionSuite();

  await step('evidence-graph-read-suite', 'evidence', async () => {
    const list = await request(`/api/v2/evidence-graph/evidence/list?case_id=${caseId}`);
    const stats = await request(`/api/v2/evidence-graph/statistics?case_id=${caseId}`);
    const summary = await request(`/api/v2/evidence-graph/summary?case_id=${caseId}`);
    const graph = await request(`/api/v2/evidence-graph/graph/data?case_id=${caseId}`);
    const types = await request('/api/v2/evidence-graph/types');
    const relationshipTypes = await request('/api/v2/evidence-graph/relationship-types');
    const evidenceId = ctx.representativeEvidence?.id;
    const detail = evidenceId ? await request(`/api/v2/evidence-graph/evidence/${evidenceId}`) : { data: null };
    const form = evidenceId ? await request(`/api/v2/evidence-graph/evidence/${evidenceId}/correction-form`) : { data: null };
    return {
      payload: { list: list.data, stats: stats.data, summary: summary.data, graph: graph.data, types: types.data, relationshipTypes: relationshipTypes.data, detail: detail.data, correction_form: form.data },
      detail: `total=${list.data?.total ?? ctx.evidence.length} representative=${evidenceId || 'none'}`,
    };
  });
  await runEvidenceGraphMutationSuite();
  await runAssistantUploadSuite();
  await step('evidence-guide-profile-suite', 'evidence', async () => {
    const diagnosis = await request('/api/v2/evidence-guide/diagnose', { method: 'POST', body: { case_id: caseId, force_refresh: false }, timeoutMs: 60000 });
    const evidenceTypes = await request('/api/v2/evidence-guide/evidence-types');
    const profileSummary = await request(`/api/v2/profile/summary/${caseId}`);
    const gaps = await request(`/api/v2/profile/gaps/${caseId}`);
    const knowledgeGraph = await request(`/api/v2/profile/knowledge-graph/${caseId}`);
    const knowledgeQuery = await request('/api/v2/profile/knowledge/query', {
      method: 'POST',
      body: { case_id: caseId, query: '博凯升华案中陈靖可以主张哪些权利？', knowledge_type: 'fact' },
      timeoutMs: 60000,
    });
    return { payload: { diagnosis: diagnosis.data, evidenceTypes: evidenceTypes.data, profileSummary: profileSummary.data, gaps: gaps.data, knowledgeGraph: knowledgeGraph.data, knowledgeQuery: knowledgeQuery.data } };
  });
  await runEvidenceGuideProfileMutationSuite(caseId);

  await step('documents-read-suite', 'documents', async () => {
    const templates = await request('/api/documents/templates');
    const docs = await request(`/api/documents/case/${caseId}`);
    const all = await request('/api/documents');
    return { payload: { templates: templates.data, case_documents: docs.data, all_documents: all.data }, detail: `templates=${normalizeList(templates.data).length} docs=${normalizeList(docs.data).length}` };
  });
  await runDocumentMutationSuite(caseId);
  await runAdversarialCrudSuite(caseId);
  await runAdversarialAsyncStatusSuite(caseId, ctx);
  await runTimeControlSuite(caseId, ctx);
  await runExecutionAppealFinanceSuites(caseId);
  await runHearingCrudSuite(caseId);
  await runHearingToolSuite(caseId);
  await runSeniorAnalysisReadSuite(caseId);
  await runReportReadSuite(caseId);
  await runReportLifecycleSuite(caseId);
}

async function runEvidenceGraphMutationSuite() {
  const marker = `Bokai Audit Temp Case Evidence Graph ${Date.now()}`;
  let tempCaseId;
  await step('evidence-graph-mutation-suite', 'evidence', async () => {
    tempCaseId = await createAuditTempCase(marker, '隔离临时案件，用于覆盖证据图谱的处理、纠偏、关系分析、单证分析和删除链路。');
    const filename = `bokai-audit-graph-${Date.now()}.txt`;
    const processed = await request('/api/v2/evidence-graph/evidence/process', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      expected: [200, 201],
      body: {
        case_id: tempCaseId,
        source_type: 'text',
        content: '博凯升华证据图谱审计临时文本：用于验证证据处理、更新、纠偏和分析历史链路。内容包含合作协议、付款、停业责任、工资社保、保证金、信息服务费等关键词。',
        original_filename: filename,
        source_party: 'OUR_SIDE',
      },
    });
    const evidenceId = processed.data?.id || processed.data?.evidence_id || processed.data?.evidence?.id;
    assert(evidenceId, `evidence process returned no evidence id: ${shortJson(processed.data)}`);
    const updated = await request('/api/v2/evidence-graph/evidence/update', {
      method: 'PUT',
      body: {
        evidence_id: String(evidenceId),
        summary: '审计更新：临时证据用于验证图谱写入链路。',
        evidence_type: 'DOCUMENT',
        source_party: 'OUR_SIDE',
        proves_facts: [{ fact: '审计临时事实', strength: 60 }],
        keywords: ['博凯升华', '审计', '证据图谱'],
      },
    });
    const corrected = await request('/api/v2/evidence-graph/evidence/correct', {
      method: 'POST',
      body: {
        evidence_id: String(evidenceId),
        correct_summary: '审计纠偏：该证据仅用于功能测试，不纳入正式案件证据链。',
        correct_type: 'DOCUMENT',
        proof_direction: 'OUR_SIDE',
        proves_facts_corrected: ['验证证据纠偏保存'],
        relevance_score: 50,
        credibility_corrected: 60,
        authenticity_corrected: 60,
        reliability_corrected: 60,
        manual_notes: 'Bokai audit temporary graph evidence.',
        is_verified: true,
        status: 'verified',
      },
    });
    const detail = await request(`/api/v2/evidence-graph/evidence/${encodeURIComponent(evidenceId)}`);
    const relationships = await request('/api/v2/evidence-graph/relationships/analyze', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: { case_id: tempCaseId, force_refresh: true },
    });
    const analyzed = await request('/api/v2/evidence-graph/evidence/analyze', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: { evidence_id: String(evidenceId), analysis_type: 'comprehensive', force_refresh: true },
    });
    const history = await request(`/api/v2/evidence-graph/evidence/${encodeURIComponent(evidenceId)}/analysis-history`);
    const historyDeleted = await request(`/api/v2/evidence-graph/evidence/${encodeURIComponent(evidenceId)}/analysis-history`, { method: 'DELETE' });
    const evidenceDeleted = await request(`/api/v2/evidence-graph/evidence/${encodeURIComponent(evidenceId)}`, { method: 'DELETE' });
    const cleanup = await cleanupTempCase(tempCaseId);
    tempCaseId = null;
    return {
      payload: { processed: processed.data, updated: updated.data, corrected: corrected.data, detail: detail.data, relationships: relationships.data, analyzed: analyzed.data, history: history.data, historyDeleted: historyDeleted.data, evidenceDeleted: evidenceDeleted.data, cleanup },
      detail: `temp_case=${marker} evidence=${evidenceId} cleanup=${cleanup?.stdout || 'done'}`,
    };
  });
  if (tempCaseId) {
    try {
      await cleanupTempCase(tempCaseId);
    } catch (error) {
      recordDefect('evidence-graph-mutation-suite-cleanup', 'P1', `证据图谱临时案件清理失败：${formatError(error)}`);
    }
  }
}

async function runAssistantUploadSuite() {
  const marker = `Bokai Audit Temp Case Assistant Upload ${Date.now()}`;
  let tempCaseId;
  await step('assistant-upload-suite', 'assistant', async () => {
    tempCaseId = await createAuditTempCase(marker, '隔离临时案件，用于覆盖统一助手上传处理入口。');
    const uploaded = await request('/api/v2/assistant/upload', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      expected: [200, 201],
      body: {
        case_id: tempCaseId,
        filename: `bokai-assistant-upload-${Date.now()}.txt`,
        content: '统一助手上传审计临时文档：说明合作出资、停业责任、工资社保、保证金和信息服务费需要分项举证。',
        doc_type: '审计临时材料',
      },
    });
    const cleanup = await cleanupTempCase(tempCaseId);
    tempCaseId = null;
    return { payload: { uploaded: uploaded.data, cleanup }, detail: `temp_case=${marker} cleanup=${cleanup?.stdout || 'done'}` };
  });
  if (tempCaseId) {
    try {
      await cleanupTempCase(tempCaseId);
    } catch (error) {
      recordDefect('assistant-upload-suite-cleanup', 'P1', `统一助手上传临时案件清理失败：${formatError(error)}`);
    }
  }
}

async function runReportReadSuite(caseId) {
  await step('reports-read-suite', 'reports', async () => {
    const all = await request('/api/reports');
    const list = await request(`/api/reports/list/${caseId}`);
    const status = await request(`/api/reports/status/${caseId}`);
    const smartHealth = await request('/api/smart-chat/health');
    return { payload: { all: all.data, list: list.data, status: status.data, smartHealth: smartHealth.data }, detail: `reports=${normalizeList(list.data).length || 'ok'}` };
  });
}

async function cleanupReportAudit(caseId, titleLike = 'Bokai Audit Report %') {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return { skipped: true };
  const safe = String(titleLike).replace(/'/g, "''");
  const sql = [
    `delete from report_sections where outline_id in (select id from report_outlines where case_id = ${Number(caseId)} and title like '${safe}');`,
    `delete from report_outlines where case_id = ${Number(caseId)} and title like '${safe}';`,
  ].join(' ');
  return runLocalAuditSql(sql);
}

async function findLatestReportId(caseId, titleLike = 'Bokai Audit Report %') {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return null;
  const safe = String(titleLike).replace(/'/g, "''");
  const output = await queryLocalAuditSql(`select id from report_outlines where case_id = ${Number(caseId)} and title like '${safe}' order by created_at desc limit 1;`);
  return String(output || '').trim() || null;
}

async function findLatestReportIdByType(caseId, reportType) {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return null;
  const safe = String(reportType).replace(/'/g, "''");
  const output = await queryLocalAuditSql(`select id from report_outlines where case_id = ${Number(caseId)} and report_type = '${safe}' order by created_at desc limit 1;`);
  return String(output || '').trim() || null;
}

async function runReportLifecycleSuite(caseId) {
  await step('reports-lifecycle-suite', 'reports', async () => {
    const startedAtSql = new Date(Date.now() - 1000).toISOString();
    const streamed = await request(`/api/reports/generate-stream/${caseId}`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      expected: [200],
      body: { report_type: 'summary', force_regenerate: true },
      headers: { Accept: 'text/event-stream, */*' },
      skipBody: true,
    });
    const generated = await request(`/api/reports/generate/${caseId}`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      expected: [200],
      body: { report_type: 'summary', force_regenerate: true },
    });
    const reportId = await findLatestReportIdByType(caseId, 'SUMMARY_REPORT');
    assert(reportId, 'report generate did not create a report outline');
    const detail = await request(`/api/reports/detail/${encodeURIComponent(reportId)}`);
    const exported = await request(`/api/reports/export/${encodeURIComponent(reportId)}?format=markdown`, { headers: { Accept: '*/*' } });
    const compared = await request(`/api/reports/compare/${encodeURIComponent(reportId)}/${encodeURIComponent(reportId)}`);
    const documents = await request(`/api/reports/generate-documents/${caseId}`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200] });
    const cancel = await request(`/api/reports/cancel/${caseId}?report_type=summary`, { method: 'POST' });
    const invalidated = await request(`/api/reports/invalidate-cache/${caseId}`, { method: 'POST' });
    const regenerated = await request(`/api/reports/regenerate/${encodeURIComponent(reportId)}`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      expected: [200, 500],
    });
    const deleted = await request(`/api/reports/${encodeURIComponent(reportId)}`, { method: 'DELETE' });
    const cleanup = await runLocalAuditSql([
      `delete from report_sections where outline_id in (select id from report_outlines where case_id = ${Number(caseId)} and created_at >= '${startedAtSql}');`,
      `delete from report_outlines where case_id = ${Number(caseId)} and created_at >= '${startedAtSql}';`,
    ].join(' '));
    const warnings = [];
    if (regenerated.response.status >= 500) warnings.push('报告重新生成接口返回 500，需检查报告生命周期重建逻辑。');
    return {
      payload: { streamedStatus: streamed.response.status, streamedChars: streamed.text?.length || 0, generated: generated.data, reportId, detail: detail.data, exportedStatus: exported.response.status, compare: compared.data, documents: documents.data, cancel: cancel.data, invalidated: invalidated.data, regenerated: regenerated.data, deleted: deleted.data, cleanup },
      detail: `report=${reportId} export=${exported.response.status} cleanup=${cleanup?.stdout || 'done'}`,
      warnings,
    };
  });
}

async function runSeniorAnalysisReadSuite(caseId) {
  await step('senior-analysis-read-suite', 'senior-analysis', async () => {
    const understanding = await request(`/api/v2/senior-analysis/case-understanding/${caseId}`);
    const requirements = await request(`/api/v2/senior-analysis/requirements/${caseId}`);
    const severityLevels = await request('/api/v2/senior-analysis/severity-levels');
    return {
      payload: { understanding: understanding.data, requirements: requirements.data, severityLevels: severityLevels.data },
      detail: `requirements=${normalizeList(requirements.data?.requirements || requirements.data).length || 'ok'}`,
    };
  });
}

async function cleanupGuideAuditDocuments(marker) {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return { skipped: true };
  const safe = String(marker).replace(/'/g, "''");
  return runLocalAuditSql(`delete from documents where filename like '${safe}%';`);
}

async function runEvidenceGuideProfileMutationSuite(caseId) {
  const marker = `Bokai Audit Guide Evidence ${Date.now()}`;
  let needsCleanup = false;
  await step('evidence-guide-profile-mutation-suite', 'evidence', async () => {
    const answer = await request('/api/v2/evidence-guide/question/answer', {
      method: 'POST',
      body: {
        case_id: caseId,
        question_id: 'gap_1',
        answer: '已有合作协议、资金流水、微信聊天记录和函件往来，审计要求继续核验证据编号和证明目的。',
      },
    });
    const added = await request('/api/v2/evidence-guide/evidence/add', {
      method: 'POST',
      body: {
        case_id: caseId,
        name: marker,
        description: '审计临时证据指引记录，完成后删除。',
        evidence_type: '审计临时证据',
        custody: '原告',
        content: '用于验证证据引导添加入口，不作为正式案件证据。',
      },
    });
    needsCleanup = true;
    const gapSolutions = await request('/api/v2/evidence-guide/gap-solutions/书面证据');
    const profile = await request('/api/v2/profile/build', { method: 'POST', body: { case_id: caseId, use_ai: false }, timeoutMs: 60000 });
    const gaps = await request(`/api/v2/profile/gaps/${caseId}`);
    const firstGap = normalizeList(gaps.data?.unresolved_gaps)[0]?.id || 'gap_contract';
    const resolved = await request('/api/v2/profile/gap/resolve', {
      method: 'POST',
      body: {
        case_id: caseId,
        gap_id: firstGap,
        resolution: '审计记录：已确认需回到177条证据链核对证明目的。',
      },
    });
    const interaction = await request('/api/v2/profile/interaction', {
      method: 'POST',
      body: {
        case_id: caseId,
        user_input: '审计：博凯升华案中哪些证据最能支撑停业责任？',
        input_type: 'audit_question',
        system_response: '优先核对合作协议、停业通知、资金流水和函件往来。',
      },
    });
    const quickActions = await request(`/api/v2/assistant/quick-actions/${caseId}`);
    const history = await request(`/api/v2/assistant/conversation-history/${caseId}?limit=5&offset=0`);
    const cleanup = await cleanupGuideAuditDocuments(marker);
    needsCleanup = false;
    return {
      payload: { answer: answer.data, added: added.data, gapSolutions: gapSolutions.data, profile: profile.data, resolved: resolved.data, interaction: interaction.data, quickActions: quickActions.data, history: history.data, cleanup },
      detail: `guide_doc=${added.data?.document_id || 'ok'} cleanup=${cleanup?.stdout || 'done'}`,
    };
  });
  if (needsCleanup) {
    try {
      await cleanupGuideAuditDocuments(marker);
    } catch (error) {
      recordDefect('evidence-guide-profile-mutation-cleanup', 'P1', `证据引导审计文档清理失败：${formatError(error)}`);
    }
  }
}

async function cleanupTempCase(caseId) {
  if (!caseId) return { skipped: true };
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) {
    return { skipped: true, reason: 'cleanup only runs against local docker target' };
  }
  const sql = `delete from cases where id = ${Number(caseId)} and title like 'Bokai Audit Temp Case %';`;
  return runLocalAuditSql(sql);
}

async function createAuditTempCase(title, description) {
  const created = await request('/api/cases', {
    method: 'POST',
    expected: [200, 201],
    body: {
      title,
      case_type: 'civil',
      plaintiff: '审计临时原告',
      defendant: '审计临时被告',
      cause: '功能审计临时案由',
      claim_amount: '1',
      description,
    },
  });
  const caseId = created.data?.id;
  assert(caseId, `temp case create returned no id: ${shortJson(created.data)}`);
  return caseId;
}

async function runLocalAuditSql(sql) {
  const { stdout, stderr } = await execFileAsync('docker', ['exec', 'legal-postgres-prod', 'psql', '-U', 'legal_user', '-d', 'legal_db', '-t', '-A', '-c', sql], { timeout: 30000 });
  return { stdout: stdout.trim(), stderr: stderr.trim() };
}

async function queryLocalAuditSql(sql) {
  const result = await runLocalAuditSql(sql);
  return result.stdout;
}

function sqlStringOrNull(value) {
  if (value === undefined || value === null || value === '') return 'NULL';
  return `'${String(value).replace(/'/g, "''")}'`;
}

function sqlNumberOrNull(value) {
  if (value === undefined || value === null || value === '') return 'NULL';
  const number = Number(value);
  return Number.isFinite(number) ? String(number) : 'NULL';
}

async function runIsolatedCaseMutationSuite() {
  const marker = `Bokai Audit Temp Case ${Date.now()}`;
  let tempCaseId;
  await step('isolated-case-lifecycle-chat-upload', 'case', async () => {
    const created = await request('/api/cases', {
      method: 'POST',
      expected: [200, 201],
      body: {
        title: marker,
        case_type: 'civil',
        plaintiff: '审计临时原告',
        defendant: '审计临时被告',
        cause: '功能审计临时案由',
        claim_amount: '1',
        description: '隔离临时案件，用于覆盖创建、修改、执行、聊天、问答、文档上传等入口，审计结束后清理。',
      },
    });
    tempCaseId = created.data?.id;
    assert(tempCaseId, 'temp case create returned no id');

    const detail = await request(`/api/cases/${tempCaseId}`);
    const updated = await request(`/api/cases/${tempCaseId}`, {
      method: 'PUT',
      body: {
        description: '隔离临时案件已更新。',
        supplement: '审计补充：用于验证补充资料节点和后续问答入口。',
      },
    });
    const supplement = await request(`/api/cases/${tempCaseId}/supplement`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: { title: '审计补充资料', content: '临时案件补充资料：合同履行、证据上传和聊天问答功能校验。', auto_analyze: false },
    });
    const nodes = await request(`/api/cases/${tempCaseId}/nodes`);
    const firstNode = normalizeList(nodes.data)[0];
    const nodeDetail = firstNode?.id ? await request(`/api/cases/${tempCaseId}/nodes/${firstNode.id}`) : { data: null };

    const chat = await request(`/api/cases/${tempCaseId}/chat`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: { content: '请基于这个临时案件说明下一步应补充哪些证据。' },
      expected: [200, 500],
    });
    const history = await request(`/api/cases/${tempCaseId}/chat/history`);
    const suggestions = await request(`/api/cases/${tempCaseId}/evidence-suggestions`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200, 500] });
    const historyDeleted = await request(`/api/cases/${tempCaseId}/chat/history`, { method: 'DELETE' });

    const form = new FormData();
    form.append('file', new Blob(['审计临时上传文档：用于验证上传、详情、下载、删除链路。'], { type: 'text/plain' }), 'bokai-audit-temp.txt');
    const upload = await request(`/api/documents/upload/${tempCaseId}?doc_type=${encodeURIComponent('审计临时文档')}`, {
      method: 'POST',
      body: form,
      timeoutMs: options.aiTimeoutMs,
      expected: [200, 201],
    });
    const docId = upload.data?.id;
    const docDetail = docId ? await request(`/api/documents/${docId}`) : { data: null };
    const legacyAsk = await request(`/api/cases/${tempCaseId}/ask`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      expected: [200, 500],
      body: { question: '请基于这个审计临时案件，说明合作关系和费用主张应补充哪些证据。' },
    });
    const legacyAnalyze = await request(`/api/cases/${tempCaseId}/analyze`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      expected: [200, 500],
    });
    const legacyStrategy = await request(`/api/cases/${tempCaseId}/strategy`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      expected: [200, 500],
    });
    const docAnalyzed = docId ? await request(`/api/cases/${tempCaseId}/document-analyzed/${docId}`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      expected: [200, 500],
    }) : { data: null, response: { status: 0 } };
    const docDownload = docId ? await request(`/api/documents/${docId}/download?doc_type=uploaded`, { headers: { Accept: '*/*' }, expected: [200] }) : { data: null, response: { status: 0 } };
    const docDeleted = docId ? await request(`/api/documents/${docId}`, { method: 'DELETE' }) : { data: null };

    const closed = await request(`/api/cases/${tempCaseId}/close`, {
      method: 'POST',
      body: {
        closure_result: '审计结案',
        closure_type: '功能审计',
        closure_amount: '0',
        closure_notes: '隔离临时案件普通结案，用于覆盖重新激活入口。',
        transfer_to_execution: false,
        archive_case: true,
      },
    });
    const reopened = await request(`/api/cases/${tempCaseId}/reopen?reason=${encodeURIComponent('审计验证重新开启')}`, { method: 'POST' });
    const executionClosed = await request(`/api/cases/${tempCaseId}/close`, {
      method: 'POST',
      body: {
        closure_result: '审计执行结案',
        closure_type: '功能审计',
        closure_amount: '0',
        closure_notes: '隔离临时案件再次结案并转入执行，用于覆盖执行跟踪入口。',
        transfer_to_execution: true,
        execution_case_number: `AUDIT-${Date.now()}`,
        execution_amount: '1',
        executor_name: '审计员',
        archive_case: false,
      },
    });
    const execution = await request(`/api/cases/${tempCaseId}/execution`);
    const executionUpdated = await request(`/api/cases/${tempCaseId}/execution`, { method: 'PUT', body: { execution_court: '审计执行法院', progress: 10, status: 'pending' } });
    const executionRecord = await request(`/api/cases/${tempCaseId}/execution/record`, { method: 'POST', body: { action: '审计执行记录', note: '覆盖执行记录新增入口' } });
    const executionList = await request('/api/cases/execution/list');
    const deleteGuard = await request(`/api/cases/${tempCaseId}`, { method: 'DELETE', expected: [403] });

    const cleanup = await cleanupTempCase(tempCaseId);
    tempCaseId = null;
    const warnings = [];
    if (chat.response.status >= 500) warnings.push('临时案件聊天接口返回 500，需检查空证据案件下的问答降级。');
    if (suggestions.response.status >= 500) warnings.push('临时案件证据建议接口返回 500，需检查空证据案件下的建议生成。');
    if (legacyAsk.response.status >= 500) warnings.push('旧案件问答接口返回 500，需检查临时案件问答降级。');
    if (legacyAnalyze.response.status >= 500) warnings.push('旧案件分析接口返回 500，需检查临时案件分析降级。');
    if (legacyStrategy.response.status >= 500) warnings.push('旧案件策略接口返回 500，需检查临时案件策略降级。');
    if (docAnalyzed.response.status >= 500) warnings.push('上传文档自动分析接口返回 500，需检查文档节点分析降级。');
    return {
      payload: { created: created.data, detail: detail.data, updated: updated.data, supplement: supplement.data, nodes: nodes.data, nodeDetail: nodeDetail.data, chat: chat.data, history: history.data, suggestions: suggestions.data, historyDeleted: historyDeleted.data, upload: upload.data, docDetail: docDetail.data, legacyAsk: legacyAsk.data, legacyAnalyze: legacyAnalyze.data, legacyStrategy: legacyStrategy.data, docAnalyzed: docAnalyzed.data, docDownloadStatus: docDownload.response.status, docDeleted: docDeleted.data, closed: closed.data, reopened: reopened.data, executionClosed: executionClosed.data, execution: execution.data, executionUpdated: executionUpdated.data, executionRecord: executionRecord.data, executionList: executionList.data, deleteGuardStatus: deleteGuard.response.status, cleanup },
      detail: `temp_case=${created.data?.id} upload_doc=${docId || 'none'} cleanup=${cleanup?.stdout || 'done'}`,
      warnings,
    };
  });
  if (tempCaseId) {
    try {
      await cleanupTempCase(tempCaseId);
    } catch (error) {
      recordDefect('isolated-case-lifecycle-chat-upload-cleanup', 'P1', `临时案件清理失败：${formatError(error)}`);
    }
  }
}

async function runCaseCrudSuite(caseId) {
  const marker = `Bokai Audit ${Date.now()}`;
  let threadId;
  let partyId;
  let claimId;
  await step('case-thread-crud', 'case', async () => {
    const created = await request(`/api/cases/${caseId}/threads`, {
      method: 'POST',
      body: { name: `${marker} thread`, cause: '审计临时线索', description: '用于全功能审计，完成后删除。', amount: '0', status: 'active' },
      expected: [200, 201],
    });
    threadId = created.data?.id;
    assert(threadId, 'thread create returned no id');
    const list = await request(`/api/cases/${caseId}/threads`);
    const aliasDetail = await request(`/api/cases/threads/${threadId}`);
    const aliasUpdated = await request(`/api/cases/threads/${threadId}`, {
      method: 'PUT',
      body: { evidence_summary: '短路径别名更新通过' },
    });
    const updated = await request(`/api/cases/${caseId}/threads/${threadId}`, {
      method: 'PUT',
      body: { description: '审计临时线索已更新。' },
    });
    const deleted = await request(`/api/cases/threads/${threadId}`, { method: 'DELETE' });
    const longDeleteAfterAlias = await request(`/api/cases/${caseId}/threads/${threadId}`, { method: 'DELETE', expected: [404] });
    return { payload: { created: created.data, list: list.data, aliasDetail: aliasDetail.data, aliasUpdated: aliasUpdated.data, updated: updated.data, deleted: deleted.data, longDeleteAfterAliasStatus: longDeleteAfterAlias.response.status } };
  });
  await step('case-party-counterclaim-crud', 'case', async () => {
    const party = await request(`/api/cases/${caseId}/parties`, {
      method: 'POST',
      expected: [200, 201],
      body: { name: `${marker} witness`, party_type: '个人', role: '证人', relation_to_case: '审计临时记录' },
    });
    partyId = party.data?.id;
    assert(partyId, 'party create returned no id');
    const parties = await request(`/api/cases/${caseId}/parties`);
    const partyAliasDetail = await request(`/api/cases/parties/${partyId}`);
    const partyAliasUpdated = await request(`/api/cases/parties/${partyId}`, { method: 'PUT', body: { relation_to_case: '短路径别名更新通过' } });
    const partyUpdated = await request(`/api/cases/${caseId}/parties/${partyId}`, { method: 'PUT', body: { phone: '13800000000' } });

    const counter = await request(`/api/cases/${caseId}/counter-claims`, {
      method: 'POST',
      expected: [200, 201],
      body: { title: `${marker} counter claim`, claim_type: '审计', amount: '0', description: '审计临时反诉记录', status: 'pending' },
    });
    claimId = counter.data?.id;
    assert(claimId, 'counter claim create returned no id');
    const counterList = await request(`/api/cases/${caseId}/counter-claims`);
    const counterAliasUpdated = await request(`/api/cases/counter-claims/${claimId}`, { method: 'PUT', body: { description: '短路径别名更新通过' } });
    const counterUpdated = await request(`/api/cases/${caseId}/counter-claims/${claimId}`, { method: 'PUT', body: { status: 'reviewed' } });
    const counterDeleted = await request(`/api/cases/counter-claims/${claimId}`, { method: 'DELETE' });
    const partyDeleted = await request(`/api/cases/parties/${partyId}`, { method: 'DELETE' });
    const counterLongDeleteAfterAlias = await request(`/api/cases/${caseId}/counter-claims/${claimId}`, { method: 'DELETE', expected: [404] });
    const partyLongDeleteAfterAlias = await request(`/api/cases/${caseId}/parties/${partyId}`, { method: 'DELETE', expected: [404] });
    return { payload: { party: party.data, parties: parties.data, partyAliasDetail: partyAliasDetail.data, partyAliasUpdated: partyAliasUpdated.data, partyUpdated: partyUpdated.data, counter: counter.data, counterList: counterList.data, counterAliasUpdated: counterAliasUpdated.data, counterUpdated: counterUpdated.data, counterDeleted: counterDeleted.data, partyDeleted: partyDeleted.data, counterLongDeleteAfterAliasStatus: counterLongDeleteAfterAlias.response.status, partyLongDeleteAfterAliasStatus: partyLongDeleteAfterAlias.response.status } };
  });
}

async function runClaimSuite(caseId, ctx) {
  const marker = `Bokai Audit Claim ${Date.now()}`;
  let claimId;
  await step('claims-crud-and-plan', 'claims', async () => {
    const created = await request('/api/claims', {
      method: 'POST',
      expected: [200, 201],
      body: {
        case_id: caseId,
        title: marker,
        description: '审计临时战役：核对合作出资、工资、保证金等主张路径。',
        claim_type: '合同/公司治理',
        amount: '0',
        priority: 3,
      },
    });
    claimId = created.data?.id;
    assert(claimId, 'claim create returned no id');
    const list = await request(`/api/claims/case/${caseId}`);
    const simpleDetail = await request(`/api/claims/${claimId}`);
    const detail = await request(`/api/claims/${claimId}/detail`);
    const updated = await request(`/api/claims/${claimId}`, { method: 'PUT', body: { notes: '审计更新', priority: 2 } });
    const evidenceId = ctx.representativeEvidence?.id;
    const evidenceAdd = evidenceId ? await request(`/api/claims/${claimId}/evidence`, { method: 'POST', body: [String(evidenceId)], expected: [200, 201, 422] }) : { data: null };
    const evidenceDelete = evidenceId ? await request(`/api/claims/${claimId}/evidence`, { method: 'DELETE', body: [String(evidenceId)], expected: [200, 201, 404, 422] }) : { data: null };
    const plan = await request(`/api/claims/${claimId}/plan`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200, 500, 504] });
    const activated = await request(`/api/claims/${claimId}/activate`, { method: 'POST', expected: [200, 400, 500] });
    const completed = await request(`/api/claims/${claimId}/complete`, { method: 'POST', expected: [200, 400, 500] });
    const deleted = await request(`/api/claims/${claimId}`, { method: 'DELETE' });
    const warnings = [];
    if (plan.response.status >= 500) warnings.push(`战役规划接口返回 ${plan.response.status}，可能存在 AI 调用、Nginx 超时或数据约束问题。`);
    return { payload: { created: created.data, list: list.data, simpleDetail: simpleDetail.data, detail: detail.data, updated: updated.data, evidenceAdd: evidenceAdd.data, evidenceDelete: evidenceDelete.data, plan: plan.data, activated: activated.data, completed: completed.data, deleted: deleted.data }, warnings };
  });
}

async function cleanupGeneratedDocs(titleLike) {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return { skipped: true };
  const safe = String(titleLike).replace(/'/g, "''");
  return runLocalAuditSql(`delete from generated_documents where title like '${safe}';`);
}

async function cleanupBatchAuditDocuments(caseId) {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return { skipped: true };
  const sql = [
    `delete from evidence_items_v2 where case_id = ${Number(caseId)} and original_filename like 'bokai-audit-batch-%';`,
    `delete from documents where case_id = ${Number(caseId)} and filename like 'bokai-audit-batch-%';`,
  ].join(' ');
  return runLocalAuditSql(sql);
}

async function findGeneratedDocId(titleLike) {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return null;
  const safe = String(titleLike).replace(/'/g, "''");
  const output = await queryLocalAuditSql(`select id from generated_documents where title like '${safe}' order by id desc limit 1;`);
  const id = Number(String(output).trim());
  return Number.isFinite(id) && id > 0 ? id : null;
}

async function runDocumentMutationSuite(caseId) {
  const marker = `Bokai Audit Doc ${Date.now()}`;
  let needsBatchCleanup = false;
  await step('documents-mutation-suite', 'documents', async () => {
    const form = new FormData();
    form.append('files', new Blob(['批量上传审计文档一：验证 upload-batch。'], { type: 'text/plain' }), 'bokai-audit-batch-1.txt');
    form.append('files', new Blob(['批量上传审计文档二：验证 upload-batch。'], { type: 'text/plain' }), 'bokai-audit-batch-2.txt');
    const batch = await request(`/api/documents/upload-batch/${caseId}`, {
      method: 'POST',
      body: form,
      timeoutMs: options.aiTimeoutMs,
      expected: [200, 201],
    });
    needsBatchCleanup = true;

    const enhanced = await request('/api/documents/generate/enhanced', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: {
        case_id: caseId,
        document_type: marker,
        custom_requirements: '审计临时增强文书，只需验证接口链路，不作为正式案件材料。',
        evidence_strategy: '引用博凯升华证据链时必须标注证据名称，不得编造案号。',
        claim_strategy: '围绕合作出资、停业责任和费用承担分层表达。',
        emphasis: '强调证据链闭环和补证缺口。',
        omissions: '不输出未核验判例。',
      },
    });

    const docs = await request(`/api/documents/case/${caseId}`);
    const docId = await findGeneratedDocId(`${marker}%`);
    assert(docId, 'enhanced document was not persisted or not listed');

    const modify = await request('/api/documents/modify', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: {
        document_id: docId,
        message: '请压缩为更明确的审计版本，并保留博凯升华案、177条证据链、民法典、公司法、民事诉讼法等关键信号。',
        current_content: enhanced.data?.content || '博凯升华案审计临时文书。',
      },
      expected: [200, 500],
    });
    const format = await request('/api/documents/format', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: {
        document_id: docId,
        content: modify.data?.content || enhanced.data?.content || '博凯升华案审计临时文书。',
      },
      expected: [200],
    });
    const generatedCleanup = await cleanupGeneratedDocs(`${marker}%`);
    const batchCleanup = await cleanupBatchAuditDocuments(caseId);
    needsBatchCleanup = false;
    const warnings = [];
    if (modify.response.status >= 500) warnings.push('文书对话修改接口返回 500，需检查大证据量文书修改降级能力。');
    return { payload: { batch: batch.data, enhanced: enhanced.data, caseDocuments: docs.data, generatedDocId: docId, modify: modify.data, format: format.data, generatedCleanup, batchCleanup }, detail: `batch=${normalizeList(batch.data).length || 'ok'} generated_doc=${docId} cleanup=${generatedCleanup?.stdout || 'done'} ${batchCleanup?.stdout || ''}`, warnings };
  });
  if (needsBatchCleanup) {
    try {
      await cleanupBatchAuditDocuments(caseId);
      await cleanupGeneratedDocs(`${marker}%`);
    } catch (error) {
      recordDefect('documents-mutation-suite-cleanup', 'P1', `文档审计数据清理失败：${formatError(error)}`);
    }
  }
}

async function cleanupAdversarialAudit(caseId, titleMarker) {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return { skipped: true };
  const safe = String(titleMarker).replace(/'/g, "''");
  const sql = [
    `delete from action_plans where title like '${safe}%';`,
    `delete from scenario_predictions where case_id = ${Number(caseId)} and scenario_name like '${safe}%';`,
    `delete from process_milestones where case_id = ${Number(caseId)} and name like '${safe}%';`,
    `delete from adversarial_analyses where case_id = ${Number(caseId)} and title like '${safe}%';`,
  ].join(' ');
  return runLocalAuditSql(sql);
}

async function runAdversarialCrudSuite(caseId) {
  const marker = `Bokai Audit Adversarial ${Date.now()}`;
  let analysisId;
  await step('adversarial-crud-suite', 'adversarial', async () => {
    const created = await request(`/api/adversarial/case/${caseId}/analysis`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        '标题': marker,
        '分析阶段': '诉前准备',
        '对手名称': '雷天乾/博凯健康',
        '对手类型': '公司控制方',
        '对手实力': '较强',
      },
    });
    analysisId = created.data?.id || created.data?.analysis_id;
    assert(analysisId, 'adversarial analysis create returned no id');
    const list = await request(`/api/adversarial/case/${caseId}/analyses`);
    const detail = await request(`/api/adversarial/${analysisId}`);
    const updated = await request(`/api/adversarial/${analysisId}`, {
      method: 'PUT',
      body: {
        '我方优势': '已有177条证据链，可建立请求权基础与证据映射。',
        '对方弱点': '停业责任、费用流向和公司治理程序需要逐项解释。',
        '总体策略': '先固定证据，再分层主张。',
      },
    });

    const evidence = await request(`/api/adversarial/analysis/${analysisId}/evidence`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        '名称': `${marker} evidence`,
        '证据类型': '书证',
        '来源': '审计脚本',
        '描述': '审计临时证据攻防项',
        '内容摘要': '用于验证对抗分析证据 CRUD。',
        '归属方': 'our',
        '角色': '进攻性',
        '证明力': 0.7,
      },
    });
    const evidenceId = evidence.data?.id;
    const evidenceList = await request(`/api/adversarial/analysis/${analysisId}/evidence`);
    const evidenceUpdated = evidenceId ? await request(`/api/adversarial/evidence/${evidenceId}`, { method: 'PUT', body: { '建议': '审计更新建议', '已核实': true } }) : { data: null };

    const action = await request(`/api/adversarial/analysis/${analysisId}/actions`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        '标题': `${marker} action`,
        '描述': '审计临时行动方案',
        '行动类型': '律师函',
        '执行步骤': ['核对证据编号', '补充原件来源'],
        '优先级': 'low',
        '成功概率': 0.6,
      },
    });
    const actionId = action.data?.id;
    const actions = await request(`/api/adversarial/analysis/${analysisId}/actions`);
    const actionUpdated = actionId ? await request(`/api/adversarial/action/${actionId}`, { method: 'PUT', body: { '风险评估': '低风险审计项', '优先级': 'medium' } }) : { data: null };
    const actionExecuted = actionId ? await request(`/api/adversarial/action/${actionId}/execute`, { method: 'POST' }) : { data: null };

    const scenario = await request(`/api/adversarial/case/${caseId}/scenarios`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        '情景名称': `${marker} scenario`,
        '情景描述': '审计临时情景',
        '情景类型': 'risk',
        '预测结果': '用于验证情景预测 CRUD。',
        '胜诉概率': 0.5,
        '准备清单': ['证据目录', '请求权基础表'],
      },
    });
    const scenarios = await request(`/api/adversarial/case/${caseId}/scenarios`);
    const milestone = await request(`/api/adversarial/case/${caseId}/milestones`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        '名称': `${marker} milestone`,
        '描述': '审计临时里程碑',
        '里程碑类型': 'audit',
        '阶段': '诉前准备',
        '阶段内顺序': 1,
      },
    });
    const milestoneId = milestone.data?.id;
    const milestones = await request(`/api/adversarial/case/${caseId}/milestones`);
    const milestoneUpdated = milestoneId ? await request(`/api/adversarial/milestone/${milestoneId}`, { method: 'PUT', body: { '描述': '审计临时里程碑已更新' } }) : { data: null };

    if (actionId) await request(`/api/adversarial/action/${actionId}`, { method: 'DELETE' });
    if (evidenceId) await request(`/api/adversarial/evidence/${evidenceId}`, { method: 'DELETE' });
    const deleted = await request(`/api/adversarial/${analysisId}`, { method: 'DELETE' });
    analysisId = null;
    const cleanup = await cleanupAdversarialAudit(caseId, marker);
    return { payload: { created: created.data, list: list.data, detail: detail.data, updated: updated.data, evidence: evidence.data, evidenceList: evidenceList.data, evidenceUpdated: evidenceUpdated.data, action: action.data, actions: actions.data, actionUpdated: actionUpdated.data, actionExecuted: actionExecuted.data, scenario: scenario.data, scenarios: scenarios.data, milestone: milestone.data, milestones: milestones.data, milestoneUpdated: milestoneUpdated.data, deleted: deleted.data, cleanup }, detail: `analysis=${created.data?.id || created.data?.analysis_id} cleanup=${cleanup?.stdout || 'done'}` };
  });
  if (analysisId) {
    try {
      await cleanupAdversarialAudit(caseId, marker);
    } catch (error) {
      recordDefect('adversarial-crud-suite-cleanup', 'P1', `对抗分析审计数据清理失败：${formatError(error)}`);
    }
  }
}

async function runAdversarialAsyncStatusSuite(caseId, ctx) {
  const evidenceText = (ctx.usefulEvidence || [])
    .slice(0, 3)
    .map((item, index) => `证据${index + 1}：${item.display_name || item.original_filename}\n${(item.raw_content || item.extracted_content || item.summary || '').slice(0, 500)}`)
    .join('\n\n');
  await step('adversarial-async-status-suite', 'adversarial', async () => {
    const started = await request(`/api/adversarial/case/${caseId}/full-analysis-async`, {
      method: 'POST',
      timeoutMs: options.timeoutMs,
      body: {
        analysis_phase: 'pre_litigation',
        opponent_name: ctx.case?.defendant || '雷天乾',
        opponent_type: '合作方/股东相关方',
        our_evidence: evidenceText,
      },
    });
    const taskId = started.data?.task_id;
    assert(taskId, `async full analysis did not return task_id: ${shortJson(started.data)}`);
    const status = await request(`/api/adversarial/task/${encodeURIComponent(taskId)}/status`, { timeoutMs: options.timeoutMs });
    return { payload: { started: started.data, status: status.data }, detail: `task=${taskId} status=${status.data?.status || 'unknown'}` };
  });
}

async function runReminderSuite(caseId) {
  const title = `Bokai Audit Reminder ${Date.now()}`;
  let reminderId;
  await step('reminders-lifecycle', 'tracking', async () => {
    const created = await request('/api/reminders', {
      method: 'POST',
      expected: [200, 201],
      body: {
        case_id: caseId,
        title,
        content: '博凯升华案审计临时提醒',
        priority: 'low',
        reminder_type: 'deadline',
        trigger_date: new Date(Date.now() + 86400000).toISOString(),
      },
    });
    reminderId = created.data?.id;
    assert(reminderId, 'reminder create returned no id');
    const list = await request(`/api/reminders?case_id=${caseId}`);
    const detail = await request(`/api/reminders/${reminderId}`);
    const updated = await request(`/api/reminders/${reminderId}`, { method: 'PUT', body: { is_read: true } });
    const snoozed = await request(`/api/reminders/${reminderId}/snooze`, { method: 'PUT', body: { days: 1 } });
    const completedOne = await request(`/api/reminders/${reminderId}/complete`, { method: 'PUT' });
    const batchPut = await request('/api/reminders/batch', { method: 'PUT', body: { reminder_ids: [reminderId], is_read: true, priority: 'low' } });
    const batch = await request('/api/reminders/batch', { method: 'POST', body: { reminder_ids: [reminderId], action: 'complete' } });
    const stats = await request('/api/reminders/stats');
    const overdue = await request('/api/reminders/overdue');
    const deleted = await request(`/api/reminders/${reminderId}`, { method: 'DELETE' });
    return { payload: { created: created.data, list: list.data, detail: detail.data, updated: updated.data, snoozed: snoozed.data, completedOne: completedOne.data, batchPut: batchPut.data, batch: batch.data, stats: stats.data, overdue: overdue.data, deleted: deleted.data } };
  });
}

async function runReminderExtensionSuite() {
  const marker = `Bokai Audit Temp Case Reminder ${Date.now()}`;
  let tempCaseId;
  await step('reminders-extension-suite', 'tracking', async () => {
    tempCaseId = await createAuditTempCase(marker, '隔离临时案件，用于覆盖提醒扩展自动生成、全部已读和批量处理入口。');
    const generated = await request(`/api/reminders/auto-generate?case_id=${tempCaseId}`, { method: 'POST' });
    const ids = normalizeList(generated.data?.reminders).map((item) => item.id).filter(Boolean);
    const markAll = await request(`/api/reminders/mark-all-read?case_id=${tempCaseId}`, { method: 'PUT' });
    const batch = ids.length
      ? await request('/api/reminders/batch', { method: 'PUT', body: { reminder_ids: ids, is_read: true, is_completed: true, priority: 'low' } })
      : { data: { skipped: true, reason: 'no generated reminders' } };
    const maxReminderBefore = Number(String(await queryLocalAuditSql('select coalesce(max(id),0) from reminders;')).trim() || 0);
    const generatedAll = await request('/api/reminders/auto-generate-all', { method: 'POST' });
    const generatedAllCleanup = Number.isFinite(maxReminderBefore) && maxReminderBefore > 0
      ? await runLocalAuditSql(`delete from reminders where id > ${maxReminderBefore} and case_id <> ${Number(tempCaseId)};`)
      : { skipped: true };
    const cleanup = await cleanupTempCase(tempCaseId);
    tempCaseId = null;
    return {
      payload: { generated: generated.data, markAll: markAll.data, batch: batch.data, generatedAll: generatedAll.data, generatedAllCleanup, cleanup },
      detail: `generated=${ids.length} auto_all_total=${generatedAll.data?.total ?? 'ok'} cleanup=${cleanup?.stdout || 'done'} ${generatedAllCleanup?.stdout || ''}`,
    };
  });
  if (tempCaseId) {
    try {
      await cleanupTempCase(tempCaseId);
    } catch (error) {
      recordDefect('reminders-extension-suite-cleanup', 'P1', `提醒扩展临时案件清理失败：${formatError(error)}`);
    }
  }
}

async function runTimeControlSuite(caseId, ctx) {
  const letterId = ctx.representativeLetter?.id;
  await step('time-control-read-suite', 'time-control', async () => {
    const letters = await request(`/api/time-control/case/${caseId}/letters`);
    const deadlines = await request(`/api/time-control/case/${caseId}/deadlines`);
    const milestones = await request(`/api/time-control/case/${caseId}/milestones`);
    const urgency = await request(`/api/time-control/case/${caseId}/urgency-report`);
    const timeline = await request(`/api/time-control/case/${caseId}/timeline`);
    const checklist = await request(`/api/time-control/case/${caseId}/checklist`);
    const tracking = await request(`/api/time-control/case/${caseId}/mail-tracking`);
    const standard = await request('/api/time-control/standard-deadlines');
    const detail = letterId ? await request(`/api/time-control/letters/${letterId}`) : { data: null };
    return { payload: { letters: letters.data, deadlines: deadlines.data, milestones: milestones.data, urgency: urgency.data, timeline: timeline.data, checklist: checklist.data, tracking: tracking.data, standard: standard.data, letter_detail: detail.data }, detail: `letters=${normalizeList(letters.data).length} letter_id=${letterId || 'none'}` };
  });
  await runTimeControlMutationSuite(caseId);
  await runTimeControlIsolatedSuite();
}

async function cleanupTimeControlAudit(caseId) {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return { skipped: true };
  const sql = [
    `delete from letters where case_id = ${Number(caseId)} and title like 'Bokai Audit Time Letter %';`,
    `delete from legal_deadlines where case_id = ${Number(caseId)} and deadline_name like 'Bokai Audit Deadline %';`,
  ].join(' ');
  return runLocalAuditSql(sql);
}

async function runTimeControlMutationSuite(caseId) {
  const marker = Date.now();
  let createdLetterId;
  await step('time-control-mutation-suite', 'time-control', async () => {
    const created = await request(`/api/time-control/case/${caseId}/letters`, {
      method: 'POST',
      expected: [200, 201],
      timeoutMs: options.aiTimeoutMs,
      body: {
        '标题': `Bokai Audit Time Letter ${marker}`,
        '方向': 'outgoing',
        '类型': 'lawyer_letter',
        '文号': `AUDIT-${marker}`,
        '发送方': '陈靖/佛山吉麟',
        '接收方': '雷天乾/博凯健康',
        '函件日期': new Date().toISOString(),
        '截止日期': new Date(Date.now() + 3 * 86400000).toISOString(),
        '内容摘要': '审计临时时控函件，用于覆盖邮寄、送达、证明和回函文档接口。',
        '核心诉求': '确认合作关系、费用承担和停业责任。',
      },
    });
    createdLetterId = created.data?.id || created.data?.letter?.id;
    assert(createdLetterId, 'time-control letter create returned no id');

    const updated = await request(`/api/time-control/letters/${createdLetterId}`, {
      method: 'PUT',
      body: {
        title: `Bokai Audit Time Letter ${marker} Updated`,
        content_summary: '审计临时时控函件已更新。',
        reply_required: 'recommended',
        urgent_level: 'medium',
      },
    });
    const mailing = await request(`/api/time-control/letters/${createdLetterId}/mailing`, {
      method: 'POST',
      body: { '运单号': `SF${marker}`, '快递公司': '顺丰', '邮寄目的': '审计验证送达链路' },
    });
    const statusSent = await request(`/api/time-control/letters/${createdLetterId}/status`, {
      method: 'POST',
      body: { '状态': 'sent', '邮寄日期': new Date().toISOString(), '备注': '审计邮寄' },
    });
    const delivered = await request(`/api/time-control/letters/${createdLetterId}/delivered`, { method: 'POST' });
    const proof = await request(`/api/time-control/letters/${createdLetterId}/proof`, {
      method: 'POST',
      body: { '文件类型': 'delivery_receipt', '文件路径': `/tmp/bokai-audit-${marker}.png`, '描述': '审计临时送达证明' },
    });
    const proofList = await request(`/api/time-control/letters/${createdLetterId}/proof`);
    const replyDocument = await request(`/api/time-control/letters/${createdLetterId}/reply-document?document_name=${encodeURIComponent('审计回函附件')}&document_path=${encodeURIComponent(`/tmp/bokai-reply-${marker}.pdf`)}`, {
      method: 'POST',
    });
    const trackingStats = await request('/api/time-control/mail-tracking/stats');
    const pendingReplies = await request('/api/time-control/mail-tracking/pending-replies');

    const deadline = await request(`/api/time-control/case/${caseId}/deadlines`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        '期限类型': 'audit',
        '期限名称': `Bokai Audit Deadline ${marker}`,
        '分类': '审计',
        '法律依据': '民事诉讼法期限规则方向',
        '期限天数': 3,
        '说明': '审计临时期限制记录',
        '起算日期': new Date().toISOString(),
        '截止日期': new Date(Date.now() + 3 * 86400000).toISOString(),
        '是否强制': false,
        '可否展期': true,
        '关联事件': '审计验证',
      },
    });
    const deadlineId = deadline.data?.id || deadline.data?.deadline?.id;
    const deadlineUpdated = deadlineId ? await request(`/api/time-control/deadlines/${deadlineId}?status=${encodeURIComponent('completed')}`, { method: 'PUT' }) : { data: null };
    const cleanup = await cleanupTimeControlAudit(caseId);
    createdLetterId = null;
    return { payload: { created: created.data, updated: updated.data, mailing: mailing.data, statusSent: statusSent.data, delivered: delivered.data, proof: proof.data, proofList: proofList.data, replyDocument: replyDocument.data, trackingStats: trackingStats.data, pendingReplies: pendingReplies.data, deadline: deadline.data, deadlineUpdated: deadlineUpdated.data, cleanup }, detail: `letter=${created.data?.id || created.data?.letter?.id} deadline=${deadlineId || 'none'} cleanup=${cleanup?.stdout || 'done'}` };
  });
  if (createdLetterId) {
    try {
      await cleanupTimeControlAudit(caseId);
    } catch (error) {
      recordDefect('time-control-mutation-suite-cleanup', 'P1', `时控审计数据清理失败：${formatError(error)}`);
    }
  }
}

async function runTimeControlIsolatedSuite() {
  const marker = `Bokai Audit Temp Case Time ${Date.now()}`;
  let tempCaseId;
  await step('time-control-isolated-suite', 'time-control', async () => {
    tempCaseId = await createAuditTempCase(marker, '隔离临时案件，用于覆盖智能里程碑、时间线和函件发现入口。');
    const milestones = await request(`/api/time-control/case/${tempCaseId}/generate-milestones`, { method: 'POST', timeoutMs: options.aiTimeoutMs });
    const timelineCreated = await request(`/api/time-control/case/${tempCaseId}/timeline`, {
      method: 'POST',
      body: {
        '事件类型': 'audit',
        '事件名称': 'Bokai Audit Timeline Event',
        '事件日期': new Date().toISOString(),
        '事件描述': '审计临时时间线事件，随临时案件清理。',
        '重要性': 'normal',
        '是否里程碑': false,
      },
    });
    const timeline = await request(`/api/time-control/case/${tempCaseId}/timeline`);
    const discover = await request(`/api/time-control/case/${tempCaseId}/letters/discover`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      expected: [200, 500],
    });
    const discoveryStatus = await request(`/api/time-control/case/${tempCaseId}/letters/discovery-status`);
    const cleanup = await cleanupTempCase(tempCaseId);
    tempCaseId = null;
    const warnings = [];
    if (discover.response.status >= 500) warnings.push('函件发现接口在空临时案件上返回 500，需检查无函件/无证据时的降级处理。');
    return {
      payload: { milestones: milestones.data, timelineCreated: timelineCreated.data, timeline: timeline.data, discover: discover.data, discoveryStatus: discoveryStatus.data, cleanup },
      detail: `milestones=${normalizeList(milestones.data?.milestones).length || 'ok'} cleanup=${cleanup?.stdout || 'done'}`,
      warnings,
    };
  });
  if (tempCaseId) {
    try {
      await cleanupTempCase(tempCaseId);
    } catch (error) {
      recordDefect('time-control-isolated-suite-cleanup', 'P1', `时控临时案件清理失败：${formatError(error)}`);
    }
  }
}

async function runExecutionAppealFinanceSuites(caseId) {
  await step('execution-suite', 'execution', async () => {
    const priorTrackingIdText = await queryLocalAuditSql(`select id from execution_tracking where case_id = ${Number(caseId)} order by id asc limit 1;`);
    const priorTrackingId = Number(String(priorTrackingIdText || '').trim()) || null;
    const overview = await request(`/api/execution/case/${caseId}`);
    const original = overview.data || {};
    const updated = await request(`/api/execution/case/${caseId}`, {
      method: 'PUT',
      body: { execution_court: '审计临时法院', execution_amount: '0', status: 'preparing', progress: 5 },
    });
    const records = await request(`/api/execution/case/${caseId}/records`);
    const tasks = await request(`/api/execution/case/${caseId}/tasks`);
    const assets = await request(`/api/execution/case/${caseId}/assets`);
    const stats = await request(`/api/execution/case/${caseId}/statistics`);
    const discovered = await request(`/api/execution/case/${caseId}/discover-assets`);
    const marker = Date.now();
    const record = await request(`/api/execution/case/${caseId}/records`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        title: `Bokai Audit Execution Record ${marker}`,
        record_type: 'audit',
        content: '审计临时执行记录',
        court_name: '审计临时法院',
        progress: 1,
      },
    });
    const recordId = record.data?.id || record.data?.record?.id;
    const recordUpdated = recordId ? await request(`/api/execution/records/${recordId}`, { method: 'PUT', body: { result: '审计更新', progress: 2 } }) : { data: null };
    const task = await request(`/api/execution/case/${caseId}/tasks`, {
      method: 'POST',
      expected: [200, 201],
      body: { title: `Bokai Audit Execution Task ${marker}`, description: '审计临时任务', priority: 'low', status: 'todo' },
    });
    const taskId = task.data?.id || task.data?.task?.id;
    const taskUpdated = taskId ? await request(`/api/execution/tasks/${taskId}`, { method: 'PUT', body: { status: 'completed', notes: '审计更新' } }) : { data: null };
    const asset = await request(`/api/execution/case/${caseId}/assets`, {
      method: 'POST',
      expected: [200, 201],
      body: { asset_name: `Bokai Audit Execution Asset ${marker}`, asset_type: 'other', description: '审计临时财产线索', estimated_value: '0' },
    });
    const assetId = asset.data?.id || asset.data?.asset?.id;
    const legacyCreated = await request(`/api/case/${caseId}/execution`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        case_id: caseId,
        execution_type: 'audit',
        applicant: '陈靖/佛山吉麟',
        respondent: '雷天乾/博凯健康',
        apply_amount: 1,
        apply_date: new Date().toISOString().slice(0, 10),
        court: '审计临时执行法院',
        notes: `Bokai Audit Legacy Execution ${marker}`,
      },
    });
    const legacyId = legacyCreated.data?.id;
    const legacyDetail = legacyId ? await request(`/api/execution/${legacyId}`) : { data: null };
    const legacyUpdated = legacyId ? await request(`/api/execution/${legacyId}`, {
      method: 'PUT',
      body: { court: '审计临时执行法院更新', officer: '审计员', status: 'in_progress', notes: `Bokai Audit Legacy Execution Updated ${marker}` },
    }) : { data: null };
    const legacyAmount = legacyId ? await request(`/api/execution/${legacyId}/amount?executed_amount=1`, { method: 'POST' }) : { data: null };
    const recordDeleted = recordId ? await request(`/api/execution/records/${recordId}`, { method: 'DELETE' }) : { data: null };
    const taskDeleted = taskId ? await request(`/api/execution/tasks/${taskId}`, { method: 'DELETE' }) : { data: null };
    const assetDeleted = assetId ? await request(`/api/execution/assets/${assetId}`, { method: 'DELETE' }) : { data: null };
    const legacyCleanup = legacyId
      ? await runLocalAuditSql(`delete from execution_tracking where id = ${Number(legacyId)} and case_id = ${Number(caseId)};`)
      : { skipped: true };
    const restoreSql = priorTrackingId
      ? `update execution_tracking set execution_case_number = ${sqlStringOrNull(original.execution_case_number)}, execution_court = ${sqlStringOrNull(original.execution_court)}, execution_amount = ${sqlStringOrNull(original.execution_amount)}, executed_amount = ${sqlStringOrNull(original.executed_amount)}, remaining_amount = ${sqlStringOrNull(original.remaining_amount)}, status = ${sqlStringOrNull(original.status)}, progress = ${sqlNumberOrNull(original.progress)} where id = ${Number(priorTrackingId)} and case_id = ${Number(caseId)}; update cases set execution_status = ${sqlStringOrNull(original.status)}, execution_progress = ${sqlNumberOrNull(original.progress)} where id = ${Number(caseId)};`
      : `delete from execution_tracking where case_id = ${Number(caseId)} and execution_court like '审计临时%'; update cases set execution_status = NULL, execution_progress = NULL where id = ${Number(caseId)};`;
    const restored = await runLocalAuditSql(restoreSql);
    return { payload: { overview: overview.data, updated: updated.data, records: records.data, tasks: tasks.data, assets: assets.data, stats: stats.data, discovered: discovered.data, record: record.data, recordUpdated: recordUpdated.data, task: task.data, taskUpdated: taskUpdated.data, asset: asset.data, legacyCreated: legacyCreated.data, legacyDetail: legacyDetail.data, legacyUpdated: legacyUpdated.data, legacyAmount: legacyAmount.data, recordDeleted: recordDeleted.data, taskDeleted: taskDeleted.data, assetDeleted: assetDeleted.data, legacyCleanup, restored } };
  });
  await step('appeal-suite', 'appeal', async () => {
    const created = await request(`/api/appeal/case/${caseId}/appeals`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        appeal_type: 'first_to_second',
        appeal_reason: 'legal_error',
        original_court: '审计临时法院',
        appellant_name: '陈靖',
        appeal_facts: '审计临时上诉记录，核对系统功能。',
        appeal_requests: '撤销错误认定，依法支持合法请求。',
      },
    });
    const appealId = created.data?.id || created.data?.appeal?.id;
    const list = await request(`/api/appeal/case/${caseId}/appeals`);
    const stats = await request(`/api/appeal/case/${caseId}/statistics`);
    const detail = appealId ? await request(`/api/appeal/appeals/${appealId}`) : { data: null };
    const updated = appealId ? await request(`/api/appeal/appeals/${appealId}`, {
      method: 'PUT',
      body: { status: 'preparing', strategy: '审计临时二审策略更新' },
    }) : { data: null };
    const countdown = appealId ? await request(`/api/appeal/appeal/${appealId}/countdown`) : { data: null };
    const argument = await request(`/api/appeal/case/${caseId}/arguments`, {
      method: 'POST',
      expected: [200, 201],
      body: { appeal_record_id: appealId, title: '审计临时论点', description: '核对上诉论点功能', importance: 'low' },
    });
    const argumentId = argument.data?.id || argument.data?.argument?.id;
    const argumentsList = await request(`/api/appeal/case/${caseId}/arguments`);
    const argumentUpdated = argumentId ? await request(`/api/appeal/argument/${argumentId}`, { method: 'PUT', body: { status: 'reviewed', reasoning: '审计更新' } }) : { data: null };
    const deadline = appealId ? await request(`/api/appeal/appeal/${appealId}/deadlines`, {
      method: 'POST',
      expected: [200, 201],
      body: { deadline_type: 'audit', deadline_name: 'Bokai Audit Appeal Deadline', description: '审计临时期限制', is_mandatory: false },
    }) : { data: null };
    const deadlines = appealId ? await request(`/api/appeal/appeal/${appealId}/deadlines`) : { data: null };
    const document = appealId ? await request(`/api/appeal/appeal/${appealId}/documents`, {
      method: 'POST',
      expected: [200, 201],
      body: { document_type: 'audit', document_name: 'Bokai Audit Appeal Document', description: '审计临时材料', is_required: false },
    }) : { data: null };
    const documents = appealId ? await request(`/api/appeal/appeal/${appealId}/documents`) : { data: null };
    const strategy = appealId ? await request(`/api/appeal/appeal/${appealId}/strategy`, {
      method: 'POST',
      expected: [200, 201],
      body: { title: 'Bokai Audit Appeal Strategy', defense_reasoning: '审计临时二审策略', is_approved: false },
    }) : { data: null };
    const strategyRead = appealId ? await request(`/api/appeal/appeal/${appealId}/strategy`) : { data: null };
    const petition = appealId ? await request(`/api/appeal/appeal/${appealId}/generate-petition`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200, 500] }) : { data: null, response: { status: 0 } };
    const legacyAppeal = await request(`/api/case/${caseId}/appeal`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        case_id: caseId,
        appeal_type: 'first_to_second',
        reason: '审计临时旧版上诉记录',
        target_court: '审计临时中院',
        filing_date: new Date().toISOString().slice(0, 10),
        arguments: [{ title: '旧版接口审计论点', content: '核对旧版追踪 API 链路。' }],
        notes: 'Bokai Audit Legacy Appeal',
      },
    });
    const legacyAppealId = legacyAppeal.data?.id;
    const legacyAppealDetail = legacyAppealId ? await request(`/api/appeal/${legacyAppealId}`) : { data: null };
    const legacyAppealUpdated = legacyAppealId ? await request(`/api/appeal/${legacyAppealId}`, {
      method: 'PUT',
      body: { notes: 'Bokai Audit Legacy Appeal Updated', status: 'preparing' },
    }) : { data: null };
    const legacyCountdown = legacyAppealId ? await request(`/api/appeal/${legacyAppealId}/countdown`) : { data: null };
    const legacyDocument = legacyAppealId ? await request(`/api/appeal/${legacyAppealId}/generate-document`, { method: 'POST', expected: [200, 501] }) : { data: null };
    const legacyStatus = legacyAppealId ? await request(`/api/appeal/${legacyAppealId}/status?status=${encodeURIComponent('submitted')}`, { method: 'PUT' }) : { data: null };
    const legacyDeleted = legacyAppealId ? await request(`/api/appeal/${legacyAppealId}`, { method: 'DELETE' }) : { data: null };
    const argumentDeleted = argumentId ? await request(`/api/appeal/argument/${argumentId}`, { method: 'DELETE' }) : { data: null };
    const appealDeleted = appealId ? await request(`/api/appeal/appeals/${appealId}`, { method: 'DELETE' }) : { data: null };
    const warnings = [];
    if (petition.response.status >= 500) warnings.push('上诉状生成接口返回 500，需检查服务实现或提示词输入。');
    return { payload: { created: created.data, detail: detail.data, updated: updated.data, list: list.data, stats: stats.data, countdown: countdown.data, argument: argument.data, argumentsList: argumentsList.data, argumentUpdated: argumentUpdated.data, deadline: deadline.data, deadlines: deadlines.data, document: document.data, documents: documents.data, strategy: strategy.data, strategyRead: strategyRead.data, petition: petition.data, legacyAppeal: legacyAppeal.data, legacyAppealDetail: legacyAppealDetail.data, legacyAppealUpdated: legacyAppealUpdated.data, legacyCountdown: legacyCountdown.data, legacyDocument: legacyDocument.data, legacyStatus: legacyStatus.data, legacyDeleted: legacyDeleted.data, argumentDeleted: argumentDeleted.data, appealDeleted: appealDeleted.data }, warnings };
  });
  await step('finance-suite', 'finance', async () => {
    const overview = await request(`/api/finance/case/${caseId}`);
    const updated = await request(`/api/finance/case/${caseId}`, { method: 'PUT', body: { expected_recovery: 1200000, actual_recovery: 0, notes: '审计临时财务记录' } });
    const expense = await request(`/api/finance/case/${caseId}/expenses`, {
      method: 'POST',
      expected: [200, 201],
      body: { category: 'other', title: '审计临时费用', amount: 1, status: 'pending' },
    });
    const expenseId = expense.data?.id || expense.data?.expense?.id;
    const expenses = await request(`/api/finance/case/${caseId}/expenses`);
    const expenseUpdated = expenseId ? await request(`/api/finance/expenses/${expenseId}`, {
      method: 'PUT',
      body: { notes: '审计临时费用已更新', status: 'paid' },
    }) : { data: null };
    const stats = await request(`/api/finance/case/${caseId}/statistics`);
    const cost = await request(`/api/finance/case/${caseId}/cost-analysis`);
    const winRate = await request(`/api/finance/case/${caseId}/win-rate`);
    const assessment = await request(`/api/finance/case/${caseId}/win-rate`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200, 500] });
    const deleted = expenseId ? await request(`/api/finance/expenses/${expenseId}`, { method: 'DELETE' }) : { data: null };
    const warnings = [];
    if (assessment.response.status >= 500) warnings.push('胜率评估接口返回 500，需检查 AI 评估流程。');
    return { payload: { overview: overview.data, updated: updated.data, expense: expense.data, expenses: expenses.data, expenseUpdated: expenseUpdated.data, stats: stats.data, cost: cost.data, winRate: winRate.data, assessment: assessment.data, deleted: deleted.data }, warnings };
  });
}

async function runHearingCrudSuite(caseId) {
  let hearingId;
  await step('hearing-record-crud-suite', 'hearing', async () => {
    const created = await request(`/api/hearings/case/${caseId}/hearing`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        '庭审类型': 'other',
        '庭审日期': new Date().toISOString(),
        '地点': '审计临时法庭',
        '案号': `BOKAI-AUDIT-${Date.now()}`,
        '参会人员': [{ name: '陈靖', role: '原告' }, { name: '雷天乾', role: '被告' }],
      },
    });
    hearingId = created.data?.id || created.data?.hearing?.id;
    assert(hearingId, 'hearing create returned no id');
    const all = await request('/api/hearings');
    const list = await request(`/api/hearings/case/${caseId}/hearings`);
    const detail = await request(`/api/hearings/hearing/${hearingId}`);
    const status = await request(`/api/hearings/hearing/${hearingId}/status?status=${encodeURIComponent('in_progress')}`, { method: 'PUT' });
    const statement = await request(`/api/hearings/hearing/${hearingId}/statement`, {
      method: 'POST',
      expected: [200, 201],
      body: {
        '发言内容': '审计临时发言：对方称停业与其无关，我方要求其说明证据依据。',
        '讲话方角色': 'defendant_lawyer',
        '讲话人姓名': '雷天乾代理人',
        '发言类型': 'statement',
      },
    });
    const statements = await request(`/api/hearings/hearing/${hearingId}/statements`);
    const cleanup = /^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)
      ? await runLocalAuditSql(`delete from hearing_records where id = ${Number(hearingId)} and case_id = ${Number(caseId)} and location = '审计临时法庭';`)
      : { skipped: true };
    hearingId = null;
    return { payload: { created: created.data, all: all.data, list: list.data, detail: detail.data, status: status.data, statement: statement.data, statements: statements.data, cleanup }, detail: `hearing_id=${created.data?.id || created.data?.hearing?.id} cleanup=${cleanup?.stdout || 'done'}` };
  });
  if (hearingId) {
    try {
      await runLocalAuditSql(`delete from hearing_records where id = ${Number(hearingId)} and case_id = ${Number(caseId)} and location = '审计临时法庭';`);
    } catch (error) {
      recordDefect('hearing-record-crud-suite-cleanup', 'P1', `临时庭审记录清理失败：${formatError(error)}`);
    }
  }
}

async function cleanupHearingToolAudit(caseId) {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return { skipped: true };
  return runLocalAuditSql(`delete from case_speaking_strategies where case_id = ${Number(caseId)} and title like '庭审说话策略%';`);
}

async function runHearingToolSuite(caseId) {
  await step('hearing-tool-suite', 'hearing', async () => {
    const realtime = await request('/api/hearings/realtime-analysis', {
      method: 'POST',
      body: {
        '发言内容': '对方称博凯升华停业完全是经营困难，与雷天乾和博凯健康无关。',
        '讲话方角色': 'defendant_lawyer',
        '讲话人姓名': '对方代理人',
        '当前阶段': 'fact_investigation',
        '对话历史': [],
      },
      expected: [200],
    });
    const caseRealtime = await request(`/api/hearings/case/${caseId}/realtime-analysis`, {
      method: 'POST',
      body: {
        '发言内容': '对方要求我方先证明每一笔保证金和信息服务费的合同依据。',
        '讲话方角色': 'defendant_lawyer',
        '讲话人姓名': '对方代理人',
        '当前阶段': 'debate',
        '对话历史': [],
      },
      expected: [200],
    });
    const timing = await request('/api/hearings/evidence-timing', {
      method: 'POST',
      body: {
        '证据名称': '证据3《付款凭证-博凯升华向博凯药业》',
        '证据类型': '书证',
        '当前阶段': 'fact_investigation',
        '情境描述': '对方否认保证金和货款转化事实。',
        '讲话方角色': 'defendant_lawyer',
      },
    });
    const sequence = await request('/api/hearings/evidence-sequence', {
      method: 'POST',
      body: [
        { name: '证据1 董事会决议', type: '书证', importance: 'high' },
        { name: '证据3 付款凭证', type: '书证', importance: 'high' },
      ],
    });
    const closing = await request(`/api/hearings/case/${caseId}/closing-statement?庭审摘要=${encodeURIComponent('审计摘要：围绕停业责任、费用承担、证据闭环进行总结。')}`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200] });
    const counter = await request('/api/hearings/counter-argument', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: {
        '对方陈述': '陈靖和佛山吉麟没有完成出资，因此不能主张工资和费用。',
        '我方角色': '原告',
      },
      expected: [200],
    });
    const mediation = await request(`/api/hearings/case/${caseId}/mediation-strategy?我方底线=${encodeURIComponent('不得放弃工资社保、保证金和停业损失核心主张')}`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200] });
    const guides = await request('/api/hearings/speaking-guides');
    const guide = await request('/api/hearings/speaking-guide/1');
    const speakingStrategy = await request(`/api/hearings/case/${caseId}/speaking-strategy`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200] });
    const speakingStrategies = await request(`/api/hearings/case/${caseId}/speaking-strategies`);
    const meetingAnalyze = await request('/api/hearings/analyze', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: {
        case_id: caseId,
        language_input: '对方坚持称停业是商业判断，我方要求其说明董事会决议和资金流向。',
        context: '博凯升华案审计会议',
        meeting_type: '庭审准备',
        participants: '陈靖、代理律师',
        topic: '停业责任和费用承担',
      },
      expected: [200],
    });
    const responseStrategy = await request('/api/hearings/response-strategy', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: {
        question_or_statement: '你方是否承认未完成出资导致公司无法经营？',
        context: '博凯升华案庭审询问',
        speaker_role: 'defendant_lawyer',
      },
      expected: [200],
    });
    const meetingOpening = await request(`/api/hearings/opening-statement?case_id=${caseId}&hearing_type=${encodeURIComponent('一审')}`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200] });
    const meetingClosing = await request(`/api/hearings/closing-statement?case_id=${caseId}&hearing_type=${encodeURIComponent('一审')}`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200] });
    const meetingCross = await request(`/api/hearings/cross-examination?case_id=${caseId}&target_witness=${encodeURIComponent('雷天乾')}`, { method: 'POST', timeoutMs: options.aiTimeoutMs, expected: [200] });
    const cleanup = await cleanupHearingToolAudit(caseId);
    return {
      payload: { realtime: realtime.data, caseRealtime: caseRealtime.data, timing: timing.data, sequence: sequence.data, closing: closing.data, counter: counter.data, mediation: mediation.data, guides: guides.data, guide: guide.data, speakingStrategy: speakingStrategy.data, speakingStrategies: speakingStrategies.data, meetingAnalyze: meetingAnalyze.data, responseStrategy: responseStrategy.data, meetingOpening: meetingOpening.data, meetingClosing: meetingClosing.data, meetingCross: meetingCross.data, cleanup },
      detail: `guides=${normalizeList(guides.data).length || 'ok'} cleanup=${cleanup?.stdout || 'done'}`,
    };
  });
}

async function runEvidenceBasedAnalysis(caseId, ctx, evidenceText) {
  const started = await request(`/api/adversarial/case/${caseId}/evidence-based-analysis`, {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
    body: {
      '案件名称': ctx.case.title || '博凯升华违背合作案',
      '原告': ctx.case.plaintiff || '陈靖',
      '被告': ctx.case.defendant || '雷天乾',
      '案由': ctx.case.cause || '合作协议纠纷',
      '诉讼金额': String(ctx.case.claim_amount || ''),
      '案件描述': ctx.case.description || '',
      '我方证据': evidenceText,
      '对方名称': ctx.case.defendant || '雷天乾',
      '对方证据': '审计脚本未发现对方单独上传证据，需以已入库证据链和对方抗辩假设交叉校验。',
      '分析阶段': '诉前准备',
      '分析深度': '深度审计',
    },
  });

  const analysisId = started.data?.analysis_id || started.data?.id;
  if (!analysisId) return started;

  const deadline = Date.now() + options.aiTimeoutMs;
  let latest = started.data;
  while (Date.now() < deadline) {
    await sleep(5000);
    const progress = await request(`/api/adversarial/progress/${encodeURIComponent(analysisId)}`, {
      timeoutMs: options.timeoutMs,
    });
    latest = progress.data;
    console.log(`INFO evidence-based-analysis status=${latest?.status || 'unknown'} progress=${latest?.progress ?? ''}`);
    if (latest?.status === 'completed') {
      return { data: latest };
    }
    if (latest?.status === 'failed') {
      throw new Error(`evidence-based-analysis failed: ${latest.error || shortJson(latest)}`);
    }
  }
  throw new Error(`evidence-based-analysis did not complete within ${options.aiTimeoutMs}ms; latest=${shortJson(latest)}`);
}

async function runAiSuite(ctx) {
  const caseId = options.caseId;
  const evidenceText = ctx.usefulEvidence
    .slice(0, 12)
    .map((item, index) => `证据${index + 1}：${item.display_name || item.original_filename}\n${(item.raw_content || item.extracted_content || item.summary || '').slice(0, 1200)}`)
    .join('\n\n');
  const userQuestion = '我是陈靖/佛山吉麟一方。请基于博凯升华完整证据链，逐项判断合作出资、停业责任、工资社保、保证金和信息服务费等主张的胜算、证据缺口、对方可能抗辩和下一步行动。不要编造案例，所有事实必须引用证据。';

  await aiStep('smart-chat-global-analysis', 'ai-chat', () => request('/api/smart-chat/global-analysis', {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
    body: {
      case_id: caseId,
      fact_description: userQuestion,
      user_expectation: '希望得到可直接用于诉讼策略校准的深度分析',
      user_role: '原告/合作方代理律师',
      session_id: `bokai-audit-${runId}`,
    },
  }), { minChars: 1800, expectedEvidenceCount: ctx.evidenceCount });

  await aiStep('smart-chat-case-analysis', 'ai-chat', () => request('/api/smart-chat/case-analysis', {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
    body: {
      case_id: caseId,
      user_message: userQuestion,
      chat_history: [],
    },
  }), { minChars: 900, expectedEvidenceCount: ctx.evidenceCount });

  await runSmartChatWorkflowSuite(caseId, ctx.evidenceCount);

  await aiStep('assistant-chat', 'ai-chat', () => request('/api/v2/assistant/chat', {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
    body: {
      case_id: caseId,
      message: userQuestion,
      conversation_context: [],
    },
  }), { minChars: 900, expectedEvidenceCount: ctx.evidenceCount });

  await aiStep('senior-analysis-standard', 'ai-analysis', () => request('/api/v2/senior-analysis/analyze', {
    method: 'POST',
    timeoutMs: options.includeExpensive ? options.expensiveTimeoutMs : options.aiTimeoutMs,
    body: { case_id: caseId, analysis_level: options.includeExpensive ? 'deep' : 'standard' },
  }), { minChars: options.includeExpensive ? 1800 : 800, expectedEvidenceCount: ctx.evidenceCount });

  await aiStep('adversarial-opponent-analysis', 'ai-adversarial', () => request(`/api/adversarial/case/${caseId}/opponent-analysis`, {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
  }), { minChars: 1000 });
  await aiStep('adversarial-evidence-matrix', 'ai-adversarial', () => request(`/api/adversarial/case/${caseId}/evidence-matrix`, {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
  }), { minChars: 1000 });
  await aiStep('adversarial-scenario-prediction', 'ai-adversarial', () => request(`/api/adversarial/case/${caseId}/scenario-prediction`, {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
  }), { minChars: 1000 });
  await aiStep('adversarial-automated-plan', 'ai-adversarial', () => request(`/api/adversarial/case/${caseId}/automated-plan`, {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
  }), { minChars: 900 });

  await aiStep('evidence-based-analysis', 'ai-adversarial', () => runEvidenceBasedAnalysis(caseId, ctx, evidenceText), { minChars: 1200 });

  await runDocumentAiSuite(caseId);
  await runHearingAiSuite(caseId, evidenceText);
  await runTimeControlAiSuite(ctx);
  await runReportAiSuite(caseId);
  await aiStep('execution-generate-application', 'ai-execution', () => request(`/api/execution/case/${caseId}/generate-application`, {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
  }), { minChars: 900, expectedEvidenceCount: ctx.evidenceCount });

  if (options.includeExpensive) {
    await aiStep('adversarial-full-analysis', 'ai-adversarial-expensive', async () => {
      const response = await request(`/api/adversarial/case/${caseId}/full-analysis`, {
        method: 'POST',
        timeoutMs: options.expensiveTimeoutMs,
        body: {
          analysis_phase: 'pre_litigation',
          opponent_name: ctx.case.defendant || '雷天乾',
          opponent_type: '合作方/股东相关方',
          our_evidence: evidenceText,
        },
      });
      const analysisId = response.data?.analysis_id;
      if (analysisId) {
        response.audit_cleanup = await runLocalAuditSql(`delete from adversarial_analyses where id = ${Number(analysisId)} and case_id = ${Number(caseId)};`);
      }
      return response;
    }, { minChars: 1800 });
  }
  if (options.includeDebate) {
    await runDebateAudit(caseId);
  }
}

async function cleanupSmartChatAudit(caseId, sessionMarker, uploadFilename) {
  if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/i.test(options.baseUrl)) return { skipped: true };
  const sessionSafe = String(sessionMarker).replace(/'/g, "''");
  const fileSafe = String(uploadFilename || '').replace(/'/g, "''");
  const sql = [
    `delete from conversation_analyses where case_id = ${Number(caseId)} and session_id = '${sessionSafe}';`,
    fileSafe ? `delete from conversation_analyses where case_id = ${Number(caseId)} and summary like '证据分析: ${fileSafe}%';` : '',
    fileSafe ? `delete from evidence_items_v2 where case_id = ${Number(caseId)} and original_filename = '${fileSafe}';` : '',
  ].filter(Boolean).join(' ');
  return runLocalAuditSql(sql);
}

async function runSmartChatWorkflowSuite(caseId, expectedEvidenceCount) {
  const sessionMarker = `bokai-smart-flow-${runId}`;
  const uploadFilename = `bokai-smart-chat-audit-${Date.now()}.txt`;
  await step('smart-chat-workflow-suite', 'ai-chat', async () => {
    const seed = await request('/api/smart-chat/global-analysis', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: {
        case_id: caseId,
        fact_description: '审计：请基于博凯升华证据链识别停业责任和费用返还主线。',
        user_expectation: '用于确认智能对话状态流转',
        user_role: '原告代理律师',
        session_id: sessionMarker,
      },
    });
    const analysisId = seed.data?.analysis_id;
    assert(analysisId, 'smart-chat global-analysis returned no analysis_id');
    const follow = await request('/api/smart-chat/follow-up', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: {
        case_id: caseId,
        message: '请进一步说明对方可能如何抗辩177条证据链，并给出回应顺序。',
        session_id: sessionMarker,
      },
    });
    const followText = extractMainText(follow.data);
    const followQuality = assessAiText('smart-chat-follow-up', followText, { minChars: 900, expectedEvidenceCount });
    const followMd = join(aiDir, 'smart-chat-follow-up.md');
    await writeFile(followMd, `# smart-chat-follow-up\n\n${followText || '(empty output)'}\n`, 'utf8');
    const confirm = await request('/api/smart-chat/confirm-suggestion', {
      method: 'POST',
      body: { analysis_id: analysisId, confirmed_fields: {} },
    });
    const approve = await request(`/api/smart-chat/approve?analysis_id=${analysisId}&set_as_main_context=true`, { method: 'POST' });
    const analyses = await request(`/api/smart-chat/analyses/${caseId}`);
    const deleted = await request(`/api/smart-chat/delete?analysis_id=${analysisId}`, { method: 'POST' });

    const form = new FormData();
    form.append('case_id', String(caseId));
    form.append('user_message', '审计上传：验证智能对话上传分析链路，完成后清理。');
    form.append('file', new Blob(['博凯升华智能对话审计上传文件：验证上传分析入口。'], { type: 'text/plain' }), uploadFilename);
    const upload = await request('/api/smart-chat/upload-analysis', {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: form,
      expected: [200],
    });
    const cleanup = await cleanupSmartChatAudit(caseId, sessionMarker, uploadFilename);
    return {
      payload: { seed: seed.data, follow: follow.data, follow_quality: followQuality, follow_markdown: followMd, confirm: confirm.data, approve: approve.data, analyses: analyses.data, deleted: deleted.data, upload: upload.data, cleanup },
      detail: `analysis=${analysisId} upload_evidence=${upload.data?.evidence_id || 'none'} cleanup=${cleanup?.stdout || 'done'}`,
      warnings: followQuality.warnings,
    };
  }, { warningAsPass: false });
}

async function runDocumentAiSuite(caseId) {
  const requirements = '只围绕博凯升华合作纠纷；必须引用证据编号/名称；不得编造法院案号；诉讼请求需要区分合作出资、工资社保、保证金、信息服务费及停业损失。';
  await aiStep('documents-generate-complaint', 'ai-documents', () => request('/api/documents/generate', {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
    body: { case_id: caseId, document_type: '起诉状', custom_requirements: requirements },
  }), { minChars: 1400 });
  await aiStep('documents-generate-evidence-list', 'ai-documents', () => request('/api/documents/generate', {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
    body: { case_id: caseId, document_type: '证据目录', custom_requirements: requirements },
  }), { minChars: 900, legalBasis: false });
  await aiStep('smart-chat-generate-document', 'ai-documents', () => request('/api/smart-chat/generate-document', {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
    body: { case_id: caseId, document_type: '代理词', custom_requirements: requirements },
  }), { minChars: 1200 });
}

async function runHearingAiSuite(caseId, evidenceText) {
  await aiStep('hearing-opening-statement', 'ai-hearing', () => request(`/api/hearings/case/${caseId}/opening-statement`, {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
  }), { minChars: 700 });
  await aiStep('hearing-cross-examination', 'ai-hearing', () => request(`/api/hearings/case/${caseId}/cross-examination?证人姓名=${encodeURIComponent('雷天乾')}&证人角色=${encodeURIComponent('opponent_lawyer')}`, {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
  }), { minChars: 700 });
  await aiStep('hearing-realtime-analysis', 'ai-hearing', () => request(`/api/hearings/case/${caseId}/realtime-analysis`, {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
    body: {
      '发言内容': '对方称陈靖并未实际履行出资义务，佛山吉麟停业与博凯升华无关，相关工资和保证金主张没有合同依据。',
      '讲话方角色': 'opponent_lawyer',
      '当前阶段': '法庭调查',
      '对话历史': [{ role: 'context', content: evidenceText.slice(0, 1000) }],
    },
  }), { minChars: 700 });
  await aiStep('hearing-trap-detection', 'ai-hearing', () => request('/api/hearings/detect-trap', {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
    body: {
      statement: '你们是否承认没有正式股东会决议，所以陈靖所有款项都只是个人自愿垫付？',
      speaker_role: 'opponent_lawyer',
      case_id: caseId,
    },
  }), { minChars: 500 });
  await aiStep('hearing-negotiation-script', 'ai-hearing', () => request('/api/hearings/negotiation-script', {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
    body: {
      meeting_type: '诉前调解',
      our_position: '陈靖/佛山吉麟要求厘清合作出资、停业责任、费用垫付和应付款。',
      their_position: '博凯健康、雷天乾一方否认责任。',
      goals: '形成可执行的调解底线和让步方案。',
    },
  }), { minChars: 700 });
}

async function runTimeControlAiSuite(ctx) {
  const caseId = ctx.case?.id || options.caseId;
  let auditLetterId = null;
  await step('time-control-create-audit-letter', 'ai-time-control-precondition', async () => {
    const created = await request(`/api/time-control/case/${caseId}/letters`, {
      method: 'POST',
      expected: [200, 201],
      timeoutMs: 60000,
      body: {
        '标题': `博凯升华案AI审计临时函件-${runId}`,
        '方向': 'outgoing',
        '类型': 'lawyer_letter',
        '发送方': ctx.case?.plaintiff || '陈靖/佛山吉麟',
        '接收方': ctx.case?.defendant || '博凯升华/雷天乾',
        '函件日期': new Date().toISOString(),
        '内容摘要': '要求对方就合作出资、停业责任、工资社保、保证金、信息服务费及相关费用承担作出书面回应。',
        '核心诉求': '确认合作关系及费用承担，说明停业原因，限期支付或提出可核验的对账方案。',
      },
    });
    auditLetterId = created.data?.letter?.id || created.data?.id;
    assert(auditLetterId, `created audit letter did not return id: ${shortJson(created.data)}`);
    return { payload: created.data };
  });
  if (!auditLetterId) {
    recordDefect('time-control-ai-suite', 'P1', '临时审计函件创建失败，跳过函件 AI 后续步骤。');
    return;
  }

  try {
    await aiStep('time-control-generate-reply', 'ai-time-control', () => request(`/api/time-control/letters/${auditLetterId}/generate-reply`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
    }), { minChars: 700 });
    await step('time-control-register-reply-for-ai', 'ai-time-control-precondition', async () => {
      const registered = await request(`/api/time-control/letters/${auditLetterId}/reply`, {
        method: 'POST',
        timeoutMs: options.timeoutMs,
        body: {
          '是否收到回函': true,
          '回函类型': 'reject',
          '回函日期': new Date().toISOString(),
          '回函摘要': '对方否认停业责任，并称陈靖/佛山吉麟未完成出资，拒绝承担工资、保证金和信息服务费等责任。',
        },
      });
      return { payload: registered.data };
    });
    await aiStep('time-control-ai-analyze-reply', 'ai-time-control', () => request(`/api/time-control/letters/${auditLetterId}/ai-analyze-reply`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
    }), { minChars: 600 });
  } finally {
    if (auditLetterId) {
      await step('time-control-delete-audit-letter', 'cleanup', async () => {
        const deleted = await request(`/api/time-control/letters/${auditLetterId}`, {
          method: 'DELETE',
          timeoutMs: options.timeoutMs,
        });
        return { payload: deleted.data };
      }, { warningAsPass: true });
    }
  }
}

async function runReportAiSuite(caseId) {
  await aiStep('reports-quick-analysis', 'ai-reports', () => request(`/api/reports/quick-analysis/${caseId}`, {
    method: 'POST',
    timeoutMs: options.aiTimeoutMs,
  }), { minChars: 700 });
  if (options.includeExpensive) {
    await aiStep('reports-generate-analysis', 'ai-reports-expensive', () => request(`/api/reports/generate/${caseId}`, {
      method: 'POST',
      timeoutMs: options.expensiveTimeoutMs,
      body: { report_type: 'analysis', force_regenerate: true },
    }), { minChars: 1800 });
  }
}

async function runDebateAudit(caseId) {
  await aiStep('adversarial-real-debate', 'ai-adversarial-expensive', async () => {
    const started = await request(`/api/adversarial/case/${caseId}/debate-stream`, {
      method: 'POST',
      timeoutMs: options.aiTimeoutMs,
      body: { debate_rounds: 4, analysis_phase: 'pre_litigation' },
    });
    const debateId = started.data?.debate_id;
    assert(debateId, `debate did not return debate_id: ${shortJson(started.data)}`);
    const deadline = Date.now() + options.expensiveTimeoutMs;
    let latest = null;
    while (Date.now() < deadline) {
      await sleep(5000);
      const progress = await request(`/api/adversarial/debate/${encodeURIComponent(debateId)}/progress`, { timeoutMs: options.timeoutMs });
      latest = progress.data;
      const rounds = Array.isArray(latest?.rounds) ? latest.rounds.length : 0;
      console.log(`INFO debate-progress status=${latest?.status || 'unknown'} current_round=${latest?.current_round || 0} rounds=${rounds}`);
      if (latest?.status === 'completed') {
        const continued = await request(`/api/adversarial/debate/${encodeURIComponent(debateId)}/continue`, {
          method: 'POST',
          timeoutMs: options.aiTimeoutMs,
          body: { user_input: '请从用户视角总结这4轮辩论中我方最应补强的三个证据点，不得编造案号。' },
        });
        return { data: { ...latest, continued: continued.data } };
      }
      if (latest?.status === 'failed') {
        throw new Error(`debate failed: ${latest.error || shortJson(latest)}`);
      }
    }
    throw new Error(`debate did not complete within ${options.expensiveTimeoutMs}ms; latest=${shortJson(latest)}`);
  }, { minChars: 1800 });
}

async function runBrowserSuite(auth) {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  const serverErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('response', (response) => {
    if (response.url().startsWith(options.baseUrl) && response.status() >= 500) {
      serverErrors.push(`${response.status()} ${response.url()}`);
    }
  });

  const routeResults = [];
  try {
    await page.goto(`${options.baseUrl}/login`, { waitUntil: 'networkidle', timeout: BROWSER_TIMEOUT_MS });
    await page.locator('#username').fill(auth.username);
    await page.locator('#password').fill(auth.password);
    await Promise.all([
      page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: BROWSER_TIMEOUT_MS }),
      page.locator('button[type="submit"]').click(),
    ]);

    const routes = frontendRoutes(options.caseId);
    for (const route of routes) {
      const started = Date.now();
      const entry = { route, status: 'PASS', body_chars: 0, duration_ms: 0, screenshot: null, detail: '' };
      try {
        await page.goto(`${options.baseUrl}${route}`, { waitUntil: 'networkidle', timeout: BROWSER_TIMEOUT_MS });
        const path = new URL(page.url()).pathname;
        assert(!path.startsWith('/login'), `${route} redirected to login`);
        const body = await page.locator('body').innerText({ timeout: BROWSER_TIMEOUT_MS });
        entry.body_chars = body.trim().length;
        assert(entry.body_chars > 30, `${route} rendered too little text`);
        const screenshot = join(browserDir, `${slug(route)}.png`);
        await page.screenshot({ path: screenshot, fullPage: true });
        entry.screenshot = screenshot;
        entry.detail = `chars=${entry.body_chars}`;
      } catch (error) {
        entry.status = 'FAIL';
        entry.detail = formatError(error);
        recordDefect(`browser:${route}`, 'P1', entry.detail);
      } finally {
        entry.duration_ms = Date.now() - started;
        routeResults.push(entry);
        log(entry.status, `browser ${route}`, entry.detail);
      }
    }

    if (pageErrors.length) recordDefect('browser-page-errors', 'P1', pageErrors.slice(0, 5).join(' | '));
    if (serverErrors.length) recordDefect('browser-server-errors', 'P1', serverErrors.slice(0, 5).join(' | '));
    if (consoleErrors.length) recordDefect('browser-console-errors', 'P2', consoleErrors.slice(0, 5).join(' | '));
  } finally {
    await browser.close();
  }

  records.push({
    name: 'browser-route-walkthrough',
    category: 'browser',
    status: routeResults.some((item) => item.status === 'FAIL') ? 'FAIL' : 'PASS',
    started_at: new Date().toISOString(),
    duration_ms: routeResults.reduce((sum, item) => sum + item.duration_ms, 0),
    detail: `routes=${routeResults.length} failed=${routeResults.filter((item) => item.status === 'FAIL').length}`,
    warnings: [],
    artifact: join(artifactsDir, 'browser-route-walkthrough.json'),
  });
  await writeJson(join(artifactsDir, 'browser-route-walkthrough.json'), { routes: routeResults, pageErrors, consoleErrors, serverErrors });
}

function frontendRoutes(caseId) {
  return [
    '/dashboard',
    '/cases',
    `/cases/${caseId}`,
    `/cases/${caseId}/overview`,
    `/cases/${caseId}/parties`,
    `/cases/${caseId}/chat`,
    `/cases/${caseId}/evidence`,
    `/cases/${caseId}/documents`,
    `/cases/${caseId}/analysis`,
    `/cases/${caseId}/letters`,
    `/cases/${caseId}/profile`,
    `/cases/${caseId}/reports`,
    `/cases/${caseId}/folder`,
    `/cases/${caseId}/timeline`,
    `/cases/${caseId}/execution`,
    `/cases/${caseId}/appeal`,
    `/evidence-graph/${caseId}`,
    `/evidence-guide/${caseId}`,
    `/timeline/${caseId}`,
    `/documents/${caseId}`,
    `/adversarial/${caseId}`,
    `/senior-analysis/${caseId}`,
    `/hearing/${caseId}`,
    `/progress/${caseId}`,
    `/execution/${caseId}`,
    `/appeal/${caseId}`,
    `/qa/${caseId}`,
    `/meeting/${caseId}`,
    `/analysis-history/${caseId}`,
    `/smart-chat/${caseId}`,
    '/reminders',
    '/settings/api-keys',
  ];
}

function loadPlaywright() {
  try {
    return frontendRequire('playwright');
  } catch (error) {
    throw new Error(`Playwright is not installed under frontend/node_modules: ${formatError(error)}`);
  }
}

function coverageSummary() {
  const allOperations = [];
  for (const [path, operations] of Object.entries(openapiPaths)) {
    for (const method of Object.keys(operations)) {
      allOperations.push(`${method.toUpperCase()} ${path}`);
    }
  }
  const auditedPrefixes = [
    '/api/cases',
    '/api/claims',
    '/api/dashboard',
    '/api/reminders',
    '/api/v2/evidence-graph',
    '/api/v2/evidence-guide',
    '/api/v2/profile',
    '/api/documents',
    '/api/smart-chat',
    '/api/v2/assistant',
    '/api/v2/senior-analysis',
    '/api/adversarial',
    '/api/time-control',
    '/api/hearings',
    '/api/reports',
    '/api/execution',
    '/api/appeal',
    '/api/finance',
  ];
  const featureOps = allOperations.filter((op) => auditedPrefixes.some((prefix) => op.includes(` ${prefix}`)));
  const coveredShapes = new Set([...coveredOperations]);
  const uncovered = featureOps.filter((op) => !coveredShapes.has(op));
  return {
    total_openapi_operations: allOperations.length,
    audited_feature_operations: featureOps.length,
    directly_covered_operations: coveredShapes.size,
    uncovered_feature_operations: uncovered,
  };
}

async function writeSummary() {
  const counts = records.reduce((acc, item) => {
    acc[item.status] = (acc[item.status] || 0) + 1;
    return acc;
  }, {});
  const coverage = coverageSummary();
  const severe = defects.filter((item) => item.severity === 'P1');
  const quality = defects.filter((item) => item.severity !== 'P1');
  const lines = [];
  lines.push('# 博凯升华全功能审计报告');
  lines.push('');
  lines.push(`- 目标环境：${options.baseUrl}`);
  lines.push(`- 案件 ID：${options.caseId}`);
  lines.push(`- 输出目录：${outputDir}`);
  lines.push(`- 模式：${options.mode}`);
  lines.push(`- 长任务：${options.includeExpensive ? '已启用' : '未启用'}`);
  lines.push(`- 真实辩论：${options.includeDebate ? '已启用' : '未启用'}`);
  lines.push('');
  lines.push('## 结果概览');
  lines.push(`- PASS：${counts.PASS || 0}`);
  lines.push(`- WARN：${counts.WARN || 0}`);
  lines.push(`- FAIL：${counts.FAIL || 0}`);
  lines.push(`- 缺陷/疑点：${defects.length}`);
  lines.push(`- OpenAPI 功能操作覆盖：${coverage.directly_covered_operations}/${coverage.audited_feature_operations}（脚本会列出未直接覆盖项）`);
  lines.push('');
  if (severe.length) {
    lines.push('## 高优先级问题');
    for (const item of severe.slice(0, 30)) {
      lines.push(`- ${item.step}：${item.message}`);
    }
    lines.push('');
  }
  if (quality.length) {
    lines.push('## AI 输出质量/提示词疑点');
    for (const item of quality.slice(0, 50)) {
      lines.push(`- ${item.step}：${item.message}`);
    }
    lines.push('');
  }
  lines.push('## 未直接覆盖的功能入口');
  for (const op of coverage.uncovered_feature_operations.slice(0, 160)) {
    lines.push(`- ${op}`);
  }
  if (coverage.uncovered_feature_operations.length > 160) {
    lines.push(`- ... 另有 ${coverage.uncovered_feature_operations.length - 160} 项`);
  }
  lines.push('');
  lines.push('## 明细文件');
  lines.push('- `manifest.json`：每一步状态、耗时、产物路径');
  lines.push('- `ai-outputs/`：AI 原始 Markdown 输出');
  lines.push('- `artifacts/`：API JSON 原始响应和质量检查');
  lines.push('- `browser/`：前端页面截图');
  lines.push('');

  await writeFile(join(outputDir, 'summary.md'), `${lines.join('\n')}\n`, 'utf8');
  await writeJson(join(outputDir, 'manifest.json'), {
    options: { ...options, password: options.password ? '[redacted]' : '' },
    outputDir,
    records,
    defects,
    coverage,
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  await mkdir(outputDir, { recursive: true });
  await mkdir(artifactsDir, { recursive: true });
  await mkdir(aiDir, { recursive: true });
  await mkdir(browserDir, { recursive: true });

  console.log(`Bokai audit target: ${options.baseUrl}`);
  console.log(`Bokai audit output: ${outputDir}`);

  await loadOpenapi();
  let auth;
  await step('auth-register-login', 'auth', async () => {
    auth = await ensureAuth();
    defaultAuthToken = auth.token;
    return { payload: { username: auth.username, generated: auth.generated }, detail: `user=${auth.username}` };
  });
  let ctx;
  await step('bokai-context-load', 'setup', async () => {
    ctx = await buildContext(options.caseId);
    const warnings = [];
    if (!String(ctx.case?.title || '').includes('博凯')) warnings.push('目标案件标题不是博凯升华相关案件，请确认 case-id。');
    if (ctx.evidence.length < 100) warnings.push(`证据数量低于完整证据链预期：${ctx.evidence.length}`);
    if (ctx.letters.length < 20) warnings.push(`函件数量低于完整证据链预期：${ctx.letters.length}`);
    return {
      payload: {
        case: ctx.case,
        evidence_count: ctx.evidence.length,
        useful_evidence_count: ctx.usefulEvidence.length,
        representative_evidence: ctx.representativeEvidence,
        letters_count: ctx.letters.length,
        representative_letter: ctx.representativeLetter,
      },
      detail: `case=${ctx.case?.title || ''} evidence=${ctx.evidence.length} letters=${ctx.letters.length}`,
      warnings,
    };
  });

  if (options.mode === 'full' || options.mode === 'data') {
    await runSystemAndDataSuite(ctx, auth);
  }
  if (options.mode === 'full' || options.mode === 'ai') {
    await runAiSuite(ctx);
  }
  if ((options.mode === 'full' || options.mode === 'browser') && !options.skipBrowser) {
    await runBrowserSuite(auth);
  }

  await writeSummary();
  const failed = records.filter((item) => item.status === 'FAIL').length;
  const warned = records.filter((item) => item.status === 'WARN').length;
  console.log(`\nBokai audit complete: pass=${records.filter((item) => item.status === 'PASS').length} warn=${warned} fail=${failed}`);
  console.log(`Summary: ${join(outputDir, 'summary.md')}`);
  if (failed > 0) process.exitCode = 1;
}

main().catch(async (error) => {
  console.error(`FATAL ${formatError(error)}`);
  recordDefect('fatal', 'P1', formatError(error));
  try {
    await writeSummary();
  } catch {
    // ignore summary failures after fatal startup errors
  }
  process.exitCode = 1;
});
