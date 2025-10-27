// frontend/src/components/simulation/visual/__tests__/BettingCard.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ThemeProvider from '../../../../theme/Provider';
import BettingCard from '../BettingCard';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe('BettingCard', () => {
  const mockBetting = {
    current_wager: 20,
    doubled: true
  };

  const mockPokerState = {
    pot_size: 80,
    betting_phase: 'In Play'
  };

  test('displays current wager', () => {
    renderWithTheme(
      <BettingCard betting={mockBetting} baseWager={10} pokerState={mockPokerState} />
    );
    expect(screen.getByText(/20/)).toBeInTheDocument();
  });

  test('shows doubled indicator when doubled', () => {
    renderWithTheme(
      <BettingCard betting={mockBetting} baseWager={10} pokerState={mockPokerState} />
    );
    expect(screen.getByText(/2x/i)).toBeInTheDocument();
  });

  test('displays pot size', () => {
    renderWithTheme(
      <BettingCard betting={mockBetting} baseWager={10} pokerState={mockPokerState} />
    );
    // Pot and amount are in separate elements
    expect(screen.getByText(/Pot:/i)).toBeInTheDocument();
    expect(screen.getByText(/80/)).toBeInTheDocument();
  });

  test('shows betting phase', () => {
    renderWithTheme(
      <BettingCard betting={mockBetting} baseWager={10} pokerState={mockPokerState} />
    );
    expect(screen.getByText(/In Play/i)).toBeInTheDocument();
  });

  test('falls back to base wager when no betting data', () => {
    renderWithTheme(
      <BettingCard baseWager={5} />
    );
    // Check for Current Wager label and that 5 appears
    expect(screen.getByText(/Current Wager/i)).toBeInTheDocument();
    expect(screen.getAllByText(/5/)[0]).toBeInTheDocument();
  });
});
