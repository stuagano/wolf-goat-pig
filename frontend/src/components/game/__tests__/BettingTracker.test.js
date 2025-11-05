// frontend/src/components/game/__tests__/BettingTracker.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BettingTracker from '../BettingTracker';

describe('BettingTracker', () => {
  const mockGameState = {
    id: 'game-123',
    current_hole: 5,
    players: [
      { id: 'p1', name: 'Player1' },
      { id: 'p2', name: 'Player2' }
    ]
  };

  test('should render collapsed by default', () => {
    render(<BettingTracker gameState={mockGameState} />);

    expect(screen.getByText(/Bet:/)).toBeInTheDocument();
    expect(screen.queryByText(/Current Bet Status/)).not.toBeInTheDocument();
  });

  test('should expand when clicked', () => {
    render(<BettingTracker gameState={mockGameState} />);

    const collapseBar = screen.getByText(/Bet:/);
    fireEvent.click(collapseBar);

    expect(screen.getByText(/Current Bet Status/)).toBeInTheDocument();
  });

  test('should show pending action indicator', () => {
    render(<BettingTracker gameState={mockGameState} hasPendingAction={true} />);

    expect(screen.getByTestId('pending-indicator')).toBeInTheDocument();
  });
});
