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
function Harness({ initial = {}, roster = players }) {
  const [quarters, setQuarters] = useState(initial);
  return (
    <>
      <QuartersPanel
        players={roster}
        quarters={quarters}
        setQuarters={setQuarters}
        theme={theme}
      />
      <output data-testid="q-p1">{quarters.p1 ?? ''}</output>
      <output data-testid="quarters-state">{JSON.stringify(quarters)}</output>
    </>
  );
}

const lost = () => screen.getByRole('button', { name: 'Stuart lost quarters' });
const won = () => screen.getByRole('button', { name: 'Stuart won quarters' });
const amountInput = () => screen.getAllByPlaceholderText('0')[0];
const value = () => screen.getByTestId('q-p1').textContent;

describe('QuartersPanel outcome and amount', () => {
  test.each([
    [{ p1: '12', p2: '-4', p3: '-4' }, 'Lost 4', '-4'],
    [{ p1: '-12', p2: '4', p3: '4', p4: '-' }, 'Won 4', '4'],
    [{ p1: '4', p2: '-4', p3: '0' }, '0 (push)', '0'],
    [{ p1: '0.1', p2: '0.2', p3: '0' }, 'Lost 0.3', '-0.3'],
  ])('fills only after confirmation, including losses, wins, pushes and fractions', (initial, label, expected) => {
    const roster = [...players, { id: 'p3', name: 'Casey' }, { id: 'p4', name: 'Kevin' }];
    render(<Harness initial={initial} roster={roster} />);
    expect(screen.getByTestId('zero-sum-validation')).toHaveTextContent('1 player left');
    expect(JSON.parse(screen.getByTestId('quarters-state').textContent)).toEqual(initial);
    fireEvent.click(screen.getByRole('button', { name: `Fill remaining for Kevin: ${label}` }));
    expect(JSON.parse(screen.getByTestId('quarters-state').textContent)).toEqual({ ...initial, p4: expected });
    expect(screen.getByTestId('zero-sum-validation')).toHaveTextContent('Balanced');
    expect(screen.queryByRole('button', { name: /Fill remaining/ })).not.toBeInTheDocument();
  });

  test('does not suggest a fill with multiple blanks or report an incomplete zero sum as balanced', () => {
    render(<Harness />);
    expect(screen.queryByRole('button', { name: /Fill remaining/ })).not.toBeInTheDocument();
    fireEvent.change(amountInput(), { target: { value: '0' } });
    expect(screen.getByTestId('zero-sum-validation')).not.toHaveTextContent('Balanced');
    fireEvent.change(screen.getByTestId('quarters-input-p2'), { target: { value: '0' } });
    expect(screen.getByTestId('zero-sum-validation')).toHaveTextContent('Balanced');
  });

  test('Lost survives blur and clearing so unsigned digits always record a loss', () => {
    render(<Harness />);
    fireEvent.click(lost());
    fireEvent.blur(amountInput());
    expect(lost()).toHaveAttribute('aria-pressed', 'true');
    fireEvent.change(amountInput(), { target: { value: '12' } });
    expect(value()).toBe('-12');
    expect(amountInput()).toHaveValue('12');
    fireEvent.change(amountInput(), { target: { value: '' } });
    fireEvent.blur(amountInput());
    fireEvent.change(amountInput(), { target: { value: '2.5' } });
    fireEvent.blur(amountInput());
    expect(value()).toBe('-2.5');
  });

  test('editing a saved loss displays its magnitude and Won changes only its sign', () => {
    render(<Harness initial={{ p1: -12, p2: 12 }} />);
    expect(amountInput()).toHaveValue('12');
    expect(lost()).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('zero-sum-validation')).toHaveTextContent('Balanced');
    fireEvent.click(won());
    expect(value()).toBe('12');
    expect(screen.getByTestId('zero-sum-validation')).toHaveTextContent('Off by +24.0');
    fireEvent.click(lost());
    expect(value()).toBe('-12');
    expect(screen.getByTestId('zero-sum-validation')).toHaveTextContent('Balanced');
  });

  test('Push resets losses to zero and Clear starts fresh', () => {
    render(<Harness initial={{ p1: '-12', p2: '12' }} />);
    fireEvent.click(screen.getByRole('button', { name: 'Push (all 0)' }));
    expect(value()).toBe('0');
    expect(screen.getByTestId('zero-sum-validation')).toHaveTextContent('Balanced');
    fireEvent.click(screen.getByRole('button', { name: 'Clear' }));
    expect(amountInput()).toHaveValue('');
    expect(lost()).toHaveAttribute('aria-pressed', 'false');
  });

  test('rejects invalid amounts and preserves loss when editing zero', () => {
    render(<Harness />);
    fireEvent.click(lost());
    fireEvent.change(amountInput(), { target: { value: '0' } });
    fireEvent.blur(amountInput());
    expect(lost()).toHaveAttribute('aria-pressed', 'true');
    fireEvent.change(amountInput(), { target: { value: '4' } });
    expect(value()).toBe('-4');
    fireEvent.change(amountInput(), { target: { value: '4.5.6' } });
    expect(value()).toBe('-4');
  });
});
