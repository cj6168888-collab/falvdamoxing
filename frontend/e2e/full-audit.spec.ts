import { test, login } from './fixtures';
import type { Page } from '@playwright/test';

test.describe('Full Page Audit', () => {
  test('audit all pages', async ({ page }) => {
    test.setTimeout(90000);
    const results: { page: string; status: string; issues: string[] }[] = [];

    await login(page);

    // Check dashboard
    await checkPage(page, results, 'Dashboard', '/dashboard', ['工作台', '案件概览', '快捷入口']);

    // Check cases list
    await checkPage(page, results, '案件列表', '/cases', ['案件', '新建案件']);

    // Check case detail
    await checkPage(page, results, '案件详情', '/cases/case-1', ['借款合同纠纷', '概览', '当事人', '证据', '文书']);

    // Check case sub-pages
    await checkPage(page, results, '案件概览', '/cases/case-1/overview', ['案件基础信息']);
    await checkPage(page, results, '当事人', '/cases/case-1/parties', ['当事人']);
    await checkPage(page, results, '对话', '/cases/case-1/chat', ['对话', 'AI 律师案情分析']);
    await checkPage(page, results, '证据', '/cases/case-1/evidence', ['证据']);
    await checkPage(page, results, '文书', '/cases/case-1/documents', ['文书']);
    await checkPage(page, results, '分析', '/cases/case-1/analysis', ['分析']);
    await checkPage(page, results, '画像', '/cases/case-1/profile', ['画像']);
    await checkPage(page, results, '报告', '/cases/case-1/reports', ['报告']);
    await checkPage(page, results, '函件', '/cases/case-1/letters', ['函件']);

    // Check reminders
    await checkPage(page, results, '提醒中心', '/reminders', ['提醒']);

    // Check other pages
    await checkPage(page, results, '证据图谱', '/evidence-graph/case-1', ['图谱']);
    await checkPage(page, results, '证据引导', '/evidence-guide/case-1', ['引导']);
    await checkPage(page, results, '时间把控', '/timeline/case-1', ['截止日期']);
    await checkPage(page, results, '对抗分析', '/adversarial/case-1', ['对抗']);
    await checkPage(page, results, '资深分析', '/senior-analysis/case-1', ['分析']);
    await checkPage(page, results, '出庭抗辩', '/hearing/case-1', ['出庭抗辩']);
    await checkPage(page, results, '进度追踪', '/progress/case-1', ['进度']);
    await checkPage(page, results, '执行跟踪', '/execution/case-1', ['执行']);
    await checkPage(page, results, '上诉追踪', '/appeal/case-1', ['上诉']);
    await checkPage(page, results, '问答', '/qa/case-1', ['法律助手']);
    await checkPage(page, results, '会议', '/meeting/case-1', ['会议']);

    // Print results
    console.log('\n=== Audit Report ===');
    results.forEach(r => {
      const status = r.issues.length === 0 ? 'PASS' : 'FAIL';
      console.log(`[${status}] ${r.page}`);
      r.issues.forEach(issue => console.log(`  - ${issue}`));
    });
  });
});

type AuditResult = { page: string; status: string; issues: string[] };

async function checkPage(page: Page, results: AuditResult[], name: string, url: string, expectedTexts: string[]) {
  const issues: string[] = [];

  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 10000 });
    await page.waitForTimeout(300);

    const bodyText = await page.textContent('body') || '';

    // Check for garbled text patterns
    const garbledPatterns = ['ĳ', 'ĳĳ', '֤', 'ֹ', 'ȫ', 'ʧ'];
    for (const pattern of garbledPatterns) {
      if (bodyText.includes(pattern)) {
        issues.push(`Contains garbled text: "${pattern}"`);
      }
    }

    // Check for expected text
    for (const text of expectedTexts) {
      if (!bodyText.includes(text)) {
        issues.push(`Missing expected text: "${text}"`);
      }
    }

    // Check for empty page
    if (bodyText.trim().length < 50) {
      issues.push(`Page appears empty (only ${bodyText.trim().length} chars)`);
    }

    // Check for "开发中" placeholder
    if (bodyText.includes('开发中') || bodyText.includes('Coming Soon')) {
      issues.push('Page shows placeholder "开发中"');
    }

    results.push({
      page: name,
      status: issues.length === 0 ? 'PASS' : 'FAIL',
      issues,
    });
  } catch (error) {
    results.push({
      page: name,
      status: 'ERROR',
      issues: [`Navigation error: ${error instanceof Error ? error.message : String(error)}`],
    });
  }
}
