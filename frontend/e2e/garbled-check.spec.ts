import { test, login, expect } from './fixtures';

test.describe('Check garbled text', () => {
  test('verify actual rendered text', async ({ page }) => {
    await login(page);

    await page.getByRole('link', { name: '案件管理' }).click();
    await page.waitForURL(/\/cases$/);
    await expect(page.locator('[data-testid="case-card"]').first()).toBeVisible();

    await expect(page.locator('body')).toContainText('借款合同纠纷');
    await expect(page.locator('body')).toContainText('测试客户');
    await expect(page.locator('body')).toContainText('对方当事人');

    // Click first case
    await page.locator('[data-testid="case-card"]').first().click();
    await expect(page).toHaveURL(/\/cases\/case-1/);
    await expect(page.getByRole('heading', { name: '借款合同纠纷' })).toBeVisible();

    await expect(page.locator('body')).toContainText('测试客户');
    await expect(page.locator('body')).toContainText('对方当事人');
    await expect(page.locator('body')).toContainText('100,000');

    for (const tabName of ['概览', '开庭/日程', '当事人', '对话', '证据', '文件夹', '文书', '分析', '函件', '财产/执行', '二审/上诉', '画像', '报告']) {
      await expect(page.getByRole('tab', { name: tabName })).toBeVisible();
    }

    const bodyText = await page.locator('body').innerText();
    const garbledPatterns = [/\ufffd/g, /\\u[0-9a-fA-F]{4}/g, /%[0-9a-fA-F]{2}%[0-9a-fA-F]{2}/g];
    expect(garbledPatterns.some((pattern) => pattern.test(bodyText))).toBe(false);

    await page.screenshot({ path: 'test-results/case-detail.png', fullPage: true });
  });
});
