import { expect, test } from '@playwright/test';
import { Buffer } from 'node:buffer';

test.skip(process.env.REAL_BACKEND_E2E !== '1', 'Set REAL_BACKEND_E2E=1 to run against the local real backend.');

const username = process.env.REAL_BACKEND_E2E_USER || 'pytest-admin';
const password = process.env.REAL_BACKEND_E2E_PASSWORD || 'pytest-password';
const backendReadyUrl = process.env.REAL_BACKEND_READY_URL || 'http://127.0.0.1:8002/ready';

async function downloadEvidenceBookAs(page: import('@playwright/test').Page, menuText: string, extension: RegExp) {
  const exportButton = page.getByRole('button', { name: /导出证据册/ });
  await expect(exportButton).toBeEnabled();

  const downloadPromise = page.waitForEvent('download');
  await exportButton.click();
  await page.getByText(menuText).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(extension);
}

test.describe('real backend main flow', () => {
  test('logs in, creates a case, uploads evidence, renders the evidence page, and downloads evidence books', async ({ page, request }) => {
    test.setTimeout(180000);

    const ready = await request.get(backendReadyUrl);
    expect(ready.ok(), `backend must be ready at ${backendReadyUrl}`).toBeTruthy();

    const suffix = Date.now().toString(36);
    const caseTitle = `真实后端主流程验收-${suffix}`;
    const evidenceName = `真实后端证据-${suffix}.txt`;

    await page.goto('/login');
    await page.locator('input[name="username"]').fill(username);
    await page.locator('input[name="password"]').fill(password);
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 30000 });

    await page.goto('/cases/new');
    await page.getByText('合同纠纷').click();
    await expect(page.getByText('已选择: 合同纠纷')).toBeVisible();

    await page.getByPlaceholder('请输入案件标题').fill(caseTitle);
    await page.getByPlaceholder('原告姓名').fill('真实后端原告');
    await page.getByPlaceholder('被告姓名').fill('真实后端被告');
    await page.getByPlaceholder('请输入金额').fill('128000');
    await page.getByPlaceholder('请描述案件情况').fill('用于验证真实后端支撑下的前端建案和证据链主流程。');
    await page.locator('button[type="submit"]').click();

    await expect(page).toHaveURL(/\/cases\/\d+(\/overview)?$/, { timeout: 30000 });
    const caseId = page.url().match(/\/cases\/(\d+)/)?.[1];
    expect(caseId, 'created case id should be present in the detail URL').toBeTruthy();
    await expect(page.getByRole('heading', { name: caseTitle })).toBeVisible({ timeout: 30000 });

    const token = await page.evaluate(() => localStorage.getItem('auth_token'));
    expect(token, 'login should persist an access token for API requests').toBeTruthy();

    const uploadResponse = await page.request.post(`/api/documents/upload-batch/${caseId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      multipart: {
        files: {
          name: evidenceName,
          mimeType: 'text/plain',
          buffer: Buffer.from('短证据', 'utf8'),
        },
      },
    });
    expect(uploadResponse.ok(), await uploadResponse.text()).toBeTruthy();
    const uploadJson = await uploadResponse.json();
    expect(uploadJson.success).toBe(1);

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
        { timeout: 15000, message: 'uploaded evidence should be indexed for the case' },
      )
      .toContainEqual(expect.objectContaining({ original_filename: evidenceName }));

    await page.goto(`/cases/${caseId}/evidence`);
    await expect(page.getByRole('heading', { name: /证据列表/ })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(evidenceName)).toBeVisible({ timeout: 30000 });
    await downloadEvidenceBookAs(page, 'Markdown 格式', /\.md$/);
    await downloadEvidenceBookAs(page, 'PDF 文档', /\.pdf$/);
    await downloadEvidenceBookAs(page, 'Word 文档', /\.docx$/);
  });
});
