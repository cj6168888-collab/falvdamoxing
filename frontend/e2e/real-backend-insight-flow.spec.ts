import { expect, test } from '@playwright/test';

test.skip(process.env.REAL_BACKEND_E2E !== '1', 'Set REAL_BACKEND_E2E=1 to run against the local real backend.');

const username = process.env.REAL_BACKEND_E2E_USER || 'pytest-admin';
const password = process.env.REAL_BACKEND_E2E_PASSWORD || 'pytest-password';
const backendReadyUrl = process.env.REAL_BACKEND_READY_URL || 'http://127.0.0.1:8002/ready';

async function login(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.locator('input[name="username"]').fill(username);
  await page.locator('input[name="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 30000 });

  const token = await page.evaluate(() => localStorage.getItem('auth_token'));
  expect(token, 'login should persist an access token for API requests').toBeTruthy();
  return token as string;
}

test.describe('real backend insight flow', () => {
  test('opens the enhanced analysis workspace and exercises safe insight endpoints', async ({ page, request }) => {
    test.setTimeout(120000);

    const ready = await request.get(backendReadyUrl);
    expect(ready.ok(), `backend must be ready at ${backendReadyUrl}`).toBeTruthy();

    const token = await login(page);
    const suffix = Date.now().toString(36);

    const caseResponse = await page.request.post('/api/cases', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        title: `增强分析 UI 验收-${suffix}`,
        case_type: 'civil',
        plaintiff: '甲方公司',
        defendant: '乙方公司',
        claim_amount: '10000',
        description: '用于验证增强分析独立页面和安全端点。',
      },
    });
    expect(caseResponse.ok(), await caseResponse.text()).toBeTruthy();
    const caseId = String((await caseResponse.json()).id);

    await page.goto(`/insight/${caseId}`);
    await expect(page.getByRole('heading', { name: '增强分析' })).toBeVisible({ timeout: 30000 });
    await expect(page.getByRole('button', { name: /清除缓存/ })).toBeVisible();

    await page.getByRole('tab', { name: /证据图谱/ }).click();
    const graphResponsePromise = page.waitForResponse((response) =>
      response.url().includes('/api/v2/evidence/graph') && response.status() === 200,
    );
    await page.getByRole('button', { name: /构建图谱/ }).click();
    await graphResponsePromise;
    await expect(page.getByText('没有找到证据，请先上传证据')).toBeVisible({ timeout: 30000 });

    const queryResponsePromise = page.waitForResponse((response) =>
      response.url().includes(`/api/v2/evidence/query/${caseId}`) && response.status() === 200,
    );
    await page.getByRole('button', { name: /^查询$/ }).click();
    await queryResponsePromise;
    await expect(page.getByText(/返回 0 条结果/)).toBeVisible();

    await page.getByRole('tab', { name: /分段报告/ }).click();
    const statusResponsePromise = page.waitForResponse((response) =>
      response.url().includes(`/api/v2/report/status/${caseId}`) && response.status() === 200,
    );
    await page.getByRole('button', { name: /刷新状态/ }).click();
    await statusResponsePromise;
    await expect(page.getByText(/状态：not_started/)).toBeVisible();

    const cacheResponsePromise = page.waitForResponse((response) =>
      response.url().includes(`/api/v2/cache/clear/${caseId}`) && response.status() === 200,
    );
    await page.getByRole('button', { name: /清除缓存/ }).click();
    await cacheResponsePromise;
    await expect(page.getByText(/缓存已清除/)).toBeVisible();
  });
});
