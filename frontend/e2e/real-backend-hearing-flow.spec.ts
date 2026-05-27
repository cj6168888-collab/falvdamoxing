import { expect, test } from '@playwright/test';

test.skip(process.env.REAL_BACKEND_E2E !== '1', 'Set REAL_BACKEND_E2E=1 to run against the local real backend.');

const username = process.env.REAL_BACKEND_E2E_USER || 'pytest-admin';
const password = process.env.REAL_BACKEND_E2E_PASSWORD || 'pytest-password';
const backendReadyUrl = process.env.REAL_BACKEND_READY_URL || 'http://127.0.0.1:8002/ready';

test.describe('real backend hearing flow', () => {
  test('renders seeded hearing status and statements through the hearing UI', async ({ page, request }) => {
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
    const caseTitle = `庭审真实后端验收-${suffix}`;
    const location = `第一法庭-${suffix}`;
    const statementContent = `请说明合同履行和付款时间-${suffix}`;

    const caseResponse = await page.request.post('/api/cases', {
      headers,
      data: {
        title: caseTitle,
        case_type: 'civil',
        plaintiff: '庭审原告',
        defendant: '庭审被告',
        claim_amount: '88000',
        description: '用于验证真实后端支撑下的庭审页面。',
      },
    });
    expect(caseResponse.ok(), await caseResponse.text()).toBeTruthy();
    const createdCase = await caseResponse.json();
    const caseId = String(createdCase.id);

    const hearingResponse = await page.request.post(`/api/hearings/case/${caseId}/hearing`, {
      headers,
      data: {
        庭审类型: 'first_trial',
        庭审日期: '2026-06-01T09:30:00.000Z',
        地点: location,
        案号: `UI-${suffix}`,
        参会人员: [{ name: '代理律师', role: '原告代理人' }],
      },
    });
    expect(hearingResponse.ok(), await hearingResponse.text()).toBeTruthy();
    const hearing = await hearingResponse.json();
    const hearingId = String(hearing.id);

    const statusResponse = await page.request.put(
      `/api/hearings/hearing/${hearingId}/status?status=in_progress&current_phase=cross_examination`,
      { headers },
    );
    expect(statusResponse.ok(), await statusResponse.text()).toBeTruthy();

    const statementResponse = await page.request.post(`/api/hearings/hearing/${hearingId}/statement`, {
      headers,
      data: {
        发言内容: statementContent,
        讲话方角色: 'plaintiff_lawyer',
        讲话人姓名: '代理律师',
        发言类型: 'question',
      },
    });
    expect(statementResponse.ok(), await statementResponse.text()).toBeTruthy();

    await page.goto(`/hearing/${caseId}`);
    await expect(page.getByRole('heading', { name: '出庭抗辩' })).toBeVisible();
    await expect(page.getByText('一审')).toBeVisible();
    await expect(page.getByText(location)).toBeVisible();
    await expect(page.getByText('进行中')).toBeVisible();
    await expect(page.getByText('法庭调查/质证')).toBeVisible();
    await expect(page.getByRole('heading', { name: '庭审发言记录' })).toBeVisible();
    await expect(page.getByText('代理律师')).toBeVisible();
    await expect(page.getByText(statementContent)).toBeVisible();
  });
});
