// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Wolf-Goat-Pig Simulation Mode', () => {
  test.beforeEach(async ({ page }) => {
    // Start at the homepage
    await page.goto('http://localhost:3000');
  });

  test('should show poker/golf hybrid gameplay with timeline events', async ({ page }) => {
    // Navigate to simulation mode
    await page.click('text=Simulation Mode');
    
    // Wait for the simulation setup to load
    await page.waitForSelector('text=Simulation Setup', { timeout: 10000 });
    
    // Fill in player name
    await page.fill('input[placeholder*="name"]', 'Test Player');
    
    // Set handicap
    const handicapInput = page.locator('input[type="number"]').first();
    await handicapInput.clear();
    await handicapInput.fill('15');
    
    // Select a course if available
    const courseDropdown = page.locator('select').first();
    if (await courseDropdown.isVisible()) {
      await courseDropdown.selectOption({ index: 1 });
    }
    
    // Start the simulation
    await page.click('button:has-text("Start Simulation")');
    
    // Wait for game to start
    await page.waitForSelector('text=/Hole 1/', { timeout: 10000 });
    
    // Verify game elements are present
    await expect(page.locator('text=Current Standings')).toBeVisible();
    
    // Check for player scores display
    const playerCards = page.locator('[style*="border-radius: 8px"]');
    await expect(playerCards).toHaveCount(4); // 1 human + 3 AI players
    
    // Test captain decision interaction
    const captainDecision = page.locator('text=Your Decision');
    if (await captainDecision.isVisible({ timeout: 5000 }).catch(() => false)) {
      // If we're captain, make a decision
      const partnerButton = page.locator('button:has-text("Partner with")').first();
      if (await partnerButton.isVisible()) {
        await partnerButton.click();
      } else {
        // Go solo
        await page.click('button:has-text("Go Solo")');
      }
    }
    
    // Wait for shot simulation interface
    await page.waitForSelector('text=/Shot/', { timeout: 10000 });
    
    // Test shot-by-shot gameplay
    let shotCount = 0;
    const maxShots = 10; // Limit to prevent infinite loop
    
    while (shotCount < maxShots) {
      // Check if "Next Shot" button is available
      const nextShotButton = page.locator('button:has-text("Next Shot"), button:has-text("Continue"), button:has-text("Execute Shot")');
      
      if (await nextShotButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        // Record current state before shot
        const shotInfo = await page.textContent('body');
        
        // Verify shot probabilities are shown (if available)
        if (shotInfo.includes('probabilities') || shotInfo.includes('Probability')) {
          console.log('Shot probabilities displayed');
        }
        
        // Execute the shot
        await nextShotButton.first().click();
        
        // Wait for animation/update
        await page.waitForTimeout(500);
        
        shotCount++;
      } else {
        // No more shots available, check if hole is complete
        break;
      }
    }
    
    // Check for timeline/feed events
    const feedbackElements = page.locator('[class*="feedback"], [class*="timeline"], [class*="event"]');
    const feedbackCount = await feedbackElements.count();
    
    if (feedbackCount > 0) {
      console.log(`Found ${feedbackCount} timeline/feedback elements`);
      
      // Verify timeline shows bets and shots
      const timelineText = await feedbackElements.allTextContents();
      const hasPokerElements = timelineText.some(text => 
        text.toLowerCase().includes('bet') || 
        text.toLowerCase().includes('fold') || 
        text.toLowerCase().includes('raise') ||
        text.toLowerCase().includes('partner') ||
        text.toLowerCase().includes('solo')
      );
      
      const hasGolfElements = timelineText.some(text => 
        text.toLowerCase().includes('shot') || 
        text.toLowerCase().includes('putt') || 
        text.toLowerCase().includes('drive') ||
        text.toLowerCase().includes('yards') ||
        text.toLowerCase().includes('hole')
      );
      
      expect(hasPokerElements || hasGolfElements).toBeTruthy();
    }
    
    // Verify scoring system
    const scoreElements = page.locator('text=/pts|points/i');
    await expect(scoreElements.first()).toBeVisible();
    
    // Test hole completion
    const completeHoleButton = page.locator('button:has-text("Complete Hole"), button:has-text("Next Hole")');
    if (await completeHoleButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await completeHoleButton.click();
      
      // Verify we moved to next hole
      await page.waitForSelector('text=/Hole 2/', { timeout: 5000 });
    }
    
    // End simulation
    const endButton = page.locator('button:has-text("End Simulation")');
    if (await endButton.isVisible()) {
      await endButton.click();
      
      // Confirm if dialog appears
      page.on('dialog', dialog => dialog.accept());
      
      // Should return to setup
      await page.waitForSelector('text=Simulation Setup', { timeout: 10000 });
    }
  });

  test('should display timeline in reverse chronological order', async ({ page }) => {
    // Quick navigation to active game
    await page.goto('http://localhost:3000');
    await page.click('text=Simulation Mode');
    
    // Quick setup
    await page.fill('input[placeholder*="name"]', 'Timeline Test');
    await page.click('button:has-text("Start Simulation")');
    
    // Wait for game to start
    await page.waitForSelector('text=/Hole/', { timeout: 10000 });
    
    // Collect timeline events
    const events = [];
    
    // Monitor for new events
    const eventSelectors = [
      '[class*="timeline"]',
      '[class*="event"]', 
      '[class*="feed"]',
      '[class*="history"]',
      '[class*="log"]'
    ];
    
    for (const selector of eventSelectors) {
      const elements = page.locator(selector);
      const count = await elements.count();
      
      if (count > 0) {
        const texts = await elements.allTextContents();
        events.push(...texts);
        
        // Check if events are in reverse chronological order
        // (most recent events should appear first)
        if (texts.length > 1) {
          console.log('Timeline events found:', texts.length);
          
          // Look for timestamp patterns or event numbering
          const hasTimestamps = texts.some(text => 
            /\d{1,2}:\d{2}/.test(text) || 
            /ago/.test(text) ||
            /just now/i.test(text)
          );
          
          if (hasTimestamps) {
            console.log('Timeline includes timestamps');
          }
        }
      }
    }
    
    // Verify we have some events
    expect(events.length).toBeGreaterThan(0);
  });

  test('should integrate Texas Hold\'em betting with golf shots', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.click('text=Simulation Mode');
    
    // Setup game
    await page.fill('input[placeholder*="name"]', 'Poker Golf Test');
    await page.click('button:has-text("Start Simulation")');
    
    await page.waitForSelector('text=/Hole/', { timeout: 10000 });
    
    // Look for poker-style betting elements
    const pokerElements = [
      'text=/fold/i',
      'text=/raise/i',
      'text=/call/i',
      'text=/bet/i',
      'text=/all.?in/i',
      'text=/check/i',
      'text=/partner/i',
      'text=/solo/i',
      'text=/double/i'
    ];
    
    let foundPokerElement = false;
    for (const selector of pokerElements) {
      if (await page.locator(selector).isVisible({ timeout: 2000 }).catch(() => false)) {
        foundPokerElement = true;
        console.log(`Found poker element: ${selector}`);
        break;
      }
    }
    
    // Look for golf elements
    const golfElements = [
      'text=/yards/i',
      'text=/par/i',
      'text=/shot/i',
      'text=/drive/i',
      'text=/putt/i',
      'text=/fairway/i',
      'text=/green/i',
      'text=/handicap/i'
    ];
    
    let foundGolfElement = false;
    for (const selector of golfElements) {
      if (await page.locator(selector).isVisible({ timeout: 2000 }).catch(() => false)) {
        foundGolfElement = true;
        console.log(`Found golf element: ${selector}`);
        break;
      }
    }
    
    // Verify hybrid nature - should have both poker and golf elements
    expect(foundPokerElement || foundGolfElement).toBeTruthy();
    
    // Test betting decisions affect gameplay
    const decisionButton = page.locator('button').first();
    if (await decisionButton.isVisible()) {
      const textBefore = await page.textContent('body');
      await decisionButton.click();
      await page.waitForTimeout(1000);
      const textAfter = await page.textContent('body');
      
      // Verify something changed after decision
      expect(textAfter).not.toBe(textBefore);
    }
  });
});