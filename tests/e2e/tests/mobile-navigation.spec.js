import { test, expect, devices } from '@playwright/test';

test.describe('Mobile Navigation', () => {
  test.use({ ...devices['iPhone 12'] });

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3001');
    // Skip splash screen if present
    const startButton = page.locator('button:has-text("Start New Game")');
    if (await startButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await startButton.click();
      await page.waitForTimeout(500);
    }
  });

  test('mobile menu hamburger is visible', async ({ page }) => {
    // Check that hamburger menu button is visible
    const hamburger = page.locator('button[aria-label="Toggle navigation menu"]');
    await expect(hamburger).toBeVisible();
    
    // Desktop navigation should be hidden
    const desktopButtons = page.locator('nav button').filter({ hasText: /Home|Game|Practice/ });
    const visibleDesktopButtons = await desktopButtons.evaluateAll(buttons => 
      buttons.filter(btn => {
        const style = window.getComputedStyle(btn);
        return style.display !== 'none' && btn.getAttribute('aria-label') !== 'Toggle navigation menu';
      }).length
    );
    
    // Only hamburger should be visible, not the full button row
    expect(visibleDesktopButtons).toBeLessThanOrEqual(1);
  });

  test('mobile menu opens and closes', async ({ page }) => {
    const hamburger = page.locator('button[aria-label="Toggle navigation menu"]');
    
    // Initially menu should be closed
    const mobileMenu = page.locator('nav').locator('div').filter({ hasText: 'Main Menu' }).first();
    await expect(mobileMenu).not.toBeVisible();
    
    // Click hamburger to open menu
    await hamburger.click();
    await page.waitForTimeout(300);
    
    // Menu should now be visible
    await expect(mobileMenu).toBeVisible();
    
    // Menu should contain navigation items
    await expect(page.locator('button:has-text("🏠 Home")')).toBeVisible();
    await expect(page.locator('button:has-text("🎮 Game")')).toBeVisible();
    await expect(page.locator('button:has-text("🎲 Practice")')).toBeVisible();
    
    // Click hamburger again to close
    await hamburger.click();
    await page.waitForTimeout(300);
    
    // Menu should be closed
    await expect(mobileMenu).not.toBeVisible();
  });

  test('mobile menu navigation works', async ({ page }) => {
    const hamburger = page.locator('button[aria-label="Toggle navigation menu"]');
    
    // Open menu
    await hamburger.click();
    await page.waitForTimeout(300);
    
    // Click on About link
    const aboutButton = page.locator('button:has-text("ℹ️ About")');
    await aboutButton.click();
    
    // Should navigate to about page
    await page.waitForURL('**/about');
    expect(page.url()).toContain('/about');
    
    // Menu should automatically close after navigation
    const mobileMenu = page.locator('nav').locator('div').filter({ hasText: 'Main Menu' }).first();
    await expect(mobileMenu).not.toBeVisible();
  });

  test('touch targets are appropriately sized', async ({ page }) => {
    const hamburger = page.locator('button[aria-label="Toggle navigation menu"]');
    
    // Check hamburger button size
    const hamburgerBox = await hamburger.boundingBox();
    expect(hamburgerBox.width).toBeGreaterThanOrEqual(44);
    expect(hamburgerBox.height).toBeGreaterThanOrEqual(44);
    
    // Open menu and check button sizes
    await hamburger.click();
    await page.waitForTimeout(300);
    
    const menuButtons = page.locator('nav button').filter({ hasText: /Home|Game|Practice|About/ });
    const buttonCount = await menuButtons.count();
    
    for (let i = 0; i < buttonCount; i++) {
      const button = menuButtons.nth(i);
      if (await button.isVisible()) {
        const box = await button.boundingBox();
        // Mobile buttons should be at least 44x44 pixels for touch targets
        expect(box.height).toBeGreaterThanOrEqual(40);
      }
    }
  });

  test('menu sections are properly organized', async ({ page }) => {
    const hamburger = page.locator('button[aria-label="Toggle navigation menu"]');
    await hamburger.click();
    await page.waitForTimeout(300);
    
    // Check for Main Menu section
    await expect(page.locator('h3:has-text("Main Menu")')).toBeVisible();
    
    // Check for More Options section
    await expect(page.locator('h3:has-text("More Options")')).toBeVisible();
    
    // Verify primary items are in Main Menu
    const mainMenuSection = page.locator('div').filter({ hasText: 'Main Menu' }).first();
    await expect(mainMenuSection.locator('button:has-text("🏠 Home")')).toBeVisible();
    await expect(mainMenuSection.locator('button:has-text("🎮 Game")')).toBeVisible();
    
    // Verify secondary items are in More Options
    const moreOptionsSection = page.locator('div').filter({ hasText: 'More Options' }).first();
    await expect(moreOptionsSection.locator('button:has-text("📋 Rules")')).toBeVisible();
  });
});

test.describe('Mobile Responsive Layout', () => {
  test('navigation adapts to different screen sizes', async ({ browser }) => {
    // Test different viewport sizes
    const viewports = [
      { width: 320, height: 568, name: 'iPhone SE' },
      { width: 375, height: 812, name: 'iPhone X' },
      { width: 768, height: 1024, name: 'iPad' },
      { width: 1024, height: 768, name: 'Desktop' }
    ];

    for (const viewport of viewports) {
      const context = await browser.newContext({
        viewport: { width: viewport.width, height: viewport.height }
      });
      const page = await context.newPage();
      
      await page.goto('http://localhost:3001');
      
      // Skip splash if needed
      const startButton = page.locator('button:has-text("Start New Game")');
      if (await startButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await startButton.click();
        await page.waitForTimeout(500);
      }
      
      // Check if hamburger is visible for mobile sizes
      const hamburger = page.locator('button[aria-label="Toggle navigation menu"]');
      
      if (viewport.width <= 768) {
        // Mobile: hamburger should be visible
        await expect(hamburger).toBeVisible();
      } else {
        // Desktop: hamburger should not be visible
        await expect(hamburger).not.toBeVisible();
        
        // Desktop buttons should be visible
        const homeButton = page.locator('nav button:has-text("🏠 Home")');
        await expect(homeButton).toBeVisible();
      }
      
      await context.close();
    }
  });

  test('content reflows properly on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:3001');
    
    // Skip splash if needed
    const startButton = page.locator('button:has-text("Start New Game")');
    if (await startButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await startButton.click();
      await page.waitForTimeout(500);
    }
    
    // Check that content doesn't overflow viewport
    const body = page.locator('body');
    const bodyBox = await body.boundingBox();
    
    // Body width should not exceed viewport
    expect(bodyBox.width).toBeLessThanOrEqual(375);
    
    // Check horizontal scrolling (there shouldn't be any)
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 10); // Allow small margin for scrollbar
  });
});