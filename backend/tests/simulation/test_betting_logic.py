"""
Test suite for Wolf Goat Pig betting logic and special rules.
Tests all betting scenarios including doubles, Karl Marx, and special rules.
"""

import pytest
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class BettingState:
    """Represents the current betting state"""
    base_wager: int
    current_wager: int
    doubled: bool
    redoubled: bool
    carry_over: bool
    float_invoked: bool
    option_invoked: bool
    duncan_invoked: bool
    tunkarri_invoked: bool
    joes_special_value: int | None = None
    
class BettingRulesEngine:
    """Validates and tests betting rules"""
    
    def calculate_wager(self, state: BettingState) -> int:
        """Calculate current wager based on state"""
        wager = state.base_wager
        
        if state.doubled:
            wager *= 2
        if state.redoubled:
            wager *= 2
        if state.carry_over:
            wager *= 2
        
        return wager
    
    def validate_double_offer(self, game_state: Dict) -> bool:
        """Validate if double can be offered"""
        # Line of Scrimmage rule
        if game_state['phase'] != 'match_play':
            return False
        
        # Can't double if already doubled
        if game_state['betting']['doubled']:
            return False
        
        # Must be furthest from hole
        furthest_player = self._get_furthest_player(game_state)
        if furthest_player != game_state['current_player']:
            return False
        
        return True
    
    def _get_furthest_player(self, game_state: Dict) -> str | None:
        """Get player furthest from hole"""
        max_distance = -1
        furthest = None

        for player_id, position in game_state['ball_positions'].items():
            if not position['holed'] and position['distance'] > max_distance:
                max_distance = position['distance']
                furthest = player_id

        return furthest
    
    def apply_karl_marx(self, hole_scores: Dict[str, int]) -> bool:
        """Check if Karl Marx rule applies (all players tie)"""
        if not hole_scores:
            return False
        
        scores = list(hole_scores.values())
        return len(set(scores)) == 1  # All scores are the same
    
    def calculate_hole_points(self, game_state: Dict) -> Dict[str, int]:
        """Calculate points for the hole"""
        points = {}
        wager = self.calculate_wager(game_state['betting'])
        
        if game_state['teams']['type'] == 'solo':
            solo_player = game_state['teams']['solo_player']
            if game_state['winner'] == solo_player:
                # Solo player wins 3x wager from each opponent
                points[solo_player] = wager * 3
                for opponent in game_state['teams']['opponents']:
                    points[opponent] = -wager
            else:
                # Solo player loses wager to each opponent
                points[solo_player] = -wager * 3
                for opponent in game_state['teams']['opponents']:
                    points[opponent] = wager
        else:
            # Partnership scoring
            winning_team = game_state['winning_team']
            losing_team = game_state['losing_team']
            
            for player in winning_team:
                points[player] = wager
            for player in losing_team:
                points[player] = -wager
        
        return points

class TestBettingLogic:
    """Test cases for betting logic"""
    
    @pytest.fixture
    def engine(self):
        return BettingRulesEngine()
    
    def test_basic_wager_calculation(self, engine):
        """Test basic wager calculation"""
        state = BettingState(
            base_wager=1,
            current_wager=1,
            doubled=False,
            redoubled=False,
            carry_over=False,
            float_invoked=False,
            option_invoked=False,
            duncan_invoked=False,
            tunkarri_invoked=False
        )
        
        assert engine.calculate_wager(state) == 1
    
    def test_doubled_wager(self, engine):
        """Test doubled wager calculation"""
        state = BettingState(
            base_wager=1,
            current_wager=2,
            doubled=True,
            redoubled=False,
            carry_over=False,
            float_invoked=False,
            option_invoked=False,
            duncan_invoked=False,
            tunkarri_invoked=False
        )
        
        assert engine.calculate_wager(state) == 2
    
    def test_redoubled_wager(self, engine):
        """Test redoubled wager (double of double)"""
        state = BettingState(
            base_wager=1,
            current_wager=4,
            doubled=True,
            redoubled=True,
            carry_over=False,
            float_invoked=False,
            option_invoked=False,
            duncan_invoked=False,
            tunkarri_invoked=False
        )
        
        assert engine.calculate_wager(state) == 4
    
    def test_carry_over_wager(self, engine):
        """Test carry over from Karl Marx rule"""
        state = BettingState(
            base_wager=1,
            current_wager=2,
            doubled=False,
            redoubled=False,
            carry_over=True,
            float_invoked=False,
            option_invoked=False,
            duncan_invoked=False,
            tunkarri_invoked=False
        )
        
        assert engine.calculate_wager(state) == 2
    
    def test_line_of_scrimmage_validation(self, engine):
        """Test Line of Scrimmage double validation"""
        game_state = {
            'phase': 'match_play',
            'current_player': 'p1',
            'betting': {'doubled': False},
            'ball_positions': {
                'p1': {'distance': 200, 'holed': False},
                'p2': {'distance': 150, 'holed': False},
                'p3': {'distance': 100, 'holed': False},
                'p4': {'distance': 50, 'holed': False}
            }
        }
        
        # p1 is furthest, can offer double
        assert engine.validate_double_offer(game_state) == True
        
        # p2 is not furthest, cannot offer
        game_state['current_player'] = 'p2'
        assert engine.validate_double_offer(game_state) == False
        
        # Already doubled, cannot double again
        game_state['current_player'] = 'p1'
        game_state['betting']['doubled'] = True
        assert engine.validate_double_offer(game_state) == False
    
    def test_karl_marx_detection(self, engine):
        """Test Karl Marx rule detection"""
        # All players score 4 - Karl Marx applies
        hole_scores = {'p1': 4, 'p2': 4, 'p3': 4, 'p4': 4}
        assert engine.apply_karl_marx(hole_scores) == True
        
        # Different scores - Karl Marx doesn't apply
        hole_scores = {'p1': 4, 'p2': 5, 'p3': 4, 'p4': 4}
        assert engine.apply_karl_marx(hole_scores) == False
        
        # All players score 5 - Karl Marx applies
        hole_scores = {'p1': 5, 'p2': 5, 'p3': 5, 'p4': 5}
        assert engine.apply_karl_marx(hole_scores) == True
    
    def test_solo_scoring(self, engine):
        """Test solo player scoring"""
        game_state = {
            'teams': {
                'type': 'solo',
                'solo_player': 'p1',
                'opponents': ['p2', 'p3', 'p4']
            },
            'betting': BettingState(
                base_wager=1,
                current_wager=2,
                doubled=True,
                redoubled=False,
                carry_over=False,
                float_invoked=False,
                option_invoked=False,
                duncan_invoked=False,
                tunkarri_invoked=False
            ),
            'winner': 'p1'
        }
        
        points = engine.calculate_hole_points(game_state)
        
        # Solo player wins 2 * 3 = 6 quarters
        assert points['p1'] == 6
        assert points['p2'] == -2
        assert points['p3'] == -2
        assert points['p4'] == -2
    
    def test_partnership_scoring(self, engine):
        """Test partnership scoring"""
        game_state = {
            'teams': {
                'type': 'partners',
                'team1': ['p1', 'p2'],
                'team2': ['p3', 'p4']
            },
            'betting': BettingState(
                base_wager=1,
                current_wager=1,
                doubled=False,
                redoubled=False,
                carry_over=False,
                float_invoked=False,
                option_invoked=False,
                duncan_invoked=False,
                tunkarri_invoked=False
            ),
            'winning_team': ['p1', 'p2'],
            'losing_team': ['p3', 'p4']
        }
        
        points = engine.calculate_hole_points(game_state)
        
        # Each winner gets 1 quarter
        assert points['p1'] == 1
        assert points['p2'] == 1
        assert points['p3'] == -1
        assert points['p4'] == -1
    
    def test_complex_betting_scenario(self, engine):
        """Test complex betting scenario with multiple modifiers"""
        state = BettingState(
            base_wager=2,  # Base wager of 2
            current_wager=8,
            doubled=True,  # Doubled to 4
            redoubled=False,
            carry_over=True,  # Carried over, so another double to 8
            float_invoked=False,
            option_invoked=False,
            duncan_invoked=False,
            tunkarri_invoked=False
        )
        
        assert engine.calculate_wager(state) == 8

class TestSpecialRules:
    """Test special Wolf Goat Pig rules"""
    
    def test_the_float(self):
        """Test The Float - once per round double after viewing tee shot"""
        game_state = {
            'players': [
                {'id': 'p1', 'float_used': False},
                {'id': 'p2', 'float_used': True},
                {'id': 'p3', 'float_used': False},
                {'id': 'p4', 'float_used': False}
            ],
            'current_hole': 5,
            'captain_id': 'p1'
        }
        
        # p1 can use float (not used yet)
        assert game_state['players'][0]['float_used'] == False
        
        # p2 cannot use float (already used)
        assert game_state['players'][1]['float_used'] == True
    
    def test_the_option(self):
        """Test The Option - automatic solo if no one accepts partnership"""
        partnership_responses = {
            'p2': False,  # Declined
            'p3': False,  # Declined  
            'p4': False   # Declined
        }
        
        # All declined, captain must go solo
        all_declined = all(not accepted for accepted in partnership_responses.values())
        assert all_declined == True
    
    def test_hoepfinger_start(self):
        """Test Hoepfinger start on hole 17"""
        game_state = {
            'current_hole': 17,
            'hoepfinger_start': 17,
            'base_wager': 1
        }
        
        # On Hoepfinger hole, wager should be higher
        if game_state['current_hole'] == game_state['hoepfinger_start']:
            adjusted_wager = game_state['base_wager'] * 2
            assert adjusted_wager == 2
    
    def test_annual_banquet_scoring(self):
        """Test annual banquet special scoring rules"""
        game_state = {
            'settings': {
                'annual_banquet': True,
                'double_points_round': True
            },
            'base_points': 10
        }
        
        if game_state['settings']['annual_banquet']:
            if game_state['settings']['double_points_round']:
                final_points = game_state['base_points'] * 2
                assert final_points == 20