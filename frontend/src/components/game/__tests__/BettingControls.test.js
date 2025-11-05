import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BettingControls from '../BettingControls';

describe('BettingControls', () => {
  const mockActions = {
    offerDouble: jest.fn(),
    acceptDouble: jest.fn(),
    declineDouble: jest.fn(),
    offerPress: jest.fn()
  };

  const mockState = {
    pendingAction: null
  };

  test('should show offer double button when no pending action', () => {
    render(<BettingControls state={mockState} actions={mockActions} currentPlayer="Player1" />);
    expect(screen.getByText(/Offer Double/)).toBeInTheDocument();
  });

  test('should call offerDouble when button clicked', () => {
    render(<BettingControls state={mockState} actions={mockActions} currentPlayer="Player1" />);

    fireEvent.click(screen.getByText(/Offer Double/));
    expect(mockActions.offerDouble).toHaveBeenCalledWith('Player1', 2);
  });

  test('should show accept/decline buttons when double offered', () => {
    const pendingState = {
      pendingAction: {
        type: 'DOUBLE_OFFERED',
        by: 'Player1',
        proposedMultiplier: 2
      }
    };

    render(<BettingControls state={pendingState} actions={mockActions} currentPlayer="Player2" />);

    expect(screen.getByText(/Accept Double/)).toBeInTheDocument();
    expect(screen.getByText(/Decline/)).toBeInTheDocument();
  });

  test('should call acceptDouble when accept clicked', () => {
    const pendingState = {
      pendingAction: {
        type: 'DOUBLE_OFFERED',
        by: 'Player1',
        proposedMultiplier: 2
      }
    };

    render(<BettingControls state={pendingState} actions={mockActions} currentPlayer="Player2" />);

    fireEvent.click(screen.getByText(/Accept Double/));
    expect(mockActions.acceptDouble).toHaveBeenCalledWith('Player2');
  });
});
