import { expect, test } from '@playwright/test';

test.skip(process.env.REAL_BACKEND_E2E !== '1', 'Set REAL_BACKEND_E2E=1 to run against the local real backend.');

const username = process.env.REAL_BACKEND_E2E_USER || 'pytest-admin';
const password = process.env.REAL_BACKEND_E2E_PASSWORD || 'pytest-password';
const backendReadyUrl = process.env.REAL_BACKEND_READY_URL || 'http://127.0.0.1:8002/ready';

test.describe('real backend time-control flow', () => {
  test('renders seeded letters and timeline events through the case UI', async ({ page, request }) => {
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
    const caseTitle = `函件时间线真实后端验收-${suffix}`;
    const letterTitle = `律师函真实后端验收-${suffix}`;
    const letterSummary = `函件页面验收摘要-${suffix}`;
    const timelineTitle = `开庭排期真实后端验收-${suffix}`;
    const timelineDescription = `时间线页面验收说明-${suffix}`;

    const caseResponse = await page.request.post('/api/cases', {
      headers,
      data: {
        title: caseTitle,
        case_type: 'civil',
        plaintiff: '时间线原告',
        defendant: '时间线被告',
        claim_amount: '66000',
        description: '用于验证真实后端支撑下的函件和时间线页面。',
      },
    });
    expect(caseResponse.ok(), await caseResponse.text()).toBeTruthy();
    const createdCase = await caseResponse.json();
    const caseId = String(createdCase.id);

    const letterResponse = await page.request.post(`/api/time-control/case/${caseId}/letters`, {
      headers,
      data: {
        标题: letterTitle,
        方向: 'outgoing',
        类型: 'lawyer_letter',
        文号: `UI-${suffix}`,
        发送方: '我方律师团队',
        接收方: '对方当事人',
        函件日期: '2026-05-17T00:00:00.000Z',
        截止日期: '2026-05-24T00:00:00.000Z',
        内容摘要: letterSummary,
        核心诉求: '要求对方在期限内履行合同付款义务。',
      },
    });
    expect(letterResponse.ok(), await letterResponse.text()).toBeTruthy();

    const timelineResponse = await page.request.post(`/api/time-control/case/${caseId}/timeline`, {
      headers,
      data: {
        事件类型: 'hearing',
        事件名称: timelineTitle,
        事件日期: '2026-05-20T09:30:00.000Z',
        事件描述: timelineDescription,
        重要性: 'important',
        是否里程碑: true,
      },
    });
    expect(timelineResponse.ok(), await timelineResponse.text()).toBeTruthy();

    await page.goto(`/cases/${caseId}/letters`);
    await expect(page.getByRole('heading', { name: '函件管理' })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(letterTitle)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(letterSummary)).toBeVisible({ timeout: 30000 });

    await page.goto(`/cases/${caseId}/timeline`);
    await expect(page.getByRole('heading', { name: /案件时间线与庭审记录/ })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(timelineTitle)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(timelineDescription)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('法庭调查/质证记录')).toBeVisible();
  });
});
