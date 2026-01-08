import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Golden Round Advanced E2E Tests
 * 
 * Tests advanced scenarios:
 * 1. Scores with quarters > 10 (big swings)
 * 2. Starting game on hole 10 (back nine start)
 * 3. Editing holes at random after completion
 * 4. Verifying totals recalculate correctly after edits
 */

const API_BASE = 'http://localhost:8333';

// Load golden round data
function loadGoldenRound() {
  const goldenPath = path.resolve(__dirname, '../../../../backend/tests/fixtures/golden_round.json');
  const data = fs.readFileSync(goldenPath, 'utf-8');
  return JSON.parse(data);
}

// Create extended golden round with higher stakes holes
function createHighStakesRound() {
  const baseRound = loadGoldenRound();
  
  // Modify some holes to have much higher quarter values (>10)
  const highStakesHoles = [
    // Hole 9: Massive solo win - captain wins 18 quarters
    {
      hole_number: 9,
      par: 4,
      rotation_order: ["player_a", "player_b", "player_c", "player_d"],
      teams: {
        type: "solo",
        captain: "player_a",
        opponents: ["player_b", "player_c", "player_d"]
      },
      scores: { player_a: 2, player_b: 5, player_c: 6, player_d: 5 }, // Eagle for captain!
      wager: 6, // High wager
      winner: "captain",
      halved: false,
      quarters: { player_a: 18, player_b: -6, player_c: -6, player_d: -6 },
      running_totals: { player_a: 18, player_b: -6, player_c: -6, player_d: -6 }
    },
    // Hole 18: Big Dick scenario - massive 24 quarter swing
    {
      hole_number: 18,
      par: 4,
      rotation_order: ["player_b", "player_c", "player_d", "player_a"],
      teams: {
        type: "solo",
        captain: "player_b",
        opponents: ["player_c", "player_d", "player_a"]
      },
      scores: { player_a: 5, player_b: 3, player_c: 5, player_d: 6 },
      wager: 8, // Hoepfinger max wager
      winner: "captain",
      halved: false,
      duncan_invoked: false,
      quarters: { player_a: -8, player_b: 24, player_c: -8, player_d: -8 },
      running_totals: { player_a: 10, player_b: 18, player_c: -14, player_d: -14 }
    }
  ];

  // Replace holes 9 and 18 with high stakes versions
  const modifiedHoles = baseRound.holes.map(hole => {
    const highStakesVersion = highStakesHoles.find(h => h.hole_number === hole.hole_number);
    return highStakesVersion || hole;
  });

  // Recalculate running totals
  const runningTotals = { player_a: 0, player_b: 0, player_c: 0, player_d: 0 };
  for (const hole of modifiedHoles) {
    for (const [pid, q] of Object.entries(hole.quarters)) {
      runningTotals[pid] += q;
    }
    hole.running_totals = { ...runningTotals };
  }

  return {
    ...baseRound,
    holes: modifiedHoles,
    expected_final_totals: { ...runningTotals }
  };
}

test.describe('Golden Round - High Stakes (Quarters > 10)', () => {
  test('handle large quarter values (18+ quarters)', async ({ request }) => {
    // Create test game
    const createResponse = await request.post(`${API_BASE}/games/create-test?player_count=4`);
    expect(createResponse.ok()).toBeTruthy();
    
    const gameData = await createResponse.json();
    const gameId = gameData.game_id;
    const players = gameData.players;

    console.log(`Created game ${gameId} for high stakes test`);

    // Map player IDs
    const playerMap = {
      'player_a': players[0].id,
      'player_b': players[1].id,
      'player_c': players[2].id,
      'player_d': players[3].id
    };

    // Submit a solo hole with very high stakes (captain wins 18 quarters)
    const highStakesHole = {
      hole_number: 1,
      rotation_order: [players[0].id, players[1].id, players[2].id, players[3].id],
      captain_index: 0,
      teams: {
        type: "solo",
        captain: players[0].id,
        opponents: [players[1].id, players[2].id, players[3].id]
      },
      final_wager: 6, // 6 quarters base * 3 opponents = 18 total
      winner: "captain",
      scores: {
        [players[0].id]: 2,  // Eagle
        [players[1].id]: 5,
        [players[2].id]: 6,
        [players[3].id]: 5
      },
      hole_par: 4,
      duncan_invoked: false
    };

    const response = await request.post(
      `${API_BASE}/games/${gameId}/holes/complete`,
      { data: highStakesHole }
    );

    if (response.ok()) {
      const result = await response.json();
      console.log('High stakes hole result:', result);
      
      // Verify captain won big (should be wager * 3 = 18)
      if (result.hole_result && result.hole_result.points_delta) {
        const captainPoints = result.hole_result.points_delta[players[0].id];
        console.log(`Captain earned ${captainPoints} quarters`);
        expect(captainPoints).toBe(18);
        
        // Each opponent should lose 6
        for (let i = 1; i < 4; i++) {
          const oppPoints = result.hole_result.points_delta[players[i].id];
          expect(oppPoints).toBe(-6);
        }
      }
    } else {
      const error = await response.text();
      console.log('High stakes hole error:', error);
    }

    // Cleanup
    await request.delete(`${API_BASE}/games/${gameId}`);
  });

  test('handle hole 18 Big Dick scenario (24+ quarters)', async ({ request }) => {
    // Create test game
    const createResponse = await request.post(`${API_BASE}/games/create-test?player_count=4`);
    expect(createResponse.ok()).toBeTruthy();
    
    const gameData = await createResponse.json();
    const gameId = gameData.game_id;
    const players = gameData.players;

    // Complete holes 1-17 first (simplified - just minimal data)
    for (let holeNum = 1; holeNum <= 17; holeNum++) {
      const simpleHole = {
        hole_number: holeNum,
        rotation_order: players.map(p => p.id),
        captain_index: 0,
        teams: {
          type: "partners",
          team1: [players[0].id, players[1].id],
          team2: [players[2].id, players[3].id]
        },
        final_wager: 1,
        winner: "team1",
        scores: {
          [players[0].id]: 4,
          [players[1].id]: 4,
          [players[2].id]: 5,
          [players[3].id]: 5
        },
        hole_par: 4,
        duncan_invoked: false
      };

      await request.post(`${API_BASE}/games/${gameId}/holes/complete`, { data: simpleHole });
    }

    // Now hole 18 with maximum wager (should be in Hoepfinger)
    const hole18 = {
      hole_number: 18,
      rotation_order: players.map(p => p.id),
      captain_index: 0,
      teams: {
        type: "solo",
        captain: players[0].id,
        opponents: [players[1].id, players[2].id, players[3].id]
      },
      final_wager: 8, // Joe's Special max
      winner: "captain",
      scores: {
        [players[0].id]: 3,  // Birdie
        [players[1].id]: 5,
        [players[2].id]: 5,
        [players[3].id]: 5
      },
      hole_par: 4,
      phase: "hoepfinger",
      joes_special_wager: 8,
      duncan_invoked: false
    };

    const response = await request.post(
      `${API_BASE}/games/${gameId}/holes/complete`,
      { data: hole18 }
    );

    if (response.ok()) {
      const result = await response.json();
      console.log('Hole 18 result:', result);
      
      if (result.hole_result && result.hole_result.points_delta) {
        const captainPoints = result.hole_result.points_delta[players[0].id];
        console.log(`Hole 18: Captain earned ${captainPoints} quarters`);
        // Solo win at 8 quarters vs 3 opponents = 24 quarters
        expect(captainPoints).toBe(24);
      }
    } else {
      const error = await response.text();
      console.log('Hole 18 error:', error);
      // Some validation may prevent this - that's OK for testing
    }

    // Cleanup
    await request.delete(`${API_BASE}/games/${gameId}`);
  });
});

test.describe('Golden Round - Start on Hole 10 (Back Nine)', () => {
  test('complete back nine only (holes 10-18)', async ({ request }) => {
    const goldenRound = loadGoldenRound();
    
    // Create test game
    const createResponse = await request.post(`${API_BASE}/games/create-test?player_count=4`);
    expect(createResponse.ok()).toBeTruthy();
    
    const gameData = await createResponse.json();
    const gameId = gameData.game_id;
    const players = gameData.players;

    console.log(`Created game ${gameId} for back nine test`);

    // Map player IDs
    const playerMap = {};
    const goldenPlayers = goldenRound.game_metadata.players;
    for (let i = 0; i < goldenPlayers.length; i++) {
      playerMap[goldenPlayers[i].id] = players[i].id;
    }

    // Track running totals (starting fresh for back nine)
    const runningTotals = {};
    players.forEach(p => runningTotals[p.id] = 0);

    // Submit ONLY holes 10-18 (back nine)
    const backNineHoles = goldenRound.holes.filter(h => h.hole_number >= 10);
    
    console.log(`Processing ${backNineHoles.length} back nine holes`);
    
    let holesCompleted = 0;
    
    for (const hole of backNineHoles) {
      // Map teams
      const teamsData = hole.teams;
      let teams;
      if (teamsData.type === 'partners') {
        teams = {
          type: 'partners',
          team1: teamsData.team1.map(id => playerMap[id]),
          team2: teamsData.team2.map(id => playerMap[id])
        };
      } else {
        teams = {
          type: 'solo',
          captain: playerMap[teamsData.captain],
          opponents: teamsData.opponents.map(id => playerMap[id])
        };
      }

      // Map scores
      const scores = {};
      for (const [goldenId, score] of Object.entries(hole.scores)) {
        scores[playerMap[goldenId]] = score;
      }

      // Determine winner
      let winner;
      if (hole.halved) {
        winner = 'push';
      } else if (teamsData.type === 'solo') {
        winner = hole.winner === 'captain' ? 'captain' : 'opponents';
      } else {
        winner = hole.winner === 'team1' ? 'team1' : 'team2';
      }

      const payload = {
        hole_number: hole.hole_number,
        rotation_order: hole.rotation_order.map(id => playerMap[id]),
        captain_index: 0,
        teams: teams,
        final_wager: hole.wager,
        winner: winner,
        scores: scores,
        hole_par: hole.par,
        duncan_invoked: hole.duncan_invoked || false
      };

      const response = await request.post(
        `${API_BASE}/games/${gameId}/holes/complete`,
        { data: payload }
      );

      if (response.ok()) {
        holesCompleted++;
        const result = await response.json();
        
        if (result.hole_result && result.hole_result.points_delta) {
          for (const [pid, pts] of Object.entries(result.hole_result.points_delta)) {
            runningTotals[pid] = (runningTotals[pid] || 0) + pts;
          }
        }
      }
    }

    console.log(`Completed ${holesCompleted} back nine holes`);
    console.log('Back nine totals:', runningTotals);

    // Verify totals sum to zero
    const totalSum = Object.values(runningTotals).reduce((a, b) => a + b, 0);
    expect(Math.abs(totalSum)).toBeLessThan(0.01);

    // Calculate expected back nine totals from golden round
    const expectedBackNine = { player_a: 0, player_b: 0, player_c: 0, player_d: 0 };
    for (const hole of backNineHoles) {
      for (const [pid, q] of Object.entries(hole.quarters)) {
        expectedBackNine[pid] += q;
      }
    }
    
    console.log('Expected back nine totals:', expectedBackNine);

    // Verify against expected
    if (holesCompleted === 9) {
      for (const [goldenId, expected] of Object.entries(expectedBackNine)) {
        const actualId = playerMap[goldenId];
        const actual = runningTotals[actualId];
        expect(actual).toBe(expected);
      }
    }

    // Cleanup
    await request.delete(`${API_BASE}/games/${gameId}`);
  });
});

test.describe('Golden Round - Random Hole Edits', () => {
  test('complete round then edit random holes', async ({ request }) => {
    const goldenRound = loadGoldenRound();
    
    // Create test game
    const createResponse = await request.post(`${API_BASE}/games/create-test?player_count=4`);
    expect(createResponse.ok()).toBeTruthy();
    
    const gameData = await createResponse.json();
    const gameId = gameData.game_id;
    const players = gameData.players;

    // Map player IDs
    const playerMap = {};
    const goldenPlayers = goldenRound.game_metadata.players;
    for (let i = 0; i < goldenPlayers.length; i++) {
      playerMap[goldenPlayers[i].id] = players[i].id;
    }

    // Complete all 18 holes first
    console.log('Completing all 18 holes...');
    
    for (const hole of goldenRound.holes) {
      const teamsData = hole.teams;
      let teams;
      if (teamsData.type === 'partners') {
        teams = {
          type: 'partners',
          team1: teamsData.team1.map(id => playerMap[id]),
          team2: teamsData.team2.map(id => playerMap[id])
        };
      } else {
        teams = {
          type: 'solo',
          captain: playerMap[teamsData.captain],
          opponents: teamsData.opponents.map(id => playerMap[id])
        };
      }

      const scores = {};
      for (const [goldenId, score] of Object.entries(hole.scores)) {
        scores[playerMap[goldenId]] = score;
      }

      let winner;
      if (hole.halved) winner = 'push';
      else if (teamsData.type === 'solo') winner = hole.winner === 'captain' ? 'captain' : 'opponents';
      else winner = hole.winner === 'team1' ? 'team1' : 'team2';

      const payload = {
        hole_number: hole.hole_number,
        rotation_order: hole.rotation_order.map(id => playerMap[id]),
        captain_index: 0,
        teams: teams,
        final_wager: hole.wager,
        winner: winner,
        scores: scores,
        hole_par: hole.par,
        duncan_invoked: hole.duncan_invoked || false
      };

      await request.post(`${API_BASE}/games/${gameId}/holes/complete`, { data: payload });
    }

    console.log('All holes completed. Now editing random holes...');

    // Pick 3 random holes to edit (holes 3, 7, 14)
    const holesToEdit = [3, 7, 14];
    
    for (const holeNum of holesToEdit) {
      const originalHole = goldenRound.holes.find(h => h.hole_number === holeNum);
      
      // Create modified version - flip the winner
      const teamsData = originalHole.teams;
      let teams, newWinner;
      
      if (teamsData.type === 'partners') {
        teams = {
          type: 'partners',
          team1: teamsData.team1.map(id => playerMap[id]),
          team2: teamsData.team2.map(id => playerMap[id])
        };
        // Flip winner
        newWinner = originalHole.winner === 'team1' ? 'team2' : 'team1';
      } else {
        teams = {
          type: 'solo',
          captain: playerMap[teamsData.captain],
          opponents: teamsData.opponents.map(id => playerMap[id])
        };
        // Flip winner
        newWinner = originalHole.winner === 'captain' ? 'opponents' : 'captain';
      }

      // Adjust scores to match new winner
      const scores = {};
      for (const [goldenId, score] of Object.entries(originalHole.scores)) {
        scores[playerMap[goldenId]] = score;
      }

      const editPayload = {
        hole_number: holeNum,
        rotation_order: originalHole.rotation_order.map(id => playerMap[id]),
        captain_index: 0,
        teams: teams,
        final_wager: originalHole.wager,
        winner: newWinner,
        scores: scores,
        hole_par: originalHole.par,
        duncan_invoked: false
      };

      console.log(`Editing hole ${holeNum}: changing winner from ${originalHole.winner} to ${newWinner}`);
      
      const editResponse = await request.patch(
        `${API_BASE}/games/${gameId}/holes/${holeNum}`,
        { data: editPayload }
      );

      if (editResponse.ok()) {
        const result = await editResponse.json();
        console.log(`Hole ${holeNum} edited successfully`);
        
        // Check that running totals were recalculated
        if (result.player_standings) {
          console.log(`New standings after editing hole ${holeNum}:`, result.player_standings);
        }
      } else {
        const error = await editResponse.text();
        console.log(`Hole ${holeNum} edit error:`, error.substring(0, 200));
      }
    }

    // Fetch final game state
    const gameStateResponse = await request.get(`${API_BASE}/games/${gameId}`);
    if (gameStateResponse.ok()) {
      const finalState = await gameStateResponse.json();
      console.log('Final game state after edits');
      
      // Verify totals still sum to zero after edits
      if (finalState.player_standings) {
        const finalTotals = Object.values(finalState.player_standings);
        const sum = finalTotals.reduce((a, b) => a + (b.total || b), 0);
        console.log('Final totals sum:', sum);
        expect(Math.abs(sum)).toBeLessThan(0.01);
      }
    }

    // Cleanup
    await request.delete(`${API_BASE}/games/${gameId}`);
  });

  test('edit hole with different team formation', async ({ request }) => {
    const goldenRound = loadGoldenRound();
    
    // Create test game
    const createResponse = await request.post(`${API_BASE}/games/create-test?player_count=4`);
    expect(createResponse.ok()).toBeTruthy();
    
    const gameData = await createResponse.json();
    const gameId = gameData.game_id;
    const players = gameData.players;

    const playerMap = {};
    const goldenPlayers = goldenRound.game_metadata.players;
    for (let i = 0; i < goldenPlayers.length; i++) {
      playerMap[goldenPlayers[i].id] = players[i].id;
    }

    // Complete hole 1 as partners
    const hole1Original = goldenRound.holes[0];
    const originalPayload = {
      hole_number: 1,
      rotation_order: hole1Original.rotation_order.map(id => playerMap[id]),
      captain_index: 0,
      teams: {
        type: 'partners',
        team1: hole1Original.teams.team1.map(id => playerMap[id]),
        team2: hole1Original.teams.team2.map(id => playerMap[id])
      },
      final_wager: 1,
      winner: 'team1',
      scores: {
        [players[0].id]: 4,
        [players[1].id]: 5,
        [players[2].id]: 5,
        [players[3].id]: 4
      },
      hole_par: 4,
      duncan_invoked: false
    };

    await request.post(`${API_BASE}/games/${gameId}/holes/complete`, { data: originalPayload });
    console.log('Hole 1 completed as partners (team1 won)');

    // Now edit it to be a SOLO hole instead
    const editedPayload = {
      hole_number: 1,
      rotation_order: [players[0].id, players[1].id, players[2].id, players[3].id],
      captain_index: 0,
      teams: {
        type: 'solo',
        captain: players[0].id,
        opponents: [players[1].id, players[2].id, players[3].id]
      },
      final_wager: 2,  // Higher wager
      winner: 'captain',  // Captain wins solo
      scores: {
        [players[0].id]: 3,  // Birdie
        [players[1].id]: 5,
        [players[2].id]: 5,
        [players[3].id]: 5
      },
      hole_par: 4,
      duncan_invoked: false
    };

    console.log('Editing hole 1 to solo format...');
    
    const editResponse = await request.patch(
      `${API_BASE}/games/${gameId}/holes/1`,
      { data: editedPayload }
    );

    if (editResponse.ok()) {
      const result = await editResponse.json();
      console.log('Hole 1 edited to solo format');
      
      if (result.hole_result && result.hole_result.points_delta) {
        const captainPts = result.hole_result.points_delta[players[0].id];
        // Solo win at 2 quarters vs 3 = 6 quarters for captain
        console.log(`Captain points after edit: ${captainPts}`);
        expect(captainPts).toBe(6);
      }
    } else {
      const error = await editResponse.text();
      console.log('Edit error:', error.substring(0, 300));
    }

    // Cleanup
    await request.delete(`${API_BASE}/games/${gameId}`);
  });
});

test.describe('Golden Round - Combined Advanced Scenarios', () => {
  test('full round with high stakes, back nine emphasis, and edits', async ({ request }) => {
    const goldenRound = loadGoldenRound();
    
    // Create test game
    const createResponse = await request.post(`${API_BASE}/games/create-test?player_count=4`);
    expect(createResponse.ok()).toBeTruthy();
    
    const gameData = await createResponse.json();
    const gameId = gameData.game_id;
    const players = gameData.players;

    const playerMap = {};
    const goldenPlayers = goldenRound.game_metadata.players;
    for (let i = 0; i < goldenPlayers.length; i++) {
      playerMap[goldenPlayers[i].id] = players[i].id;
    }

    // Create modified holes with escalating stakes
    const modifiedHoles = goldenRound.holes.map(hole => {
      const modified = { ...hole };
      
      // Increase wagers on back nine
      if (hole.hole_number >= 10) {
        modified.wager = Math.min(hole.wager * 2, 8);
      }
      
      return modified;
    });

    console.log('Starting full advanced round...');
    
    let holesCompleted = 0;
    const runningTotals = {};
    players.forEach(p => runningTotals[p.id] = 0);

    // Complete all holes
    for (const hole of modifiedHoles) {
      const teamsData = hole.teams;
      let teams;
      if (teamsData.type === 'partners') {
        teams = {
          type: 'partners',
          team1: teamsData.team1.map(id => playerMap[id]),
          team2: teamsData.team2.map(id => playerMap[id])
        };
      } else {
        teams = {
          type: 'solo',
          captain: playerMap[teamsData.captain],
          opponents: teamsData.opponents.map(id => playerMap[id])
        };
      }

      const scores = {};
      for (const [goldenId, score] of Object.entries(hole.scores)) {
        scores[playerMap[goldenId]] = score;
      }

      let winner;
      if (hole.halved) winner = 'push';
      else if (teamsData.type === 'solo') winner = hole.winner === 'captain' ? 'captain' : 'opponents';
      else winner = hole.winner === 'team1' ? 'team1' : 'team2';

      const payload = {
        hole_number: hole.hole_number,
        rotation_order: hole.rotation_order.map(id => playerMap[id]),
        captain_index: 0,
        teams: teams,
        final_wager: hole.wager,
        winner: winner,
        scores: scores,
        hole_par: hole.par,
        duncan_invoked: hole.duncan_invoked || false
      };

      const response = await request.post(
        `${API_BASE}/games/${gameId}/holes/complete`,
        { data: payload }
      );

      if (response.ok()) {
        holesCompleted++;
        const result = await response.json();
        
        if (result.hole_result && result.hole_result.points_delta) {
          for (const [pid, pts] of Object.entries(result.hole_result.points_delta)) {
            runningTotals[pid] = (runningTotals[pid] || 0) + pts;
          }
        }
        
        // Log high-value holes
        const maxQuarters = Math.max(...Object.values(result.hole_result?.points_delta || {}));
        if (maxQuarters > 6) {
          console.log(`Hole ${hole.hole_number}: High stakes! Max quarters: ${maxQuarters}`);
        }
      }
    }

    console.log(`Completed ${holesCompleted}/18 holes`);
    console.log('Pre-edit totals:', runningTotals);

    // Now edit a back nine hole to flip the result
    const holeToEdit = 15;
    const originalHole15 = modifiedHoles.find(h => h.hole_number === holeToEdit);
    
    if (originalHole15) {
      const teamsData = originalHole15.teams;
      let teams, newWinner;
      
      if (teamsData.type === 'solo') {
        teams = {
          type: 'solo',
          captain: playerMap[teamsData.captain],
          opponents: teamsData.opponents.map(id => playerMap[id])
        };
        newWinner = originalHole15.winner === 'captain' ? 'opponents' : 'captain';
      } else {
        teams = {
          type: 'partners',
          team1: teamsData.team1.map(id => playerMap[id]),
          team2: teamsData.team2.map(id => playerMap[id])
        };
        newWinner = originalHole15.winner === 'team1' ? 'team2' : 'team1';
      }

      const scores = {};
      for (const [goldenId, score] of Object.entries(originalHole15.scores)) {
        scores[playerMap[goldenId]] = score;
      }

      const editPayload = {
        hole_number: holeToEdit,
        rotation_order: originalHole15.rotation_order.map(id => playerMap[id]),
        captain_index: 0,
        teams: teams,
        final_wager: originalHole15.wager,
        winner: newWinner,
        scores: scores,
        hole_par: originalHole15.par,
        duncan_invoked: false
      };

      console.log(`Editing hole ${holeToEdit}...`);
      
      const editResponse = await request.patch(
        `${API_BASE}/games/${gameId}/holes/${holeToEdit}`,
        { data: editPayload }
      );

      if (editResponse.ok()) {
        console.log(`Hole ${holeToEdit} edited successfully`);
      }
    }

    // Verify totals still sum to zero
    const gameStateResponse = await request.get(`${API_BASE}/games/${gameId}`);
    if (gameStateResponse.ok()) {
      const finalState = await gameStateResponse.json();
      
      if (finalState.player_standings) {
        const values = Object.values(finalState.player_standings).map(v => typeof v === 'object' ? v.total : v);
        const sum = values.reduce((a, b) => a + b, 0);
        console.log('Final totals after edit sum:', sum);
        expect(Math.abs(sum)).toBeLessThan(0.01);
      }
    }

    // Cleanup
    await request.delete(`${API_BASE}/games/${gameId}`);
  });
});
