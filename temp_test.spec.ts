import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('https://sandbox.demo-rst7.rschooltoday.com/ado-52434/');
  await page.getByRole('button', { name: 'Select Sports Filter' }).click();
  await page.getByText('Futsal').click();
  await page.locator('.lucide').first().click();
  await page.getByRole('button', { name: '← Previous' }).click();
  await page.getByRole('button', { name: '← Next' }).click();
  await page.getByRole('button', { name: 'View game details' }).nth(2).click();
  await page.getByRole('button', { name: 'Close modal' }).click();
  await page.getByRole('button', { name: 'View game details' }).nth(1).click();
  const page1Promise = page.waitForEvent('popup');
  await page.getByRole('button', { name: 'Open directions in maps for' }).click();
  const page1 = await page1Promise;
});