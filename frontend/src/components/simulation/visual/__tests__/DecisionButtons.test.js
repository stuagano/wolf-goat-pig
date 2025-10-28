// frontend/src/components/simulation/visual/__tests__/DecisionButtons.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ThemeProvider from '../../../../theme/Provider';
import DecisionButtons from '../DecisionButtons';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe('DecisionButtons', () => {
  test('shows continue button when hasNextShot and no interaction', () => {
    const onNextShot = jest.fn();
    renderWithTheme(
      <DecisionButtons
        hasNextShot={true}
        interactionNeeded={null}
        onNextShot={onNextShot}
      />
    );
    const button = screen.getByText(/Play Next Shot/i);
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onNextShot).toHaveBeenCalled();
  });

  test('shows partnership buttons when captain chooses partner', () => {
    const onDecision = jest.fn();
    const interaction = {
      type: 'captain_chooses_partner',
      available_partners: ['bot1', 'bot2']
    };
    const gameState = {
      players: [
        { id: 'bot1', name: 'Alice' },
        { id: 'bot2', name: 'Bob' }
      ]
    };

    renderWithTheme(
      <DecisionButtons
        interactionNeeded={interaction}
        onDecision={onDecision}
        gameState={gameState}
      />
    );

    expect(screen.getByText(/Alice/i)).toBeInTheDocument();
    expect(screen.getByText(/Bob/i)).toBeInTheDocument();
    expect(screen.getByText(/Go Solo/i)).toBeInTheDocument();
  });

  test('shows betting buttons when double offered', () => {
    const onDecision = jest.fn();
    const interaction = {
      type: 'double_offer'
    };

    renderWithTheme(
      <DecisionButtons
        interactionNeeded={interaction}
        onDecision={onDecision}
      />
    );

    expect(screen.getByText(/Accept.*Double/i)).toBeInTheDocument();
    expect(screen.getByText(/Decline.*Double/i)).toBeInTheDocument();
  });

  test('disables buttons when loading', () => {
    renderWithTheme(
      <DecisionButtons
        hasNextShot={true}
        loading={true}
      />
    );

    const button = screen.getByText(/Play Next Shot/i).closest('button');
    expect(button).toBeDisabled();
  });

  test('shows no buttons when no action available', () => {
    const { container } = renderWithTheme(
      <DecisionButtons
        hasNextShot={false}
        interactionNeeded={null}
      />
    );

    expect(screen.getByText(/Waiting/i)).toBeInTheDocument();
  });
});
