import { test, expect } from '@playwright/test';
import type { ConsoleMessage, Page, Request, Response } from '@playwright/test';
import { mockApi } from './fixtures';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPORT_DIR = path.join(__dirname, '../test-output/detailed-audit');
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5174';

if (!fs.existsSync(REPORT_DIR)) {
  fs.mkdirSync(REPORT_DIR, { recursive: true });
}

type AuditResult = {
  testName: string;
  url: string;
  pageTitle: string;
  isBlank: boolean;
  consoleErrors: string[];
  consoleWarnings: string[];
  failedRequests: string[];
  apiCalls: { url: string; status: number; method: string }[];
  bodyTextPreview: string;
  bodyTextLength: number;
  errorElements: string[];
  loadingCount: number;
  hasGarbled: boolean;
  buttonTexts: string[];
  inputInfo: string[];
  brokenImages: string[];
  hasChinese: boolean;
  hasHardcodedMock: boolean;
};

const results: AuditResult[] = [];

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

async function auditPage(page: Page, testName: string, url: string) {
  const consoleErrors: string[] = [];
  const consoleWarnings: string[] = [];
  const failedRequests: string[] = [];
  const apiCalls: { url: string; status: number; method: string }[] = [];

  page.on('console', (msg: ConsoleMessage) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
    if (msg.type() === 'warning') consoleWarnings.push(msg.text());
  });

  page.on('requestfailed', (req: Request) => {
    failedRequests.push(`${req.url()} - ${req.failure()?.errorText || 'unknown'}`);
  });

  page.on('response', (resp: Response) => {
    if (resp.url().includes('/api/') || resp.url().includes('.ts') || resp.url().includes('.tsx')) {
      apiCalls.push({ url: resp.url(), status: resp.status(), method: resp.request().method() });
    }
    if (resp.status() >= 400 && !resp.url().includes('node_modules')) {
      failedRequests.push(`${resp.url()} - ${resp.status()}`);
    }
  });

  await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);

  const pageTitle = await page.title();
  const bodyText = await page.locator('body').innerText();

  // Check for blank page
  const isBlank = bodyText.trim().length < 50;

  // Check for error indicators in DOM
  const errorElements = await page.locator('[class*="error"], [class*="Error"], [role="alert"]').all();
  const errorTexts: string[] = [];
  for (const el of errorElements) {
    try {
      const t = await el.innerText();
      if (t.trim()) errorTexts.push(t.trim().substring(0, 200));
    } catch {
      continue;
    }
  }

  // Check for loading states
  const loadingCount = await page.locator('[class*="loading"], [class*="Loading"], [class*="spinner"], [class*="Skeleton"]').count();

  // Check for garbled text
  const hasGarbled = /[\ufffd]|\\u[0-9a-f]{4}/.test(bodyText);

  // Get all visible buttons and links
  const buttons = await page.locator('button:visible, a:visible, [role="button"]:visible').all();
  const buttonTexts: string[] = [];
  for (const btn of buttons.slice(0, 30)) {
    try {
      const t = (await btn.innerText()).trim();
      if (t && t.length > 0 && t.length < 100) buttonTexts.push(t);
    } catch {
      continue;
    }
  }

  // Get all input fields
  const inputs = await page.locator('input:visible, textarea:visible, select:visible').all();
  const inputInfo: string[] = [];
  for (const inp of inputs) {
    try {
      const type = await inp.getAttribute('type') || 'text';
      const placeholder = await inp.getAttribute('placeholder') || '';
      const name = await inp.getAttribute('name') || '';
      inputInfo.push(`${type} name="${name}" placeholder="${placeholder}"`);
    } catch {
      continue;
    }
  }

  // Get all images and check for broken ones
  const images = await page.locator('img').all();
  const brokenImages: string[] = [];
  for (const img of images) {
    const naturalWidth = await img.evaluate((el) => (el as HTMLImageElement).naturalWidth);
    if (naturalWidth === 0) {
      const src = await img.getAttribute('src') || '';
      brokenImages.push(src);
    }
  }

  // Check for specific content patterns
  const hasChinese = /[\u4e00-\u9fa5]/.test(bodyText);
  const hasHardcodedMock = /测试数据|mock|dummy|lorem ipsum/i.test(bodyText);

  const result = {
    testName,
    url,
    pageTitle,
    isBlank,
    consoleErrors: consoleErrors.slice(0, 20),
    consoleWarnings: consoleWarnings.slice(0, 20),
    failedRequests: failedRequests.slice(0, 20),
    apiCalls: apiCalls.slice(0, 20),
    bodyTextPreview: bodyText.substring(0, 1000),
    bodyTextLength: bodyText.length,
    errorElements: errorTexts,
    loadingCount,
    hasGarbled,
    buttonTexts: [...new Set(buttonTexts)],
    inputInfo,
    brokenImages,
    hasChinese,
    hasHardcodedMock,
  };

  results.push(result);

  // Save detailed report
  const reportPath = path.join(REPORT_DIR, `${testName.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(result, null, 2), 'utf-8');

  // Save full page screenshot
  await page.screenshot({ path: path.join(REPORT_DIR, `${testName.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}.png`), fullPage: true });

  return result;
}

async function login(page: Page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'password');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(2000);
}

test.describe('Detailed Page Audit', () => {
  test('01 - Login Page', async ({ page }) => {
    const r = await auditPage(page, '01_Login', `${BASE_URL}/login`);
    expect(r.isBlank).toBe(false);
    expect(r.consoleErrors.length).toBe(0);
  });

  test('02 - Dashboard', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '02_Dashboard', `${BASE_URL}/dashboard`);
    expect(r.isBlank).toBe(false);
    console.log('Dashboard text preview:', r.bodyTextPreview.substring(0, 500));
  });

  test('03 - Cases List', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '03_Cases_List', `${BASE_URL}/cases`);
    console.log('Cases list text:', r.bodyTextPreview.substring(0, 500));
    console.log('API calls:', JSON.stringify(r.apiCalls));
    console.log('Failed requests:', r.failedRequests);
    console.log('Console errors:', r.consoleErrors);
  });

  test('04 - New Case', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '04_New_Case', `${BASE_URL}/cases/new`);
    expect(r.isBlank).toBe(false);
    console.log('New case inputs:', r.inputInfo);
    console.log('New case buttons:', r.buttonTexts);
  });

  test('05 - Case Detail Overview', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '05_Case_Detail_Overview', `${BASE_URL}/cases/1`);
    console.log('Case detail blank:', r.isBlank);
    console.log('Case detail text:', r.bodyTextPreview.substring(0, 500));
    console.log('Console errors:', r.consoleErrors);
    console.log('Failed requests:', r.failedRequests);
    console.log('API calls:', JSON.stringify(r.apiCalls));
  });

  test('06 - Case Parties', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '06_Case_Parties', `${BASE_URL}/cases/1/parties`);
    console.log('Parties blank:', r.isBlank);
    console.log('Parties text:', r.bodyTextPreview.substring(0, 500));
    console.log('Console errors:', r.consoleErrors);
    console.log('Failed requests:', r.failedRequests);
    console.log('API calls:', JSON.stringify(r.apiCalls));
  });

  test('07 - Case Chat', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '07_Case_Chat', `${BASE_URL}/cases/1/chat`);
    console.log('Chat blank:', r.isBlank);
    console.log('Chat text:', r.bodyTextPreview.substring(0, 500));
    console.log('Console errors:', r.consoleErrors);
    console.log('Failed requests:', r.failedRequests);
    console.log('API calls:', JSON.stringify(r.apiCalls));
  });

  test('08 - Case Evidence', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '08_Case_Evidence', `${BASE_URL}/cases/1/evidence`);
    console.log('Evidence blank:', r.isBlank);
    console.log('Evidence text:', r.bodyTextPreview.substring(0, 500));
    console.log('Console errors:', r.consoleErrors);
    console.log('Failed requests:', r.failedRequests);
    console.log('API calls:', JSON.stringify(r.apiCalls));
  });

  test('09 - Case Documents', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '09_Case_Documents', `${BASE_URL}/cases/1/documents`);
    console.log('Documents blank:', r.isBlank);
    console.log('Documents text:', r.bodyTextPreview.substring(0, 500));
    console.log('Console errors:', r.consoleErrors);
    console.log('Failed requests:', r.failedRequests);
    console.log('API calls:', JSON.stringify(r.apiCalls));
  });

  test('10 - Case Analysis', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '10_Case_Analysis', `${BASE_URL}/cases/1/analysis`);
    console.log('Analysis blank:', r.isBlank);
    console.log('Analysis text:', r.bodyTextPreview.substring(0, 500));
    console.log('Console errors:', r.consoleErrors);
    console.log('Failed requests:', r.failedRequests);
    console.log('API calls:', JSON.stringify(r.apiCalls));
  });

  test('11 - Case Profile', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '11_Case_Profile', `${BASE_URL}/cases/1/profile`);
    console.log('Profile blank:', r.isBlank);
    console.log('Profile text:', r.bodyTextPreview.substring(0, 500));
    console.log('Console errors:', r.consoleErrors);
    console.log('Failed requests:', r.failedRequests);
    console.log('API calls:', JSON.stringify(r.apiCalls));
  });

  test('12 - Case Reports', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '12_Case_Reports', `${BASE_URL}/cases/1/reports`);
    console.log('Reports blank:', r.isBlank);
    console.log('Reports text:', r.bodyTextPreview.substring(0, 500));
    console.log('Console errors:', r.consoleErrors);
    console.log('Failed requests:', r.failedRequests);
    console.log('API calls:', JSON.stringify(r.apiCalls));
  });

  test('13 - Case Letters', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '13_Case_Letters', `${BASE_URL}/cases/1/letters`);
    console.log('Letters blank:', r.isBlank);
    console.log('Letters text:', r.bodyTextPreview.substring(0, 500));
    console.log('Console errors:', r.consoleErrors);
    console.log('Failed requests:', r.failedRequests);
    console.log('API calls:', JSON.stringify(r.apiCalls));
  });

  test('14 - Evidence Graph', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '14_Evidence_Graph', `${BASE_URL}/evidence-graph/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('15 - Evidence Guide', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '15_Evidence_Guide', `${BASE_URL}/evidence-guide/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('16 - Timeline', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '16_Timeline', `${BASE_URL}/timeline/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('17 - Documents Generator', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '17_Documents_Generator', `${BASE_URL}/documents/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('18 - Adversarial', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '18_Adversarial', `${BASE_URL}/adversarial/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('19 - Senior Analysis', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '19_Senior_Analysis', `${BASE_URL}/senior-analysis/1`);
    expect(r.isBlank).toBe(false);
  });

  test('20 - Hearing', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '20_Hearing', `${BASE_URL}/hearing/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('21 - Progress', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '21_Progress', `${BASE_URL}/progress/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('22 - Execution', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '22_Execution', `${BASE_URL}/execution/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('23 - Appeal', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '23_Appeal', `${BASE_URL}/appeal/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('24 - Q&A', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '24_QA', `${BASE_URL}/qa/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('25 - Meeting', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '25_Meeting', `${BASE_URL}/meeting/case-1`);
    expect(r.isBlank).toBe(false);
  });

  test('26 - Reminders', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '26_Reminders', `${BASE_URL}/reminders`);
    expect(r.isBlank).toBe(false);
  });

  test('27 - Case Folder', async ({ page }) => {
    await login(page);
    const r = await auditPage(page, '27_Case_Folder', `${BASE_URL}/cases/1/folder`);
    console.log('Folder blank:', r.isBlank);
    console.log('Folder text:', r.bodyTextPreview.substring(0, 500));
    console.log('Console errors:', r.consoleErrors);
    console.log('Failed requests:', r.failedRequests);
    console.log('API calls:', JSON.stringify(r.apiCalls));
    expect(r.isBlank).toBe(false);
  });

  // Final summary
  test('99 - Generate Summary Report', async () => {
    const summary = {
      total: results.length,
      blankPages: results.filter(r => r.isBlank).map(r => r.testName),
      pagesWithConsoleErrors: results.filter(r => r.consoleErrors.length > 0).map(r => ({ name: r.testName, errors: r.consoleErrors })),
      pagesWithFailedRequests: results.filter(r => r.failedRequests.length > 0).map(r => ({ name: r.testName, requests: r.failedRequests })),
      pagesWithGarbledText: results.filter(r => r.hasGarbled).map(r => r.testName),
      pagesWithBrokenImages: results.filter(r => r.brokenImages.length > 0).map(r => ({ name: r.testName, images: r.brokenImages })),
      pagesWithLoading: results.filter(r => r.loadingCount > 3).map(r => ({ name: r.testName, count: r.loadingCount })),
      allResults: results,
    };

    const summaryPath = path.join(REPORT_DIR, 'SUMMARY.json');
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2), 'utf-8');

    console.log('\n========== TEST SUMMARY ==========');
    console.log(`Total pages tested: ${summary.total}`);
    console.log(`Blank pages: ${summary.blankPages.length}`);
    if (summary.blankPages.length > 0) console.log('  -', summary.blankPages.join(', '));
    console.log(`Pages with console errors: ${summary.pagesWithConsoleErrors.length}`);
    console.log(`Pages with failed requests: ${summary.pagesWithFailedRequests.length}`);
    console.log(`Pages with garbled text: ${summary.pagesWithGarbledText.length}`);
    console.log(`Pages with broken images: ${summary.pagesWithBrokenImages.length}`);
    console.log(`Pages with excessive loading: ${summary.pagesWithLoading.length}`);
    console.log('===================================');
  });
});
