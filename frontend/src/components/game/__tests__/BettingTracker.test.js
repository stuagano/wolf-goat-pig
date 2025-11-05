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
    expect(screen.queryByText(/Betting Tracker/)).not.toBeInTheDocument();
  });

  test('should expand when clicked', () => {
    render(<BettingTracker gameState={mockGameState} />);

    const collapseBar = screen.getByText(/Bet:/);
    fireEvent.click(collapseBar);

    expect(screen.getByText(/Betting Tracker/)).toBeInTheDocument();
  });

  test('should show all components when expanded', () => {
    render(<BettingTracker gameState={mockGameState} currentPlayer="Player1" />);

    const collapseBar = screen.getByText(/Bet:/);
    fireEvent.click(collapseBar);

    // Should show CurrentBetStatus
    expect(screen.getByText(/1x/)).toBeInTheDocument();

    // Should show BettingControls
    expect(screen.getByText(/Offer Double/)).toBeInTheDocument();
    expect(screen.getByText(/Offer Press/)).toBeInTheDocument();

    // Should show BettingHistory
    expect(screen.getByText(/Current Hole/)).toBeInTheDocument();
    expect(screen.getByText(/Last Hole/)).toBeInTheDocument();
    expect(screen.getByText(/Game History/)).toBeInTheDocument();
  });
});
