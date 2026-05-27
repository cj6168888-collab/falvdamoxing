import { expect, test } from '@playwright/test';

test.skip(process.env.REAL_BACKEND_E2E !== '1', 'Set REAL_BACKEND_E2E=1 to run against the local real backend.');

const username = process.env.REAL_BACKEND_E2E_USER || 'pytest-admin';
const password = process.env.REAL_BACKEND_E2E_PASSWORD || 'pytest-password';
const backendReadyUrl = process.env.REAL_BACKEND_READY_URL || 'http://127.0.0.1:8002/ready';

async function downloadReportAs(page: import('@playwright/test').Page, menuText: string, extension: RegExp) {
  const exportButton = page.getByRole('button', { name: /导出/ });
  await expect(exportButton).toBeEnabled();

  const downloadPromise = page.waitForEvent('download');
  await exportButton.click();
  await page.getByText(menuText).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(extension);
}

test.describe('real backend report and export flow', () => {
  test('generates a stable report from the UI, opens details, and downloads markdown, PDF, and Word', async ({ page, request }) => {
    test.setTimeout(180000);

    const ready = await request.get(backendReadyUrl);
    expect(ready.ok(), `backend must be ready at ${backendReadyUrl}`).toBeTruthy();

    await page.goto('/login');
    await page.locator('input[name="username"]').fill(username);
    await page.locator('input[name="password"]').fill(password);
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 30000 });

    const token = await page.evaluate(() => localStorage.getItem('auth_token'));
    expect(token, 'login should persist an access token for API requests').toBeTruthy();

    const suffix = Date.now().toString(36);
    const caseTitle = `博凯升华报告真实后端验收-${suffix}`;
    const caseResponse = await page.request.post('/api/cases', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        title: caseTitle,
        case_type: 'civil',
        plaintiff: '报告原告',
        defendant: '报告被告',
        claim_amount: '99000',
        description: '用于验证真实后端支撑下的报告生成、详情和导出主流程。',
      },
    });
    expect(caseResponse.ok(), await caseResponse.text()).toBeTruthy();
    const createdCase = await caseResponse.json();
    const caseId = String(createdCase.id);

    await page.goto(`/cases/${caseId}/reports`);
    await expect(page.getByRole('heading', { name: '报告中心' })).toBeVisible({ timeout: 30000 });
    await page.getByRole('button', { name: /生成第一份报告|生成报告/ }).first().click();
    await expect(page.getByRole('heading', { name: '生成报告' })).toBeVisible();
    await page.getByText('案件分析').click();

    await expect(page.getByRole('heading', { name: '报告中心' })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(`${caseTitle} - 案件分析`)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('已完成')).toBeVisible();

    await page.getByText(`${caseTitle} - 案件分析`).click();
    await expect(page.getByRole('heading', { name: '报告详情' })).toBeVisible();
    await expect(page.getByText('报告内容')).toBeVisible();
    await expect(page.getByRole('heading', { name: /案件定位/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: /主要风险/ })).toBeVisible();

    await downloadReportAs(page, 'Markdown 格式', /\.md$/);
    await downloadReportAs(page, 'PDF 文档', /\.pdf$/);
    await downloadReportAs(page, 'Word 文档', /\.docx$/);
  });
});
