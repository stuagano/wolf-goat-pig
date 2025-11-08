# Phase 3: Final Core Rules Implementation

## Goal
Implement the remaining essential rules to reach 85%+ coverage

## Current Coverage
- Phase 1: 55-60% (rotation, Hoepfinger, carry-over, Vinnie's)
- Phase 2: 70-75% (Option, Duncan, Float)
- **Phase 3 Target**: 85-90%

## Remaining High-Priority Rules

### Task 1: Solo Requirement (4-man only)
**Rule**: "Each player is required to go solo at least once in the first 16 holes"

**Backend**:
- Track `solo_used` count per player
- Validate solo_used on hole submission
- Warning/enforcement before hole 17

**Test**:
```python
def test_solo_requirement_tracked():
    # Track solo usage
    # Verify count increases
```

**Complexity**: Low
**Impact**: High (compliance with core rule)

---

### Task 2: Double Points (Holes 17-18)
**Rule**: Last two holes worth double points

**Backend**:
- Multiply points_delta by 2 for holes 17-18
- No doubling during Hoepfinger (already has Joe's Special)
- Wait - CHECK THIS RULE!

**Test**:
```python
def test_double_points_on_17_and_18():
    # Complete hole 17 with 2Q wager
    # Verify points_delta is 4Q (doubled)
```

**Complexity**: Low
**Impact**: Medium

---

### Task 3: Karl Marx Rule
**Rule**: "Uneven distribution favors player furthest down"

**Backend**:
- When partners win/lose, check if tied for Goat
- Award extra quarter to non-leader
- Handle "hanging chad" (tie postponement)

**Test**:
```python
def test_karl_marx_uneven_split():
    # Two tied Goats on same team
    # One is leader
    # Verify non-leader gets extra Q
```

**Complexity**: Medium
**Impact**: Medium (edge case)

---

### Task 4: Solo Requirement Warning UI
**Frontend**:
- Display solo usage count per player
- Highlight players who haven't gone solo
- Warning indicator before hole 17

**Complexity**: Low
**Impact**: High (user experience)

---

### Task 5: Integration Testing & Final Summary
- Run all tests
- Document final coverage
- Create deployment guide

---

## Out of Scope (Future Phases)

These are complex or rare edge cases:
- **Real-time Doubling** - Complex state machine
- **Aardvark mechanics** (5-man/6-man) - Different game modes
- **The Big Dick** - 18th hole only, complex
- **Ackerley's Gambit** - Partner opt-out, complex
- **Ping Ponging Aardvark** - 5-man game
- **Tossing Invisible Aardvark** - 4-man edge case

---

## Implementation Order

1. ✅ Solo Requirement backend + tests
2. ✅ Double Points backend + tests
3. ✅ Karl Marx Rule backend + tests
4. ✅ Frontend UI updates
5. ✅ Documentation

**Estimated Coverage After Phase 3**: 85-90%

This brings the core 4-man game to production-ready state!
