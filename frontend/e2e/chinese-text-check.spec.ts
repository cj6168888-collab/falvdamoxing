import { test, expect, login } from './fixtures';

test.describe('Verify Chinese text renders correctly', () => {
  test('check exact text content', async ({ page }) => {
    await login(page);

    await page.getByRole('link', { name: '案件管理' }).click();
    await page.waitForURL(/\/cases$/);
    await expect(page.locator('[data-testid="case-card"]').first()).toBeVisible();

    // Verify case card text
    await expect(page.locator('text=借款合同纠纷')).toBeVisible();
    await expect(page.locator('text=测试客户')).toBeVisible();
    await expect(page.locator('text=对方当事人')).toBeVisible();
    await expect(page.locator('text=¥100,000')).toBeVisible();

    // Click first case
    await page.locator('[data-testid="case-card"]').first().click();
    await expect(page).toHaveURL(/\/cases\/case-1/);

    // Verify case detail
    await expect(page.locator('text=借款合同纠纷').first()).toBeVisible();
    await expect(page.locator('text=civil').first()).toBeVisible();
    await expect(page.locator('text=litigating').first()).toBeVisible();
    await expect(page.locator('text=原告').first()).toBeVisible();
    await expect(page.locator('text=测试客户').first()).toBeVisible();
    await expect(page.locator('text=被告').first()).toBeVisible();
    await expect(page.locator('text=对方当事人').first()).toBeVisible();
    await expect(page.locator('text=100,000').first()).toBeVisible();

    // Verify tabs
    await expect(page.locator('text=概览').first()).toBeVisible();
    await expect(page.locator('text=当事人').first()).toBeVisible();
    await expect(page.locator('text=对话').first()).toBeVisible();
    await expect(page.locator('text=证据').first()).toBeVisible();
    await expect(page.locator('text=文书').first()).toBeVisible();
    await expect(page.locator('text=分析').first()).toBeVisible();
    await expect(page.locator('text=画像').first()).toBeVisible();
    await expect(page.locator('text=报告').first()).toBeVisible();
    await expect(page.locator('text=函件').first()).toBeVisible();
  });
});
