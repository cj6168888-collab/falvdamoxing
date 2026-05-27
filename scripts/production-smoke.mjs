#!/usr/bin/env node
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const frontendRequire = createRequire(resolve(repoRoot, 'frontend', 'package.json'));

const DEFAULT_BASE_URL = 'http://localhost';
const DEFAULT_TIMEOUT_MS = 15000;
const BROWSER_TIMEOUT_MS = 30000;
const DEFAULT_DEBATE_TIMEOUT_MS = 900000;

function parseArgs(argv) {
  const options = {
    baseUrl: process.env.SMOKE_BASE_URL || DEFAULT_BASE_URL,
    username: process.env.SMOKE_USERNAME || '',
    password: process.env.SMOKE_PASSWORD || '',
    caseId: process.env.SMOKE_CASE_ID || '',
    debateRounds: numberFromEnv('SMOKE_DEBATE_ROUNDS', 4),
    debateTimeoutMs: numberFromEnv('SMOKE_DEBATE_TIMEOUT_MS', DEFAULT_DEBATE_TIMEOUT_MS),
    includeDebate: flagFromEnv('SMOKE_INCLUDE_DEBATE'),
    skipBrowser: flagFromEnv('SMOKE_SKIP_BROWSER'),
  };

  for (const arg of argv) {
    if (arg === '--include-debate') {
      options.includeDebate = true;
    } else if (arg === '--skip-browser') {
      options.skipBrowser = true;
    } else if (arg.startsWith('--base-url=')) {
      options.baseUrl = arg.slice('--base-url='.length);
    } else if (arg.startsWith('--username=')) {
      options.username = arg.slice('--username='.length);
    } else if (arg.startsWith('--password=')) {
      options.password = arg.slice('--password='.length);
    } else if (arg.startsWith('--case-id=')) {
      options.caseId = arg.slice('--case-id='.length);
    } else if (arg.startsWith('--debate-rounds=')) {
      options.debateRounds = Number(arg.slice('--debate-rounds='.length));
    } else if (arg.startsWith('--debate-timeout-ms=')) {
      options.debateTimeoutMs = Number(arg.slice('--debate-timeout-ms='.length));
    } else if (arg === '--help' || arg === '-h') {
      printUsage();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  options.baseUrl = options.baseUrl.replace(/\/+$/, '');
  assert(Number.isFinite(options.debateRounds) && options.debateRounds >= 1, 'debate rounds must be a positive number');
  assert(Number.isFinite(options.debateTimeoutMs) && options.debateTimeoutMs >= 60000, 'debate timeout must be at least 60000ms');
  return options;
}

function flagFromEnv(name) {
  return ['1', 'true', 'yes', 'on'].includes(String(process.env[name] || '').toLowerCase());
}

function numberFromEnv(name, fallback) {
  const raw = process.env[name];
  if (!raw) return fallback;
  const value = Number(raw);
  return Number.isFinite(value) ? value : fallback;
}

function printUsage() {
  console.log(`Production smoke test

Usage:
  node scripts/production-smoke.mjs [options]

Options:
  --base-url=http://localhost       Production base URL. Default: SMOKE_BASE_URL or http://localhost
  --username=name                   Existing account username. Default: SMOKE_USERNAME
  --password=password               Existing account password. Default: SMOKE_PASSWORD
  --case-id=1                       Existing case id. Default: SMOKE_CASE_ID or first available case
  --skip-browser                    Skip Playwright browser checks
  --include-debate                  Run the real LLM debate flow and poll completion
  --debate-rounds=4                 Requested debate rounds. Backend currently enforces at least 4
  --debate-timeout-ms=900000        Debate completion timeout when --include-debate is enabled
`);
}

const options = parseArgs(process.argv.slice(2));
const results = [];
let failureCount = 0;
let warningCount = 0;

function record(status, name, detail = '') {
  if (status === 'FAIL') {
    failureCount += 1;
  } else if (status === 'WARN') {
    warningCount += 1;
  }
  results.push({ status, name, detail });
  const prefix = status.padEnd(4);
  console.log(`${prefix} ${name}${detail ? ` - ${detail}` : ''}`);
}

async function step(name, fn) {
  try {
    const value = await fn();
    record('PASS', name, describeStepValue(name, value));
    return value;
  } catch (error) {
    record('FAIL', name, formatError(error));
    return undefined;
  }
}

function warn(name, detail) {
  record('WARN', name, detail);
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function formatError(error) {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

function shortJson(value) {
  const text = typeof value === 'string' ? value : JSON.stringify(value);
  return text.length > 260 ? `${text.slice(0, 260)}...` : text;
}

function describeStepValue(name, value) {
  if (value === undefined || value === null) return '';
  if (typeof value === 'string') return value;

  if (name === 'auth-login') {
    return `${value.generated ? 'registered' : 'existing'} user=${value.username}`;
  }
  if (name === 'case-resolution') {
    return `id=${value.id} title=${value.title || ''}`;
  }
  if (name === 'reminder-create') {
    return `id=${value.id} title=${value.title || ''}`;
  }

  return shortJson(value);
}

async function request(path, init = {}) {
  const {
    method = 'GET',
    body,
    token,
    expected = [200],
    timeoutMs = DEFAULT_TIMEOUT_MS,
  } = init;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const headers = {
    Accept: 'application/json',
    ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init.headers || {}),
  };

  try {
    const response = await fetch(`${options.baseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
    const text = await response.text();
    const data = parseJson(text);

    if (!expected.includes(response.status)) {
      throw new Error(`${method} ${path} returned ${response.status}: ${shortJson(data ?? text)}`);
    }

    return { response, data, text };
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`${method} ${path} timed out after ${timeoutMs}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function parseJson(text) {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function normalizeCaseList(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.cases)) return payload.cases;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (payload?.id) return [payload];
  return [];
}

async function verifyHealth() {
  const health = await request('/health');
  assert(health.data?.status === 'healthy', `/health status is ${shortJson(health.data)}`);

  const ready = await request('/ready');
  assert(ready.data?.status === 'ready', `/ready status is ${shortJson(ready.data)}`);

  return 'health=healthy ready=ready';
}

async function verifyRouterStatus() {
  const status = await request('/api/llm/router/status', { expected: [200, 503] });
  assert(status.data?.status, `unexpected router status payload ${shortJson(status.data)}`);
  if (status.response.status !== 200 || status.data.status === 'degraded') {
    warn('llm-router', shortJson(status.data));
  }
  return `status=${status.data.status}`;
}

async function verifyThirdPartyHealth() {
  const health = await request('/api/third-party/health', { expected: [200, 503] });
  assert(health.data && typeof health.data === 'object', 'third-party health did not return JSON');
  if (health.response.status !== 200 || health.data.status === 'degraded') {
    warn('third-party-health', shortJson(health.data));
  }
  return `status=${health.data.status || health.response.status}`;
}

async function ensureAuth() {
  let username = options.username;
  let password = options.password;

  if ((username && !password) || (!username && password)) {
    throw new Error('SMOKE_USERNAME and SMOKE_PASSWORD must be provided together');
  }

  if (!username) {
    const suffix = Date.now();
    username = `smoke_${suffix}`;
    password = `Smoke-${suffix}!`;
    const registered = await request('/api/auth/register', {
      method: 'POST',
      expected: [200, 201],
      body: {
        username,
        email: `${username}@codexsmoke.dev`,
        password,
        full_name: 'Production Smoke User',
        tenant_name: `Production Smoke Tenant ${suffix}`,
        tenant_type: 'law_firm',
        role: 'assistant',
      },
    });
    assert(registered.data?.tokens?.access_token, 'registration did not return an access token');
  }

  const login = await request('/api/auth/login', {
    method: 'POST',
    body: { username, password },
  });
  const token = login.data?.tokens?.access_token;
  assert(token, 'login did not return an access token');

  return { username, password, token, generated: !options.username };
}

async function resolveCase() {
  if (options.caseId) {
    const response = await request(`/api/cases/${encodeURIComponent(options.caseId)}`);
    assert(response.data?.id, `case ${options.caseId} was not found`);
    return response.data;
  }

  const response = await request('/api/cases');
  const cases = normalizeCaseList(response.data);
  if (cases.length > 0) {
    const selected = cases[0];
    assert(selected.id, `first case did not contain id: ${shortJson(selected)}`);
    return selected;
  }

  const created = await request('/api/cases', {
    method: 'POST',
    body: {
      title: `Smoke Case ${Date.now()}`,
      case_type: 'civil',
      plaintiff: 'Smoke Plaintiff',
      defendant: 'Smoke Defendant',
      cause: 'Production smoke test',
      description: 'Created by scripts/production-smoke.mjs because no case existed.',
    },
  });
  assert(created.data?.id, `case creation did not return id: ${shortJson(created.data)}`);
  warn('case-created', `created smoke case id=${created.data.id}; no delete API is available`);
  return created.data;
}

async function createReminder(caseId) {
  const title = `Smoke Reminder ${Date.now()}`;
  const response = await request('/api/reminders', {
    method: 'POST',
    expected: [200, 201],
    body: {
      case_id: Number(caseId),
      title,
      content: 'Production smoke reminder lifecycle check',
      priority: 'low',
      reminder_type: 'deadline',
      trigger_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      is_read: false,
      is_completed: false,
    },
  });
  assert(response.data?.id, `created reminder did not contain id: ${shortJson(response.data)}`);
  assert(response.data.title === title, `created reminder title mismatch: ${shortJson(response.data)}`);
  return response.data;
}

async function verifyReminderLifecycle(reminderId) {
  const read = await request(`/api/reminders/${reminderId}`, {
    method: 'PUT',
    body: { is_read: true },
  });
  assert(read.data?.is_read === true, 'single reminder update did not mark is_read=true');

  const batch = await request('/api/reminders/batch', {
    method: 'POST',
    body: { reminder_ids: [reminderId], action: 'complete' },
  });
  assert(batch.data?.success === true, `batch operation failed: ${shortJson(batch.data)}`);
  assert(Number(batch.data?.processed) >= 1, `batch processed count was ${shortJson(batch.data?.processed)}`);

  const fetched = await request(`/api/reminders/${reminderId}`);
  assert(fetched.data?.is_completed === true, 'batch operation did not mark is_completed=true');

  const stats = await request('/api/reminders/stats');
  assert(typeof stats.data?.total === 'number', `reminder stats total is invalid: ${shortJson(stats.data)}`);

  const overdue = await request('/api/reminders/overdue');
  assert(overdue.data !== null, 'overdue endpoint returned an empty response');

  return `id=${reminderId} stats.total=${stats.data.total}`;
}

async function deleteReminder(reminderId) {
  const response = await request(`/api/reminders/${reminderId}`, {
    method: 'DELETE',
    expected: [200, 204],
  });
  if (response.response.status !== 204) {
    assert(response.data?.deleted === true, `delete response was ${shortJson(response.data)}`);
  }
}

async function verifyBrowserFlow(auth, caseData, reminder) {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  const pageErrors = [];
  const serverErrors = [];
  const consoleErrors = [];

  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text());
    }
  });
  page.on('response', (response) => {
    const url = response.url();
    if (url.startsWith(options.baseUrl) && response.status() >= 500) {
      serverErrors.push(`${response.status()} ${url}`);
    }
  });

  try {
    await page.goto(`${options.baseUrl}/login`, { waitUntil: 'networkidle', timeout: BROWSER_TIMEOUT_MS });
    await page.locator('#username').fill(auth.username);
    await page.locator('#password').fill(auth.password);
    await Promise.all([
      page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: BROWSER_TIMEOUT_MS }),
      page.locator('button[type="submit"]').click(),
    ]);
    await page.waitForLoadState('networkidle', { timeout: BROWSER_TIMEOUT_MS });
    assert(!new URL(page.url()).pathname.startsWith('/login'), 'login did not leave /login');

    await verifyBrowserPage(page, '/dashboard');
    await verifyBrowserPage(page, `/cases/${caseData.id}`);
    await verifyBrowserPage(page, `/adversarial/${caseData.id}`);
    await verifyBrowserPage(page, '/reminders');
    await page.getByText(reminder.title, { exact: false }).waitFor({ timeout: BROWSER_TIMEOUT_MS });

    if (pageErrors.length > 0) {
      throw new Error(`browser page errors: ${pageErrors.slice(0, 3).join(' | ')}`);
    }
    if (serverErrors.length > 0) {
      throw new Error(`browser observed server errors: ${serverErrors.slice(0, 3).join(' | ')}`);
    }
    if (consoleErrors.length > 0) {
      warn('browser-console-errors', consoleErrors.slice(0, 3).join(' | '));
    }
  } finally {
    await browser.close();
  }

  return `dashboard/case/adversarial/reminders OK`;
}

async function verifyBrowserPage(page, path) {
  await page.goto(`${options.baseUrl}${path}`, { waitUntil: 'networkidle', timeout: BROWSER_TIMEOUT_MS });
  const currentPath = new URL(page.url()).pathname;
  assert(!currentPath.startsWith('/login'), `${path} redirected to login`);
  const bodyText = await page.locator('body').innerText({ timeout: BROWSER_TIMEOUT_MS });
  assert(bodyText.trim().length > 40, `${path} rendered too little text`);
}

function loadPlaywright() {
  try {
    return frontendRequire('playwright');
  } catch (error) {
    throw new Error(`Playwright is not installed under frontend/node_modules: ${formatError(error)}`);
  }
}

async function verifyDebate(caseId) {
  const started = await request(`/api/adversarial/case/${caseId}/debate-stream`, {
    method: 'POST',
    body: { debate_rounds: options.debateRounds },
    timeoutMs: DEFAULT_TIMEOUT_MS,
  });
  const debateId = started.data?.debate_id;
  assert(debateId, `debate did not return debate_id: ${shortJson(started.data)}`);

  const deadline = Date.now() + options.debateTimeoutMs;
  let latest = null;
  let lastProgressKey = '';
  while (Date.now() < deadline) {
    await sleep(4000);
    const progress = await request(`/api/adversarial/debate/${encodeURIComponent(debateId)}/progress`, {
      timeoutMs: DEFAULT_TIMEOUT_MS,
    });
    latest = progress.data;
    const roundCount = Array.isArray(latest?.rounds) ? latest.rounds.length : 0;
    const progressKey = `${latest?.status || 'unknown'}:${latest?.current_round || 0}:${roundCount}`;
    if (progressKey !== lastProgressKey) {
      console.log(`INFO real-debate-progress - status=${latest?.status || 'unknown'} current_round=${latest?.current_round || 0} rounds=${roundCount}`);
      lastProgressKey = progressKey;
    }
    if (latest?.status === 'completed') {
      assert(roundCount >= 4, `completed debate has only ${roundCount} rounds`);
      assert(latest.analysis_id, 'completed debate did not persist analysis_id');
      return `debate_id=${debateId} rounds=${roundCount} analysis_id=${latest.analysis_id}`;
    }
    if (latest?.status === 'failed') {
      throw new Error(`debate failed: ${latest.error || shortJson(latest)}`);
    }
  }

  throw new Error(`debate did not complete within ${options.debateTimeoutMs}ms; latest=${shortJson(latest)}`);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  console.log(`Production smoke target: ${options.baseUrl}`);

  await step('system-health', verifyHealth);
  await step('llm-router-status', verifyRouterStatus);
  await step('third-party-health', verifyThirdPartyHealth);

  const auth = await step('auth-login', ensureAuth);
  const caseData = await step('case-resolution', resolveCase);
  let reminder = null;

  if (auth && caseData) {
    reminder = await step('reminder-create', () => createReminder(caseData.id));
    if (reminder) {
      await step('reminder-lifecycle', () => verifyReminderLifecycle(reminder.id));
    }
  }

  if (auth && caseData && reminder && !options.skipBrowser) {
    await step('browser-flow', () => verifyBrowserFlow(auth, caseData, reminder));
  }

  if (caseData && options.includeDebate && failureCount === 0) {
    await step('real-debate-flow', () => verifyDebate(caseData.id));
  } else if (options.includeDebate && failureCount > 0) {
    warn('real-debate-flow', 'skipped because earlier smoke checks failed');
  } else if (!options.includeDebate) {
    warn('real-debate-flow', 'skipped; pass --include-debate to run model-consuming debate smoke');
  }

  if (reminder?.id) {
    await step('reminder-cleanup', () => deleteReminder(reminder.id));
  }

  console.log('');
  console.log(`Summary: ${results.length - failureCount - warningCount} passed, ${warningCount} warnings, ${failureCount} failed`);
  if (failureCount > 0) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  record('FAIL', 'smoke-runner', formatError(error));
  console.log('');
  console.log(`Summary: ${results.length - failureCount - warningCount} passed, ${warningCount} warnings, ${failureCount} failed`);
  process.exitCode = 1;
});
