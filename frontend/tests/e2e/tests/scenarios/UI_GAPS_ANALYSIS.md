# Wolf Goat Pig - UI Gaps Analysis

## Overview
Your scenario tests are revealing that the UI is missing critical elements needed for complete Wolf Goat Pig gameplay. The backend logic exists, but the frontend needs these interactive elements.

## ✅ **What Already Exists** (Found in SimpleScorekeeper.jsx)

1. **✅ Scorekeeper Container** - `data-testid="scorekeeper-container"`
2. **✅ Score Input Fields** - `data-testid="score-input-${playerId}"`
3. **✅ Partner Selection** - `data-testid="partner-${playerId}"`
4. **✅ Go Solo Button** - `data-testid="go-solo-button"`
5. **✅ Complete Hole Button** - `data-testid="complete-hole-button"`
6. **✅ Quarters Input** - `data-testid="quarters-input-${playerId}"`

## ❌ **Missing UI Elements** (Needed for Tests)

### 1. ❌ **Current Hole Display**
**Missing:** `data-testid="current-hole"`
**Purpose:** Shows which hole players are currently on (1-18)
**Example:** "Hole 5 of 18"
**Location:** Should be prominently displayed at top of scorekeeper

### 2. ❌ **Player Running Totals Display**
**Missing:** `data-testid="player-${playerId}-points"`
**Purpose:** Shows each player's current quarter total (running score)
**Example:**
- Player 1: +5.5 quarters
- Player 2: -3.0 quarters
- Player 3: +1.5 quarters
- Player 4: -4.0 quarters

**Requirement:** Must sum to zero (zero-sum game)
**Location:** Should be visible near player names/scores

### 3. ❌ **Special Rules UI Elements**

#### a) Float Button
**Missing:** `data-testid="float-button-${playerId}"`
**Purpose:** Captain can invoke "Float" to delay solo decision
**Rule:** Can only be used once per player per game
**Behavior:** Doubles the wager, delays partner selection

#### b) Joe's Special Wager Input
**Missing:** `data-testid="joes-special-wager-input"`
**Purpose:** During Hoepfinger phase, low player sets wager (2/4/8 quarters)
**Rule:** Only available on holes 17-18 (4-man game)
**Behavior:** Player furthest down chooses starting wager

#### c) Duncan Indicator
**Missing:** `data-testid="duncan-indicator"`
**Purpose:** Shows when captain declares solo BEFORE hitting (3-for-2 payoff)
**Rule:** Duncan = declaring solo before tee shot
**Behavior:** Changes quarter calculation from 3/1 split to 3-for-2

#### d) Hoepfinger Phase Indicator
**Missing:** `data-testid="hoepfinger-phase"`
**Purpose:** Indicates game has entered Hoepfinger phase (final holes)
**Rule:** Begins on hole 17 (4-man), hole 16 (5-man)
**Behavior:** Special rules apply, goat chooses rotation spot

#### e) Vinnie's Variation Indicator
**Missing:** `data-testid="vinnies-variation-active"`
**Purpose:** Shows when double points are active (holes 13-16)
**Rule:** Base wager doubled for these holes
**Behavior:** Visual indicator that points are doubled

### 4. ❌ **Betting UI Elements**

#### a) Current Wager Display
**Missing:** `data-testid="current-wager"`
**Purpose:** Shows the current wager for this hole
**Example:** "Current Wager: 2 quarters" or "Current Wager: 8 quarters (Joe's Special)"

#### b) Double Button
**Missing:** `data-testid="double-button"`
**Purpose:** Teams can offer to double the current wager
**Behavior:** If accepted, wager doubles; if declined, offerer wins automatically

#### c) Carry-Over Indicator
**Missing:** `data-testid="carry-over-amount"`
**Purpose:** Shows quarters carried over from tied holes
**Example:** "Carry-Over: +4 quarters from last hole"

#### d) The Option Indicator
**Missing:** `data-testid="option-active"`
**Purpose:** Shows when "The Option" is automatically active
**Rule:** Automatic double when captain is furthest down
**Behavior:** Can be turned off by captain before teeing off

### 5. ❌ **Game Phase Indicators**

#### a) Captain Indicator
**Missing:** `data-testid="captain-indicator"`
**Purpose:** Clearly shows who is captain for current hole
**Example:** Highlight or badge on captain's name

#### b) Rotation Order Display
**Missing:** `data-testid="rotation-order"`
**Purpose:** Shows the tee-off order for current hole
**Example:** "Order: Player 2 → Player 3 → Player 4 → Player 1"

#### c) Team Formation Status
**Missing:** `data-testid="team-status"`
**Purpose:** Shows current team alignment
**Examples:**
- "Captain solo vs 3 opponents"
- "Team 1 (P1+P2) vs Team 2 (P3+P4)"
- "Awaiting partner selection..."

### 6. ❌ **Zero-Sum Validation Display**
**Missing:** `data-testid="zero-sum-validation"`
**Purpose:** Real-time validation that quarters balance to zero
**Example:** "✓ Quarters balanced: 0.0"
**Color coding:**
- Green ✓ when balanced
- Red ✗ when imbalanced (indicates error)

## 📋 **Implementation Priority**

### **Phase 1: Critical (Required for Basic Gameplay)**
1. Current Hole Display - `data-testid="current-hole"`
2. Player Running Totals - `data-testid="player-${playerId}-points"`
3. Current Wager Display - `data-testid="current-wager"`
4. Zero-Sum Validation - `data-testid="zero-sum-validation"`

### **Phase 2: Core Game Mechanics**
5. Captain Indicator - `data-testid="captain-indicator"`
6. Team Status Display - `data-testid="team-status"`
7. Hoepfinger Phase Indicator - `data-testid="hoepfinger-phase"`

### **Phase 3: Special Rules**
8. Float Button - `data-testid="float-button-${playerId}"`
9. Joe's Special Input - `data-testid="joes-special-wager-input"`
10. Duncan Indicator - `data-testid="duncan-indicator"`
11. Vinnie's Variation - `data-testid="vinnies-variation-active"`

### **Phase 4: Advanced Betting**
12. Double Button - `data-testid="double-button"`
13. Carry-Over Indicator - `data-testid="carry-over-amount"`
14. The Option Indicator - `data-testid="option-active"`
15. Rotation Order - `data-testid="rotation-order"`

## 🎯 **Quick Wins**

These are easy to add and provide immediate value:

1. **Current Hole** - Add simple text display: `<div data-testid="current-hole">Hole {currentHole} of 18</div>`

2. **Running Totals** - Add to player name display:
```jsx
<span data-testid={`player-${player.id}-points`}>
  {playerStandings[player.id] > 0 ? '+' : ''}{playerStandings[player.id].toFixed(1)}
</span>
```

3. **Zero-Sum Validation** - Add calculated check:
```jsx
const totalQuarters = Object.values(playerStandings).reduce((sum, val) => sum + val, 0);
const isBalanced = Math.abs(totalQuarters) < 0.01;
<div data-testid="zero-sum-validation" style={{color: isBalanced ? 'green' : 'red'}}>
  {isBalanced ? '✓' : '✗'} Quarters: {totalQuarters.toFixed(2)}
</div>
```

## 🔧 **Recommended Approach**

1. **Start with Phase 1** - Get the basic display elements working
2. **Run scenario tests** - See which tests pass with Phase 1 complete
3. **Add Phase 2** - Core game mechanics for team formation
4. **Run tests again** - More tests should pass
5. **Iterate on Phases 3-4** - Add special rules as needed

## 📊 **Test Coverage Impact**

With all elements implemented, you'll be able to run comprehensive E2E tests that verify:
- ✅ Complete game flows from hole 1-18
- ✅ Solo vs partnership dynamics
- ✅ Special rules (Float, Duncan, Hoepfinger, Joe's Special)
- ✅ Betting mechanics (doubles, carry-overs, options)
- ✅ Zero-sum validation throughout
- ✅ Edge cases (ties, extreme scores, comebacks)

## 💡 **Next Steps**

Would you like me to:
1. **Implement Phase 1** elements right now (quick wins)?
2. **Create a complete UI enhancement PR** with all elements?
3. **Focus on specific features** you want most urgently?
4. **Generate mock-ups** of what the enhanced UI should look like?

The scenario tests are READY - they just need the UI to catch up! 🚀
