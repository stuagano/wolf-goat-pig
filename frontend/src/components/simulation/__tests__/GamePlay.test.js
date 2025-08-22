import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import GamePlay from '../GamePlay';

// Mock game state data
const mockGameState = {
  status: 'active',
  current_hole: 1,
  players: [
    { id: 'human', name: 'John Doe', handicap: 18, is_human: true },
    { id: 'comp1', name: 'Computer 1', handicap: 15, is_human: false },
    { id: 'comp2', name: 'Computer 2', handicap: 12, is_human: false },
    { id: 'comp3', name: 'Computer 3', handicap: 8, is_human: false },
  ],
  teams: null,
  scores: {},
  game_phase: 'tee_shots',
};

const mockShotProbabilities = {
  excellent: 0.2,
  good: 0.4,
  average: 0.3,
  poor: 0.1,
  betting_analysis: {
    should_double: false,
    confidence: 0.7,
  },
};

const mockInteractionNeeded = {
  type: 'captain_decision',
  message: 'Choose your action as captain',
  options: ['request_partner', 'go_solo'],
  data: {
    available_partners: ['comp1', 'comp2', 'comp3'],
  },
};

const defaultProps = {
  gameState: mockGameState,
  onEndSimulation: jest.fn(),
  interactionNeeded: null,
  onMakeDecision: jest.fn(),
  feedback: [],
  shotState: null,
  shotProbabilities: null,
  onNextShot: jest.fn(),
  hasNextShot: true,
};

describe('GamePlay', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders game state information', () => {
    render(<GamePlay {...defaultProps} />);
    
    expect(screen.getByText(/hole 1/i)).toBeInTheDocument();
    expect(screen.getByText(/john doe/i)).toBeInTheDocument();
    expect(screen.getByText(/computer 1/i)).toBeInTheDocument();
  });

  test('shows next shot button when available', () => {
    render(<GamePlay {...defaultProps} />);
    
    const nextShotButton = screen.getByText(/next shot/i);
    expect(nextShotButton).toBeInTheDocument();
    expect(nextShotButton).not.toBeDisabled();
  });

  test('disables next shot button when no shots available', () => {
    const propsWithNoShots = {
      ...defaultProps,
      hasNextShot: false,
    };
    
    render(<GamePlay {...propsWithNoShots} />);
    
    const nextShotButton = screen.getByText(/next shot/i);
    expect(nextShotButton).toBeDisabled();
  });

  test('calls onNextShot when next shot button clicked', () => {
    render(<GamePlay {...defaultProps} />);
    
    const nextShotButton = screen.getByText(/next shot/i);
    fireEvent.click(nextShotButton);
    
    expect(defaultProps.onNextShot).toHaveBeenCalled();
  });

  test('shows interaction panel when interaction needed', () => {
    const propsWithInteraction = {
      ...defaultProps,
      interactionNeeded: mockInteractionNeeded,
    };
    
    render(<GamePlay {...propsWithInteraction} />);
    
    expect(screen.getByText(/choose your action as captain/i)).toBeInTheDocument();
    expect(screen.getByText(/request partner/i)).toBeInTheDocument();
    expect(screen.getByText(/go solo/i)).toBeInTheDocument();
  });

  test('makes decision when interaction option clicked', () => {
    const propsWithInteraction = {
      ...defaultProps,
      interactionNeeded: mockInteractionNeeded,
    };
    
    render(<GamePlay {...propsWithInteraction} />);
    
    const goSoloButton = screen.getByText(/go solo/i);
    fireEvent.click(goSoloButton);
    
    expect(defaultProps.onMakeDecision).toHaveBeenCalledWith({ action: 'go_solo' });
  });

  test('shows shot probabilities when available', () => {
    const propsWithProbabilities = {
      ...defaultProps,
      shotProbabilities: mockShotProbabilities,
    };
    
    render(<GamePlay {...propsWithProbabilities} />);
    
    expect(screen.getByText(/shot probabilities/i)).toBeInTheDocument();
    expect(screen.getByText(/excellent.*20%/i)).toBeInTheDocument();
    expect(screen.getByText(/good.*40%/i)).toBeInTheDocument();
  });

  test('shows betting analysis when available', () => {
    const propsWithProbabilities = {
      ...defaultProps,
      shotProbabilities: mockShotProbabilities,
    };
    
    render(<GamePlay {...propsWithProbabilities} />);
    
    expect(screen.getByText(/betting analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/confidence.*70%/i)).toBeInTheDocument();
  });

  test('displays feedback messages', () => {
    const propsWithFeedback = {
      ...defaultProps,
      feedback: ['Game started!', 'Shot played successfully', 'Partnership formed'],
    };
    
    render(<GamePlay {...propsWithFeedback} />);
    
    expect(screen.getByText('Game started!')).toBeInTheDocument();
    expect(screen.getByText('Shot played successfully')).toBeInTheDocument();
    expect(screen.getByText('Partnership formed')).toBeInTheDocument();
  });

  test('shows end simulation button', () => {
    render(<GamePlay {...defaultProps} />);
    
    const endButton = screen.getByText(/end simulation/i);
    expect(endButton).toBeInTheDocument();
  });

  test('calls onEndSimulation when end button clicked', () => {
    render(<GamePlay {...defaultProps} />);
    
    const endButton = screen.getByText(/end simulation/i);
    fireEvent.click(endButton);
    
    expect(defaultProps.onEndSimulation).toHaveBeenCalled();
  });

  test('handles partnership decision interaction', () => {
    const partnershipInteraction = {
      type: 'partnership_response',
      message: 'Accept partnership with Computer 1?',
      options: ['accept', 'decline'],
      data: {
        partner_id: 'comp1',
      },
    };
    
    const propsWithPartnership = {
      ...defaultProps,
      interactionNeeded: partnershipInteraction,
    };
    
    render(<GamePlay {...propsWithPartnership} />);
    
    expect(screen.getByText(/accept partnership/i)).toBeInTheDocument();
    
    const acceptButton = screen.getByText(/accept/i);
    fireEvent.click(acceptButton);
    
    expect(defaultProps.onMakeDecision).toHaveBeenCalledWith({ accept_partnership: true });
  });

  test('handles doubling decision interaction', () => {
    const doublingInteraction = {
      type: 'double_decision',
      message: 'Offer to double the bet?',
      options: ['offer_double', 'decline'],
      data: {
        current_bet: 10,
      },
    };
    
    const propsWithDoubling = {
      ...defaultProps,
      interactionNeeded: doublingInteraction,
    };
    
    render(<GamePlay {...propsWithDoubling} />);
    
    expect(screen.getByText(/offer to double/i)).toBeInTheDocument();
    
    const offerButton = screen.getByText(/offer double/i);
    fireEvent.click(offerButton);
    
    expect(defaultProps.onMakeDecision).toHaveBeenCalledWith({ offer_double: true });
  });

  test('shows player scores when available', () => {
    const gameStateWithScores = {
      ...mockGameState,
      scores: {
        human: { total: 72, net: 68 },
        comp1: { total: 75, net: 70 },
      },
    };
    
    const propsWithScores = {
      ...defaultProps,
      gameState: gameStateWithScores,
    };
    
    render(<GamePlay {...propsWithScores} />);
    
    expect(screen.getByText(/72/)).toBeInTheDocument();
    expect(screen.getByText(/68/)).toBeInTheDocument();
  });

  test('handles empty feedback gracefully', () => {
    render(<GamePlay {...defaultProps} />);
    
    // Should not crash and should render other elements
    expect(screen.getByText(/hole 1/i)).toBeInTheDocument();
  });

  test('handles null game state gracefully', () => {
    const propsWithNullState = {
      ...defaultProps,
      gameState: null,
    };
    
    render(<GamePlay {...propsWithNullState} />);
    
    // Should show loading or error state
    expect(screen.getByText(/loading/i) || screen.getByText(/error/i)).toBeInTheDocument();
  });
});