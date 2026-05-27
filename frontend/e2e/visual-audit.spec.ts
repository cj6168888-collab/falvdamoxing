import { test, expect } from '@playwright/test';
import type { ConsoleMessage, Page, Request } from '@playwright/test';
import { mockApi } from './fixtures';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SCREENSHOT_DIR = path.join(__dirname, '../test-output/visual-audit');
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5174';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const issues: { page: string; type: string; detail: string }[] = [];

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

async function screenshot(page: Page, name: string) {
  const filePath = path.join(SCREENSHOT_DIR, `${name}.png`);
  await page.screenshot({ path: filePath, fullPage: true });
  return filePath;
}

async function checkPageHealth(page: Page, pageName: string) {
  const healthIssues: string[] = [];

  // Check blank page
  const bodyText = await page.locator('body').innerText();
  if (bodyText.trim().length < 50) {
    healthIssues.push('页面完全空白（<50字符）');
    issues.push({ page: pageName, type: 'blank', detail: `body text length: ${bodyText.trim().length}` });
  }

  // Check console errors
  page.on('console', (msg: ConsoleMessage) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (!text.includes('favicon') && !text.includes('ERR_ABORTED') && !text.includes('404')) {
        healthIssues.push(`Console Error: ${text.substring(0, 200)}`);
        issues.push({ page: pageName, type: 'console-error', detail: text.substring(0, 200) });
      }
    }
  });

  // Check failed requests
  page.on('requestfailed', (req: Request) => {
    const url = req.url();
    if (url.includes('/api/') && !url.includes('favicon')) {
      healthIssues.push(`API Request Failed: ${url.substring(0, 150)}`);
      issues.push({ page: pageName, type: 'api-failed', detail: url.substring(0, 150) });
    }
  });

  // Check for error indicators in DOM
  const errorTexts = await page.locator('[class*="error"], [class*="Error"], [role="alert"]').allTextContents();
  for (const t of errorTexts) {
    if (t.trim() && t.length > 5 && t.length < 500) {
      healthIssues.push(`Error Element: ${t.trim().substring(0, 200)}`);
      issues.push({ page: pageName, type: 'error-element', detail: t.trim().substring(0, 200) });
    }
  }

  return healthIssues;
}

async function clickAllButtons(page: Page, pageName: string, maxClicks = 15) {
  const clicked: string[] = [];
  const buttons = await page.locator('button:visible, a:visible, [role="button"]:visible, [class*="tab"]:visible').all();

  for (let i = 0; i < Math.min(buttons.length, maxClicks); i++) {
    try {
      const btn = page.locator('button:visible, a:visible, [role="button"]:visible, [class*="tab"]:visible').nth(i);
      const text = (await btn.innerText()).trim().substring(0, 80);
      if (!text || text.length < 1) continue;
      if (text.includes('退出') || text.includes('登出') || text === '登录') continue;

      const isVisible = await btn.isVisible().catch(() => false);
      if (!isVisible) continue;

      await btn.click({ timeout: 3000 });
      await page.waitForTimeout(800);
      clicked.push(text);

      // Screenshot after click
      const safeName = text.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '').substring(0, 30);
      if (safeName) {
        await screenshot(page, `${pageName}-click-${safeName}`);
      }
    } catch {
      // Button may have caused navigation or modal
    }
  }

  return clicked;
}

async function login(page: Page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'password');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);
}

// ==================== TESTS ====================

test.describe('Visual Audit - Login', () => {
  test('01 - Login Page', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await screenshot(page, '01-login');

    const health = await checkPageHealth(page, 'Login');
    expect(await page.locator('input[name="username"]').isVisible()).toBe(true);
    expect(await page.locator('input[name="password"]').isVisible()).toBe(true);
    expect(await page.locator('button[type="submit"]').isVisible()).toBe(true);
    console.log('Login health:', health);
  });
});

test.describe('Visual Audit - After Login', () => {
  test('02 - Dashboard', async ({ page }) => {
    await login(page);
    await screenshot(page, '02-dashboard');
    const health = await checkPageHealth(page, 'Dashboard');
    const bodyText = await page.locator('body').innerText();
    console.log('Dashboard content preview:', bodyText.substring(0, 300));
    console.log('Dashboard health:', health);
    expect(bodyText.length).toBeGreaterThan(100);
  });

  test('03 - Cases List', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await screenshot(page, '03-cases-list');
    const health = await checkPageHealth(page, 'Cases List');
    const bodyText = await page.locator('body').innerText();
    console.log('Cases list content:', bodyText.substring(0, 300));
    console.log('Cases list health:', health);

    const clicked = await clickAllButtons(page, 'cases-list', 3);
    console.log('Cases list clicked:', clicked);
  });

  test('04 - New Case', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/new`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await screenshot(page, '04-new-case');
    const health = await checkPageHealth(page, 'New Case');
    console.log('New case health:', health);
    expect(await page.locator('body').innerText()).not.toBe('');
  });

  test('05 - Case Detail Overview', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/1/overview`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '05-case-overview');
    const health = await checkPageHealth(page, 'Case Overview');
    const bodyText = await page.locator('body').innerText();
    console.log('Case overview content:', bodyText.substring(0, 300));
    console.log('Case overview health:', health);
    expect(bodyText.length).toBeGreaterThan(100);
  });

  test('06 - Case Parties', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/1/parties`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await screenshot(page, '06-case-parties');
    const health = await checkPageHealth(page, 'Case Parties');
    console.log('Case parties health:', health);
  });

  test('07 - Case Chat', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/1/chat`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await screenshot(page, '07-case-chat');
    const health = await checkPageHealth(page, 'Case Chat');
    console.log('Case chat health:', health);
  });

  test('08 - Case Evidence', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/1/evidence`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '08-case-evidence');
    const health = await checkPageHealth(page, 'Case Evidence');
    const bodyText = await page.locator('body').innerText();
    console.log('Evidence content:', bodyText.substring(0, 300));
    console.log('Evidence health:', health);
  });

  test('09 - Case Documents', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/1/documents`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '09-case-documents');
    const health = await checkPageHealth(page, 'Case Documents');
    const bodyText = await page.locator('body').innerText();
    console.log('Documents content:', bodyText.substring(0, 500));
    console.log('Documents health:', health);

    const clicked = await clickAllButtons(page, 'case-documents', 10);
    console.log('Documents clicked:', clicked);
  });

  test('10 - Case Analysis', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/1/analysis`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await screenshot(page, '10-case-analysis');
    const health = await checkPageHealth(page, 'Case Analysis');
    console.log('Case analysis health:', health);
  });

  test('11 - Case Profile', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/1/profile`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await screenshot(page, '11-case-profile');
    const health = await checkPageHealth(page, 'Case Profile');
    console.log('Case profile health:', health);
  });

  test('12 - Case Reports', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/1/reports`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await screenshot(page, '12-case-reports');
    const health = await checkPageHealth(page, 'Case Reports');
    console.log('Case reports health:', health);
  });

  test('13 - Case Letters', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/1/letters`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await screenshot(page, '13-case-letters');
    const health = await checkPageHealth(page, 'Case Letters');
    console.log('Case letters health:', health);
  });

  test('14 - Case Folder', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/cases/1/folder`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '14-case-folder');
    const health = await checkPageHealth(page, 'Case Folder');
    const bodyText = await page.locator('body').innerText();
    console.log('Folder content:', bodyText.substring(0, 300));
    console.log('Folder health:', health);
  });

  test('15 - Evidence Graph', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/evidence-graph/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '15-evidence-graph');
    const health = await checkPageHealth(page, 'Evidence Graph');
    console.log('Evidence graph health:', health);
  });

  test('16 - Evidence Guide', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/evidence-guide/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '16-evidence-guide');
    const health = await checkPageHealth(page, 'Evidence Guide');
    console.log('Evidence guide health:', health);
  });

  test('17 - Timeline', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/timeline/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '17-timeline');
    const health = await checkPageHealth(page, 'Timeline');
    console.log('Timeline health:', health);
  });

  test('18 - Documents Generator', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/documents/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '18-documents-generator');
    const health = await checkPageHealth(page, 'Documents Generator');
    console.log('Documents generator health:', health);
  });

  test('19 - Adversarial', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/adversarial/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '19-adversarial');
    const health = await checkPageHealth(page, 'Adversarial');
    console.log('Adversarial health:', health);
  });

  test('20 - Senior Analysis', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/senior-analysis/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '20-senior-analysis');
    const health = await checkPageHealth(page, 'Senior Analysis');
    console.log('Senior analysis health:', health);
  });

  test('21 - Hearing', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/hearing/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '21-hearing');
    const health = await checkPageHealth(page, 'Hearing');
    console.log('Hearing health:', health);
  });

  test('22 - Progress', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/progress/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '22-progress');
    const health = await checkPageHealth(page, 'Progress');
    console.log('Progress health:', health);
  });

  test('23 - Execution', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/execution/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '23-execution');
    const health = await checkPageHealth(page, 'Execution');
    console.log('Execution health:', health);
  });

  test('24 - Appeal', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/appeal/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '24-appeal');
    const health = await checkPageHealth(page, 'Appeal');
    console.log('Appeal health:', health);
  });

  test('25 - Q&A', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/qa/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '25-qa');
    const health = await checkPageHealth(page, 'Q&A');
    console.log('Q&A health:', health);
  });

  test('26 - Meeting', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/meeting/1`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '26-meeting');
    const health = await checkPageHealth(page, 'Meeting');
    console.log('Meeting health:', health);
  });

  test('27 - Reminders', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/reminders`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    await screenshot(page, '27-reminders');
    const health = await checkPageHealth(page, 'Reminders');
    console.log('Reminders health:', health);
  });

  test('99 - Generate Issues Report', async () => {
    const reportPath = path.join(SCREENSHOT_DIR, 'ISSUES.json');
    fs.writeFileSync(reportPath, JSON.stringify(issues, null, 2), 'utf-8');

    console.log('\n========== VISUAL AUDIT SUMMARY ==========');
    console.log(`Total pages tested: 27`);
    console.log(`Total issues found: ${issues.length}`);

    if (issues.length > 0) {
      const byType: Record<string, number> = {};
      const byPage: Record<string, number> = {};
      for (const issue of issues) {
        byType[issue.type] = (byType[issue.type] || 0) + 1;
        byPage[issue.page] = (byPage[issue.page] || 0) + 1;
      }
      console.log('\nIssues by type:');
      for (const [type, count] of Object.entries(byType)) {
        console.log(`  ${type}: ${count}`);
      }
      console.log('\nIssues by page:');
      for (const [page, count] of Object.entries(byPage)) {
        console.log(`  ${page}: ${count}`);
      }
      console.log('\nDetailed issues:');
      for (const issue of issues) {
        console.log(`  [${issue.type}] ${issue.page}: ${issue.detail}`);
      }
    } else {
      console.log('No issues found! All pages are healthy.');
    }
    console.log('===========================================');
  });
});
