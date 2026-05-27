import { test, expect, login } from './fixtures';

test.describe('Evidence Management', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display evidence list for a case', async ({ page }) => {
    await page.goto('/cases/case-1/evidence');
    await expect(page.getByRole('heading', { name: /证据列表/ })).toBeVisible();
    expect(await page.locator('[data-testid="evidence-item"]').count()).toBeGreaterThan(0);
  });

  test('should open upload panel', async ({ page }) => {
    await page.goto('/cases/case-1/evidence');
    await page.click('button:has-text("上传证据")');
    await expect(page.getByLabel('证据', { exact: true }).getByRole('button', { name: '返回' })).toBeVisible();
  });

  test('should view evidence details', async ({ page }) => {
    await page.goto('/cases/case-1/evidence');
    await page.click('[data-testid="evidence-item"]:first-child');
    await expect(page.locator('text=证据内容')).toBeVisible();
  });

  test('should switch evidence to list view', async ({ page }) => {
    await page.goto('/cases/case-1/evidence');
    await page.getByRole('button', { name: /列表/ }).click();
    await expect(page.locator('text=借款合同.pdf')).toBeVisible();
  });

  test('should display evidence graph', async ({ page }) => {
    await page.goto('/evidence-graph/case-1');
    await expect(page.getByRole('heading', { name: '证据图谱' })).toBeVisible();
  });

  test('should display evidence guide', async ({ page }) => {
    await page.goto('/evidence-guide/case-1');
    await expect(page.getByRole('heading', { name: '证据引导' })).toBeVisible();
  });
});
