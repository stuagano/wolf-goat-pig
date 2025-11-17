// frontend/src/components/game/__tests__/CurrentBetStatus.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import CurrentBetStatus from '../CurrentBetStatus';

describe.skip('CurrentBetStatus', () => {
  const mockState = {
    currentMultiplier: 4,
    baseAmount: 1.00,
    currentBet: 4.00,
    teams: [
      { players: ['Player1', 'Player2'], betAmount: 4.00, score: 0 },
      { players: ['Player3', 'Player4'], betAmount: 4.00, score: 0 }
    ]
  };

  test('should display current multiplier', () => {
    render(<CurrentBetStatus state={mockState} />);
    expect(screen.getByText(/4x/)).toBeInTheDocument();
  });

  test('should display base amount', () => {
    render(<CurrentBetStatus state={mockState} />);
    expect(screen.getByText(/\$1\.00/)).toBeInTheDocument();
  });

  test('should display total bet', () => {
    render(<CurrentBetStatus state={mockState} />);
    expect(screen.getByText(/Total: \$4\.00/)).toBeInTheDocument();
  });

  test('should display team compositions', () => {
    render(<CurrentBetStatus state={mockState} />);
    expect(screen.getByText(/Player1/)).toBeInTheDocument();
    expect(screen.getByText(/Player2/)).toBeInTheDocument();
    expect(screen.getByText(/Player3/)).toBeInTheDocument();
    expect(screen.getByText(/Player4/)).toBeInTheDocument();
  });
});
