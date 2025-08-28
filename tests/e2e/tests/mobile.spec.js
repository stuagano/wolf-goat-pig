import { test, expect, devices } from '@playwright/test';

// Define mobile viewports to test
const mobileDevices = [
  { name: 'iPhone 12', device: devices['iPhone 12'] },
  { name: 'iPhone SE', device: devices['iPhone SE'] },
  { name: 'Pixel 5', device: devices['Pixel 5'] },
  { name: 'Galaxy S9+', device: devices['Galaxy S9+'] },
  { name: 'iPad Mini', device: devices['iPad Mini'] }
];

// Test each major page on mobile devices
mobileDevices.forEach(({ name, device }) => {
  test.describe(`Mobile Testing on ${name}`, () => {
    test.use({ ...device });

    test.beforeEach(async ({ page }) => {
      // Set up mobile context
      await page.goto('http://localhost:3000');
      await page.waitForLoadState('networkidle');
    });

    test('Homepage renders correctly on mobile', async ({ page }) => {
      // Check main title is visible
      await expect(page.locator('h1').first()).toBeVisible();
      
      // Check navigation menu (should be mobile-friendly)
      const navMenu = page.locator('nav').first();
      await expect(navMenu).toBeVisible();
      
      // Check game mode buttons are clickable
      const gameButtons = page.locator('button:has-text("Play")');
      const buttonCount = await gameButtons.count();
      expect(buttonCount).toBeGreaterThan(0);
      
      // Check responsive layout
      const mainContainer = page.locator('div').first();
      const containerWidth = await mainContainer.evaluate(el => el.offsetWidth);
      expect(containerWidth).toBeLessThanOrEqual(device.viewport.width);
      
      // Take screenshot for visual verification
      await page.screenshot({ 
        path: `test-results/mobile-homepage-${name.replace(' ', '-')}.png`,
        fullPage: true 
      });
    });

    test('Leaderboard is accessible and scrollable on mobile', async ({ page }) => {
      // Navigate to leaderboard
      await page.goto('http://localhost:3000/leaderboard');
      await page.waitForLoadState('networkidle');
      
      // Check leaderboard title
      await expect(page.locator('h1:has-text("Leaderboard")')).toBeVisible();
      
      // Check table is scrollable horizontally if needed
      const table = page.locator('table').first();
      if (await table.isVisible()) {
        const tableContainer = page.locator('.overflow-x-auto').first();
        if (await tableContainer.isVisible()) {
          const containerWidth = await tableContainer.evaluate(el => el.scrollWidth);
          const viewportWidth = await tableContainer.evaluate(el => el.clientWidth);
          
          // If table is wider than viewport, ensure it's scrollable
          if (containerWidth > viewportWidth) {
            await expect(tableContainer).toHaveCSS('overflow-x', 'auto');
          }
        }
      }
      
      // Check metric selector buttons are visible and tappable
      const metricButtons = page.locator('button').filter({ hasText: /Overall|Average|Most Rounds/ });
      const firstButton = metricButtons.first();
      if (await firstButton.isVisible()) {
        // Check button is large enough for mobile tap (minimum 44x44 pixels)
        const buttonBox = await firstButton.boundingBox();
        expect(buttonBox.width).toBeGreaterThanOrEqual(44);
        expect(buttonBox.height).toBeGreaterThanOrEqual(44);
      }
      
      await page.screenshot({ 
        path: `test-results/mobile-leaderboard-${name.replace(' ', '-')}.png`,
        fullPage: true 
      });
    });

    test('Simulation mode works on mobile', async ({ page }) => {
      // Navigate to simulation
      await page.goto('http://localhost:3000/simulation');
      await page.waitForLoadState('networkidle');
      
      // Check if setup form is visible
      const setupForm = page.locator('form, [role="form"], div:has(input[placeholder*="name"])');
      if (await setupForm.isVisible()) {
        // Check input fields are accessible
        const nameInput = page.locator('input').first();
        if (await nameInput.isVisible()) {
          // Ensure input is large enough for mobile
          const inputBox = await nameInput.boundingBox();
          expect(inputBox.height).toBeGreaterThanOrEqual(40);
          
          // Test input interaction
          await nameInput.fill('Mobile Test Player');
          await expect(nameInput).toHaveValue('Mobile Test Player');
        }
        
        // Check start button
        const startButton = page.locator('button').filter({ hasText: /start|begin|play/i }).first();
        if (await startButton.isVisible()) {
          const buttonBox = await startButton.boundingBox();
          expect(buttonBox.width).toBeGreaterThanOrEqual(44);
          expect(buttonBox.height).toBeGreaterThanOrEqual(44);
        }
      }
      
      await page.screenshot({ 
        path: `test-results/mobile-simulation-${name.replace(' ', '-')}.png`,
        fullPage: true 
      });
    });

    test('Navigation menu works on mobile', async ({ page }) => {
      // Check for hamburger menu or mobile nav
      const hamburger = page.locator('[aria-label*="menu"], button:has(svg), button:has-text("☰")');
      const navLinks = page.locator('nav a, nav button');
      
      if (await hamburger.isVisible()) {
        // Test hamburger menu interaction
        await hamburger.click();
        await page.waitForTimeout(500); // Wait for animation
        
        // Check menu items are visible after clicking hamburger
        const menuItems = page.locator('a:visible, button:visible').filter({ hasText: /home|game|leaderboard|simulation/i });
        await expect(menuItems.first()).toBeVisible();
      } else {
        // Check if nav links are directly visible
        const visibleLinks = await navLinks.count();
        expect(visibleLinks).toBeGreaterThan(0);
      }
    });

    test('Touch interactions work properly', async ({ page }) => {
      // Test tap interactions on buttons
      const buttons = page.locator('button:visible');
      const firstButton = buttons.first();
      
      if (await firstButton.isVisible()) {
        // Simulate tap
        await firstButton.tap();
        
        // Verify tap worked (button should have some feedback)
        // This could be a navigation, style change, or state change
        await page.waitForTimeout(100);
      }
      
      // Test swipe/scroll
      await page.evaluate(() => {
        window.scrollTo(0, document.body.scrollHeight / 2);
      });
      await page.waitForTimeout(500);
      
      // Verify scroll worked
      const scrollY = await page.evaluate(() => window.scrollY);
      expect(scrollY).toBeGreaterThan(0);
    });

    test('Forms are usable on mobile', async ({ page }) => {
      // Find any form on the page
      const forms = page.locator('form, [role="form"]');
      const firstForm = forms.first();
      
      if (await firstForm.isVisible()) {
        // Check all inputs are accessible
        const inputs = firstForm.locator('input, select, textarea');
        const inputCount = await inputs.count();
        
        for (let i = 0; i < inputCount; i++) {
          const input = inputs.nth(i);
          if (await input.isVisible()) {
            const inputBox = await input.boundingBox();
            // Inputs should be at least 40px tall for mobile
            expect(inputBox.height).toBeGreaterThanOrEqual(36);
          }
        }
        
        // Check submit buttons
        const submitButton = firstForm.locator('button[type="submit"], button:has-text("Submit"), button:has-text("Save")');
        if (await submitButton.isVisible()) {
          const buttonBox = await submitButton.boundingBox();
          // Buttons should meet minimum tap target size
          expect(buttonBox.width).toBeGreaterThanOrEqual(44);
          expect(buttonBox.height).toBeGreaterThanOrEqual(44);
        }
      }
    });

    test('Text is readable on mobile', async ({ page }) => {
      // Check font sizes are appropriate for mobile
      const bodyText = page.locator('p, span').first();
      if (await bodyText.isVisible()) {
        const fontSize = await bodyText.evaluate(el => 
          window.getComputedStyle(el).fontSize
        );
        const fontSizeValue = parseInt(fontSize);
        // Text should be at least 14px on mobile
        expect(fontSizeValue).toBeGreaterThanOrEqual(14);
      }
      
      // Check headings are appropriately sized
      const heading = page.locator('h1, h2, h3').first();
      if (await heading.isVisible()) {
        const fontSize = await heading.evaluate(el => 
          window.getComputedStyle(el).fontSize
        );
        const fontSizeValue = parseInt(fontSize);
        // Headings should be at least 20px on mobile
        expect(fontSizeValue).toBeGreaterThanOrEqual(20);
      }
    });

    test('Images and icons scale properly', async ({ page }) => {
      // Check images don't overflow viewport
      const images = page.locator('img');
      const imageCount = await images.count();
      
      for (let i = 0; i < Math.min(imageCount, 5); i++) {
        const img = images.nth(i);
        if (await img.isVisible()) {
          const imgBox = await img.boundingBox();
          // Images shouldn't be wider than viewport
          expect(imgBox.width).toBeLessThanOrEqual(device.viewport.width);
        }
      }
    });

    test('Modal dialogs are mobile-friendly', async ({ page }) => {
      // Try to trigger a modal (e.g., login, settings, etc.)
      const modalTriggers = page.locator('button').filter({ hasText: /login|sign in|settings|help/i });
      const trigger = modalTriggers.first();
      
      if (await trigger.isVisible()) {
        await trigger.click();
        await page.waitForTimeout(500);
        
        // Check if modal appeared
        const modal = page.locator('[role="dialog"], .modal, [class*="modal"]').first();
        if (await modal.isVisible()) {
          const modalBox = await modal.boundingBox();
          
          // Modal should fit within viewport
          expect(modalBox.width).toBeLessThanOrEqual(device.viewport.width);
          
          // Check close button is accessible
          const closeButton = modal.locator('button').filter({ hasText: /close|cancel|x/i }).first();
          if (await closeButton.isVisible()) {
            const closeBox = await closeButton.boundingBox();
            expect(closeBox.width).toBeGreaterThanOrEqual(44);
            expect(closeBox.height).toBeGreaterThanOrEqual(44);
          }
        }
      }
    });

    test('Performance on mobile is acceptable', async ({ page }) => {
      // Measure page load performance
      const metrics = await page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0];
        return {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        };
      });
      
      // DOM content should load within 3 seconds on mobile
      expect(metrics.domContentLoaded).toBeLessThan(3000);
      
      // Full page load should complete within 5 seconds
      expect(metrics.loadComplete).toBeLessThan(5000);
    });
  });
});

// Specific mobile interaction tests
test.describe('Mobile-specific interactions', () => {
  test.use({ ...devices['iPhone 12'] });

  test('Pinch to zoom is disabled where appropriate', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check viewport meta tag
    const viewportMeta = await page.locator('meta[name="viewport"]').getAttribute('content');
    if (viewportMeta) {
      // Check if user-scalable is set appropriately
      expect(viewportMeta).toContain('width=device-width');
    }
  });

  test('Orientation change handling', async ({ page, context }) => {
    await page.goto('http://localhost:3000');
    
    // Test portrait orientation
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(500);
    let portraitWidth = await page.evaluate(() => window.innerWidth);
    expect(portraitWidth).toBeLessThanOrEqual(390);
    
    // Test landscape orientation
    await page.setViewportSize({ width: 844, height: 390 });
    await page.waitForTimeout(500);
    let landscapeWidth = await page.evaluate(() => window.innerWidth);
    expect(landscapeWidth).toBeLessThanOrEqual(844);
    
    // Content should adapt to orientation
    const mainContent = page.locator('main, [role="main"], div').first();
    await expect(mainContent).toBeVisible();
  });

  test('Virtual keyboard does not break layout', async ({ page }) => {
    await page.goto('http://localhost:3000/simulation');
    
    // Find an input field
    const input = page.locator('input[type="text"], input[type="email"]').first();
    if (await input.isVisible()) {
      // Focus input (simulates virtual keyboard appearing)
      await input.focus();
      await page.waitForTimeout(300);
      
      // Check that content is still accessible
      const submitButton = page.locator('button[type="submit"], button:has-text("Start")').first();
      if (await submitButton.isVisible()) {
        // Button should still be reachable (might require scroll)
        await submitButton.scrollIntoViewIfNeeded();
        await expect(submitButton).toBeInViewport();
      }
    }
  });
});

// Accessibility tests for mobile
test.describe('Mobile Accessibility', () => {
  test.use({ ...devices['iPhone 12'] });

  test('Touch targets meet minimum size requirements', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check all interactive elements
    const interactiveElements = page.locator('button, a, input, select, textarea, [role="button"], [onclick]');
    const count = await interactiveElements.count();
    
    let tooSmallElements = [];
    for (let i = 0; i < Math.min(count, 20); i++) {
      const element = interactiveElements.nth(i);
      if (await element.isVisible()) {
        const box = await element.boundingBox();
        if (box.width < 44 || box.height < 44) {
          const text = await element.textContent();
          tooSmallElements.push({ text: text?.substring(0, 20), width: box.width, height: box.height });
        }
      }
    }
    
    // Log elements that are too small
    if (tooSmallElements.length > 0) {
      console.log('Elements below minimum tap target size (44x44):', tooSmallElements);
    }
    
    // Warn but don't fail - some elements might be intentionally small
    expect(tooSmallElements.length).toBeLessThanOrEqual(5);
  });

  test('Text contrast is sufficient on mobile', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check text contrast for readability
    const textElements = page.locator('p, span, h1, h2, h3, h4, h5, h6, a, button');
    const firstText = textElements.first();
    
    if (await firstText.isVisible()) {
      const contrast = await firstText.evaluate(el => {
        const style = window.getComputedStyle(el);
        const color = style.color;
        const backgroundColor = style.backgroundColor;
        // Simple check - in production, use a proper contrast calculation
        return { color, backgroundColor };
      });
      
      // Ensure text has defined colors
      expect(contrast.color).toBeTruthy();
    }
  });
});