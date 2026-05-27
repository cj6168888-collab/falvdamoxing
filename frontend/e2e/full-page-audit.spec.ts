import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import { mockApi } from './fixtures';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SCREENSHOT_DIR = path.join(__dirname, '../test-output/full-audit');
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5174';

test.setTimeout(90000);

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function screenshot(page: Page, name: string) {
  const filePath = path.join(SCREENSHOT_DIR, `${name}.png`);
  await page.screenshot({ path: filePath, fullPage: true });
  console.log(`Screenshot saved: ${filePath}`);
  return filePath;
}

async function checkPageHealth(page: Page): Promise<{ errors: string[]; warnings: string[] }> {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check for blank page
  const bodyText = await page.locator('body').innerText();
  if (bodyText.trim().length === 0) {
    errors.push('页面完全空白，没有任何内容');
  }

  // Check for error messages in the page
  const errorElements = await page.locator('[class*="error"], [class*="Error"], [class*="alert-danger"], [class*="toast-error"]').count();
  if (errorElements > 0) {
    const errorTexts = await page.locator('[class*="error"], [class*="Error"], [class*="alert-danger"]').allTextContents();
    errors.push(`页面包含错误提示: ${errorTexts.join('; ')}`);
  }

  // Check for loading spinners stuck
  const loadingElements = await page.locator('[class*="loading"], [class*="spinner"], [class*="Loading"]').count();
  if (loadingElements > 5) {
    warnings.push(`页面有 ${loadingElements} 个加载指示器，可能卡住`);
  }

  // Check for garbled text
  const hasGarbled = await page.evaluate(() => {
    const body = document.body.innerText;
    // Check for common garbled patterns
    const garbledPatterns = [/\ufffd/g, /\\u[0-9a-fA-F]{4}/g, /%[0-9a-fA-F]{2}%[0-9a-fA-F]{2}/g];
    for (const pattern of garbledPatterns) {
      if (pattern.test(body)) return true;
    }
    return false;
  });
  if (hasGarbled) {
    errors.push('页面存在乱码');
  }

  return { errors, warnings };
}

async function clickAllButtons(page: Page, _pageName: string): Promise<{ clicked: string[]; errors: string[] }> {
  const clicked: string[] = [];
  const errors: string[] = [];

  // Get all buttons
  const interactiveSelector = 'main button, main [role="button"], main a[href]';
  const buttons = await page.locator(interactiveSelector).all();
  const maxButtons = Math.min(buttons.length, 30); // Limit to avoid infinite loops

  for (let i = 0; i < maxButtons; i++) {
    try {
      const btn = page.locator(interactiveSelector).nth(i);
      const text = (await btn.innerText()).trim().substring(0, 50);
      const isVisible = await btn.isVisible().catch(() => false);

      if (isVisible && text && text.length > 0) {
        // Don't click logout or navigation that would leave the page
        if (text.includes('退出') || text.includes('登出') || text === '登录') {
          continue;
        }

        try {
          await btn.click({ timeout: 3000 });
          await page.waitForTimeout(1000);
          clicked.push(text);
        } catch (e) {
          // Button might have caused navigation or modal
          const message = e instanceof Error ? e.message : String(e);
          if (!message.includes('navigation')) {
            errors.push(`按钮 "${text}" 点击失败: ${message.substring(0, 100)}`);
          }
        }
      }
    } catch (e) {
      // Skip inaccessible elements
    }
  }

  return { clicked, errors };
}

test.describe('Full Page Audit - Login', () => {
  test('01 - Login Page', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');

    // Screenshot
    await screenshot(page, '01-login-page');

    // Check page health
    const health = await checkPageHealth(page);
    console.log('Login page health:', JSON.stringify(health));

    // Verify login form elements
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    // Check for demo credentials text
    const demoText = await page.locator('text=admin').count();
    console.log('Demo credentials visible:', demoText > 0);

    expect(health.errors.length).toBe(0);
  });
});

test.describe('Full Page Audit - After Login', () => {
  test.use({ storageState: undefined });

  test('02 - Login and Dashboard', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await screenshot(page, '02-dashboard');

    const health = await checkPageHealth(page);
    console.log('Dashboard health:', JSON.stringify(health));

    // Check dashboard content
    const bodyText = await page.locator('body').innerText();
    console.log('Dashboard content preview:', bodyText.substring(0, 500));

    expect(bodyText.length).toBeGreaterThan(100);
  });

  test('03 - Sidebar Navigation Items', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Expand sidebar if collapsed
    const sidebar = page.locator('[class*="sidebar"], aside');
    await sidebar.hover();
    await page.waitForTimeout(500);

    await screenshot(page, '03-sidebar-expanded');

    // Get all sidebar nav items
    const navItems = page.locator('nav a, nav button, aside a, aside button');
    const count = await navItems.count();
    console.log(`Found ${count} navigation items`);

    for (let i = 0; i < count; i++) {
      const item = navItems.nth(i);
      const text = (await item.innerText()).trim().substring(0, 80);
      if (text) {
        console.log(`Nav item ${i}: ${text}`);
      }
    }
  });

  test('04 - Case Management Page', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Navigate to cases
    await page.goto(`${BASE_URL}/cases`);
    await page.waitForTimeout(3000);

    await screenshot(page, '04-cases-list');

    const health = await checkPageHealth(page);
    console.log('Cases page health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Cases page content:', bodyText.substring(0, 500));

    // Click all buttons on cases page
    const { clicked, errors } = await clickAllButtons(page, 'cases');
    console.log('Clicked buttons:', clicked);
    console.log('Button errors:', errors);

    await screenshot(page, '04-cases-after-clicks');
  });

  test('05 - New Case Page', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/cases/new`);
    await page.waitForTimeout(3000);

    await screenshot(page, '05-new-case');

    const health = await checkPageHealth(page);
    console.log('New case page health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('New case content:', bodyText.substring(0, 500));

    expect(health.errors.length).toBe(0);
  });

  test('06 - Reminders Page', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/reminders`);
    await page.waitForTimeout(3000);

    await screenshot(page, '06-reminders');

    const health = await checkPageHealth(page);
    console.log('Reminders page health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Reminders content:', bodyText.substring(0, 500));
  });
});

test.describe('Full Page Audit - Case Detail Pages', () => {
  test('07 - Case Detail Overview', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // First, get a case ID from the cases list
    await page.goto(`${BASE_URL}/cases`);
    await page.waitForTimeout(3000);

    // Try to find and click a case card
    const caseCards = page.locator('[class*="card"], [class*="Card"]').first();
    const cardCount = await caseCards.count();
    console.log(`Found ${cardCount} case cards`);

    // Navigate to case-1 as fallback
    await page.goto(`${BASE_URL}/cases/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '07-case-detail-overview');

    const health = await checkPageHealth(page);
    console.log('Case detail health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Case detail content:', bodyText.substring(0, 500));

    // Re-query role tabs before each click; route changes can invalidate nth() locators.
    const tabCount = await page.locator('[role="tab"]').count();
    console.log(`Found ${tabCount} tabs`);

    for (let i = 0; i < Math.min(tabCount, 10); i++) {
      try {
        await page.goto(`${BASE_URL}/cases/case-1`, { waitUntil: 'domcontentloaded', timeout: 10000 });
        const tabs = page.locator('[role="tab"]');
        const tab = tabs.nth(i);
        const tabText = (await tab.innerText()).trim().substring(0, 50);
        if (!tabText) {
          continue;
        }
        console.log(`Clicking tab: ${tabText}`);
        await tab.click({ timeout: 3000 });
        await page.waitForTimeout(1000);
        await screenshot(page, `07-tab-${tabText.replace(/[^a-zA-Z\u4e00-\u9fa5]/g, '')}`);
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        console.log(`Tab click error: ${message.substring(0, 100)}`);
      }
    }
  });

  test('08 - Case Parties', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/cases/case-1/parties`);
    await page.waitForTimeout(3000);

    await screenshot(page, '08-case-parties');

    const health = await checkPageHealth(page);
    console.log('Case parties health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Parties content:', bodyText.substring(0, 500));
  });

  test('09 - Case Chat', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/cases/case-1/chat`);
    await page.waitForTimeout(3000);

    await screenshot(page, '09-case-chat');

    const health = await checkPageHealth(page);
    console.log('Case chat health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Chat content:', bodyText.substring(0, 500));
  });

  test('10 - Case Evidence', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/cases/case-1/evidence`);
    await page.waitForTimeout(3000);

    await screenshot(page, '10-case-evidence');

    const health = await checkPageHealth(page);
    console.log('Case evidence health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Evidence content:', bodyText.substring(0, 500));
  });

  test('11 - Case Documents', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/cases/case-1/documents`);
    await page.waitForTimeout(3000);

    await screenshot(page, '11-case-documents');

    const health = await checkPageHealth(page);
    console.log('Case documents health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Documents content:', bodyText.substring(0, 500));
  });

  test('12 - Case Analysis', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/cases/case-1/analysis`);
    await page.waitForTimeout(3000);

    await screenshot(page, '12-case-analysis');

    const health = await checkPageHealth(page);
    console.log('Case analysis health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Analysis content:', bodyText.substring(0, 500));
  });

  test('13 - Case Profile', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/cases/case-1/profile`);
    await page.waitForTimeout(3000);

    await screenshot(page, '13-case-profile');

    const health = await checkPageHealth(page);
    console.log('Case profile health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Profile content:', bodyText.substring(0, 500));
  });

  test('14 - Case Reports', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/cases/case-1/reports`);
    await page.waitForTimeout(3000);

    await screenshot(page, '14-case-reports');

    const health = await checkPageHealth(page);
    console.log('Case reports health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Reports content:', bodyText.substring(0, 500));
  });

  test('15 - Case Letters', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/cases/case-1/letters`);
    await page.waitForTimeout(3000);

    await screenshot(page, '15-case-letters');

    const health = await checkPageHealth(page);
    console.log('Case letters health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Letters content:', bodyText.substring(0, 500));
  });
});

test.describe('Full Page Audit - Special Pages', () => {
  test('16 - Evidence Graph', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/evidence-graph/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '16-evidence-graph');

    const health = await checkPageHealth(page);
    console.log('Evidence graph health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Evidence graph content:', bodyText.substring(0, 500));
  });

  test('17 - Evidence Guide', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/evidence-guide/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '17-evidence-guide');

    const health = await checkPageHealth(page);
    console.log('Evidence guide health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Evidence guide content:', bodyText.substring(0, 500));
  });

  test('18 - Timeline', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/timeline/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '18-timeline');

    const health = await checkPageHealth(page);
    console.log('Timeline health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Timeline content:', bodyText.substring(0, 500));
  });

  test('19 - Documents Generator', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/documents/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '19-documents-generator');

    const health = await checkPageHealth(page);
    console.log('Documents generator health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Documents generator content:', bodyText.substring(0, 500));
  });

  test('20 - Adversarial Analysis', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/adversarial/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '20-adversarial');

    const health = await checkPageHealth(page);
    console.log('Adversarial health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Adversarial content:', bodyText.substring(0, 500));
  });

  test('21 - Senior Analysis', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/senior-analysis/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '21-senior-analysis');

    const health = await checkPageHealth(page);
    console.log('Senior analysis health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Senior analysis content:', bodyText.substring(0, 500));
  });

  test('22 - Hearing', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/hearing/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '22-hearing');

    const health = await checkPageHealth(page);
    console.log('Hearing health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Hearing content:', bodyText.substring(0, 500));
  });

  test('23 - Progress', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/progress/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '23-progress');

    const health = await checkPageHealth(page);
    console.log('Progress health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Progress content:', bodyText.substring(0, 500));
  });

  test('24 - Execution', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/execution/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '24-execution');

    const health = await checkPageHealth(page);
    console.log('Execution health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Execution content:', bodyText.substring(0, 500));
  });

  test('25 - Appeal', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/appeal/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '25-appeal');

    const health = await checkPageHealth(page);
    console.log('Appeal health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Appeal content:', bodyText.substring(0, 500));
  });

  test('26 - Q&A', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/qa/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '26-qa');

    const health = await checkPageHealth(page);
    console.log('Q&A health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Q&A content:', bodyText.substring(0, 500));
  });

  test('27 - Meeting', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/meeting/case-1`);
    await page.waitForTimeout(3000);

    await screenshot(page, '27-meeting');

    const health = await checkPageHealth(page);
    console.log('Meeting health:', JSON.stringify(health));

    const bodyText = await page.locator('body').innerText();
    console.log('Meeting content:', bodyText.substring(0, 500));
  });
});
