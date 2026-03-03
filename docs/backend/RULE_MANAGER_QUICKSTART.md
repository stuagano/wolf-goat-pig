# RuleManager Quick Start Guide

## Installation

The RuleManager is already integrated into the Wolf Goat Pig backend. No installation needed.

## Basic Usage

```python
from app.managers import RuleManager, RuleViolationError

# Get singleton instance
manager = RuleManager.get_instance()
```

## Common Use Cases

### 1. Check if Partnership Can Be Formed

```python
try:
    can_form = manager.can_form_partnership(
        captain_id="player_1",
        partner_id="player_2",
        game_state=current_state
    )
    if can_form:
        # Form partnership
        print("Partnership allowed!")
except RuleViolationError as e:
    print(f"Cannot form partnership: {e.message}")
```

### 2. Validate Player's Turn

```python
try:
    manager.validate_player_turn(player_id, game_state)
    # Player can take action
except RuleViolationError as e:
    print(f"Not your turn: {e.message}")
```

### 3. Get Available Actions for Player

```python
actions = manager.get_valid_actions(player_id, game_state)

# Example output: ['hit_shot', 'double', 'go_lone_wolf']
for action in actions:
    print(f"- {action}")
```

### 4. Check Betting Actions

```python
# Check if can double
try:
    if manager.can_double(player_id, game_state):
        # Show double button
        pass
except RuleViolationError as e:
    # Hide double button
    pass

# Check if can invoke Duncan
try:
    if manager.can_duncan(player_id, game_state):
        # Show Duncan option
        pass
except RuleViolationError as e:
    pass
```

### 5. Calculate Hole Winner

```python
# Net scores for each player
hole_results = {
    "player_1": 4,
    "player_2": 5,
    "player_3": 4
}

winner = manager.calculate_hole_winner(hole_results)

if winner:
    print(f"Winner: {winner}")
else:
    print("Hole tied - carry over!")
```

### 6. Apply Handicap Strokes

```python
player_handicaps = {
    "player_1": 18.0,
    "player_2": 10.0,
    "player_3": 5.0
}

# Hole 1, stroke index 5
strokes = manager.apply_handicap_strokes(
    hole_number=1,
    player_handicaps=player_handicaps,
    hole_stroke_index=5
)

# Result: {'player_1': 1, 'player_2': 1, 'player_3': 0}
print(f"Strokes received: {strokes}")
```

### 7. Get Rule Summary

```python
summary = manager.get_rule_summary()

print("Partnership Rules:")
print(summary["partnership"])

print("\nBetting Rules:")
print(summary["betting"])
```

## Error Handling

```python
from app.managers import RuleViolationError

try:
    manager.can_form_partnership(captain, partner, state)
except RuleViolationError as e:
    # Access error information
    error_message = e.message
    error_field = e.field
    error_details = e.details

    # Convert to dict for API response
    error_dict = e.to_dict()
    # Returns: {
    #   "error": "Cannot partner with yourself",
    #   "field": "partnership",
    #   "details": {...}
    # }
```

## API Integration Example

```python
from fastapi import HTTPException
from app.managers import RuleManager, RuleViolationError

@app.post("/api/game/{game_id}/partnership")
async def form_partnership(
    game_id: str,
    captain_id: str,
    partner_id: str
):
    manager = RuleManager.get_instance()

    try:
        # Get current game state
        game_state = get_game_state(game_id)

        # Validate partnership
        if manager.can_form_partnership(captain_id, partner_id, game_state):
            # Create partnership
            create_partnership(game_id, captain_id, partner_id)
            return {"status": "success"}

    except RuleViolationError as e:
        raise HTTPException(
            status_code=400,
            detail=e.to_dict()
        )
```

## Frontend Integration Example

```javascript
// Get valid actions for current player
async function getPlayerActions(gameId, playerId) {
  const response = await fetch(
    `/api/game/${gameId}/actions?player_id=${playerId}`
  );
  const actions = await response.json();

  // actions = ['hit_shot', 'double', 'form_partnership']

  // Show/hide UI buttons based on valid actions
  document.getElementById('double-btn').style.display =
    actions.includes('double') ? 'block' : 'none';

  document.getElementById('partnership-btn').style.display =
    actions.includes('form_partnership') ? 'block' : 'none';
}

// Attempt an action
async function formPartnership(gameId, captainId, partnerId) {
  try {
    const response = await fetch(`/api/game/${gameId}/partnership`, {
      method: 'POST',
      body: JSON.stringify({ captain_id: captainId, partner_id: partnerId }),
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      const error = await response.json();
      alert(`Cannot form partnership: ${error.error}`);
    }
  } catch (err) {
    console.error('Partnership failed:', err);
  }
}
```

## Testing

```python
def test_partnership_rules():
    manager = RuleManager.get_instance()

    # Create test game state
    game_state = {
        "players": [
            {"id": "p1", "handicap": 10.0},
            {"id": "p2", "handicap": 15.0}
        ],
        "current_hole": {
            "hitting_order": ["p1", "p2"],
            "teams": {},
            "tee_shots_complete": 0,
            # ... other fields
        }
    }

    # Test valid partnership
    assert manager.can_form_partnership("p1", "p2", game_state)

    # Test invalid partnership (self)
    try:
        manager.can_form_partnership("p1", "p1", game_state)
        assert False, "Should have raised RuleViolationError"
    except RuleViolationError:
        pass  # Expected
```

## Quick Reference

### Methods that return `bool`
- `can_form_partnership()` - Can captain form partnership?
- `can_go_lone_wolf()` - Can captain go solo?
- `can_double()` - Can player double wager?
- `can_redouble()` - Can player redouble?
- `can_duncan()` - Can captain invoke Duncan?
- `validate_player_turn()` - Is it player's turn?

### Methods that return data
- `get_valid_actions()` - Returns `List[str]` of actions
- `calculate_hole_winner()` - Returns `Optional[str]` winner ID
- `apply_handicap_strokes()` - Returns `Dict[str, int]` strokes
- `get_rule_summary()` - Returns `Dict[str, Any]` rules

### All methods may raise
- `RuleViolationError` - When rule is violated

## Constants

```python
RuleManager.MIN_PLAYERS = 2
RuleManager.MAX_PLAYERS = 6
RuleManager.HOLES_PER_ROUND = 18
RuleManager.BASE_WAGER_QUARTERS = 1
RuleManager.MAX_DOUBLE_MULTIPLIER = 8
```

## Tips

1. **Always catch `RuleViolationError`** - All validation methods may raise this
2. **Use `get_valid_actions()`** - Easier than checking each action individually
3. **Singleton pattern** - Always use `get_instance()`, don't create new instances
4. **Check before modifying state** - Validate actions before updating game state
5. **Log violations** - Use error details for debugging and analytics

## Game State Requirements

Minimum required fields in game_state:

```python
{
    "players": [{"id": str, "handicap": float}, ...],
    "current_hole": {
        "hole_number": int,
        "hitting_order": [str, ...],
        "teams": dict,
        "betting": {
            "doubled": bool,
            "redoubled": bool,
            "duncan_invoked": bool
        },
        "tee_shots_complete": int,
        "partnership_deadline_passed": bool,
        "wagering_closed": bool,
        "hole_complete": bool,
        "balls_in_hole": [str, ...],
        "next_player_to_hit": str
    }
}
```

## Need Help?

- See full documentation: `backend/app/managers/README.md`
- Run tests: `python3 backend/test_rule_manager.py`
- Check validators: `backend/app/validators/`
