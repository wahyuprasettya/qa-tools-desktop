import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('https://wahyuprasettya.github.io/');
  await page.getByRole('link', { name: 'Explore Projects' }).click();
  const page1Promise = page.waitForEvent('popup');
  await page.getByRole('article').filter({ hasText: 'MissionKedai Tengger APP☕' }).getByRole('link').click();
  const page1 = await page1Promise;
  await page.getByRole('link', { name: 'Blog' }).click();
  await page.getByRole('link', { name: 'About' }).click();
});