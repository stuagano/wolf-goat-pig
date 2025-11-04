# Architecture Quick Reference Guide

## File Locations of Key Classes

### Player Classes (THREE IMPLEMENTATIONS - CONSOLIDATE!)
- `/app/domain/player.py` - **RECOMMENDED:** Full Player class with validation, strength levels, hole scores
- `/app/wolf_goat_pig_simulation.py:38` - WGPPlayer (game-specific, 10 lines)
- `/app/services/odds_calculator.py:34` - PlayerState (odds calculation only, 9 fields)

**Action:** Use domain/player.py everywhere, remove others

---

### BettingState Classes (TWO INCOMPATIBLE IMPLEMENTATIONS)
- `/app/state/betting_state.py` - SIMPLE VERSION (4 fields)
  - Fields: `teams`, `base_wager`, `doubled_status`, `game_phase`
  - Methods: request_partner, accept_partner, decline_partner, go_solo, offer_double, accept_double, decline_double, concede_hole, calculate_hole_points
  - Used by: GameState (MVP)

- `/app/wolf_goat_pig_simulation.py:69` - COMPLEX VERSION (13 fields)
  - Fields: base_wager, current_wager, doubled, redoubled, carry_over, float_invoked, option_invoked, duncan_invoked, tunkarri_invoked, big_dick_invoked, joes_special_value, ackerley_gambit, line_of_scrimmage, doubles_history, tossed_aardvarks, ping_pong_count
  - Used by: WolfGoatPigSimulation
  - Special rule support: The Option, The Float, The Duncan, The Tunkarri, The Big Dick, Ackerley Gambit

**Problem:** No conversion between them; they're incompatible data structures
**Action:** Merge into single ComprehensiveBettingState

---

### HoleState Classes (TWO DIFFERENT PURPOSES)
- `/app/services/odds_calculator.py:49` - LIGHTWEIGHT (11 fields)
  - Purpose: Odds calculation during hole play
  - Fields: hole_number, par, difficulty_rating, weather_factor, pin_position, course_conditions, teams, current_wager, is_doubled, line_of_scrimmage_passed
  - Used by: OddsCalculator

- `/app/wolf_goat_pig_simulation.py:109` - HEAVYWEIGHT (30+ fields, 500+ lines with methods)
  - Purpose: Complete hole state with shot-by-shot tracking
  - Fields: hole_number, hitting_order, teams, betting, ball_positions, current_order_of_play, line_of_scrimmage, next_player_to_hit, stroke_advantages, hole_par, stroke_index, hole_yardage, hole_difficulty, scores, shots_completed, balls_in_hole, concessions, current_shot_number, hole_complete, wagering_closed, tee_shots_complete, partnership_deadline_passed, invitation_windows
  - Methods: set_hole_info(), calculate_stroke_advantages(), add_shot(), process_tee_shot(), get_team_positions(), get_available_partners_for_captain(), get_team_stroke_advantages(), etc.
  - Used by: WolfGoatPigSimulation

**Problem:** Impossible to use one where other is needed
**Action:** Create unified HoleState that supports both

---

### Game State Containers (TWO SEPARATE SYSTEMS - CHOOSE ONE!)

#### GameState (`/app/game_state.py`)
- Lines: 776 lines
- Persistent: YES (uses GameStateModel in database)
- Delegation: Uses PlayerManager, BettingState, ShotState, CourseManager
- Supports: 4-player MVP rules
- Database: Uses GameStateModel to serialize entire state as JSON blob
- Methods: dispatch_action, invoke_float, toggle_option, record_gross_score, calculate_hole_points, next_hole, complete_game
- Persistence: _save_to_db(), _load_from_db(), _serialize(), _deserialize()

#### WolfGoatPigSimulation (`/app/wolf_goat_pig_simulation.py`)
- Lines: 1000+ lines
- Persistent: NO
- Delegation: Contains HoleState, BettingState, WGPPlayer, TeamFormation, WGPHoleProgression internally
- Supports: 4/5/6-player games, all special rules (Hoepfinger, Vinnie Variation, The Option, etc.)
- Methods: play_hole, add_shot, decide_partnership, offer_double, process_tee_shot
- Persistence: None (pure simulation)

**Problem:** They're incompatible systems managing the same concept
**Action:** Deprecate GameState, enhance WolfGoatPigSimulation with persistence layer

---

### Stroke Calculation Logic (THREE IMPLEMENTATIONS - UNIFY!)
- `/app/wolf_goat_pig_simulation.py:198` - HoleState._calculate_strokes_received()
  - Takes: handicap, stroke_index
  - Returns: float (0, 0.5, or 1.0)

- `/app/game_state.py:599` - GameState.get_player_strokes()
  - Takes: (none, uses self.player_manager.players)
  - Returns: dict {player_id: {hole_number: stroke_count}}
  - Uses relative handicap (vs minimum in group)

- `/app/services/odds_calculator.py:876` - calculate_strokes_received() UTILITY FUNCTION
  - Takes: handicap, stroke_index
  - Returns: float (0, 0.5, or 1.0)
  - Has special handling for handicaps > 18

**Problem:** Three different implementations, different parameters, different return types
**Action:** Create single authoritative function in shared utility module

---

### Shot Tracking Systems (THREE WAYS - CHOOSE ONE!)

#### ShotState (`/app/state/shot_state.py`)
- Purpose: Abstract shot phases management
- What it tracks: phase (tee_shots/approach_shots), current_player_index, completed_shots list, pending_decisions
- Used by: GameState

#### HoleState.ball_positions (`/app/wolf_goat_pig_simulation.py`)
- Purpose: Physical ball position tracking
- What it tracks: Dictionary of {player_id: BallPosition} with distance_to_pin, lie_type, shot_count, holed, conceded
- Used by: WolfGoatPigSimulation

#### WGPHoleProgression (`/app/wolf_goat_pig_simulation.py:562`)
- Purpose: Historical shot progression with timeline
- What it tracks: shots_taken dict, current_shot_order, betting_opportunities, timeline_events
- Used by: WolfGoatPigSimulation

**Problem:** Three overlapping tracking systems, unclear which to use when
**Action:** Consolidate into single comprehensive shot tracking system

---

### Betting Logic Scattered Across (FOUR PLACES!)
1. BettingState.calculate_hole_points() - Points distribution
2. BettingState._distribute_points_karl_marx() - Karl Marx rule
3. GameState.calculate_hole_points() - Delegates to BettingState, then updates hole_history
4. OddsCalculator._calculate_expected_value() - EV for betting scenarios
5. OddsCalculator._generate_betting_scenarios() - Scenario analysis
6. WolfGoatPigSimulation._calculate_base_wager() - Base wager calculation
7. WolfGoatPigSimulation._should_apply_option() - Option logic
8. WolfGoatPigSimulation._prompt_joes_special() - Hoepfinger special rule

**Problem:** Betting rules are scattered everywhere
**Action:** Centralize ALL betting logic into single ComprehensiveBettingState class

---

### Team Formation (TWO CONCEPTS)
- **TeamFormation** (`/app/wolf_goat_pig_simulation.py:56`)
  - Purpose: Single hole team configuration
  - Fields: type, captain, second_captain, team1, team2, team3, solo_player, opponents, pending_request
  - Used by: WolfGoatPigSimulation.HoleState

- **TeamFormationService** (`/app/services/team_formation_service.py`)
  - Purpose: Create balanced 4-player groups from daily signups
  - Methods: generate_random_teams(), create_team_pairings_with_rotations(), generate_balanced_teams(), validate_team_formation()
  - Used by: Daily signup matchmaking

**Relationship:** Different levels (game-level team vs daily signup grouping)
**Action:** Document clear separation of concerns or integrate if they should be unified

---

## Critical Data Structure Inconsistencies

### How Teams Are Represented
```python
# BettingState.teams:
{"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]}

# TeamFormation:
TeamFormation(type="partners", team1=["p1", "p2"], team2=["p3", "p4"], captain="p1")

# OddsCalculator.HoleState.teams:
TeamConfiguration.PARTNERS enum (not dict)
```
→ **Action:** Single consistent team representation

### How Players Are Stored
```python
# GameState:
PlayerManager with List[Player] + captain_id string + hitting_order list

# WolfGoatPigSimulation:
List[WGPPlayer] directly

# OddsCalculator:
List[PlayerState] for calculation
```
→ **Action:** Standardize on single Player representation

---

## Current State Management Flow

### GameState path (MVP):
1. GameState.__init__() → _load_from_db()
2. dispatch_action("action", payload)
3. _serialize() → GameStateModel(state=JSON) → Database
4. On next load: _deserialize() from JSON

### WolfGoatPigSimulation path (full rules):
1. WolfGoatPigSimulation.__init__() → _initialize_hole()
2. add_shot()/decide_partnership()/process_tee_shot()
3. State exists only in memory
4. No database integration

**Gap:** No way to persist WolfGoatPigSimulation to database
**Action:** Add persistence layer to WolfGoatPigSimulation

---

## Recommended Refactoring Order

### STEP 1: Create Shared Utilities (LOW RISK)
- `/app/utils/stroke_calculation.py`
  - Single source of truth for all stroke calculations
  - Tests: Comprehensive unit tests

### STEP 2: Create Unified Player
- Consolidate Player, WGPPlayer, PlayerState
- Keep domain/player.py as source
- Update all imports

### STEP 3: Create Comprehensive BettingState
- Merge simple + complex versions
- Support all special rules
- Comprehensive test coverage

### STEP 4: Create Unified HoleState
- Merge OddsCalculator version + WGP version
- Support both use cases

### STEP 5: Add Persistence to WolfGoatPigSimulation
- Create database adapter
- Deprecate GameState

### STEP 6: Consolidate Shot Tracking
- Choose best approach
- Deprecate others

---

## Files That Need Changes (If Full Refactor)

### CRITICAL (Will break existing code if changed):
- `/app/game_state.py` - MVP depends on this
- `/app/wolf_goat_pig_simulation.py` - Simulation tests depend on this
- `/app/models.py` - Database schema
- `/app/main.py` - API endpoints use both

### HIGH PRIORITY:
- `/app/state/betting_state.py` - Need to consolidate
- `/app/services/odds_calculator.py` - Uses its own classes
- `/app/domain/player.py` - Source of truth for player

### MEDIUM:
- `/app/state/player_manager.py` - Can be simplified
- `/app/state/shot_state.py` - Might consolidate
- `/app/services/team_formation_service.py` - Clarify role

---

## Code Duplication by Lines

| Code | Location 1 | Location 2 | Location 3 | Duplicated Lines |
|------|-----------|-----------|-----------|-----------------|
| Stroke calculation | HoleState:198-223 | GameState:619-633 | OddsCalculator:876-908 | ~30 lines |
| Points distribution | BettingState:143-170 | GameState:166-198 | (none) | ~30 lines |
| Team creation | TeamFormation | TeamFormationService | (different levels) | N/A |
| Player data | domain/player.py | WGPPlayer | PlayerState | ~50 lines |
| HoleState | OddsCalculator:49-60 | WGPSim:109-400 | (different) | N/A |

**Total Estimated Duplication:** 150+ lines of redundant/overlapping code

