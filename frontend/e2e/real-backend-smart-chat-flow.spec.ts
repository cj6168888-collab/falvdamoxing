import { expect, test } from '@playwright/test';
import { Buffer } from 'node:buffer';

test.skip(process.env.REAL_BACKEND_E2E !== '1', 'Set REAL_BACKEND_E2E=1 to run against the local real backend.');

const username = process.env.REAL_BACKEND_E2E_USER || 'pytest-admin';
const password = process.env.REAL_BACKEND_E2E_PASSWORD || 'pytest-password';
const backendReadyUrl = process.env.REAL_BACKEND_READY_URL || 'http://127.0.0.1:8002/ready';

function firstVisibleHeading(markdown: string): string {
  const line = markdown
    .split(/\r?\n/)
    .map((item) => item.replace(/^#+\s*/, '').trim())
    .find((item) => item.length > 0);

  return line || '分析';
}

test.describe('real backend smart chat flow', () => {
  test('starts a full-case AI analysis from the UI and reloads the saved result', async ({ page, request }) => {
    test.setTimeout(180000);

    const ready = await request.get(backendReadyUrl);
    expect(ready.ok(), `backend must be ready at ${backendReadyUrl}`).toBeTruthy();

    const suffix = Date.now().toString(36);
    const caseTitle = `真实后端AI分析验收-${suffix}`;
    const evidenceName = `AI分析证据-${suffix}.txt`;
    const userPrompt = `请基于 ${caseTitle} 的证据，判断我方能否主张违约责任，并列出证据缺口。`;

    await page.goto('/login');
    await page.locator('input[name="username"]').fill(username);
    await page.locator('input[name="password"]').fill(password);
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 30000 });

    const token = await page.evaluate(() => localStorage.getItem('auth_token'));
    expect(token, 'login should persist an access token for API requests').toBeTruthy();

    const createCaseResponse = await page.request.post('/api/cases', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        title: caseTitle,
        case_type: '民事',
        plaintiff: '真实后端原告公司',
        defendant: '真实后端被告公司',
        description: '原告已付款，被告未按合同完成交付，需要评估违约责任、证据链和下一步诉讼策略。',
      },
    });
    expect(createCaseResponse.ok(), await createCaseResponse.text()).toBeTruthy();
    const caseId = (await createCaseResponse.json()).id;

    const uploadResponse = await page.request.post(`/api/documents/upload-batch/${caseId}`, {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        files: {
          name: evidenceName,
          mimeType: 'text/plain',
          buffer: Buffer.from(
            [
              '合同约定乙方应在2026年5月10日前完成交付。',
              '甲方已于2026年5月1日支付合同款128000元。',
              '乙方截至2026年5月17日仍未交付，也未说明合理延期原因。',
            ].join('\n'),
            'utf8',
          ),
        },
      },
    });
    expect(uploadResponse.ok(), await uploadResponse.text()).toBeTruthy();
    expect((await uploadResponse.json()).success).toBe(1);

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
        { timeout: 15000, message: 'uploaded evidence should be indexed for smart chat' },
      )
      .toContainEqual(expect.objectContaining({ original_filename: evidenceName }));

    await page.goto(`/smart-chat/${caseId}`);
    await expect(page.getByRole('heading', { name: '全案证据驱动分析' })).toBeVisible();
    await expect(page.getByRole('heading', { name: caseTitle })).toBeVisible();

    await page.getByRole('button', { name: /我是原告/ }).click();
    await page.locator('textarea').first().fill(userPrompt);

    const analysisResponsePromise = page.waitForResponse(
      (response) =>
        response.url().includes('/api/smart-chat/global-analysis') &&
        response.request().method() === 'POST',
      { timeout: 150000 },
    );

    await page.getByRole('button', { name: /开始全案分析/ }).click();
    await expect(page.getByRole('heading', { name: 'AI 正在分析案情' })).toBeVisible();

    const analysisResponse = await analysisResponsePromise;
    expect(analysisResponse.ok(), await analysisResponse.text()).toBeTruthy();
    const analysisData = await analysisResponse.json();
    expect(analysisData.analysis_id).toBeTruthy();
    expect(analysisData.full_analysis).toContain('证据');

    const resultHeading = firstVisibleHeading(analysisData.full_analysis);
    await expect(page.getByText(userPrompt)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('AI 分析').first()).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(resultHeading).first()).toBeVisible({ timeout: 30000 });

    await page.reload();
    await expect(page.getByText('AI 分析').first()).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(resultHeading).first()).toBeVisible({ timeout: 30000 });
  });
});
