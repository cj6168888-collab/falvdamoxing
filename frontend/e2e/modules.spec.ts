import { type Page } from '@playwright/test';
import { test, expect, login } from './fixtures';

async function expectAuthenticatedShell(page: Page) {
  await expect(page.getByRole('banner')).toBeVisible();
  await expect(page.getByRole('navigation')).toBeVisible();
  await expect(page.getByLabel('用户菜单')).toBeVisible();
  await expect(page.getByRole('button', { name: '登录' })).not.toBeVisible();
}

test.describe('Authenticated modules', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display dashboard sections', async ({ page }) => {
    await expectAuthenticatedShell(page);
    await expect(page.getByRole('heading', { name: '工作台' })).toBeVisible();
    await expect(page.getByText('案件概览')).toBeVisible();
    await expect(page.getByText('快捷入口')).toBeVisible();
  });

  test('should display case list and detail tabs', async ({ page }) => {
    await page.getByRole('link', { name: '案件管理' }).click();
    await expect(page).toHaveURL(/\/cases/);
    await expect(page.getByPlaceholder(/搜索案件/)).toBeVisible();
    await expect(page.locator('[data-testid="case-card"]')).toHaveCount(1);

    await page.locator('[data-testid="case-card"]').first().click();
    await expect(page.getByRole('heading', { name: '借款合同纠纷' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '证据' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '文书' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '开庭/日程' })).toBeVisible();
  });

  test('should display document workspace', async ({ page }) => {
    await page.goto('/cases/case-1');
    await page.getByRole('tab', { name: '文书' }).click();
    await expect(page).toHaveURL(/\/cases\/case-1\/documents/);
    await expect(page.getByRole('tab', { name: '文书' })).toHaveAttribute('data-state', 'active');
  });

  test('should display evidence modules', async ({ page }) => {
    await page.goto('/cases/case-1/evidence');
    await expect(page.getByRole('heading', { name: /证据列表/ })).toBeVisible();
    await expect(page.locator('[data-testid="evidence-item"]')).toHaveCount(1);

    await page.goto('/evidence-graph/case-1');
    await expect(page.getByRole('heading', { name: '证据图谱' })).toBeVisible();

    await page.goto('/evidence-guide/case-1');
    await expect(page.getByRole('heading', { name: '证据引导' })).toBeVisible();
  });

  test('should display case support routes', async ({ page }) => {
    const routes = [
      '/timeline/case-1',
      '/hearing/case-1',
      '/adversarial/case-1',
      '/senior-analysis/case-1',
      '/appeal/case-1',
      '/execution/case-1',
      '/progress/case-1',
      '/meeting/case-1',
      '/qa/case-1',
    ] as const;

    for (const route of routes) {
      await page.goto(route);
      await expectAuthenticatedShell(page);
      await expect(page.locator('main')).not.toHaveText('');
    }
  });

  test('should display reminders and responsive header', async ({ page }) => {
    await page.goto('/reminders');
    await expect(page.getByRole('heading', { name: '提醒中心' })).toBeVisible();

    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    await expect(page.getByRole('banner')).toBeVisible();

    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/dashboard');
    await expect(page.getByRole('banner')).toBeVisible();
  });
});
