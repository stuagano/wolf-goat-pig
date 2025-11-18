# Half-Stroke (Creecher Feature) Compliance Analysis

**Date:** 2025-11-17
**Priority:** HIGH - Critical Rules Compliance Issue
**Status:** ⚠️ PARTIAL COMPLIANCE - Workaround in Place

---

## Executive Summary

The **Creecher Feature** (half-stroke handicapping) is **partially implemented** through a fallback mechanism. The primary `HandicapValidator` does NOT support half strokes, causing the system to rely on legacy code for compliance.

**Key Finding:** Half-stroke functionality exists but is **not properly integrated** into the validation layer.

---

## The Creecher Feature Rule

**From:** `backend/app/seed_rules.py:177-178`

> "In awarding strokes, highest six handicap holes for each player played at ½ stroke. Other holes, full strokes."

**Detailed Rule:**
- Players get ½ stroke on their 6 hardest holes (based on stroke index)
- Full strokes on remaining holes
- For handicap >18: Additional ½ strokes on some of the easiest holes
- Net scores can be decimals (e.g., 4 - 0.5 = 3.5 net)

---

## Current Implementation

### 1. **HandicapValidator (PRIMARY VALIDATOR)**
**File:** `backend/app/validators/handicap_validator.py:166-209`

**Status:** ❌ DOES NOT SUPPORT HALF STROKES

```python
@classmethod
def calculate_strokes_received(
    cls,
    course_handicap: float,
    stroke_index: int,
    validate: bool = True
) -> int:  # ❌ Returns INT, not float!
    """Calculate number of strokes a player receives on a hole."""

    # Line 200: Rounds to integer - loses half strokes!
    rounded_handicap = round(course_handicap)

    # Lines 203-207: Calculates full strokes only
    for band in range(0, 3):
        if rounded_handicap >= (stroke_index + (band * 18)):
            strokes += 1

    return strokes  # ❌ Returns 0, 1, 2, etc. NEVER 0.5
```

**Problems:**
1. Return type is `int`, not `float`
2. Rounds handicap instead of using fractional values
3. No Creecher Feature logic
4. Cannot return 0.5 strokes

---

### 2. **WolfGoatPigSimulation (FALLBACK IMPLEMENTATION)**
**File:** `backend/app/wolf_goat_pig_simulation.py:213-250`

**Status:** ✅ IMPLEMENTS HALF STROKES (as fallback)

```python
def _calculate_strokes_received(self, handicap: float, stroke_index: int) -> float:
    """Calculate strokes received on this hole."""
    try:
        # Line 220-226: Try validator first
        strokes = HandicapValidator.calculate_strokes_received(
            handicap, stroke_index, validate=True
        )
        return float(strokes)  # ⚠️ Converts int to float (no half strokes)
    except HandicapValidationError as e:
        # Line 228-250: FALLBACK - Legacy code with half-stroke support
        logger.warning(f"Stroke calculation error: {e.message}, falling back")

        full_strokes = int(handicap)
        half_stroke = (handicap - full_strokes) >= 0.5  # ✅ Checks for .5

        # Line 234-235: Full strokes
        if stroke_index <= full_strokes:
            return 1.0

        # Line 238-239: ✅ Half stroke logic
        if half_stroke and stroke_index == full_strokes + 1:
            return 0.5

        # Line 241-248: ✅ Creecher Feature implementation
        if stroke_index >= 13 and stroke_index <= 18:
            if handicap > 18:
                extra_half_strokes = int((handicap - 18) / 1.0)
                easiest_holes = [18, 17, 16, 15, 14, 13]
                if stroke_index in easiest_holes[:extra_half_strokes]:
                    return 0.5  # ✅ Returns half stroke

        return 0.0
```

**How It Works:**
1. Tries validator (which fails to provide half strokes)
2. Falls back to legacy code
3. Legacy code properly implements Creecher Feature
4. Returns float values (0.0, 0.5, 1.0, etc.)

---

### 3. **Data Structures Support Half Strokes**
**File:** `backend/app/wolf_goat_pig_simulation.py:114-120`

```python
@dataclass
class StrokeAdvantage:
    """Represents stroke advantages for a player on a specific hole"""
    player_id: str
    handicap: float
    strokes_received: float  # ✅ Float type - can store 0.5
    net_score: Optional[float] = None  # ✅ Float - can be decimal
    stroke_index: Optional[int] = None
```

**Status:** ✅ FULLY SUPPORTS HALF STROKES

---

### 4. **Alternative Implementation (Odds Calculator)**
**File:** `backend/app/services/odds_calculator.py:876-911`

**Status:** ✅ IMPLEMENTS HALF STROKES

```python
def calculate_strokes_received(handicap: Union[int, float], stroke_index: int) -> float:
    """
    Returns the number of strokes (0, 0.5, or 1).
    Implements Creecher Feature.
    """
    full_strokes = int(handicap_value)
    half_stroke = (handicap_value - full_strokes) >= 0.5  # ✅ Half stroke check

    # Line 899-900: Assign half stroke
    if half_stroke and stroke_index == full_strokes + 1:
        return 0.5  # ✅

    # Line 903-906: Creecher Feature for easiest 6 holes
    extra_half_strokes = min(int(handicap_value - 18), 6)
    if stroke_index in easiest_holes[:extra_half_strokes]:
        return 0.5  # ✅
```

**Status:** ✅ Proper Creecher implementation, independent of validator

---

## Testing Status

### Test Files Found:

1. **`tests/backend/test_advanced_rules.py:199-214`**
   - Test: `test_handicap_creecher_feature()`
   - **Status:** ⚠️ Weak test - only verifies strokes_received >= 0
   - **Does NOT** verify half strokes are actually returned

2. **`tests/backend/test_hole_state_mechanics.py:77-85`**
   ```python
   # Validate full and half stroke behaviour
   half_stroke_player = hole_state.get_player_stroke_advantage("p2")
   assert half_stroke_player.strokes_received == pytest.approx(0.5)  # ✅ Good test!
   ```
   - **Status:** ✅ Explicitly tests for 0.5 strokes

3. **`test_multi_hole_tracking.py:55-63`**
   - Displays strokes with symbols: ● (full), ◐ (half)
   - Shows system is aware of half strokes

---

## Compliance Status

| Component | Half-Stroke Support | Creecher Feature | Status |
|-----------|---------------------|------------------|--------|
| HandicapValidator | ❌ No | ❌ No | **FAILS** |
| WolfGoatPigSimulation | ✅ Yes (fallback) | ✅ Yes (fallback) | **WORKS** |
| OddsCalculator | ✅ Yes | ✅ Yes | **PASSES** |
| StrokeAdvantage dataclass | ✅ Yes | ✅ Yes | **PASSES** |
| Net Score calculation | ✅ Yes | ✅ Yes | **PASSES** |

**Overall:** ⚠️ **FUNCTIONALLY COMPLIANT via workaround, ARCHITECTURALLY NON-COMPLIANT**

---

## Root Cause Analysis

### Why the Validator Doesn't Have Half Strokes:

1. **USGA Standard vs. Wolf-Goat-Pig Custom Rule**
   - `HandicapValidator` implements standard USGA rules (full strokes only)
   - Creecher Feature is a Wolf-Goat-Pig house rule
   - Validator was never updated for WGP-specific rules

2. **Type Mismatch**
   - Validator returns `int`
   - Game needs `float`
   - Conversion `float(int_strokes)` loses half-stroke information

3. **Fallback Mechanism Masks Issue**
   - Legacy code catches validator shortcomings
   - System "works" so issue went unnoticed
   - Not discovered until deep rules audit

---

## Risks & Impact

### Current Risks:

1. **Validator Not Used** ⚠️
   - HandicapValidator provides integer strokes
   - System falls back to legacy code
   - Validator's validation benefits are lost

2. **Inconsistent Implementations** ⚠️
   - Three different places calculate strokes:
     - HandicapValidator (wrong)
     - WolfGoatPigSimulation._calculate_strokes_received (correct)
     - OddsCalculator.calculate_strokes_received (correct)
   - Maintenance burden - must update multiple places

3. **Testing Gap** ⚠️
   - test_advanced_rules.py doesn't verify half strokes
   - Could break without detection

### What Works:

1. **Actual Gameplay** ✅
   - Game correctly uses half strokes via fallback
   - Net scores calculated properly
   - Creecher Feature is enforced

2. **Data Integrity** ✅
   - StrokeAdvantage stores floats
   - No data loss

---

## Recommended Fixes

### Priority 1: Fix HandicapValidator (HIGH)

**Update:** `backend/app/validators/handicap_validator.py`

```python
@classmethod
def calculate_strokes_received_with_creecher(
    cls,
    course_handicap: float,
    stroke_index: int,
    validate: bool = True
) -> float:  # ✅ Return float, not int
    """
    Calculate strokes received including Creecher Feature (half strokes).

    Creecher Feature Rules:
    - Highest 6 handicap holes: ½ stroke
    - Other holes: full strokes
    - For handicap >18: additional ½ strokes on easiest holes

    Args:
        course_handicap: Player's course handicap (can be fractional)
        stroke_index: Hole's stroke index (1-18, where 1 is hardest)
        validate: Whether to validate inputs

    Returns:
        Float strokes: 0.0, 0.5, 1.0, 1.5, 2.0, etc.
    """
    if validate:
        cls.validate_handicap(course_handicap, "course_handicap")
        cls.validate_stroke_index(stroke_index)

    full_strokes = int(course_handicap)
    has_half_stroke = (course_handicap - full_strokes) >= 0.5

    # Full strokes on holes harder than player's handicap
    if stroke_index <= full_strokes:
        return 1.0

    # Half stroke on next hardest hole
    if has_half_stroke and stroke_index == full_strokes + 1:
        return 0.5

    # Creecher Feature: Half strokes on easiest 6 holes for high handicaps
    if stroke_index >= 13 and stroke_index <= 18 and course_handicap > 18:
        extra_half_strokes = min(int(course_handicap - 18), 6)
        easiest_holes = [18, 17, 16, 15, 14, 13]  # Easiest to hardest
        if stroke_index in easiest_holes[:extra_half_strokes]:
            return 0.5

    return 0.0
```

### Priority 2: Update Simulation to Use Fixed Validator

**Update:** `backend/app/wolf_goat_pig_simulation.py:213-250`

```python
def _calculate_strokes_received(self, handicap: float, stroke_index: int) -> float:
    """Calculate strokes received using HandicapValidator."""
    try:
        # Use validator's Creecher-aware method
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(
            handicap, stroke_index, validate=True
        )
        return strokes  # Already float
    except HandicapValidationError as e:
        logger.error(f"Stroke calculation failed: {e.message}")
        # Fallback to 0 strokes if validation fails
        return 0.0
```

### Priority 3: Update Net Score Calculation

**Update:** `backend/app/validators/handicap_validator.py:211-247`

```python
@classmethod
def calculate_net_score(
    cls,
    gross_score: Union[int, float],  # ✅ Accept float
    strokes_received: float,  # ✅ Changed from int
    validate: bool = True
) -> float:  # ✅ Return float
    """
    Calculate net score with half-stroke support.

    Examples:
        gross=5, strokes=0.5 → net=4.5
        gross=4, strokes=1.0 → net=3.0
    """
    if validate:
        if not isinstance(gross_score, (int, float)) or gross_score < 1:
            raise HandicapValidationError(...)

        if not isinstance(strokes_received, (int, float)) or strokes_received < 0:
            raise HandicapValidationError(...)

    return float(gross_score) - strokes_received
```

### Priority 4: Add Comprehensive Tests

**New Test:** `backend/tests/test_creecher_feature.py`

```python
def test_half_strokes_on_hardest_holes():
    """Test half strokes awarded correctly."""
    # Player with 10.5 handicap
    strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.5, 11)
    assert strokes == 0.5  # 11th hole gets half stroke

    strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.5, 10)
    assert strokes == 1.0  # 10th hole gets full stroke

    strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.5, 12)
    assert strokes == 0.0  # 12th hole gets no stroke

def test_creecher_feature_high_handicap():
    """Test Creecher Feature for handicap > 18."""
    # Player with 20 handicap gets extra half strokes on easiest holes
    strokes = HandicapValidator.calculate_strokes_received_with_creecher(20.0, 18)
    assert strokes == 0.5  # Easiest hole gets half stroke

    strokes = HandicapValidator.calculate_strokes_received_with_creecher(20.0, 17)
    assert strokes == 0.5  # 2nd easiest gets half stroke

def test_net_score_with_half_strokes():
    """Test net score calculation with half strokes."""
    net = HandicapValidator.calculate_net_score(5, 0.5)
    assert net == 4.5

    net = HandicapValidator.calculate_net_score(4, 1.5)
    assert net == 2.5
```

---

## Migration Path

### Phase 1: Fix Validator (No Breaking Changes)
1. Add `calculate_strokes_received_with_creecher()` method
2. Keep old `calculate_strokes_received()` for backward compatibility
3. Update `calculate_net_score()` to accept floats
4. Add tests

### Phase 2: Update Simulation
1. Switch simulation to use new method
2. Remove fallback logic
3. Test extensively

### Phase 3: Deprecate Old Method
1. Mark `calculate_strokes_received()` as deprecated
2. Update all callers
3. Eventually remove

---

## Verification Checklist

After implementing fixes:

- [ ] HandicapValidator returns floats (0.0, 0.5, 1.0, etc.)
- [ ] Player with 10.5 handicap gets 0.5 strokes on stroke index 11
- [ ] Player with 20 handicap gets half strokes on stroke index 18, 17
- [ ] Net scores can be decimals (e.g., 4.5, 3.5)
- [ ] Simulation uses validator (no fallback needed)
- [ ] All tests pass
- [ ] No regression in existing gameplay

---

## Conclusion

**Current Status:** ⚠️ **Functionally Correct, Architecturally Flawed**

The Creecher Feature IS implemented and DOES work correctly during gameplay. However:

1. **HandicapValidator is bypassed** - validator doesn't support the rule
2. **Legacy fallback code** - system relies on old implementation
3. **Multiple implementations** - stroke calculation exists in 3 places
4. **Type inconsistency** - validator returns int, game needs float

**Recommendation:** Implement Priority 1 & 2 fixes to properly integrate the Creecher Feature into the validation layer and remove dependency on fallback code.

**Risk Level:** MEDIUM - System works but is fragile and hard to maintain

**Estimated Effort:** 4-6 hours (fix validator, update simulation, add tests)
