import { test, login, expect } from './fixtures';

test.describe('Full UI Audit', () => {
  test('check all pages for real issues', async ({ page }) => {
    const issues: string[] = [];

    await login(page);

    // 2. Check Dashboard
    await page.waitForTimeout(1000);
    const dashboardText = await page.textContent('body') || '';
    if (!dashboardText.includes('工作台')) issues.push('Dashboard: missing "工作台"');
    if (!dashboardText.includes('案件概览')) issues.push('Dashboard: missing "案件概览"');
    if (!dashboardText.includes('快捷入口')) issues.push('Dashboard: missing "快捷入口"');

    // 3. Check Cases List
    await page.click('text=案件管理');
    await page.waitForURL(/\/cases/);
    await page.waitForTimeout(1000);
    const casesText = await page.textContent('body') || '';
    const caseCards = await page.locator('[data-testid="case-card"]').count();
    if (caseCards === 0) issues.push('Cases: 0 case cards displayed');
    if (!casesText.includes('新建案件')) issues.push('Cases: missing "新建案件"');

    // 4. Click first case card
    if (caseCards > 0) {
      await page.locator('[data-testid="case-card"]').first().click();
      await page.waitForTimeout(1000);
      const detailText = await page.textContent('body') || '';
      if (!detailText.includes('借款合同纠纷') && !detailText.includes('概览')) issues.push('Case detail: missing content');

      // 5. Check tabs
      const tabChecks = [
        { name: '概览', expected: '案件基础信息' },
        { name: '开庭/日程', expected: '案件时间线与庭审记录' },
        { name: '当事人', expected: '当事人 (2)' },
        { name: '对话', expected: 'AI 律师案情分析' },
        { name: '证据', expected: '证据列表' },
        { name: '文件夹', expected: '证据文件夹配置' },
        { name: '文书', expected: '文书生成' },
        { name: '分析', expected: '对抗性分析' },
        { name: '函件', expected: '函件管理' },
      ];
      const tabs = await page.locator('[role="tab"]').count();
      if (tabs === 0) issues.push('Case detail: 0 tabs found');

      // 6. Click each tab and check content
      for (const { name: tabText, expected } of tabChecks) {
        await page.goto('/cases/case-1');
        await page.waitForSelector('[role="tab"]');
        const tab = page.getByRole('tab', { name: tabText });
        if (await tab.count() === 0) {
          issues.push(`Tab ${tabText}: missing`);
          continue;
        }
        await tab.click();
        await expect(page.locator('body')).toContainText(expected, { timeout: 5000 }).catch(() => {});
        const tabContent = await page.textContent('body') || '';
        if (tabContent.length < 100) issues.push(`Tab ${tabText}: content too short (${tabContent.length} chars)`);
        if (!tabContent.includes(expected)) issues.push(`Tab ${tabText}: missing "${expected}"`);
      }
    }

    expect(issues, issues.join('\n')).toEqual([]);
  });
});
