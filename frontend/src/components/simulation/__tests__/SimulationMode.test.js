import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SimulationMode from '../SimulationMode';
import { GameProvider } from '../../../context/GameProvider';

// Mock fetch
global.fetch = jest.fn();

// Mock useGame hook
const mockGameContext = {
  gameState: null,
  setGameState: jest.fn(),
  isGameActive: false,
  startGame: jest.fn(),
  endGame: jest.fn(),
  loading: false,
  setLoading: jest.fn(),
  feedback: [],
  addFeedback: jest.fn(),
  clearFeedback: jest.fn(),
  shotState: null,
  setShotState: jest.fn(),
  interactionNeeded: null,
  setInteractionNeeded: jest.fn(),
  pendingDecision: {},
  setPendingDecision: jest.fn(),
  shotProbabilities: null,
  setShotProbabilities: jest.fn(),
  hasNextShot: true,
  setHasNextShot: jest.fn(),
};

jest.mock('../../../context', () => ({
  useGame: () => mockGameContext,
}));

// Mock simulation components
jest.mock('../GameSetup', () => {
  return function MockGameSetup({ onStartGame }) {
    return (
      <div data-testid="game-setup">
        <button onClick={onStartGame} data-testid="start-game-btn">
          Start Simulation
        </button>
      </div>
    );
  };
});

jest.mock('../GamePlay', () => {
  return function MockGamePlay({ onEndSimulation, onMakeDecision, onNextShot }) {
    return (
      <div data-testid="game-play">
        <button onClick={onEndSimulation} data-testid="end-game-btn">
          End Simulation
        </button>
        <button onClick={() => onMakeDecision({ action: 'test' })} data-testid="make-decision-btn">
          Make Decision
        </button>
        <button onClick={onNextShot} data-testid="next-shot-btn">
          Next Shot
        </button>
      </div>
    );
  };
});

describe('SimulationMode', () => {
  beforeEach(() => {
    fetch.mockClear();
    Object.values(mockGameContext).forEach(fn => {
      if (typeof fn === 'function') fn.mockClear();
    });
  });

  test('renders game setup when game is not active', () => {
    render(
      <GameProvider>
        <SimulationMode />
      </GameProvider>
    );

    expect(screen.getByTestId('game-setup')).toBeInTheDocument();
    expect(screen.queryByTestId('game-play')).not.toBeInTheDocument();
  });

  test('renders game play when game is active', () => {
    const activeGameContext = {
      ...mockGameContext,
      isGameActive: true,
      gameState: { status: 'active', players: [] },
    };

    jest.doMock('../../../context', () => ({
      useGame: () => activeGameContext,
    }));

    const SimulationModeWithActiveGame = require('../SimulationMode').default;

    render(
      <GameProvider>
        <SimulationModeWithActiveGame />
      </GameProvider>
    );

    expect(screen.queryByTestId('game-setup')).not.toBeInTheDocument();
    expect(screen.getByTestId('game-play')).toBeInTheDocument();
  });

  test('fetches initial data on mount', async () => {
    fetch
      .mockResolvedValueOnce({
        json: () => Promise.resolve({ personalities: [] }),
      })
      .mockResolvedValueOnce({
        json: () => Promise.resolve({ opponents: [] }),
      })
      .mockResolvedValueOnce({
        json: () => Promise.resolve({}),
      });

    render(
      <GameProvider>
        <SimulationMode />
      </GameProvider>
    );

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/simulation/available-personalities');
      expect(fetch).toHaveBeenCalledWith('/simulation/suggested-opponents');
      expect(fetch).toHaveBeenCalledWith('/courses');
    });
  });

  test('handles API errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    fetch.mockRejectedValue(new Error('API Error'));

    render(
      <GameProvider>
        <SimulationMode />
      </GameProvider>
    );

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error fetching initial data:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  test('validates human player name before starting simulation', async () => {
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation();

    render(
      <GameProvider>
        <SimulationMode />
      </GameProvider>
    );

    // Simulate starting game without name
    fireEvent.click(screen.getByTestId('start-game-btn'));

    expect(alertSpy).toHaveBeenCalledWith('Please enter your name');
    alertSpy.mockRestore();
  });

  test('starts simulation successfully with valid data', async () => {
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve({
        status: 'ok',
        game_state: { status: 'active' },
        message: 'Game started!',
      }),
    });

    // Mock a successful game start with named player
    const activeContext = {
      ...mockGameContext,
      gameState: { humanPlayer: { name: 'Test Player' } },
    };

    jest.doMock('../../../context', () => ({
      useGame: () => activeContext,
    }));

    const SimulationModeWithData = require('../SimulationMode').default;

    render(
      <GameProvider>
        <SimulationModeWithData />
      </GameProvider>
    );

    // This would be called internally when starting simulation
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });
  });
});

describe('SimulationMode API Integration', () => {
  test('makeDecision handles different decision types', async () => {
    const activeGameContext = {
      ...mockGameContext,
      isGameActive: true,
      gameState: { status: 'active' },
    };

    jest.doMock('../../../context', () => ({
      useGame: () => activeGameContext,
    }));

    const SimulationModeActive = require('../SimulationMode').default;

    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        game_state: { updated: true },
        feedback: ['Decision made'],
      }),
    });

    render(
      <GameProvider>
        <SimulationModeActive />
      </GameProvider>
    );

    fireEvent.click(screen.getByTestId('make-decision-btn'));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/simulation/play-hole', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'test' }),
      });
    });
  });

  test('playNextShot handles shot progression', async () => {
    const activeGameContext = {
      ...mockGameContext,
      isGameActive: true,
      gameState: { status: 'active' },
    };

    jest.doMock('../../../context', () => ({
      useGame: () => activeGameContext,
    }));

    const SimulationModeActive = require('../SimulationMode').default;

    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        status: 'ok',
        game_state: { updated: true },
        feedback: ['Shot played'],
        next_shot_available: false,
      }),
    });

    render(
      <GameProvider>
        <SimulationModeActive />
      </GameProvider>
    );

    fireEvent.click(screen.getByTestId('next-shot-btn'));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/simulation/play-next-shot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
    });
  });

  test('handles network errors gracefully', async () => {
    const activeGameContext = {
      ...mockGameContext,
      isGameActive: true,
      gameState: { status: 'active' },
    };

    jest.doMock('../../../context', () => ({
      useGame: () => activeGameContext,
    }));

    const SimulationModeActive = require('../SimulationMode').default;

    fetch.mockRejectedValue(new Error('Network error'));

    render(
      <GameProvider>
        <SimulationModeActive />
      </GameProvider>
    );

    fireEvent.click(screen.getByTestId('next-shot-btn'));

    await waitFor(() => {
      expect(mockGameContext.setLoading).toHaveBeenCalledWith(false);
    });
  });
});