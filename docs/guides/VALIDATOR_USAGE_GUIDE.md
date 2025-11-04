# Wolf Goat Pig Validator Usage Guide

**Version:** 1.0
**Last Updated:** 2025-11-03

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [HandicapValidator Guide](#handicapvalidator-guide)
4. [BettingValidator Guide](#bettingvalidator-guide)
5. [GameStateValidator Guide](#gamestatevalidator-guide)
6. [Error Handling](#error-handling)
7. [Integration Patterns](#integration-patterns)
8. [Testing with Validators](#testing-with-validators)
9. [Best Practices](#best-practices)

---

## Overview

### What Are Validators?

Validators are specialized classes that enforce Wolf Goat Pig game rules and ensure data integrity throughout the application. They provide:

- **Centralized validation logic** - Single source of truth for business rules
- **USGA compliance** - Handicap calculations follow official standards
- **Defensive programming** - Catch invalid states before they cause problems
- **Clear error messages** - Descriptive errors with context for debugging
- **Type safety** - Validate data types and ranges

### Why Do Validators Exist?

Before validators, validation logic was scattered across multiple classes:
- Player models validated their own data
- Service classes had duplicated validation
- Game state checks were inconsistent
- Error messages varied in quality

Validators solve these problems by:
- **Consolidating rules** - All validation in one place
- **Eliminating duplication** - DRY principle enforcement
- **Improving testability** - Easy to test validation logic in isolation
- **Enhancing maintainability** - Update rules in one location

### Available Validators

| Validator | Purpose | Key Features |
|-----------|---------|--------------|
| **HandicapValidator** | USGA handicap compliance | Handicap ranges, stroke allocation, net scores |
| **BettingValidator** | Wolf Goat Pig betting rules | Doubles, Duncan, carry-overs, wager calculations |
| **GameStateValidator** | Game flow and transitions | Phase validation, player actions, partnerships |

---

## Quick Start

### Installation

Validators are included in the backend app. Import from the validators package:

```python
from app.validators import (
    HandicapValidator,
    BettingValidator,
    GameStateValidator,
    ValidationError,
    HandicapValidationError,
    BettingValidationError,
    GameStateValidationError
)
```

### Basic Usage Example

```python
from app.validators import HandicapValidator, HandicapValidationError

try:
    # Validate a player's handicap
    HandicapValidator.validate_handicap(12.5)

    # Calculate strokes received on a hole
    strokes = HandicapValidator.calculate_strokes_received(
        course_handicap=15.0,
        stroke_index=8
    )
    print(f"Player receives {strokes} strokes on this hole")

except HandicapValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Field: {e.field}")
    print(f"Details: {e.details}")
```

### Common Pattern

All validators follow this pattern:

1. **Static methods** - Use class methods, no instantiation needed
2. **Explicit validation** - Methods clearly indicate what they validate
3. **Specific exceptions** - Raise domain-specific validation errors
4. **Rich error context** - Errors include field names and details

---

## HandicapValidator Guide

### Overview

`HandicapValidator` ensures all handicap-related calculations comply with USGA rules. It validates handicap ranges, stroke allocation, net scores, and course handicap calculations.

### Constants

```python
HandicapValidator.MIN_HANDICAP = 0.0
HandicapValidator.MAX_HANDICAP = 54.0
HandicapValidator.MIN_STROKE_INDEX = 1
HandicapValidator.MAX_STROKE_INDEX = 18
```

### Methods Reference

#### validate_handicap()

Validates a handicap is within USGA range (0-54).

**Signature:**
```python
@classmethod
def validate_handicap(
    cls,
    handicap: float,
    field_name: str = "handicap"
) -> None
```

**Example:**
```python
from app.validators import HandicapValidator, HandicapValidationError

# Valid handicap
try:
    HandicapValidator.validate_handicap(15.5)
    print("Handicap is valid")
except HandicapValidationError as e:
    print(f"Error: {e.message}")

# Invalid handicap - too high
try:
    HandicapValidator.validate_handicap(60.0)
except HandicapValidationError as e:
    print(f"Error: {e.message}")  # "handicap cannot exceed 54.0"
    print(f"Details: {e.details}")  # {'value': 60.0, 'max': 54.0}

# Invalid handicap - wrong type
try:
    HandicapValidator.validate_handicap("12")
except HandicapValidationError as e:
    print(f"Error: {e.message}")  # "handicap must be a number"
```

**Raises:**
- `HandicapValidationError` if handicap is not a number
- `HandicapValidationError` if handicap < 0.0 or > 54.0

---

#### validate_stroke_index()

Validates stroke index (handicap allocation per hole) is between 1-18.

**Signature:**
```python
@classmethod
def validate_stroke_index(
    cls,
    stroke_index: int,
    field_name: str = "stroke_index"
) -> None
```

**Example:**
```python
# Valid stroke index
HandicapValidator.validate_stroke_index(8)

# Invalid - out of range
try:
    HandicapValidator.validate_stroke_index(19)
except HandicapValidationError as e:
    print(e.message)  # "stroke_index must be between 1 and 18"

# Invalid - not an integer
try:
    HandicapValidator.validate_stroke_index(8.5)
except HandicapValidationError as e:
    print(e.message)  # "stroke_index must be an integer"
```

---

#### calculate_strokes_received()

Calculates number of strokes a player receives on a hole using USGA rules.

**USGA Stroke Allocation Rules:**
- If course handicap >= stroke index, player gets 1 stroke
- If course handicap >= (stroke index + 18), player gets 2 strokes
- If course handicap >= (stroke index + 36), player gets 3 strokes

**Signature:**
```python
@classmethod
def calculate_strokes_received(
    cls,
    course_handicap: float,
    stroke_index: int,
    validate: bool = True
) -> int
```

**Example:**
```python
# Player with 15 handicap on stroke index 8 hole
strokes = HandicapValidator.calculate_strokes_received(
    course_handicap=15.0,
    stroke_index=8
)
print(strokes)  # 1 (because 15 >= 8)

# Player with 25 handicap on stroke index 5 hole
strokes = HandicapValidator.calculate_strokes_received(
    course_handicap=25.0,
    stroke_index=5
)
print(strokes)  # 2 (because 25 >= 5 and 25 >= 5+18)

# Skip validation for performance (only if already validated)
strokes = HandicapValidator.calculate_strokes_received(
    course_handicap=10.0,
    stroke_index=12,
    validate=False
)
```

**Returns:** Integer number of strokes (0, 1, 2, or 3)

---

#### calculate_net_score()

Calculates net score from gross score and strokes received.

**Signature:**
```python
@classmethod
def calculate_net_score(
    cls,
    gross_score: int,
    strokes_received: int,
    validate: bool = True
) -> int
```

**Example:**
```python
# Player shoots 5 on a par 4, receives 1 stroke
net_score = HandicapValidator.calculate_net_score(
    gross_score=5,
    strokes_received=1
)
print(net_score)  # 4

# Player shoots 6, receives 2 strokes
net_score = HandicapValidator.calculate_net_score(
    gross_score=6,
    strokes_received=2
)
print(net_score)  # 4

# Invalid gross score
try:
    HandicapValidator.calculate_net_score(
        gross_score=0,
        strokes_received=1
    )
except HandicapValidationError as e:
    print(e.message)  # "Gross score must be a positive integer"
```

---

#### validate_course_rating()

Validates course rating and slope rating meet USGA standards.

**USGA Standards:**
- Course rating: 60.0 - 85.0 (typically 67-77)
- Slope rating: 55 - 155 (113 is average difficulty)

**Signature:**
```python
@classmethod
def validate_course_rating(
    cls,
    course_rating: float,
    slope_rating: int
) -> None
```

**Example:**
```python
# Valid course ratings
HandicapValidator.validate_course_rating(
    course_rating=71.5,
    slope_rating=130
)

# Invalid slope rating
try:
    HandicapValidator.validate_course_rating(
        course_rating=72.0,
        slope_rating=200  # Too high
    )
except HandicapValidationError as e:
    print(e.message)  # "Slope rating must be between 55 and 155"
```

---

#### calculate_course_handicap()

Calculates course handicap from handicap index using official USGA formula.

**USGA Formula:**
```
Course Handicap = (Handicap Index × Slope Rating / 113) + (Course Rating - Par)
```

**Signature:**
```python
@classmethod
def calculate_course_handicap(
    cls,
    handicap_index: float,
    slope_rating: int,
    course_rating: float,
    par: int,
    validate: bool = True
) -> int
```

**Example:**
```python
# Calculate course handicap for a player
course_handicap = HandicapValidator.calculate_course_handicap(
    handicap_index=15.0,
    slope_rating=130,
    course_rating=71.5,
    par=72
)
print(course_handicap)  # 17 (rounded from 16.7)

# Easier course (slope 113, average)
course_handicap = HandicapValidator.calculate_course_handicap(
    handicap_index=15.0,
    slope_rating=113,
    course_rating=72.0,
    par=72
)
print(course_handicap)  # 15 (handicap index = course handicap)

# Invalid par
try:
    HandicapValidator.calculate_course_handicap(
        handicap_index=15.0,
        slope_rating=130,
        course_rating=71.5,
        par=100  # Unrealistic
    )
except HandicapValidationError as e:
    print(e.message)  # "Par must be between 54 and 90"
```

---

#### validate_stroke_allocation()

Validates stroke allocation for all players on all holes.

**Signature:**
```python
@classmethod
def validate_stroke_allocation(
    cls,
    players_handicaps: List[float],
    hole_stroke_indexes: List[int]
) -> None
```

**Example:**
```python
# Valid stroke allocation
players = [10.5, 15.0, 8.0, 20.0]
holes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

HandicapValidator.validate_stroke_allocation(
    players_handicaps=players,
    hole_stroke_indexes=holes
)

# Invalid - missing stroke indexes
try:
    HandicapValidator.validate_stroke_allocation(
        players_handicaps=players,
        hole_stroke_indexes=[1, 2, 3, 4, 5, 6, 7, 8, 9]  # Only 9 holes
    )
except HandicapValidationError as e:
    print(e.message)  # "Must have stroke indexes for all 18 holes"

# Invalid - duplicate stroke indexes
try:
    holes_with_dupe = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 17]
    HandicapValidator.validate_stroke_allocation(
        players_handicaps=players,
        hole_stroke_indexes=holes_with_dupe
    )
except HandicapValidationError as e:
    print(e.message)  # "Stroke indexes must be unique values 1-18"
    print(e.details)  # {'missing': [18], 'duplicates': [17]}
```

---

#### get_handicap_category()

Categorizes handicap into skill level.

**Categories:**
- SCRATCH: 0-5
- LOW: 6-12
- MID: 13-20
- HIGH: 21-30
- BEGINNER: 31+

**Signature:**
```python
@classmethod
def get_handicap_category(cls, handicap: float) -> str
```

**Example:**
```python
category = HandicapValidator.get_handicap_category(3.5)
print(category)  # "SCRATCH"

category = HandicapValidator.get_handicap_category(15.0)
print(category)  # "MID"

category = HandicapValidator.get_handicap_category(35.0)
print(category)  # "BEGINNER"
```

---

#### validate_team_handicaps()

Validates team handicaps are balanced and fair.

**Signature:**
```python
@classmethod
def validate_team_handicaps(
    cls,
    team1_handicaps: List[float],
    team2_handicaps: List[float],
    max_difference: float = 10.0
) -> Dict[str, Any]
```

**Example:**
```python
# Balanced teams
team1 = [10.0, 15.0]
team2 = [12.0, 14.0]

result = HandicapValidator.validate_team_handicaps(team1, team2)
print(result)
# {
#     'valid': True,
#     'team1_average': 12.5,
#     'team2_average': 13.0,
#     'difference': 0.5,
#     'balanced': True
# }

# Unbalanced teams
team1 = [5.0, 8.0]
team2 = [20.0, 25.0]

try:
    result = HandicapValidator.validate_team_handicaps(team1, team2)
except HandicapValidationError as e:
    print(e.message)  # "Team handicaps too unbalanced (difference: 16.0)"
    print(e.details)
    # {
    #     'team1_average': 6.5,
    #     'team2_average': 22.5,
    #     'difference': 16.0,
    #     'max_allowed': 10.0
    # }

# Allow larger difference
result = HandicapValidator.validate_team_handicaps(
    team1,
    team2,
    max_difference=20.0
)
print(result['valid'])  # True
```

### Common Use Cases

#### Use Case 1: Validate Player Handicap on Registration

```python
def register_player(name: str, handicap: float):
    try:
        HandicapValidator.validate_handicap(handicap)
        category = HandicapValidator.get_handicap_category(handicap)

        return {
            "name": name,
            "handicap": handicap,
            "category": category,
            "status": "registered"
        }
    except HandicapValidationError as e:
        return {
            "error": e.message,
            "field": e.field,
            "details": e.details
        }
```

#### Use Case 2: Calculate Hole Strokes for All Players

```python
def calculate_hole_strokes(players: List[Dict], stroke_index: int):
    results = []

    for player in players:
        try:
            strokes = HandicapValidator.calculate_strokes_received(
                course_handicap=player['course_handicap'],
                stroke_index=stroke_index
            )

            results.append({
                "player_id": player['id'],
                "strokes_received": strokes
            })
        except HandicapValidationError as e:
            results.append({
                "player_id": player['id'],
                "error": e.message
            })

    return results
```

#### Use Case 3: Complete Handicap Pipeline

```python
def setup_player_for_round(
    handicap_index: float,
    course_rating: float,
    slope_rating: int,
    par: int
):
    """Complete handicap setup for a round."""
    try:
        # Step 1: Validate handicap index
        HandicapValidator.validate_handicap(handicap_index)

        # Step 2: Validate course
        HandicapValidator.validate_course_rating(course_rating, slope_rating)

        # Step 3: Calculate course handicap
        course_handicap = HandicapValidator.calculate_course_handicap(
            handicap_index=handicap_index,
            slope_rating=slope_rating,
            course_rating=course_rating,
            par=par
        )

        # Step 4: Get category
        category = HandicapValidator.get_handicap_category(handicap_index)

        return {
            "handicap_index": handicap_index,
            "course_handicap": course_handicap,
            "category": category,
            "ready": True
        }

    except HandicapValidationError as e:
        return {
            "error": e.message,
            "field": e.field,
            "details": e.details,
            "ready": False
        }
```

---

## BettingValidator Guide

### Overview

`BettingValidator` enforces Wolf Goat Pig betting rules including doubles, Duncan, carry-overs, and wager calculations.

### Methods Reference

#### validate_base_wager()

Validates base wager amount is valid.

**Signature:**
```python
@classmethod
def validate_base_wager(cls, base_wager: int) -> None
```

**Example:**
```python
from app.validators import BettingValidator, BettingValidationError

# Valid wager (in quarters)
BettingValidator.validate_base_wager(4)  # $1.00

# Invalid - not positive
try:
    BettingValidator.validate_base_wager(0)
except BettingValidationError as e:
    print(e.message)  # "Base wager must be positive"

# Invalid - not an integer
try:
    BettingValidator.validate_base_wager(2.5)
except BettingValidationError as e:
    print(e.message)  # "Base wager must be an integer"
```

---

#### validate_double()

Validates a double action is allowed according to Wolf Goat Pig rules.

**Double Rules:**
- Hole cannot already be doubled
- Wagering window must still be open
- Partnership must be formed first

**Signature:**
```python
@classmethod
def validate_double(
    cls,
    already_doubled: bool,
    wagering_closed: bool,
    partnership_formed: bool
) -> None
```

**Example:**
```python
# Valid double
BettingValidator.validate_double(
    already_doubled=False,
    wagering_closed=False,
    partnership_formed=True
)

# Invalid - already doubled
try:
    BettingValidator.validate_double(
        already_doubled=True,
        wagering_closed=False,
        partnership_formed=True
    )
except BettingValidationError as e:
    print(e.message)  # "Hole has already been doubled"

# Invalid - wagering closed
try:
    BettingValidator.validate_double(
        already_doubled=False,
        wagering_closed=True,
        partnership_formed=True
    )
except BettingValidationError as e:
    print(e.message)  # "Wagering is closed for this hole"

# Invalid - no partnership
try:
    BettingValidator.validate_double(
        already_doubled=False,
        wagering_closed=False,
        partnership_formed=False
    )
except BettingValidationError as e:
    print(e.message)  # "Partnership must be formed before doubling"
```

---

#### validate_duncan()

Validates "The Duncan" (captain goes solo) is allowed.

**Duncan Rules:**
- Only the captain can invoke Duncan
- Cannot invoke after partnership is formed
- Cannot invoke after tee shots are complete

**Signature:**
```python
@classmethod
def validate_duncan(
    cls,
    is_captain: bool,
    partnership_formed: bool,
    tee_shots_complete: bool
) -> None
```

**Example:**
```python
# Valid Duncan
BettingValidator.validate_duncan(
    is_captain=True,
    partnership_formed=False,
    tee_shots_complete=False
)

# Invalid - not captain
try:
    BettingValidator.validate_duncan(
        is_captain=False,
        partnership_formed=False,
        tee_shots_complete=False
    )
except BettingValidationError as e:
    print(e.message)  # "Only the captain can invoke The Duncan"

# Invalid - partnership already formed
try:
    BettingValidator.validate_duncan(
        is_captain=True,
        partnership_formed=True,
        tee_shots_complete=False
    )
except BettingValidationError as e:
    print(e.message)  # "Cannot invoke The Duncan after partnership formed"

# Invalid - tee shots complete
try:
    BettingValidator.validate_duncan(
        is_captain=True,
        partnership_formed=False,
        tee_shots_complete=True
    )
except BettingValidationError as e:
    print(e.message)  # "Cannot invoke The Duncan after tee shots complete"
```

---

#### validate_carry_over()

Validates carry over is allowed.

**Carry Over Rules:**
- Cannot carry over on first hole
- Previous hole must have been tied

**Signature:**
```python
@classmethod
def validate_carry_over(
    cls,
    hole_number: int,
    previous_hole_tied: bool
) -> None
```

**Example:**
```python
# Valid carry over
BettingValidator.validate_carry_over(
    hole_number=5,
    previous_hole_tied=True
)

# Invalid - first hole
try:
    BettingValidator.validate_carry_over(
        hole_number=1,
        previous_hole_tied=True
    )
except BettingValidationError as e:
    print(e.message)  # "Cannot carry over on first hole"

# Invalid - previous hole not tied
try:
    BettingValidator.validate_carry_over(
        hole_number=3,
        previous_hole_tied=False
    )
except BettingValidationError as e:
    print(e.message)  # "Previous hole must have been tied to carry over"
```

---

#### calculate_wager_multiplier()

Calculates wager multiplier based on betting modifiers.

**Multiplier Rules:**
- Base multiplier: 1x
- Doubled: 2x
- Carry over: 2x
- Duncan: 2x
- All stack multiplicatively

**Signature:**
```python
@classmethod
def calculate_wager_multiplier(
    cls,
    doubled: bool = False,
    carry_over: bool = False,
    duncan: bool = False
) -> int
```

**Example:**
```python
# No modifiers
multiplier = BettingValidator.calculate_wager_multiplier()
print(multiplier)  # 1

# Just doubled
multiplier = BettingValidator.calculate_wager_multiplier(doubled=True)
print(multiplier)  # 2

# Doubled + carry over
multiplier = BettingValidator.calculate_wager_multiplier(
    doubled=True,
    carry_over=True
)
print(multiplier)  # 4 (2 × 2)

# All modifiers (rare but possible)
multiplier = BettingValidator.calculate_wager_multiplier(
    doubled=True,
    carry_over=True,
    duncan=True
)
print(multiplier)  # 8 (2 × 2 × 2)
```

---

#### calculate_total_wager()

Calculates total wager amount.

**Signature:**
```python
@classmethod
def calculate_total_wager(
    cls,
    base_wager: int,
    multiplier: int
) -> int
```

**Example:**
```python
# Simple wager
total = BettingValidator.calculate_total_wager(
    base_wager=4,  # $1.00 (4 quarters)
    multiplier=1
)
print(total)  # 4 quarters = $1.00

# Doubled wager
total = BettingValidator.calculate_total_wager(
    base_wager=4,
    multiplier=2
)
print(total)  # 8 quarters = $2.00

# Complex wager (doubled + carry over)
total = BettingValidator.calculate_total_wager(
    base_wager=4,
    multiplier=4
)
print(total)  # 16 quarters = $4.00
```

### Wolf Goat Pig Betting Rules Explained

#### The Basics

1. **Base Wager**: Set at game start (typically $0.25 to $1.00)
2. **Team Formation**: Captain chooses partner after tee shots
3. **Team vs. Other 3**: Partnership plays against other three players

#### Special Betting Actions

| Action | Effect | Rules |
|--------|--------|-------|
| **Double** | 2x wager | After partnership formed, before wagering closes |
| **The Duncan** | Captain goes solo (2x) | Before partnership formed, captain only |
| **Carry Over** | 2x wager | Previous hole tied, carries to next hole |

#### Multiplier Stacking

Multipliers stack multiplicatively:

```
Base: $1.00
Doubled: $2.00 (2x)
Doubled + Carry Over: $4.00 (2x × 2x)
Doubled + Carry Over + Duncan: $8.00 (2x × 2x × 2x)
```

#### Wagering Window

```
Hole Start
    ↓
Tee Shots Complete ← Captain can invoke Duncan before this
    ↓
Partnership Formed ← Wagering window opens
    ↓
First Approach Shot ← Wagering window closes
    ↓
Hole Complete
```

### Common Use Cases

#### Use Case 1: Handle Double Request

```python
def handle_double_request(hole_state: Dict):
    try:
        BettingValidator.validate_double(
            already_doubled=hole_state['doubled'],
            wagering_closed=hole_state['wagering_closed'],
            partnership_formed=hole_state['partnership_formed']
        )

        # Apply double
        hole_state['doubled'] = True
        hole_state['multiplier'] = BettingValidator.calculate_wager_multiplier(
            doubled=True,
            carry_over=hole_state.get('carry_over', False),
            duncan=hole_state.get('duncan', False)
        )

        return {"success": True, "multiplier": hole_state['multiplier']}

    except BettingValidationError as e:
        return {"success": False, "error": e.message}
```

#### Use Case 2: Calculate Final Wager

```python
def calculate_hole_wager(
    base_wager: int,
    doubled: bool,
    carry_over: bool,
    duncan: bool
):
    try:
        # Validate base wager
        BettingValidator.validate_base_wager(base_wager)

        # Calculate multiplier
        multiplier = BettingValidator.calculate_wager_multiplier(
            doubled=doubled,
            carry_over=carry_over,
            duncan=duncan
        )

        # Calculate total
        total = BettingValidator.calculate_total_wager(base_wager, multiplier)

        return {
            "base_wager": base_wager,
            "multiplier": multiplier,
            "total_wager": total,
            "modifiers": {
                "doubled": doubled,
                "carry_over": carry_over,
                "duncan": duncan
            }
        }

    except BettingValidationError as e:
        return {"error": e.message, "details": e.details}
```

#### Use Case 3: Complete Betting Pipeline

```python
def process_betting_action(
    action: str,
    player_id: str,
    hole_state: Dict
):
    """Process a betting action with full validation."""
    try:
        if action == "double":
            BettingValidator.validate_double(
                already_doubled=hole_state['doubled'],
                wagering_closed=hole_state['wagering_closed'],
                partnership_formed=hole_state['partnership_formed']
            )
            hole_state['doubled'] = True

        elif action == "duncan":
            BettingValidator.validate_duncan(
                is_captain=(player_id == hole_state['captain_id']),
                partnership_formed=hole_state['partnership_formed'],
                tee_shots_complete=hole_state['tee_shots_complete']
            )
            hole_state['duncan'] = True

        # Recalculate multiplier
        multiplier = BettingValidator.calculate_wager_multiplier(
            doubled=hole_state.get('doubled', False),
            carry_over=hole_state.get('carry_over', False),
            duncan=hole_state.get('duncan', False)
        )

        total_wager = BettingValidator.calculate_total_wager(
            base_wager=hole_state['base_wager'],
            multiplier=multiplier
        )

        return {
            "success": True,
            "action": action,
            "multiplier": multiplier,
            "total_wager": total_wager
        }

    except BettingValidationError as e:
        return {
            "success": False,
            "action": action,
            "error": e.message,
            "field": e.field
        }
```

---

## GameStateValidator Guide

### Overview

`GameStateValidator` ensures game state transitions are valid and player actions follow game flow rules.

### Constants

```python
GameStateValidator.VALID_PHASES = ["SETUP", "PRE_TEE", "PLAYING", "COMPLETED"]
GameStateValidator.MIN_PLAYERS = 2
GameStateValidator.MAX_PLAYERS = 6
GameStateValidator.MIN_HOLE = 1
GameStateValidator.MAX_HOLE = 18
```

### Methods Reference

#### validate_game_phase()

Validates game phase is valid.

**Signature:**
```python
@classmethod
def validate_game_phase(cls, phase: str) -> None
```

**Example:**
```python
from app.validators import GameStateValidator, GameStateValidationError

# Valid phase
GameStateValidator.validate_game_phase("PLAYING")

# Invalid phase
try:
    GameStateValidator.validate_game_phase("INVALID")
except GameStateValidationError as e:
    print(e.message)  # "Invalid game phase: INVALID"
    print(e.details)  # {'value': 'INVALID', 'valid_phases': [...]}
```

---

#### validate_player_count()

Validates player count is within valid range (2-6 players).

**Signature:**
```python
@classmethod
def validate_player_count(cls, count: int) -> None
```

**Example:**
```python
# Valid player count
GameStateValidator.validate_player_count(4)

# Invalid - too few
try:
    GameStateValidator.validate_player_count(1)
except GameStateValidationError as e:
    print(e.message)  # "Player count must be between 2 and 6"

# Invalid - too many
try:
    GameStateValidator.validate_player_count(8)
except GameStateValidationError as e:
    print(e.message)  # "Player count must be between 2 and 6"
```

---

#### validate_hole_number()

Validates hole number is valid (1-18).

**Signature:**
```python
@classmethod
def validate_hole_number(cls, hole_number: int) -> None
```

**Example:**
```python
# Valid hole
GameStateValidator.validate_hole_number(5)

# Invalid - out of range
try:
    GameStateValidator.validate_hole_number(0)
except GameStateValidationError as e:
    print(e.message)  # "Hole number must be between 1 and 18"

try:
    GameStateValidator.validate_hole_number(19)
except GameStateValidationError as e:
    print(e.message)  # "Hole number must be between 1 and 18"
```

---

#### validate_player_action()

Validates a player action is allowed in current game state.

**Signature:**
```python
@classmethod
def validate_player_action(
    cls,
    player_id: str,
    action: str,
    current_player: str,
    game_phase: str
) -> None
```

**Example:**
```python
# Valid action - player's turn
GameStateValidator.validate_player_action(
    player_id="player1",
    action="hit_shot",
    current_player="player1",
    game_phase="PLAYING"
)

# Invalid - not player's turn
try:
    GameStateValidator.validate_player_action(
        player_id="player1",
        action="hit_shot",
        current_player="player2",
        game_phase="PLAYING"
    )
except GameStateValidationError as e:
    print(e.message)  # "Not your turn"

# Invalid - wrong game phase
try:
    GameStateValidator.validate_player_action(
        player_id="player1",
        action="hit_shot",
        current_player="player1",
        game_phase="SETUP"
    )
except GameStateValidationError as e:
    print(e.message)  # "Cannot perform action in current game phase"
```

---

#### validate_partnership_formation()

Validates partnership formation is allowed.

**Partnership Rules:**
- Captain cannot partner with themselves
- Tee shots must be complete
- Cannot form after deadline

**Signature:**
```python
@classmethod
def validate_partnership_formation(
    cls,
    captain_id: str,
    partner_id: str,
    tee_shots_complete: bool
) -> None
```

**Example:**
```python
# Valid partnership
GameStateValidator.validate_partnership_formation(
    captain_id="player1",
    partner_id="player2",
    tee_shots_complete=True
)

# Invalid - partnering with self
try:
    GameStateValidator.validate_partnership_formation(
        captain_id="player1",
        partner_id="player1",
        tee_shots_complete=True
    )
except GameStateValidationError as e:
    print(e.message)  # "Cannot partner with yourself"

# Invalid - tee shots not complete
try:
    GameStateValidator.validate_partnership_formation(
        captain_id="player1",
        partner_id="player2",
        tee_shots_complete=False
    )
except GameStateValidationError as e:
    print(e.message)  # "Partnership deadline has passed (tee shots complete)"
```

---

#### validate_shot_execution()

Validates shot execution is allowed.

**Signature:**
```python
@classmethod
def validate_shot_execution(
    cls,
    player_id: str,
    hole_complete: bool,
    player_holed: bool
) -> None
```

**Example:**
```python
# Valid shot
GameStateValidator.validate_shot_execution(
    player_id="player1",
    hole_complete=False,
    player_holed=False
)

# Invalid - hole complete
try:
    GameStateValidator.validate_shot_execution(
        player_id="player1",
        hole_complete=True,
        player_holed=False
    )
except GameStateValidationError as e:
    print(e.message)  # "Hole is already complete"

# Invalid - player already holed out
try:
    GameStateValidator.validate_shot_execution(
        player_id="player1",
        hole_complete=False,
        player_holed=True
    )
except GameStateValidationError as e:
    print(e.message)  # "Player has already holed out"
```

---

#### validate_game_start()

Validates game can start.

**Start Requirements:**
- Valid player count
- Course selected
- All players ready

**Signature:**
```python
@classmethod
def validate_game_start(
    cls,
    player_count: int,
    course_selected: bool,
    all_players_ready: bool
) -> None
```

**Example:**
```python
# Valid game start
GameStateValidator.validate_game_start(
    player_count=4,
    course_selected=True,
    all_players_ready=True
)

# Invalid - no course
try:
    GameStateValidator.validate_game_start(
        player_count=4,
        course_selected=False,
        all_players_ready=True
    )
except GameStateValidationError as e:
    print(e.message)  # "Course must be selected before starting game"

# Invalid - players not ready
try:
    GameStateValidator.validate_game_start(
        player_count=4,
        course_selected=True,
        all_players_ready=False
    )
except GameStateValidationError as e:
    print(e.message)  # "All players must be ready before starting game"
```

---

#### validate_hole_completion()

Validates hole can be completed.

**Signature:**
```python
@classmethod
def validate_hole_completion(
    cls,
    players_holed: List[str],
    total_players: int
) -> None
```

**Example:**
```python
# Valid - all players holed out
GameStateValidator.validate_hole_completion(
    players_holed=["p1", "p2", "p3", "p4"],
    total_players=4
)

# Invalid - not all players done
try:
    GameStateValidator.validate_hole_completion(
        players_holed=["p1", "p2"],
        total_players=4
    )
except GameStateValidationError as e:
    print(e.message)  # "Not all players have completed the hole"
    print(e.details)  # {'completed': 2, 'total': 4, 'remaining': 2}
```

### Game Flow Validation

#### Game Phase Flow

```
SETUP
  ↓
  validate_game_start() → PRE_TEE
  ↓
  validate_hole_number(1) → PLAYING
  ↓
  validate_shot_execution() → (shots)
  ↓
  validate_hole_completion() → (next hole)
  ↓
  validate_hole_number(18) → COMPLETED
```

#### Hole Flow

```
Start Hole
  ↓
  validate_hole_number()
  ↓
Tee Shots
  ↓
  validate_shot_execution()
  ↓
Partnership Window
  ↓
  validate_partnership_formation()
  ↓
Approach Shots
  ↓
  validate_shot_execution()
  ↓
All Players Holed Out
  ↓
  validate_hole_completion()
  ↓
Complete Hole
```

### Common Use Cases

#### Use Case 1: Validate Game Setup

```python
def setup_game(players: List[Dict], course: Dict):
    try:
        # Validate player count
        GameStateValidator.validate_player_count(len(players))

        # Validate game can start
        GameStateValidator.validate_game_start(
            player_count=len(players),
            course_selected=(course is not None),
            all_players_ready=all(p.get('ready') for p in players)
        )

        return {
            "success": True,
            "game_phase": "PRE_TEE",
            "player_count": len(players)
        }

    except GameStateValidationError as e:
        return {
            "success": False,
            "error": e.message,
            "field": e.field
        }
```

#### Use Case 2: Handle Player Action

```python
def execute_player_action(
    player_id: str,
    action: str,
    game_state: Dict
):
    try:
        # Validate action is allowed
        GameStateValidator.validate_player_action(
            player_id=player_id,
            action=action,
            current_player=game_state['current_player'],
            game_phase=game_state['phase']
        )

        # Execute action
        if action == "hit_shot":
            GameStateValidator.validate_shot_execution(
                player_id=player_id,
                hole_complete=game_state['hole_complete'],
                player_holed=game_state['players'][player_id]['holed']
            )
            # ... execute shot

        return {"success": True, "action": action}

    except GameStateValidationError as e:
        return {
            "success": False,
            "error": e.message,
            "details": e.details
        }
```

#### Use Case 3: Validate Hole Progression

```python
def progress_to_next_hole(game_state: Dict):
    try:
        current_hole = game_state['current_hole']
        next_hole = current_hole + 1

        # Validate current hole is complete
        GameStateValidator.validate_hole_completion(
            players_holed=game_state['players_holed'],
            total_players=len(game_state['players'])
        )

        # Validate next hole number
        GameStateValidator.validate_hole_number(next_hole)

        # Progress to next hole
        game_state['current_hole'] = next_hole
        game_state['hole_complete'] = False
        game_state['players_holed'] = []

        return {
            "success": True,
            "current_hole": next_hole
        }

    except GameStateValidationError as e:
        # Check if game is complete
        if current_hole == 18:
            GameStateValidator.validate_game_phase("COMPLETED")
            return {
                "success": True,
                "game_complete": True
            }

        return {
            "success": False,
            "error": e.message
        }
```

---

## Error Handling

### Exception Hierarchy

```
Exception
  └─ ValidationError (base)
      ├─ HandicapValidationError
      ├─ BettingValidationError
      ├─ GameStateValidationError
      └─ PartnershipValidationError
```

### ValidationError Structure

All validation errors inherit from `ValidationError` and include:

```python
class ValidationError(Exception):
    message: str              # Human-readable error message
    field: Optional[str]      # Field that failed validation
    details: Dict[str, Any]   # Additional context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
```

### Catching Validation Errors

#### Basic Error Handling

```python
from app.validators import HandicapValidator, HandicapValidationError

try:
    HandicapValidator.validate_handicap(60.0)
except HandicapValidationError as e:
    print(f"Error: {e.message}")
    print(f"Field: {e.field}")
    print(f"Details: {e.details}")
```

#### Specific vs. Generic Errors

```python
from app.validators import (
    ValidationError,
    HandicapValidationError,
    BettingValidationError
)

try:
    # Some validation
    pass
except HandicapValidationError as e:
    # Handle handicap-specific error
    print(f"Handicap error: {e.message}")
except BettingValidationError as e:
    # Handle betting-specific error
    print(f"Betting error: {e.message}")
except ValidationError as e:
    # Handle any other validation error
    print(f"Validation error: {e.message}")
```

#### Extract Error Details

```python
try:
    HandicapValidator.validate_handicap(60.0, "player_handicap")
except HandicapValidationError as e:
    error_dict = e.to_dict()
    # {
    #     'error': 'player_handicap cannot exceed 54.0',
    #     'field': 'player_handicap',
    #     'details': {'value': 60.0, 'max': 54.0}
    # }
```

### Using Error Details in API Responses

#### FastAPI Error Handler

```python
from fastapi import FastAPI, HTTPException
from app.validators import ValidationError

app = FastAPI()

@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Failed",
            "message": exc.message,
            "field": exc.field,
            "details": exc.details
        }
    )
```

#### API Endpoint with Validation

```python
from fastapi import APIRouter, HTTPException
from app.validators import HandicapValidator, HandicapValidationError

router = APIRouter()

@router.post("/players")
async def create_player(name: str, handicap: float):
    try:
        # Validate handicap
        HandicapValidator.validate_handicap(handicap)

        # Create player
        player = {"name": name, "handicap": handicap}

        return {
            "success": True,
            "player": player
        }

    except HandicapValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=e.to_dict()
        )
```

#### Pydantic Integration

```python
from pydantic import BaseModel, field_validator
from app.validators import HandicapValidator, HandicapValidationError

class Player(BaseModel):
    name: str
    handicap: float

    @field_validator('handicap')
    @classmethod
    def validate_handicap(cls, v):
        try:
            HandicapValidator.validate_handicap(v)
            return v
        except HandicapValidationError as e:
            raise ValueError(e.message)
```

### Error Response Patterns

#### Success/Error Response

```python
def validate_and_execute(data: Dict) -> Dict:
    try:
        # Validation
        HandicapValidator.validate_handicap(data['handicap'])

        # Execution
        result = execute_operation(data)

        return {
            "success": True,
            "data": result
        }

    except ValidationError as e:
        return {
            "success": False,
            "error": {
                "message": e.message,
                "field": e.field,
                "details": e.details
            }
        }
```

#### Multiple Validations

```python
def validate_multiple_fields(data: Dict) -> Dict:
    errors = []

    # Validate handicap
    try:
        HandicapValidator.validate_handicap(data['handicap'])
    except HandicapValidationError as e:
        errors.append(e.to_dict())

    # Validate base wager
    try:
        BettingValidator.validate_base_wager(data['base_wager'])
    except BettingValidationError as e:
        errors.append(e.to_dict())

    if errors:
        return {
            "success": False,
            "errors": errors
        }

    return {"success": True}
```

---

## Integration Patterns

### Using Validators in WolfGoatPigSimulation

#### Example: Hole Setup

```python
class WolfGoatPigSimulation:
    def setup_hole(self, hole_number: int):
        try:
            # Validate hole number
            GameStateValidator.validate_hole_number(hole_number)

            # Get hole data
            hole = self.course.holes[hole_number - 1]

            # Validate stroke allocation
            HandicapValidator.validate_stroke_allocation(
                players_handicaps=[p.course_handicap for p in self.players],
                hole_stroke_indexes=self.course.get_stroke_indexes()
            )

            # Calculate strokes for each player
            for player in self.players:
                strokes = HandicapValidator.calculate_strokes_received(
                    course_handicap=player.course_handicap,
                    stroke_index=hole.stroke_index
                )
                player.strokes_on_hole = strokes

            return {"success": True, "hole": hole_number}

        except (GameStateValidationError, HandicapValidationError) as e:
            return {"success": False, "error": e.message}
```

#### Example: Apply Double

```python
class WolfGoatPigSimulation:
    def apply_double(self):
        try:
            # Validate double is allowed
            BettingValidator.validate_double(
                already_doubled=self.current_hole_state.doubled,
                wagering_closed=self.current_hole_state.wagering_closed,
                partnership_formed=self.current_hole_state.partnership is not None
            )

            # Apply double
            self.current_hole_state.doubled = True

            # Recalculate wager
            multiplier = BettingValidator.calculate_wager_multiplier(
                doubled=True,
                carry_over=self.current_hole_state.carry_over,
                duncan=self.current_hole_state.duncan
            )

            total = BettingValidator.calculate_total_wager(
                base_wager=self.base_wager,
                multiplier=multiplier
            )

            self.current_hole_state.wager = total

            return {"success": True, "wager": total}

        except BettingValidationError as e:
            return {"success": False, "error": e.message}
```

### Using Validators in API Handlers

#### Example: Create Game Endpoint

```python
from fastapi import APIRouter, HTTPException
from app.validators import (
    GameStateValidator,
    HandicapValidator,
    ValidationError
)

router = APIRouter()

@router.post("/games")
async def create_game(
    players: List[Dict],
    course_id: str
):
    try:
        # Validate player count
        GameStateValidator.validate_player_count(len(players))

        # Validate each player's handicap
        for player in players:
            HandicapValidator.validate_handicap(player['handicap'])

        # Get course
        course = get_course(course_id)

        # Validate game can start
        GameStateValidator.validate_game_start(
            player_count=len(players),
            course_selected=(course is not None),
            all_players_ready=True
        )

        # Create game
        game = create_game_instance(players, course)

        return {
            "success": True,
            "game_id": game.id,
            "players": len(players)
        }

    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=e.to_dict()
        )
```

#### Example: Execute Shot Endpoint

```python
@router.post("/games/{game_id}/shot")
async def execute_shot(
    game_id: str,
    player_id: str,
    shot_data: Dict
):
    try:
        game = get_game(game_id)

        # Validate player action
        GameStateValidator.validate_player_action(
            player_id=player_id,
            action="hit_shot",
            current_player=game.current_player,
            game_phase=game.phase
        )

        # Validate shot execution
        GameStateValidator.validate_shot_execution(
            player_id=player_id,
            hole_complete=game.hole_complete,
            player_holed=game.players[player_id].holed
        )

        # Execute shot
        result = game.execute_shot(player_id, shot_data)

        return {
            "success": True,
            "result": result
        }

    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=e.to_dict()
        )
```

### Defensive Programming Patterns

#### Pattern 1: Validate Early

```python
def process_hole_result(hole_state: Dict, players: List):
    # Validate FIRST, execute SECOND
    try:
        GameStateValidator.validate_hole_completion(
            players_holed=[p.id for p in players if p.holed],
            total_players=len(players)
        )
    except GameStateValidationError as e:
        return {"success": False, "error": e.message}

    # Now safe to process
    winner = determine_winner(hole_state, players)
    distribute_winnings(winner, hole_state.wager)

    return {"success": True, "winner": winner}
```

#### Pattern 2: Validate at Boundaries

```python
class GameAPI:
    def execute_action(self, game_id: str, player_id: str, action: Dict):
        # Validate at API boundary
        try:
            self._validate_action(player_id, action)
        except ValidationError as e:
            return {"success": False, "error": e.to_dict()}

        # Pass to domain layer (already validated)
        return self.game_service.execute(game_id, player_id, action)

    def _validate_action(self, player_id: str, action: Dict):
        if action['type'] == 'double':
            BettingValidator.validate_double(
                already_doubled=self.game.doubled,
                wagering_closed=self.game.wagering_closed,
                partnership_formed=self.game.partnership is not None
            )
```

#### Pattern 3: Chain Validations

```python
def setup_player_for_game(player_data: Dict, course: Dict):
    try:
        # Chain validations - fail fast
        HandicapValidator.validate_handicap(player_data['handicap'])

        HandicapValidator.validate_course_rating(
            course['rating'],
            course['slope']
        )

        course_handicap = HandicapValidator.calculate_course_handicap(
            handicap_index=player_data['handicap'],
            slope_rating=course['slope'],
            course_rating=course['rating'],
            par=course['par']
        )

        return {
            "success": True,
            "course_handicap": course_handicap
        }

    except HandicapValidationError as e:
        # Single catch for all validations
        return {"success": False, "error": e.to_dict()}
```

#### Pattern 4: Validation Guards

```python
class HoleState:
    def apply_double(self):
        # Guard: validate before state change
        BettingValidator.validate_double(
            already_doubled=self.doubled,
            wagering_closed=self.wagering_closed,
            partnership_formed=self.partnership is not None
        )

        # Safe to mutate state
        self.doubled = True
        self._recalculate_wager()

    def form_partnership(self, captain_id: str, partner_id: str):
        # Guard: validate before state change
        GameStateValidator.validate_partnership_formation(
            captain_id=captain_id,
            partner_id=partner_id,
            tee_shots_complete=self.tee_shots_complete
        )

        # Safe to mutate state
        self.partnership = (captain_id, partner_id)
```

---

## Testing with Validators

### Testing Validation Logic

#### Test Valid Cases

```python
import pytest
from app.validators import HandicapValidator, HandicapValidationError

def test_valid_handicap():
    """Test valid handicap passes validation."""
    # Should not raise
    HandicapValidator.validate_handicap(15.0)
    HandicapValidator.validate_handicap(0.0)
    HandicapValidator.validate_handicap(54.0)

def test_valid_stroke_calculation():
    """Test stroke calculation is correct."""
    # Player with 15 handicap on stroke index 8 hole
    strokes = HandicapValidator.calculate_strokes_received(
        course_handicap=15.0,
        stroke_index=8
    )
    assert strokes == 1

    # Player with 25 handicap on stroke index 5 hole
    strokes = HandicapValidator.calculate_strokes_received(
        course_handicap=25.0,
        stroke_index=5
    )
    assert strokes == 2
```

#### Test Invalid Cases

```python
def test_invalid_handicap():
    """Test invalid handicaps raise errors."""
    # Handicap too high
    with pytest.raises(HandicapValidationError) as exc:
        HandicapValidator.validate_handicap(60.0)
    assert "cannot exceed" in str(exc.value)

    # Handicap negative
    with pytest.raises(HandicapValidationError) as exc:
        HandicapValidator.validate_handicap(-5.0)
    assert "cannot be less than" in str(exc.value)

    # Wrong type
    with pytest.raises(HandicapValidationError) as exc:
        HandicapValidator.validate_handicap("15")
    assert "must be a number" in str(exc.value)
```

#### Test Error Details

```python
def test_validation_error_details():
    """Test error includes useful details."""
    try:
        HandicapValidator.validate_handicap(60.0, "player_handicap")
    except HandicapValidationError as e:
        assert e.message == "player_handicap cannot exceed 54.0"
        assert e.field == "player_handicap"
        assert e.details == {"value": 60.0, "max": 54.0}

        # Test to_dict() method
        error_dict = e.to_dict()
        assert "error" in error_dict
        assert "field" in error_dict
        assert "details" in error_dict
```

### Mocking Validation for Unit Tests

#### Mock Validator Methods

```python
from unittest.mock import patch
from app.validators import HandicapValidator

def test_game_setup_with_mocked_validation():
    """Test game setup with mocked handicap validation."""
    with patch.object(HandicapValidator, 'validate_handicap'):
        # Validation is bypassed
        game = setup_game(players=[
            {"id": "p1", "handicap": 999}  # Would normally fail
        ])
        assert game is not None
```

#### Pytest Fixtures for Validation

```python
import pytest

@pytest.fixture
def mock_validators(monkeypatch):
    """Mock all validators to always pass."""
    monkeypatch.setattr(
        'app.validators.HandicapValidator.validate_handicap',
        lambda x: None
    )
    monkeypatch.setattr(
        'app.validators.BettingValidator.validate_double',
        lambda **kwargs: None
    )

def test_with_mocked_validators(mock_validators):
    """Test using mocked validators."""
    # All validations pass
    game = create_game_with_invalid_data()
    assert game is not None
```

#### Selective Mocking

```python
def test_double_logic_without_validation():
    """Test double logic without validation overhead."""
    hole_state = HoleState()

    with patch.object(BettingValidator, 'validate_double'):
        # Test the logic, not the validation
        hole_state.apply_double()
        assert hole_state.doubled is True
        assert hole_state.multiplier == 2
```

### Integration Tests with Validators

```python
def test_complete_hole_flow():
    """Integration test: complete hole with all validations."""
    # Setup
    game = WolfGoatPigSimulation()
    game.setup_players([
        {"id": "p1", "handicap": 10.0},
        {"id": "p2", "handicap": 15.0},
        {"id": "p3", "handicap": 8.0},
        {"id": "p4", "handicap": 20.0}
    ])

    # Start hole (validates hole number)
    result = game.start_hole(1)
    assert result['success'] is True

    # Form partnership (validates partnership rules)
    result = game.form_partnership("p1", "p2")
    assert result['success'] is True

    # Apply double (validates betting rules)
    result = game.apply_double()
    assert result['success'] is True

    # Complete hole (validates completion)
    result = game.complete_hole()
    assert result['success'] is True
```

### Test Parameterization

```python
@pytest.mark.parametrize("handicap,expected_category", [
    (3.5, "SCRATCH"),
    (10.0, "LOW"),
    (15.0, "MID"),
    (25.0, "HIGH"),
    (35.0, "BEGINNER"),
])
def test_handicap_categories(handicap, expected_category):
    """Test handicap categorization."""
    category = HandicapValidator.get_handicap_category(handicap)
    assert category == expected_category

@pytest.mark.parametrize("handicap,stroke_index,expected_strokes", [
    (15.0, 8, 1),
    (25.0, 5, 2),
    (5.0, 8, 0),
    (36.0, 1, 2),
])
def test_stroke_allocation(handicap, stroke_index, expected_strokes):
    """Test stroke allocation calculation."""
    strokes = HandicapValidator.calculate_strokes_received(
        course_handicap=handicap,
        stroke_index=stroke_index
    )
    assert strokes == expected_strokes
```

---

## Best Practices

### 1. Validate Early, Fail Fast

```python
# GOOD: Validate before doing work
def create_player(data: Dict):
    HandicapValidator.validate_handicap(data['handicap'])  # Fail fast
    player = Player(**data)  # Now safe to create
    return player

# BAD: Create first, validate later
def create_player(data: Dict):
    player = Player(**data)  # Might create invalid player
    HandicapValidator.validate_handicap(player.handicap)  # Too late
    return player
```

### 2. Use Specific Exceptions

```python
# GOOD: Catch specific exceptions
try:
    HandicapValidator.validate_handicap(handicap)
except HandicapValidationError as e:
    return {"error": e.message}

# BAD: Catch generic exceptions
try:
    HandicapValidator.validate_handicap(handicap)
except Exception as e:  # Too broad
    return {"error": str(e)}
```

### 3. Provide Context in Errors

```python
# GOOD: Use field_name parameter
for i, player in enumerate(players):
    HandicapValidator.validate_handicap(
        player['handicap'],
        field_name=f"player_{i}_handicap"
    )

# BAD: Generic field name
for player in players:
    HandicapValidator.validate_handicap(player['handicap'])
```

### 4. Chain Validations Logically

```python
# GOOD: Logical validation order
HandicapValidator.validate_handicap(handicap_index)
HandicapValidator.validate_course_rating(course_rating, slope_rating)
course_handicap = HandicapValidator.calculate_course_handicap(...)

# BAD: Calculate before validating
course_handicap = HandicapValidator.calculate_course_handicap(...)
HandicapValidator.validate_handicap(handicap_index)  # Too late
```

### 5. Skip Validation Only When Safe

```python
# GOOD: Skip when already validated
# First call - validate
strokes = HandicapValidator.calculate_strokes_received(
    course_handicap=handicap,
    stroke_index=index,
    validate=True
)

# Repeated calls in loop - skip validation
for hole in holes:
    strokes = HandicapValidator.calculate_strokes_received(
        course_handicap=handicap,
        stroke_index=hole.index,
        validate=False  # Already validated once
    )

# BAD: Always skip validation
strokes = HandicapValidator.calculate_strokes_received(
    course_handicap=user_input,  # Untrusted!
    stroke_index=hole.index,
    validate=False  # Dangerous!
)
```

### 6. Use Validators at Boundaries

```python
# GOOD: Validate at API/service boundary
class GameAPI:
    def create_game(self, data: Dict):
        # Validate at boundary
        GameStateValidator.validate_player_count(len(data['players']))

        # Pass to domain layer (validated data)
        return self.game_service.create(data)

# BAD: Validate deep in domain logic
class Game:
    def __init__(self, players: List):
        self.players = players
        # Don't validate here - too late
```

### 7. Document Validation Rules

```python
# GOOD: Document what validations occur
def setup_hole(self, hole_number: int):
    """
    Setup a hole for play.

    Validations:
    - Hole number must be 1-18
    - All player handicaps must be 0-54
    - Stroke indexes must be unique 1-18

    Raises:
        GameStateValidationError: Invalid hole number
        HandicapValidationError: Invalid handicap or stroke allocation
    """
    GameStateValidator.validate_hole_number(hole_number)
    # ...
```

### 8. Return Rich Error Context

```python
# GOOD: Return full error context
except ValidationError as e:
    return {
        "success": False,
        "error": {
            "message": e.message,
            "field": e.field,
            "details": e.details,
            "type": type(e).__name__
        }
    }

# BAD: Return only message
except ValidationError as e:
    return {"error": str(e)}
```

### 9. Test Validation Separately

```python
# GOOD: Test validation in isolation
def test_handicap_validation():
    with pytest.raises(HandicapValidationError):
        HandicapValidator.validate_handicap(60.0)

def test_game_logic():
    # Test game logic with valid data
    game = create_game(valid_data)
    assert game.ready is True

# BAD: Mix validation testing with logic testing
def test_game_with_invalid_handicap():
    # Testing two things at once
    with pytest.raises(HandicapValidationError):
        game = create_game(invalid_data)
```

### 10. Use Type Hints

```python
# GOOD: Type hints make usage clear
def validate_and_setup(
    handicap: float,
    course_rating: float,
    slope_rating: int
) -> int:
    HandicapValidator.validate_handicap(handicap)
    HandicapValidator.validate_course_rating(course_rating, slope_rating)
    return HandicapValidator.calculate_course_handicap(...)

# BAD: No type hints
def validate_and_setup(handicap, course_rating, slope_rating):
    # What types are these?
    HandicapValidator.validate_handicap(handicap)
    # ...
```

---

## Summary

Wolf Goat Pig validators provide:

- **HandicapValidator**: USGA-compliant handicap calculations and validation
- **BettingValidator**: Wolf Goat Pig betting rules enforcement
- **GameStateValidator**: Game flow and state transition validation

Key Benefits:
- Centralized validation logic
- Clear, descriptive error messages
- Type safety and range checking
- Easy integration with APIs
- Comprehensive test coverage

Use validators to:
1. Validate data at API boundaries
2. Enforce business rules consistently
3. Provide clear error feedback
4. Enable defensive programming
5. Simplify testing

For more examples, see:
- `/backend/app/validators/` - Validator implementations
- `/backend/app/validators/test_game_state_validator.py` - Test examples
- API handlers in `/backend/app/main.py` - Integration examples
