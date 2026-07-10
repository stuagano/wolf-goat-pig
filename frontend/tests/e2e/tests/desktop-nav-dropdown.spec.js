/**
 * Regression test for a real production bug: the desktop "More" dropdown's
 * z-index only counted inside <nav>'s own (lower) stacking context, so a
 * page-level "click outside to close" overlay sat on top of the entire nav
 * bar and silently swallowed every click inside the dropdown — no console
 * error, no failed request, just a menu that visually closes and never
 * navigates. jsdom/vitest can't catch this class of bug (no real paint/hit-
 * testing), which is why this lives here instead of a unit test.
 */
import { test, expect } from '@playwright/test';

test.describe('Desktop nav "More" dropdown', () => {
  test.use({ viewport: { width: 1280, height: 800 } });

  test('clicking a dropdown link actually navigates, not just closes the menu', async ({ page }) => {
    // Land on a non-home route so the login/splash screen (which only guards
    // "/") is bypassed and the real Navigation bar renders.
    await page.goto('/rules');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /more/i }).click();

    const playersLink = page.getByRole('button', { name: /players/i });
    await expect(playersLink).toBeVisible();
    await playersLink.click();

    await expect(page).toHaveURL(/\/players$/);
    await expect(page.getByRole('heading', { name: 'Players' })).toBeVisible();
  });
});
