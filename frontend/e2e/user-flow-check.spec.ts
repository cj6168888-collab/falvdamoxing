import { test, expect, login } from './fixtures';

test.describe('User Flow Check', () => {
  test('complete user flow - login to case detail', async ({ page }) => {
    await page.goto('/');
    
    // Check if we're on login page
    await page.waitForLoadState('networkidle');
    const url = page.url();
    
    // If redirected to login, login
    if (url.includes('/login')) {
      await login(page);
    }
    
    // Check dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('heading', { name: '工作台' })).toBeVisible();
    
    // Navigate to cases
    await page.getByRole('link', { name: '案件管理' }).click();
    await page.waitForURL(/\/cases$/);
    await expect(page.locator('[data-testid="case-card"]').first()).toBeVisible();
    const casesContent = await page.textContent('body');
    
    // Check for garbled text
    const garbledPatterns = [/\ufffd/g, /\\u[0-9a-fA-F]{4}/g, /%[0-9a-fA-F]{2}%[0-9a-fA-F]{2}/g];
    const hasGarbled = garbledPatterns.some((pattern) => pattern.test(casesContent || ''));
    expect(hasGarbled).toBe(false);
    
    // Click first case card
    const caseCards = await page.locator('[data-testid="case-card"]').count();
    expect(caseCards).toBeGreaterThan(0);
    
    await page.locator('[data-testid="case-card"]').first().click();
    await expect(page).toHaveURL(/\/cases\/case-1/);
    await expect(page.getByRole('heading', { name: '借款合同纠纷' })).toBeVisible();

    // Check tabs
    const tabs = await page.locator('[role="tab"]').count();
    expect(tabs).toBeGreaterThanOrEqual(9);

    for (const tabText of ['概览', '当事人', '对话', '证据', '文书', '分析', '函件']) {
      await page.goto('/cases/case-1');
      await page.getByRole('tab', { name: tabText }).click();
      await expect(page.locator('body')).toContainText(tabText === '概览' ? '案件基础信息' : tabText);
    }
  });
});

