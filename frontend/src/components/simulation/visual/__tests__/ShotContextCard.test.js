// frontend/src/components/simulation/visual/__tests__/ShotContextCard.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ThemeProvider from '../../../../theme/Provider';
import ShotContextCard from '../ShotContextCard';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe('ShotContextCard', () => {
  const mockShotState = {
    distance_to_hole: 185,
    lie: 'fairway',
    recommended_shot: '5-iron'
  };

  const mockHoleState = {
    current_shot_number: 2,
    total_shots: 4
  };

  const mockProbabilities = {
    win_probability: 0.65
  };

  test('displays shot number and total', () => {
    renderWithTheme(
      <ShotContextCard
        shotState={mockShotState}
        holeState={mockHoleState}
        probabilities={mockProbabilities}
      />
    );
    expect(screen.getByText(/Shot 2 of 4/i)).toBeInTheDocument();
  });

  test('shows distance to hole', () => {
    renderWithTheme(
      <ShotContextCard
        shotState={mockShotState}
        holeState={mockHoleState}
        probabilities={mockProbabilities}
      />
    );
    // Distance and "yards" are in separate elements
    expect(screen.getByText('185')).toBeInTheDocument();
    expect(screen.getByText(/yards/i)).toBeInTheDocument();
  });

  test('displays lie quality', () => {
    renderWithTheme(
      <ShotContextCard
        shotState={mockShotState}
        holeState={mockHoleState}
        probabilities={mockProbabilities}
      />
    );
    expect(screen.getByText(/fairway/i)).toBeInTheDocument();
  });

  test('shows recommended shot', () => {
    renderWithTheme(
      <ShotContextCard
        shotState={mockShotState}
        holeState={mockHoleState}
        probabilities={mockProbabilities}
      />
    );
    expect(screen.getByText(/5-iron/i)).toBeInTheDocument();
  });

  test('displays win probability as percentage', () => {
    renderWithTheme(
      <ShotContextCard
        shotState={mockShotState}
        holeState={mockHoleState}
        probabilities={mockProbabilities}
      />
    );
    expect(screen.getByText(/65%/i)).toBeInTheDocument();
  });
});
