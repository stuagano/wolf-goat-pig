"""
Game state validation and snapshot testing for Wolf Goat Pig simulation.
Ensures game state transitions are valid and consistent.
"""

import pytest
import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class GameStateSnapshot:
    """Represents a complete game state at a point in time"""
    hole_number: int
    phase: str
    captain_id: str
    teams: Dict[str, Any]
    betting: Dict[str, Any]
    ball_positions: Dict[str, Any]
    scores: Dict[str, int]
    
    def to_hash(self) -> str:
        """Create hash of game state for comparison"""
        state_json = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()

class GameStateValidator:
    """Validates game state transitions and consistency"""
    
    VALID_PHASES = ['setup', 'captain_selection', 'partnership_decision', 'match_play', 'hole_complete']
    VALID_TRANSITIONS = {
        'setup': ['captain_selection'],
        'captain_selection': ['partnership_decision', 'match_play'],
        'partnership_decision': ['match_play'],
        'match_play': ['hole_complete'],
        'hole_complete': ['captain_selection', 'game_complete']
    }
    
    def validate_state(self, state: Dict[str, Any]) -> List[str]:
        """Validate a game state and return any errors"""
        errors = []
        
        # Check required fields
        required_fields = ['hole_number', 'phase', 'players', 'betting']
        for field in required_fields:
            if field not in state:
                errors.append(f"Missing required field: {field}")
        
        # Validate phase
        if state.get('phase') not in self.VALID_PHASES:
            errors.append(f"Invalid phase: {state.get('phase')}")
        
        # Validate hole number
        if not 1 <= state.get('hole_number', 0) <= 18:
            errors.append(f"Invalid hole number: {state.get('hole_number')}")
        
        # Validate players
        if len(state.get('players', [])) != 4:
            errors.append("Game must have exactly 4 players")
        
        # Validate betting
        betting = state.get('betting', {})
        if betting.get('current_wager', 0) < betting.get('base_wager', 1):
            errors.append("Current wager cannot be less than base wager")
        
        # Validate teams based on phase
        if state.get('phase') == 'match_play':
            teams = state.get('teams', {})
            if teams.get('type') not in ['partners', 'solo', 'pending']:
                errors.append(f"Invalid team type: {teams.get('type')}")
        
        return errors
    
    def validate_transition(self, from_state: Dict[str, Any], to_state: Dict[str, Any]) -> List[str]:
        """Validate a state transition"""
        errors = []

        from_phase = from_state.get('phase')
        to_phase = to_state.get('phase')

        # Check valid transition
        valid_next_phases = self.VALID_TRANSITIONS.get(from_phase, []) if from_phase else []
        if to_phase not in valid_next_phases:
            errors.append(f"Invalid transition: {from_phase} -> {to_phase}")
        
        # Validate hole progression
        from_hole = from_state.get('hole_number')
        to_hole = to_state.get('hole_number')

        if to_phase == 'captain_selection' and from_phase == 'hole_complete':
            if from_hole is not None and to_hole is not None and to_hole != from_hole + 1:
                errors.append(f"Hole should increment after completion: {from_hole} -> {to_hole}")
        elif to_hole != from_hole:
            errors.append(f"Hole changed unexpectedly: {from_hole} -> {to_hole}")
        
        # Validate captain rotation
        if to_phase == 'captain_selection' and to_hole is not None:
            players = to_state.get('players', [])
            captain_id = to_state.get('captain_id')
            expected_captain_idx = (to_hole - 1) % 4
            if players[expected_captain_idx].get('id') != captain_id:
                errors.append(f"Captain rotation incorrect for hole {to_hole}")
        
        # Validate betting progression
        from_wager = from_state.get('betting', {}).get('current_wager', 1)
        to_wager = to_state.get('betting', {}).get('current_wager', 1)
        
        if to_wager < from_wager and to_phase != 'captain_selection':
            errors.append("Wager decreased unexpectedly")
        
        return errors

class TestGameStateValidation:
    """Test cases for game state validation"""
    
    @pytest.fixture
    def validator(self):
        return GameStateValidator()
    
    def test_valid_initial_state(self, validator):
        """Test validation of initial game state"""
        state = {
            'hole_number': 1,
            'phase': 'captain_selection',
            'players': [
                {'id': 'p1', 'name': 'Player 1'},
                {'id': 'p2', 'name': 'Player 2'},
                {'id': 'p3', 'name': 'Player 3'},
                {'id': 'p4', 'name': 'Player 4'}
            ],
            'captain_id': 'p1',
            'betting': {
                'base_wager': 1,
                'current_wager': 1,
                'doubled': False
            },
            'teams': {'type': 'pending'}
        }
        
        errors = validator.validate_state(state)
        assert len(errors) == 0
    
    def test_invalid_player_count(self, validator):
        """Test validation catches wrong player count"""
        state = {
            'hole_number': 1,
            'phase': 'captain_selection',
            'players': [
                {'id': 'p1', 'name': 'Player 1'},
                {'id': 'p2', 'name': 'Player 2'}
            ],
            'betting': {'base_wager': 1, 'current_wager': 1}
        }
        
        errors = validator.validate_state(state)
        assert "Game must have exactly 4 players" in errors
    
    def test_valid_phase_transition(self, validator):
        """Test valid phase transitions"""
        from_state = {
            'hole_number': 1,
            'phase': 'captain_selection',
            'players': [{'id': f'p{i}'} for i in range(4)],
            'betting': {'current_wager': 1}
        }
        
        to_state = {
            'hole_number': 1,
            'phase': 'partnership_decision',
            'players': [{'id': f'p{i}'} for i in range(4)],
            'betting': {'current_wager': 1}
        }
        
        errors = validator.validate_transition(from_state, to_state)
        assert len(errors) == 0
    
    def test_invalid_phase_transition(self, validator):
        """Test invalid phase transitions are caught"""
        from_state = {
            'hole_number': 1,
            'phase': 'captain_selection',
            'players': [{'id': f'p{i}'} for i in range(4)],
            'betting': {'current_wager': 1}
        }
        
        to_state = {
            'hole_number': 1,
            'phase': 'hole_complete',  # Can't skip to hole_complete
            'players': [{'id': f'p{i}'} for i in range(4)],
            'betting': {'current_wager': 1}
        }
        
        errors = validator.validate_transition(from_state, to_state)
        assert any("Invalid transition" in e for e in errors)
    
    def test_captain_rotation(self, validator):
        """Test captain rotation across holes"""
        players = [
            {'id': 'p1', 'name': 'Player 1'},
            {'id': 'p2', 'name': 'Player 2'},
            {'id': 'p3', 'name': 'Player 3'},
            {'id': 'p4', 'name': 'Player 4'}
        ]
        
        # Hole 1 - Player 1 is captain
        state_hole_1 = {
            'hole_number': 1,
            'phase': 'captain_selection',
            'players': players,
            'captain_id': 'p1',
            'betting': {'current_wager': 1}
        }
        errors = validator.validate_state(state_hole_1)
        assert len(errors) == 0
        
        # Hole 2 - Player 2 should be captain
        state_hole_2 = {
            'hole_number': 2,
            'phase': 'captain_selection',
            'players': players,
            'captain_id': 'p2',
            'betting': {'current_wager': 1}
        }
        
        from_state = {
            'hole_number': 1,
            'phase': 'hole_complete',
            'players': players,
            'betting': {'current_wager': 1}
        }
        
        errors = validator.validate_transition(from_state, state_hole_2)
        assert len(errors) == 0
    
    def test_betting_validation(self, validator):
        """Test betting state validation"""
        # Test doubled wager
        state = {
            'hole_number': 1,
            'phase': 'match_play',
            'players': [{'id': f'p{i}'} for i in range(4)],
            'betting': {
                'base_wager': 1,
                'current_wager': 2,
                'doubled': True
            },
            'teams': {'type': 'partners'}
        }
        
        errors = validator.validate_state(state)
        assert len(errors) == 0
        
        # Test invalid wager (current < base)
        state['betting']['current_wager'] = 0
        errors = validator.validate_state(state)
        assert any("Current wager cannot be less than base wager" in e for e in errors)

class TestGameStateSnapshots:
    """Test game state snapshot functionality"""
    
    def test_snapshot_creation(self):
        """Test creating game state snapshots"""
        snapshot = GameStateSnapshot(
            hole_number=1,
            phase='captain_selection',
            captain_id='p1',
            teams={'type': 'pending'},
            betting={'base_wager': 1, 'current_wager': 1},
            ball_positions={},
            scores={'p1': 0, 'p2': 0, 'p3': 0, 'p4': 0}
        )
        
        # Test serialization
        snapshot_dict = asdict(snapshot)
        assert snapshot_dict['hole_number'] == 1
        assert snapshot_dict['phase'] == 'captain_selection'
        
        # Test hashing
        hash1 = snapshot.to_hash()
        hash2 = snapshot.to_hash()
        assert hash1 == hash2  # Same state produces same hash
        
        # Change state
        snapshot.hole_number = 2
        hash3 = snapshot.to_hash()
        assert hash1 != hash3  # Different state produces different hash
    
    def test_snapshot_comparison(self):
        """Test comparing game state snapshots"""
        snapshot1 = GameStateSnapshot(
            hole_number=1,
            phase='captain_selection',
            captain_id='p1',
            teams={'type': 'pending'},
            betting={'base_wager': 1, 'current_wager': 1},
            ball_positions={},
            scores={'p1': 0, 'p2': 0, 'p3': 0, 'p4': 0}
        )
        
        snapshot2 = GameStateSnapshot(
            hole_number=1,
            phase='match_play',
            captain_id='p1',
            teams={'type': 'partners', 'team1': ['p1', 'p2'], 'team2': ['p3', 'p4']},
            betting={'base_wager': 1, 'current_wager': 2},
            ball_positions={'p1': {'distance': 150}},
            scores={'p1': 0, 'p2': 0, 'p3': 0, 'p4': 0}
        )
        
        # Different phases should have different hashes
        assert snapshot1.to_hash() != snapshot2.to_hash()
        
        # Track state progression
        state_history = [snapshot1, snapshot2]
        assert len(set(s.to_hash() for s in state_history)) == 2  # All unique states