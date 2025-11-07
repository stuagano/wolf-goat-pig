# Scorekeeper Rules Compliance Analysis

**Date**: 2025-01-07
**Component Analyzed**: SimpleScorekeeper.jsx + /games/{game_id}/holes/complete endpoint
**Reference**: Official Wolf Goat Pig Rules (WOLF_GOAT_PIG_RULES.md)

## Executive Summary

The current scorekeeper implementation supports **basic 4-man game functionality** but is missing significant rule mechanics, betting conventions, and game phase logic that are essential to the full Wolf Goat Pig experience as defined in the official rules.

**Overall Rule Coverage**: ~35-40%

### ✅ What's Implemented (Working)
- Basic team formation (Partners vs Solo modes)
- Score entry and tracking
- Quarter tracking and standings
- Float tracking (one-time use per player, enforced)
- Option tracking (informational)
- Solo requirement tracking (visual indicator for 1 solo per player)
- Double button (manual wager increase)
- Push outcomes
- Flush outcomes (double-rejection wins)
- Hole editing capability
- Golf-style scorecard display

### ❌ Critical Missing Rules & Features

---

## Detailed Rule-by-Rule Analysis

### 1. CAPTAIN ROTATION ⚠️ **MISSING**

**Rule**: The player selected to go first is the Captain. Order rotates each hole.

**Status**: ❌ NOT IMPLEMENTED
- No captain rotation tracking
- No toss tees implementation
- No visual indicator of hitting order
- User manually selects captain each hole (prone to error)

**Required Implementation**:
- Track rotation order per hole
- Display hitting order (1st, 2nd, 3rd, 4th)
- Auto-rotate for next hole
- Show current captain indicator

---

### 2. THE HOEPFINGER PHASE ⚠️ **MISSING**

**Rule**:
- 4-man: Starts hole 17
- 5-man: Starts hole 16
- 6-man: Starts hole 13
- Furthest down (Goat) chooses rotation spot

**Status**: ❌ NOT IMPLEMENTED
- No Hoepfinger phase detection
- No rotation selection for the Goat
- No special rules for Hoepfinger holes

**Required Implementation**:
- Detect when Hoepfinger starts based on player count
- Allow Goat to select their position in rotation
- Apply Joe's Special betting rules during Hoepfinger

---

### 3. JOE'S SPECIAL ⚠️ **MISSING**

**Rule**: During Hoepfinger, the Goat may set starting wager at 2, 4, or 8 quarters (or natural carryover if higher). Max 8 quarters. No doubling until all tee shots complete.

**Status**: ❌ NOT IMPLEMENTED
- No special Hoepfinger wager selection
- No restriction on doubling before tee shots

**Required Implementation**:
- Goat selects base wager (2/4/8Q) on Hoepfinger holes
- Block doubling button until all players hit tee shots
- Default to max(2Q, carryover) if not invoked

---

### 4. THE OPTION (Auto-Double) ⚠️ **PARTIALLY IMPLEMENTED**

**Rule**: If Captain is furthest down (Goat), wager automatically doubles before any tee shots. Captain can turn it off.

**Status**: ⚠️ TRACKED BUT NOT ENFORCED
- `option_invoked_by` field exists
- Visual tracking in UI
- **BUT**: No automatic wager doubling logic
- **BUT**: No "turn off" mechanism for captain

**Required Implementation**:
- Detect if captain is the Goat before hole starts
- Auto-set wager to 2x base
- Add "Turn Off Option" button for captain
- Apply Option multiplier correctly in scoring

---

### 5. THE FLOAT ✅ **IMPLEMENTED**

**Rule**: Each player may invoke float once per round during their captain turn (doubles base wager).

**Status**: ✅ WORKING
- One-time use per player enforced
- Visual tracking shows used/available
- Buttons disabled after use
- Tracked in hole history

**Improvement Needed**:
- Only allow float when player IS the captain (not currently enforced)

---

### 6. THE DUNCAN (3-for-2 Solo) ⚠️ **MISSING**

**Rule**: If Captain announces BEFORE hitting that he's going solo (Pig), he wins 3 quarters for every 2 quarters wagered.

**Status**: ❌ NOT IMPLEMENTED
- No Duncan mechanic
- Solo mode uses standard 1:1 wagering

**Required Implementation**:
- Add "Duncan" checkbox for captain going solo
- Apply 3:2 win multiplier when Duncan invoked
- Only available to captain before tee shot

---

### 7. THE TUNKARRI (Aardvark 3-for-2) ⚠️ **MISSING**

**Rule**: In 5/6-man game, Aardvark can declare solo before Captain hits, wins 3-for-2.

**Status**: ❌ NOT IMPLEMENTED (5/6 man games not supported)

---

### 8. THE CARRY-OVER ⚠️ **MISSING**

**Rule**: If hole is halved (push), next hole starts at 2x the prior wager. Cannot occur on consecutive holes.

**Status**: ❌ NOT IMPLEMENTED
- Push outcomes recorded
- But no carry-over logic to next hole
- Base wager doesn't auto-increase

**Required Implementation**:
- When winner = "push", set flag for next hole
- Next hole base wager = previous wager × 2
- Prevent consecutive carry-overs (max one carry per sequence)

---

### 9. VINNIE'S VARIATION ⚠️ **MISSING**

**Rule**: In 4-man game, base wager doubles on holes 13-16.

**Status**: ❌ NOT IMPLEMENTED
- Base wager stays constant

**Required Implementation**:
- For 4-player games, holes 13-16 start at 2x base wager
- Auto-apply when entering hole 13

---

### 10. THE KARL MARX RULE ⚠️ **MISSING**

**Rule**: When quarters aren't evenly divisible, furthest down player pays/wins less. If tied, use "hanging chad" until scores diverge.

**Status**: ❌ NOT IMPLEMENTED
- Backend uses simple division (likely creates fractional quarters)
- No special allocation for odd quarters

**Example**:
- 5-man game, 3-on-2 loses, wager = 1Q
- Team of 3 wins 1Q each (3Q total)
- Team of 2 owes 3Q total
- **Karl Marx**: Furthest down owes 1Q, partner owes 2Q
- **Current Implementation**: Each owes 1.5Q (incorrect)

**Required Implementation**:
- Identify Goat among losing team
- Allocate minimum quarters to Goat, remainder to partner
- Track "hanging chad" when tied until divergence

---

### 11. THE INVISIBLE AARDVARK ⚠️ **MISSING**

**Rule**: 4-man game only. Auto-joins forcibly formed team. Can be "tossed" for 3-for-2 win potential.

**Status**: ❌ NOT IMPLEMENTED
- No Aardvark concept in 4-man mode
- No tossing mechanism
- No 3-for-2 calculation when tossed

---

### 12. TOSSING THE AARDVARK ⚠️ **MISSING**

**Rule**:
- 4-man: Tossing Invisible Aardvark = 3-for-2 win
- 5-man: Tossing Aardvark doubles wager
- 6-man: Tossing doubles wager with affected teams

**Status**: ❌ NOT IMPLEMENTED (Aardvark not supported)

---

### 13. DOUBLE POINTS ROUNDS ⚠️ **MISSING**

**Rule**: Base bet doubles during Major Championship weeks (Masters, PGA, US Open, British Open, Players) and Annual Banquet day.

**Status**: ❌ NOT IMPLEMENTED
- No tournament detection
- Base wager is static per game

**Required Implementation**:
- Allow game creator to set "Major Week" flag
- Auto-set base wager to 2Q when flagged
- Display indicator that it's a Major round

---

### 14. ACKERLEY'S GAMBIT ⚠️ **MISSING**

**Rule**: When offered a double, team members can disagree. Those who "opt in" cover full bet and keep benefits. Those who "opt out" surrender prior quarters.

**Status**: ❌ NOT IMPLEMENTED
- No double negotiation workflow
- No team split mechanics

**Required Implementation**:
- When double offered, each team member responds individually
- Calculate new stake allocation
- Track partial team participation

---

### 15. THE BIG DICK ⚠️ **MISSING**

**Rule**: Before 18th tee, player with most winnings can risk everything vs rest of group.

**Status**: ❌ NOT IMPLEMENTED
- No pre-hole-18 special betting
- No all-in mechanism

---

### 16. IF AT FIRST YOU DO SUCCEED ⚠️ **MISSING**

**Rule**: If hole result determined on tee box (all OB except one), furthest down selects new partner, 2Q at risk, no further doubling.

**Status**: ❌ NOT IMPLEMENTED
- No mid-hole team reformation
- No special 2Q locked bet

---

### 17. 5-MAN and 6-MAN GAME MODES ⚠️ **NOT SUPPORTED**

**Rule**: Different team structures, Aardvark roles, rotation logic.

**Status**: ❌ NOT IMPLEMENTED
- Only 4-man (2v2 or solo) supported
- No Aardvark position
- No 2v3 or 3v3 team modes
- No dual-captain selection (6-man)

---

### 18. HANDICAP & CREECHER FEATURE ⚠️ **MISSING**

**Rule**:
- Highest 6 handicap holes played at half stroke
- Net handicaps calculated relative to lowest player
- Complex stroke allocation

**Status**: ❌ NOT IMPLEMENTED
- Gross scores only
- No handicap adjustments
- No net score calculation
- No stroke allocation by hole

**Required Implementation**:
- Capture player handicaps at game start
- Calculate net handicaps (all relative to lowest)
- Apply Creecher Feature (6 easiest holes at 0.5 stroke)
- Display both gross and net scores
- Determine winner based on NET scores

---

### 19. FLUSH OUTCOMES ✅ **IMPLEMENTED**

**Rule**: When double rejected, rejecting team wins by default at pre-double wager.

**Status**: ✅ WORKING
- Team 1 Flush, Team 2 Flush
- Captain Flush, Opponents Flush
- Correctly awards quarters

---

### 20. LINE OF SCRIMMAGE ⚠️ **MISSING** (In-Play Rule)

**Rule**: Cannot offer double if past furthest ball OR using info from someone past it.

**Status**: ❌ NOT APPLICABLE TO SCOREKEEPER
- This is an in-play rule for live games
- Scorekeeper records final results retroactively
- Not enforceable in current design (post-hole entry)

**Note**: Would only apply if building real-time shot-by-shot tracking

---

### 21. MANDATORY SOLO REQUIREMENT ⚠️ **PARTIALLY IMPLEMENTED**

**Rule**: 4-man game - each player must go solo at least once before hole 17 (Hoepfinger).

**Status**: ⚠️ TRACKED, NOT ENFORCED
- Visual compliance tracking shows 0/1 or 1/1
- Red warning if not met
- **BUT**: No blocking mechanism
- **BUT**: No validation at hole 16 completion

**Required Implementation**:
- Warn at hole 14-15 if players haven't gone solo
- Consider blocking Hoepfinger entry if requirement not met
- Auto-suggest solo for players behind on requirement

---

### 22. EARLY DEPARTURES ⚠️ **MISSING**

**Rule**: Special quarter distribution if player leaves early.

**Status**: ❌ NOT IMPLEMENTED
- No early departure workflow
- No partial-round completion

---

### 23. RANGE FINDERS & ORDER OF PLAY ⚠️ **MISSING** (In-Play Rules)

**Rule**: Range finder restrictions, match play order, "good but not in".

**Status**: ❌ NOT APPLICABLE
- These are in-play protocol rules
- Scorekeeper is post-hole summary entry

---

## Backend Scoring Logic Analysis

**File**: `backend/app/main.py:1311-1443` (`complete_hole` endpoint)

### What Backend Does Well ✅
1. Calculates quarter deltas correctly for basic winners
2. Supports flush outcomes
3. Handles push (tie) outcomes
4. Stores float_invoked_by and option_invoked_by
5. Allows hole editing (updates existing hole)
6. Maintains hole history properly

### What Backend is Missing ❌
1. **No Karl Marx Rule** - Uses simple division, doesn't allocate odd quarters to Goat
2. **No 3-for-2 calculations** - Duncan, Tunkarri, Tossed Aardvark
3. **No Option multiplier** - Doesn't auto-double wager when captain is Goat
4. **No Float multiplier enforcement** - Doesn't validate float increases wager
5. **No carry-over logic** - Doesn't propagate push to next hole's base wager
6. **No Vinnie's Variation** - Doesn't double holes 13-16
7. **No Hoepfinger rules** - Doesn't apply Joe's Special or rotation selection
8. **No handicap calculations** - Doesn't compute net scores
9. **No validation** - Accepts any team structure, doesn't enforce rules

---

## Recommended Implementation Priority

### Phase 1: Core Game Flow (Critical)
1. ✅ **Captain Rotation Tracking** - Track hitting order, auto-rotate
2. ✅ **The Hoepfinger Phase** - Detect start, enable Goat rotation selection
3. ✅ **Joe's Special** - Goat sets wager, block premature doubles
4. ✅ **The Carry-Over** - Push -> double next hole (max 1 consecutive)
5. ✅ **Vinnie's Variation** - Auto-double holes 13-16

### Phase 2: Betting Mechanics (High Priority)
6. ✅ **The Option (Auto-Double)** - Auto-double when captain is Goat, allow turn-off
7. ✅ **The Duncan** - 3-for-2 solo wins when declared before hit
8. ✅ **Float Enforcement** - Only allow on captain's turn
9. ✅ **The Karl Marx Rule** - Proper odd-quarter allocation to Goat
10. ✅ **Double Points Rounds** - Major championship flag

### Phase 3: Advanced Features (Medium Priority)
11. **The Invisible Aardvark** - Auto-join, tossing for 3-for-2
12. **Mandatory Solo Enforcement** - Warn/block if not met by hole 16
13. **5-Man Game Support** - Aardvark, 2v3 teams, tossing doubles
14. **6-Man Game Support** - Dual Aardvarks, second captain

### Phase 4: Handicap & Scoring (Medium Priority)
15. **Handicap System** - Net handicaps, Creecher Feature
16. **Net Score Display** - Show both gross and net
17. **Stroke Allocation** - Apply strokes per hole

### Phase 5: Edge Cases (Low Priority)
18. **Ackerley's Gambit** - Team member opt-in/out on doubles
19. **The Big Dick** - 18th hole all-in bet
20. **If at First You Do Succeed** - Mid-hole team reformation
21. **The Tunkarri** - 5/6-man Aardvark solo 3-for-2
22. **Early Departure Handling** - Partial round completion

---

## Critical Data Model Additions Needed

### Hole Data Structure
```typescript
{
  hole: number,
  rotation_order: string[],  // NEW: [p1, p2, p3, p4] hitting order
  captain_index: number,      // NEW: Which player is captain (0-3)
  phase: "normal" | "hoepfinger",  // NEW
  teams: { ... },
  wager: number,
  base_wager: number,         // NEW: Before multipliers
  wager_modifiers: {          // NEW
    float: boolean,
    option: boolean,
    duncan: boolean,
    tunkarri: boolean,
    carry_over: boolean,
    vinnies_variation: boolean,
    hoepfinger: boolean,
    major_week: boolean
  },
  winner: string,
  points_delta: {},
  gross_scores: {},
  net_scores: {},             // NEW: After handicaps
  float_invoked_by: string?,
  option_invoked_by: string?,
  duncan_invoked: boolean,    // NEW
  aardvark_tossed: boolean,   // NEW
  ...
}
```

### Game State Structure
```typescript
{
  game_id: string,
  player_count: 4 | 5 | 6,
  base_wager: number,
  is_major_week: boolean,     // NEW
  hoepfinger_start_hole: number,  // NEW: 17 for 4-man, 16 for 5-man, 13 for 6-man
  players: [
    {
      id: string,
      name: string,
      handicap: number,       // NEW
      net_handicap: number,   // NEW: Relative to lowest
      quarters: number,
      solo_count: number,
      float_used: boolean,
      option_triggers: number
    }
  ],
  current_hole: number,
  rotation_order: string[],   // NEW: Current rotation
  hole_history: [ ... ],
  last_push_hole: number?,    // NEW: Track for carry-over blocking
  ...
}
```

---

## Testing Recommendations

### Unit Tests Needed
1. Karl Marx odd-quarter allocation
2. Carry-over propagation (single and blocked consecutive)
3. Vinnie's Variation on holes 13-16
4. Joe's Special wager selection
5. Option auto-detection and doubling
6. Duncan 3-for-2 calculation
7. Rotation order advancement
8. Handicap + Creecher Feature calculations

### Integration Tests Needed
1. Full 18-hole game with all rules active
2. Hoepfinger phase transition
3. Major week double-points round
4. 5-man and 6-man game flows
5. Aardvark tossing scenarios

---

## UI/UX Enhancements Needed

### Pre-Hole Entry Screen
- Show current rotation order with captain highlighted
- Display "Hoepfinger" phase badge if active
- Show Goat indicator (furthest down)
- Show which players still need to go solo
- Option toggle for captain (if they're the Goat)
- Duncan checkbox for captain going solo
- Joe's Special wager selector (Hoepfinger only)

### During Hole Entry
- Disabled double button with tooltip explaining why (if restrictions apply)
- Float button only enabled for current captain
- Visual indicators for active multipliers

### Post-Hole Display
- Show effective wager breakdown (base + all multipliers)
- Display which rules were invoked (badges)
- Show net scores alongside gross scores
- Highlight if carry-over will apply to next hole

---

## Conclusion

The current scorekeeper implements approximately **35-40% of the official Wolf Goat Pig rules**. It handles basic team formation, scoring, and quarter tracking, but is missing:

- **Critical game phase logic** (Captain rotation, Hoepfinger, rotation selection)
- **Advanced betting mechanics** (Duncan, Option auto-double, Karl Marx, carry-over)
- **Special game conditions** (Vinnie's Variation, Joe's Special, Major weeks)
- **Multi-player support** (5-man and 6-man games with Aardvarks)
- **Handicap system** (Net scores, Creecher Feature)

To achieve full compliance, the application needs significant enhancements to both frontend UI logic and backend scoring calculations, with careful attention to the intricate betting conventions that make Wolf Goat Pig unique.

**Recommended Next Step**: Implement Phase 1 items (Captain Rotation, Hoepfinger, Joe's Special, Carry-Over, Vinnie's Variation) as these form the foundation of proper game flow and are prerequisites for more advanced features.
