import { test, expect, login } from './fixtures';

test.describe('Case Management', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display case list on cases page', async ({ page }) => {
    await page.goto('/cases');
    await expect(page.getByPlaceholder(/搜索案件/)).toBeVisible();
    await expect(page.locator('[data-testid="case-card"]').first()).toBeVisible();
  });

  test('should create a new case', async ({ page }) => {
    await page.goto('/cases');
    await page.click('button:has-text("新建案件")');
    await expect(page).toHaveURL(/\/cases\/new/);
    
    await page.getByPlaceholder('请输入案件标题').fill('测试案件');
    await page.getByPlaceholder('原告姓名').fill('测试客户');
    await page.getByPlaceholder('被告姓名').fill('对方当事人');
    await page.getByPlaceholder('请描述案件情况').fill('测试案件描述');
    
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/cases\/case-new/);
  });

  test('should view case details', async ({ page }) => {
    await page.goto('/cases');
    await page.click('[data-testid="case-card"]:first-child');
    await expect(page.getByText('借款合同纠纷')).toBeVisible();
  });

  test('should navigate to case sub-pages', async ({ page }) => {
    await page.goto('/cases/case-1');
    
    await page.getByRole('tab', { name: '证据' }).click();
    await expect(page).toHaveURL(/\/cases\/case-1\/evidence/);
    
    await page.getByRole('tab', { name: '文书' }).click();
    await expect(page).toHaveURL(/\/cases\/case-1\/documents/);
    
    await page.getByRole('tab', { name: '开庭/日程' }).click();
    await expect(page).toHaveURL(/\/cases\/case-1\/timeline/);
  });

  test('should enter batch mode', async ({ page }) => {
    await page.goto('/cases');
    await page.getByRole('button', { name: /批量操作/ }).click();
    await expect(page.getByText(/已选择|请选择要操作的案件/)).toBeVisible();
  });

  test('should search cases', async ({ page }) => {
    await page.goto('/cases');
    await expect(page.locator('[data-testid="case-card"]')).toHaveCount(1);
    await page.fill('input[placeholder*="搜索"]', '借款');
    await expect(page.locator('[data-testid="case-card"]')).toHaveCount(1);
  });
});
