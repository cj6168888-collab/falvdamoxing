import { test, login, expect } from './fixtures';

test.describe('Debug tabs', () => {
  test('check tab DOM', async ({ page }) => {
    await login(page);

    await page.getByRole('link', { name: '案件管理' }).click();
    await page.waitForURL(/\/cases$/);
    await expect(page.locator('[data-testid="case-card"]').first()).toBeVisible();

    await page.goto('/cases/case-1');
    await expect(page).toHaveURL(/\/cases\/case-1/);
    await expect(page.getByRole('heading', { name: '借款合同纠纷' })).toBeVisible();
    await expect(page.locator('[role="tab"]').first()).toBeVisible();

    const tabCount = await page.locator('[role="tab"]').count();
    expect(tabCount).toBe(13);

    const tabChecks = [
      { name: '概览', url: /\/cases\/case-1$/, expected: '案件基础信息' },
      { name: '开庭/日程', url: /\/cases\/case-1\/timeline$/, expected: '案件时间线与庭审记录' },
      { name: '当事人', url: /\/cases\/case-1\/parties$/, expected: '当事人 (2)' },
      { name: '对话', url: /\/cases\/case-1\/chat$/, expected: 'AI 律师案情分析' },
      { name: '证据', url: /\/cases\/case-1\/evidence$/, expected: '证据列表' },
      { name: '文件夹', url: /\/cases\/case-1\/folder$/, expected: '证据文件夹配置' },
      { name: '文书', url: /\/cases\/case-1\/documents$/, expected: '文书生成' },
      { name: '分析', url: /\/cases\/case-1\/analysis$/, expected: '对抗性分析' },
      { name: '函件', url: /\/cases\/case-1\/letters$/, expected: '函件管理' },
      { name: '财产/执行', url: /\/cases\/case-1\/execution$/, expected: '执行跟踪' },
      { name: '二审/上诉', url: /\/cases\/case-1\/appeal$/, expected: '上诉追踪' },
      { name: '画像', url: /\/cases\/case-1\/profile$/, expected: '案件画像分析' },
      { name: '报告', url: /\/cases\/case-1\/reports$/, expected: '报告中心' },
    ];

    for (const { name, url, expected } of tabChecks) {
      await page.goto('/cases/case-1');
      await page.getByRole('tab', { name }).click();
      await expect(page).toHaveURL(url);
      await expect(page.locator('body')).toContainText(expected);
    }

    // Screenshot
    await page.screenshot({ path: 'test-results/tabs-debug.png', fullPage: true });
  });
});
