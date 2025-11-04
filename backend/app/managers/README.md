# Managers Package

This package contains manager classes that centralize business logic for the Wolf Goat Pig application.

## Overview

Managers provide a higher-level abstraction over validators and game state, encapsulating complex business rules and workflows.

### Available Managers

1. **RuleManager** - Centralized game rule enforcement
2. **ScoringManager** - Score calculation and management

---

## RuleManager

The `RuleManager` provides centralized enforcement of all Wolf Goat Pig game rules.

### Features

- **Singleton Pattern**: Ensures consistent rule application across the entire application
- **Rule Enforcement**: Validates all game actions against official rules
- **Integration**: Works seamlessly with existing validators
- **Comprehensive Validation**: Covers partnerships, betting, turn order, scoring, and handicaps

### Usage

```python
from app.managers import RuleManager, RuleViolationError

# Get the singleton instance
manager = RuleManager.get_instance()

# Check if partnership can be formed
try:
    can_form = manager.can_form_partnership(
        captain_id="player_1",
        partner_id="player_2",
        game_state=current_game_state
    )
    if can_form:
        # Proceed with partnership formation
        pass
except RuleViolationError as e:
    print(f"Cannot form partnership: {e.message}")
    print(f"Details: {e.details}")
```

### Core Methods

#### Partnership Rules

##### `can_form_partnership(captain_id, partner_id, game_state)`
Check if a partnership can be formed.

**Rules:**
- Captain cannot partner with themselves
- Both players must be in the game
- Partnership deadline must not have passed (tee shots incomplete)
- No existing partnership for this hole

**Returns:** `bool` - True if partnership can be formed

**Raises:** `RuleViolationError` if rules are violated

```python
try:
    manager.can_form_partnership("player_1", "player_2", game_state)
except RuleViolationError as e:
    print(f"Partnership blocked: {e.message}")
```

##### `can_go_lone_wolf(player_id, game_state)`
Check if player can go lone wolf (solo against all).

**Rules:**
- Must be the captain (first in hitting order)
- Partnership must not have been formed yet
- Creates 1 vs. all scenario

**Returns:** `bool` - True if player can go lone wolf

```python
if manager.can_go_lone_wolf("player_1", game_state):
    # Allow lone wolf action
    pass
```

#### Betting Rules

##### `can_double(player_id, game_state)`
Check if player can double the wager.

**Rules:**
- Partnership must be formed first
- Hole cannot have been doubled already
- Wagering window must be open (no balls holed)

**Returns:** `bool` - True if player can double

```python
if manager.can_double("player_1", game_state):
    # Allow double action
    pass
```

##### `can_redouble(player_id, game_state)`
Check if player can redouble the wager.

**Rules:**
- Hole must have been doubled first
- Cannot redouble if already redoubled
- Wagering window must be open

**Returns:** `bool` - True if player can redouble

##### `can_duncan(player_id, game_state)`
Check if The Duncan can be invoked.

**Rules:**
- Only captain can invoke Duncan
- Cannot be used after partnership formed
- Cannot be used after tee shots complete
- Doubles the wager (captain goes solo)

**Returns:** `bool` - True if Duncan can be invoked

```python
if manager.can_duncan("player_1", game_state):
    # Allow Duncan invocation
    pass
```

#### Turn Order Rules

##### `validate_player_turn(player_id, game_state)`
Validate that it's the specified player's turn.

**Rules:**
- Based on distance from hole (farthest plays first)
- On tee, follows hitting order
- Player cannot act out of turn

**Returns:** `bool` - True if it's player's turn

**Raises:** `RuleViolationError` if not player's turn

```python
try:
    manager.validate_player_turn("player_1", game_state)
    # Player can take action
except RuleViolationError:
    # Not player's turn
    pass
```

#### Action Discovery

##### `get_valid_actions(player_id, game_state)`
Get list of valid actions for a player.

Returns all actions the player can legally take right now.

**Returns:** `List[str]` - List of valid action names

**Possible Actions:**
- `"hit_shot"` - Take a shot
- `"concede_hole"` - Concede the hole
- `"form_partnership"` - Form a partnership (captain only)
- `"go_lone_wolf"` - Go solo against all (captain only)
- `"invoke_duncan"` - Invoke The Duncan (captain only)
- `"double"` - Double the wager
- `"redouble"` - Redouble the wager
- `"advance_to_next_hole"` - Move to next hole (hole complete)

```python
actions = manager.get_valid_actions("player_1", game_state)
print(f"Available actions: {actions}")
# Output: ['hit_shot', 'form_partnership', 'invoke_duncan']
```

#### Scoring Rules

##### `calculate_hole_winner(hole_results)`
Determine the winner of a hole.

**Args:**
- `hole_results` - Dictionary mapping player_id/team_id to net scores

**Returns:** `Optional[str]` - Winner ID, or None if tied

```python
results = {"player_1": 4, "player_2": 5, "player_3": 4}
winner = manager.calculate_hole_winner(results)
# Returns: None (tie between player_1 and player_3)
```

##### `apply_handicap_strokes(hole_number, player_handicaps, hole_stroke_index)`
Calculate handicap strokes for each player on a hole.

Uses USGA stroke allocation rules.

**Args:**
- `hole_number` - Current hole (1-18)
- `player_handicaps` - Dict mapping player_id to handicap
- `hole_stroke_index` - Stroke index for hole (1-18)

**Returns:** `Dict[str, int]` - Strokes received by each player

```python
handicaps = {
    "player_1": 18.0,
    "player_2": 10.0,
    "player_3": 5.0
}
strokes = manager.apply_handicap_strokes(1, handicaps, 5)
# Returns: {'player_1': 1, 'player_2': 1, 'player_3': 0}
```

### Helper Methods

##### `get_rule_summary()`
Get a summary of all game rules.

**Returns:** `Dict[str, Any]` - Rule categories and descriptions

```python
summary = manager.get_rule_summary()
print(summary["partnership"]["formation"])
# Output: "Captain can form partnership before all tee shots complete"
```

### Exception Handling

The `RuleManager` raises `RuleViolationError` when rules are violated.

```python
from app.managers import RuleViolationError

try:
    manager.can_form_partnership(captain_id, partner_id, game_state)
except RuleViolationError as e:
    # Access error details
    print(f"Error: {e.message}")
    print(f"Field: {e.field}")
    print(f"Details: {e.details}")

    # Convert to dict for API response
    error_dict = e.to_dict()
```

### Game State Structure

The `RuleManager` expects game state in the following format:

```python
game_state = {
    "game_id": "game-123",
    "players": [
        {"id": "player_1", "name": "Alice", "handicap": 10.0},
        {"id": "player_2", "name": "Bob", "handicap": 15.0},
        # ...
    ],
    "current_hole_number": 1,
    "current_hole": {
        "hole_number": 1,
        "par": 4,
        "yards": 420,
        "stroke_index": 5,
        "hitting_order": ["player_1", "player_2", "player_3"],
        "teams": {
            "partnership_captain": "player_1",  # Optional
            "partnership_partner": "player_2"   # Optional
        },
        "betting": {
            "base_wager": 1,
            "current_wager": 1,
            "doubled": False,
            "redoubled": False,
            "duncan_invoked": False,
        },
        "tee_shots_complete": 0,
        "partnership_deadline_passed": False,
        "wagering_closed": False,
        "hole_complete": False,
        "balls_in_hole": [],
        "next_player_to_hit": "player_1",
    }
}
```

### Integration with Validators

The `RuleManager` internally uses validators for low-level validation:

- **BettingValidator** - Validates betting actions
- **GameStateValidator** - Validates game state transitions
- **HandicapValidator** - Validates handicap calculations

This provides a layered validation approach:
1. **Validators** - Low-level, focused validation
2. **RuleManager** - High-level, business rule enforcement

### Constants

```python
# Player limits
RuleManager.MIN_PLAYERS = 2
RuleManager.MAX_PLAYERS = 6
RuleManager.HOLES_PER_ROUND = 18

# Betting
RuleManager.BASE_WAGER_QUARTERS = 1
RuleManager.MIN_WAGER = 1
RuleManager.MAX_DOUBLE_MULTIPLIER = 8  # 2^3 = 8x
```

### Testing

Run the test suite to verify functionality:

```bash
cd backend
python3 test_rule_manager.py
```

### Best Practices

1. **Always use the singleton instance:**
   ```python
   manager = RuleManager.get_instance()
   ```

2. **Handle exceptions gracefully:**
   ```python
   try:
       manager.can_form_partnership(...)
   except RuleViolationError as e:
       return {"error": e.message, "details": e.details}
   ```

3. **Use valid actions discovery:**
   ```python
   # Instead of checking each action individually
   actions = manager.get_valid_actions(player_id, game_state)
   if "double" in actions:
       # Show double button
   ```

4. **Validate before state changes:**
   ```python
   # Check first
   if manager.can_form_partnership(captain, partner, state):
       # Then modify state
       form_partnership(captain, partner)
   ```

### Design Patterns

- **Singleton Pattern**: Ensures one instance across application
- **Facade Pattern**: Simplifies interaction with multiple validators
- **Strategy Pattern**: Different validation strategies for different actions

### Future Enhancements

Potential additions to the RuleManager:

1. **Rule Configuration**: Allow custom rule sets
2. **Rule History**: Track rule enforcement for analytics
3. **Rule Explanations**: Provide detailed explanations for why actions are blocked
4. **Undo Support**: Validate if actions can be undone
5. **Multi-format Support**: Support different game variants (scramble, best ball, etc.)

---

## Contributing

When adding new game rules:

1. Add validation method to appropriate validator
2. Add high-level rule check to RuleManager
3. Update `get_valid_actions()` to include new action
4. Add tests to `test_rule_manager.py`
5. Update this documentation
