import { test, expect } from '@playwright/test';

const API = 'http://localhost:8099/api';

const STATUS_OK = { online: true, last_webhook_timestamp: null, checked_at: new Date().toISOString() };

const STATS = { total_vehicles: 42, today_access_total: 17, today_denied_total: 3 };

test('dashboard shows all three stats', async ({ page }) => {
  await page.route(`${API}/system/status`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATUS_OK) })
  );
  await page.route(`${API}/stats`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATS) })
  );

  // Inject auth token.
  await page.goto('/login');
  await page.evaluate(() => localStorage.setItem('anpr_access_token', 'fake-token'));
  await page.goto('/');

  // All three stat values must be visible on the page.
  await expect(page.getByText('42')).toBeVisible();
  await expect(page.getByText('17')).toBeVisible();
  await expect(page.getByText('3')).toBeVisible();
});

test('dashboard system status indicator shows online', async ({ page }) => {
  await page.route(`${API}/system/status`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATUS_OK) })
  );
  await page.route(`${API}/stats`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATS) })
  );

  await page.goto('/login');
  await page.evaluate(() => localStorage.setItem('anpr_access_token', 'fake-token'));
  await page.goto('/');

  // The green dot + "online" text from SystemStatusIndicator.
  const indicator = page.locator('[data-testid="system-status"]');
  await expect(indicator).toBeVisible();
  await expect(indicator.locator('.bg-green-500')).toBeVisible();
});

test('dashboard system status indicator shows offline when API fails', async ({ page }) => {
  await page.route(`${API}/system/status`, (route) => route.abort());
  await page.route(`${API}/stats`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATS) })
  );

  await page.goto('/login');
  await page.evaluate(() => localStorage.setItem('anpr_access_token', 'fake-token'));
  await page.goto('/');

  const indicator = page.locator('[data-testid="system-status"]');
  await expect(indicator).toBeVisible();
  await expect(indicator.locator('.bg-red-500')).toBeVisible();
});
