"""
Test script for RuleManager functionality.

Demonstrates the key features of the RuleManager including:
- Singleton pattern
- Partnership rules
- Betting rules
- Turn validation
- Action discovery
- Handicap stroke calculation
"""

from app.managers import RuleManager, RuleViolationError
import json


def create_sample_game_state():
    """Create a sample game state for testing."""
    return {
        "game_id": "test-game-123",
        "players": [
            {"id": "player_1", "name": "Alice", "handicap": 10.0},
            {"id": "player_2", "name": "Bob", "handicap": 15.0},
            {"id": "player_3", "name": "Charlie", "handicap": 8.0},
            {"id": "player_4", "name": "Diana", "handicap": 20.0},
        ],
        "current_hole_number": 1,
        "current_hole": {
            "hole_number": 1,
            "par": 4,
            "yards": 420,
            "stroke_index": 5,
            "hitting_order": ["player_1", "player_2", "player_3", "player_4"],
            "teams": {},
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


def test_singleton_pattern():
    """Test that RuleManager follows singleton pattern."""
    print("\n=== Testing Singleton Pattern ===")

    manager1 = RuleManager.get_instance()
    manager2 = RuleManager.get_instance()

    print(f"Manager 1 ID: {id(manager1)}")
    print(f"Manager 2 ID: {id(manager2)}")
    print(f"Same instance: {manager1 is manager2}")

    assert manager1 is manager2, "RuleManager should be a singleton"
    print("✓ Singleton pattern works correctly")


def test_partnership_rules():
    """Test partnership formation rules."""
    print("\n=== Testing Partnership Rules ===")

    manager = RuleManager.get_instance()
    game_state = create_sample_game_state()

    # Test valid partnership
    try:
        can_partner = manager.can_form_partnership("player_1", "player_2", game_state)
        print(f"✓ Can form partnership (player_1 -> player_2): {can_partner}")
    except RuleViolationError as e:
        print(f"✗ Partnership failed: {e.message}")

    # Test self-partnership (should fail)
    try:
        manager.can_form_partnership("player_1", "player_1", game_state)
        print("✗ Self-partnership should have failed!")
    except RuleViolationError as e:
        print(f"✓ Self-partnership correctly rejected: {e.message}")

    # Test partnership after deadline
    game_state["current_hole"]["tee_shots_complete"] = 4
    try:
        manager.can_form_partnership("player_1", "player_2", game_state)
        print("✗ Partnership after deadline should have failed!")
    except RuleViolationError as e:
        print(f"✓ Late partnership correctly rejected: {e.message}")


def test_lone_wolf():
    """Test lone wolf rules."""
    print("\n=== Testing Lone Wolf Rules ===")

    manager = RuleManager.get_instance()
    game_state = create_sample_game_state()

    # Captain can go lone wolf
    try:
        can_lone_wolf = manager.can_go_lone_wolf("player_1", game_state)
        print(f"✓ Captain can go lone wolf: {can_lone_wolf}")
    except RuleViolationError as e:
        print(f"✗ Lone wolf failed: {e.message}")

    # Non-captain cannot
    try:
        manager.can_go_lone_wolf("player_2", game_state)
        print("✗ Non-captain lone wolf should have failed!")
    except RuleViolationError as e:
        print(f"✓ Non-captain correctly rejected: {e.message}")


def test_betting_rules():
    """Test betting action rules."""
    print("\n=== Testing Betting Rules ===")

    manager = RuleManager.get_instance()
    game_state = create_sample_game_state()

    # Cannot double before partnership
    try:
        manager.can_double("player_1", game_state)
        print("✗ Double before partnership should have failed!")
    except RuleViolationError as e:
        print(f"✓ Early double correctly rejected: {e.message}")

    # Form partnership, then double should work
    game_state["current_hole"]["teams"] = {
        "partnership_captain": "player_1",
        "partnership_partner": "player_2"
    }

    try:
        can_double = manager.can_double("player_1", game_state)
        print(f"✓ Can double after partnership: {can_double}")
    except RuleViolationError as e:
        print(f"✗ Double failed: {e.message}")

    # Test Duncan
    game_state["current_hole"]["teams"] = {}  # Reset partnership
    try:
        can_duncan = manager.can_duncan("player_1", game_state)
        print(f"✓ Captain can invoke Duncan: {can_duncan}")
    except RuleViolationError as e:
        print(f"✗ Duncan failed: {e.message}")


def test_valid_actions():
    """Test getting valid actions for a player."""
    print("\n=== Testing Valid Actions Discovery ===")

    manager = RuleManager.get_instance()
    game_state = create_sample_game_state()

    # Player 1 (captain, current turn)
    actions = manager.get_valid_actions("player_1", game_state)
    print(f"Valid actions for player_1 (captain, current turn): {actions}")

    # Player 2 (not captain, not current turn)
    actions = manager.get_valid_actions("player_2", game_state)
    print(f"Valid actions for player_2 (not captain, not turn): {actions}")

    # After forming partnership
    game_state["current_hole"]["teams"] = {
        "partnership_captain": "player_1",
        "partnership_partner": "player_2"
    }
    actions = manager.get_valid_actions("player_1", game_state)
    print(f"Valid actions for player_1 after partnership: {actions}")


def test_handicap_strokes():
    """Test handicap stroke calculation."""
    print("\n=== Testing Handicap Stroke Calculation ===")

    manager = RuleManager.get_instance()

    player_handicaps = {
        "player_1": 10.0,
        "player_2": 15.0,
        "player_3": 8.0,
        "player_4": 20.0,
    }

    # Hole with stroke index 5 (moderately difficult)
    strokes = manager.apply_handicap_strokes(1, player_handicaps, 5)
    print(f"Strokes on hole 1 (SI=5): {json.dumps(strokes, indent=2)}")

    # Hole with stroke index 1 (hardest hole)
    strokes = manager.apply_handicap_strokes(5, player_handicaps, 1)
    print(f"Strokes on hole 5 (SI=1): {json.dumps(strokes, indent=2)}")

    # Hole with stroke index 18 (easiest hole)
    strokes = manager.apply_handicap_strokes(10, player_handicaps, 18)
    print(f"Strokes on hole 10 (SI=18): {json.dumps(strokes, indent=2)}")


def test_hole_winner():
    """Test hole winner calculation."""
    print("\n=== Testing Hole Winner Calculation ===")

    manager = RuleManager.get_instance()

    # Clear winner
    results = {"player_1": 4, "player_2": 5, "player_3": 6}
    winner = manager.calculate_hole_winner(results)
    print(f"Results: {results}")
    print(f"Winner: {winner}")

    # Tie (carry over)
    results = {"player_1": 4, "player_2": 4, "player_3": 5}
    winner = manager.calculate_hole_winner(results)
    print(f"\nResults: {results}")
    print(f"Winner: {winner} (None = tie/carry over)")


def test_rule_summary():
    """Test getting rule summary."""
    print("\n=== Testing Rule Summary ===")

    manager = RuleManager.get_instance()
    summary = manager.get_rule_summary()

    print("Partnership Rules:")
    print(json.dumps(summary["partnership"], indent=2))

    print("\nBetting Rules:")
    print(json.dumps(summary["betting"], indent=2))

    print("\nGame Info:")
    print(json.dumps(summary["game"], indent=2))


def main():
    """Run all tests."""
    print("=" * 60)
    print("RuleManager Test Suite")
    print("=" * 60)

    try:
        test_singleton_pattern()
        test_partnership_rules()
        test_lone_wolf()
        test_betting_rules()
        test_valid_actions()
        test_handicap_strokes()
        test_hole_winner()
        test_rule_summary()

        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
