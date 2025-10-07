import React from 'react';
import { render, act } from '@testing-library/react';

import { GameProvider, useGame } from '../GameProvider';

const ContextConsumer = ({ onReady }) => {
  const context = useGame();

  React.useEffect(() => {
    if (onReady) {
      onReady(context);
    }
  }, [context, onReady]);

  return null;
};

describe('GameProvider shot probabilities', () => {
  it('resolves updater functions to plain objects', () => {
    let contextValue;

    render(
      <GameProvider>
        <ContextConsumer onReady={(ctx) => { contextValue = ctx; }} />
      </GameProvider>
    );

    const initialProbabilities = { shot: { success: 0.45 } };
    const bettingProbabilities = { offer_double: 0.3 };

    act(() => {
      contextValue.setShotProbabilities(initialProbabilities);
    });

    expect(contextValue.shotProbabilities).toEqual(initialProbabilities);
    expect(typeof contextValue.shotProbabilities).toBe('object');

    act(() => {
      contextValue.setShotProbabilities((prev) => ({
        ...prev,
        betting_analysis: bettingProbabilities,
      }));
    });

    expect(contextValue.shotProbabilities).toEqual({
      ...initialProbabilities,
      betting_analysis: bettingProbabilities,
    });
    expect(typeof contextValue.shotProbabilities).toBe('object');
  });
});
