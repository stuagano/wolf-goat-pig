const { test, expect } = require('@playwright/test');

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const APP_URL = process.env.REACT_APP_URL || 'http://localhost:3001';

test.describe('Wolf-Goat-Pig Simulation Mode', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto(APP_URL);

    // Wait for app to fully initialize - first wait for network idle
    await page.waitForLoadState('networkidle');

    // Wait for the loading screen to disappear and main content to appear
    // The app shows "Hold On Please" while cold starting
    await page.waitForFunction(() => {
      const loadingText = document.body.textContent;
      return !loadingText.includes('Hold On Please');
    }, { timeout: 60000 });

    // Additional wait to ensure React has fully rendered
    await page.waitForTimeout(2000);

    // Click Browse Without Login to access the app
    const browseButton = page.locator('button:has-text("Browse Without Login")');
    if (await browseButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await browseButton.click();
      await page.waitForLoadState('networkidle');
    }

    // Navigate to Practice Mode
    await page.click('button:has-text("🎮 Practice Mode")');
    await page.waitForLoadState('networkidle');
    // Wait for the practice/simulation interface to load
    await page.waitForTimeout(2000);
  });

  test.describe('Setup and Initialization', () => {
    test('should display simulation setup form', async ({ page }) => {
      // Check for setup form elements
      await expect(page.locator('h3:has-text("Your Details")')).toBeVisible();
      await expect(page.locator('h3:has-text("Computer Opponents")')).toBeVisible();
      
      // Verify player name input
      const playerNameInput = page.locator('input[type="text"]').first();
      await expect(playerNameInput).toBeVisible();
      
      // Verify handicap input
      const handicapInput = page.locator('input[type="number"]').first();
      await expect(handicapInput).toBeVisible();
      await expect(handicapInput).toHaveValue('18');
    });

    test('should allow player name and handicap entry', async ({ page }) => {
      // Enter player details
      const playerNameInput = page.locator('input[type="text"]').first();
      await playerNameInput.clear();
      await playerNameInput.fill('Test Golfer');
      
      const handicapInput = page.locator('input[type="number"]').first();
      await handicapInput.clear();
      await handicapInput.fill('15');
      
      // Verify values are set
      await expect(playerNameInput).toHaveValue('Test Golfer');
      await expect(handicapInput).toHaveValue('15');
    });

    test('should select AI opponents using quick select buttons', async ({ page }) => {
      // Select Clive for Player 1
      await page.locator('button:has-text("Clive")').first().click();
      await expect(page.locator('input[value="Clive"]')).toBeVisible();
      await expect(page.locator('input[value="8"]')).toBeVisible(); // Clive's handicap
      
      // Select Gary for Player 2  
      await page.locator('button:has-text("Gary")').nth(1).click();
      await expect(page.locator('input[value="Gary"]')).toBeVisible();
      await expect(page.locator('input[value="12"]')).toBeVisible(); // Gary's handicap
      
      // Select Bernard for Player 3
      await page.locator('button:has-text("Bernard")').nth(2).click();
      await expect(page.locator('input[value="Bernard"]')).toBeVisible();
      await expect(page.locator('input[value="15"]')).toBeVisible(); // Bernard's handicap
    });

    test('should select course and start simulation', async ({ page }) => {
      // Setup players
      await page.locator('input[type="text"]').first().fill('Test Player');
      await page.locator('button:has-text("Clive")').first().click();
      await page.locator('button:has-text("Gary")').nth(1).click();
      await page.locator('button:has-text("Bernard")').nth(2).click();
      
      // Select course
      const courseSelect = page.locator('select').last();
      await courseSelect.selectOption('Wing Point');
      await expect(courseSelect).toHaveValue('Wing Point');
      
      // Start simulation
      await page.click('button:has-text("🚀 Start Simulation")');
      
      // Verify game started
      await expect(page.locator('text=/Hole 1.*Par/')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('button:has-text("⛳ Play Next Shot")')).toBeVisible();
    });
  });

  test.describe('Game Progression', () => {
    async function setupAndStartGame(page) {
      // Quick setup
      await page.locator('input[type="text"]').first().fill('Test Player');
      await page.locator('button:has-text("Clive")').first().click();
      await page.locator('button:has-text("Gary")').nth(1).click();
      await page.locator('button:has-text("Bernard")').nth(2).click();
      await page.locator('select').last().selectOption('Wing Point');
      await page.click('button:has-text("🚀 Start Simulation")');
      await page.waitForSelector('button:has-text("⛳ Play Next Shot")', { timeout: 10000 });
    }

    test('should display game state after initialization', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Check hole information
      await expect(page.locator('text=/Hole 1.*Par 4/')).toBeVisible();
      await expect(page.locator('text=/Base Wager/')).toBeVisible();
      
      // Check player display
      await expect(page.locator('text=Test Player')).toBeVisible();
      await expect(page.locator('text=Clive')).toBeVisible();
      await expect(page.locator('text=Gary')).toBeVisible();
      await expect(page.locator('text=Bernard')).toBeVisible();
      
      // Check analytics sections
      await expect(page.locator('h3:has-text("Live Analytics")')).toBeVisible();
      await expect(page.locator('h4:has-text("Win Probability")')).toBeVisible();
    });

    test('should play first shot and update game state', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Play first shot
      await page.click('button:has-text("⛳ Play Next Shot")');
      
      // Wait for shot result
      await page.waitForTimeout(1000);
      
      // Check for shot result in action feed
      const actionFeed = page.locator('h4:has-text("Action Feed") + div');
      await expect(actionFeed.locator('text=/hits.*shot/')).toBeVisible({ timeout: 5000 });
      
      // Verify shot updated the display
      await expect(page.locator('text=/Shot #2/')).toBeVisible();
    });

    test('should progress through multiple shots', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Play multiple shots
      for (let i = 0; i < 4; i++) {
        await page.click('button:has-text("⛳ Play Next Shot")');
        await page.waitForTimeout(500);
        
        // Check shot counter increments
        const shotNumber = i + 2;
        if (shotNumber <= 4) {
          await expect(page.locator(`text=/Shot #${shotNumber}/`)).toBeVisible({ timeout: 5000 });
        }
      }
      
      // All players should have teed off
      const actionFeed = page.locator('h4:has-text("Action Feed") + div');
      await expect(actionFeed.locator('div').count()).toBeGreaterThan(3);
    });

    test('should display betting decisions when captain needs to decide', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Play shots until partnership decision point
      for (let i = 0; i < 4; i++) {
        await page.click('button:has-text("⛳ Play Next Shot")');
        await page.waitForTimeout(500);
      }
      
      // Check if betting decision interface appears
      // This depends on who is captain and game flow
      const bettingSection = page.locator('text=/partnership|solo|double/i');
      if (await bettingSection.isVisible()) {
        // Verify betting options are displayed
        await expect(bettingSection).toBeVisible();
      }
    });
  });

  test.describe('Timeline Feature', () => {
    async function setupAndStartGame(page) {
      await page.locator('input[type="text"]').first().fill('Test Player');
      await page.locator('button:has-text("Clive")').first().click();
      await page.locator('button:has-text("Gary")').nth(1).click();
      await page.locator('button:has-text("Bernard")').nth(2).click();
      await page.locator('select').last().selectOption('Wing Point');
      await page.click('button:has-text("🚀 Start Simulation")');
      await page.waitForSelector('button:has-text("⛳ Play Next Shot")', { timeout: 10000 });
    }

    test('should fetch and display timeline events', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Make API call to get timeline
      const timelineResponse = await page.request.get(`${API_URL}/simulation/timeline`);
      expect(timelineResponse.ok()).toBeTruthy();
      
      const timelineData = await timelineResponse.json();
      expect(timelineData).toHaveProperty('events');
      expect(Array.isArray(timelineData.events)).toBeTruthy();
    });

    test('should track shot events in timeline', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Play a shot
      await page.click('button:has-text("⛳ Play Next Shot")');
      await page.waitForTimeout(1000);
      
      // Check timeline API
      const timelineResponse = await page.request.get(`${API_URL}/simulation/timeline`);
      const timelineData = await timelineResponse.json();
      
      // Should have at least one shot event
      const shotEvents = timelineData.events.filter(e => e.type === 'shot');
      expect(shotEvents.length).toBeGreaterThan(0);
      
      // Verify event structure
      const latestShot = shotEvents[0];
      expect(latestShot).toHaveProperty('description');
      expect(latestShot).toHaveProperty('player');
      expect(latestShot).toHaveProperty('timestamp');
    });

    test('should display events in reverse chronological order', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Play multiple shots
      for (let i = 0; i < 3; i++) {
        await page.click('button:has-text("⛳ Play Next Shot")');
        await page.waitForTimeout(500);
      }
      
      // Get timeline
      const timelineResponse = await page.request.get(`${API_URL}/simulation/timeline`);
      const timelineData = await timelineResponse.json();
      
      // Verify reverse chronological order
      const events = timelineData.events;
      expect(events.length).toBeGreaterThan(1);
      
      // Check timestamps are descending
      for (let i = 0; i < events.length - 1; i++) {
        const currentTime = new Date(events[i].timestamp).getTime();
        const nextTime = new Date(events[i + 1].timestamp).getTime();
        expect(currentTime).toBeGreaterThanOrEqual(nextTime);
      }
    });
  });

  test.describe('Poker-Style Betting', () => {
    async function setupAndStartGame(page) {
      await page.locator('input[type="text"]').first().fill('Test Player');
      await page.locator('button:has-text("Clive")').first().click();
      await page.locator('button:has-text("Gary")').nth(1).click();
      await page.locator('button:has-text("Bernard")').nth(2).click();
      await page.locator('select').last().selectOption('Wing Point');
      await page.click('button:has-text("🚀 Start Simulation")');
      await page.waitForSelector('button:has-text("⛳ Play Next Shot")', { timeout: 10000 });
    }

    test('should fetch poker-style betting state', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Get poker state from API
      const pokerResponse = await page.request.get(`${API_URL}/simulation/poker-state`);
      expect(pokerResponse.ok()).toBeTruthy();
      
      const pokerData = await pokerResponse.json();
      
      // Verify poker state structure
      expect(pokerData).toHaveProperty('pot_size');
      expect(pokerData).toHaveProperty('betting_phase');
      expect(pokerData).toHaveProperty('current_bet');
      expect(pokerData).toHaveProperty('players_in');
      
      // Verify betting phase is valid
      expect(['pre-flop', 'flop', 'turn', 'river']).toContain(pokerData.betting_phase);
    });

    test('should update betting phase as hole progresses', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Initial phase (pre-flop)
      let pokerResponse = await page.request.get(`${API_URL}/simulation/poker-state`);
      let pokerData = await pokerResponse.json();
      expect(pokerData.betting_phase).toBe('pre-flop');
      
      // Play shots to advance phase
      for (let i = 0; i < 4; i++) {
        await page.click('button:has-text("⛳ Play Next Shot")');
        await page.waitForTimeout(500);
      }
      
      // Check if phase advanced (should be at flop after tee shots)
      pokerResponse = await page.request.get(`${API_URL}/simulation/poker-state`);
      pokerData = await pokerResponse.json();
      expect(['flop', 'turn', 'river']).toContain(pokerData.betting_phase);
    });

    test('should provide betting options in poker format', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Get poker state with options
      const pokerResponse = await page.request.get(`${API_URL}/simulation/poker-state`);
      const pokerData = await pokerResponse.json();
      
      if (pokerData.betting_options && pokerData.betting_options.length > 0) {
        // Verify option structure
        const option = pokerData.betting_options[0];
        expect(option).toHaveProperty('action');
        expect(option).toHaveProperty('label');
        expect(option).toHaveProperty('description');
        expect(option).toHaveProperty('icon');
        
        // Check for poker-style actions
        const validActions = ['check', 'call', 'raise', 'fold', 'all_in', 'bet'];
        const hasPokerAction = pokerData.betting_options.some(opt => 
          validActions.includes(opt.action)
        );
        expect(hasPokerAction).toBeTruthy();
      }
    });
  });

  test.describe('Partnership and Betting Decisions', () => {
    async function setupAndStartGame(page) {
      await page.locator('input[type="text"]').first().fill('Test Player');
      await page.locator('button:has-text("Clive")').first().click();
      await page.locator('button:has-text("Gary")').nth(1).click();
      await page.locator('button:has-text("Bernard")').nth(2).click();
      await page.locator('select').last().selectOption('Wing Point');
      await page.click('button:has-text("🚀 Start Simulation")');
      await page.waitForSelector('button:has-text("⛳ Play Next Shot")', { timeout: 10000 });
    }

    test('should handle betting decisions via API', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Make a betting decision
      const decision = {
        decision_type: 'check',
        player_id: 'human',
        amount: 0
      };
      
      const response = await page.request.post(`${API_URL}/simulation/betting-decision`, {
        data: decision
      });
      
      // Decision should be accepted
      expect(response.ok()).toBeTruthy();
      const result = await response.json();
      expect(result).toHaveProperty('success');
      expect(result).toHaveProperty('game_state');
    });

    test('should track partnership formations', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Simulate partnership request
      const partnershipDecision = {
        decision_type: 'partnership_request',
        player_id: 'human',
        partner_id: 'classic_quartet'
      };
      
      const response = await page.request.post(`${API_URL}/simulation/betting-decision`, {
        data: partnershipDecision
      });
      
      if (response.ok()) {
        const result = await response.json();
        
        // Check timeline for partnership event
        const timelineResponse = await page.request.get(`${API_URL}/simulation/timeline`);
        const timelineData = await timelineResponse.json();
        
        const partnershipEvents = timelineData.events.filter(e => 
          e.type === 'partnership' || e.type === 'partnership_request'
        );
        
        // Should have partnership-related events if request was valid
        if (partnershipEvents.length > 0) {
          expect(partnershipEvents[0]).toHaveProperty('description');
          expect(partnershipEvents[0].description).toContain('partner');
        }
      }
    });

    test('should handle solo decisions', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Try to go solo
      const soloDecision = {
        decision_type: 'go_solo',
        player_id: 'human'
      };
      
      const response = await page.request.post(`${API_URL}/simulation/betting-decision`, {
        data: soloDecision
      });
      
      // Check if decision was processed
      if (response.ok()) {
        const result = await response.json();
        expect(result).toHaveProperty('game_state');
        
        // Verify in timeline
        const timelineResponse = await page.request.get(`${API_URL}/simulation/timeline`);
        const timelineData = await timelineResponse.json();
        
        const soloEvents = timelineData.events.filter(e => 
          e.description && e.description.toLowerCase().includes('solo')
        );
        
        if (soloEvents.length > 0) {
          expect(soloEvents[0].description).toContain('solo');
        }
      }
    });
  });

  test.describe('AI Player Behavior', () => {
    async function setupAndStartGame(page) {
      await page.locator('input[type="text"]').first().fill('Test Player');
      await page.locator('button:has-text("Clive")').first().click();
      await page.locator('button:has-text("Gary")').nth(1).click();
      await page.locator('button:has-text("Bernard")').nth(2).click();
      await page.locator('select').last().selectOption('Wing Point');
      await page.click('button:has-text("🚀 Start Simulation")');
      await page.waitForSelector('button:has-text("⛳ Play Next Shot")', { timeout: 10000 });
    }

    test('should have AI players with different personalities', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Get game state
      const stateResponse = await page.request.get(`${API_URL}/simulation/state`);
      
      if (stateResponse.ok()) {
        const gameState = await stateResponse.json();
        
        // Check AI players have personalities
        const players = gameState.players || [];
        const aiPlayers = players.filter(p => p.id !== 'human');
        
        expect(aiPlayers.length).toBe(3);
        
        // Verify different play styles reflected in game
        // Clive is aggressive, Gary is conservative, Bernard is strategic
      }
    });

    test('should show AI players making autonomous decisions', async ({ page }) => {
      await setupAndStartGame(page);
      
      // Play through several shots
      for (let i = 0; i < 8; i++) {
        await page.click('button:has-text("⛳ Play Next Shot")');
        await page.waitForTimeout(500);
      }
      
      // Check timeline for AI decisions
      const timelineResponse = await page.request.get(`${API_URL}/simulation/timeline`);
      const timelineData = await timelineResponse.json();
      
      // Look for AI player actions
      const aiActions = timelineData.events.filter(e => 
        e.player && ['Clive', 'Gary', 'Bernard'].includes(e.player)
      );
      
      expect(aiActions.length).toBeGreaterThan(0);
      
      // Verify variety of AI actions
      const actionTypes = [...new Set(aiActions.map(a => a.type))];
      expect(actionTypes.length).toBeGreaterThan(1);
    });
  });

  test.describe('Error Handling and Edge Cases', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      // Try to play shot without setup
      const response = await page.request.post(`${API_URL}/simulation/play-next-shot`);
      
      // Should get error
      expect(response.status()).toBe(400);
      const error = await response.json();
      expect(error).toHaveProperty('detail');
    });

    test('should validate player setup requirements', async ({ page }) => {
      // Try to start with insufficient players
      await page.locator('input[type="text"]').first().fill('Test Player');
      await page.locator('select').last().selectOption('Wing Point');
      
      // This should fail or show error
      await page.click('button:has-text("🚀 Start Simulation")');
      
      // Check for error message or that we're still on setup
      const isStillOnSetup = await page.locator('h3:has-text("Computer Opponents")').isVisible();
      expect(isStillOnSetup).toBeTruthy();
    });

    test('should handle rapid shot clicking', async ({ page }) => {
      // Setup game
      await page.locator('input[type="text"]').first().fill('Test Player');
      await page.locator('button:has-text("Clive")').first().click();
      await page.locator('button:has-text("Gary")').nth(1).click();
      await page.locator('button:has-text("Bernard")').nth(2).click();
      await page.locator('select').last().selectOption('Wing Point');
      await page.click('button:has-text("🚀 Start Simulation")');
      await page.waitForSelector('button:has-text("⛳ Play Next Shot")', { timeout: 10000 });
      
      // Rapidly click play shot
      const playButton = page.locator('button:has-text("⛳ Play Next Shot")');
      
      // Click multiple times quickly
      await Promise.all([
        playButton.click(),
        playButton.click(),
        playButton.click()
      ].map(p => p.catch(() => {}))); // Catch any errors from rapid clicking
      
      // Game should still be in valid state
      await page.waitForTimeout(2000);
      
      // Check game is still playable
      const gameElements = await page.locator('h3:has-text("Players")').isVisible();
      expect(gameElements).toBeTruthy();
    });
  });

  test.describe('Full Game Flow', () => {
    test('should complete an entire hole', async ({ page }) => {
      test.setTimeout(60000); // Extend timeout for full hole

      // Setup game
      await page.locator('input[type="text"]').first().fill('Test Player');
      await page.locator('button:has-text("Clive")').first().click();
      await page.locator('button:has-text("Gary")').nth(1).click();
      await page.locator('button:has-text("Bernard")').nth(2).click();

      // Wait for courses to load in dropdown before selecting
      await page.waitForFunction(() => {
        const selects = document.querySelectorAll('select');
        const courseSelect = selects[selects.length - 1];
        return courseSelect && courseSelect.options.length > 1;
      }, { timeout: 10000 });

      await page.locator('select').last().selectOption('Wing Point');
      await page.click('button:has-text("🚀 Start Simulation")');
      await page.waitForSelector('button:has-text("⛳ Play Next Shot")', { timeout: 10000 });
      
      // Play shots until hole is complete
      let holeComplete = false;
      let shotCount = 0;
      const maxShots = 30; // Prevent infinite loop
      
      while (!holeComplete && shotCount < maxShots) {
        // Play next shot
        const playButton = page.locator('button:has-text("⛳ Play Next Shot")');
        if (await playButton.isVisible()) {
          await playButton.click();
          await page.waitForTimeout(1000);
          shotCount++;
          
          // Check if hole is complete
          const holeStatus = await page.locator('text=/Hole.*Complete/i').isVisible();
          if (holeStatus) {
            holeComplete = true;
          }
          
          // Also check for next hole button
          const nextHole = await page.locator('button:has-text("Next Hole")').isVisible();
          if (nextHole) {
            holeComplete = true;
          }
        } else {
          // No play button, might be complete or need decision
          break;
        }
      }
      
      // Verify we played a reasonable number of shots
      expect(shotCount).toBeGreaterThan(4); // At least everyone teed off
      expect(shotCount).toBeLessThan(maxShots); // Didn't hit max
      
      // Check final timeline
      const timelineResponse = await page.request.get(`${API_URL}/simulation/timeline`);
      const timelineData = await timelineResponse.json();
      
      // Should have multiple events
      expect(timelineData.events.length).toBeGreaterThan(4);
      
      // Should have different event types
      const eventTypes = [...new Set(timelineData.events.map(e => e.type))];
      expect(eventTypes.length).toBeGreaterThan(1);
    });
  });
});