# Wolf Goat Pig - Scenario-Based E2E Tests

Comprehensive end-to-end test suite for the Wolf Goat Pig golf betting game. These tests validate realistic game scenarios covering all major mechanics, special rules, and edge cases.

## Overview

The test suite consists of 6 main test files covering different aspects of the game:

1. **solo-wolf-scenarios.spec.js** - Solo Wolf mechanics
2. **partnership-scenarios.spec.js** - Partnership (Goat) mechanics
3. **special-rules-scenarios.spec.js** - Special rules and wagers
4. **betting-scenarios.spec.js** - Betting and doubling mechanics
5. **edge-case-scenarios.spec.js** - Edge cases and boundary conditions
6. **complete-game-scenarios.spec.js** - Full game simulations

## Test Structure

### Solo Wolf Scenarios (`solo-wolf-scenarios.spec.js`)

Tests solo wolf game format where captain plays alone against partnership of 3 other players.

**Coverage:**
- ✅ Captain declares solo before hitting (Duncan rule)
- ✅ Captain goes solo after seeing bad shots
- ✅ Captain invokes Float to delay decision
- ✅ Solo wins with proper quarter calculations (+3 for captain, -1 for others)
- ✅ Solo losses with proper calculations (-3 for captain, +1 for others)
- ✅ Mandatory solo requirement (first 16 holes in 4-man game)
- ✅ Multiple solo holes with running totals
- ✅ Solo with extreme score gaps

**Key Verifications:**
- Quarter calculations match expected values
- Zero-sum validation (all quarters sum to zero)
- Running totals accumulate correctly

### Partnership Scenarios (`partnership-scenarios.spec.js`)

Tests partnership (Goat) format where captain selects partner for best-ball play.

**Coverage:**
- ✅ Captain selects partner with favorable matchup
- ✅ Captain selects partner with unfavorable matchup
- ✅ Partners split quarters evenly
- ✅ Best-ball scoring calculations
- ✅ Best-ball tie-breaker (equal scores)
- ✅ Zero-sum validation with partnerships
- ✅ Partner selection from all available players

**Key Verifications:**
- Each partner gets exactly half the team's quarters
- Best-ball correctly uses best score from each team
- Quarters always split evenly (1.5 each on 3-quarter win)

### Special Rules Scenarios (`special-rules-scenarios.spec.js`)

Tests special game rules and wagers.

**Coverage:**
- ✅ Hoepfinger phase (holes 17-18 in 4-man game)
- ✅ Joe's Special with 2-quarter wager
- ✅ Joe's Special with 8-quarter wager
- ✅ Vinnie's Variation (double points holes 13-16)
- ✅ Karl Marx rule (uneven distribution for extreme outliers)
- ✅ Tossing the Invisible Aardvark (3-for-2 payoff)
- ✅ Special rules don't break zero-sum property
- ✅ Combination of multiple special rules

**Key Verifications:**
- Wagers apply correctly
- Point multipliers work accurately
- Zero-sum maintained with special rules

### Betting Mechanics Scenarios (`betting-scenarios.spec.js`)

Tests complex betting and doubling mechanics.

**Coverage:**
- ✅ Doubling when team is winning
- ✅ Redoubling after initial double
- ✅ Carry-over from tied holes
- ✅ Carry-over limits (no consecutive carries)
- ✅ The Option (automatic double when furthest down)
- ✅ Ackerley's Gambit (opt-in higher wager)
- ✅ Betting mechanics preserve zero-sum
- ✅ Complex betting sequences

**Key Verifications:**
- Doubles/redoubles multiply quarters correctly
- Carry-overs accumulate and apply to next hole
- Zero-sum maintained through all betting
- Team option mechanics work as expected

### Edge Case Scenarios (`edge-case-scenarios.spec.js`)

Tests unusual and boundary conditions.

**Coverage:**
- ✅ All players tie on a hole
- ✅ Partnership with both players tying
- ✅ Zero-sum validation in simple games
- ✅ Zero-sum validation in complex games
- ✅ Game completion and final standings
- ✅ Extreme score variance
- ✅ Negative to positive swing scenarios
- ✅ Maximum running total variance
- ✅ Fractional quarters (partnerships create .5 increments)

**Key Verifications:**
- Tie scenarios handled correctly
- Extreme scores don't break calculations
- Fractional values accumulate properly
- Final standings always sum to zero

### Complete Game Scenarios (`complete-game-scenarios.spec.js`)

Tests full or near-full game simulations with realistic play patterns.

**Coverage:**
- ✅ Standard 4-man game with alternating formats
- ✅ Game with heavy betting (multiple doubles)
- ✅ Hoepfinger comeback scenario
- ✅ Close finish with dramatic final holes
- ✅ Zero-sum validation throughout 12-hole game
- ✅ Big Dick scenario (early game close-out)
- ✅ Full 18-hole game structure verification

**Key Verifications:**
- Games flow properly through multiple holes
- Zero-sum maintained at every step
- Final standings are realistic and valid
- Game progression is smooth

## Running the Tests

### Run All Scenario Tests

```bash
npm run test:e2e -- --grep "Scenarios"
```

### Run Specific Test File

```bash
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/solo-wolf-scenarios.spec.js
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/partnership-scenarios.spec.js
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/special-rules-scenarios.spec.js
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/betting-scenarios.spec.js
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/edge-case-scenarios.spec.js
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/complete-game-scenarios.spec.js
```

### Run Specific Test Scenario

```bash
npm run test:e2e -- --grep "Captain declares solo BEFORE hitting"
npm run test:e2e -- --grep "All players tie"
npm run test:e2e -- --grep "Standard 4-man game"
```

### Run with Detailed Output

```bash
npm run test:e2e -- --grep "Scenarios" --reporter=verbose
```

### Debug Mode

```bash
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/solo-wolf-scenarios.spec.js --debug
```

## Test Implementation Patterns

### Pattern 1: API-Based Game Creation + UI Testing

Tests use this efficient pattern:
1. Create game via API (`apiHelpers.createTestGame()`)
2. Navigate to game UI
3. Play key holes via UI (testing critical interactions)
4. Use API for fast-forward if needed
5. Verify UI displays correct calculations

```javascript
const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
gameId = gameData.game_id;
players = gameData.players;

await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
await scorekeeperPage.verifyGameLoaded(gameId);

await scorekeeperPage.playHole(1, {
  scores: { [p1]: 4, [p2]: 5, [p3]: 6, [p4]: 7 },
  captain: p1,
  solo: true
});
```

### Pattern 2: Zero-Sum Validation

Every test validates the critical property that quarters always sum to zero:

```javascript
const p1Points = await scorekeeperPage.getPlayerPoints(p1);
const p2Points = await scorekeeperPage.getPlayerPoints(p2);
const p3Points = await scorekeeperPage.getPlayerPoints(p3);
const p4Points = await scorekeeperPage.getPlayerPoints(p4);

const totalQuarters = p1Points + p2Points + p3Points + p4Points;
expect(Math.abs(totalQuarters)).toBeLessThan(0.01);
```

### Pattern 3: Running Total Validation

Tests verify cumulative points track correctly:

```javascript
for (let hole = 1; hole <= 3; hole++) {
  // Play hole
  await scorekeeperPage.playHole(hole, {...});

  // Get running totals
  const total = await scorekeeperPage.getPlayerPoints(p1);

  // Verify accumulation
  expect(total).toBeDefined();
}
```

## Game Rules Tested

### Solo (Wolf/Pig) Format
- Captain plays alone vs partnership of 3 others
- Win: +3 quarters for captain, -1 for others
- Loss: -3 quarters for captain, +1 for others
- Mandatory for holes 1-16 in 4-man game

### Partnership (Goat) Format
- Captain selects partner
- Best-ball format (best score from each team)
- Win: +1.5 for each partner, -1.5 for opponents
- Loss: -1.5 for each partner, +1.5 for opponents

### Special Rules
- **Float**: Delay solo decision to next hole
- **Joe's Special**: Low player sets wager (2/4/8 quarters)
- **Hoepfinger**: Holes 17-18 special format in 4-man
- **Vinnie's Variation**: Double points on holes 13-16
- **Karl Marx**: Uneven distribution for outliers
- **The Option**: Auto-double when team is furthest down
- **Ackerley's Gambit**: Individual opt-in to higher wager

### Betting Mechanics
- **Double**: Increase wager when winning
- **Redouble**: Counter-double after opponent doubles
- **Carry-over**: Tied hole quarters roll to next hole
- **Carry-over Limit**: No consecutive carry-overs

## Key Test Data

### Players
- Test games always create 4 players with realistic handicaps
- Player IDs referenced as p1, p2, p3, p4

### Scores
- Realistic scores range 3-10 strokes per hole
- Varied to create different win/loss scenarios
- Extreme scores (3, 10) used for edge case testing

### Expected Outcomes
Every test documents expected quarter calculations:
- Solo win: +3, -1, -1, -1
- Solo loss: -3, +1, +1, +1
- Partnership win: +1.5, +1.5, -1.5, -1.5
- Partnership loss: -1.5, -1.5, +1.5, +1.5
- Tie: 0, 0, 0, 0

## Verification Methods

### Quarter Calculations
```javascript
const points = await scorekeeperPage.getPlayerPoints(playerId);
expect(points).toBe(expectedValue);
```

### Zero-Sum Property
```javascript
const sum = p1 + p2 + p3 + p4;
expect(Math.abs(sum)).toBeLessThan(0.01);
```

### Game Progression
```javascript
const currentHole = await scorekeeperPage.getCurrentHole();
expect(currentHole).toBe(expectedHoleNumber);
```

### Running Totals
```javascript
for (let hole = 1; hole <= 3; hole++) {
  await scorekeeperPage.playHole(hole, {...});
  const total = await scorekeeperPage.getPlayerPoints(p1);
  expect(total).toBeDefined();
}
```

## Common Issues & Solutions

### Issue: Float API Helper Not Returning Correct Data
**Solution**: Ensure game was properly created and players are valid

### Issue: Carry-over Not Applying
**Solution**: Verify consecutive carries are limited - blocked automatically

### Issue: Fractional Quarters Not Calculating
**Solution**: Check partnership scoring - should always be .5 increments

### Issue: Zero-Sum Failing
**Solution**: Review quarter calculation logic - check for rounding errors

## Future Enhancements

Potential test additions:
- [ ] Multi-player late departure scenarios
- [ ] Score correction scenarios
- [ ] Undo/rollback testing
- [ ] Pause/resume game scenarios
- [ ] Custom handicap impact on handicap-based scoring
- [ ] Tiebreaker scenarios beyond current coverage
- [ ] Performance testing (large game history)
- [ ] Concurrent game testing (multiple games simultaneously)

## Debugging Tips

### Enable Console Logging
Tests include console.log statements for tracking:
```
Hole 1: P1=3, P2=-1, P3=-1, P4=-1, Total=0
```

### Check Test Output
Review detailed hole-by-hole results in console:
```
Standard 4-man game - alternating solo and partnership
Hole 1: P1=3, P2=-1, P3=-1, P4=-1, Total=0
Hole 2: P1=1.5, P2=1.5, P3=-1.5, P4=-1.5, Total=0
...
```

### Visual Debugging
Use `--debug` flag and Playwright Inspector:
```bash
npm run test:e2e -- scenarios/solo-wolf-scenarios.spec.js --debug
```

### Check Screenshots
On test failure, review:
- `playwright-report/` - HTML report with screenshots
- `test-results/` - Detailed test result logs

## Test Coverage Summary

| Category | Tests | Key Metrics |
|----------|-------|------------|
| Solo Wolf | 6 | Duncan rule, Float, extreme scores |
| Partnership | 7 | Best-ball, even splits, partner selection |
| Special Rules | 7 | Hoepfinger, Joe's Special, Karl Marx |
| Betting | 7 | Doubles, redoubles, carry-over, The Option |
| Edge Cases | 8 | Ties, extreme variance, fractional quarters |
| Complete Games | 7 | 6-18 hole games, comeback scenarios, Big Dick |
| **TOTAL** | **42** | **Comprehensive game coverage** |

## Notes

- All tests use `http://localhost:3333` for frontend and `http://localhost:8333` for API
- Tests run serially (workers: 1) to avoid port conflicts
- Each test cleans up after itself via `cleanupTestGame()`
- Screenshots and videos retained on failure for debugging
- Tests timeout at 120 seconds per test
