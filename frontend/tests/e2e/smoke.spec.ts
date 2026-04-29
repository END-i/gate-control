import { expect, test } from '@playwright/test';

test('login page renders', async ({ page }) => {
  await page.goto('/login');

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.locator('input[autocomplete="username"]')).toBeVisible();
  await expect(page.locator('input[autocomplete="current-password"]')).toBeVisible();
  await expect(page.locator('button[type="submit"]')).toBeVisible();
});
