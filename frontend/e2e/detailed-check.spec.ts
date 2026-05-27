import { test, login, expect } from './fixtures';

test.describe('Detailed UI Check', () => {
  test('check dashboard sections', async ({ page }) => {
    await login(page);
    await expect(page.getByRole('heading', { name: '工作台' })).toBeVisible();
    await expect(page.locator('body')).toContainText('案件概览');
    await expect(page.locator('body')).toContainText('快捷入口');

    // Get full page text
    const fullText = await page.textContent('body') || '';

    // Check for specific strings
    const checks = [
      '工作台',
      '案件概览',
      '全案件数',
      '进行中',
      '近期待办',
      '快捷入口',
      '新建案件',
      '法律咨询',
    ];

    for (const text of checks) {
      const found = fullText.includes(text);
      expect(found, `Expected dashboard to include "${text}"`).toBe(true);
    }

    // Check for grid layout
    const grids = await page.locator('[class*="grid"]').count();
    expect(grids).toBeGreaterThan(0);

    // Screenshot for visual check
    await page.screenshot({ path: 'test-results/dashboard-full.png', fullPage: true });
  });
});
