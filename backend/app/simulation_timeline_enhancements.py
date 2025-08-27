"""
Timeline enhancements for Wolf-Goat-Pig simulation
Adds proper timeline tracking and poker-style betting visualization
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class EnhancedTimelineEvent:
    """Enhanced timeline event with poker-style formatting"""
    id: str
    timestamp: datetime
    type: str  # "bet", "fold", "raise", "call", "shot", "hole_complete", etc.
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    player_name: Optional[str] = None
    icon: Optional[str] = None  # Visual icon for the event
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert to display-friendly format"""
        # Calculate time ago
        now = datetime.now()
        time_diff = now - self.timestamp
        
        if time_diff.seconds < 60:
            time_ago = f"{time_diff.seconds}s ago"
        elif time_diff.seconds < 3600:
            time_ago = f"{time_diff.seconds // 60}m ago"
        else:
            time_ago = f"{time_diff.seconds // 3600}h ago"
        
        return {
            'id': self.id,
            'time_ago': time_ago,
            'timestamp': self.timestamp.isoformat(),
            'type': self.type,
            'description': self.description,
            'player': self.player_name,
            'icon': self.icon or self._get_icon_for_type(),
            'details': self.details
        }
    
    def _get_icon_for_type(self) -> str:
        """Get appropriate icon for event type"""
        icons = {
            'bet': '💰',
            'fold': '🚫',
            'raise': '📈',
            'call': '✅',
            'check': '👀',
            'all_in': '🎯',
            'shot': '⛳',
            'hole_complete': '🏁',
            'partnership': '🤝',
            'solo': '🎯',
            'double': '2️⃣',
            'captain': '👑',
            'win': '🏆',
            'loss': '❌'
        }
        return icons.get(self.type, '📍')

class SimulationTimelineManager:
    """Manages timeline events for the simulation"""
    
    def __init__(self):
        self.events: List[EnhancedTimelineEvent] = []
        self.event_counter = 0
    
    def add_event(self, event_type: str, description: str, 
                  player_name: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  icon: Optional[str] = None) -> EnhancedTimelineEvent:
        """Add a new timeline event"""
        self.event_counter += 1
        event = EnhancedTimelineEvent(
            id=f"evt_{self.event_counter}",
            timestamp=datetime.now(),
            type=event_type,
            description=description,
            player_name=player_name,
            details=details or {},
            icon=icon
        )
        self.events.append(event)
        logger.info(f"Timeline event: {description}")
        return event
    
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent events in reverse chronological order"""
        # Return most recent events first
        sorted_events = sorted(self.events, key=lambda e: e.timestamp, reverse=True)
        return [event.to_display_dict() for event in sorted_events[:limit]]
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events in reverse chronological order"""
        sorted_events = sorted(self.events, key=lambda e: e.timestamp, reverse=True)
        return [event.to_display_dict() for event in sorted_events]
    
    def clear_events(self):
        """Clear all events (for new hole/game)"""
        self.events = []
        self.event_counter = 0

def enhance_simulation_with_timeline(simulation):
    """Enhance an existing simulation with timeline tracking"""
    if not hasattr(simulation, 'timeline_manager'):
        simulation.timeline_manager = SimulationTimelineManager()
    
    # Wrap key methods to add timeline tracking
    original_request_partner = simulation.request_partner
    def tracked_request_partner(captain_id, partner_id):
        result = original_request_partner(captain_id, partner_id)
        captain = next((p for p in simulation.players if p.id == captain_id), None)
        partner = next((p for p in simulation.players if p.id == partner_id), None)
        
        if captain and partner:
            simulation.timeline_manager.add_event(
                'partnership',
                f"{captain.name} requests partnership with {partner.name}",
                player_name=captain.name,
                details={'action': 'request', 'partner': partner.name}
            )
        return result
    simulation.request_partner = tracked_request_partner
    
    # Track solo decisions
    original_go_solo = simulation.go_solo
    def tracked_go_solo(captain_id):
        result = original_go_solo(captain_id)
        captain = next((p for p in simulation.players if p.id == captain_id), None)
        
        if captain:
            simulation.timeline_manager.add_event(
                'solo',
                f"{captain.name} decides to GO SOLO! (2x stakes)",
                player_name=captain.name,
                details={'action': 'solo', 'multiplier': 2}
            )
        return result
    simulation.go_solo = tracked_go_solo
    
    # Track shots
    original_simulate_shot = simulation.simulate_shot
    def tracked_simulate_shot(player_id):
        result = original_simulate_shot(player_id)
        player = next((p for p in simulation.players if p.id == player_id), None)
        
        if player and 'shot_detail' in result:
            detail = result['shot_detail']
            simulation.timeline_manager.add_event(
                'shot',
                f"{player.name} hits {detail.get('distance', 0)} yards with {detail.get('club', 'unknown')}",
                player_name=player.name,
                details=detail
            )
        return result
    simulation.simulate_shot = tracked_simulate_shot
    
    return simulation

def format_poker_betting_state(simulation) -> Dict[str, Any]:
    """Format the current state in poker-style betting terms"""
    if not simulation.hole_progression:
        return {}
    
    hole_state = simulation.hole_progression
    betting = hole_state.betting
    
    # Calculate pot size
    pot_size = betting.current_wager * len(simulation.players)
    if betting.doubled:
        pot_size *= 2
    
    # Determine betting phase (like poker streets)
    phase = "pre-flop"  # Before tee shots
    if hole_state.tee_shots_complete > 0:
        phase = "flop"  # After tee shots
    if hole_state.current_shot_number > len(simulation.players):
        phase = "turn"  # Mid-hole
    if any(hole_state.balls_in_hole):
        phase = "river"  # Near completion
    
    return {
        'pot_size': pot_size,
        'base_bet': betting.base_wager,
        'current_bet': betting.current_wager,
        'betting_phase': phase,
        'doubled': betting.doubled,
        'players_in': len([p for p in simulation.players if p.id not in hole_state.concessions]),
        'action_on': hole_state.next_player_to_hit,
        'can_raise': not hole_state.wagering_closed,
        'can_fold': True  # Players can always concede
    }

def create_betting_options(simulation, player_id: str) -> List[Dict[str, Any]]:
    """Create poker-style betting options for a player"""
    options = []
    
    if not simulation.hole_progression:
        return options
    
    hole_state = simulation.hole_progression
    betting = hole_state.betting
    
    # Captain options
    if player_id == hole_state.hitting_order[0] and not hole_state.partnership_deadline_passed:
        options.extend([
            {
                'action': 'request_partner',
                'label': 'Request Partner',
                'description': 'Team up with another player',
                'icon': '🤝'
            },
            {
                'action': 'go_solo',
                'label': 'Go Solo (All-In)',
                'description': 'Play against all others for 2x stakes',
                'icon': '🎯',
                'multiplier': 2
            }
        ])
    
    # Betting options (like poker)
    if not hole_state.wagering_closed:
        if not betting.doubled:
            options.append({
                'action': 'offer_double',
                'label': 'Raise (Double)',
                'description': 'Double the stakes',
                'icon': '📈',
                'amount': betting.current_wager * 2
            })
        
        options.append({
            'action': 'check',
            'label': 'Check',
            'description': 'Continue without raising',
            'icon': '✅'
        })
    
    # Always can concede (fold)
    options.append({
        'action': 'concede',
        'label': 'Fold (Concede)',
        'description': 'Give up the hole',
        'icon': '🚫'
    })
    
    return options