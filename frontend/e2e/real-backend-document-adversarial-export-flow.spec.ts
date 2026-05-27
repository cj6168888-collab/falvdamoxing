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

async function downloadFromButton(page: import('@playwright/test').Page, buttonName: RegExp) {
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: buttonName }).first().click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.md$/);
}

async function downloadFromAdversarialMenu(
  page: import('@playwright/test').Page,
  itemName: RegExp,
  filenamePattern: RegExp,
) {
  await page.getByRole('button', { name: /^导出$/ }).first().click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('menuitem', { name: itemName }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(filenamePattern);
}

test.describe('real backend document and adversarial export UI flow', () => {
  test('exports generated documents and adversarial analyses from the UI', async ({ page, request }) => {
    test.setTimeout(180000);

    const ready = await request.get(backendReadyUrl);
    expect(ready.ok(), `backend must be ready at ${backendReadyUrl}`).toBeTruthy();

    const token = await login(page);
    const suffix = Date.now().toString(36);
    const caseTitle = `导出 UI 验收-${suffix}`;

    const caseResponse = await page.request.post('/api/cases', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        title: caseTitle,
        case_type: 'civil',
        plaintiff: '甲方公司',
        defendant: '乙方公司',
        claim_amount: '88000',
        description: '用于验证文书和对抗分析导出 UI 的真实后端主流程。',
      },
    });
    expect(caseResponse.ok(), await caseResponse.text()).toBeTruthy();
    const caseId = String((await caseResponse.json()).id);

    const documentResponse = await page.request.post('/api/documents/generate', {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 90000,
      data: {
        case_id: Number(caseId),
        document_type: '起诉状',
        custom_requirements: '简要说明付款事实和继续履行请求。',
      },
    });
    expect(documentResponse.ok(), await documentResponse.text()).toBeTruthy();

    await page.goto(`/cases/${caseId}/documents`);
    await expect(page.getByRole('heading', { name: '文书生成' })).toBeVisible({ timeout: 30000 });
    await page.getByRole('tab', { name: /历史文书/ }).click();
    const generatedDocumentTitle = page.getByRole('heading', { name: /起诉状_/ });
    await expect(generatedDocumentTitle).toBeVisible({ timeout: 30000 });
    await generatedDocumentTitle.click();
    await page.getByRole('button', { name: /查看\/下载/ }).click();
    await expect(page.getByText(/已准备就绪/)).toBeVisible();
    await downloadFromButton(page, /导出 Markdown/);

    const analysisResponse = await page.request.post(`/api/adversarial/case/${caseId}/analysis`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        标题: `对抗导出 UI 验收-${suffix}`,
        分析阶段: '诉讼',
        对手名称: '乙方公司',
        对手类型: '企业',
      },
    });
    expect(analysisResponse.ok(), await analysisResponse.text()).toBeTruthy();
    const analysisId = (await analysisResponse.json()).id;

    const updateResponse = await page.request.put(`/api/adversarial/${analysisId}`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        我方优势: '我方已有付款凭证。',
        对方弱点: '对方承认收款。',
        总体策略: '先固定付款事实，再推动继续履行。',
      },
    });
    expect(updateResponse.ok(), await updateResponse.text()).toBeTruthy();

    await page.goto(`/cases/${caseId}/analysis`);
    await expect(page.getByRole('heading', { name: '对抗性分析' })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('历史对抗分析')).toBeVisible();
    await expect(page.getByText(`对抗导出 UI 验收-${suffix}`)).toBeVisible();
    await downloadFromAdversarialMenu(page, /导出 Markdown/, /\.md$/);
    await downloadFromAdversarialMenu(page, /导出 Word/, /\.(docx|html)$/);
    await downloadFromAdversarialMenu(page, /导出 PDF/, /\.(pdf|html)$/);
  });
});
