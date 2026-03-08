// @ts-check
import { test, expect } from '@playwright/test';

const ROUTES = [
  { path: '/', name: 'Home', heading: 'Home' },
  { path: '/careers/pathfinder', name: 'Pathfinder', heading: 'Where you are' },
  { path: '/careers/pathfinder/map', name: 'Career Map', heading: 'Career Map' },
  { path: '/skillbridge', name: 'SkillBridge', heading: 'SkillBridge Explorer' },
  { path: '/benefits', name: 'Benefits', heading: 'Benefits' },
  { path: '/communities', name: 'Communities', heading: 'Communities' },
  { path: '/employment/ergs', name: 'ERGs', heading: 'ERG Directory' },
  { path: '/employment/networking', name: 'Networking', heading: 'Employment Networking' },
  { path: '/news', name: 'News', heading: 'VA News' },
  { path: '/dashboard', name: 'Dashboard', heading: 'Dashboard' },
];

test.describe('FOB site — user journey', () => {
  test('home page loads and shows app shell', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('h1', { state: 'visible', timeout: 15000 });
    await expect(page.locator('h1')).toContainText('Home');
    await expect(page.getByRole('link', { name: /THE FOB/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Sign In/i })).toBeVisible();
  });

  test('every main route loads with correct content', async ({ page }) => {
    for (const { path, name, heading } of ROUTES) {
      await page.goto(path, { waitUntil: 'domcontentloaded' });
      await expect(page.locator('h1')).toContainText(heading, { timeout: 15000 });
    }
  });

  test('nav links navigate to correct pages', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('h1', { state: 'visible', timeout: 15000 });
    const nav = page.getByRole('navigation').first();
    for (const { path, name, heading } of ROUTES) {
      const link = nav.getByRole('link', { name: new RegExp(name, 'i') }).first();
      await link.click();
      await expect(page).toHaveURL(new RegExp(path.replace(/\//g, '\\/') + '(\\?|$)', 'i'));
      await expect(page.locator('h1')).toContainText(heading, { timeout: 10000 });
    }
  });

  test('footer links work', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('footer', { state: 'visible', timeout: 15000 });
    const footer = page.locator('footer');
    await footer.getByRole('link', { name: 'Pathfinder' }).click();
    await expect(page).toHaveURL(/\/careers\/pathfinder/);
    await footer.getByRole('link', { name: 'Benefits' }).click();
    await expect(page).toHaveURL(/\/benefits/);
    await expect(page.locator('h1')).toContainText('Benefits');
  });

  test('logo links back to home', async ({ page }) => {
    await page.goto('/benefits', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('h1', { state: 'visible', timeout: 15000 });
    await page.getByRole('navigation').getByRole('link', { name: /THE FOB/i }).click();
    await expect(page).toHaveURL('/');
    await expect(page.locator('h1')).toContainText('Home');
  });

  test('404 page shows and Back to Home works', async ({ page }) => {
    await page.goto('/nonexistent-page-xyz', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1')).toContainText('404', { timeout: 15000 });
    await expect(page.getByRole('link', { name: 'Back to Home' })).toBeVisible();
    await page.getByRole('link', { name: 'Back to Home' }).click();
    await expect(page).toHaveURL('/');
    await expect(page.locator('h1')).toContainText('Home');
  });

  test('Sign In opens auth modal', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('h1', { state: 'visible', timeout: 15000 });
    await page.getByRole('button', { name: /Sign In/i }).first().click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 5000 });
    await expect(dialog.getByRole('tab', { name: 'Sign In' })).toBeVisible();
  });

  test('Pathfinder page has form and Generate button', async ({ page }) => {
    await page.goto('/careers/pathfinder', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1')).toContainText('Where you are', { timeout: 15000 });
    await expect(page.getByRole('button', { name: /Generate|Get roadmap/i })).toBeVisible({ timeout: 10000 });
  });

  test('mobile menu opens and nav links work', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('h1', { state: 'visible', timeout: 15000 });
    await page.getByRole('button', { name: /Open menu/i }).click();
    await expect(page.getByRole('link', { name: 'Pathfinder' })).toBeVisible();
    await page.getByRole('link', { name: 'Benefits' }).click();
    await expect(page).toHaveURL(/\/benefits/);
    await expect(page.locator('h1')).toContainText('Benefits');
  });
});
