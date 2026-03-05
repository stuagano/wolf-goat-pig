# GameStateValidator Usage Guide

The `GameStateValidator` class provides comprehensive validation for Wolf Goat Pig game state transitions. It ensures game rules are properly enforced throughout the game lifecycle.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Core Validation Methods](#core-validation-methods)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Integration Patterns](#integration-patterns)

## Overview

The GameStateValidator validates:
- Game initialization (4 players required, valid course)
- Hole state transitions (sequential progression)
- Shot execution timing (correct player's turn)
- Partnership formation timing (after tee shots, before deadline)
- Player actions (valid player IDs, player exists)
- Game phase transitions (REGULAR → VINNIE_VARIATION → HOEPFINGER)
- Ball positions (valid distances, lie types)
- Hole completion (all players finished)

## Installation

```python
from app.validators import GameStateValidator
from app.validators.exceptions import GameStateValidationError, PartnershipValidationError
```

## Core Validation Methods

### Game Initialization

```python
validate_game_initialization(players, course_info, validate=True)
```

Validates game can be initialized with provided configuration.

**Parameters:**
- `players`: List of player dictionaries with id, name, handicap
- `course_info`: Course configuration with name, holes
- `validate`: Whether to perform validation (default: True)

**Raises:**
- `GameStateValidationError`: If initialization requirements not met

**Example:**
```python
players = [
    {"id": "p1", "name": "Alice", "handicap": 10},
    {"id": "p2", "name": "Bob", "handicap": 15},
    {"id": "p3", "name": "Charlie", "handicap": 8},
    {"id": "p4", "name": "Dana", "handicap": 12}
]

course = {
    "name": "Pebble Beach",
    "holes": [{"number": i, "par": 4, "yardage": 400} for i in range(1, 19)]
}

try:
    GameStateValidator.validate_game_initialization(players, course)
    print("✓ Game can be initialized")
except GameStateValidationError as e:
    print(f"✗ Cannot initialize: {e.message}")
```

### Hole State Transitions

```python
validate_hole_can_start(hole_number, current_hole, previous_hole_complete, validate=True)
```

Validates that a hole can be started.

**Parameters:**
- `hole_number`: Hole number to start (1-18)
- `current_hole`: Currently active hole (None if no active hole)
- `previous_hole_complete`: Whether previous hole is complete
- `validate`: Whether to perform validation

**Example:**
```python
# Starting hole 5
try:
    GameStateValidator.validate_hole_can_start(
        hole_number=5,
        current_hole=None,
        previous_hole_complete=True
    )
    # Start hole 5
    game.start_hole(5)
except GameStateValidationError as e:
    print(f"Cannot start hole: {e.message}")
```

### Shot Execution

```python
validate_shot_execution(player_id, next_player_to_hit, players, hole_complete, ball_positions, validate=True)
```

Validates a shot can be executed.

**Parameters:**
- `player_id`: Player attempting to hit
- `next_player_to_hit`: Player whose turn it is
- `players`: List of all player IDs in game
- `hole_complete`: Whether hole is already complete
- `ball_positions`: Current ball positions

**Example:**
```python
try:
    GameStateValidator.validate_shot_execution(
        player_id="p1",
        next_player_to_hit="p1",
        players=["p1", "p2", "p3", "p4"],
        hole_complete=False,
        ball_positions=game.get_ball_positions()
    )
    # Execute shot
    game.execute_shot(player_id="p1", shot_result=result)
except GameStateValidationError as e:
    print(f"Cannot execute shot: {e.message}")
```

### Partnership Formation

```python
validate_partnership_request(captain_id, partner_id, players, tee_shots_complete,
                            partnership_deadline_passed, current_team_type, validate=True)
```

Validates a partnership request can be made.

**Example:**
```python
try:
    GameStateValidator.validate_partnership_request(
        captain_id="p1",
        partner_id="p2",
        players=["p1", "p2", "p3", "p4"],
        tee_shots_complete=4,
        partnership_deadline_passed=False,
        current_team_type=None
    )
    # Send partnership request
    game.request_partnership("p1", "p2")
except PartnershipValidationError as e:
    print(f"Cannot request partnership: {e.message}")
```

### Partnership Response

```python
validate_partnership_response(partner_id, pending_request, validate=True)
```

Validates a partnership response.

**Example:**
```python
pending_request = game.get_pending_partnership_request()

try:
    GameStateValidator.validate_partnership_response(
        partner_id="p2",
        pending_request=pending_request
    )
    # Accept or reject
    game.respond_to_partnership("p2", accept=True)
except PartnershipValidationError as e:
    print(f"Cannot respond: {e.message}")
```

### Ball Position Validation

```python
validate_ball_position(player_id, distance_to_pin, lie_type, shot_count, players, validate=True)
```

Validates ball position data.

**Parameters:**
- `player_id`: Player who hit the ball
- `distance_to_pin`: Distance remaining to pin in yards
- `lie_type`: Type of lie ("tee", "fairway", "rough", "bunker", "green", "in_hole")
- `shot_count`: Number of shots taken
- `players`: List of valid player IDs

**Example:**
```python
try:
    GameStateValidator.validate_ball_position(
        player_id="p1",
        distance_to_pin=150.5,
        lie_type="fairway",
        shot_count=1,
        players=["p1", "p2", "p3", "p4"]
    )
    # Update ball position
    game.update_ball_position("p1", distance=150.5, lie="fairway")
except GameStateValidationError as e:
    print(f"Invalid ball position: {e.message}")
```

### Game Phase Transitions

```python
validate_game_phase_transition(current_phase, new_phase, hole_number, validate=True)
```

Validates game phase transition is valid.

**Parameters:**
- `current_phase`: Current game phase ("regular", "vinnie_variation", "hoepfinger")
- `new_phase`: Requested new phase
- `hole_number`: Current hole number

**Example:**
```python
try:
    GameStateValidator.validate_game_phase_transition(
        current_phase="regular",
        new_phase="vinnie_variation",
        hole_number=13
    )
    # Transition to Vinnie Variation
    game.set_phase("vinnie_variation")
except GameStateValidationError as e:
    print(f"Cannot transition: {e.message}")
```

### Hole Completion

```python
validate_hole_completion(ball_positions, players, validate=True) -> bool
```

Validates whether a hole can be marked complete.

**Returns:** True if hole is complete, False otherwise

**Example:**
```python
ball_positions = game.get_ball_positions()
players = game.get_player_ids()

if GameStateValidator.validate_hole_completion(ball_positions, players):
    print("✓ Hole is complete - all players holed out or conceded")
    game.complete_hole()
else:
    print("○ Hole still in progress")
```

## Usage Examples

### Complete Game Flow

```python
from app.validators import GameStateValidator
from app.validators.exceptions import GameStateValidationError, PartnershipValidationError

# 1. Initialize game
players = [
    {"id": f"p{i}", "name": f"Player {i}", "handicap": 10}
    for i in range(1, 5)
]
course = load_course("Pebble Beach")

try:
    GameStateValidator.validate_game_initialization(players, course)
    game = WolfGoatPigSimulation(players=players, course=course)
except GameStateValidationError as e:
    print(f"Cannot start game: {e.message}")
    return

# 2. Start first hole
try:
    GameStateValidator.validate_hole_can_start(
        hole_number=1,
        current_hole=None,
        previous_hole_complete=True
    )
    game.start_hole(1)
except GameStateValidationError as e:
    print(f"Cannot start hole: {e.message}")
    return

# 3. Execute tee shots
for player_id in game.get_hitting_order():
    try:
        GameStateValidator.validate_shot_execution(
            player_id=player_id,
            next_player_to_hit=game.get_next_player(),
            players=game.get_player_ids(),
            hole_complete=False,
            ball_positions=game.get_ball_positions()
        )

        result = game.simulate_shot(player_id)
        game.execute_shot(player_id, result)

    except GameStateValidationError as e:
        print(f"Cannot execute shot: {e.message}")
        break

# 4. Form partnerships
try:
    GameStateValidator.validate_partnership_request(
        captain_id="p1",
        partner_id="p2",
        players=game.get_player_ids(),
        tee_shots_complete=game.get_tee_shots_complete(),
        partnership_deadline_passed=game.is_partnership_deadline_passed(),
        current_team_type=game.get_team_type()
    )

    game.request_partnership("p1", "p2")

except PartnershipValidationError as e:
    print(f"Cannot form partnership: {e.message}")

# 5. Continue play until hole complete
while not game.is_hole_complete():
    next_player = game.get_next_player()

    try:
        GameStateValidator.validate_shot_execution(
            player_id=next_player,
            next_player_to_hit=next_player,
            players=game.get_player_ids(),
            hole_complete=False,
            ball_positions=game.get_ball_positions()
        )

        result = game.simulate_shot(next_player)
        game.execute_shot(next_player, result)

    except GameStateValidationError as e:
        print(f"Shot error: {e.message}")
        break

# 6. Validate hole completion
if GameStateValidator.validate_hole_completion(
    ball_positions=game.get_ball_positions(),
    players=game.get_player_ids()
):
    game.complete_hole()
    print("✓ Hole complete!")
```

### Defensive Programming Pattern

```python
def execute_player_action(game, player_id, action_type, **kwargs):
    """
    Execute player action with comprehensive validation.

    Returns: (success: bool, message: str, data: dict)
    """

    # Validate player exists
    try:
        GameStateValidator.validate_player_action(
            player_id=player_id,
            players=game.get_player_ids()
        )
    except GameStateValidationError as e:
        return False, e.message, {}

    # Route to specific action with validation
    if action_type == "execute_shot":
        try:
            GameStateValidator.validate_shot_execution(
                player_id=player_id,
                next_player_to_hit=game.get_next_player(),
                players=game.get_player_ids(),
                hole_complete=game.is_hole_complete(),
                ball_positions=game.get_ball_positions()
            )

            result = game.execute_shot(player_id, kwargs.get("shot_result"))
            return True, "Shot executed", result

        except GameStateValidationError as e:
            return False, e.message, {}

    elif action_type == "request_partnership":
        try:
            GameStateValidator.validate_partnership_request(
                captain_id=player_id,
                partner_id=kwargs.get("partner_id"),
                players=game.get_player_ids(),
                tee_shots_complete=game.get_tee_shots_complete(),
                partnership_deadline_passed=game.is_partnership_deadline_passed(),
                current_team_type=game.get_team_type()
            )

            result = game.request_partnership(player_id, kwargs.get("partner_id"))
            return True, "Partnership requested", result

        except PartnershipValidationError as e:
            return False, e.message, {}

    return False, f"Unknown action: {action_type}", {}
```

### Validation Summary for UI

```python
def get_available_actions(game):
    """Get summary of what actions are currently valid."""

    game_state = {
        "players": game.get_players(),
        "current_hole": game.get_current_hole(),
        "hole_state": {
            "hole_complete": game.is_hole_complete(),
            "tee_shots_complete": game.get_tee_shots_complete(),
            "partnership_deadline_passed": game.is_partnership_deadline_passed(),
            "next_player_to_hit": game.get_next_player()
        }
    }

    summary = GameStateValidator.get_validation_summary(game_state)

    return {
        "valid": summary["valid"],
        "errors": summary["errors"],
        "available_operations": summary["available_operations"],
        "can_execute_shot": "shot_available" in " ".join(summary["available_operations"]),
        "can_form_partnership": "partnership_window_open" in summary["available_operations"],
        "hole_in_progress": "hole_in_progress" in summary["available_operations"]
    }
```

## Error Handling

### Exception Types

- **GameStateValidationError**: General game state violations
- **PartnershipValidationError**: Partnership-specific violations
- **HandicapValidationError**: Handicap calculation errors

### Error Information

All validation errors include:
- `message`: Human-readable error description
- `field`: Field that failed validation (optional)
- `details`: Additional context dictionary (optional)

### Example Error Handling

```python
try:
    GameStateValidator.validate_partnership_request(
        captain_id="p1",
        partner_id="p1",  # Invalid: can't partner with self
        players=["p1", "p2", "p3", "p4"],
        tee_shots_complete=4,
        partnership_deadline_passed=False,
        current_team_type=None
    )
except PartnershipValidationError as e:
    print(f"Error: {e.message}")
    print(f"Field: {e.field}")
    print(f"Details: {e.details}")

    # Convert to API response
    error_response = e.to_dict()
    # Returns: {
    #   "error": "Captain cannot partner with themselves",
    #   "field": "partner_id",
    #   "details": {"captain_id": "p1", "partner_id": "p1"}
    # }
```

## Integration Patterns

### FastAPI Endpoint Integration

```python
from fastapi import HTTPException
from app.validators import GameStateValidator
from app.validators.exceptions import GameStateValidationError

@app.post("/game/{game_id}/action")
async def execute_action(
    game_id: str,
    action: ActionRequest
):
    game = get_game(game_id)

    try:
        if action.action_type == "EXECUTE_SHOT":
            GameStateValidator.validate_shot_execution(
                player_id=action.player_id,
                next_player_to_hit=game.get_next_player(),
                players=game.get_player_ids(),
                hole_complete=game.is_hole_complete(),
                ball_positions=game.get_ball_positions()
            )

            result = game.execute_shot(action.player_id, action.shot_result)
            return {"success": True, "result": result}

    except GameStateValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=e.to_dict()
        )
```

### Pre-Flight Validation

```python
def can_execute_action(game, player_id, action_type) -> tuple[bool, str]:
    """
    Check if action can be executed without actually executing it.

    Returns: (can_execute: bool, reason: str)
    """

    try:
        if action_type == "execute_shot":
            GameStateValidator.validate_shot_execution(
                player_id=player_id,
                next_player_to_hit=game.get_next_player(),
                players=game.get_player_ids(),
                hole_complete=game.is_hole_complete(),
                ball_positions=game.get_ball_positions()
            )
            return True, "Shot can be executed"

        elif action_type == "request_partnership":
            GameStateValidator.validate_partnership_request(
                captain_id=player_id,
                partner_id=None,  # Check window is open
                players=game.get_player_ids(),
                tee_shots_complete=game.get_tee_shots_complete(),
                partnership_deadline_passed=game.is_partnership_deadline_passed(),
                current_team_type=game.get_team_type()
            )
            return True, "Partnership can be requested"

    except (GameStateValidationError, PartnershipValidationError) as e:
        return False, e.message

    return False, "Unknown action type"
```

## Constants and Configuration

```python
# Available as class constants
GameStateValidator.REQUIRED_PLAYER_COUNT  # 4
GameStateValidator.TOTAL_HOLES  # 18
GameStateValidator.VALID_GAME_PHASES  # {"regular", "vinnie_variation", "hoepfinger"}
GameStateValidator.VALID_TEAM_TYPES  # {"partners", "solo", "aardvark_choice", "pending"}
GameStateValidator.VALID_LIE_TYPES  # {"tee", "fairway", "rough", "bunker", "green", "in_hole"}
GameStateValidator.MIN_DISTANCE  # 0.0
GameStateValidator.MAX_DISTANCE  # 700.0
GameStateValidator.MIN_HOLE_NUMBER  # 1
GameStateValidator.MAX_HOLE_NUMBER  # 18
GameStateValidator.MIN_PAR  # 3
GameStateValidator.MAX_PAR  # 6
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest app/validators/test_game_state_validator.py -v

# Run specific test class
pytest app/validators/test_game_state_validator.py::TestPartnershipValidation -v

# Run with coverage
pytest app/validators/test_game_state_validator.py --cov=app.validators.game_state_validator
```

## Best Practices

1. **Always validate before state changes**: Call validation methods before modifying game state
2. **Use validate=True by default**: Only set to False in testing scenarios
3. **Catch specific exceptions**: Distinguish between GameStateValidationError and PartnershipValidationError
4. **Provide user-friendly feedback**: Use the error message and details for UI messaging
5. **Pre-flight checks**: Use validation to enable/disable UI elements before user actions
6. **Log validation failures**: Track validation failures for debugging and analytics
7. **Test edge cases**: Write tests for boundary conditions and invalid states

## See Also

- `HandicapValidator` - Handicap calculation validation
- `BettingValidator` - Betting rules validation
- `exceptions.py` - Custom exception definitions
- Wolf Goat Pig game rules documentation
