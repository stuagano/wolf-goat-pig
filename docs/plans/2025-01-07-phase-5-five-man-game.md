# Phase 5: 5-Man Game Completion

## Goal
Complete 5-man game implementation to reach 95%+ coverage for 5-player games

## Current Coverage
- Phase 1-4: 60-65% for 5-man (basic infrastructure only)
- **Phase 5 Target**: 95%+ for 5-man

## High-Priority Tasks

### Task 1: The Aardvark Mechanics
**Rule**: "The 5th player (Aardvark) has special partnership mechanics"

**Backend**:
- Captain can only partner with players #2-4 (not Aardvark)
- Aardvark requests to join teams AFTER Captain forms partnership
- "Toss" mechanism: if rejected, auto-join other team
- When tossed, the team that rejected has doubled risk
- Aardvark can "go it alone" creating 1v1v3 scenario
- Validation: Aardvark is player in position #5

**API Changes**:
```python
# New field in CompleteHoleRequest
aardvark_requested_team: Optional[str] = None  # "team1" or "team2"
aardvark_tossed: Optional[bool] = False
aardvark_solo: Optional[bool] = False

# Validation
- If aardvark_requested_team, verify player is in position 5
- If aardvark_tossed, auto-join other team
- If tossed, double points for team that tossed
```

**Tests**:
```python
def test_aardvark_joins_team():
    # Aardvark requests team1, accepted
    # Verify 3v2 formation

def test_aardvark_tossed():
    # Aardvark requests team1, tossed
    # Verify auto-joins team2
    # Verify team1 risk doubled

def test_aardvark_solo():
    # Aardvark goes solo
    # Verify 1v1v3 formation

def test_captain_cannot_partner_aardvark():
    # Captain tries to partner with #5
    # Verify error
```

**Complexity**: HIGH
**Impact**: HIGH (core 5-man mechanic)

---

### Task 2: Dynamic Rotation Selection (Holes 16-18)
**Rule**: "On holes 16-18, the Goat (lowest score) selects rotation position"

**Backend**:
- New endpoint: `POST /games/{game_id}/select-rotation`
- Identify current Goat (lowest total points)
- Goat selects position 1-5
- Other players fall into relative spots
- Only on holes 16, 17, 18 for 5-man games

**API**:
```python
class RotationSelectionRequest(BaseModel):
    hole_number: int  # 16, 17, or 18
    goat_player_id: str
    selected_position: int  # 1-5

# Endpoint
@app.post("/games/{game_id}/select-rotation")
async def select_rotation(game_id: str, request: RotationSelectionRequest):
    # Validate hole_number in [16, 17, 18]
    # Validate player_count == 5
    # Identify current Goat
    # Set new rotation order
    # Return updated rotation
```

**Tests**:
```python
def test_goat_selects_position_hole_16():
    # Hole 16, Goat selects position 3
    # Verify rotation reordered

def test_non_goat_cannot_select():
    # Non-Goat tries to select
    # Verify error

def test_rotation_selection_5man_only():
    # Try on 4-man game
    # Verify error
```

**Complexity**: MEDIUM
**Impact**: HIGH (5-man specific feature)

---

### Task 3: Hoepfinger Start Hole Adjustment
**Rule**: "Hoepfinger starts on hole 16 for 5-man (not 17)"

**Backend**:
```python
# In Hoepfinger detection logic
def get_hoepfinger_start_hole(player_count):
    if player_count == 4:
        return 17
    elif player_count == 5:
        return 16
    elif player_count == 6:
        return 13
    return 17  # Default to 4-man
```

**Tests**:
```python
def test_hoepfinger_starts_hole_16_5man():
    # 5-man game, hole 16
    # Verify Hoepfinger phase active

def test_hoepfinger_not_on_hole_15_5man():
    # 5-man game, hole 15
    # Verify normal phase
```

**Complexity**: LOW
**Impact**: MEDIUM (correctness for 5-man)

---

### Task 4: Karl Marx Edge Case Fixes
**Rule**: "Fix Hanging Chad and losing team distributions"

**Backend**:
#### 4a. Hanging Chad
```python
# When Karl Marx applies but players tied
if goat_points == non_goat_points:
    game_state["hanging_chad"] = {
        "hole_number": hole_num,
        "team": team_id,
        "pending_amount": remainder,
        "tied_players": [goat_id, non_goat_id]
    }

# On subsequent holes, check if diverged
hanging_chad = game_state.get("hanging_chad")
if hanging_chad:
    player1_points = get_current_points(tied_players[0])
    player2_points = get_current_points(tied_players[1])

    if player1_points != player2_points:
        # Apply deferred distribution
        # Clear hanging_chad
```

#### 4b. Losing Team Distribution Fix
Review and fix the losing team Karl Marx distribution logic.

**Tests**:
```python
def test_hanging_chad_defers_distribution():
    # Two players tied, Karl Marx applies
    # Verify distribution deferred

def test_hanging_chad_applied_when_diverged():
    # Players diverge on next hole
    # Verify deferred distribution applied

def test_karl_marx_losing_team_distribution():
    # 5-man, 2v3, 2-man team loses
    # Verify correct uneven distribution
```

**Complexity**: MEDIUM
**Impact**: MEDIUM (edge case handling)

---

## Implementation Order

1. ✅ Task 3: Hoepfinger Adjustment (LOW complexity, quick win)
2. ✅ Task 1: The Aardvark (HIGH priority, HIGH complexity)
3. ✅ Task 2: Dynamic Rotation Selection (HIGH priority, MEDIUM complexity)
4. ✅ Task 4: Karl Marx Fixes (MEDIUM priority, edge cases)

**Estimated Coverage After Phase 5**: 95%+ for 5-man games

---

## Out of Scope (Future)

- **Ping Pong Rule**: Additional drama when Aardvark tossed multiple times
- **6-Man Game**: Two Aardvarks, even more complexity
- **Frontend UI**: 5-man specific interface elements

---

## Success Criteria

- Aardvark mechanics working (join, toss, solo)
- Rotation selection working on holes 16-18
- Hoepfinger starts correctly on hole 16
- Karl Marx edge cases resolved
- 95%+ test coverage for 5-man games
- 5-man games production-ready

---

**Estimated Time**: 1-2 sessions
**Commits**: ~4-5 commits (one per task)
**Tests**: ~20-25 new tests
