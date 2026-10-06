// frontend/src/components/game/scorekeeper/__tests__/HoleNavigation.test.jsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import HoleNavigation from '../HoleNavigation';

const baseProps = {
  currentHole: 5,
  editingHole: null,
  submitting: false,
  holeHistory: [],
  jumpToHole: vi.fn(),
  handleSubmitHole: vi.fn(),
};

describe('HoleNavigation — 18-hole round cap', () => {
  test('offers Save & next hole during the round and Save & finish round on hole 18', () => {
    const { rerender } = render(<HoleNavigation {...baseProps} />);
    expect(screen.getByTestId('complete-hole-button')).toHaveTextContent('Save & next hole');
    rerender(<HoleNavigation {...baseProps} currentHole={18} />);
    const btn = screen.getByTestId('complete-hole-button');
    expect(btn).toHaveTextContent('Save & finish round');
    expect(btn).not.toBeDisabled();
  });

  test('past hole 18 (edit-complete mode), the complete button is disabled — no hole 19', () => {
    render(<HoleNavigation {...baseProps} currentHole={19} />);
    const btn = screen.getByTestId('complete-hole-button');
    expect(btn).toHaveTextContent('Round complete');
    expect(btn).toBeDisabled();

    fireEvent.click(btn);
    expect(baseProps.handleSubmitHole).not.toHaveBeenCalled();
  });

  test('editing an existing hole still works regardless of currentHole sentinel', () => {
    render(<HoleNavigation {...baseProps} currentHole={19} editingHole={7} />);
    const btn = screen.getByTestId('complete-hole-button');
    expect(btn).toHaveTextContent('Save changes to hole 7');
    expect(btn).not.toBeDisabled();
  });
});
