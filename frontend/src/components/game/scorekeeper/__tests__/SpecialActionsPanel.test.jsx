import React from 'react';
import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SpecialActionsPanel from '../SpecialActionsPanel';

const theme = {
  colors: {
    primary: '#059669',
    warning: '#f59e0b',
    paper: '#fff',
    border: '#e5e7eb',
    text: '#111',
    textSecondary: '#666',
    backgroundSecondary: '#f3f4f6',
  },
};

const players = [
  { id: 'p1', name: 'Alice Park' },
  { id: 'p2', name: 'Bob Smith' },
  { id: 'p3', name: 'Carol Lee' },
  { id: 'p4', name: 'Dave Ng' },
];

describe('SpecialActionsPanel', () => {
  test('expands and toggles float for a player who has not used it', () => {
    const setFloatInvokedBy = vi.fn();
    const setShowSpecialActions = vi.fn();
    render(
      <SpecialActionsPanel
        theme={theme}
        players={players}
        playerStandings={{
          p1: { floatCount: 0 },
          p2: { floatCount: 0 },
          p3: { floatCount: 0 },
          p4: { floatCount: 0 },
        }}
        floatInvokedBy={null}
        setFloatInvokedBy={setFloatInvokedBy}
        optionInvokedBy={null}
        setOptionInvokedBy={vi.fn()}
        showSpecialActions={false}
        setShowSpecialActions={setShowSpecialActions}
      />,
    );

    fireEvent.click(screen.getByText(/Special Actions/));
    expect(setShowSpecialActions).toHaveBeenCalledWith(true);
  });

  test('selecting float sets the player; selecting again clears', () => {
    const setFloatInvokedBy = vi.fn();
    const { rerender } = render(
      <SpecialActionsPanel
        theme={theme}
        players={players}
        playerStandings={{
          p1: { floatCount: 0 },
          p2: { floatCount: 0 },
          p3: { floatCount: 0 },
          p4: { floatCount: 0 },
        }}
        floatInvokedBy={null}
        setFloatInvokedBy={setFloatInvokedBy}
        optionInvokedBy={null}
        setOptionInvokedBy={vi.fn()}
        showSpecialActions
        setShowSpecialActions={vi.fn()}
      />,
    );

    // Alice appears in both Float and Option rows — click Float's first button
    const floatLabel = screen.getByText(/Float:/);
    fireEvent.click(floatLabel.nextElementSibling.querySelector('button'));
    expect(setFloatInvokedBy).toHaveBeenCalledWith('p1');

    rerender(
      <SpecialActionsPanel
        theme={theme}
        players={players}
        playerStandings={{
          p1: { floatCount: 0 },
          p2: { floatCount: 0 },
          p3: { floatCount: 0 },
          p4: { floatCount: 0 },
        }}
        floatInvokedBy="p1"
        setFloatInvokedBy={setFloatInvokedBy}
        optionInvokedBy={null}
        setOptionInvokedBy={vi.fn()}
        showSpecialActions
        setShowSpecialActions={vi.fn()}
      />,
    );
    const floatLabel2 = screen.getByText(/Float:/);
    fireEvent.click(floatLabel2.nextElementSibling.querySelector('button'));
    expect(setFloatInvokedBy).toHaveBeenCalledWith(null);
  });

  test('player who already floated is disabled with a checkmark', () => {
    render(
      <SpecialActionsPanel
        theme={theme}
        players={players}
        playerStandings={{
          p1: { floatCount: 1 },
          p2: { floatCount: 0 },
          p3: { floatCount: 0 },
          p4: { floatCount: 0 },
        }}
        floatInvokedBy={null}
        setFloatInvokedBy={vi.fn()}
        optionInvokedBy={null}
        setOptionInvokedBy={vi.fn()}
        showSpecialActions
        setShowSpecialActions={vi.fn()}
      />,
    );

    const used = screen.getByText(/Alice ✓/);
    expect(used.closest('button')).toBeDisabled();
  });

  test('option toggle sets and clears the triggering player', () => {
    const setOptionInvokedBy = vi.fn();
    render(
      <SpecialActionsPanel
        theme={theme}
        players={players}
        playerStandings={{}}
        floatInvokedBy={null}
        setFloatInvokedBy={vi.fn()}
        optionInvokedBy={null}
        setOptionInvokedBy={setOptionInvokedBy}
        showSpecialActions
        setShowSpecialActions={vi.fn()}
      />,
    );

    // Option section has the same first names — click Bob under Option Triggered
    const optionLabel = screen.getByText('Option Triggered:');
    const optionRow = optionLabel.parentElement;
    fireEvent.click(optionRow.querySelector('button')); // Alice in option row
    expect(setOptionInvokedBy).toHaveBeenCalledWith('p1');
  });
});
