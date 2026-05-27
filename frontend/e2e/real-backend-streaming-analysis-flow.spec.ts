import { expect, test } from '@playwright/test';

test.skip(process.env.REAL_BACKEND_E2E !== '1', 'Set REAL_BACKEND_E2E=1 to run against the local real backend.');

const username = process.env.REAL_BACKEND_E2E_USER || 'pytest-admin';
const password = process.env.REAL_BACKEND_E2E_PASSWORD || 'pytest-password';
const backendReadyUrl = process.env.REAL_BACKEND_READY_URL || 'http://127.0.0.1:8002/ready';

test.describe('real backend streaming analysis flow', () => {
  test('starts a custom streaming analysis from the UI and opens the saved history record', async ({ page, request }) => {
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
    const caseTitle = `流式分析真实后端验收-${suffix}`;
    const createCaseResponse = await page.request.post('/api/cases', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        title: caseTitle,
        case_type: 'civil',
        cause: '买卖合同纠纷',
        plaintiff: '流式原告',
        defendant: '流式被告',
        claim_amount: '88000',
        description: '用于验证真实后端支撑下的流式分析启动、SSE输出和历史记录。',
      },
    });
    expect(createCaseResponse.ok(), await createCaseResponse.text()).toBeTruthy();
    const caseId = String((await createCaseResponse.json()).id);

    await page.goto(`/analysis-history/${caseId}`);
    await expect(page.getByRole('heading', { name: '流式分析' })).toBeVisible({ timeout: 30000 });
    await page.getByRole('button', { name: '启动流式分析' }).click();

    await expect(page.getByText('实时输出')).toBeVisible();
    await expect(page.getByText('分析完成')).toBeVisible({ timeout: 150000 });
    await expect(page.getByText('共 1 条记录')).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('已完成').first()).toBeVisible({ timeout: 30000 });

    await page.getByLabel('查看分析记录').first().click();
    await expect(page.getByRole('heading', { name: '分析摘要' })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(/AI 服务暂时不可用|争议|证据|行动|分析失败|分析完成/).first()).toBeVisible();
  });
});
