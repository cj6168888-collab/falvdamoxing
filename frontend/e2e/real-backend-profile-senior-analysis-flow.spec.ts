import { expect, test } from '@playwright/test';

test.skip(process.env.REAL_BACKEND_E2E !== '1', 'Set REAL_BACKEND_E2E=1 to run against the local real backend.');

const username = process.env.REAL_BACKEND_E2E_USER || 'pytest-admin';
const password = process.env.REAL_BACKEND_E2E_PASSWORD || 'pytest-password';
const backendReadyUrl = process.env.REAL_BACKEND_READY_URL || 'http://127.0.0.1:8002/ready';

test.describe('real backend profile and senior analysis flow', () => {
  test('renders case profile data and completes senior lawyer analysis through real backend tasks', async ({ page, request }) => {
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
    const headers = { Authorization: `Bearer ${token}` };

    const suffix = Date.now().toString(36);
    const caseTitle = `画像资深分析真实后端验收-${suffix}`;

    const caseResponse = await page.request.post('/api/cases', {
      headers,
      data: {
        title: caseTitle,
        case_type: 'civil',
        cause: '合同纠纷',
        plaintiff: '画像原告',
        defendant: '画像被告',
        claim_amount: '96000',
        description: '用于验证真实后端支撑下的案件画像、知识原子、证据缺口和资深律师分析任务。',
      },
    });
    expect(caseResponse.ok(), await caseResponse.text()).toBeTruthy();
    const caseId = String((await caseResponse.json()).id);

    const buildProfileResponse = await page.request.post('/api/v2/profile/build', {
      headers,
      data: {
        case_id: Number(caseId),
        use_ai: false,
      },
    });
    expect(buildProfileResponse.ok(), await buildProfileResponse.text()).toBeTruthy();

    await page.goto(`/cases/${caseId}/profile`);
    await expect(page.getByRole('heading', { name: '案件画像分析' })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('案件画像概览')).toBeVisible();
    await expect(page.getByText('知识原子')).toBeVisible();
    await expect(page.getByText('证据缺口', { exact: true })).toBeVisible();
    await expect(page.getByText('知识库', { exact: true })).toBeVisible();
    await expect(page.getByText('知识图谱', { exact: true })).toBeVisible();
    await expect(page.getByText('原告: 画像原告').first()).toBeVisible();
    await expect(page.getByText('被告: 画像被告').first()).toBeVisible();
    await expect(page.getByText('案由: 合同纠纷').first()).toBeVisible();
    await expect(page.getByText('转账凭证').first()).toBeVisible();

    await page.goto(`/senior-analysis/${caseId}`);
    await expect(page.getByRole('heading', { name: '资深律师分析' })).toBeVisible({ timeout: 30000 });
    await page.getByRole('button', { name: '深度' }).click();
    await page.getByRole('button', { name: '开始分析' }).click();

    await expect(page.getByText('分析结果')).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('分析摘要')).toBeVisible();
    await expect(page.getByText('案件理解')).toBeVisible();
    await expect(page.getByText('证据盘点')).toBeVisible();
    await expect(page.getByText('要件核对')).toBeVisible();
    await expect(page.getByText('风险评估')).toBeVisible();
    await expect(page.getByText(caseTitle)).toBeVisible();
    await expect(page.getByText('证据数量仅0份')).toBeVisible();
  });
});
