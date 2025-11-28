"""
Unit tests for ScoreCalculationService

Tests the core scoring logic for Wolf Goat Pig game including:
- Net score calculation
- Best ball team scoring
- Partners (2v2) scoring
- Solo vs all scoring
- All vs all scoring
- Special rules (Karl Marx, Duncan, Tunkarri)
"""

import pytest
from app.services.score_calculation_service import (
    ScoreCalculationService,
    TeamType,
    TeamConfig,
    HoleResult,
    get_score_calculation_service,
)


class TestNetScoreCalculation:
    """Test net score calculation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScoreCalculationService()

    def test_net_score_no_handicap(self):
        """Test net score without handicap strokes."""
        net = self.service.calculate_net_score(gross_score=5, handicap_strokes=0)
        assert net == 5

    def test_net_score_with_one_stroke(self):
        """Test net score with one handicap stroke."""
        net = self.service.calculate_net_score(gross_score=5, handicap_strokes=1)
        assert net == 4

    def test_net_score_with_multiple_strokes(self):
        """Test net score with multiple handicap strokes."""
        net = self.service.calculate_net_score(gross_score=6, handicap_strokes=2)
        assert net == 4

    def test_net_score_minimum_is_one(self):
        """Test that net score cannot go below 1."""
        net = self.service.calculate_net_score(gross_score=2, handicap_strokes=5)
        assert net == 1

    def test_net_score_validation_negative_gross(self):
        """Test validation catches negative gross score."""
        with pytest.raises(ValueError, match="Gross score must be positive"):
            self.service.calculate_net_score(gross_score=-1, handicap_strokes=0)

    def test_net_score_validation_negative_handicap(self):
        """Test validation catches negative handicap strokes."""
        with pytest.raises(ValueError, match="Handicap strokes cannot be negative"):
            self.service.calculate_net_score(gross_score=5, handicap_strokes=-1)

    def test_net_score_skip_validation(self):
        """Test validation can be skipped."""
        # Should not raise even with invalid input
        net = self.service.calculate_net_score(gross_score=0, handicap_strokes=0, validate=False)
        assert net == 1  # Still enforces minimum of 1


class TestBestBallCalculation:
    """Test best ball team scoring."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScoreCalculationService()

    def test_best_ball_single_score(self):
        """Test best ball with single player."""
        best = self.service.calculate_team_best_ball([4])
        assert best == 4

    def test_best_ball_multiple_scores(self):
        """Test best ball with multiple players."""
        best = self.service.calculate_team_best_ball([4, 5, 6])
        assert best == 4

    def test_best_ball_tied_scores(self):
        """Test best ball when multiple players tie."""
        best = self.service.calculate_team_best_ball([4, 4, 5])
        assert best == 4

    def test_best_ball_empty_list_raises(self):
        """Test that empty scores list raises error."""
        with pytest.raises(ValueError, match="Cannot calculate best ball with empty scores"):
            self.service.calculate_team_best_ball([])


class TestPartnersScoring:
    """Test partners (2v2) scoring calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScoreCalculationService()

    def test_partners_team1_wins(self):
        """Test partners scoring when team 1 wins."""
        scores = {"p1": 4, "p2": 5, "p3": 5, "p4": 6}
        team_config = TeamConfig(
            team_type=TeamType.PARTNERS,
            team1=["p1", "p2"],
            team2=["p3", "p4"]
        )
        result = self.service.calculate_hole_points(scores, team_config, wager=2)

        assert result.winners == ["p1", "p2"]
        assert result.losers == ["p3", "p4"]
        assert result.points_changes["p1"] == 2
        assert result.points_changes["p2"] == 2
        assert result.points_changes["p3"] == -2
        assert result.points_changes["p4"] == -2
        assert not result.halved
        assert result.team_type == TeamType.PARTNERS
        assert result.wager == 2

    def test_partners_team2_wins(self):
        """Test partners scoring when team 2 wins."""
        scores = {"p1": 5, "p2": 6, "p3": 4, "p4": 5}
        team_config = TeamConfig(
            team_type=TeamType.PARTNERS,
            team1=["p1", "p2"],
            team2=["p3", "p4"]
        )
        result = self.service.calculate_hole_points(scores, team_config, wager=2)

        assert result.winners == ["p3", "p4"]
        assert result.losers == ["p1", "p2"]
        assert result.points_changes["p1"] == -2
        assert result.points_changes["p2"] == -2
        assert result.points_changes["p3"] == 2
        assert result.points_changes["p4"] == 2
        assert not result.halved

    def test_partners_halved(self):
        """Test partners scoring when hole is halved."""
        scores = {"p1": 4, "p2": 5, "p3": 4, "p4": 6}
        team_config = TeamConfig(
            team_type=TeamType.PARTNERS,
            team1=["p1", "p2"],
            team2=["p3", "p4"]
        )
        result = self.service.calculate_hole_points(scores, team_config, wager=2)

        assert result.winners == []
        assert result.losers == []
        assert result.points_changes["p1"] == 0
        assert result.points_changes["p2"] == 0
        assert result.points_changes["p3"] == 0
        assert result.points_changes["p4"] == 0
        assert result.halved

    def test_partners_empty_team_raises(self):
        """Test that empty team raises error."""
        scores = {"p1": 4, "p2": 5}
        team_config = TeamConfig(
            team_type=TeamType.PARTNERS,
            team1=["p1", "p2"],
            team2=[]
        )
        with pytest.raises(ValueError, match="Both teams must have players"):
            self.service.calculate_hole_points(scores, team_config, wager=2)

    def test_partners_to_dict(self):
        """Test HoleResult.to_dict() method."""
        scores = {"p1": 4, "p2": 5, "p3": 5, "p4": 6}
        team_config = TeamConfig(
            team_type=TeamType.PARTNERS,
            team1=["p1", "p2"],
            team2=["p3", "p4"]
        )
        result = self.service.calculate_hole_points(scores, team_config, wager=2)
        result_dict = result.to_dict()

        assert result_dict["team_type"] == "partners"
        assert result_dict["wager"] == 2
        assert result_dict["halved"] is False
        assert "winners" in result_dict
        assert "losers" in result_dict


class TestSoloScoring:
    """Test solo (1 vs all) scoring calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScoreCalculationService()

    def test_solo_player_wins(self):
        """Test solo scoring when solo player wins."""
        scores = {"wolf": 3, "p2": 4, "p3": 5, "p4": 4}
        team_config = TeamConfig(
            team_type=TeamType.SOLO,
            solo_player="wolf",
            opponents=["p2", "p3", "p4"]
        )
        result = self.service.calculate_hole_points(scores, team_config, wager=2)

        assert result.winners == ["wolf"]
        assert set(result.losers) == {"p2", "p3", "p4"}
        # Solo player wins 2 * 3 = 6 points
        assert result.points_changes["wolf"] == 6
        assert result.points_changes["p2"] == -2
        assert result.points_changes["p3"] == -2
        assert result.points_changes["p4"] == -2
        assert not result.halved
        assert result.team_type == TeamType.SOLO

    def test_solo_player_loses(self):
        """Test solo scoring when solo player loses."""
        scores = {"wolf": 5, "p2": 4, "p3": 5, "p4": 6}
        team_config = TeamConfig(
            team_type=TeamType.SOLO,
            solo_player="wolf",
            opponents=["p2", "p3", "p4"]
        )
        result = self.service.calculate_hole_points(scores, team_config, wager=2)

        assert result.winners == ["p2", "p3", "p4"]
        assert result.losers == ["wolf"]
        # Solo player loses 2 * 3 = 6 points
        assert result.points_changes["wolf"] == -6
        assert result.points_changes["p2"] == 2
        assert result.points_changes["p3"] == 2
        assert result.points_changes["p4"] == 2
        assert not result.halved

    def test_solo_halved(self):
        """Test solo scoring when hole is halved."""
        scores = {"wolf": 4, "p2": 4, "p3": 5, "p4": 6}
        team_config = TeamConfig(
            team_type=TeamType.SOLO,
            solo_player="wolf",
            opponents=["p2", "p3", "p4"]
        )
        result = self.service.calculate_hole_points(scores, team_config, wager=2)

        assert result.winners == []
        assert result.losers == []
        assert all(v == 0 for v in result.points_changes.values())
        assert result.halved

    def test_solo_no_player_raises(self):
        """Test that missing solo player raises error."""
        scores = {"p1": 4, "p2": 5}
        team_config = TeamConfig(
            team_type=TeamType.SOLO,
            solo_player=None,
            opponents=["p1", "p2"]
        )
        with pytest.raises(ValueError, match="solo_player required"):
            self.service.calculate_hole_points(scores, team_config, wager=2)

    def test_solo_no_opponents_raises(self):
        """Test that missing opponents raises error."""
        scores = {"wolf": 4}
        team_config = TeamConfig(
            team_type=TeamType.SOLO,
            solo_player="wolf",
            opponents=[]
        )
        with pytest.raises(ValueError, match="Solo player must have opponents"):
            self.service.calculate_hole_points(scores, team_config, wager=2)


class TestAllVsAllScoring:
    """Test all vs all (skins-like) scoring calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScoreCalculationService()

    def test_single_winner_takes_all(self):
        """Test all vs all with single winner."""
        scores = {"p1": 3, "p2": 4, "p3": 5, "p4": 4}
        team_config = TeamConfig(team_type=TeamType.ALL_VS_ALL)
        result = self.service.calculate_hole_points(scores, team_config, wager=1)

        assert result.winners == ["p1"]
        assert set(result.losers) == {"p2", "p3", "p4"}
        # Winner takes 1 * 3 = 3 points
        assert result.points_changes["p1"] == 3
        assert result.points_changes["p2"] == -1
        assert result.points_changes["p3"] == -1
        assert result.points_changes["p4"] == -1
        assert not result.halved
        assert result.team_type == TeamType.ALL_VS_ALL

    def test_tie_pushes_hole(self):
        """Test all vs all with tie (push)."""
        scores = {"p1": 4, "p2": 4, "p3": 5, "p4": 6}
        team_config = TeamConfig(team_type=TeamType.ALL_VS_ALL)
        result = self.service.calculate_hole_points(scores, team_config, wager=1)

        assert set(result.winners) == {"p1", "p2"}
        assert set(result.losers) == {"p3", "p4"}
        # Hole is pushed when tied
        assert result.halved
        assert all(v == 0 for v in result.points_changes.values())

    def test_empty_scores_raises(self):
        """Test that empty scores raises error."""
        team_config = TeamConfig(team_type=TeamType.ALL_VS_ALL)
        with pytest.raises(ValueError, match="No scores provided"):
            self.service.calculate_hole_points({}, team_config, wager=1)


class TestSpecialRules:
    """Test special rule applications."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScoreCalculationService()

    def test_duncan_rule_multiplier(self):
        """Test Duncan rule applies 1.5x multiplier."""
        scores = {"p1": 3, "p2": 5, "p3": 5, "p4": 5}
        team_config = TeamConfig(
            team_type=TeamType.SOLO,
            solo_player="p1",
            opponents=["p2", "p3", "p4"]
        )
        result = self.service.calculate_hole_points(
            scores, team_config, wager=2,
            apply_special_rules=True,
            special_rules={"duncan": True}
        )

        # Base: 2 * 3 = 6, with 1.5x = 9
        assert result.points_changes["p1"] == 9

    def test_tunkarri_rule_multiplier(self):
        """Test Tunkarri rule applies same 1.5x multiplier."""
        scores = {"p1": 3, "p2": 5, "p3": 5, "p4": 5}
        team_config = TeamConfig(
            team_type=TeamType.SOLO,
            solo_player="p1",
            opponents=["p2", "p3", "p4"]
        )
        result = self.service.calculate_hole_points(
            scores, team_config, wager=2,
            apply_special_rules=True,
            special_rules={"tunkarri": True}
        )

        # Base: 2 * 3 = 6, with 1.5x = 9
        assert result.points_changes["p1"] == 9

    def test_double_down_multiplier(self):
        """Test double down rule doubles all points."""
        scores = {"p1": 3, "p2": 5, "p3": 5, "p4": 5}
        team_config = TeamConfig(
            team_type=TeamType.SOLO,
            solo_player="p1",
            opponents=["p2", "p3", "p4"]
        )
        result = self.service.calculate_hole_points(
            scores, team_config, wager=2,
            apply_special_rules=True,
            special_rules={"double_down": True}
        )

        # Base: 2 * 3 = 6, with 2x = 12
        assert result.points_changes["p1"] == 12
        # Losers also doubled
        assert result.points_changes["p2"] == -4

    def test_no_special_rules_on_halved(self):
        """Test special rules don't apply when hole is halved."""
        scores = {"p1": 4, "p2": 4, "p3": 4, "p4": 4}
        team_config = TeamConfig(
            team_type=TeamType.SOLO,
            solo_player="p1",
            opponents=["p2", "p3", "p4"]
        )
        result = self.service.calculate_hole_points(
            scores, team_config, wager=2,
            apply_special_rules=True,
            special_rules={"duncan": True}
        )

        # Should be halved, no multipliers applied
        assert result.halved
        assert all(v == 0 for v in result.points_changes.values())


class TestKarlMarxRule:
    """Test Karl Marx distribution rule."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScoreCalculationService()

    def test_karl_marx_distribution_basics(self):
        """Test basic Karl Marx distribution logic."""
        winners = ["p1", "p2"]
        losers = ["p3", "p4"]
        standings = {"p1": -5, "p2": 0, "p3": 5, "p4": 10}  # p1 is down, p4 is up

        result = self.service.apply_karl_marx_rule(
            winners=winners,
            losers=losers,
            wager=4,
            current_standings=standings
        )

        # Higher standing loser (p4) should pay more
        # Lower standing winner (p1) should receive more
        assert result["p4"] < result["p3"] or result["p4"] == result["p3"]
        assert result["p1"] >= result["p2"] or result["p1"] == result["p2"]

    def test_karl_marx_empty_lists(self):
        """Test Karl Marx with empty winner/loser lists."""
        result = self.service.apply_karl_marx_rule(
            winners=[],
            losers=["p1", "p2"],
            wager=2,
            current_standings={"p1": 0, "p2": 0}
        )
        assert all(v == 0 for v in result.values())


class TestUtilityMethods:
    """Test utility methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScoreCalculationService()

    def test_compare_scores_gross(self):
        """Test comparing gross scores."""
        scores = {"p1": 4, "p2": 5, "p3": 4}
        winners, best_score = self.service.compare_scores(scores, use_net=False)

        assert set(winners) == {"p1", "p3"}
        assert best_score == 4

    def test_compare_scores_net_with_handicaps(self):
        """Test comparing net scores with handicaps."""
        scores = {"p1": 5, "p2": 4, "p3": 5}
        handicaps = {"p1": 18.0, "p2": 0.0, "p3": 10.0}
        # p1 gets 1 stroke on hole index 9 -> net 4
        # p2 gets 0 strokes -> net 4
        # p3 might or might not get stroke based on calculation
        winners, best_score = self.service.compare_scores(
            scores, use_net=True, handicaps=handicaps, hole_handicap_index=9
        )

        # Both p1 and p2 should have net 4
        assert "p1" in winners
        assert "p2" in winners

    def test_calculate_strokes_received_no_handicap(self):
        """Test no strokes received with 0 handicap."""
        strokes = self.service._calculate_strokes_received(handicap=0, hole_handicap_index=1)
        assert strokes == 0

    def test_calculate_strokes_received_18_handicap(self):
        """Test strokes with 18 handicap."""
        # 18 handicap gets 1 stroke per hole
        strokes = self.service._calculate_strokes_received(handicap=18, hole_handicap_index=1)
        assert strokes == 1

    def test_calculate_strokes_received_36_handicap(self):
        """Test strokes with 36 handicap."""
        # 36 handicap gets 2 strokes per hole
        strokes = self.service._calculate_strokes_received(handicap=36, hole_handicap_index=1)
        assert strokes == 2

    def test_calculate_final_standings(self):
        """Test calculating final standings from hole results."""
        results = [
            HoleResult(
                points_changes={"p1": 2, "p2": -2},
                winners=["p1"], losers=["p2"],
                message="", halved=False,
                team_type=TeamType.ALL_VS_ALL, wager=2
            ),
            HoleResult(
                points_changes={"p1": -1, "p2": 1},
                winners=["p2"], losers=["p1"],
                message="", halved=False,
                team_type=TeamType.ALL_VS_ALL, wager=1
            ),
        ]

        standings = self.service.calculate_final_standings(results)
        assert standings["p1"] == 1  # 2 - 1 = 1
        assert standings["p2"] == -1  # -2 + 1 = -1


class TestSingletonPattern:
    """Test singleton pattern for service."""

    def test_get_service_returns_same_instance(self):
        """Test that get_score_calculation_service returns same instance."""
        service1 = get_score_calculation_service()
        service2 = get_score_calculation_service()
        assert service1 is service2

    def test_service_is_initialized(self):
        """Test that service is properly initialized."""
        service = get_score_calculation_service()
        assert service._initialized is True


class TestTeamConfigDataclass:
    """Test TeamConfig dataclass initialization."""

    def test_default_values(self):
        """Test TeamConfig default values."""
        config = TeamConfig(team_type=TeamType.PARTNERS)
        assert config.team1 == []
        assert config.team2 == []
        assert config.opponents == []
        assert config.solo_player is None

    def test_with_values(self):
        """Test TeamConfig with provided values."""
        config = TeamConfig(
            team_type=TeamType.PARTNERS,
            team1=["p1", "p2"],
            team2=["p3", "p4"]
        )
        assert config.team1 == ["p1", "p2"]
        assert config.team2 == ["p3", "p4"]


class TestInvalidTeamType:
    """Test handling of invalid team types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScoreCalculationService()

    def test_invalid_team_type_raises(self):
        """Test that invalid team type raises error."""
        # Create a mock config with invalid team type
        from unittest.mock import Mock
        config = Mock()
        config.team_type = "invalid"

        with pytest.raises(ValueError, match="Unknown team type"):
            self.service.calculate_hole_points({"p1": 4}, config, wager=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
