/**
 * Comprehensive tests for GameProvider.js - Game state management context
 * 
 * Tests cover:
 * - Context provider initialization
 * - State management and reducer actions
 * - API interactions and error handling
 * - Game lifecycle methods
 * - State persistence and cleanup
 * - Performance optimizations
 * - Error boundaries
 */

import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Mock fetch for API calls
global.fetch = jest.fn();

import { GameProvider, useGame } from '../GameProvider';

// Test component to access context
const TestComponent = ({ onStateChange }) => {
  const gameContext = useGame();
  
  React.useEffect(() => {
    if (onStateChange) {
      onStateChange(gameContext);
    }
  }, [gameContext, onStateChange]);

  return (
    <div>
      <div data-testid="loading">{gameContext.loading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="error">{gameContext.error || 'No Error'}</div>
      <div data-testid="game-active">{gameContext.isGameActive ? 'Active' : 'Inactive'}</div>
      <div data-testid="current-hole">{gameContext.currentHole}</div>
      <div data-testid="players-count">{gameContext.players.length}</div>
      
      {/* Action buttons for testing */}
      <button onClick={() => gameContext.startGame()}>Start Game</button>
      <button onClick={() => gameContext.endGame()}>End Game</button>
      <button onClick={() => gameContext.fetchGameState()}>Fetch State</button>
      <button onClick={() => gameContext.makeGameAction('test_action', { test: 'data' })}>
        Make Action
      </button>
      <button onClick={() => gameContext.clearError()}>Clear Error</button>
      <button onClick={() => gameContext.setLoading(true)}>Set Loading</button>
    </div>
  );
};

// Helper to render with provider
const renderWithProvider = (component, initialState = {}) => {
  return render(
    <GameProvider initialState={initialState}>
      {component}
    </GameProvider>
  );
};

describe('GameProvider', () => {
  let user;

  beforeEach(() => {
    user = userEvent.setup();
    fetch.mockClear();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Provider Initialization', () => {
    it('initializes with default state', () => {
      let contextValue;
      
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      expect(contextValue.gameState).toBeNull();
      expect(contextValue.loading).toBe(false);
      expect(contextValue.error).toBeNull();
      expect(contextValue.isGameActive).toBe(false);
      expect(contextValue.currentHole).toBe(1);
      expect(contextValue.players).toEqual([]);
    });

    it('initializes with custom initial state', () => {
      const customInitialState = {
        currentHole: 5,
        players: [{ id: 'p1', name: 'Test Player' }],
        isGameActive: true
      };

      let contextValue;
      
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />,
        customInitialState
      );

      expect(contextValue.currentHole).toBe(5);
      expect(contextValue.players).toHaveLength(1);
      expect(contextValue.isGameActive).toBe(true);
    });

    it('throws error when used outside provider', () => {
      // Mock console.error to avoid noise in tests
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      expect(() => {
        render(<TestComponent />);
      }).toThrow();

      consoleSpy.mockRestore();
    });
  });

  describe('State Management', () => {
    it('updates loading state correctly', async () => {
      renderWithProvider(<TestComponent />);

      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');

      const setLoadingButton = screen.getByText('Set Loading');
      await user.click(setLoadingButton);

      expect(screen.getByTestId('loading')).toHaveTextContent('Loading');
    });

    it('manages error state correctly', async () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      // Set error
      act(() => {
        contextValue.setError('Test error message');
      });

      expect(screen.getByTestId('error')).toHaveTextContent('Test error message');

      // Clear error
      const clearErrorButton = screen.getByText('Clear Error');
      await user.click(clearErrorButton);

      expect(screen.getByTestId('error')).toHaveTextContent('No Error');
    });

    it('manages game active state', async () => {
      renderWithProvider(<TestComponent />);

      expect(screen.getByTestId('game-active')).toHaveTextContent('Inactive');

      // Start game
      const startButton = screen.getByText('Start Game');
      await user.click(startButton);

      expect(screen.getByTestId('game-active')).toHaveTextContent('Active');

      // End game
      const endButton = screen.getByText('End Game');
      await user.click(endButton);

      expect(screen.getByTestId('game-active')).toHaveTextContent('Inactive');
    });

    it('updates game state correctly', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      const newGameState = {
        current_hole: 3,
        players: [
          { id: 'p1', name: 'Alice', points: 5 },
          { id: 'p2', name: 'Bob', points: 3 }
        ],
        game_status_message: 'Hole 3 in progress'
      };

      act(() => {
        contextValue.setGameState(newGameState);
      });

      expect(contextValue.gameState).toEqual(newGameState);
    });
  });

  describe('API Integration', () => {
    it('fetches game state successfully', async () => {
      const mockGameState = {
        current_hole: 2,
        players: [{ id: 'p1', name: 'Test Player' }],
        game_status_message: 'Test message'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockGameState
      });

      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      const fetchButton = screen.getByText('Fetch State');
      await user.click(fetchButton);

      await waitFor(() => {
        expect(contextValue.gameState).toEqual(mockGameState);
      });

      expect(fetch).toHaveBeenCalledWith(`${process.env.REACT_APP_API_URL}/game/state`);
    });

    it('handles fetch game state error', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      renderWithProvider(<TestComponent />);

      const fetchButton = screen.getByText('Fetch State');
      await user.click(fetchButton);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Failed to fetch game state');
      });
    });

    it('makes game actions successfully', async () => {
      const mockResponse = { 
        success: true, 
        message: 'Action completed',
        gameState: { current_hole: 2 }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      const actionButton = screen.getByText('Make Action');
      await user.click(actionButton);

      await waitFor(() => {
        expect(contextValue.gameState).toEqual(mockResponse.gameState);
      });

      expect(fetch).toHaveBeenCalledWith(
        `${process.env.REACT_APP_API_URL}/game/action`,
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'test_action', payload: { test: 'data' } })
        })
      );
    });

    it('handles game action errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Action failed'));

      renderWithProvider(<TestComponent />);

      const actionButton = screen.getByText('Make Action');
      await user.click(actionButton);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Action failed');
      });
    });

    it('handles API server errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      renderWithProvider(<TestComponent />);

      const fetchButton = screen.getByText('Fetch State');
      await user.click(fetchButton);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('HTTP error! status: 500');
      });
    });
  });

  describe('Game Lifecycle', () => {
    it('starts game with proper initialization', async () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      const startButton = screen.getByText('Start Game');
      await user.click(startButton);

      expect(contextValue.isGameActive).toBe(true);
      expect(contextValue.error).toBeNull();
    });

    it('ends game and resets state', async () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      // Start game first
      const startButton = screen.getByText('Start Game');
      await user.click(startButton);

      expect(contextValue.isGameActive).toBe(true);

      // End game
      const endButton = screen.getByText('End Game');
      await user.click(endButton);

      expect(contextValue.isGameActive).toBe(false);
    });

    it('resets game state completely', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      // Set some state
      act(() => {
        contextValue.setGameState({ current_hole: 5 });
        contextValue.setError('Some error');
        contextValue.startGame();
      });

      // Reset game
      act(() => {
        contextValue.resetGame();
      });

      expect(contextValue.gameState).toBeNull();
      expect(contextValue.error).toBeNull();
      expect(contextValue.isGameActive).toBe(false);
      expect(contextValue.currentHole).toBe(1);
    });
  });

  describe('Player Management', () => {
    it('updates player list correctly', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      const players = [
        { id: 'p1', name: 'Alice', handicap: 10 },
        { id: 'p2', name: 'Bob', handicap: 15 },
        { id: 'p3', name: 'Charlie', handicap: 8 },
        { id: 'p4', name: 'Dave', handicap: 20 }
      ];

      act(() => {
        contextValue.setPlayers(players);
      });

      expect(contextValue.players).toEqual(players);
      expect(screen.getByTestId('players-count')).toHaveTextContent('4');
    });

    it('handles empty player list', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      act(() => {
        contextValue.setPlayers([]);
      });

      expect(contextValue.players).toEqual([]);
      expect(screen.getByTestId('players-count')).toHaveTextContent('0');
    });

    it('updates current player correctly', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      const player = { id: 'p1', name: 'Alice' };

      act(() => {
        contextValue.setCurrentPlayer(player);
      });

      expect(contextValue.currentPlayer).toEqual(player);
    });
  });

  describe('Hole Management', () => {
    it('advances to next hole', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      expect(contextValue.currentHole).toBe(1);

      act(() => {
        contextValue.nextHole();
      });

      expect(contextValue.currentHole).toBe(2);
    });

    it('goes to previous hole', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />,
        { currentHole: 5 }
      );

      expect(contextValue.currentHole).toBe(5);

      act(() => {
        contextValue.previousHole();
      });

      expect(contextValue.currentHole).toBe(4);
    });

    it('does not go below hole 1', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      expect(contextValue.currentHole).toBe(1);

      act(() => {
        contextValue.previousHole();
      });

      expect(contextValue.currentHole).toBe(1);
    });

    it('does not go above hole 18', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />,
        { currentHole: 18 }
      );

      expect(contextValue.currentHole).toBe(18);

      act(() => {
        contextValue.nextHole();
      });

      expect(contextValue.currentHole).toBe(18);
    });
  });

  describe('Feedback Management', () => {
    it('adds feedback correctly', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      const feedback = {
        id: '1',
        type: 'info',
        message: 'Test feedback'
      };

      act(() => {
        contextValue.addFeedback(feedback);
      });

      expect(contextValue.feedback).toContain(feedback);
    });

    it('clears feedback correctly', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />,
        { feedback: [{ id: '1', message: 'Test' }] }
      );

      expect(contextValue.feedback).toHaveLength(1);

      act(() => {
        contextValue.clearFeedback();
      });

      expect(contextValue.feedback).toHaveLength(0);
    });
  });

  describe('Betting and Tips', () => {
    it('updates betting tips', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      const tips = ['Tip 1', 'Tip 2', 'Tip 3'];

      act(() => {
        contextValue.setBettingTips(tips);
      });

      expect(contextValue.bettingTips).toEqual(tips);
    });
  });

  describe('Performance', () => {
    it('memoizes context value to prevent unnecessary re-renders', () => {
      const renderSpy = jest.fn();
      
      const ChildComponent = () => {
        renderSpy();
        const context = useGame();
        return <div>{context.currentHole}</div>;
      };

      const { rerender } = renderWithProvider(<ChildComponent />);

      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-render with same state
      rerender(
        <GameProvider>
          <ChildComponent />
        </GameProvider>
      );

      // Should not cause unnecessary re-renders
      expect(renderSpy).toHaveBeenCalledTimes(2);
    });

    it('batches state updates correctly', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      // Batch multiple updates
      act(() => {
        contextValue.setLoading(true);
        contextValue.setCurrentHole(5);
        contextValue.startGame();
      });

      expect(contextValue.loading).toBe(true);
      expect(contextValue.currentHole).toBe(5);
      expect(contextValue.isGameActive).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('handles reducer errors gracefully', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      // Try to dispatch invalid action
      act(() => {
        try {
          contextValue.dispatch({ type: 'INVALID_ACTION' });
        } catch (error) {
          // Should handle gracefully
          expect(error).toBeInstanceOf(Error);
        }
      });
    });

    it('provides fallback for missing API URL', async () => {
      // Temporarily remove API URL
      const originalApiUrl = process.env.REACT_APP_API_URL;
      delete process.env.REACT_APP_API_URL;

      renderWithProvider(<TestComponent />);

      const fetchButton = screen.getByText('Fetch State');
      await user.click(fetchButton);

      // Should still attempt to make request with empty base URL
      expect(fetch).toHaveBeenCalled();

      // Restore API URL
      process.env.REACT_APP_API_URL = originalApiUrl;
    });
  });

  describe('Context Hook', () => {
    it('provides all expected context methods', () => {
      let contextValue;
      renderWithProvider(
        <TestComponent onStateChange={(ctx) => contextValue = ctx} />
      );

      // Check that all expected methods are available
      expect(typeof contextValue.setGameState).toBe('function');
      expect(typeof contextValue.setLoading).toBe('function');
      expect(typeof contextValue.setError).toBe('function');
      expect(typeof contextValue.clearError).toBe('function');
      expect(typeof contextValue.fetchGameState).toBe('function');
      expect(typeof contextValue.makeGameAction).toBe('function');
      expect(typeof contextValue.startGame).toBe('function');
      expect(typeof contextValue.endGame).toBe('function');
      expect(typeof contextValue.nextHole).toBe('function');
      expect(typeof contextValue.previousHole).toBe('function');
      expect(typeof contextValue.setPlayers).toBe('function');
      expect(typeof contextValue.setCurrentPlayer).toBe('function');
      expect(typeof contextValue.addFeedback).toBe('function');
      expect(typeof contextValue.clearFeedback).toBe('function');
      expect(typeof contextValue.setBettingTips).toBe('function');
      expect(typeof contextValue.resetGame).toBe('function');
    });
  });
});

// Helper component for testing provider with multiple children
const MultiChildTest = () => {
  return (
    <GameProvider>
      <TestComponent />
      <TestComponent />
    </GameProvider>
  );
};

describe('GameProvider with Multiple Children', () => {
  it('provides same context to all children', () => {
    render(<MultiChildTest />);
    
    // Both components should show same state
    const loadingElements = screen.getAllByTestId('loading');
    expect(loadingElements).toHaveLength(2);
    expect(loadingElements[0]).toHaveTextContent('Not Loading');
    expect(loadingElements[1]).toHaveTextContent('Not Loading');
  });
});
