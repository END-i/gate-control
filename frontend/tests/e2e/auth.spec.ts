import { test, expect, type Page } from '@playwright/test';

const API = 'http://localhost:8099/api';

const STATUS_OK = { online: true, last_webhook_timestamp: null, checked_at: new Date().toISOString() };

async function injectToken(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('anpr_access_token', 'fake-token');
  });
}

test('login page renders', async ({ page }) => {
  await page.goto('/login');
  await expect(page.locator('input[autocomplete="username"]')).toBeVisible();
  await expect(page.locator('input[autocomplete="current-password"]')).toBeVisible();
  await expect(page.locator('button[type="submit"]')).toBeVisible();
});

test('login success → redirects to dashboard', async ({ page }) => {
  await page.route(`${API}/auth/login`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ access_token: 'test-token', token_type: 'bearer' }),
    })
  );
  await page.route(`${API}/system/status`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATUS_OK) })
  );
  await page.route(`${API}/stats`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total_vehicles: 0, today_access_total: 0, today_denied_total: 0 }),
    })
  );

  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.fill('input[autocomplete="username"]', 'admin');
  await page.fill('input[autocomplete="current-password"]', 'secret');
  await page.locator('button[type="submit"]').click();

  await page.waitForURL('/');
  await expect(page).toHaveURL('/');
});

test('login failure → shows error message', async ({ page }) => {
  await page.route(`${API}/auth/login`, (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Invalid credentials' }),
    })
  );

  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.fill('input[autocomplete="username"]', 'admin');
  await page.fill('input[autocomplete="current-password"]', 'wrong');
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('p.text-red-600')).toBeVisible();
});

test('unauthenticated access to / redirects to login', async ({ page }) => {
  // No token in localStorage → layout guard should redirect.
  await page.goto('/');
  await page.waitForURL('/login');
  await expect(page).toHaveURL('/login');
});

test('logout → redirects to login', async ({ page }) => {
  await injectToken(page);
  await page.route(`${API}/system/status`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATUS_OK) })
  );
  await page.route(`${API}/stats`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total_vehicles: 0, today_access_total: 0, today_denied_total: 0 }),
    })
  );

  await page.goto('/');

  // Click logout button.
  const logoutBtn = page.getByRole('button', { name: /logout|вийти/i });
  await expect(logoutBtn).toBeVisible();
  await logoutBtn.click();

  await page.waitForURL('/login');
  await expect(page).toHaveURL('/login');
});
