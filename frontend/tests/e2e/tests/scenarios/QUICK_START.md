# Quick Start Guide - Scenario Tests

## What You Get

45 comprehensive E2E tests covering:
- ✅ 8 Solo Wolf scenarios
- ✅ 7 Partnership scenarios
- ✅ 8 Special Rules scenarios
- ✅ 7 Betting Mechanics scenarios
- ✅ 8 Edge Case scenarios
- ✅ 7 Complete Game scenarios

## Run Tests

### All Scenarios
```bash
npm run test:e2e -- --grep "Scenarios"
```

### By Category
```bash
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/solo-wolf-scenarios.spec.js
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/partnership-scenarios.spec.js
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/special-rules-scenarios.spec.js
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/betting-scenarios.spec.js
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/edge-case-scenarios.spec.js
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/complete-game-scenarios.spec.js
```

### Specific Test
```bash
npm run test:e2e -- --grep "Captain declares solo BEFORE hitting"
npm run test:e2e -- --grep "All players tie"
npm run test:e2e -- --grep "Standard 4-man game"
```

### With Debugging
```bash
npm run test:e2e -- frontend/tests/e2e/tests/scenarios/solo-wolf-scenarios.spec.js --debug
```

## Test Files Structure

```
scenarios/
├── solo-wolf-scenarios.spec.js           # 8 tests
├── partnership-scenarios.spec.js          # 7 tests
├── special-rules-scenarios.spec.js        # 8 tests
├── betting-scenarios.spec.js              # 7 tests
├── edge-case-scenarios.spec.js            # 8 tests
├── complete-game-scenarios.spec.js        # 7 tests
├── README.md                              # Full documentation
├── IMPLEMENTATION_NOTES.md                # Technical details
└── QUICK_START.md                         # This file
```

## Key Testing Patterns

### Pattern 1: Create Game + Play Holes
```javascript
const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
gameId = gameData.game_id;
players = gameData.players;

const p1 = players[0].id;
const p2 = players[1].id;
const p3 = players[2].id;
const p4 = players[3].id;

// Navigate to game
await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
await scorekeeperPage.verifyGameLoaded(gameId);

// Play hole 1: Solo format
await scorekeeperPage.playHole(1, {
  scores: { [p1]: 4, [p2]: 5, [p3]: 6, [p4]: 7 },
  captain: p1,
  solo: true
});

// Check results
const p1Points = await scorekeeperPage.getPlayerPoints(p1);
expect(p1Points).toBe(3); // Solo win = +3
```

### Pattern 2: Verify Zero-Sum
```javascript
const p1 = await scorekeeperPage.getPlayerPoints(p1);
const p2 = await scorekeeperPage.getPlayerPoints(p2);
const p3 = await scorekeeperPage.getPlayerPoints(p3);
const p4 = await scorekeeperPage.getPlayerPoints(p4);

const total = p1 + p2 + p3 + p4;
expect(Math.abs(total)).toBeLessThan(0.01); // Always sums to zero
```

### Pattern 3: Multi-Hole Game
```javascript
for (let hole = 1; hole <= 5; hole++) {
  const scenario = holeScenarios[hole - 1];

  await scorekeeperPage.playHole(hole, {
    scores: scenario.scores,
    captain: scenario.captain,
    solo: scenario.solo || false,
    partnership: scenario.partnership || null
  });

  // Verify zero-sum at each step
  const total =
    (await scorekeeperPage.getPlayerPoints(p1)) +
    (await scorekeeperPage.getPlayerPoints(p2)) +
    (await scorekeeperPage.getPlayerPoints(p3)) +
    (await scorekeeperPage.getPlayerPoints(p4));

  expect(Math.abs(total)).toBeLessThan(0.01);
}
```

## Game Rules Reference

### Solo (Wolf/Pig)
- Captain plays alone vs partnership of 3
- Win: Captain +3, Others -1 each
- Loss: Captain -3, Others +1 each
- Mandatory holes 1-16 in 4-man

### Partnership (Goat)
- Captain selects partner
- Best-ball format
- Win: Each partner +1.5, Opponents -1.5 each
- Loss: Each partner -1.5, Opponents +1.5 each

### Special Rules
- **Float**: Delay decision to next hole
- **Joe's Special**: Low player sets wager (2/4/8)
- **Hoepfinger**: Holes 17-18 special format
- **Vinnie's Variation**: 2x points holes 13-16
- **The Option**: Auto-double when furthest down
- **Ackerley's Gambit**: Opt-in higher wager

## Expected Quarter Values

| Scenario | P1 | P2 | P3 | P4 | Total |
|----------|----|----|----|----|-------|
| Solo Win | +3 | -1 | -1 | -1 | 0 |
| Solo Loss | -3 | +1 | +1 | +1 | 0 |
| Partnership Win | +1.5 | +1.5 | -1.5 | -1.5 | 0 |
| Partnership Loss | -1.5 | -1.5 | +1.5 | +1.5 | 0 |
| All Tie | 0 | 0 | 0 | 0 | 0 |

## Test Results

### Expected Timing
- Each test: 10-30 seconds
- Full suite (45 tests): 15-20 minutes
- With serial execution (default): ~20 minutes

### Output Locations
- HTML Report: `playwright-report/index.html`
- XML Report: `test-results/junit.xml`
- Screenshots: `test-results/[test-name]-*.png`
- Videos: `test-results/[test-name]-*.webm` (on failure)

## Common Commands

```bash
# Run all scenario tests
npm run test:e2e -- --grep "Scenarios"

# Run solo wolf tests only
npm run test:e2e -- --grep "Solo Wolf Scenarios"

# Run with detailed output
npm run test:e2e -- --grep "Scenarios" --reporter=verbose

# Debug specific test
npm run test:e2e -- --grep "Captain declares solo" --debug

# Update snapshots (if using snapshot testing)
npm run test:e2e -- --grep "Scenarios" --update-snapshots

# Show test list without running
npm run test:e2e -- --grep "Scenarios" --list
```

## Debugging Failed Tests

### 1. Check Console Output
Tests include console.log() showing calculations:
```
Hole 1 - Duncan solo win: P1=3, P2=-1, P3=-1, P4=-1
Zero-sum validation passed: Total=0
```

### 2. Review HTML Report
```bash
open playwright-report/index.html
```

### 3. Debug with Inspector
```bash
npm run test:e2e -- solo-wolf-scenarios.spec.js --debug
```

### 4. Check Test Results
```bash
cat test-results/junit.xml
ls -la test-results/ | grep screenshot
```

## Key Files to Know

| File | Purpose |
|------|---------|
| `APIHelpers` | Game creation & API calls |
| `ScorekeeperPage` | UI interaction abstraction |
| `cleanupTestGame` | Test cleanup helper |
| `test-helpers.js` | Utility functions |

## File Locations

- Tests: `/frontend/tests/e2e/tests/scenarios/*.spec.js`
- Page Objects: `/frontend/tests/e2e/page-objects/`
- Fixtures: `/frontend/tests/e2e/fixtures/`
- Utilities: `/frontend/tests/e2e/utils/`

## Next Steps

1. **Read README.md** for detailed documentation
2. **Review IMPLEMENTATION_NOTES.md** for technical details
3. **Run tests** to ensure environment is working
4. **Review test code** to understand patterns
5. **Add new tests** following same patterns
6. **Maintain tests** as UI/rules change

## Troubleshooting

### Port Already in Use
```bash
# Kill processes on port 3333 and 8333
lsof -ti:3333 | xargs kill -9
lsof -ti:8333 | xargs kill -9
```

### Tests Timeout
- Increase timeout in `playwright.config.js`
- Check if servers are starting properly
- Review console for errors

### API Calls Fail
- Ensure backend is running on port 8333
- Check `APIHelpers` configuration
- Verify game creation endpoint works

### UI Selectors Not Found
- Review `ScorekeeperPage.js` selectors
- Check if UI structure changed
- Use `--debug` mode to inspect DOM

## Support

Refer to:
- **README.md** - Complete documentation
- **IMPLEMENTATION_NOTES.md** - Technical deep dive
- **Test comments** - Individual test explanations
- **Console output** - Debug information

## Summary

You now have a comprehensive test suite for Wolf Goat Pig that:
- ✅ Tests all game mechanics
- ✅ Validates quarter calculations
- ✅ Ensures zero-sum property
- ✅ Covers edge cases
- ✅ Simulates realistic games
- ✅ Runs efficiently (~20 minutes)
- ✅ Integrates with CI/CD
- ✅ Provides clear debugging info

Ready to use! 🎉
