import { test, expect, mockApi } from './fixtures';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page);
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto('/');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/');
    await page.fill('input[name="username"]', 'invalid');
    await page.fill('input[name="password"]', 'wrong');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=用户名或密码错误')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    await page.goto('/');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
    
    await page.getByLabel('用户菜单').click();
    await page.getByRole('button', { name: /退出登录/ }).click();
    await expect(page).toHaveURL(/\/login/);
  });
});
