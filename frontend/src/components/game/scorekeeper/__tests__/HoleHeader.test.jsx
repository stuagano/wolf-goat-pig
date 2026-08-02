import React from 'react';
import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import HoleHeader from '../HoleHeader';

const theme = {
  colors: {
    primary: '#059669',
    accent: '#10b981',
    paper: '#fff',
    border: '#e5e7eb',
    textPrimary: '#111',
    textSecondary: '#666',
  },
};

const players = [
  { id: 'p1', name: 'Alice' },
  { id: 'p2', name: 'Bob' },
  { id: 'p3', name: 'Carol' },
  { id: 'p4', name: 'Dave' },
];

const baseProps = {
  currentHole: 3,
  courseData: { holes: [{ hole_number: 3, handicap: 7, par: 4 }] },
  players,
  rotationOrder: ['p1', 'p2', 'p3', 'p4'],
  captainIndex: 0,
  currentWager: 1,
  phase: 'normal',
  strokeAllocation: {},
  isHoepfinger: false,
  theme,
  holeHistory: [],
  holePar: 4,
  editingHole: null,
  editingOrder: false,
  setEditingOrder: vi.fn(),
  jumpToHole: vi.fn(),
  movePlayerInOrder: vi.fn(),
};

describe('HoleHeader hitting order', () => {
  test('Redo Order button calls onRedoOrder', () => {
    const onRedoOrder = vi.fn();
    render(<HoleHeader {...baseProps} onRedoOrder={onRedoOrder} />);

    fireEvent.click(screen.getByRole('button', { name: /Redo Order/i }));
    expect(onRedoOrder).toHaveBeenCalledTimes(1);
  });

  test('Edit toggles editingOrder', () => {
    const setEditingOrder = vi.fn();
    render(<HoleHeader {...baseProps} setEditingOrder={setEditingOrder} />);

    fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
    expect(setEditingOrder).toHaveBeenCalledWith(true);
  });

  test('editing mode shows 1st = captain hint and nudge arrows', () => {
    render(
      <HoleHeader
        {...baseProps}
        editingOrder
        onRedoOrder={vi.fn()}
      />,
    );
    expect(screen.getByText(/1st = captain/i)).toBeInTheDocument();
  });

  test('shows current hole and wager testids', () => {
    render(<HoleHeader {...baseProps} currentWager={2} carryOver />);
    expect(screen.getByTestId('current-hole')).toHaveTextContent('Hole 3');
    expect(screen.getByTestId('current-wager')).toHaveTextContent('2q');
  });

  test('shows Carry-Over badge when carryOver is active', () => {
    render(<HoleHeader {...baseProps} currentWager={2} carryOver />);
    expect(screen.getByTestId('carry-over-badge')).toHaveTextContent(/Carry-Over/i);
    expect(screen.getByText('2q')).toBeInTheDocument();
  });

  test('hides Carry-Over badge when inactive', () => {
    render(<HoleHeader {...baseProps} carryOver={false} />);
    expect(screen.queryByTestId('carry-over-badge')).toBeNull();
  });
});
