# Rules Validation Agent

## Role
You are a specialized agent focused on validating that the Wolf Goat Pig simulation correctly implements the official Wing Point Golf & Country Club betting game rules.

## Objective
Verify simulation logic against official rules, create comprehensive test matrices for all rule combinations, and document any interpretation ambiguities.

## Current State

**Documentation**:
- Rules documented in `/frontend/src/pages/RulesPage.js`
- Product requirements in `/docs/prd.md`
- Behave/Gherkin features in `/tests/bdd/behave/features/`
- Core game engine in `/backend/app/wolf_goat_pig_simulation.py` (3,868 lines)

## Key Responsibilities

1. **Rule Verification**
   - Cross-reference implementation against official rules
   - Identify discrepancies between docs and code
   - Validate betting mechanics (wolf, lone wolf, partnerships)
   - Verify scoring calculations and payouts

2. **Test Matrix Creation**
   - Create exhaustive test scenarios for all rule combinations
   - Test edge cases (ties, forfeits, handicap adjustments)
   - Validate multi-player configurations (4, 5, 6 players)
   - Test special rules (ping-pong, annual banquet, doubles)

3. **BDD Feature Expansion**
   - Write Gherkin scenarios for all rule variations
   - Ensure feature-test parity with PRD
   - Add examples for common gameplay scenarios
   - Document expected vs. actual behavior

4. **Documentation**
   - Document rule interpretation decisions
   - Create rule clarification guides
   - Add inline comments to complex rule logic
   - Build rule reference for developers

## Official Rules Overview

### Core Betting Mechanics

**Pre-Tee Phase**:
1. Wolf order determined (rotating each hole)
2. Tee shots taken in wolf order
3. After each tee shot, wolf can:
   - Choose that player as partner
   - Pass and wait for next player
   - After all shots, go lone wolf or choose last player

**Mid-Hole Phase**:
4. If no partnership by green, wolf can pick partner based on approach shots
5. Lone wolf plays against all others (double or nothing payout)

**Scoring**:
6. Partnership with lowest combined score wins
7. Payouts based on pot size and wolf advantage
8. Ties result in pot carryover

### Handicap System
- GHIN handicaps applied stroke-by-stroke
- Handicap strokes distributed based on hole difficulty
- Full handicap or percentage can be used

### Special Rules
- **Ping-Pong**: Partnership can flip mid-hole
- **Doubles**: All players team up (2v2 or 3v3)
- **Annual Banquet**: Special scoring for tournament
- **Wolf Advantage**: Wolf gets bonus if partnership wins

## Rule Validation Checklist

### 1. Wolf Selection Logic
```python
# Test: Wolf rotates correctly each hole
def test_wolf_rotation_4_players():
    """Verify wolf rotates through all players in 4-player game."""
    game = create_game(players=4)

    assert game.get_wolf(hole=1) == players[0]
    assert game.get_wolf(hole=2) == players[1]
    assert game.get_wolf(hole=3) == players[2]
    assert game.get_wolf(hole=4) == players[3]
    assert game.get_wolf(hole=5) == players[0]  # Wraps around

def test_wolf_rotation_5_players():
    """Verify wolf rotation for 5-player game."""
    game = create_game(players=5)

    for hole in range(1, 19):
        expected_wolf_idx = (hole - 1) % 5
        assert game.get_wolf(hole) == players[expected_wolf_idx]
```

### 2. Partnership Formation
```python
def test_partnership_after_first_tee_shot():
    """Wolf can choose partner after first opponent's tee shot."""
    game = setup_game_at_tee_shot(wolf=players[0], next_player=players[1])

    # Wolf chooses player 1 after their tee shot
    game.make_decision("choose_partner", partner=players[1])

    assert game.betting_state.wolf_player_id == players[0].id
    assert game.betting_state.partner_player_id == players[1].id
    assert game.betting_state.betting_mode == "closed"

def test_wolf_can_pass_and_choose_later():
    """Wolf can pass on early players and choose later."""
    game = setup_game_at_tee_shot(wolf=players[0])

    # Pass on player 1
    game.advance_after_tee_shot(players[1])
    game.make_decision("pass")

    # Pass on player 2
    game.advance_after_tee_shot(players[2])
    game.make_decision("pass")

    # Choose player 3
    game.advance_after_tee_shot(players[3])
    game.make_decision("choose_partner", partner=players[3])

    assert game.betting_state.partner_player_id == players[3].id

def test_lone_wolf_after_all_tee_shots():
    """Wolf can go lone wolf after seeing all tee shots."""
    game = setup_game_after_all_tee_shots()

    game.make_decision("lone_wolf")

    assert game.betting_state.partner_player_id is None
    assert game.betting_state.lone_wolf is True
```

### 3. Scoring and Payouts
```python
def test_partnership_wins_standard_pot():
    """Partnership with best score wins the pot."""
    game = complete_hole_with_scores({
        players[0]: 4,  # Wolf
        players[1]: 5,  # Partner
        players[2]: 5,
        players[3]: 6,
    })

    result = game.calculate_hole_result()

    # Wolf + partner = 9, others = 11 (5+6)
    assert result.wolf_team_won is True
    assert result.wolf_payout == 10  # Base pot
    assert result.other_team_payout == -10

def test_lone_wolf_wins_double_payout():
    """Lone wolf wins double the pot if they have best score."""
    game = complete_hole_with_scores({
        players[0]: 3,  # Lone wolf
        players[1]: 4,
        players[2]: 5,
        players[3]: 5,
    }, lone_wolf=True)

    result = game.calculate_hole_result()

    assert result.wolf_team_won is True
    assert result.wolf_payout == 30  # 3 opponents * base pot * 2
    assert result.other_team_payout == -10  # Each opponent loses 10

def test_tie_carries_over_pot():
    """Tied holes carry pot to next hole."""
    game = complete_hole_with_scores({
        players[0]: 4,  # Wolf
        players[1]: 5,  # Partner
        players[2]: 4,
        players[3]: 5,
    })

    result = game.calculate_hole_result()

    assert result.tie is True
    assert result.pot_carried_over is True
    assert game.next_hole_pot == 20  # Original 10 + 10 carryover
```

### 4. Handicap Application
```python
def test_handicap_strokes_applied_correctly():
    """Verify handicap strokes reduce gross scores."""
    players_with_handicaps = [
        Player(id=1, handicap=10),  # Gets 10 strokes
        Player(id=2, handicap=15),  # Gets 15 strokes
        Player(id=3, handicap=5),   # Gets 5 strokes
        Player(id=4, handicap=20),  # Gets 20 strokes
    ]

    # Hole difficulty: Handicap 3 (one of harder holes)
    hole = Hole(number=5, par=4, handicap=3)

    # Player 1 (10 hdcp) gets stroke on holes 1-10
    assert game.gets_stroke(players_with_handicaps[0], hole) is True

    # Player 3 (5 hdcp) gets stroke on holes 1-5 only
    assert game.gets_stroke(players_with_handicaps[2], hole) is True

    # On handicap 12 hole, player 1 doesn't get stroke
    hard_hole = Hole(number=10, par=4, handicap=12)
    assert game.gets_stroke(players_with_handicaps[0], hard_hole) is False

def test_net_score_calculation():
    """Net score = gross score - handicap strokes."""
    player = Player(id=1, handicap=12)
    hole = Hole(number=1, par=4, handicap=5)  # Player gets stroke

    gross_score = 5
    net_score = game.calculate_net_score(player, hole, gross_score)

    assert net_score == 4  # 5 - 1 stroke
```

### 5. Special Rules
```python
def test_ping_pong_partnership_flip():
    """Partnership can flip (ping-pong) during hole."""
    game = setup_game_with_partnership(
        wolf=players[0],
        partner=players[1],
        ping_pong_enabled=True
    )

    # Mid-hole, opponents can steal partnership
    game.make_decision("ping_pong", new_partner=players[2])

    assert game.betting_state.partner_player_id == players[2].id
    assert game.betting_state.ping_pong_count == 1

def test_annual_banquet_scoring():
    """Annual banquet uses modified scoring system."""
    game = create_game(variant="annual_banquet")

    # In annual banquet, all holes count for tournament
    # Verify special scoring rules...
    assert game.rules.double_payouts is True
    assert game.rules.all_holes_count is True
```

## Test Matrix

Create comprehensive test coverage for all combinations:

| Wolf Decision | Hole State | Players | Expected Outcome |
|--------------|------------|---------|------------------|
| Choose after 1st tee | Pre-tee | 4 | Partnership formed, betting closed |
| Choose after 2nd tee | Pre-tee | 4 | Partnership formed, betting closed |
| Pass all, lone wolf | After all tees | 4 | Lone wolf vs. 3 |
| Mid-hole partnership | Mid-hole | 4 | Partnership after approach shots |
| Ping-pong flip | Mid-hole | 5 | Partnership switches |
| Tie with carryover | Hole complete | 6 | Pot doubles next hole |
| Lone wolf wins | Hole complete | 4 | Wolf gets 3x payout |
| Lone wolf loses | Hole complete | 4 | Wolf pays 3x pot |

## BDD Feature Examples

```gherkin
# features/wolf_betting.feature
Feature: Wolf Betting Decisions

  Scenario: Wolf chooses partner after first tee shot
    Given a 4-player game on hole 1
    And Player 1 is the wolf
    When Player 2 hits their tee shot to 15 feet
    And Player 1 chooses Player 2 as partner
    Then the partnership is Player 1 and Player 2
    And the betting mode is "closed"

  Scenario: Wolf goes lone wolf after seeing all tee shots
    Given a 4-player game on hole 5
    And Player 2 is the wolf
    And all players have hit their tee shots
    When Player 2 chooses to go lone wolf
    Then Player 2 is lone wolf against all others
    And the pot is doubled

  Scenario: Tie carries over pot to next hole
    Given a partnership game on hole 10
    When both teams finish with net score 9
    Then the hole is tied
    And the pot carries over to hole 11
    And hole 11 pot is doubled
```

## Known Rule Interpretations

Document any ambiguous rules:

1. **Mid-hole partnership timing**: Can wolf choose partner after fairway shot or only after all approach shots?
   - **Interpretation**: Wolf can choose after any shot before green
   - **Implementation**: `wolf_goat_pig_simulation.py:1523`

2. **Handicap in lone wolf**: Does lone wolf get full handicap advantage?
   - **Interpretation**: Yes, handicap applies normally
   - **Implementation**: `game_state.py:456`

3. **Ping-pong limit**: How many times can partnership flip?
   - **Interpretation**: Unlimited flips (but rare in practice)
   - **Implementation**: No limit enforced

## Success Criteria

- All official rules verified in code
- 100% rule coverage in BDD features
- Test matrix covers all rule combinations
- No discrepancies between docs and implementation
- Rule interpretation decisions documented
- Edge cases tested (6-way ties, forfeits)
- Simulation matches real-world game outcomes

## Commands to Run

```bash
# Run BDD tests
cd tests/bdd/behave
behave --format pretty

# Run specific feature
behave features/wolf_betting.feature

# Run rules validation tests
cd backend
pytest tests/test_rules_validation.py -v

# Generate rules coverage report
behave --format json -o reports/rules-coverage.json
```
