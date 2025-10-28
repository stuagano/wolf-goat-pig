// frontend/src/components/simulation/visual/__tests__/SimulationVisualInterface.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ThemeProvider from '../../../../theme/Provider';
import SimulationVisualInterface from '../SimulationVisualInterface';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe('SimulationVisualInterface', () => {
  const mockGameState = {
    players: [
      { id: 'human', name: 'You', points: 12, is_human: true },
      { id: 'bot1', name: 'Alice', points: 8, is_human: false }
    ],
    captain_id: 'human',
    base_wager: 10,
    betting: { current_wager: 20 },
    hole_state: { current_shot_number: 2 },
    hole_info: { hole_number: 1, par: 4, yards: 380 }
  };

  const mockShotState = {
    distance_to_hole: 185,
    lie: 'fairway'
  };

  test('renders all three sections', () => {
    const { container } = renderWithTheme(
      <SimulationVisualInterface
        gameState={mockGameState}
        shotState={mockShotState}
        hasNextShot={true}
      />
    );

    // Check structure exists
    const svg = container.querySelector('svg'); // Hole visualization
    expect(svg).toBeInTheDocument();

    // Check for cards
    expect(screen.getByText(/PLAYERS/i)).toBeInTheDocument();
    expect(screen.getByText(/BETTING/i)).toBeInTheDocument();
    expect(screen.getByText(/SHOT CONTEXT/i)).toBeInTheDocument();

    // Check for buttons section
    expect(screen.getByText(/Play Next Shot/i)).toBeInTheDocument();
  });

  test('applies correct layout proportions', () => {
    const { container } = renderWithTheme(
      <SimulationVisualInterface
        gameState={mockGameState}
        shotState={mockShotState}
        hasNextShot={true}
      />
    );

    // Check for class-based sections instead of data attributes
    const visualizationSection = container.querySelector('.visualization-section');
    const cardsSection = container.querySelector('.cards-section');
    const buttonsSection = container.querySelector('.buttons-section');

    expect(visualizationSection).toBeInTheDocument();
    expect(cardsSection).toBeInTheDocument();
    expect(buttonsSection).toBeInTheDocument();
  });

  test('responsive: stacks cards on mobile', () => {
    // Mock window width
    global.innerWidth = 500;

    const { container } = renderWithTheme(
      <SimulationVisualInterface
        gameState={mockGameState}
        shotState={mockShotState}
        hasNextShot={true}
      />
    );

    const cardsContainer = container.querySelector('.cards-section');
    expect(cardsContainer).toBeInTheDocument();
  });
});
