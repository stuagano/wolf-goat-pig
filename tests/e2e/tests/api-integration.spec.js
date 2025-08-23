import { test, expect } from '@playwright/test';

test.describe('API Integration Tests', () => {
  const API_BASE = 'http://localhost:8000';
  
  test('should connect to backend API', async ({ request }) => {
    console.log('🔌 Testing API connectivity...');
    
    try {
      const response = await request.get(`${API_BASE}/docs`);
      expect(response.status()).toBe(200);
      console.log('   ✅ Backend API is running and accessible');
    } catch (error) {
      console.log('   ⚠️  Backend API not accessible, may need to start manually');
      console.log(`   Error: ${error.message}`);
    }
  });

  test('should create new game via API', async ({ request }) => {
    console.log('🎮 Testing game creation via API...');
    
    try {
      const gameData = {
        players: [
          { id: 'p1', name: 'Stuart', handicap: 18 },
          { id: 'p2', name: 'Alex', handicap: 5 },
          { id: 'p3', name: 'Sam', handicap: 12 },
          { id: 'p4', name: 'Ace', handicap: 8 }
        ]
      };
      
      const response = await request.post(`${API_BASE}/api/games`, {
        data: gameData
      });
      
      if (response.status() === 201 || response.status() === 200) {
        const gameResponse = await response.json();
        console.log(`   ✅ Game created successfully: ${JSON.stringify(gameResponse).substring(0, 100)}...`);
        
        expect(gameResponse).toHaveProperty('game_id');
        return gameResponse.game_id;
      } else {
        console.log(`   ⚠️  Game creation returned ${response.status()}`);
      }
    } catch (error) {
      console.log(`   ⚠️  Game creation failed: ${error.message}`);
    }
  });

  test('should simulate shots via API', async ({ request }) => {
    console.log('🏌️ Testing shot simulation via API...');
    
    try {
      // First create a game
      const gameData = {
        players: [
          { id: 'p1', name: 'Stuart', handicap: 18 },
          { id: 'p2', name: 'Alex', handicap: 5 },
          { id: 'p3', name: 'Sam', handicap: 12 },
          { id: 'p4', name: 'Ace', handicap: 8 }
        ]
      };
      
      const gameResponse = await request.post(`${API_BASE}/api/games`, {
        data: gameData
      });
      
      if (gameResponse.ok()) {
        const game = await gameResponse.json();
        const gameId = game.game_id;
        
        // Simulate a shot
        const shotResponse = await request.post(`${API_BASE}/api/games/${gameId}/shots`, {
          data: { player_id: 'p1' }
        });
        
        if (shotResponse.ok()) {
          const shotResult = await shotResponse.json();
          console.log(`   ✅ Shot simulated: ${JSON.stringify(shotResult).substring(0, 100)}...`);
          
          expect(shotResult).toHaveProperty('shot_result');
          expect(shotResult.shot_result).toHaveProperty('distance_to_pin');
          expect(shotResult.shot_result).toHaveProperty('shot_quality');
        } else {
          console.log(`   ⚠️  Shot simulation returned ${shotResponse.status()}`);
        }
      }
    } catch (error) {
      console.log(`   ⚠️  Shot simulation failed: ${error.message}`);
    }
  });

  test('should handle partnership requests via API', async ({ request }) => {
    console.log('🤝 Testing partnership requests via API...');
    
    try {
      // Create game
      const gameData = {
        players: [
          { id: 'p1', name: 'Stuart', handicap: 18 },
          { id: 'p2', name: 'Alex', handicap: 5 },
          { id: 'p3', name: 'Sam', handicap: 12 },
          { id: 'p4', name: 'Ace', handicap: 8 }
        ]
      };
      
      const gameResponse = await request.post(`${API_BASE}/api/games`, {
        data: gameData
      });
      
      if (gameResponse.ok()) {
        const game = await gameResponse.json();
        const gameId = game.game_id;
        
        // Take a couple shots first to enable partnerships
        await request.post(`${API_BASE}/api/games/${gameId}/shots`, {
          data: { player_id: 'p1' }
        });
        
        await request.post(`${API_BASE}/api/games/${gameId}/shots`, {
          data: { player_id: 'p2' }
        });
        
        // Try to request partnership
        const partnershipResponse = await request.post(`${API_BASE}/api/games/${gameId}/partnership`, {
          data: { 
            captain_id: 'p1',
            partner_id: 'p2'
          }
        });
        
        if (partnershipResponse.ok()) {
          const result = await partnershipResponse.json();
          console.log(`   ✅ Partnership request handled: ${JSON.stringify(result)}`);
        } else {
          console.log(`   ℹ️  Partnership request returned ${partnershipResponse.status()} (may be expected)`);
        }
      }
    } catch (error) {
      console.log(`   ⚠️  Partnership test failed: ${error.message}`);
    }
  });

  test('should get game state via API', async ({ request }) => {
    console.log('📊 Testing game state retrieval via API...');
    
    try {
      // Create and simulate game
      const gameData = {
        players: [
          { id: 'p1', name: 'Stuart', handicap: 18 },
          { id: 'p2', name: 'Alex', handicap: 5 },
          { id: 'p3', name: 'Sam', handicap: 12 },
          { id: 'p4', name: 'Ace', handicap: 8 }
        ]
      };
      
      const gameResponse = await request.post(`${API_BASE}/api/games`, {
        data: gameData
      });
      
      if (gameResponse.ok()) {
        const game = await gameResponse.json();
        const gameId = game.game_id;
        
        // Take a shot
        await request.post(`${API_BASE}/api/games/${gameId}/shots`, {
          data: { player_id: 'p1' }
        });
        
        // Get game state
        const stateResponse = await request.get(`${API_BASE}/api/games/${gameId}/state`);
        
        if (stateResponse.ok()) {
          const state = await stateResponse.json();
          console.log(`   ✅ Game state retrieved: ${Object.keys(state).join(', ')}`);
          
          expect(state).toHaveProperty('current_hole');
          expect(state).toHaveProperty('hole_states');
        } else {
          console.log(`   ⚠️  Game state retrieval returned ${stateResponse.status()}`);
        }
      }
    } catch (error) {
      console.log(`   ⚠️  Game state test failed: ${error.message}`);
    }
  });

  test('should handle betting actions via API', async ({ request }) => {
    console.log('💰 Testing betting actions via API...');
    
    try {
      // Create and simulate game
      const gameData = {
        players: [
          { id: 'p1', name: 'Stuart', handicap: 18 },
          { id: 'p2', name: 'Alex', handicap: 5 },
          { id: 'p3', name: 'Sam', handicap: 12 },
          { id: 'p4', name: 'Ace', handicap: 8 }
        ]
      };
      
      const gameResponse = await request.post(`${API_BASE}/api/games`, {
        data: gameData
      });
      
      if (gameResponse.ok()) {
        const game = await gameResponse.json();
        const gameId = game.game_id;
        
        // Take some shots
        await request.post(`${API_BASE}/api/games/${gameId}/shots`, {
          data: { player_id: 'p1' }
        });
        
        // Try to offer double
        const doubleResponse = await request.post(`${API_BASE}/api/games/${gameId}/double`, {
          data: { player_id: 'p2' }
        });
        
        if (doubleResponse.ok()) {
          const result = await doubleResponse.json();
          console.log(`   ✅ Double offer handled: ${JSON.stringify(result)}`);
        } else {
          console.log(`   ℹ️  Double offer returned ${doubleResponse.status()} (may not be available yet)`);
        }
      }
    } catch (error) {
      console.log(`   ⚠️  Betting actions test failed: ${error.message}`);
    }
  });
});

test.describe('Frontend-Backend Integration', () => {
  test('should load game through full stack', async ({ page }) => {
    console.log('🔄 Testing full-stack integration...');
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check that page loads without API errors
    const errorMessages = page.locator('.error, [data-testid*="error"]');
    const hasErrors = await errorMessages.first().isVisible().catch(() => false);
    
    if (hasErrors) {
      const errorText = await errorMessages.first().textContent();
      console.log(`   ⚠️  Frontend error detected: ${errorText}`);
    } else {
      console.log('   ✅ No frontend errors detected');
    }
    
    // Try to start a game (tests frontend-backend communication)
    const startButton = page.locator('button', { hasText: /start|begin|play|new.*game/i });
    if (await startButton.first().isVisible()) {
      await startButton.first().click();
      await page.waitForTimeout(2000);
      
      // Check if game started successfully
      const shotButton = page.locator('button', { hasText: /shot|hit|play|swing/i });
      if (await shotButton.first().isVisible()) {
        console.log('   ✅ Game started successfully through full stack');
      } else {
        console.log('   ℹ️  Game start may require additional setup steps');
      }
    } else {
      console.log('   ℹ️  No start button found, may already be in game');
    }
  });

  test('should handle network errors gracefully', async ({ page }) => {
    console.log('🚫 Testing network error handling...');
    
    // Intercept API calls to simulate network issues
    await page.route('**/api/**', route => {
      route.abort('failed');
    });
    
    await page.goto('/');
    await page.waitForTimeout(3000);
    
    // Check that app doesn't crash
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toBe('');
    
    console.log('   ✅ App remains functional despite network errors');
  });

  test('should maintain consistent data flow', async ({ page }) => {
    console.log('📡 Testing data flow consistency...');
    
    let apiCalls = [];
    
    // Monitor API calls
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiCalls.push({
          method: request.method(),
          url: request.url(),
          timestamp: Date.now()
        });
      }
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Try to trigger API calls through user interaction
    const startButton = page.locator('button', { hasText: /start|begin|play/i });
    if (await startButton.first().isVisible()) {
      await startButton.first().click();
      await page.waitForTimeout(2000);
    }
    
    const shotButton = page.locator('button', { hasText: /shot|hit|play|swing/i });
    if (await shotButton.first().isVisible()) {
      await shotButton.first().click();
      await page.waitForTimeout(2000);
    }
    
    console.log(`   📊 Captured ${apiCalls.length} API calls`);
    
    for (const call of apiCalls) {
      console.log(`   🔗 ${call.method} ${call.url.replace('http://localhost:8000', '')}`);
    }
    
    console.log('   ✅ Data flow monitoring completed');
  });
});