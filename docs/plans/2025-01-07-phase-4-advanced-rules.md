# Phase 4: Advanced Rules & Polish

## Goal
Implement remaining advanced rules to reach 95%+ coverage and production polish

## Current Coverage
- Phase 1: 55-60% (rotation, Hoepfinger, carry-over, Vinnie's)
- Phase 2: 70-75% (Option, Duncan, Float)
- Phase 3: 85-90% (Solo requirement, Double Points, Karl Marx)
- **Phase 4 Target**: 95-98%

## High-Priority Rules

### Task 1: Scorekeeping Validation & Balance Checks
**Rule**: "Points on each hole should always balance to zero"

**Backend**:
- Add validation after points calculation
- Ensure sum of all points_delta == 0
- Return warning if imbalance detected
- Log discrepancies for debugging

**Test**:
```python
def test_points_balance_on_every_hole():
    # Complete a hole
    # Verify sum(points_delta.values()) == 0
```

**Complexity**: Low
**Impact**: High (data integrity)

---

### Task 2: Line of Scrimmage & Balls-in-Hole Restrictions
**Rule**: "No double can be offered after the line of scrimmage or when balls are in hole"

**Backend**:
- Track "line_of_scrimmage_passed" state
- Track "balls_in_hole" state
- Validate double offers against these restrictions
- Return 400 if restrictions violated

**Frontend**:
- Disable double buttons when restrictions active
- Show visual indicator for line of scrimmage
- Show "balls in hole" status

**Test**:
```python
def test_cannot_double_after_line_of_scrimmage():
    # Set line_of_scrimmage_passed = True
    # Attempt to offer double
    # Verify 400 error
```

**Complexity**: Medium
**Impact**: Medium (edge case enforcement)

---

### Task 3: The Big Dick (18th Hole Special)
**Rule**: "On the 18th hole, any player can challenge to go solo against the field"

**Backend**:
- Allow any player (not just captain) to declare Big Dick on hole 18
- 1 vs all remaining players
- Special payout mechanics
- Only available on hole 18

**Frontend**:
- "Big Dick" button on hole 18
- Player selection for who declares
- Special UI indicator

**Test**:
```python
def test_big_dick_on_hole_18():
    # Play to hole 18
    # Any player can declare Big Dick
    # Verify 1 vs 3 teams formed
```

**Complexity**: Medium
**Impact**: Medium (special 18th hole mechanic)

---

### Task 4: Real-time Doubling (Simplified)
**Rule**: "Players can offer doubles during play"

**Implementation** (Simplified for Phase 4):
- Allow doubles to be offered BEFORE hole starts
- Pre-hole double offer/accept/decline flow
- Track double history
- Calculate final wager with all doubles applied

**Deferred** (Future Phase):
- Mid-hole doubling (requires real-time state)
- Complex line of scrimmage tracking during play
- Balls-in-hole mid-round tracking

**Test**:
```python
def test_pre_hole_double_offer():
    # Offer double before hole starts
    # Accept/decline
    # Verify wager multiplied
```

**Complexity**: Low (pre-hole only)
**Impact**: High (common feature)

---

### Task 5: Enhanced Error Handling & Validation
**Features**:
- Validate all team formations before hole completion
- Check for duplicate players on teams
- Verify captain is in rotation order
- Validate scores are reasonable (e.g., not negative)
- Better error messages

**Complexity**: Low
**Impact**: High (production stability)

---

## Out of Scope (Future Phases)

These remain complex or rare:
- **Mid-hole Real-time Doubling** - Requires WebSocket/real-time state
- **Aardvark mechanics** (5-man/6-man) - Different game modes
- **Ackerley's Gambit** - Partner opt-out, complex
- **Advanced Karl Marx** - Hanging chad edge cases

---

## Implementation Order

1. ✅ Scorekeeping Validation (data integrity)
2. ✅ Enhanced Error Handling (stability)
3. ✅ Pre-hole Doubling (common feature)
4. ✅ Line of Scrimmage Restrictions (edge case)
5. ✅ The Big Dick (special 18th hole)

**Estimated Coverage After Phase 4**: 95-98%

This brings the 4-man game to feature-complete production state!

---

## Success Criteria

- All holes validate to zero balance
- Robust error handling for invalid inputs
- Pre-hole doubling works smoothly
- Line of scrimmage enforced
- The Big Dick available on hole 18
- 95%+ rule coverage
- Production-ready stability
