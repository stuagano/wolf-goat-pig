# 5-Man Game Implementation Status

## Current State Summary

**Status**: 🟡 **PARTIALLY IMPLEMENTED**

The 5-man game has basic infrastructure but is missing several key features specific to 5-player gameplay.

---

## What's Implemented ✅

### Basic 5-Player Support
- ✅ Game creation with `player_count=5`
- ✅ 5 mock players in test mode
- ✅ Basic team formations with 5 players
- ✅ Scorekeeping for 5 players

### Phase 3: Karl Marx Rule (Partial)
- ✅ Karl Marx uneven distribution detection
- ✅ 2v3 team uneven splits (winning team)
- ⚠️ 2v3 team uneven splits (losing team) - **TEST FAILING**
- ⚠️ Hanging Chad logic - **TEST FAILING**

**Test Results**: 2/4 Karl Marx tests passing
- ✅ `test_karl_marx_5man_uneven_win`: Goat wins more ✓
- ✅ `test_karl_marx_not_applied_in_4man`: Correctly excludes 4-man ✓
- ❌ `test_karl_marx_5man_uneven_loss`: Complex edge case failing
- ❌ `test_karl_marx_hanging_chad`: Tie-breaking logic failing

### Phase 4: Validation Works
- ✅ All Phase 4 validation rules work for 5-player games
- ✅ Scorekeeping balance validation (5-man test passing)
- ✅ Team formation validation supports 5 players

---

## What's Missing ❌

### 1. The Aardvark (5th Player Special Role)
**Priority**: HIGH
**Complexity**: MEDIUM-HIGH

The Aardvark is the 5th player in rotation who has special mechanics:

**Not Implemented**:
- ❌ Captain can only partner with players #2-4 (not Aardvark)
- ❌ Aardvark asks to join teams AFTER Captain forms partnership
- ❌ Aardvark can be "tossed" to other team with doubled risk
- ❌ Aardvark can "go it alone" creating 1v1v3 scenario
- ❌ Ping Pong rule (additional drama when Aardvark is tossed)

**Impact**: Cannot properly play 5-man games without this core mechanic

**Implementation Needed**:
```python
# Request model
class AardvarkRequest(BaseModel):
    requesting_player: str  # Aardvark player ID
    target_team: str  # "team1" or "team2"

# Validation
- Verify player is in 5th position
- Verify teams already formed
- Handle "toss" (rejection) -> auto-join other team
- Double points for team that tossed Aardvark
```

### 2. Dynamic Rotation Selection (Holes 16-18)
**Priority**: HIGH
**Complexity**: MEDIUM

In 5-man games, the low point-getter selects rotation position on holes 16, 17, and 18.

**Not Implemented**:
- ❌ Rotation selection on hole 16
- ❌ Recalculation and selection on holes 17-18
- ❌ "Goat" (lowest score) identification
- ❌ Position selection UI/API

**Current Behavior**: Rotation continues normally without selection

**Implementation Needed**:
```python
# For 5-man games only
if player_count == 5 and hole_number in [16, 17, 18]:
    # Find current Goat
    goat = find_lowest_score_player(game_state)

    # Allow Goat to select position
    # Endpoint: POST /games/{game_id}/select-rotation
    {
        "hole_number": 16,
        "goat_player_id": "...",
        "selected_position": 1,  # 1-5
        # Other players fall into relative spots
    }
```

### 3. Hoepfinger Starts on Hole 16 (Not 17)
**Priority**: MEDIUM
**Complexity**: LOW

**Current**: Hoepfinger starts on hole 17 (4-man logic)
**Should Be**: Hoepfinger starts on hole 16 for 5-man games

**Implementation Needed**:
```python
# In Hoepfinger detection
if player_count == 4:
    hoepfinger_start = 17
elif player_count == 5:
    hoepfinger_start = 16
elif player_count == 6:
    hoepfinger_start = 13
```

### 4. Karl Marx Edge Cases
**Priority**: MEDIUM
**Complexity**: MEDIUM

**Failing Tests**:
- ❌ `test_karl_marx_5man_uneven_loss`: Losing team distribution incorrect
- ❌ `test_karl_marx_hanging_chad`: Tie-breaking logic not implemented

**Hanging Chad**: When Karl Marx applies but impacted players have same score, defer distribution until scores diverge.

**Implementation Needed**:
```python
# Hanging Chad detection
if goat_points == non_goat_points:
    # Store pending distribution
    game_state["hanging_chad"] = {
        "hole_number": hole_num,
        "team": team,
        "pending_amount": remainder,
        "tied_players": [goat_id, non_goat_id]
    }

# On subsequent holes, check if tied_players have diverged
# Then apply deferred distribution
```

### 5. Invisible Aardvark (4-Man Only)
**Status**: Not applicable to 5-man
**Note**: 4-man games have "Invisible Aardvark" mechanic, but this doesn't apply to 5-man games

---

## Implementation Priority

### Phase 5 (Recommended): 5-Man Game Completion

**High Priority** (Core Gameplay):
1. ✅ The Aardvark mechanics
   - Aardvark partnership requests
   - Toss mechanism with doubled risk
   - Aardvark going solo (1v1v3)

2. ✅ Dynamic Rotation Selection (holes 16-18)
   - Goat selects position
   - Other players fall into relative spots

3. ✅ Hoepfinger Start Hole Adjustment
   - Start on hole 16 for 5-man

**Medium Priority** (Polish):
4. ✅ Karl Marx Edge Cases
   - Fix losing team distribution
   - Implement Hanging Chad logic

5. ✅ Ping Pong Rule
   - Additional drama when Aardvark tossed multiple times

**Low Priority** (Advanced):
6. ⏭️ Frontend UI for 5-man specific features
   - Aardvark request buttons
   - Rotation selection interface
   - Visual indicators for Aardvark status

---

## Estimated Effort

**Backend Implementation**: ~3-4 tasks
- Task 1: Aardvark mechanics (HIGH complexity)
- Task 2: Dynamic rotation selection (MEDIUM complexity)
- Task 3: Hoepfinger & Karl Marx fixes (LOW-MEDIUM complexity)
- Task 4: Ping Pong rule (LOW complexity)

**Testing**: ~150-200 lines of tests
- Aardvark tests (6-8 tests)
- Rotation selection tests (3-4 tests)
- Karl Marx edge case fixes (2 tests)

**Total Estimated Time**: 1-2 sessions

---

## Rule Coverage Impact

### Current Coverage for 5-Man Games: ~60-65%

**What Works**:
- ✅ Basic gameplay (rotation, teams, scoring)
- ✅ Scorekeeping validation
- ✅ Input validation
- ✅ Karl Marx (partial)
- ✅ Double points (holes 17-18)
- ✅ Pre-hole doubling
- ✅ The Big Dick (hole 18)

**What's Missing**:
- ❌ Aardvark mechanics (~20% coverage)
- ❌ Dynamic rotation selection (~5% coverage)
- ❌ Karl Marx edge cases (~5% coverage)
- ❌ Hoepfinger start hole (~5% coverage)

**After Phase 5**: 95%+ coverage for 5-man games

---

## Compatibility Notes

### Works in 5-Man Games
- ✅ All Phase 4 features (validation, doubling, Big Dick)
- ✅ Basic team formations (2v3, 1v4)
- ✅ Duncan (3-for-2 solo)
- ✅ Float enforcement
- ✅ The Option
- ✅ Double points on holes 17-18

### Doesn't Apply to 5-Man Games
- 🚫 Vinnie's Variation (4-man only)
- 🚫 Solo requirement (4-man only)
- 🚫 Invisible Aardvark (4-man only)

---

## Recommendation

**For Production**:
- ✅ 4-man games are **PRODUCTION READY** (95-98% coverage)
- 🟡 5-man games are **PLAYABLE BUT INCOMPLETE** (60-65% coverage)
- ❌ Missing core Aardvark mechanics make 5-man games less authentic

**Suggested Path Forward**:
1. **Option A**: Deploy with 4-man only, add 5-man in Phase 5
2. **Option B**: Implement Phase 5 (5-man completion) before deployment
3. **Option C**: Deploy with warning that 5-man is "beta" feature

---

## 6-Man Game Status

**Status**: ❌ **NOT IMPLEMENTED**

6-man games require even more complex mechanics:
- 2 Aardvarks (#5 and #6)
- First Aardvark settles before second can act
- Second Captain selection from remaining players
- Hoepfinger starts on hole 13

**Recommendation**: Defer to future phase after 5-man is complete

---

**Last Updated**: January 7, 2025
**Current Phase**: 4 (Complete)
**Next Recommended**: Phase 5 - 5-Man Game Completion
