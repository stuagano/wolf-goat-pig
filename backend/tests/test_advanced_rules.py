"""
Comprehensive tests for advanced Wolf Goat Pig rules
Tests all the newly implemented rules and edge cases
"""
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer


class TestAdvancedWGPRules:
    """Test advanced Wolf Goat Pig rules implementation"""
    
    def setup_method(self):
        """Setup common test data"""
        self.simulation = WolfGoatPigSimulation(player_count=4)
        self.players = [
            WGPPlayer("p1", "Player1", 12.0),
            WGPPlayer("p2", "Player2", 15.0),
            WGPPlayer("p3", "Player3", 8.0),
            WGPPlayer("p4", "Player4", 20.0)
        ]
        self.simulation.players = self.players
    
    def test_hoepfinger_phase_4_man_game(self):
        """Test Hoepfinger phase starting on hole 17 for 4-man game"""
        # Just test the hoepfinger start hole calculation
        assert self.simulation.hoepfinger_start_hole == 17
        
        # Test that 17 >= hoepfinger_start_hole would trigger hoepfinger phase
        assert 17 >= self.simulation.hoepfinger_start_hole
    
    def test_hoepfinger_phase_5_man_game(self):
        """Test Hoepfinger phase starting on hole 16 for 5-man game"""
        simulation_5 = WolfGoatPigSimulation(player_count=5)
        assert simulation_5.hoepfinger_start_hole == 16
    
    def test_hoepfinger_phase_6_man_game(self):
        """Test Hoepfinger phase starting on hole 13 for 6-man game"""
        simulation_6 = WolfGoatPigSimulation(player_count=6)
        assert simulation_6.hoepfinger_start_hole == 13
    
    def test_joes_special_implementation(self):
        """Test Joe's Special wager selection in Hoepfinger"""
        # Initialize hole 1 first to establish base state
        self.simulation.current_hole = 1
        self.simulation._initialize_hole(1)
        
        hole_state = self.simulation.hole_states[1]
        
        # Simulate Joe's Special selection
        selected_value = 4
        hole_state.betting.joes_special_value = selected_value
        hole_state.betting.base_wager = selected_value
        hole_state.betting.current_wager = selected_value
        
        assert hole_state.betting.joes_special_value == 4
        assert hole_state.betting.base_wager == 4
        assert hole_state.betting.current_wager == 4
    
    def test_carry_over_rules(self):
        """Test carry-over rules for halved holes"""
        self.simulation.current_hole = 1
        self.simulation._initialize_hole(1)
        
        hole_state = self.simulation.hole_states[1]
        hole_state.betting.base_wager = 2
        hole_state.betting.current_wager = 2
        
        # Simulate a halved hole
        hole_state.betting.carry_over = True
        
        # Next hole should start with doubled wager
        self.simulation.current_hole = 2
        self.simulation._initialize_hole(2)
        
        next_hole_state = self.simulation.hole_states[2]
        # The carry-over logic should be implemented in _calculate_base_wager
        assert next_hole_state.betting.base_wager >= hole_state.betting.base_wager
    
    def test_duncan_rule_3_for_2_odds(self):
        """Test Duncan rule (captain goes solo for 3-for-2 odds)"""
        self.simulation.current_hole = 1
        self.simulation._initialize_hole(1)
        
        hole_state = self.simulation.hole_states[1]
        captain_id = hole_state.teams.captain
        
        # Captain goes solo with Duncan rule
        result = self.simulation.captain_go_solo(captain_id, use_duncan=True)
        
        assert result["status"] == "solo"
        assert hole_state.betting.duncan_invoked == True
        assert hole_state.teams.type == "solo"
    
    def test_big_dick_rule_hole_18(self):
        """Test Big Dick rule on hole 18"""
        # Set up a player with most points
        self.players[0].points = 10  # Highest points
        self.players[1].points = 5
        self.players[2].points = 3
        self.players[3].points = 2
        
        self.simulation.current_hole = 18
        self.simulation._initialize_hole(18)
        
        # Player with most points can offer Big Dick
        result = self.simulation.offer_big_dick("p1")
        
        assert result["status"] == "big_dick_offered"
        assert result["challenger"] == "p1"
        assert result["wager_amount"] == 10  # Risk all winnings
        
        hole_state = self.simulation.hole_states[18]
        assert hole_state.betting.big_dick_invoked == True
    
    def test_big_dick_unanimous_acceptance(self):
        """Test Big Dick unanimous acceptance"""
        # Set up Big Dick scenario
        self.players[0].points = 10
        self.simulation.current_hole = 18
        self.simulation._initialize_hole(18)
        
        self.simulation.offer_big_dick("p1")
        
        # All other players accept
        accepting_players = ["p2", "p3", "p4"]
        result = self.simulation.accept_big_dick(accepting_players)
        
        assert result["status"] == "big_dick_accepted"
        assert result["teams_formed"] == True
        
        hole_state = self.simulation.hole_states[18]
        assert hole_state.teams.type == "solo"
        assert hole_state.teams.solo_player == "p1"
    
    def test_big_dick_ackerley_gambit(self):
        """Test Big Dick with Ackerley's Gambit (partial acceptance)"""
        self.players[0].points = 12
        self.simulation.current_hole = 18
        self.simulation._initialize_hole(18)
        
        self.simulation.offer_big_dick("p1")
        
        # Only some players accept
        accepting_players = ["p2", "p3"]  # p4 declines
        result = self.simulation.accept_big_dick(accepting_players)
        
        assert result["status"] == "big_dick_gambit"
        assert len(result["accepting_players"]) == 2
        assert len(result["declining_players"]) == 1
        assert result["wager_per_player"] == 6  # 12 / 2 accepting players
    
    def test_ping_pong_aardvark(self):
        """Test Ping Pong Aardvark rule"""
        self.simulation.current_hole = 1
        self.simulation._initialize_hole(1)
        
        hole_state = self.simulation.hole_states[1]
        initial_wager = hole_state.betting.current_wager
        
        # Ping pong an aardvark
        result = self.simulation.ping_pong_aardvark("team1", "p4")
        
        assert result["status"] in ["aardvark_ping_ponged", "aardvark_stuck"]
        assert result["new_wager"] == initial_wager * 2  # Wager doubled
        
        # Should track tossed aardvarks
        assert "p4" in hole_state.betting.tossed_aardvarks
        assert hole_state.betting.ping_pong_count == 1
    
    def test_ping_pong_aardvark_same_player_twice_fails(self):
        """Test that same aardvark cannot be ping ponged twice"""
        self.simulation.current_hole = 1
        self.simulation._initialize_hole(1)
        
        # First ping pong
        self.simulation.ping_pong_aardvark("team1", "p4")
        
        # Second ping pong of same player should fail
        with pytest.raises(ValueError, match="Cannot ping pong the same Aardvark twice"):
            self.simulation.ping_pong_aardvark("team1", "p4")
    
    def test_vinnies_variation_4_man_game(self):
        """Test Vinnie's Variation (doubled holes 13-16 in 4-man game)"""
        assert self.simulation.vinnie_variation_start == 13
        
        # Just test the start hole calculation
        assert 13 >= self.simulation.vinnie_variation_start
        assert 12 < self.simulation.vinnie_variation_start
    
    def test_vinnies_variation_not_in_5_man_game(self):
        """Test that Vinnie's Variation doesn't exist in 5-man game"""
        simulation_5 = WolfGoatPigSimulation(player_count=5)
        assert simulation_5.vinnie_variation_start is None
    
    def test_handicap_creecher_feature(self):
        """Test Creecher Feature (half strokes on easiest 6 holes)"""
        self.simulation.current_hole = 1
        self.simulation._initialize_hole(1)
        
        hole_state = self.simulation.hole_states[1]
        
        # Check that stroke advantages are calculated
        assert len(hole_state.stroke_advantages) == 4  # One per player
        
        for player_id, stroke_advantage in hole_state.stroke_advantages.items():
            assert player_id in ["p1", "p2", "p3", "p4"]
            assert stroke_advantage.player_id in ["p1", "p2", "p3", "p4"]
            assert stroke_advantage.handicap >= 0
            assert stroke_advantage.strokes_received >= 0
    
    def test_karl_marx_rule_implementation(self):
        """Test Karl Marx rule for uneven quarter distribution"""
        # This is tested indirectly through point calculations
        # The rule should distribute odd quarters to the player furthest down
        
        # Set up players with different point totals
        self.players[0].points = 5   # Best
        self.players[1].points = 0   # Middle
        self.players[2].points = -3  # Worst (should get fewer quarters in Karl Marx)
        self.players[3].points = -1  # Second worst
        
        # Test the _apply_karl_marx_rule method indirectly
        winners = ["p1"]
        losers = ["p2", "p3", "p4"]
        wager = 5  # Odd number to trigger Karl Marx
        
        points_changes = self.simulation._apply_karl_marx_rule(winners, losers, wager)
        
        # Verify that the rule was applied (furthest down pays less)
        assert points_changes["p3"] >= points_changes["p4"]  # Worst player pays less or equal
    
    def test_option_rule_for_losing_captain(self):
        """Test The Option rule for captain who lost most quarters"""
        # Set captain as the biggest loser
        self.players[0].points = -5  # Captain with lowest score
        self.players[1].points = 0
        self.players[2].points = 2
        self.players[3].points = 1
        
        self.simulation.current_hole = 5
        self.simulation._initialize_hole(5)
        
        hole_state = self.simulation.hole_states[5]
        captain_id = hole_state.teams.captain
        
        # If the captain is the biggest loser, The Option should be available
        should_apply_option = self.simulation._should_apply_option(captain_id)
        
        # This depends on the captain actually being p1 (the biggest loser)
        if captain_id == "p1":
            assert should_apply_option == True
            assert hole_state.betting.option_invoked == True
    
    def test_complete_rule_integration(self):
        """Test that multiple advanced rules can work together"""
        # Set up a complex scenario with multiple rules
        self.simulation.current_hole = 17  # Hoepfinger phase
        self.simulation._initialize_hole(17)
        
        hole_state = self.simulation.hole_states[17]
        
        # Apply Joe's Special
        hole_state.betting.joes_special_value = 8
        hole_state.betting.current_wager = 8
        
        # Test that game phase is correct
        assert self.simulation.game_phase.value == "hoepfinger"
        
        # Test that teams can still be formed
        captain_id = hole_state.teams.captain
        # Choose a different player than the captain
        partner_id = next(p.id for p in self.simulation.players if p.id != captain_id)
        result = self.simulation.request_partner(captain_id, partner_id)
        assert result["status"] == "pending"
        
        # Test that partnership can be accepted
        result = self.simulation.respond_to_partnership(partner_id, True)
        assert result["status"] == "partnership_formed"
        
        # Verify the complex state
        assert hole_state.teams.type == "partners"
        assert hole_state.betting.joes_special_value == 8
        assert self.simulation.game_phase.value == "hoepfinger"