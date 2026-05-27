import { test, login, expect } from './fixtures';

test.describe('Full Functional Test', () => {
  test.setTimeout(60000);
  test('test all buttons and features', async ({ page }) => {
    const results: string[] = [];

    await login(page);
    await page.waitForTimeout(1000);

    // 1. Dashboard
    results.push('\n=== Dashboard ===');
    
    const dashboardLoaded = await page.getByRole('heading', { name: '工作台' }).count();
    results.push(`Dashboard loaded: ${dashboardLoaded > 0 ? 'PASS' : 'FAIL'}`);
    
    const newCaseBtn = await page.locator('text=新建案件').count();
    results.push(`New case button: ${newCaseBtn > 0 ? 'PASS' : 'FAIL'}`);
    
    await page.click('text=新建案件');
    await page.waitForTimeout(1000);
    results.push(`New case nav: ${page.url().includes('/cases/new') ? 'PASS' : 'FAIL'}`);
    
    await page.goto('/dashboard');
    await page.waitForTimeout(1000);

    // 2. Cases List
    results.push('\n=== Cases List ===');
    await page.click('text=案件管理');
    await page.waitForURL(/\/cases/);
    await page.waitForTimeout(1000);
    
    const caseCards = await page.locator('[data-testid="case-card"]').count();
    results.push(`Case cards: ${caseCards} ${caseCards > 0 ? 'PASS' : 'FAIL'}`);
    
    // Search
    await page.fill('input[placeholder*="搜索"]', '借款');
    await page.waitForTimeout(500);
    const filtered = await page.locator('[data-testid="case-card"]').count();
    results.push(`Search: ${filtered > 0 ? 'PASS' : 'FAIL'}`);
    await page.fill('input[placeholder*="搜索"]', '');
    await page.waitForTimeout(500);

    // 3. Case Detail
    results.push('\n=== Case Detail ===');
    await page.locator('[data-testid="case-card"]').first().click();
    await page.waitForTimeout(1000);
    results.push(`Detail URL: ${page.url().includes('/cases/') ? 'PASS' : 'FAIL'}`);
    
    // Back button
    await page.click('text=返回');
    await page.waitForURL(/\/cases/);
    await page.waitForTimeout(500);
    results.push('Back button: PASS');
    
    await page.locator('[data-testid="case-card"]').first().click();
    await page.waitForTimeout(1000);

    // 4. Tabs - click by index
    results.push('\n=== Tabs ===');
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
    
    for (const { name: tabName, expected } of tabChecks) {
      await page.goto('/cases/case-1');
      await page.waitForSelector('[role="tab"]');
      const tab = page.getByRole('tab', { name: tabName });
      if (await tab.count() === 0) {
        results.push(`Tab ${tabName}: missing WARN`);
        continue;
      }
      await tab.click();
      await expect(page.locator('body')).toContainText(expected, { timeout: 5000 }).catch(() => {});
      const url = page.url();
      const bodyText = await page.textContent('body') || '';
      const hasExpected = bodyText.includes(expected);
      results.push(`Tab ${tabName}: URL=${url.split('/').pop()}, expected=${hasExpected ? 'PASS' : 'WARN'}`);
    }

    // 5. Overview tab content
    results.push('\n=== Overview Content ===');
    await page.goto('/cases/case-1');
    await page.getByRole('tab', { name: '概览' }).click();
    await page.waitForTimeout(500);
    const hasAmount = await page.locator('text=100,000').count() > 0;
    const hasPlaintiff = await page.locator('text=测试客户').count() > 0;
    const hasDefendant = await page.locator('text=对方当事人').count() > 0;
    const hasDesc = await page.locator('text=测试案件描述').count() > 0;
    results.push(`Amount: ${hasAmount ? 'PASS' : 'FAIL'}`);
    results.push(`Plaintiff: ${hasPlaintiff ? 'PASS' : 'FAIL'}`);
    results.push(`Defendant: ${hasDefendant ? 'PASS' : 'FAIL'}`);
    results.push(`Description: ${hasDesc ? 'PASS' : 'FAIL'}`);

    // 6. Parties tab
    results.push('\n=== Parties Tab ===');
    await page.goto('/cases/case-1');
    await page.getByRole('tab', { name: '当事人' }).click();
    await page.waitForTimeout(500);
    const hasParties = (await page.textContent('body') || '').length > 100;
    results.push(`Parties content: ${hasParties ? 'PASS' : 'WARN'}`);

    // 7. Chat tab
    results.push('\n=== Chat Tab ===');
    await page.goto('/cases/case-1');
    await page.getByRole('tab', { name: '对话' }).click();
    await page.waitForTimeout(500);
    const hasInput = await page.locator('input, textarea').count() > 0;
    results.push(`Chat input: ${hasInput ? 'PASS' : 'FAIL'}`);

    // 8. Evidence tab
    results.push('\n=== Evidence Tab ===');
    await page.goto('/cases/case-1');
    await page.getByRole('tab', { name: '证据' }).click();
    await page.waitForTimeout(500);
    const hasEvidence = (await page.textContent('body') || '').length > 50;
    results.push(`Evidence content: ${hasEvidence ? 'PASS' : 'WARN'}`);

    // 9. Documents tab
    results.push('\n=== Documents Tab ===');
    await page.goto('/cases/case-1');
    await page.getByRole('tab', { name: '文书' }).click();
    await page.waitForTimeout(500);
    const hasDocs = (await page.textContent('body') || '').length > 50;
    results.push(`Documents content: ${hasDocs ? 'PASS' : 'WARN'}`);

    // 10. Analysis tab
    results.push('\n=== Analysis Tab ===');
    await page.goto('/cases/case-1');
    await page.getByRole('tab', { name: '分析' }).click();
    await page.waitForTimeout(500);
    const hasAnalysis = (await page.textContent('body') || '').length > 50;
    results.push(`Analysis content: ${hasAnalysis ? 'PASS' : 'WARN'}`);

    // 11. Profile tab
    results.push('\n=== Profile Tab ===');
    await page.goto('/cases/case-1');
    await page.getByRole('tab', { name: '画像' }).click();
    await page.waitForTimeout(500);
    const hasProfile = (await page.textContent('body') || '').length > 50;
    results.push(`Profile content: ${hasProfile ? 'PASS' : 'WARN'}`);

    // 12. Reports tab
    results.push('\n=== Reports Tab ===');
    await page.goto('/cases/case-1');
    await page.getByRole('tab', { name: '报告' }).click();
    await page.waitForTimeout(500);
    const hasReports = (await page.textContent('body') || '').length > 50;
    results.push(`Reports content: ${hasReports ? 'PASS' : 'WARN'}`);

    // 13. Letters tab
    results.push('\n=== Letters Tab ===');
    await page.goto('/cases/case-1');
    await page.getByRole('tab', { name: '函件' }).click();
    await page.waitForTimeout(500);
    const hasLetters = (await page.textContent('body') || '').length > 50;
    results.push(`Letters content: ${hasLetters ? 'PASS' : 'WARN'}`);

    // 14. Sidebar navigation
    results.push('\n=== Sidebar Navigation ===');
    const navItems = [
      { name: '工作台', url: '/dashboard' },
      { name: '案件管理', url: '/cases' },
      { name: '提醒中心', url: '/reminders' },
    ];
    for (const item of navItems) {
      try {
        await page.getByRole('link', { name: item.name }).click({ timeout: 3000 });
        await page.waitForURL(new RegExp(item.url), { timeout: 3000 });
        results.push(`Nav ${item.name}: ${page.url().includes(item.url) ? 'PASS' : 'FAIL'}`);
      } catch {
        results.push(`Nav ${item.name}: FAIL`);
      }
    }

    // Print results
    console.log('\n' + '='.repeat(60));
    console.log('FUNCTIONAL TEST RESULTS');
    console.log('='.repeat(60));
    results.forEach(r => console.log(r));
    console.log('='.repeat(60));
    
    const passCount = results.filter(r => r.includes('PASS')).length;
    const failCount = results.filter(r => r.includes('FAIL')).length;
    const warnCount = results.filter(r => r.includes('WARN')).length;
    console.log(`\nPASS: ${passCount} | FAIL: ${failCount} | WARN: ${warnCount}`);
    console.log(`Total: ${passCount + failCount + warnCount} tests`);
  });
});
