# Embedded Logic Analysis - Wolf Goat Pig

**Date:** November 3, 2025
**Purpose:** Identify embedded business logic in main.py that should be extracted to services/managers
**Status:** Analysis Complete - 11 Items Found

---

## Executive Summary

Found **11 distinct pieces of embedded business logic** in main.py (8300 lines) that violate separation of concerns and should be extracted to appropriate services/managers.

**Impact:**
- 11 code sections with business logic mixed into endpoint handlers
- Estimated 200+ lines of logic that should be in services/managers
- Several incomplete implementations noted with "TBD" comments
- Some deprecated helpers that should be fully removed

**Priority:** Medium-High (code works but is harder to maintain and test)

---

## Findings by Category

### 1. SCORING LOGIC (1 item) → ScoringManager

#### 1.1 Flush (Concession) Points Award Logic
**Location:** `main.py:3238-3271`
**Priority:** High
**Complexity:** Medium

**What it does:**
Awards points to winning team(s) based on hole concession, with special multipliers for solo players. Includes logic for partners mode vs solo mode point distribution.

**Current implementation:**
```python
# Mark hole as completed with concession
hole_state.status = "completed"
hole_state.conceded = True
hole_state.conceding_player = player_id if player_id is not None else team_id

# Determine winners based on team structure
if hole_state.teams.type == "partners":
    # In partners mode, one team concedes, the other wins
    if team_id == 1:
        # Team 1 conceded, Team 2 wins
        for pid in hole_state.teams.team2 or []:
            player = next((p for p in game_state.player_manager.players if p.id == pid), None)
            if player:
                player.points += hole_state.betting.current_wager or 1
    else:
        # Team 2 conceded, Team 1 wins
        for pid in hole_state.teams.team1 or []:
            player = next((p for p in game_state.player_manager.players if p.id == pid), None)
            if player:
                player.points += hole_state.betting.current_wager or 1
elif hole_state.teams.type == "solo":
    # In solo mode, if solo player concedes, the other team wins
    solo_player = hole_state.teams.solo_player
    if player_id == solo_player:
        # Solo player conceded, partners win
        for pid in hole_state.teams.team1 or []:
            player = next((p for p in game_state.player_manager.players if p.id == pid), None)
            if player:
                player.points += hole_state.betting.current_wager or 1
    else:
        # Partner(s) conceded, solo player wins
        player = next((p for p in game_state.player_manager.players if p.id == solo_player), None)
        if player:
            player.points += (hole_state.betting.current_wager or 1) * 2  # Solo gets double
```

**Should be:**
```python
# In main.py handler:
scoring_mgr = get_scoring_manager()
scoring_mgr.award_concession_points(
    game_state=game_state,
    conceding_player=player_id,
    conceding_team=team_id,
    hole_number=game_state.current_hole
)
```

**Extraction target:** `ScoringManager.award_concession_points()`

---

### 2. HANDICAP LOGIC (2 items) → HandicapValidator

#### 2.1 Strength Calculation from Handicap
**Location:** `main.py:1798-1800`
**Priority:** Medium
**Complexity:** Low

**What it does:**
Derives player strength from handicap using formula: `max(1, 10 - handicap)`

**Current implementation:**
```python
if "strength" not in player:
    # Default strength based on handicap (lower handicap = higher strength)
    player["strength"] = max(1, 10 - int(player["handicap"]))
```

**Should be:**
```python
# In main.py:
player["strength"] = HandicapValidator.calculate_strength_from_handicap(player["handicap"])
```

**Extraction target:** `HandicapValidator.calculate_strength_from_handicap()`

---

#### 2.2 Handicap Validation and Defaulting
**Location:** `main.py:1779-1793`
**Priority:** High
**Complexity:** Low

**What it does:**
Validates handicap values, converts to float, applies defaults, with error handling

**Current implementation:**
```python
# REFACTORED: Using HandicapValidator for validation
if "handicap" not in player:
    player["handicap"] = 18.0  # Default handicap
    logger.warning(f"Player {player['name']} missing handicap, using default 18.0")

# Ensure handicap is numeric and valid
try:
    player["handicap"] = float(player["handicap"])
    # Validate handicap range using HandicapValidator
    HandicapValidator.validate_handicap(player["handicap"])
except (ValueError, TypeError):
    logger.warning(f"Invalid handicap for {player['name']}, using 18.0")
    player["handicap"] = 18.0
except HandicapValidationError as e:
    logger.warning(f"Handicap validation failed for {player['name']}: {e}, using 18.0")
    player["handicap"] = 18.0
```

**Should be:**
```python
# In main.py:
player["handicap"] = HandicapValidator.validate_and_normalize_handicap(
    player.get("handicap"),
    player_name=player["name"]
)
```

**Extraction target:** `HandicapValidator.validate_and_normalize_handicap()`

---

### 3. BETTING LOGIC (3 items) → RuleManager/BettingValidator

#### 3.1 Joe's Special Wager Selection Logic
**Location:** `main.py:2792-2821`
**Priority:** High
**Complexity:** Medium

**What it does:**
Directly mutates betting state to set wager values for special Hoepfinger variant

**Current implementation:**
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

**Should be:**
```python
# In main.py handler:
rule_mgr = RuleManager.get_instance()
rule_mgr.apply_joes_special(
    game_state=game.get_game_state(),
    hole_number=game.current_hole,
    selected_value=selected_value
)
```

**Extraction target:** `RuleManager.apply_joes_special()`

---

#### 3.2 Double/Flush Opportunity Detection
**Location:** `main.py:2147-2218`
**Priority:** High
**Complexity:** High

**What it does:**
Determines when to offer doubles/flushes based on shot quality and position analysis

**Current implementation:**
```python
# Check for betting opportunities during hole play (doubles/flushes)
if not hole_state.wagering_closed and hole_state.teams.type in ["partners", "solo"]:
    # Get the recent shot context for betting decisions
    recent_shots = []
    for player_id, ball in hole_state.ball_positions.items():
        if ball and ball.shot_count > 0:
            player_name = game._get_player_name(player_id)
            recent_shots.append(f"{player_name}: {ball.distance_to_pin:.0f}yd ({ball.shot_count} shots)")

    # Check if there's a compelling reason to double (great shot, bad position, etc.)
    should_offer_betting = False
    betting_context = []

    # Look for recent excellent or terrible shots that create betting opportunities
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

**Should be:**
```python
# In main.py handler:
rule_mgr = RuleManager.get_instance()
betting_opportunity = rule_mgr.check_betting_opportunities(
    game_state=game.get_game_state(),
    hole_number=game.current_hole,
    last_shot=shot_response.get("shot_result")
)

if betting_opportunity["should_offer"]:
    # Add betting actions with context
    available_actions.append(betting_opportunity["action"])
```

**Extraction target:** `RuleManager.check_betting_opportunities()`

---

#### 3.3 Option Auto-Double Logic (INCOMPLETE)
**Location:** `main.py:3156-3163`
**Priority:** High
**Complexity:** Medium

**What it does:**
Toggle option_active flag with comment noting "The Option automatically doubles wager when captain is losing" but implementation incomplete

**Current implementation:**
```python
# Toggle the option (for now, just update state - full implementation TBD)
# The Option automatically doubles wager when captain is losing
hole_state = game_state.hole_states[game_state.current_hole]

# Toggle option_active flag
current_option = getattr(hole_state.betting, 'option_active', False)
hole_state.betting.option_active = not current_option
```

**Should be:**
```python
# In main.py handler:
rule_mgr = RuleManager.get_instance()
rule_mgr.apply_option(
    game_state=game_state,
    captain_id=captain_id,
    hole_number=game_state.current_hole
)
```

**Extraction target:** `RuleManager.apply_option()` (needs full implementation)

---

### 4. PARTNERSHIP TIMING LOGIC (2 items) → RuleManager

#### 4.1 Partnership Decision Timing Validation
**Location:** `main.py:2054-2106`
**Priority:** High
**Complexity:** High

**What it does:**
Validates when partnership decisions can be offered based on number of tee shots completed and uses RuleManager for validation

**Current implementation:**
```python
# REFACTORED: Partnership timing validation
# Real Wolf-Goat-Pig timing: Partnership decision comes AFTER shots are hit
# Count how many tee shots have been completed
tee_shots_completed = sum(1 for player_id, ball in hole_state.ball_positions.items()
                        if ball and ball.shot_count >= 1)

# Partnership decision point: After captain and at least one other player have hit
# RuleManager validates partnership formation timing rules
if tee_shots_completed >= 2:
    # REFACTORED: Using RuleManager for partnership validation
    # Get available partners based on timing rules
    rule_mgr = RuleManager.get_instance()
    current_game_state = game.get_game_state()

    available_partners = []
    for player in game.players:
        # Use both hole state check and RuleManager validation
        if player.id != captain_id and hole_state.can_request_partnership(captain_id, player.id):
            # Validate partnership using RuleManager
            try:
                if rule_mgr.can_form_partnership(captain_id, player.id, current_game_state):
                    # Only show players who have already hit their tee shot
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
                # Partnership not allowed, skip this player
                pass
```

**Should be:**
```python
# In main.py handler:
rule_mgr = RuleManager.get_instance()
available_partners = rule_mgr.get_available_partners(
    game_state=game.get_game_state(),
    captain_id=captain_id,
    hole_number=game.current_hole
)
```

**Extraction target:** `RuleManager.get_available_partners()`

---

#### 4.2 Partnership Check Helper (DEPRECATED)
**Location:** `main.py:3032-3066`
**Priority:** High
**Complexity:** Low

**What it does:**
Checks if partnerships have been formed by examining hole state teams type. Already marked DEPRECATED.

**Current implementation:**
```python
def _check_partnerships_formed(game: WolfGoatPigSimulation) -> bool:
    """
    DEPRECATED: Legacy helper function for partnership validation.

    This function is maintained for backward compatibility but should not be used
    for new code. Use RuleManager.can_form_partnership() or check game state directly.

    Check if partnerships have been formed on the current hole.
    Returns True if teams.type is 'partners' or 'solo', False if 'pending'.
    """
    try:
        game_state = game.game_state if hasattr(game, 'game_state') else None

        if not game_state:
            logger.warning("No active game state found when checking partnerships")
            return False

        hole_state = game_state.hole_states.get(game_state.current_hole)
        if not hole_state:
            logger.warning(f"No hole state found for hole {game_state.current_hole}")
            return False

        # Partnerships are formed if teams.type is 'partners' or 'solo' (not 'pending')
        teams_type = getattr(hole_state.teams, 'type', 'pending')
        partnerships_formed = teams_type in ['partners', 'solo']

        logger.info(f"Partnership check: teams.type={teams_type}, partnerships_formed={partnerships_formed}")
        return partnerships_formed

    except Exception as e:
        logger.error(f"Error checking partnerships: {e}")
        return False
```

**Should be:**
```python
# Remove entire function and replace all calls with:
rule_mgr = RuleManager.get_instance()
partnerships_formed = rule_mgr.are_partnerships_formed(game_state, hole_number)
```

**Extraction target:** Remove function, add `RuleManager.are_partnerships_formed()`

---

### 5. VALIDATION LOGIC (2 items) → GameStateValidator/RuleManager

#### 5.1 Player Count Validation
**Location:** `main.py:1768-1770`
**Priority:** Medium
**Complexity:** Low

**What it does:**
Validates that 4, 5, or 6 players are present

**Current implementation:**
```python
# Validate player count (support 4, 5, 6 players)
if len(players) not in [4, 5, 6]:
    raise HTTPException(status_code=400, detail="4, 5, or 6 players required.")
```

**Should be:**
```python
# In main.py:
GameStateValidator.validate_player_count(len(players))
```

**Extraction target:** `GameStateValidator.validate_player_count()`

---

#### 5.2 Float Invocation Validation
**Location:** `main.py:3092-3099`
**Priority:** Medium
**Complexity:** Low

**What it does:**
Validates if captain can double (Float is a type of double)

**Current implementation:**
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

**Should be:**
```python
# In main.py:
rule_mgr = RuleManager.get_instance()
rule_mgr.validate_can_double(captain_id, game.get_game_state())  # Raises RuleViolationError
```

**Extraction target:** `RuleManager.validate_can_double()` (raises exception instead of returning bool)

---

### 6. ACTION ROUTING (1 item) → Strategy Pattern

#### 6.1 Action Type Dispatch Routing
**Location:** `main.py:1688-1749`
**Priority:** Low
**Complexity:** High

**What it does:**
Routes action types to appropriate handlers using if/elif chain (20+ branches)

**Current implementation:**
```python
# Route to appropriate handler based on action type
# All handlers now receive the game instance instead of using global wgp_simulation
if action_type == "INITIALIZE_GAME":
    return await handle_initialize_game(game, payload)
elif action_type == "PLAY_SHOT":
    return await handle_play_shot(game, payload)
elif action_type == "REQUEST_PARTNERSHIP":
    return await handle_request_partnership(game, payload)
# ... 20+ more elif branches
elif action_type == "CALCULATE_HOLE_POINTS":
    # Handle calculate points action from frontend
    action_dict = action.model_dump() if hasattr(action, 'model_dump') else action.dict()
    return await handle_calculate_hole_points(game, action_dict)
else:
    raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")
```

**Should be:**
```python
# In main.py:
from .action_handlers import ActionHandlerRegistry

handler_registry = ActionHandlerRegistry.get_instance()
handler = handler_registry.get_handler(action_type)
return await handler(game, payload)
```

**Extraction target:** New `ActionHandlerRegistry` class with handler registration

**Note:** This is lower priority as it's more of an architectural improvement than business logic extraction.

---

## Extraction Plan

### Phase 1: High Priority Scoring & Betting Logic (Items 1, 3.1, 3.2, 3.3)

**Target:** ScoringManager + RuleManager
**Estimated effort:** 4-6 hours
**Impact:** High - removes most complex embedded logic

**Steps:**
1. Add `award_concession_points()` to ScoringManager
2. Add `apply_joes_special()` to RuleManager
3. Add `check_betting_opportunities()` to RuleManager
4. Add `apply_option()` to RuleManager (complete implementation)
5. Update main.py handlers to use new methods
6. Test all betting scenarios

---

### Phase 2: Handicap Validation Logic (Items 2.1, 2.2)

**Target:** HandicapValidator
**Estimated effort:** 1-2 hours
**Impact:** Medium - improves validation consistency

**Steps:**
1. Add `calculate_strength_from_handicap()` to HandicapValidator
2. Add `validate_and_normalize_handicap()` to HandicapValidator
3. Update main.py initialization code
4. Test with various handicap inputs

---

### Phase 3: Partnership Logic (Items 4.1, 4.2)

**Target:** RuleManager
**Estimated effort:** 2-3 hours
**Impact:** High - removes deprecated code

**Steps:**
1. Add `get_available_partners()` to RuleManager
2. Add `are_partnerships_formed()` to RuleManager
3. Remove `_check_partnerships_formed()` function
4. Update all calls in main.py
5. Test partnership formation flows

---

### Phase 4: Validation Logic (Items 5.1, 5.2)

**Target:** GameStateValidator + RuleManager
**Estimated effort:** 1 hour
**Impact:** Low - minor cleanup

**Steps:**
1. Add `validate_player_count()` to GameStateValidator
2. Add `validate_can_double()` to RuleManager
3. Update main.py handlers
4. Test validation edge cases

---

### Phase 5 (Optional): Action Routing (Item 6.1)

**Target:** New ActionHandlerRegistry
**Estimated effort:** 4-6 hours
**Impact:** Low - architectural improvement

**Steps:**
1. Create `action_handlers.py` with registry pattern
2. Register all 20+ handlers
3. Update main.py to use registry
4. Test all action types

**Note:** This is optional and can be deferred.

---

## Benefits of Extraction

### Testability
- Business logic can be unit tested without FastAPI infrastructure
- Easier to test edge cases in isolation
- Faster test execution

### Maintainability
- Single responsibility: handlers orchestrate, services/managers contain logic
- Easier to find and modify business rules
- Reduced code duplication

### Reusability
- Logic can be reused across different endpoints
- Services can be used by background jobs, CLI tools, etc.

### Type Safety
- Contract validation via Protocols
- Better IDE support for method discovery
- Type checking catches interface violations

---

## Priority Matrix

```
High Business Value + High Technical Complexity:
- Betting opportunity detection (3.2)
- Partnership timing validation (4.1)

High Business Value + Medium Technical Complexity:
- Concession points (1.1)
- Joe's Special (3.1)
- Option logic (3.3)

Medium Business Value + Low Technical Complexity:
- Handicap validation (2.1, 2.2)
- Partnership check (4.2)
- Player count validation (5.1)
- Float validation (5.2)

Low Business Value + High Technical Complexity:
- Action routing (6.1) - optional
```

---

## Risks & Mitigation

### Risk 1: Breaking Existing Behavior
**Mitigation:**
- Extract and test one item at a time
- Keep existing code commented out initially
- Run full test suite after each extraction
- Test in local environment before deploying

### Risk 2: Missing Edge Cases
**Mitigation:**
- Review all usage sites before extraction
- Document assumptions in service methods
- Add comprehensive unit tests for new methods

### Risk 3: Performance Impact
**Mitigation:**
- Profile before/after extraction
- Ensure services use proper caching
- Monitor production metrics

---

## Next Steps

1. **Review this analysis** with team/stakeholders
2. **Prioritize phases** based on business needs
3. **Create feature branch** for extraction work
4. **Start with Phase 1** (scoring & betting logic)
5. **Test thoroughly** after each extraction
6. **Update contracts** to reflect new service methods

---

## Metrics

**Current State:**
- 11 embedded logic items in main.py
- ~200 lines of business logic in handlers
- Several deprecated/incomplete implementations

**Target State:**
- 0 embedded business logic in main.py
- All logic in services/managers with unit tests
- All deprecated code removed
- Complete implementations for all features

---

**Created:** November 3, 2025
**Status:** Analysis Complete
**Next Action:** Begin Phase 1 extraction (scoring & betting logic)
**Estimated Total Effort:** 12-18 hours across all phases
