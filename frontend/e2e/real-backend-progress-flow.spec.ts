import { expect, test } from '@playwright/test';

test.skip(process.env.REAL_BACKEND_E2E !== '1', 'Set REAL_BACKEND_E2E=1 to run against the local real backend.');

const username = process.env.REAL_BACKEND_E2E_USER || 'pytest-admin';
const password = process.env.REAL_BACKEND_E2E_PASSWORD || 'pytest-password';
const backendReadyUrl = process.env.REAL_BACKEND_READY_URL || 'http://127.0.0.1:8002/ready';

test.describe('real backend progress flow', () => {
  test('renders seeded deadlines and milestones through the progress UI', async ({ page, request }) => {
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
    const caseTitle = `进度期限真实后端验收-${suffix}`;
    const deadlineTitle = `举证期限真实后端验收-${suffix}`;
    const milestoneTitle = `立案材料真实后端验收-${suffix}`;
    const milestoneDescription = `进度页里程碑说明-${suffix}`;

    const caseResponse = await page.request.post('/api/cases', {
      headers,
      data: {
        title: caseTitle,
        case_type: 'civil',
        plaintiff: '进度原告',
        defendant: '进度被告',
        claim_amount: '73000',
        description: '用于验证真实后端支撑下的期限和里程碑进度页。',
      },
    });
    expect(caseResponse.ok(), await caseResponse.text()).toBeTruthy();
    const caseId = String((await caseResponse.json()).id);

    const deadlineResponse = await page.request.post(`/api/time-control/case/${caseId}/deadlines`, {
      headers,
      data: {
        期限类型: 'evidence',
        期限名称: deadlineTitle,
        分类: '举证',
        法律依据: '法院举证通知书',
        期限天数: 15,
        说明: '提交付款凭证、合同和沟通记录',
        起算日期: '2026-05-17T00:00:00.000Z',
        截止日期: '2026-05-28T00:00:00.000Z',
        是否强制: true,
        可否展期: true,
        关联事件: '证据交换',
      },
    });
    expect(deadlineResponse.ok(), await deadlineResponse.text()).toBeTruthy();

    const milestoneResponse = await page.request.post(`/api/time-control/case/${caseId}/timeline`, {
      headers,
      data: {
        事件类型: 'filing',
        事件名称: milestoneTitle,
        事件日期: '2026-05-20T10:00:00.000Z',
        事件描述: milestoneDescription,
        重要性: 'important',
        是否里程碑: true,
      },
    });
    expect(milestoneResponse.ok(), await milestoneResponse.text()).toBeTruthy();

    await page.goto(`/progress/${caseId}`);
    await expect(page.getByRole('heading', { name: '进度追踪' })).toBeVisible({ timeout: 30000 });
    await expect(page.getByRole('heading', { name: '阶段流转' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '关键里程碑' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '期限节点' })).toBeVisible();
    await expect(page.getByText('当前阶段：立案')).toBeVisible();
    await expect(page.getByText(milestoneTitle)).toBeVisible();
    await expect(page.getByText(milestoneDescription)).toBeVisible();
    await expect(page.getByText(deadlineTitle)).toBeVisible();
    await expect(page.getByText('法院举证通知书')).toBeVisible();
    await expect(page.getByText('2026 年 5 月 28 日')).toBeVisible();
  });
});
