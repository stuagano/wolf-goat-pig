// frontend/src/components/simulation/visual/__tests__/PlayersCard.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ThemeProvider from '../../../../theme/Provider';
import PlayersCard from '../PlayersCard';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe('PlayersCard', () => {
  const mockPlayers = [
    { id: 'human', name: 'You', points: 12, is_human: true },
    { id: 'bot1', name: 'Alice', points: 8, is_human: false },
    { id: 'bot2', name: 'Bob', points: 10, is_human: false },
    { id: 'bot3', name: 'Carol', points: 6, is_human: false }
  ];

  test('renders all players', () => {
    renderWithTheme(<PlayersCard players={mockPlayers} />);
    expect(screen.getByText('You')).toBeInTheDocument();
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('Carol')).toBeInTheDocument();
  });

  test('displays player points', () => {
    renderWithTheme(<PlayersCard players={mockPlayers} />);
    expect(screen.getByText(/12/)).toBeInTheDocument();
    expect(screen.getByText(/8/)).toBeInTheDocument();
  });

  test('shows captain indicator', () => {
    renderWithTheme(<PlayersCard players={mockPlayers} captainId="bot1" />);
    // Check for crown emoji or captain text - Alice should have crown next to name
    const aliceElement = screen.getByText(/Alice/);
    expect(aliceElement.textContent).toMatch(/👑/);
  });

  test('highlights human player', () => {
    renderWithTheme(<PlayersCard players={mockPlayers} />);
    const humanElement = screen.getByText('You').closest('[data-is-human]');
    // Should have some styling distinction (we'll check for data attribute)
    expect(humanElement).toHaveAttribute('data-is-human', 'true');
  });
});
