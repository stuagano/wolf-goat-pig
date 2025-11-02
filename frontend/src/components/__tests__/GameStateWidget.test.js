/**
 * Comprehensive test suite for GameStateWidget component
 *
 * Tests the real-time game state display including:
 * - Hole information display
 * - Team formation rendering (partners/solo/pending)
 * - Betting state visualization
 * - Stroke advantages (Creecher Feature)
 * - Ball position tracking
 * - Player status display
 * - Error handling for missing/partial data
 * - Graceful degradation
 */

import React from 'react';
import { render, screen, within } from '@testing-library/react';
import '@testing-library/jest-dom';

// Component under test
import GameStateWidget from '../GameStateWidget';

// Test data fixtures
const createMockPlayers = () => [
  { id: 'p1', name: 'Bob', handicap: 10.5, points: 5 },
  { id: 'p2', name: 'Scott', handicap: 15, points: 3 },
  { id: 'p3', name: 'Vince', handicap: 8, points: -2 },
  { id: 'p4', name: 'Mike', handicap: 20.5, points: -6 }
];

const createMockHoleState = (overrides = {}) => ({
  hole_number: 5,
  hole_par: 4,
  stroke_index: 5,
  current_shot_number: 3,
  hole_complete: false,
  wagering_closed: false,
  teams: {
    type: 'partners',
    captain: 'p1',
    team1: ['p1', 'p2'],
    team2: ['p3', 'p4'],
    solo_player: null,
    opponents: [],
    pending_request: null
  },
  betting: {
    base_wager: 1,
    current_wager: 2,
    doubled: true,
    redoubled: false,
    carry_over: false,
    special_rules: {
      float_invoked: false,
      option_invoked: false,
      duncan_invoked: false,
      tunkarri_invoked: false,
      joes_special_value: null
    }
  },
  stroke_advantages: {
    p1: { handicap: 10.5, strokes_received: 1.0, stroke_index: 5 },
    p2: { handicap: 15, strokes_received: 1.0, stroke_index: 5 },
    p3: { handicap: 8, strokes_received: 0, stroke_index: 5 },
    p4: { handicap: 20.5, strokes_received: 1.0, stroke_index: 5 }
  },
  ball_positions: {
    p1: { distance_to_pin: 150, shot_count: 2, lie_type: 'fairway' },
    p2: { distance_to_pin: 200, shot_count: 2, lie_type: 'rough' },
    p3: { distance_to_pin: 120, shot_count: 2, lie_type: 'fairway' },
    p4: { distance_to_pin: 250, shot_count: 3, lie_type: 'bunker' }
  },
  next_player_to_hit: 'p4',
  line_of_scrimmage: 'p4',
  ...overrides
});

const createMockGameState = (holeStateOverrides = {}) => ({
  current_hole: 5,
  game_phase: 'regular',
  players: createMockPlayers(),
  hole_state: createMockHoleState(holeStateOverrides)
});

describe('GameStateWidget', () => {
  describe('Rendering with valid data', () => {
    it('renders without crashing with complete data', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Hole 5/i)).toBeInTheDocument();
    });

    it('displays hole information correctly', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Par 4/i)).toBeInTheDocument();
      expect(screen.getByText(/Stroke Index 5/i)).toBeInTheDocument();
    });

    it('displays current shot number', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Shot #3/i)).toBeInTheDocument();
    });

    it('shows game phase with correct icon', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      // Regular phase should show golf emoji
      expect(screen.getByText(/🏌️/)).toBeInTheDocument();
    });
  });

  describe('Team Formation Display', () => {
    it('displays partners team formation correctly', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Team Formation/i)).toBeInTheDocument();
      expect(screen.getByText(/Team 1:/i)).toBeInTheDocument();
      expect(screen.getByText(/p1, p2/i)).toBeInTheDocument();
      expect(screen.getByText(/Team 2:/i)).toBeInTheDocument();
      expect(screen.getByText(/p3, p4/i)).toBeInTheDocument();
    });

    it('displays solo team formation correctly', () => {
      const holeState = createMockHoleState({
        teams: {
          type: 'solo',
          captain: 'p1',
          team1: [],
          team2: [],
          solo_player: 'p1',
          opponents: ['p2', 'p3', 'p4'],
          pending_request: null
        }
      });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      expect(screen.getByText(/Solo:/i)).toBeInTheDocument();
      expect(screen.getByText(/p1/i)).toBeInTheDocument();
      expect(screen.getByText(/Opponents:/i)).toBeInTheDocument();
    });

    it('displays pending team formation correctly', () => {
      const holeState = createMockHoleState({
        teams: {
          type: 'pending',
          captain: 'p1',
          team1: [],
          team2: [],
          solo_player: null,
          opponents: [],
          pending_request: { requested: 'p2' }
        }
      });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      expect(screen.getByText(/Waiting for team formation/i)).toBeInTheDocument();
    });

    it('shows correct team type icon', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      // Partners should show handshake emoji
      expect(screen.getByText(/🤝/)).toBeInTheDocument();
    });
  });

  describe('Betting State Display', () => {
    it('displays betting information correctly', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Betting State/i)).toBeInTheDocument();
      expect(screen.getByText(/Current Wager: 2 quarters/i)).toBeInTheDocument();
      expect(screen.getByText(/Base Wager: 1 quarters/i)).toBeInTheDocument();
    });

    it('shows doubled indicator when bet is doubled', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/⚡ Doubled!/i)).toBeInTheDocument();
    });

    it('shows redoubled indicator when bet is redoubled', () => {
      const holeState = createMockHoleState({
        betting: {
          base_wager: 1,
          current_wager: 4,
          doubled: true,
          redoubled: true,
          carry_over: false,
          special_rules: {}
        }
      });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      expect(screen.getByText(/⚡⚡ Redoubled!/i)).toBeInTheDocument();
    });

    it('displays special rules when active', () => {
      const holeState = createMockHoleState({
        betting: {
          base_wager: 1,
          current_wager: 2,
          doubled: false,
          redoubled: false,
          carry_over: false,
          special_rules: {
            float_invoked: true,
            option_invoked: false,
            duncan_invoked: true,
            tunkarri_invoked: false
          }
        }
      });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      expect(screen.getByText(/⚡ Special Rules Active/i)).toBeInTheDocument();
      expect(screen.getByText(/🦅 Float Invoked/i)).toBeInTheDocument();
      expect(screen.getByText(/👑 Duncan Invoked/i)).toBeInTheDocument();
    });
  });

  describe('Stroke Advantages (Creecher Feature)', () => {
    it('displays stroke advantages section', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/🎯 Handicap Stroke Advantages \(Creecher Feature\)/i)).toBeInTheDocument();
    });

    it('shows players with full stroke advantage', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      // Bob should have 1 full stroke
      const bobCard = screen.getByText(/Bob/i).closest('div');
      expect(within(bobCard).getByText(/● Full Stroke/i)).toBeInTheDocument();
    });

    it('shows players with half stroke advantage', () => {
      const holeState = createMockHoleState({
        stroke_advantages: {
          p1: { handicap: 10.5, strokes_received: 0.5, stroke_index: 5 },
          p2: { handicap: 15, strokes_received: 1.0, stroke_index: 5 },
          p3: { handicap: 8, strokes_received: 0, stroke_index: 5 },
          p4: { handicap: 20.5, strokes_received: 1.5, stroke_index: 5 }
        }
      });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      // Bob should have half stroke
      const bobCard = screen.getByText(/Bob/i).closest('div');
      expect(within(bobCard).getByText(/◐ Half Stroke/i)).toBeInTheDocument();
    });

    it('shows players with no stroke advantage', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      // Vince has 0 strokes
      const vinceCard = screen.getByText(/Vince/i).closest('div');
      expect(within(vinceCard).getByText(/No Strokes/i)).toBeInTheDocument();
    });

    it('displays handicap information for each player', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Handicap: 10.5/i)).toBeInTheDocument();
      expect(screen.getByText(/Handicap: 15/i)).toBeInTheDocument();
      expect(screen.getByText(/Handicap: 8/i)).toBeInTheDocument();
      expect(screen.getByText(/Handicap: 20.5/i)).toBeInTheDocument();
    });
  });

  describe('Shot Progression Display', () => {
    it('displays shot progression information', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Shot Progression/i)).toBeInTheDocument();
      expect(screen.getByText(/Shot #3/i)).toBeInTheDocument();
      expect(screen.getByText(/Next to Hit: p4/i)).toBeInTheDocument();
      expect(screen.getByText(/Line of Scrimmage: p4/i)).toBeInTheDocument();
    });

    it('shows hole complete indicator when hole is finished', () => {
      const holeState = createMockHoleState({ hole_complete: true });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      expect(screen.getByText(/✅ Hole Complete!/i)).toBeInTheDocument();
    });
  });

  describe('Player Status Display', () => {
    it('displays all players status', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/👥 Player Status/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Bob/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Scott/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Vince/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Mike/i).length).toBeGreaterThan(0);
    });

    it('shows ball positions for players who have hit', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      // Check for distance and shot count
      expect(screen.getByText(/150 yds • Shot #2/i)).toBeInTheDocument(); // Bob
      expect(screen.getByText(/200 yds • Shot #2/i)).toBeInTheDocument(); // Scott
    });

    it('shows "Not yet hit" for players without ball position', () => {
      const holeState = createMockHoleState({
        ball_positions: {
          p1: { distance_to_pin: 150, shot_count: 2, lie_type: 'fairway' },
          p2: null,
          p3: null,
          p4: null
        }
      });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      const notYetHitElements = screen.getAllByText(/Not yet hit/i);
      expect(notYetHitElements.length).toBe(3); // Scott, Vince, Mike
    });

    it('displays player points', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Points: 5/i)).toBeInTheDocument(); // Bob
      expect(screen.getByText(/Points: 3/i)).toBeInTheDocument(); // Scott
      expect(screen.getByText(/Points: -2/i)).toBeInTheDocument(); // Vince
      expect(screen.getByText(/Points: -6/i)).toBeInTheDocument(); // Mike
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('renders nothing when gameState is null', () => {
      const { container } = render(<GameStateWidget gameState={null} holeState={null} />);
      expect(container.firstChild).toBeNull();
    });

    it('renders nothing when gameState is undefined', () => {
      const { container } = render(<GameStateWidget gameState={undefined} holeState={undefined} />);
      expect(container.firstChild).toBeNull();
    });

    it('renders nothing when holeState is null', () => {
      const gameState = createMockGameState();
      const { container } = render(<GameStateWidget gameState={gameState} holeState={null} />);
      expect(container.firstChild).toBeNull();
    });

    it('renders nothing when holeState is undefined', () => {
      const gameState = { ...createMockGameState(), hole_state: undefined };
      const { container } = render(<GameStateWidget gameState={gameState} holeState={undefined} />);
      expect(container.firstChild).toBeNull();
    });

    it('handles missing players array gracefully', () => {
      const gameState = { ...createMockGameState(), players: [] };
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      // Should still render hole info
      expect(screen.getByText(/Hole 5/i)).toBeInTheDocument();
    });

    it('handles missing stroke advantages gracefully', () => {
      const holeState = createMockHoleState({ stroke_advantages: {} });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      // Should still render but show no stroke info
      expect(screen.getByText(/Hole 5/i)).toBeInTheDocument();
    });

    it('handles missing ball positions gracefully', () => {
      const holeState = createMockHoleState({ ball_positions: {} });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      // All players should show "Not yet hit"
      const notYetHitElements = screen.getAllByText(/Not yet hit/i);
      expect(notYetHitElements.length).toBe(4);
    });

    it('handles partial betting data gracefully', () => {
      const holeState = createMockHoleState({
        betting: {
          base_wager: 1,
          current_wager: 1,
          doubled: false,
          redoubled: false
          // Missing special_rules
        }
      });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      // Should still render betting section
      expect(screen.getByText(/Betting State/i)).toBeInTheDocument();
    });

    it('handles missing team data gracefully', () => {
      const holeState = createMockHoleState({
        teams: {
          type: 'pending',
          captain: null,
          team1: [],
          team2: []
        }
      });
      const gameState = createMockGameState(holeState);

      render(<GameStateWidget gameState={gameState} holeState={holeState} />);

      // Should still render
      expect(screen.getByText(/Team Formation/i)).toBeInTheDocument();
    });
  });

  describe('Game Phase Variations', () => {
    it('displays regular phase correctly', () => {
      const gameState = createMockGameState();
      gameState.game_phase = 'regular';

      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Regular Play/i)).toBeInTheDocument();
      expect(screen.getByText(/🏌️/)).toBeInTheDocument();
    });

    it('displays Vinnie Variation phase correctly', () => {
      const gameState = createMockGameState();
      gameState.game_phase = 'vinnie_variation';

      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Vinnie Variation/i)).toBeInTheDocument();
      expect(screen.getByText(/🎯/)).toBeInTheDocument();
    });

    it('displays Hoepfinger phase correctly', () => {
      const gameState = createMockGameState();
      gameState.game_phase = 'hoepfinger';

      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      expect(screen.getByText(/Hoepfinger/i)).toBeInTheDocument();
      expect(screen.getByText(/👑/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses semantic HTML structure', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      // Check for heading
      expect(screen.getByRole('heading', { name: /Hole 5/i })).toBeInTheDocument();
    });

    it('provides meaningful text content (no icon-only information)', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} holeState={gameState.hole_state} />);

      // All important info should have text, not just icons
      expect(screen.getByText(/Team Formation/i)).toBeInTheDocument();
      expect(screen.getByText(/Betting State/i)).toBeInTheDocument();
      expect(screen.getByText(/Shot Progression/i)).toBeInTheDocument();
    });
  });

  describe('Backwards Compatibility', () => {
    it('works with gameState prop when holeState is not explicitly passed', () => {
      const gameState = createMockGameState();
      render(<GameStateWidget gameState={gameState} />);

      // Should use gameState.hole_state
      expect(screen.getByText(/Hole 5/i)).toBeInTheDocument();
    });

    it('prioritizes explicit holeState prop over gameState.hole_state', () => {
      const gameState = createMockGameState();
      const differentHoleState = createMockHoleState({ hole_number: 7, hole_par: 3 });

      render(<GameStateWidget gameState={gameState} holeState={differentHoleState} />);

      // Should use the explicit holeState prop
      expect(screen.getByText(/Hole 7/i)).toBeInTheDocument();
      expect(screen.getByText(/Par 3/i)).toBeInTheDocument();
    });
  });
});
