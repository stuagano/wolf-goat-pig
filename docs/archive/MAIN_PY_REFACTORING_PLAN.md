# main.py Refactoring Plan - Logic Extraction

**Date:** November 3, 2025
**Purpose:** Replace embedded logic in main.py with extracted service/manager methods
**Status:** Methods extracted, ready to refactor main.py

---

## Extraction Summary

All 10 methods have been successfully added to their target services/managers. Now we need to update main.py to use them.

### Methods Added:

#### ScoringManager (1 method)
✅ `award_concession_points(game_state, conceding_player, conceding_team, hole_number)`

#### RuleManager (6 methods)
✅ `apply_joes_special(game_state, hole_number, selected_value)`
✅ `check_betting_opportunities(game_state, hole_number, last_shot)`
✅ `apply_option(game_state, captain_id, hole_number)`
✅ `get_available_partners(game_state, captain_id, hole_number)`
✅ `are_partnerships_formed(game_state, hole_number)`
✅ `validate_can_double(player_id, game_state)`

#### HandicapValidator (2 methods)
✅ `validate_and_normalize_handicap(handicap, player_name)`
✅ `calculate_strength_from_handicap(handicap)`

#### GameStateValidator (1 method)
✅ `validate_player_count(player_count)` - Updated to enforce 4-6 players only

---

## Refactoring Tasks for main.py

### Task 1: Player Initialization Logic (Lines 1768-1800)

**Current code:**
```python
# Validate player count (support 4, 5, 6 players)
if len(players) not in [4, 5, 6]:
    raise HTTPException(status_code=400, detail="4, 5, or 6 players required.")

# Process each player
for player in players:
    # REFACTORED: Using HandicapValidator for validation
    if "handicap" not in player:
        player["handicap"] = 18.0
        logger.warning(f"Player {player['name']} missing handicap, using default 18.0")

    try:
        player["handicap"] = float(player["handicap"])
        HandicapValidator.validate_handicap(player["handicap"])
    except (ValueError, TypeError):
        logger.warning(f"Invalid handicap for {player['name']}, using 18.0")
        player["handicap"] = 18.0
    except HandicapValidationError as e:
        logger.warning(f"Handicap validation failed for {player['name']}: {e}, using 18.0")
        player["handicap"] = 18.0

    if "strength" not in player:
        player["strength"] = max(1, 10 - int(player["handicap"]))
```

**Refactored code:**
```python
# Validate player count using GameStateValidator
GameStateValidator.validate_player_count(len(players))

# Process each player
for player in players:
    # Validate and normalize handicap
    player["handicap"] = HandicapValidator.validate_and_normalize_handicap(
        player.get("handicap"),
        player_name=player.get("name")
    )

    # Calculate strength from handicap
    if "strength" not in player:
        player["strength"] = HandicapValidator.calculate_strength_from_handicap(
            player["handicap"]
        )
```

**Lines to change:** 1768-1800

---

### Task 2: Partnership Timing Logic (Lines 2054-2106)

**Current code:**
```python
# REFACTORED: Partnership timing validation
# Count how many tee shots have been completed
tee_shots_completed = sum(1 for player_id, ball in hole_state.ball_positions.items()
                        if ball and ball.shot_count >= 1)

# Partnership decision point: After captain and at least one other player have hit
if tee_shots_completed >= 2:
    rule_mgr = RuleManager.get_instance()
    current_game_state = game.get_game_state()

    available_partners = []
    for player in game.players:
        if player.id != captain_id and hole_state.can_request_partnership(captain_id, player.id):
            try:
                if rule_mgr.can_form_partnership(captain_id, player.id, current_game_state):
                    if player.id in hole_state.ball_positions and hole_state.ball_positions[player.id]:
                        partner_ball = hole_state.ball_positions[player.id]
                        available_partners.append({
                            "id": player.id,
                            "name": player.name,
                            "handicap": player.handicap,
                            "tee_shot_distance": partner_ball.distance_to_pin,
                            "tee_shot_quality": getattr(partner_ball, 'last_shot_quality', 'unknown')
                        })
            except RuleViolationError:
                pass
```

**Refactored code:**
```python
# Get available partners using RuleManager
rule_mgr = RuleManager.get_instance()
available_partners = rule_mgr.get_available_partners(
    game_state=game.get_game_state(),
    captain_id=captain_id,
    hole_number=game.current_hole
)
```

**Lines to change:** 2054-2106

---

### Task 3: Betting Opportunities Detection (Lines 2147-2218)

**Current code:**
```python
# Check for betting opportunities during hole play (doubles/flushes)
if not hole_state.wagering_closed and hole_state.teams.type in ["partners", "solo"]:
    recent_shots = []
    for player_id, ball in hole_state.ball_positions.items():
        if ball and ball.shot_count > 0:
            player_name = game._get_player_name(player_id)
            recent_shots.append(f"{player_name}: {ball.distance_to_pin:.0f}yd ({ball.shot_count} shots)")

    should_offer_betting = False
    betting_context = []

    if shot_response and "shot_result" in shot_response:
        last_shot = shot_response["shot_result"]
        player_name = game._get_player_name(last_shot["player_id"])

        if last_shot["shot_quality"] == "excellent" and last_shot["distance_to_pin"] < 50:
            should_offer_betting = True
            betting_context.append(f"🎯 {player_name} hit an excellent shot to {last_shot['distance_to_pin']:.0f} yards!")
        elif last_shot["shot_quality"] == "terrible" and last_shot["shot_number"] <= 3:
            should_offer_betting = True
            betting_context.append(f"😬 {player_name} struggling after terrible shot")
```

**Refactored code:**
```python
# Check for betting opportunities using RuleManager
rule_mgr = RuleManager.get_instance()
betting_check = rule_mgr.check_betting_opportunities(
    game_state=game.get_game_state(),
    hole_number=game.current_hole,
    last_shot=shot_response.get("shot_result") if shot_response else None
)

if betting_check["should_offer"]:
    # Add betting action to available_actions
    available_actions.append(betting_check["action"])
```

**Lines to change:** 2147-2218

---

### Task 4: Joe's Special Handler (Lines 2792-2821)

**Current code:**
```python
async def handle_joes_special(game: WolfGoatPigSimulation, payload: Dict[str, Any]) -> ActionResponse:
    """Handle Joe's Special wager selection in Hoepfinger"""
    try:
        selected_value = payload.get("selected_value", 2)

        # Apply Joe's Special value to current hole betting
        hole_state = game.hole_states[game.current_hole]
        hole_state.betting.joes_special_value = selected_value
        hole_state.betting.base_wager = selected_value
        hole_state.betting.current_wager = selected_value
```

**Refactored code:**
```python
async def handle_joes_special(game: WolfGoatPigSimulation, payload: Dict[str, Any]) -> ActionResponse:
    """Handle Joe's Special wager selection in Hoepfinger"""
    try:
        selected_value = payload.get("selected_value", 2)

        # Apply Joe's Special using RuleManager
        rule_mgr = RuleManager.get_instance()
        rule_mgr.apply_joes_special(
            game_state=game.get_game_state(),
            hole_number=game.current_hole,
            selected_value=selected_value
        )
```

**Lines to change:** 2792-2821

---

### Task 5: Partnership Check Helper (Lines 3032-3066)

**Current code:**
```python
def _check_partnerships_formed(game: WolfGoatPigSimulation) -> bool:
    """
    DEPRECATED: Legacy helper function for partnership validation.
    ...
    """
    try:
        game_state = game.game_state if hasattr(game, 'game_state') else None
        if not game_state:
            return False

        hole_state = game_state.hole_states.get(game_state.current_hole)
        if not hole_state:
            return False

        teams_type = getattr(hole_state.teams, 'type', 'pending')
        partnerships_formed = teams_type in ['partners', 'solo']
        return partnerships_formed
    except Exception as e:
        logger.error(f"Error checking partnerships: {e}")
        return False
```

**Refactored code:**
```python
# REMOVE ENTIRE FUNCTION

# Replace all calls like:
# partnerships_formed = _check_partnerships_formed(game)
#
# With:
# rule_mgr = RuleManager.get_instance()
# partnerships_formed = rule_mgr.are_partnerships_formed(
#     game_state=game.get_game_state(),
#     hole_number=game.current_hole
# )
```

**Action:** DELETE lines 3032-3066, update all call sites

---

### Task 6: Float Validation (Lines 3092-3099)

**Current code:**
```python
# Additional validation: Check if captain can double (Float is a type of double)
rule_mgr = RuleManager.get_instance()
full_game_state = game.get_game_state()
if not rule_mgr.can_double(captain_id, full_game_state):
    raise HTTPException(
        status_code=400,
        detail="Cannot invoke Float at this time"
    )
```

**Refactored code:**
```python
# Validate captain can double (Float is a type of double)
rule_mgr = RuleManager.get_instance()
try:
    rule_mgr.validate_can_double(captain_id, game.get_game_state())
except RuleViolationError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

**Lines to change:** 3092-3099

---

### Task 7: Option Toggle Handler (Lines 3156-3163)

**Current code:**
```python
# Toggle the option (for now, just update state - full implementation TBD)
# The Option automatically doubles wager when captain is losing
hole_state = game_state.hole_states[game_state.current_hole]

# Toggle option_active flag
current_option = getattr(hole_state.betting, 'option_active', False)
hole_state.betting.option_active = not current_option
```

**Refactored code:**
```python
# Apply The Option using RuleManager (FULL IMPLEMENTATION)
rule_mgr = RuleManager.get_instance()
rule_mgr.apply_option(
    game_state=game_state,
    captain_id=captain_id,
    hole_number=game_state.current_hole
)
```

**Lines to change:** 3156-3163

---

### Task 8: Concession Points Award (Lines 3238-3271)

**Current code:**
```python
# Mark hole as completed with concession
hole_state.status = "completed"
hole_state.conceded = True
hole_state.conceding_player = player_id if player_id is not None else team_id

# Determine winners based on team structure
if hole_state.teams.type == "partners":
    if team_id == 1:
        for pid in hole_state.teams.team2 or []:
            player = next((p for p in game_state.player_manager.players if p.id == pid), None)
            if player:
                player.points += hole_state.betting.current_wager or 1
    else:
        for pid in hole_state.teams.team1 or []:
            player = next((p for p in game_state.player_manager.players if p.id == pid), None)
            if player:
                player.points += hole_state.betting.current_wager or 1
elif hole_state.teams.type == "solo":
    solo_player = hole_state.teams.solo_player
    if player_id == solo_player:
        for pid in hole_state.teams.team1 or []:
            player = next((p for p in game_state.player_manager.players if p.id == pid), None)
            if player:
                player.points += hole_state.betting.current_wager or 1
    else:
        player = next((p for p in game_state.player_manager.players if p.id == solo_player), None)
        if player:
            player.points += (hole_state.betting.current_wager or 1) * 2
```

**Refactored code:**
```python
# Award concession points using ScoringManager
scoring_mgr = get_scoring_manager()
points_awarded = scoring_mgr.award_concession_points(
    game_state=game_state,
    conceding_player=player_id,
    conceding_team=team_id,
    hole_number=game_state.current_hole
)
```

**Lines to change:** 3238-3271

---

## Search and Replace for _check_partnerships_formed()

Need to find all call sites and replace:

**Search pattern:**
```python
_check_partnerships_formed(game)
```

**Replace with:**
```python
RuleManager.get_instance().are_partnerships_formed(game.get_game_state(), game.current_hole)
```

---

## Benefits After Refactoring

1. **Reduced main.py size**: ~200 lines removed
2. **Centralized logic**: All business logic in services/managers
3. **Better testability**: Logic can be unit tested without FastAPI
4. **Improved maintainability**: Single source of truth for rules
5. **Type safety**: Contract validation via Protocols
6. **Complete implementations**: Option logic fully implemented

---

## Testing Strategy

After refactoring, test:
1. Game initialization with various player counts
2. Partnership formation timing
3. Betting opportunities (doubles/flushes)
4. Joe's Special wager selection
5. Float invocation
6. The Option auto-doubling
7. Hole concession with points award
8. Invalid handicap handling

---

## Rollback Plan

If issues arise:
1. Git has the original code
2. New methods don't change existing behavior
3. Can revert main.py changes while keeping new methods
4. All new methods are additive (no breaking changes)

---

**Next Step:** Update main.py with all refactorings
