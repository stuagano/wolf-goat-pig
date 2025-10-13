import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import GamePlay from '../GamePlay';

const baseGameState = {
  status: 'active',
  current_hole: 1,
  hole_par: 4,
  base_wager: 4,
  players: [
    { id: 'human', name: 'John Doe', handicap: 18, is_human: true, points: 0 },
    { id: 'comp1', name: 'Computer 1', handicap: 15, is_human: false, points: 0 },
    { id: 'comp2', name: 'Computer 2', handicap: 12, is_human: false, points: 0 },
    { id: 'comp3', name: 'Computer 3', handicap: 8, is_human: false, points: 0 },
  ],
  game_status_message: 'Ready to tee off',
};

const defaultProps = {
  gameState: baseGameState,
  onEndSimulation: jest.fn(),
  interactionNeeded: null,
  onMakeDecision: jest.fn(),
  feedback: [],
  shotState: null,
  shotProbabilities: null,
  onNextShot: jest.fn(),
  hasNextShot: true,
};

const renderComponent = (overrides = {}) =>
  render(<GamePlay {...defaultProps} {...overrides} />);

describe('GamePlay', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders header and player cards', () => {
    renderComponent();

    expect(screen.getByText(/simulation - hole 1/i)).toBeInTheDocument();
    expect(screen.getByText(/john doe/i)).toBeInTheDocument();
    expect(screen.getByText(/computer 1/i)).toBeInTheDocument();
  });

  test('shows next shot button when available and fires handler', () => {
    renderComponent();

    const nextShotButton = screen.getByRole('button', { name: /play next shot/i });
    expect(nextShotButton).toBeEnabled();

    fireEvent.click(nextShotButton);
    expect(defaultProps.onNextShot).toHaveBeenCalled();
  });

  test('hides next shot button when no shots remain', () => {
    renderComponent({ hasNextShot: false });

    expect(screen.queryByRole('button', { name: /play next shot/i })).not.toBeInTheDocument();
  });

  test('renders captain decision panel and handles go solo choice', () => {
    renderComponent({
      interactionNeeded: {
        type: 'captain_decision',
        captain_name: 'John Doe',
      },
    });

    expect(screen.getByText(/your decision/i)).toBeInTheDocument();
    const partnerButtons = screen.getAllByRole('button', { name: /team with/i });
    expect(partnerButtons.length).toBeGreaterThan(0);

    const goSoloButton = screen.getByRole('button', { name: /go solo/i });
    fireEvent.click(goSoloButton);

    expect(defaultProps.onMakeDecision).toHaveBeenCalledWith(expect.objectContaining({ action: 'go_solo' }));
  });

  test('handles partnership acceptance interaction', () => {
    renderComponent({
      interactionNeeded: {
        type: 'partnership_response',
        captain_name: 'Computer 1',
      },
    });

    const acceptButton = screen.getByRole('button', { name: /accept partnership/i });
    fireEvent.click(acceptButton);

    expect(defaultProps.onMakeDecision).toHaveBeenCalledWith(expect.objectContaining({ accept_partnership: true }));
  });

  test('handles double offer interaction', () => {
    renderComponent({
      interactionNeeded: {
        type: 'double_offer',
        message: 'Double has been offered',
      },
    });

    const acceptButton = screen.getByRole('button', { name: /accept double/i });
    fireEvent.click(acceptButton);

    expect(defaultProps.onMakeDecision).toHaveBeenCalledWith(expect.objectContaining({ accept_double: true }));
  });

  test('displays shot analysis and probability grid when provided', () => {
    renderComponent({
      shotState: { description: 'Approach shot with 8 iron' },
      shotProbabilities: {
        excellent: 0.2,
        good: 0.4,
        average: 0.3,
        poor: 0.1,
      },
    });

    expect(screen.getByText(/shot analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/excellent/i)).toBeInTheDocument();
    expect(screen.getByText(/40\.0%/i)).toBeInTheDocument();
  });

  test('renders feedback items', () => {
    renderComponent({
      feedback: ['Game started!', 'Shot played successfully'],
    });

    expect(screen.getByText('Game started!')).toBeInTheDocument();
    expect(screen.getByText('Shot played successfully')).toBeInTheDocument();
  });

  test('calls onEndSimulation when user confirms ending the simulation', () => {
    renderComponent();

    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
    const endButton = screen.getByRole('button', { name: /end simulation/i });
    fireEvent.click(endButton);

    expect(defaultProps.onEndSimulation).toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  test('handles null game state gracefully', () => {
    renderComponent({ gameState: null });

    expect(screen.getByText(/simulation - hole 1/i)).toBeInTheDocument();
  });
});
