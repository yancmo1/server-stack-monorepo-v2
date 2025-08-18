import { test, expect } from '@playwright/test';

test('happy path: navigate through app and add a race', async ({ page }) => {
  // Start at the home page
  await page.goto('http://localhost:7777');

  // Check that we're on the dashboard
  await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();

  // Navigate to races page
  await page.getByRole('link', { name: /races/i }).click();
  await expect(page.getByRole('heading', { name: /races/i })).toBeVisible();

  // Click "Add Race" button
  await page.getByRole('link', { name: /add race/i }).click();
  await expect(page.getByRole('heading', { name: /add new race/i })).toBeVisible();

  // Fill out the form
  await page.getByRole('textbox', { name: /date/i }).fill('2024-01-20');
  await page.getByRole('combobox', { name: /distance/i }).selectOption('5');
  await page.getByRole('textbox', { name: /duration/i }).fill('24:30');
  await page.getByRole('textbox', { name: /location/i }).fill('Test Park');
  await page.getByRole('textbox', { name: /weather/i }).fill('Sunny, 20°C');
  await page.getByRole('textbox', { name: /notes/i }).fill('Great test run!');

  // Submit the form
  await page.getByRole('button', { name: /save race/i }).click();

  // Should be back on races page
  await expect(page.getByRole('heading', { name: /races/i })).toBeVisible();

  // Navigate to analytics
  await page.getByRole('link', { name: /analytics/i }).click();
  await expect(page.getByRole('heading', { name: /analytics/i })).toBeVisible();
  
  // Check that charts are present
  await expect(page.getByText('Monthly Runs Count')).toBeVisible();
  await expect(page.getByText('Average Pace Trend')).toBeVisible();
  await expect(page.getByText('Personal Records')).toBeVisible();
});