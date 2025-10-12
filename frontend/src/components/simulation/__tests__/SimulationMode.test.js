import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SimulationMode from '../SimulationMode';
import { GameProvider } from '../../../context/GameProvider';

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

const mockUseGame = jest.fn(() => mockGameContext);
const mockAutoFillPlayerName = { value: true };

jest.mock('../../../context', () => ({
  useGame: () => mockUseGame(),
}));

jest.mock('../GameSetup', () => {
  return function MockGameSetup({ onStartGame, setHumanPlayer }) {
    return (
      <div data-testid="game-setup">
        <button
          data-testid="start-game-btn"
          onClick={() => {
            if (mockAutoFillPlayerName.value && setHumanPlayer) {
              setHumanPlayer((current) => ({
                ...current,
                name: 'Mock Player',
              }));
            }
            onStartGame();
          }}
        >
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
        <button data-testid="end-game-btn" onClick={onEndSimulation}>
          End Simulation
        </button>
        <button
          data-testid="make-decision-btn"
          onClick={() => onMakeDecision({ action: 'test' })}
        >
          Make Decision
        </button>
        <button data-testid="next-shot-btn" onClick={onNextShot}>
          Next Shot
        </button>
      </div>
    );
  };
});

global.fetch = jest.fn();

const renderWithProviders = () =>
  render(
    <GameProvider>
      <SimulationMode />
    </GameProvider>
  );

describe('SimulationMode', () => {
  beforeEach(() => {
    mockAutoFillPlayerName.value = true;
    mockUseGame.mockReturnValue(mockGameContext);
    fetch.mockReset();
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
    Object.values(mockGameContext).forEach((fn) => {
      if (typeof fn === 'function') fn.mockReset();
    });
  });

  test('renders setup view when no active game', () => {
    renderWithProviders();
    expect(screen.getByTestId('game-setup')).toBeInTheDocument();
    expect(screen.queryByTestId('game-play')).not.toBeInTheDocument();
  });

  test('validates missing player name before starting', () => {
    mockAutoFillPlayerName.value = false;
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation();

    renderWithProviders();
    fireEvent.click(screen.getByTestId('start-game-btn'));

    expect(alertSpy).toHaveBeenCalledWith('Please enter your name');
    alertSpy.mockRestore();
  });
});
