# Quarters-Focused Scenario Tests

## Overview
These tests focus on **quarter calculation and zero-sum validation** using your existing SimpleScorekeeper UI with manual quarter entry.

## What Gets Tested

### ✅ **Quarter Distribution Patterns**

1. **Solo Win** (+3, -1, -1, -1)
   - Solo player wins = gets 3 quarters
   - Each opponent loses = pays 1 quarter
   - Sum = 0 ✓

2. **Solo Loss** (-3, +1, +1, +1)
   - Solo player loses = pays 3 quarters
   - Each opponent wins = gets 1 quarter
   - Sum = 0 ✓

3. **Partnership Win** (+1.5, +1.5, -1.5, -1.5)
   - Winning team splits 3 quarters = 1.5 each
   - Losing team splits -3 quarters = -1.5 each
   - Sum = 0 ✓

4. **All Tied** (0, 0, 0, 0)
   - Nobody wins or loses
   - Carry-over to next hole
   - Sum = 0 ✓

### ✅ **Zero-Sum Validation**

- **Accepts** valid entries that sum to zero
- **Rejects** imbalanced entries
- **Shows error** when quarters don't balance
- **Validates** before completing hole

### ✅ **Running Totals**

Tests that quarters accumulate correctly across multiple holes:
- Hole 1: P1=+3, P2=-1, P3=-1, P4=-1
- Hole 2: P1=-1, P2=+3, P3=-1, P4=-1
- Hole 3: P1=+1.5, P2=+1.5, P3=-1.5, P4=-1.5
- **Running Totals**: P1=+3.5, P2=+3.5, P3=-3.5, P4=-3.5
- **Total Sum = 0** ✓

### ✅ **Edge Cases**

- Fractional quarters (1.5, 2.5, etc.)
- Large wagers (8+ quarters for Joe's Special)
- Negative to positive swings
- Close games with small differences

## Test Files

### `quarters-calculation-scenarios.spec.js` (8 tests)
Comprehensive quarters validation covering:
- Solo win/loss patterns
- Partnership distributions
- Zero-sum validation
- Running totals
- Fractional quarters
- Large wagers

## How to Run

```bash
# Run all quarters tests
npm run test:e2e -- tests/scenarios/quarters-calculation-scenarios.spec.js

# Run with UI mode for debugging
npm run test:e2e -- tests/scenarios/quarters-calculation-scenarios.spec.js --ui

# Run specific test
npm run test:e2e -- tests/scenarios/quarters-calculation-scenarios.spec.js -g "Solo win"
```

## What This Validates

✅ **Quarters always balance to zero** (zero-sum property)
✅ **Running totals accumulate correctly** across holes
✅ **Validation catches errors** before completing holes
✅ **All distribution patterns work** (solo, partnership, ties)
✅ **Fractional values work** (1.5, 2.5, etc.)
✅ **Large wagers work** (Joe's Special, Vinnie's Variation)

## Expected Behavior

When tests pass, you'll know:
1. ✓ Quarter entry system works correctly
2. ✓ Zero-sum validation is enforced
3. ✓ Running totals track properly
4. ✓ All game scenarios can be played
5. ✓ No quarters "leak" or get lost

## Next Steps

If these tests pass:
- ✅ Your quarters calculation is solid
- ✅ Game can be played hole-by-hole
- ✅ Zero-sum property is maintained

If tests fail:
- 🔍 Check which quarter pattern fails
- 🔍 Verify zero-sum validation logic
- 🔍 Check running totals calculation
- 🔍 Review quarter input handling

## Focus Areas

Since you want to focus on quarters calculating, these tests ensure:

1. **Accuracy** - Quarters distribute correctly
2. **Validation** - Errors are caught early
3. **Persistence** - Totals accumulate properly
4. **Integrity** - Zero-sum property maintained
5. **Coverage** - All scenarios tested

The test suite is **lean and focused** - just quarters, no complex UI interactions.
