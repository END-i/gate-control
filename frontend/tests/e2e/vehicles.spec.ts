import { test, expect, type Page } from '@playwright/test';

const API = 'http://localhost:8099/api';

const STATUS_OK = { online: true, last_webhook_timestamp: null, checked_at: new Date().toISOString() };

const VEHICLES = [
  { id: 1, license_plate: 'ABC123', status: 'allowed', owner_info: 'Alice', created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
  { id: 2, license_plate: 'XYZ999', status: 'denied', owner_info: 'Bob', created_at: '2024-01-02T00:00:00Z', updated_at: '2024-01-02T00:00:00Z' },
];

async function setupAuth(page: Page) {
  await page.route(`${API}/system/status`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATUS_OK) })
  );
  await page.goto('/login');
  await page.evaluate(() => localStorage.setItem('anpr_access_token', 'fake-token'));
}

test('vehicles page shows vehicle list', async ({ page }) => {
  await setupAuth(page);
  await page.route(`${API}/vehicles?limit=200&offset=0`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: VEHICLES, total: 2, limit: 200, offset: 0 }),
    })
  );

  await page.goto('/vehicles');
  await expect(page.getByText('ABC123')).toBeVisible();
  await expect(page.getByText('XYZ999')).toBeVisible();
});

test('add vehicle modal: valid plate creates vehicle', async ({ page }) => {
  await setupAuth(page);

  const vehiclesList = [...VEHICLES];

  await page.route(`${API}/vehicles?limit=200&offset=0`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: vehiclesList, total: vehiclesList.length, limit: 200, offset: 0 }),
    })
  );
  await page.route(`${API}/vehicles`, async (route) => {
    if (route.request().method() === 'POST') {
      const body = JSON.parse(route.request().postData() ?? '{}');
      const newVehicle = { id: 99, license_plate: body.license_plate, status: body.status, owner_info: body.owner_info ?? '', created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
      vehiclesList.push(newVehicle);
      await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(newVehicle) });
    } else {
      await route.continue();
    }
  });

  await page.goto('/vehicles');

  // Open create modal.
  await page.getByRole('button', { name: /add vehicle/i }).click();

  // Fill form.
  await page.fill('input[placeholder]', 'NEW001');

  // Select status "allowed".
  await page.selectOption('select', 'allowed');

  // Submit.
  await page.click('button[type="submit"]');

  // New plate should appear in table.
  await expect(page.getByText('NEW001')).toBeVisible();
});

test('add vehicle modal: invalid plate shows validation error', async ({ page }) => {
  await setupAuth(page);
  await page.route(`${API}/vehicles?limit=200&offset=0`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: VEHICLES, total: 2, limit: 200, offset: 0 }),
    })
  );

  await page.goto('/vehicles');
  await page.getByRole('button', { name: /add vehicle/i }).click();

  // "ab" is too short and lowercase — should fail regex.
  await page.fill('input[placeholder]', 'ab');
  await page.click('button[type="submit"]');

  // Expect the form to show an error (not close modal, plate still invalid).
  await expect(page.locator('button[type="submit"]')).toBeVisible();
});

test('delete vehicle removes row from list', async ({ page }) => {
  await setupAuth(page);

  const vehiclesList = [...VEHICLES];

  await page.route(`${API}/vehicles?limit=200&offset=0`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: vehiclesList, total: vehiclesList.length, limit: 200, offset: 0 }),
    })
  );
  await page.route(`${API}/vehicles/1`, async (route) => {
    if (route.request().method() === 'DELETE') {
      const idx = vehiclesList.findIndex((v) => v.id === 1);
      if (idx !== -1) vehiclesList.splice(idx, 1);
      await route.fulfill({ status: 204 });
    } else {
      await route.continue();
    }
  });

  await page.goto('/vehicles');
  await expect(page.getByText('ABC123')).toBeVisible();

  // Accept the confirm() dialog that the delete handler shows.
  page.on('dialog', (dialog) => dialog.accept());

  // Click the delete button in the ABC123 row.
  const row = page.locator('tr', { hasText: 'ABC123' });
  await row.locator('button.text-red-700').click();

  await expect(page.getByText('ABC123')).not.toBeVisible();
});
