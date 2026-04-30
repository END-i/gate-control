# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> login success → redirects to dashboard
- Location: tests/e2e/auth.spec.ts:20:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.waitForURL: Test timeout of 30000ms exceeded.
=========================== logs ===========================
waiting for navigation to "/" until "load"
  navigated to "http://127.0.0.1:4173/login?"
============================================================
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - heading "Admin Login" [level=1] [ref=e4]
  - generic [ref=e5]:
    - generic [ref=e6]:
      - generic [ref=e7]: Username
      - textbox "Username" [ref=e8]
    - generic [ref=e9]:
      - generic [ref=e10]: Password
      - textbox "Password" [ref=e11]
    - button "Sign In" [ref=e12]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const API = 'http://localhost:8099/api';
  4  | 
  5  | const STATUS_OK = { online: true, last_webhook_timestamp: null, checked_at: new Date().toISOString() };
  6  | 
  7  | async function mockStatusEndpoint(page: Parameters<typeof test>[1] extends { page: infer P } ? P : never) {
  8  |   await page.route(`${API}/system/status`, (route) =>
  9  |     route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATUS_OK) })
  10 |   );
  11 | }
  12 | 
  13 | test('login page renders', async ({ page }) => {
  14 |   await page.goto('/login');
  15 |   await expect(page.locator('input[autocomplete="username"]')).toBeVisible();
  16 |   await expect(page.locator('input[autocomplete="current-password"]')).toBeVisible();
  17 |   await expect(page.locator('button[type="submit"]')).toBeVisible();
  18 | });
  19 | 
  20 | test('login success → redirects to dashboard', async ({ page }) => {
  21 |   await page.route(`${API}/auth/login`, (route) =>
  22 |     route.fulfill({
  23 |       status: 200,
  24 |       contentType: 'application/json',
  25 |       body: JSON.stringify({ access_token: 'test-token', token_type: 'bearer' }),
  26 |     })
  27 |   );
  28 |   await page.route(`${API}/system/status`, (route) =>
  29 |     route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATUS_OK) })
  30 |   );
  31 |   await page.route(`${API}/stats`, (route) =>
  32 |     route.fulfill({
  33 |       status: 200,
  34 |       contentType: 'application/json',
  35 |       body: JSON.stringify({ total_vehicles: 0, today_access_total: 0, today_denied_total: 0 }),
  36 |     })
  37 |   );
  38 | 
  39 |   await page.goto('/login');
  40 |   await page.fill('input[autocomplete="username"]', 'admin');
  41 |   await page.fill('input[autocomplete="current-password"]', 'secret');
  42 |   await page.click('button[type="submit"]');
  43 | 
> 44 |   await page.waitForURL('/');
     |              ^ Error: page.waitForURL: Test timeout of 30000ms exceeded.
  45 |   await expect(page).toHaveURL('/');
  46 | });
  47 | 
  48 | test('login failure → shows error message', async ({ page }) => {
  49 |   await page.route(`${API}/auth/login`, (route) =>
  50 |     route.fulfill({
  51 |       status: 401,
  52 |       contentType: 'application/json',
  53 |       body: JSON.stringify({ detail: 'Invalid credentials' }),
  54 |     })
  55 |   );
  56 | 
  57 |   await page.goto('/login');
  58 |   await page.fill('input[autocomplete="username"]', 'admin');
  59 |   await page.fill('input[autocomplete="current-password"]', 'wrong');
  60 |   await page.click('button[type="submit"]');
  61 | 
  62 |   await expect(page.locator('p.text-red-600')).toBeVisible();
  63 | });
  64 | 
  65 | test('unauthenticated access to / redirects to login', async ({ page }) => {
  66 |   // No token in localStorage → layout guard should redirect.
  67 |   await page.goto('/');
  68 |   await page.waitForURL('/login');
  69 |   await expect(page).toHaveURL('/login');
  70 | });
  71 | 
  72 | test('logout → redirects to login', async ({ page }) => {
  73 |   await page.route(`${API}/system/status`, (route) =>
  74 |     route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATUS_OK) })
  75 |   );
  76 |   await page.route(`${API}/stats`, (route) =>
  77 |     route.fulfill({
  78 |       status: 200,
  79 |       contentType: 'application/json',
  80 |       body: JSON.stringify({ total_vehicles: 0, today_access_total: 0, today_denied_total: 0 }),
  81 |     })
  82 |   );
  83 | 
  84 |   // Inject token before navigating.
  85 |   await page.goto('/login');
  86 |   await page.evaluate(() => localStorage.setItem('anpr_access_token', 'fake-token'));
  87 |   await page.goto('/');
  88 | 
  89 |   // Click logout button.
  90 |   const logoutBtn = page.getByRole('button', { name: /logout|вийти/i });
  91 |   await expect(logoutBtn).toBeVisible();
  92 |   await logoutBtn.click();
  93 | 
  94 |   await page.waitForURL('/login');
  95 |   await expect(page).toHaveURL('/login');
  96 | });
  97 | 
```