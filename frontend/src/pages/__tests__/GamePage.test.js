/**
 * GamePage Component Tests
 * Tests the main game interface functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import GamePage from '../GamePage';
import { ThemeProvider } from '../../theme/Provider';
import { GameProvider } from '../../context/GameProvider';
import { AuthProvider } from '../../context/AuthContext';

// Mock API calls
global.fetch = jest.fn();

// Mock the navigation hook
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

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
});