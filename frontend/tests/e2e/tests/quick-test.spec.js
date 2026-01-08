/**
 * Quick test without global setup/teardown
 */
import { test, expect } from '@playwright/test';

test('quick scorekeeper check', async ({ page }) => {
  await page.goto('http://localhost:3333/simple-scorekeeper');
  await page.waitForTimeout(3000);
  
  const bodyText = await page.textContent('body');
  console.log('Page content:', bodyText?.slice(0, 800));
  
  await page.screenshot({ path: 'test-results/quick-test.png', fullPage: true });
  
  // Check for login button
  const loginBtn = await page.locator('button:has-text("Log In")').isVisible().catch(() => false);
  console.log('Login button visible:', loginBtn);
  
  if (!loginBtn) {
    // We're past login! Check for scorekeeper elements
    const buttons = await page.locator('button').count();
    console.log('Buttons on page:', buttons);
  }
});
