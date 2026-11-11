import React from 'react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import SettleUp from '../SettleUp';

vi.mock('../../../config/api.config', () => ({ apiConfig: { baseUrl: 'http://test-api' } }));

const roster = [
  { id: 3, venmo_handle: '@ann-golf' },
  { id: 4, venmo_handle: null },
];

beforeEach(() => {
  global.fetch = vi.fn(async () => ({ ok: true, json: async () => roster }));
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const players = [
  { id: 'a', name: 'Ann', profile_id: 3, quarters: 12 },
  { id: 'b', name: 'Bob', profile_id: 4, quarters: 8 },
  { id: 'c', name: 'Cy', profile_id: null, quarters: -20 },
];

describe('SettleUp', () => {
  test('lists who pays whom with a Venmo button when the winner has a handle', async () => {
    render(<SettleUp players={players} note="Wolf Goat Pig · 2026-11-08" />);

    expect(screen.getByText('Cy pays Ann $3.00')).toBeInTheDocument();
    expect(screen.getByText('Cy pays Bob $2.00')).toBeInTheDocument();
    const pay = await screen.findByRole('link', { name: 'Pay on Venmo' });
    const url = new URL(pay.getAttribute('href'));
    expect(url.searchParams.get('recipients')).toBe('ann-golf');
    expect(url.searchParams.get('amount')).toBe('3.00');
    expect(screen.getByText('(Bob has no Venmo yet)')).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith('http://test-api/players');
  });

  test('refuses to settle an unbalanced card and fetches nothing', () => {
    render(<SettleUp players={[{ ...players[0] }, { ...players[2], quarters: -5 }]} note="x" />);
    expect(screen.getByRole('status')).toHaveTextContent("Quarters don't balance — fix the card first.");
    expect(screen.queryByText(/pays/)).toBeNull();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  test('a flat round shows nothing', () => {
    const { container } = render(<SettleUp players={[{ ...players[0], quarters: 0 }]} note="x" />);
    expect(container).toBeEmptyDOMElement();
  });

  test('still lists debts when the player list fails to load', async () => {
    global.fetch = vi.fn(async () => { throw new Error('offline'); });
    render(<SettleUp players={players} note="x" />);
    expect(await screen.findByText('(Ann has no Venmo yet)')).toBeInTheDocument();
    expect(screen.getByText('Cy pays Ann $3.00')).toBeInTheDocument();
  });
});
