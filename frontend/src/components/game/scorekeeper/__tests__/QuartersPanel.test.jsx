import React, { useState } from 'react';
import { describe, test, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import QuartersPanel from '../QuartersPanel';

const theme = {
  colors: {
    paper: '#ffffff',
    border: '#e0e0e0',
    backgroundSecondary: '#f5f5f5',
    textPrimary: '#333',
    textSecondary: '#666',
    primary: '#2196F3',
  },
};

const players = [
  { id: 'p1', name: 'Stuart' },
  { id: 'p2', name: 'Steve' },
];

// Controlled wrapper so we can observe what QuartersPanel writes back.
function Harness({ initial = {} }) {
  const [quarters, setQuarters] = useState(initial);
  return (
    <>
      <QuartersPanel
        players={players}
        quarters={quarters}
        setQuarters={setQuarters}
        theme={theme}
      />
      <output data-testid="q-p1">{quarters.p1 ?? ''}</output>
    </>
  );
}

const signToggle = () =>
  screen.getByLabelText('Set sign for Stuart (negative or positive)');
const amountInput = () => screen.getAllByPlaceholderText('0')[0];
const value = () => screen.getByTestId('q-p1').textContent;

describe('QuartersPanel sign toggle', () => {
  test('tapping the sign FIRST arms a negative so typed digits go negative', () => {
    render(<Harness />);
    fireEvent.click(signToggle());
    expect(value()).toBe('-'); // armed
    // user now types 3 on the numeric keypad -> field becomes "-3"
    fireEvent.change(amountInput(), { target: { value: '-3' } });
    expect(value()).toBe('-3');
  });

  test('tapping the sign again disarms it', () => {
    render(<Harness />);
    fireEvent.click(signToggle());
    expect(value()).toBe('-');
    fireEvent.click(signToggle());
    expect(value()).toBe('');
  });

  test('type-then-tap also flips a positive to negative', () => {
    render(<Harness />);
    fireEvent.change(amountInput(), { target: { value: '2' } });
    expect(value()).toBe('2');
    fireEvent.click(signToggle());
    expect(value()).toBe('-2');
  });

  test('blur normalizes a dangling minus back to empty', () => {
    render(<Harness />);
    fireEvent.click(signToggle()); // arms "-"
    fireEvent.blur(amountInput());
    expect(value()).toBe('');
  });
});
