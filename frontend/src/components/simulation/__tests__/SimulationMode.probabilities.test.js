import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react';
import '@testing-library/jest-dom';

const mockGameContext = {
  gameState: null,
  setGameState: jest.fn(),
  isGameActive: true,
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

jest.mock('../GamePlay', () => ({ onMakeDecision }) => (
  <div data-testid="game-play">
    <button onClick={() => onMakeDecision({ action: 'test' })} data-testid="make-decision-btn">
      Make Decision
    </button>
  </div>
));

jest.mock('../EnhancedSimulationLayout', () => ({ onDecision }) => (
  <div data-testid="enhanced-layout">
    <button onClick={() => onDecision({ action: 'test' })} data-testid="make-decision-btn">
      Make Decision
    </button>
  </div>
));

jest.mock('../visual', () => ({
  SimulationVisualInterface: ({ onMakeDecision }) => (
    <div data-testid="visual-interface">
      <button onClick={() => onMakeDecision({ action: 'test' })} data-testid="make-decision-btn">
        Make Decision
      </button>
    </div>
  )
}));

// Import after mocks are defined
import SimulationMode from '../SimulationMode';

global.fetch = jest.fn();

const flushSimulationModeEffects = async () => {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
};

describe('SimulationMode probabilities merging', () => {
  beforeEach(() => {
    fetch.mockReset();
    Object.values(mockGameContext).forEach((value) => {
      if (typeof value === 'function') {
        value.mockClear();
      }
    });
    mockGameContext.isGameActive = true;
    mockGameContext.gameState = { status: 'active' };
    mockGameContext.interactionNeeded = null;
    mockGameContext.pendingDecision = {};
    mockGameContext.shotProbabilities = null;
    mockGameContext.hasNextShot = true;
  });

  it('combines shot and betting probabilities into a single payload', async () => {
    const decisionResponse = {
      status: 'ok',
      game_state: { status: 'active', updated: true },
      probabilities: { shot: { success: 0.65 } },
      betting_probabilities: { offer_double: 0.4 },
      next_shot_available: false,
    };

    fetch.mockImplementation((url) => {
      if (url.includes('/simulation/available-personalities')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ personalities: [] }) });
      }
      if (url.includes('/simulation/suggested-opponents')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ opponents: [] }) });
      }
      if (url.endsWith('/courses')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      if (url.includes('/simulation/play-hole')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(decisionResponse) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    render(<SimulationMode />);
    await flushSimulationModeEffects();

    fireEvent.click(await screen.findByTestId('make-decision-btn'));

    await waitFor(() => {
      expect(mockGameContext.setShotProbabilities).toHaveBeenCalledWith({
        shot: { success: 0.65 },
        betting_analysis: { offer_double: 0.4 },
      });
    });
    expect(mockGameContext.setShotProbabilities).toHaveBeenCalledTimes(1);
  });
});
