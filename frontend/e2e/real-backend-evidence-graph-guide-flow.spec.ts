import { expect, test } from '@playwright/test';
import { Buffer } from 'node:buffer';

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

test.describe('real backend evidence graph, QA, and guide flow', () => {
  test('indexes evidence, renders graph, answers evidence questions, and records guide answers', async ({ page, request }) => {
    test.setTimeout(180000);

    const ready = await request.get(backendReadyUrl);
    expect(ready.ok(), `backend must be ready at ${backendReadyUrl}`).toBeTruthy();

    const token = await login(page);
    const suffix = Date.now().toString(36);
    const caseTitle = `证据图谱引导验收-${suffix}`;
    const evidenceName = `付款合同证据-${suffix}.txt`;

    const caseResponse = await page.request.post('/api/cases', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        title: caseTitle,
        case_type: 'civil',
        plaintiff: '甲方公司',
        defendant: '乙方公司',
        claim_amount: '128000',
        description: '用于验证证据图谱、证据问答和补证引导的真实后端主流程。',
      },
    });
    expect(caseResponse.ok(), await caseResponse.text()).toBeTruthy();
    const caseId = String((await caseResponse.json()).id);

    const uploadResponse = await page.request.post(`/api/documents/upload-batch/${caseId}`, {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        files: {
          name: evidenceName,
          mimeType: 'text/plain',
          buffer: Buffer.from('双方签订付款合同，乙方确认收到甲方转账128000元，并承诺继续履行交付义务。', 'utf8'),
        },
      },
    });
    expect(uploadResponse.ok(), await uploadResponse.text()).toBeTruthy();

    await expect
      .poll(
        async () => {
          const response = await page.request.get(`/api/v2/evidence-graph/evidence/list?case_id=${caseId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (!response.ok()) return [];
          const data = await response.json();
          return data.evidence_list || [];
        },
        { timeout: 15000, message: 'uploaded evidence should be indexed for graph and guide flows' },
      )
      .toContainEqual(expect.objectContaining({ original_filename: evidenceName }));

    await page.goto(`/evidence-graph/${caseId}`);
    await expect(page.getByRole('heading', { name: '证据图谱' })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(evidenceName)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('已索引证据')).toBeVisible();
    await page.getByRole('button', { name: /分析关系/ }).click();
    await expect(page.getByRole('heading', { name: '证据问答' })).toBeVisible();
    await page.getByPlaceholder('围绕当前案件证据提问').fill('这份证据能证明什么？');
    await page.getByRole('button', { name: /提交证据问题/ }).click();
    await expect(page.getByTestId('evidence-qa-answer')).toBeVisible({ timeout: 30000 });

    await page.goto(`/evidence-guide/${caseId}`);
    await expect(page.getByRole('heading', { name: '证据引导' })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('准备度')).toBeVisible();
    await expect(page.getByText('证据完整性')).toBeVisible();

    const submitGuideAnswer = page.getByRole('button', { name: /提交引导答案/ });
    if (await submitGuideAnswer.isVisible()) {
      await page.getByPlaceholder('回答上方第一个补证问题').fill('有书面合同和银行转账记录，可以上传原件和流水。');
      await submitGuideAnswer.click();
      await expect(page.getByText('已记录回答')).toBeVisible({ timeout: 30000 });
    }
  });
});
