import { test, expect } from '@playwright/test';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

test.describe('Simulation API Tests', () => {
  
  test('should handle API errors gracefully', async ({ page }) => {
    // Try to play shot without setup
    const response = await page.request.post(`${API_URL}/simulation/play-next-shot`);
    
    // Should get error
    expect(response.status()).toBe(400);
    const error = await response.json();
    expect(error).toHaveProperty('detail');
    expect(error.detail).toContain('Simulation not initialized');
  });

  test('should setup simulation via API', async ({ page }) => {
    const setupData = {
      human_player: {
        id: "human",
        name: "Test Player",
        handicap: 15
      },
      computer_players: [
        { id: "ai1", name: "AI Player 1", handicap: 10 },
        { id: "ai2", name: "AI Player 2", handicap: 12 },
        { id: "ai3", name: "AI Player 3", handicap: 8 }
      ],
      course_name: "Wing Point"
    };

    const response = await page.request.post(`${API_URL}/simulation/setup`, {
      data: setupData
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    
    expect(result).toHaveProperty('status', 'ok');
    expect(result).toHaveProperty('game_state');
    expect(result).toHaveProperty('players');
    expect(result.players.length).toBe(4);
  });

  test('should fetch timeline after setup', async ({ page }) => {
    // Setup simulation first
    const setupData = {
      human_player: {
        id: "human",
        name: "Test Player", 
        handicap: 15
      },
      computer_players: [
        { id: "ai1", name: "AI Player 1", handicap: 10 },
        { id: "ai2", name: "AI Player 2", handicap: 12 },
        { id: "ai3", name: "AI Player 3", handicap: 8 }
      ],
      course_name: "Wing Point"
    };

    await page.request.post(`${API_URL}/simulation/setup`, {
      data: setupData
    });

    // Get timeline
    const timelineResponse = await page.request.get(`${API_URL}/simulation/timeline`);
    expect(timelineResponse.ok()).toBeTruthy();
    
    const timelineData = await timelineResponse.json();
    expect(timelineData).toHaveProperty('success', true);
    expect(timelineData).toHaveProperty('events');
    expect(Array.isArray(timelineData.events)).toBeTruthy();
  });

  test('should fetch poker-style betting state after setup', async ({ page }) => {
    // Setup simulation first
    const setupData = {
      human_player: {
        id: "human",
        name: "Test Player",
        handicap: 15
      },
      computer_players: [
        { id: "ai1", name: "AI Player 1", handicap: 10 },
        { id: "ai2", name: "AI Player 2", handicap: 12 },
        { id: "ai3", name: "AI Player 3", handicap: 8 }
      ],
      course_name: "Wing Point"
    };

    await page.request.post(`${API_URL}/simulation/setup`, {
      data: setupData
    });

    // Get poker state
    const pokerResponse = await page.request.get(`${API_URL}/simulation/poker-state`);
    expect(pokerResponse.ok()).toBeTruthy();
    
    const pokerData = await pokerResponse.json();
    
    // Verify poker state structure
    expect(pokerData).toHaveProperty('success', true);
    expect(pokerData).toHaveProperty('pot_size');
    expect(pokerData).toHaveProperty('betting_phase');
    expect(pokerData).toHaveProperty('current_bet');
    expect(pokerData).toHaveProperty('players_in');
    
    // Verify betting phase is valid
    expect(['pre-flop', 'flop', 'turn', 'river']).toContain(pokerData.betting_phase);
  });

  test('should play shots and track in timeline', async ({ page }) => {
    // Setup simulation
    const setupData = {
      human_player: {
        id: "human",
        name: "Test Player",
        handicap: 15
      },
      computer_players: [
        { id: "ai1", name: "AI Player 1", handicap: 10 },
        { id: "ai2", name: "AI Player 2", handicap: 12 },
        { id: "ai3", name: "AI Player 3", handicap: 8 }
      ],
      course_name: "Wing Point"
    };

    await page.request.post(`${API_URL}/simulation/setup`, {
      data: setupData
    });

    // Play a shot
    const shotResponse = await page.request.post(`${API_URL}/simulation/play-next-shot`);
    expect(shotResponse.ok()).toBeTruthy();

    const shotResult = await shotResponse.json();
    expect(shotResult).toHaveProperty('success', true);

    // Check timeline has shot events
    const timelineResponse = await page.request.get(`${API_URL}/simulation/timeline`);
    const timelineData = await timelineResponse.json();
    
    // Timeline should now have events
    expect(timelineData.events.length).toBeGreaterThan(0);
    
    // Should have shot-related events
    const shotEvents = timelineData.events.filter(e => 
      e.type === 'shot' || e.description.includes('shot') || e.description.includes('hits')
    );
    expect(shotEvents.length).toBeGreaterThan(0);

    // Verify event structure
    const event = timelineData.events[0];
    expect(event).toHaveProperty('description');
    expect(event).toHaveProperty('timestamp');
  });

  test('should handle betting decisions', async ({ page }) => {
    // Setup simulation
    const setupData = {
      human_player: {
        id: "human",
        name: "Test Player",
        handicap: 15
      },
      computer_players: [
        { id: "ai1", name: "AI Player 1", handicap: 10 },
        { id: "ai2", name: "AI Player 2", handicap: 12 },
        { id: "ai3", name: "AI Player 3", handicap: 8 }
      ],
      course_name: "Wing Point"
    };

    await page.request.post(`${API_URL}/simulation/setup`, {
      data: setupData
    });

    // Try a betting decision
    const decision = {
      decision_type: 'check',
      player_id: 'human',
      amount: 0
    };
    
    const response = await page.request.post(`${API_URL}/simulation/betting-decision`, {
      data: decision
    });
    
    // Decision should be processed (may succeed or fail based on game state)
    if (response.ok()) {
      const result = await response.json();
      expect(result).toHaveProperty('success');
    } else {
      // If it fails, should have error details
      const error = await response.json();
      expect(error).toHaveProperty('detail');
    }
  });

  test('should update poker betting phase as game progresses', async ({ page }) => {
    // Setup simulation
    const setupData = {
      human_player: {
        id: "human", 
        name: "Test Player",
        handicap: 15
      },
      computer_players: [
        { id: "ai1", name: "AI Player 1", handicap: 10 },
        { id: "ai2", name: "AI Player 2", handicap: 12 },
        { id: "ai3", name: "AI Player 3", handicap: 8 }
      ],
      course_name: "Wing Point"
    };

    await page.request.post(`${API_URL}/simulation/setup`, {
      data: setupData
    });

    // Initial phase
    let pokerResponse = await page.request.get(`${API_URL}/simulation/poker-state`);
    let pokerData = await pokerResponse.json();
    const initialPhase = pokerData.betting_phase;
    expect(['pre-flop', 'flop', 'turn', 'river']).toContain(initialPhase);

    // Play multiple shots
    for (let i = 0; i < 4; i++) {
      const shotResponse = await page.request.post(`${API_URL}/simulation/play-next-shot`);
      if (!shotResponse.ok()) break; // Stop if no more shots available
    }

    // Check if phase changed
    pokerResponse = await page.request.get(`${API_URL}/simulation/poker-state`);
    pokerData = await pokerResponse.json();
    
    // Should still have valid phase
    expect(['pre-flop', 'flop', 'turn', 'river']).toContain(pokerData.betting_phase);
    
    // Pot size should be reasonable
    expect(pokerData.pot_size).toBeGreaterThanOrEqual(0);
  });

  test('should track multiple shot events with timestamps', async ({ page }) => {
    // Setup simulation
    const setupData = {
      human_player: {
        id: "human",
        name: "Test Player", 
        handicap: 15
      },
      computer_players: [
        { id: "ai1", name: "AI Player 1", handicap: 10 },
        { id: "ai2", name: "AI Player 2", handicap: 12 },
        { id: "ai3", name: "AI Player 3", handicap: 8 }
      ],
      course_name: "Wing Point"
    };

    await page.request.post(`${API_URL}/simulation/setup`, {
      data: setupData
    });

    // Play multiple shots
    for (let i = 0; i < 3; i++) {
      const shotResponse = await page.request.post(`${API_URL}/simulation/play-next-shot`);
      if (!shotResponse.ok()) break;
      
      // Small delay between shots
      await page.waitForTimeout(100);
    }

    // Check timeline
    const timelineResponse = await page.request.get(`${API_URL}/simulation/timeline`);
    const timelineData = await timelineResponse.json();
    
    // Should have multiple events
    expect(timelineData.events.length).toBeGreaterThan(1);
    
    // Events should be in reverse chronological order
    const events = timelineData.events;
    for (let i = 0; i < events.length - 1; i++) {
      const currentTime = new Date(events[i].timestamp);
      const nextTime = new Date(events[i + 1].timestamp);
      expect(currentTime >= nextTime).toBeTruthy();
    }
    
    // Should have variety of events
    const eventTypes = [...new Set(events.map(e => e.type))];
    // Could have setup, shot, or other types
    expect(eventTypes.length).toBeGreaterThan(0);
  });
});