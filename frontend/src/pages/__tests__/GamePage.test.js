/**
 * GamePage Component Tests
 * Tests the main game interface functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, __setNavigateMock, __resetRouterMocks } from 'react-router-dom';
import GamePage from '../GamePage';
import { ThemeProvider } from '../../theme/Provider';
import { GameProvider } from '../../context/GameProvider';
import { AuthProvider } from '../../context/AuthContext';

// Mock API calls
global.fetch = jest.fn();

// Mock the navigation hook
const mockNavigate = jest.fn();

// Mock Auth0
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    isAuthenticated: true,
    user: { name: 'Test User', email: 'test@example.com' },
    isLoading: false,
    getAccessTokenSilently: jest.fn(() => Promise.resolve('mock-token')),
  }),
}));

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider>
      <AuthProvider>
        <GameProvider>
          {children}
        </GameProvider>
      </AuthProvider>
    </ThemeProvider>
  </BrowserRouter>
);

describe('GamePage', () => {
  beforeEach(() => {
    fetch.mockClear();
    mockNavigate.mockClear();
    __resetRouterMocks();
    __setNavigateMock(mockNavigate);
  });

  test('renders game page layout', () => {
    render(
      <TestWrapper>
        <GamePage />
      </TestWrapper>
    );

    // Should render without crashing
    expect(screen.getByTestId('game-page')).toBeInTheDocument();
  });

  test('displays game setup when no game is active', () => {
    render(
      <TestWrapper>
        <GamePage />
      </TestWrapper>
    );

    // Look for setup elements
    expect(screen.getByText(/setup/i) || screen.getByText(/start/i)).toBeInTheDocument();
  });

  test('shows player setup form', () => {
    render(
      <TestWrapper>
        <GamePage />
      </TestWrapper>
    );

    // Look for player input fields
    const playerInputs = screen.getAllByLabelText(/player.*name/i);
    expect(playerInputs.length).toBeGreaterThanOrEqual(4); // Should have at least 4 players
  });

  test('handles game initialization', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        game_state: { current_hole: 1, players: [] }
      }),
    });

    render(
      <TestWrapper>
        <GamePage />
      </TestWrapper>
    );

    const startButton = screen.getByRole('button', { name: /start.*game/i });
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/game/setup'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  test('displays game interface when game is active', () => {
    // Mock an active game state
    const mockGameState = {
      current_hole: 1,
      players: [
        { id: 'p1', name: 'Player 1', points: 0 },
        { id: 'p2', name: 'Player 2', points: 0 },
      ],
      hole_state: { hole_complete: false }
    };

    render(
      <TestWrapper>
        <GamePage gameState={mockGameState} />
      </TestWrapper>
    );

    // Should show current hole information
    expect(screen.getByText(/hole.*1/i)).toBeInTheDocument();
  });

  test('shows hole completion screen when hole is finished', () => {
    const mockGameState = {
      current_hole: 1,
      players: [
        { id: 'p1', name: 'Player 1', points: 2 },
        { id: 'p2', name: 'Player 2', points: -2 },
      ],
      hole_state: { hole_complete: true }
    };

    render(
      <TestWrapper>
        <GamePage gameState={mockGameState} />
      </TestWrapper>
    );

    // Should show hole results
    expect(screen.getByText(/hole.*complete/i) || screen.getByText(/results/i)).toBeInTheDocument();
  });

  test('handles navigation back to home', () => {
    render(
      <TestWrapper>
        <GamePage />
      </TestWrapper>
    );

    const homeButton = screen.getByRole('button', { name: /home/i });
    fireEvent.click(homeButton);

    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  test('displays scoring information', () => {
    const mockGameState = {
      current_hole: 5,
      players: [
        { id: 'p1', name: 'Player 1', points: 4 },
        { id: 'p2', name: 'Player 2', points: -2 },
        { id: 'p3', name: 'Player 3', points: 1 },
        { id: 'p4', name: 'Player 4', points: -3 },
      ]
    };

    render(
      <TestWrapper>
        <GamePage gameState={mockGameState} />
      </TestWrapper>
    );

    // Should display all players and their scores
    mockGameState.players.forEach(player => {
      expect(screen.getByText(player.name)).toBeInTheDocument();
      expect(screen.getByText(player.points.toString())).toBeInTheDocument();
    });
  });

  test('shows betting interface when betting is available', () => {
    const mockGameState = {
      current_hole: 1,
      players: [],
      hole_state: {
        betting_available: true,
        current_wager: 2
      }
    };

    render(
      <TestWrapper>
        <GamePage gameState={mockGameState} />
      </TestWrapper>
    );

    // Should show betting options
    expect(screen.getByText(/wager/i) || screen.getByText(/bet/i)).toBeInTheDocument();
  });

  test('handles error states gracefully', () => {
    fetch.mockRejectedValueOnce(new Error('API Error'));

    render(
      <TestWrapper>
        <GamePage />
      </TestWrapper>
    );

    // Should still render without crashing
    expect(screen.getByTestId('game-page')).toBeInTheDocument();
  });

  describe('GameStateWidget Integration', () => {
    test('renders GameStateWidget when game is active with hole_state', () => {
      const mockGameState = {
        current_hole: 3,
        game_phase: 'regular',
        players: [
          { id: 'p1', name: 'Bob', handicap: 10.5, points: 5 },
          { id: 'p2', name: 'Scott', handicap: 15, points: 3 }
        ],
        hole_state: {
          hole_number: 3,
          hole_par: 4,
          stroke_index: 3,
          current_shot_number: 2,
          hole_complete: false,
          teams: {
            type: 'partners',
            captain: 'p1',
            team1: ['p1', 'p2'],
            team2: []
          },
          betting: {
            base_wager: 1,
            current_wager: 2,
            doubled: true
          },
          stroke_advantages: {
            p1: { handicap: 10.5, strokes_received: 1.0 },
            p2: { handicap: 15, strokes_received: 1.0 }
          },
          ball_positions: {}
        }
      };

      render(
        <TestWrapper>
          <GamePage gameState={mockGameState} />
        </TestWrapper>
      );

      // GameStateWidget should display hole information
      expect(screen.getByText(/Hole 3/i)).toBeInTheDocument();
      expect(screen.getByText(/Team Formation/i)).toBeInTheDocument();
      expect(screen.getByText(/Betting State/i)).toBeInTheDocument();
    });

    test('GameStateWidget shows stroke advantages (Creecher Feature)', () => {
      const mockGameState = {
        current_hole: 5,
        game_phase: 'regular',
        players: [
          { id: 'p1', name: 'Bob', handicap: 10.5, points: 0 },
          { id: 'p2', name: 'Scott', handicap: 15, points: 0 }
        ],
        hole_state: {
          hole_number: 5,
          hole_par: 4,
          stroke_index: 5,
          teams: { type: 'pending', captain: 'p1' },
          betting: { base_wager: 1, current_wager: 1 },
          stroke_advantages: {
            p1: { handicap: 10.5, strokes_received: 1.0, stroke_index: 5 },
            p2: { handicap: 15, strokes_received: 1.0, stroke_index: 5 }
          },
          ball_positions: {}
        }
      };

      render(
        <TestWrapper>
          <GamePage gameState={mockGameState} />
        </TestWrapper>
      );

      // Should show stroke advantages section
      expect(screen.getByText(/Handicap Stroke Advantages \(Creecher Feature\)/i)).toBeInTheDocument();
    });

    test('GameStateWidget updates when gameState changes', async () => {
      const initialGameState = {
        current_hole: 1,
        game_phase: 'regular',
        players: [
          { id: 'p1', name: 'Bob', handicap: 10.5, points: 0 }
        ],
        hole_state: {
          hole_number: 1,
          hole_par: 4,
          stroke_index: 1,
          current_shot_number: 1,
          teams: { type: 'pending', captain: 'p1' },
          betting: { base_wager: 1, current_wager: 1 },
          stroke_advantages: {},
          ball_positions: {}
        }
      };

      const { rerender } = render(
        <TestWrapper>
          <GamePage gameState={initialGameState} />
        </TestWrapper>
      );

      expect(screen.getByText(/Hole 1/i)).toBeInTheDocument();

      // Update to hole 2
      const updatedGameState = {
        ...initialGameState,
        current_hole: 2,
        hole_state: {
          ...initialGameState.hole_state,
          hole_number: 2
        }
      };

      rerender(
        <TestWrapper>
          <GamePage gameState={updatedGameState} />
        </TestWrapper>
      );

      expect(screen.getByText(/Hole 2/i)).toBeInTheDocument();
    });

    test('handles missing hole_state gracefully', () => {
      const mockGameState = {
        current_hole: 1,
        game_phase: 'regular',
        players: [
          { id: 'p1', name: 'Bob', handicap: 10.5, points: 0 }
        ]
        // No hole_state property
      };

      render(
        <TestWrapper>
          <GamePage gameState={mockGameState} />
        </TestWrapper>
      );

      // Page should still render without GameStateWidget
      expect(screen.getByText(/Hole 1/i)).toBeInTheDocument();
      // GameStateWidget sections should not be present
      expect(screen.queryByText(/Team Formation/i)).not.toBeInTheDocument();
    });

    test('displays team formation types correctly', () => {
      const mockGameState = {
        current_hole: 2,
        game_phase: 'regular',
        players: [
          { id: 'p1', name: 'Bob', handicap: 10.5, points: 0 },
          { id: 'p2', name: 'Scott', handicap: 15, points: 0 },
          { id: 'p3', name: 'Vince', handicap: 8, points: 0 }
        ],
        hole_state: {
          hole_number: 2,
          hole_par: 4,
          stroke_index: 2,
          teams: {
            type: 'solo',
            captain: 'p1',
            solo_player: 'p1',
            opponents: ['p2', 'p3']
          },
          betting: { base_wager: 1, current_wager: 2 },
          stroke_advantages: {},
          ball_positions: {}
        }
      };

      render(
        <TestWrapper>
          <GamePage gameState={mockGameState} />
        </TestWrapper>
      );

      // Should show solo formation
      expect(screen.getByText(/Solo:/i)).toBeInTheDocument();
      expect(screen.getByText(/p1/i)).toBeInTheDocument();
    });

    test('displays betting state including doubles', () => {
      const mockGameState = {
        current_hole: 4,
        game_phase: 'regular',
        players: [
          { id: 'p1', name: 'Bob', handicap: 10.5, points: 0 }
        ],
        hole_state: {
          hole_number: 4,
          hole_par: 4,
          stroke_index: 4,
          teams: { type: 'pending', captain: 'p1' },
          betting: {
            base_wager: 1,
            current_wager: 4,
            doubled: true,
            redoubled: true
          },
          stroke_advantages: {},
          ball_positions: {}
        }
      };

      render(
        <TestWrapper>
          <GamePage gameState={mockGameState} />
        </TestWrapper>
      );

      // Should show doubled and redoubled indicators
      expect(screen.getByText(/Current Wager: 4 quarters/i)).toBeInTheDocument();
      expect(screen.getByText(/⚡⚡ Redoubled!/i)).toBeInTheDocument();
    });

    test('shows special rules when active', () => {
      const mockGameState = {
        current_hole: 6,
        game_phase: 'regular',
        players: [
          { id: 'p1', name: 'Bob', handicap: 10.5, points: 0 }
        ],
        hole_state: {
          hole_number: 6,
          hole_par: 4,
          stroke_index: 6,
          teams: { type: 'pending', captain: 'p1' },
          betting: {
            base_wager: 1,
            current_wager: 2,
            doubled: false,
            redoubled: false,
            special_rules: {
              float_invoked: true,
              duncan_invoked: true
            }
          },
          stroke_advantages: {},
          ball_positions: {}
        }
      };

      render(
        <TestWrapper>
          <GamePage gameState={mockGameState} />
        </TestWrapper>
      );

      // Should show special rules section
      expect(screen.getByText(/⚡ Special Rules Active/i)).toBeInTheDocument();
      expect(screen.getByText(/🦅 Float Invoked/i)).toBeInTheDocument();
      expect(screen.getByText(/👑 Duncan Invoked/i)).toBeInTheDocument();
    });

    test('displays ball positions for players', () => {
      const mockGameState = {
        current_hole: 7,
        game_phase: 'regular',
        players: [
          { id: 'p1', name: 'Bob', handicap: 10.5, points: 0 },
          { id: 'p2', name: 'Scott', handicap: 15, points: 0 }
        ],
        hole_state: {
          hole_number: 7,
          hole_par: 4,
          stroke_index: 7,
          teams: { type: 'pending', captain: 'p1' },
          betting: { base_wager: 1, current_wager: 1 },
          stroke_advantages: {},
          ball_positions: {
            p1: { distance_to_pin: 150, shot_count: 2, lie_type: 'fairway' },
            p2: { distance_to_pin: 200, shot_count: 2, lie_type: 'rough' }
          }
        }
      };

      render(
        <TestWrapper>
          <GamePage gameState={mockGameState} />
        </TestWrapper>
      );

      // Should show ball position information
      expect(screen.getByText(/150 yds • Shot #2/i)).toBeInTheDocument();
      expect(screen.getByText(/200 yds • Shot #2/i)).toBeInTheDocument();
    });

    test('works across different game phases', () => {
      const hoepfingerGameState = {
        current_hole: 17,
        game_phase: 'hoepfinger',
        players: [
          { id: 'p1', name: 'Bob', handicap: 10.5, points: 0 }
        ],
        hole_state: {
          hole_number: 17,
          hole_par: 4,
          stroke_index: 17,
          teams: { type: 'pending', captain: 'p1' },
          betting: { base_wager: 1, current_wager: 1 },
          stroke_advantages: {},
          ball_positions: {}
        }
      };

      render(
        <TestWrapper>
          <GamePage gameState={hoepfingerGameState} />
        </TestWrapper>
      );

      // Should show Hoepfinger phase
      expect(screen.getByText(/Hoepfinger/i)).toBeInTheDocument();
      expect(screen.getByText(/👑/)).toBeInTheDocument();
    });
  });
});
