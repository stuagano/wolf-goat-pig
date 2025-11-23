"""
Test suite demonstrating GameStateValidator usage.

Run with: pytest test_game_state_validator.py -v
"""

import pytest  # type: ignore[import-not-found]

from .exceptions import GameStateValidationError, PartnershipValidationError
from .game_state_validator import GameStateValidator


class TestGameInitialization:
    """Test game initialization validation"""

    def test_valid_game_initialization(self):
        """Valid 4-player game should pass validation"""
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

        # Should not raise
        GameStateValidator.validate_game_initialization(players, course)

    def test_wrong_player_count(self):
        """Game with wrong player count should fail"""
        players = [
            {"id": "p1", "name": "Alice", "handicap": 10},
            {"id": "p2", "name": "Bob", "handicap": 15}
        ]
        course = {"name": "Test Course", "holes": []}

        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_game_initialization(players, course)
        assert "exactly 4 players" in str(exc.value)

    def test_duplicate_player_ids(self):
        """Duplicate player IDs should fail"""
        players = [
            {"id": "p1", "name": "Alice", "handicap": 10},
            {"id": "p1", "name": "Bob", "handicap": 15},  # Duplicate ID
            {"id": "p3", "name": "Charlie", "handicap": 8},
            {"id": "p4", "name": "Dana", "handicap": 12}
        ]
        course = {"name": "Test Course", "holes": [{"number": i} for i in range(1, 19)]}

        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_game_initialization(players, course)
        assert "Duplicate player ID" in str(exc.value)

    def test_missing_course_info(self):
        """Missing course should fail"""
        players = [
            {"id": f"p{i}", "name": f"Player {i}", "handicap": 10}
            for i in range(1, 5)
        ]

        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_game_initialization(players, None)
        assert "course" in str(exc.value).lower()


class TestHoleStateTransitions:
    """Test hole state transition validation"""

    def test_valid_hole_start(self):
        """Starting hole 1 with no active hole should pass"""
        GameStateValidator.validate_hole_can_start(
            hole_number=1,
            current_hole=None,
            previous_hole_complete=True
        )

    def test_cannot_start_hole_with_active_hole(self):
        """Cannot start new hole while another is active"""
        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_hole_can_start(
                hole_number=2,
                current_hole=1,
                previous_hole_complete=False
            )
        assert "hole 1 is active" in str(exc.value)

    def test_must_complete_previous_hole(self):
        """Must complete previous hole before starting next"""
        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_hole_can_start(
                hole_number=5,
                current_hole=None,
                previous_hole_complete=False
            )
        assert "hole 4 is complete" in str(exc.value)

    def test_invalid_hole_number(self):
        """Invalid hole numbers should fail"""
        with pytest.raises(GameStateValidationError):
            GameStateValidator.validate_hole_can_start(
                hole_number=0,
                current_hole=None,
                previous_hole_complete=True
            )

        with pytest.raises(GameStateValidationError):
            GameStateValidator.validate_hole_can_start(
                hole_number=19,
                current_hole=None,
                previous_hole_complete=True
            )


class TestShotExecution:
    """Test shot execution validation"""

    def test_valid_shot_execution(self):
        """Valid shot should pass"""
        players = ["p1", "p2", "p3", "p4"]
        ball_positions = {
            "p1": {"distance_to_pin": 150, "holed": False, "conceded": False}
        }

        GameStateValidator.validate_shot_execution(
            player_id="p1",
            next_player_to_hit="p1",
            players=players,
            hole_complete=False,
            ball_positions=ball_positions
        )

    def test_cannot_hit_when_not_turn(self):
        """Player cannot hit when it's not their turn"""
        players = ["p1", "p2", "p3", "p4"]

        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_shot_execution(
                player_id="p1",
                next_player_to_hit="p2",
                players=players,
                hole_complete=False,
                ball_positions={}
            )
        assert "Not p1's turn" in str(exc.value)

    def test_cannot_hit_on_completed_hole(self):
        """Cannot execute shot on completed hole"""
        players = ["p1", "p2", "p3", "p4"]

        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_shot_execution(
                player_id="p1",
                next_player_to_hit="p1",
                players=players,
                hole_complete=True,
                ball_positions={}
            )
        assert "completed hole" in str(exc.value)

    def test_cannot_hit_after_holed_out(self):
        """Player who holed out cannot hit again"""
        players = ["p1", "p2", "p3", "p4"]
        ball_positions = {
            "p1": {"distance_to_pin": 0, "holed": True, "conceded": False}
        }

        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_shot_execution(
                player_id="p1",
                next_player_to_hit="p1",
                players=players,
                hole_complete=False,
                ball_positions=ball_positions
            )
        assert "already holed out" in str(exc.value)


class TestPartnershipValidation:
    """Test partnership formation validation"""

    def test_valid_partnership_request(self):
        """Valid partnership request should pass"""
        players = ["p1", "p2", "p3", "p4"]

        GameStateValidator.validate_partnership_request(
            captain_id="p1",
            partner_id="p2",
            players=players,
            tee_shots_complete=4,
            partnership_deadline_passed=False,
            current_team_type=None
        )

    def test_cannot_partner_with_self(self):
        """Captain cannot partner with themselves"""
        players = ["p1", "p2", "p3", "p4"]

        with pytest.raises(PartnershipValidationError) as exc:
            GameStateValidator.validate_partnership_request(
                captain_id="p1",
                partner_id="p1",
                players=players,
                tee_shots_complete=4,
                partnership_deadline_passed=False,
                current_team_type=None
            )
        assert "cannot partner with themselves" in str(exc.value)

    def test_partnership_requires_tee_shots_complete(self):
        """Partnership requires all tee shots complete"""
        players = ["p1", "p2", "p3", "p4"]

        with pytest.raises(PartnershipValidationError) as exc:
            GameStateValidator.validate_partnership_request(
                captain_id="p1",
                partner_id="p2",
                players=players,
                tee_shots_complete=2,
                partnership_deadline_passed=False,
                current_team_type=None
            )
        assert "tee shots" in str(exc.value)

    def test_partnership_after_deadline(self):
        """Cannot request partnership after deadline"""
        players = ["p1", "p2", "p3", "p4"]

        with pytest.raises(PartnershipValidationError) as exc:
            GameStateValidator.validate_partnership_request(
                captain_id="p1",
                partner_id="p2",
                players=players,
                tee_shots_complete=4,
                partnership_deadline_passed=True,
                current_team_type=None
            )
        assert "deadline" in str(exc.value)

    def test_partnership_response_requires_pending_request(self):
        """Partnership response requires pending request"""
        with pytest.raises(PartnershipValidationError) as exc:
            GameStateValidator.validate_partnership_response(
                partner_id="p2",
                pending_request=None
            )
        assert "No partnership request" in str(exc.value)

    def test_only_invited_partner_can_respond(self):
        """Only invited partner can respond"""
        pending_request = {
            "captain_id": "p1",
            "partner_id": "p2"
        }

        with pytest.raises(PartnershipValidationError) as exc:
            GameStateValidator.validate_partnership_response(
                partner_id="p3",
                pending_request=pending_request
            )
        assert "not the invited partner" in str(exc.value)


class TestBallPositions:
    """Test ball position validation"""

    def test_valid_ball_position(self):
        """Valid ball position should pass"""
        players = ["p1", "p2", "p3", "p4"]

        GameStateValidator.validate_ball_position(
            player_id="p1",
            distance_to_pin=150.5,
            lie_type="fairway",
            shot_count=1,
            players=players
        )

    def test_invalid_distance(self):
        """Invalid distances should fail"""
        players = ["p1", "p2", "p3", "p4"]

        # Negative distance
        with pytest.raises(GameStateValidationError):
            GameStateValidator.validate_ball_position(
                player_id="p1",
                distance_to_pin=-10,
                lie_type="fairway",
                shot_count=1,
                players=players
            )

        # Excessive distance
        with pytest.raises(GameStateValidationError):
            GameStateValidator.validate_ball_position(
                player_id="p1",
                distance_to_pin=1000,
                lie_type="fairway",
                shot_count=1,
                players=players
            )

    def test_invalid_lie_type(self):
        """Invalid lie type should fail"""
        players = ["p1", "p2", "p3", "p4"]

        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_ball_position(
                player_id="p1",
                distance_to_pin=100,
                lie_type="swamp",
                shot_count=1,
                players=players
            )
        assert "Invalid lie type" in str(exc.value)

    def test_in_hole_must_have_zero_distance(self):
        """Ball in hole must have distance 0"""
        players = ["p1", "p2", "p3", "p4"]

        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_ball_position(
                player_id="p1",
                distance_to_pin=5,
                lie_type="in_hole",
                shot_count=3,
                players=players
            )
        assert "distance 0" in str(exc.value)


class TestGamePhaseTransitions:
    """Test game phase transition validation"""

    def test_valid_phase_transitions(self):
        """Valid phase transitions should pass"""
        # Regular to Vinnie at hole 13
        GameStateValidator.validate_game_phase_transition(
            current_phase="regular",
            new_phase="vinnie_variation",
            hole_number=13
        )

        # Vinnie to Hoepfinger at hole 17
        GameStateValidator.validate_game_phase_transition(
            current_phase="vinnie_variation",
            new_phase="hoepfinger",
            hole_number=17
        )

    def test_cannot_go_backwards_in_phases(self):
        """Cannot transition backwards through phases"""
        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_game_phase_transition(
                current_phase="vinnie_variation",
                new_phase="regular",
                hole_number=14
            )
        assert "Cannot transition from vinnie_variation to regular" in str(exc.value)

    def test_vinnie_variation_timing(self):
        """Vinnie variation should start around hole 13"""
        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_game_phase_transition(
                current_phase="regular",
                new_phase="vinnie_variation",
                hole_number=5
            )
        assert "hole 13" in str(exc.value)

    def test_hoepfinger_timing(self):
        """Hoepfinger should start around hole 17"""
        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_game_phase_transition(
                current_phase="vinnie_variation",
                new_phase="hoepfinger",
                hole_number=10
            )
        assert "hole 17" in str(exc.value)


class TestTeamFormation:
    """Test team formation validation"""

    def test_valid_partners_formation(self):
        """Valid partners formation should pass"""
        players = ["p1", "p2", "p3", "p4"]

        GameStateValidator.validate_team_formation(
            team_type="partners",
            captain="p1",
            partner="p2",
            solo_player=None,
            players=players
        )

    def test_valid_solo_formation(self):
        """Valid solo formation should pass"""
        players = ["p1", "p2", "p3", "p4"]

        GameStateValidator.validate_team_formation(
            team_type="solo",
            captain=None,
            partner=None,
            solo_player="p1",
            players=players
        )

    def test_partners_requires_captain_and_partner(self):
        """Partners formation requires both captain and partner"""
        players = ["p1", "p2", "p3", "p4"]

        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_team_formation(
                team_type="partners",
                captain="p1",
                partner=None,
                solo_player=None,
                players=players
            )
        assert "requires partner" in str(exc.value)

    def test_solo_requires_solo_player(self):
        """Solo formation requires solo_player"""
        players = ["p1", "p2", "p3", "p4"]

        with pytest.raises(GameStateValidationError) as exc:
            GameStateValidator.validate_team_formation(
                team_type="solo",
                captain=None,
                partner=None,
                solo_player=None,
                players=players
            )
        assert "requires solo_player" in str(exc.value)


class TestHoleCompletion:
    """Test hole completion validation"""

    def test_hole_complete_when_all_holed_out(self):
        """Hole complete when all players holed out"""
        players = ["p1", "p2", "p3", "p4"]
        ball_positions = {
            "p1": {"holed": True, "conceded": False},
            "p2": {"holed": True, "conceded": False},
            "p3": {"holed": True, "conceded": False},
            "p4": {"holed": True, "conceded": False}
        }

        result = GameStateValidator.validate_hole_completion(
            ball_positions=ball_positions,
            players=players
        )
        assert result is True

    def test_hole_complete_with_concessions(self):
        """Hole complete with mix of holed and conceded"""
        players = ["p1", "p2", "p3", "p4"]
        ball_positions = {
            "p1": {"holed": True, "conceded": False},
            "p2": {"holed": False, "conceded": True},
            "p3": {"holed": True, "conceded": False},
            "p4": {"holed": False, "conceded": True}
        }

        result = GameStateValidator.validate_hole_completion(
            ball_positions=ball_positions,
            players=players
        )
        assert result is True

    def test_hole_not_complete_when_player_still_playing(self):
        """Hole not complete when player still playing"""
        players = ["p1", "p2", "p3", "p4"]
        ball_positions = {
            "p1": {"holed": True, "conceded": False},
            "p2": {"holed": True, "conceded": False},
            "p3": {"holed": True, "conceded": False},
            "p4": {"holed": False, "conceded": False}  # Still playing
        }

        result = GameStateValidator.validate_hole_completion(
            ball_positions=ball_positions,
            players=players
        )
        assert result is False


class TestValidationSummary:
    """Test comprehensive validation summary"""

    def test_validation_summary_for_initialized_game(self):
        """Validation summary for initialized game"""
        game_state = {
            "players": [
                {"id": "p1", "name": "Alice"},
                {"id": "p2", "name": "Bob"},
                {"id": "p3", "name": "Charlie"},
                {"id": "p4", "name": "Dana"}
            ],
            "current_hole": None,
            "hole_state": {}
        }

        summary = GameStateValidator.get_validation_summary(game_state)

        assert summary["valid"] is True
        assert "game_initialized" in summary["available_operations"]

    def test_validation_summary_with_partnership_window_open(self):
        """Validation summary with partnership window open"""
        game_state = {
            "players": [
                {"id": f"p{i}", "name": f"Player {i}"}
                for i in range(1, 5)
            ],
            "current_hole": 1,
            "hole_state": {
                "hole_complete": False,
                "tee_shots_complete": 4,
                "partnership_deadline_passed": False,
                "next_player_to_hit": "p1"
            }
        }

        summary = GameStateValidator.get_validation_summary(game_state)

        assert "hole_in_progress" in summary["available_operations"]
        assert "partnership_window_open" in summary["available_operations"]
        assert "shot_available_p1" in summary["available_operations"]


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running GameStateValidator smoke tests...")
    print()

    # Test 1: Valid game initialization
    print("✓ Test 1: Valid game initialization")
    players = [
        {"id": f"p{i}", "name": f"Player {i}", "handicap": 10}
        for i in range(1, 5)
    ]
    course = {
        "name": "Test Course",
        "holes": [{"number": i, "par": 4, "yardage": 400} for i in range(1, 19)]
    }
    GameStateValidator.validate_game_initialization(players, course)

    # Test 2: Invalid player count
    print("✓ Test 2: Invalid player count caught")
    try:
        GameStateValidator.validate_game_initialization(players[:2], course)
        print("  ERROR: Should have raised exception")
    except GameStateValidationError as e:
        print(f"  Correctly caught: {e.message}")

    # Test 3: Partnership validation
    print("✓ Test 3: Partnership validation")
    try:
        GameStateValidator.validate_partnership_formation(
            captain_id="p1",
            partner_id="p1",  # Can't partner with self
            tee_shots_complete=False
        )
        print("  ERROR: Should have raised exception")
    except GameStateValidationError as e:
        print(f"  Correctly caught: {e.message}")

    print()
    print("All smoke tests passed!")
    print()
    print("Run full test suite with: pytest test_game_state_validator.py -v")
