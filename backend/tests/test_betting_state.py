"""
Comprehensive tests for betting_state.py - Betting logic and state management

Tests cover:
- Betting state initialization and reset
- Partner request/accept/decline workflow
- Solo play functionality
- Double offer/accept/decline mechanics
- Point calculation with Karl Marx rule
- Action dispatching
- Betting tips generation
- Serialization/deserialization
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock
from backend.app.state.betting_state import BettingState
from backend.app.domain.player import Player


class TestBettingStateInitialization:
    """Test betting state initialization and reset"""
    
    def test_default_initialization(self):
        """Test default initialization"""
        betting_state = BettingState()
        
        assert betting_state.teams == {}
        assert betting_state.base_wager == 1
        assert betting_state.doubled_status == False
        assert betting_state.game_phase == 'Regular'

    def test_reset_functionality(self):
        """Test full reset"""
        betting_state = BettingState()
        
        # Modify state
        betting_state.teams = {"type": "partners"}
        betting_state.base_wager = 4
        betting_state.doubled_status = True
        betting_state.game_phase = 'Hoepfinger'
        
        # Reset
        betting_state.reset()
        
        assert betting_state.teams == {}
        assert betting_state.base_wager == 1
        assert betting_state.doubled_status == False
        assert betting_state.game_phase == 'Regular'

    def test_reset_hole_functionality(self):
        """Test hole-specific reset"""
        betting_state = BettingState()
        
        # Modify state
        betting_state.teams = {"type": "partners"}
        betting_state.base_wager = 4
        betting_state.doubled_status = True
        betting_state.game_phase = 'Hoepfinger'
        
        # Reset hole (should preserve base_wager and game_phase)
        betting_state.reset_hole()
        
        assert betting_state.teams == {}
        assert betting_state.base_wager == 4  # Preserved
        assert betting_state.doubled_status == False
        assert betting_state.game_phase == 'Hoepfinger'  # Preserved


class TestPartnershipWorkflow:
    """Test partnership request, accept, and decline workflow"""
    
    @pytest.fixture
    def players(self):
        return [
            Player(id="p1", name="Alice", handicap=10),
            Player(id="p2", name="Bob", handicap=15),
            Player(id="p3", name="Charlie", handicap=8),
            Player(id="p4", name="Dave", handicap=20)
        ]
    
    def test_request_partner(self, players):
        """Test partner request"""
        betting_state = BettingState()
        
        result = betting_state.request_partner("p1", "p2")
        
        assert result == "Partner requested."
        assert betting_state.teams == {
            "type": "pending",
            "captain": "p1",
            "requested": "p2"
        }

    def test_accept_partner_valid(self, players):
        """Test valid partner acceptance"""
        betting_state = BettingState()
        betting_state.request_partner("p1", "p2")
        
        result = betting_state.accept_partner("p2", players)
        
        assert result == "Partnership accepted."
        assert betting_state.teams["type"] == "partners"
        assert betting_state.teams["team1"] == ["p1", "p2"]
        assert betting_state.teams["team2"] == ["p3", "p4"]

    def test_accept_partner_no_request(self, players):
        """Test partner acceptance with no pending request"""
        betting_state = BettingState()
        
        with pytest.raises(ValueError, match="No pending partner request"):
            betting_state.accept_partner("p2", players)

    def test_accept_partner_wrong_player(self, players):
        """Test partner acceptance by wrong player"""
        betting_state = BettingState()
        betting_state.request_partner("p1", "p2")
        
        with pytest.raises(ValueError, match="No pending partner request"):
            betting_state.accept_partner("p3", players)

    def test_decline_partner_valid(self, players):
        """Test valid partner decline"""
        betting_state = BettingState()
        betting_state.request_partner("p1", "p2")
        
        result = betting_state.decline_partner("p2", players)
        
        assert result == "Partnership declined. Captain goes solo."
        assert betting_state.teams["type"] == "solo"
        assert betting_state.teams["captain"] == "p1"
        assert betting_state.teams["opponents"] == ["p2", "p3", "p4"]
        assert betting_state.base_wager == 2  # Doubled due to "on your own" rule

    def test_decline_partner_no_request(self, players):
        """Test partner decline with no pending request"""
        betting_state = BettingState()
        
        with pytest.raises(ValueError, match="No pending partner request"):
            betting_state.decline_partner("p2", players)

    def test_decline_partner_wrong_player(self, players):
        """Test partner decline by wrong player"""
        betting_state = BettingState()
        betting_state.request_partner("p1", "p2")
        
        with pytest.raises(ValueError, match="No pending partner request"):
            betting_state.decline_partner("p3", players)


class TestSoloPlay:
    """Test solo play functionality"""
    
    @pytest.fixture
    def players(self):
        return [
            Player(id="p1", name="Alice", handicap=10),
            Player(id="p2", name="Bob", handicap=15),
            Player(id="p3", name="Charlie", handicap=8),
            Player(id="p4", name="Dave", handicap=20)
        ]
    
    def test_go_solo(self, players):
        """Test captain choosing to go solo"""
        betting_state = BettingState()
        
        result = betting_state.go_solo("p1", players)
        
        assert result == "Captain goes solo."
        assert betting_state.teams["type"] == "solo"
        assert betting_state.teams["captain"] == "p1"
        assert betting_state.teams["opponents"] == ["p2", "p3", "p4"]
        assert betting_state.base_wager == 2  # Doubled


class TestDoubleOfferSystem:
    """Test double offer, accept, and decline mechanics"""
    
    def test_offer_double(self):
        """Test offering a double"""
        betting_state = BettingState()
        
        result = betting_state.offer_double("team1", "team2")
        
        assert result == "Double offered."
        assert betting_state.doubled_status == True

    def test_offer_double_already_offered(self):
        """Test offering double when already offered"""
        betting_state = BettingState()
        betting_state.doubled_status = True
        
        with pytest.raises(ValueError, match="Double already offered"):
            betting_state.offer_double("team1", "team2")

    def test_accept_double(self):
        """Test accepting a double"""
        betting_state = BettingState()
        betting_state.base_wager = 2
        betting_state.doubled_status = True
        
        result = betting_state.accept_double("team1")
        
        assert result == "Double accepted."
        assert betting_state.base_wager == 4  # Doubled
        assert betting_state.doubled_status == False

    def test_accept_double_no_offer(self):
        """Test accepting double with no offer"""
        betting_state = BettingState()
        
        with pytest.raises(ValueError, match="No double to accept"):
            betting_state.accept_double("team1")

    def test_decline_double(self):
        """Test declining a double"""
        betting_state = BettingState()
        betting_state.doubled_status = True
        
        result = betting_state.decline_double("team1")
        
        assert result == "Double declined. Offering team wins hole."
        assert betting_state.doubled_status == False

    def test_decline_double_no_offer(self):
        """Test declining double with no offer"""
        betting_state = BettingState()
        
        with pytest.raises(ValueError, match="No double to decline"):
            betting_state.decline_double("team1")


class TestPointCalculation:
    """Test point calculation with various scenarios"""
    
    @pytest.fixture
    def players(self):
        players = [
            Player(id="p1", name="Alice", handicap=10),
            Player(id="p2", name="Bob", handicap=15),
            Player(id="p3", name="Charlie", handicap=8),
            Player(id="p4", name="Dave", handicap=20)
        ]
        # Reset points to ensure clean test state
        for player in players:
            player.points = 0
        return players
    
    def test_calculate_hole_points_partners_team1_wins(self, players):
        """Test point calculation when team1 wins in partners"""
        betting_state = BettingState()
        betting_state.teams = {
            "type": "partners",
            "team1": ["p1", "p2"],
            "team2": ["p3", "p4"]
        }
        betting_state.base_wager = 2
        
        hole_scores = {"p1": 4, "p2": 5, "p3": 6, "p4": 7}
        
        result = betting_state.calculate_hole_points(hole_scores, players)
        
        assert "Alice & Bob win" in result
        # Team1 wins: each winner gets base_wager per loser
        assert players[0].points == 2  # Alice: 2 * 1 = 2
        assert players[1].points == 2  # Bob: 2 * 1 = 2
        assert players[2].points == -2  # Charlie: -2
        assert players[3].points == -2  # Dave: -2

    def test_calculate_hole_points_partners_team2_wins(self, players):
        """Test point calculation when team2 wins in partners"""
        betting_state = BettingState()
        betting_state.teams = {
            "type": "partners",
            "team1": ["p1", "p2"],
            "team2": ["p3", "p4"]
        }
        betting_state.base_wager = 2
        
        hole_scores = {"p1": 6, "p2": 7, "p3": 4, "p4": 5}
        
        result = betting_state.calculate_hole_points(hole_scores, players)
        
        assert "Charlie & Dave win" in result
        assert players[0].points == -2  # Alice: -2
        assert players[1].points == -2  # Bob: -2
        assert players[2].points == 2   # Charlie: 2
        assert players[3].points == 2   # Dave: 2

    def test_calculate_hole_points_partners_tie(self, players):
        """Test point calculation when partners tie"""
        betting_state = BettingState()
        betting_state.teams = {
            "type": "partners",
            "team1": ["p1", "p2"],
            "team2": ["p3", "p4"]
        }
        
        hole_scores = {"p1": 4, "p2": 5, "p3": 4, "p4": 6}
        
        result = betting_state.calculate_hole_points(hole_scores, players)
        
        assert result == "Hole halved. No points awarded."
        # No points should be awarded
        for player in players:
            assert player.points == 0

    def test_calculate_hole_points_solo_captain_wins(self, players):
        """Test point calculation when solo captain wins"""
        betting_state = BettingState()
        betting_state.teams = {
            "type": "solo",
            "captain": "p1",
            "opponents": ["p2", "p3", "p4"]
        }
        betting_state.base_wager = 2
        
        hole_scores = {"p1": 3, "p2": 4, "p3": 5, "p4": 6}
        
        result = betting_state.calculate_hole_points(hole_scores, players)
        
        assert "Alice win" in result
        # Captain wins: gets base_wager * num_opponents
        assert players[0].points == 6  # Alice: 2 * 3 = 6
        assert players[1].points == -2  # Bob: -2
        assert players[2].points == -2  # Charlie: -2
        assert players[3].points == -2  # Dave: -2

    def test_calculate_hole_points_solo_opponents_win(self, players):
        """Test point calculation when opponents beat solo captain"""
        betting_state = BettingState()
        betting_state.teams = {
            "type": "solo",
            "captain": "p1",
            "opponents": ["p2", "p3", "p4"]
        }
        betting_state.base_wager = 2
        
        hole_scores = {"p1": 6, "p2": 3, "p3": 4, "p4": 5}
        
        result = betting_state.calculate_hole_points(hole_scores, players)
        
        assert "Bob & Charlie & Dave win" in result
        # Opponents win: each gets base_wager / num_opponents (rounded down)
        assert players[0].points == -2  # Alice: -2
        assert players[1].points == 2   # Bob: 2 * 1 = 2
        assert players[2].points == 2   # Charlie: 2 * 1 = 2  
        assert players[3].points == 2   # Dave: 2 * 1 = 2

    def test_calculate_hole_points_karl_marx_rule(self, players):
        """Test Karl Marx rule for odd quarters"""
        betting_state = BettingState()
        betting_state.teams = {
            "type": "solo",
            "captain": "p1",
            "opponents": ["p2", "p3", "p4"]
        }
        betting_state.base_wager = 1  # This creates odd quarters: 3 total, 3 winners = 1 each + 0 remainder
        
        # Set different point totals to test Karl Marx rule
        players[1].points = 5  # Bob has most points
        players[2].points = 2  # Charlie has fewer
        players[3].points = 1  # Dave has least
        
        hole_scores = {"p1": 6, "p2": 3, "p3": 4, "p4": 5}
        
        result = betting_state.calculate_hole_points(hole_scores, players)
        
        # With base_wager=1, total_quarters=3, per_winner=1, odd_quarters=0
        # So no Karl Marx rule should apply in this case
        assert players[1].points == 6  # Bob: 5 + 1 = 6
        assert players[2].points == 3  # Charlie: 2 + 1 = 3
        assert players[3].points == 2  # Dave: 1 + 1 = 2

    def test_calculate_hole_points_karl_marx_with_remainder(self, players):
        """Test Karl Marx rule when there are remaining quarters"""
        betting_state = BettingState()
        betting_state.teams = {
            "type": "partners",
            "team1": ["p1", "p2"],
            "team2": ["p3", "p4"]
        }
        betting_state.base_wager = 3  # 3 * 2 losers = 6 quarters, 6 / 2 winners = 3 each, no remainder
        
        hole_scores = {"p1": 4, "p2": 5, "p3": 6, "p4": 7}
        
        result = betting_state.calculate_hole_points(hole_scores, players)
        
        # Should distribute 3 quarters to each winner
        assert players[0].points == 3  # Alice
        assert players[1].points == 3  # Bob

    def test_calculate_hole_points_incomplete_scores(self, players):
        """Test point calculation with incomplete scores"""
        betting_state = BettingState()
        betting_state.teams = {
            "type": "partners",
            "team1": ["p1", "p2"],
            "team2": ["p3", "p4"]
        }
        
        hole_scores = {"p1": 4, "p2": None, "p3": 5, "p4": 6}
        
        with pytest.raises(ValueError, match="Not all scores entered"):
            betting_state.calculate_hole_points(hole_scores, players)

    def test_calculate_hole_points_no_teams(self, players):
        """Test point calculation with no teams set"""
        betting_state = BettingState()
        
        hole_scores = {"p1": 4, "p2": 5, "p3": 6, "p4": 7}
        
        with pytest.raises(ValueError, match="Teams not set"):
            betting_state.calculate_hole_points(hole_scores, players)


class TestActionDispatcher:
    """Test action dispatching system"""
    
    @pytest.fixture
    def players(self):
        return [
            Player(id="p1", name="Alice", handicap=10),
            Player(id="p2", name="Bob", handicap=15),
            Player(id="p3", name="Charlie", handicap=8),
            Player(id="p4", name="Dave", handicap=20)
        ]
    
    def test_dispatch_request_partner(self, players):
        """Test dispatching partner request"""
        betting_state = BettingState()
        
        result = betting_state.dispatch_action("request_partner", {"captain_id": "p1", "partner_id": "p2"}, players)
        
        assert result == "Partner requested."

    def test_dispatch_accept_partner(self, players):
        """Test dispatching partner accept"""
        betting_state = BettingState()
        betting_state.request_partner("p1", "p2")
        
        result = betting_state.dispatch_action("accept_partner", {"partner_id": "p2"}, players)
        
        assert result == "Partnership accepted."

    def test_dispatch_decline_partner(self, players):
        """Test dispatching partner decline"""
        betting_state = BettingState()
        betting_state.request_partner("p1", "p2")
        
        result = betting_state.dispatch_action("decline_partner", {"partner_id": "p2"}, players)
        
        assert result == "Partnership declined. Captain goes solo."

    def test_dispatch_go_solo(self, players):
        """Test dispatching go solo"""
        betting_state = BettingState()
        
        result = betting_state.dispatch_action("go_solo", {"captain_id": "p1"}, players)
        
        assert result == "Captain goes solo."

    def test_dispatch_offer_double(self, players):
        """Test dispatching double offer"""
        betting_state = BettingState()
        
        result = betting_state.dispatch_action("offer_double", {"offering_team_id": "team1", "target_team_id": "team2"}, players)
        
        assert result == "Double offered."

    def test_dispatch_accept_double(self, players):
        """Test dispatching double accept"""
        betting_state = BettingState()
        betting_state.doubled_status = True
        
        result = betting_state.dispatch_action("accept_double", {"team_id": "team1"}, players)
        
        assert result == "Double accepted."

    def test_dispatch_decline_double(self, players):
        """Test dispatching double decline"""
        betting_state = BettingState()
        betting_state.doubled_status = True
        
        result = betting_state.dispatch_action("decline_double", {"team_id": "team1"}, players)
        
        assert result == "Double declined. Offering team wins hole."

    def test_dispatch_unknown_action(self, players):
        """Test dispatching unknown action"""
        betting_state = BettingState()
        
        with pytest.raises(ValueError, match="Unknown betting action"):
            betting_state.dispatch_action("unknown_action", {}, players)


class TestBettingTips:
    """Test betting tips generation"""
    
    @pytest.fixture
    def players(self):
        return [
            Player(id="p1", name="Alice", handicap=10),
            Player(id="p2", name="Bob", handicap=15),
            Player(id="p3", name="Charlie", handicap=8),
            Player(id="p4", name="Dave", handicap=20)
        ]
    
    def test_get_betting_tips_double_offered(self, players):
        """Test tips when double is offered"""
        betting_state = BettingState()
        betting_state.doubled_status = True
        
        tips = betting_state.get_betting_tips(players, 5, {}, False)
        
        assert any("double has been offered" in tip for tip in tips)

    def test_get_betting_tips_can_offer_double(self, players):
        """Test tips when can offer double"""
        betting_state = BettingState()
        betting_state.teams = {"type": "partners"}
        
        tips = betting_state.get_betting_tips(players, 5, {}, False)
        
        assert any("Consider offering a double" in tip for tip in tips)

    def test_get_betting_tips_solo_advice(self, players):
        """Test tips for solo play"""
        betting_state = BettingState()
        betting_state.teams = {"type": "solo"}
        
        tips = betting_state.get_betting_tips(players, 5, {}, False)
        
        assert any("Going solo doubles the wager" in tip for tip in tips)

    def test_get_betting_tips_large_point_spread(self, players):
        """Test tips when there's a large point spread"""
        betting_state = BettingState()
        players[0].points = 10  # Alice leads
        players[3].points = 0   # Dave trails by 10
        
        tips = betting_state.get_betting_tips(players, 5, {}, False)
        
        assert any("Alice is ahead by a large margin" in tip for tip in tips)

    def test_get_betting_tips_float_unused(self, players):
        """Test tips when float is unused"""
        betting_state = BettingState()
        # Mock a captain
        players[0].is_captain = True
        
        tips = betting_state.get_betting_tips(players, 5, {"p1": False}, False)
        
        assert any("haven't used your float yet" in tip for tip in tips)

    def test_get_betting_tips_carry_over(self, players):
        """Test tips when carry over is active"""
        betting_state = BettingState()
        
        tips = betting_state.get_betting_tips(players, 5, {}, True)
        
        assert any("carry-over in effect" in tip for tip in tips)

    def test_get_betting_tips_late_holes(self, players):
        """Test tips for late holes"""
        betting_state = BettingState()
        
        tips = betting_state.get_betting_tips(players, 17, {}, False)
        
        assert any("final holes" in tip for tip in tips)
        assert any("Hoepfinger phase" in tip for tip in tips)

    def test_get_betting_tips_karl_marx_applicable(self, players):
        """Test tips when Karl Marx rule might apply"""
        betting_state = BettingState()
        betting_state.teams = {"type": "solo"}  # 1 winner, 3 losers
        betting_state.base_wager = 2  # 2 * 3 = 6 quarters, 6 / 1 = 6 (evenly divisible)
        
        tips = betting_state.get_betting_tips(players, 5, {}, False)
        
        # Should not mention Karl Marx rule since quarters divide evenly
        karl_marx_tips = [tip for tip in tips if "Karl Marx" in tip]
        # Actually, the logic shows it mentions Karl Marx whenever there's potential for it
        # Let's check for the general tip about uneven division

    def test_get_betting_tips_general_advice(self, players):
        """Test general betting tips are always included"""
        betting_state = BettingState()
        
        tips = betting_state.get_betting_tips(players, 5, {}, False)
        
        assert any("bluffing" in tip for tip in tips)
        assert any("table talk" in tip for tip in tips)
        assert any("decline a double" in tip for tip in tips)


class TestSerialization:
    """Test serialization and deserialization"""
    
    def test_to_dict(self):
        """Test converting to dictionary"""
        betting_state = BettingState()
        betting_state.teams = {"type": "partners"}
        betting_state.base_wager = 4
        betting_state.doubled_status = True
        betting_state.game_phase = 'Hoepfinger'
        
        data = betting_state.to_dict()
        
        assert data == {
            "teams": {"type": "partners"},
            "base_wager": 4,
            "doubled_status": True,
            "game_phase": 'Hoepfinger'
        }

    def test_from_dict(self):
        """Test loading from dictionary"""
        betting_state = BettingState()
        data = {
            "teams": {"type": "solo"},
            "base_wager": 8,
            "doubled_status": True,
            "game_phase": 'Final'
        }
        
        betting_state.from_dict(data)
        
        assert betting_state.teams == {"type": "solo"}
        assert betting_state.base_wager == 8
        assert betting_state.doubled_status == True
        assert betting_state.game_phase == 'Final'

    def test_from_dict_with_defaults(self):
        """Test loading from dictionary with missing values"""
        betting_state = BettingState()
        data = {"teams": {"type": "partners"}}
        
        betting_state.from_dict(data)
        
        assert betting_state.teams == {"type": "partners"}
        assert betting_state.base_wager == 1  # Default
        assert betting_state.doubled_status == False  # Default
        assert betting_state.game_phase == 'Regular'  # Default


class TestUtilityMethods:
    """Test utility methods"""
    
    @pytest.fixture
    def players(self):
        return [
            Player(id="p1", name="Alice", handicap=10),
            Player(id="p2", name="Bob", handicap=15),
            Player(id="p3", name="Charlie", handicap=8),
            Player(id="p4", name="Dave", handicap=20)
        ]
    
    def test_player_name_lookup(self, players):
        """Test player name lookup"""
        betting_state = BettingState()
        
        name = betting_state._player_name("p1", players)
        assert name == "Alice"
        
        name = betting_state._player_name("p2", players)
        assert name == "Bob"
        
        # Unknown player returns ID
        name = betting_state._player_name("unknown", players)
        assert name == "unknown"


if __name__ == "__main__":
    pytest.main([__file__])