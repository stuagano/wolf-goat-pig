import React from 'react';
import { test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ScorecardReview from '../ScorecardReview';

const extraction = {
  players: [{ name: 'Jon', confidence: 0.9 }, { name: 'Mary', confidence: 0.9 }],
  running_totals: Array.from({ length: 18 }, (_, i) => [
    { player_index: 0, hole: i + 1, value: i + 1 },
    { player_index: 1, hole: i + 1, value: -i - 1 },
  ]).flat(),
};

test('partial names require explicit roster selection, never fuzzy attribution', () => {
  const confirm = vi.fn();
  render(<ScorecardReview extraction={extraction} players={[]} mode="new-round"
    rosterNames={['Jon Smith', 'Mary Jones']} onConfirm={confirm} />);
  const selects = screen.getAllByRole('combobox');
  expect(selects[0].value).toBe('__unlinked__');
  fireEvent.change(selects[0], { target: { value: 'Jon Smith' } });
  fireEvent.change(selects[1], { target: { value: 'Mary Jones' } });
  fireEvent.click(screen.getByRole('button', { name: /hole-by-hole/i }));
  fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
  const body = confirm.mock.calls[0][0];
  expect(body.players[0]).toEqual({ name: 'Jon Smith', player_profile_id: null });
  expect(body.detail_coverage).toBe('per_hole_complete');
  expect(body.per_hole_quarters).toHaveLength(36);
  expect(body.per_hole_quarters[0].quarters).toBe(1);
});

test('reversed OCR rows retain scores with the correct named participant', () => {
  const confirm = vi.fn();
  render(<ScorecardReview extraction={extraction} players={[]} mode="new-round"
    pickedPlayers={['Mary', 'Jon']} onConfirm={confirm} />);
  fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
  const body = confirm.mock.calls[0][0];
  expect(body.players.map(p => [p.name, p.quarters])).toEqual([['Jon', 18], ['Mary', -18]]);
  expect(body.per_hole_quarters).toBeUndefined();
});

test('garbled OCR blocks save until the user explicitly maps the row', () => {
  const confirm = vi.fn();
  render(<ScorecardReview extraction={{ ...extraction, players: [{ name: 'garbled' }, { name: 'Mary' }] }}
    players={[]} mode="new-round" pickedPlayers={['Jon', 'Mary']} onConfirm={confirm} />);
  expect(screen.getByRole('button', { name: /mapping to continue/i })).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Map scanned row 1'), { target: { value: '0' } });
  fireEvent.click(screen.getByRole('button', { name: /confirm totals/i }));
  expect(confirm.mock.calls[0][0].players[0]).toMatchObject({ name: 'Jon', quarters: 18 });
});

test('explicit unlinked player keeps the scanned name and explicit total', () => {
  const confirm = vi.fn();
  render(<ScorecardReview extraction={extraction} players={[]} mode="new-round"
    rosterNames={['Jon Smith']} onConfirm={confirm} />);
  fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
  expect(confirm.mock.calls[0][0].players[0]).toEqual({ name: 'Jon', player_profile_id: null, unlinked: true, quarters: 18 });
});

test('attach maps to stable slot IDs rather than display names', () => {
  const confirm = vi.fn();
  render(<ScorecardReview extraction={extraction} players={[{ id: 'slot-mary', name: 'Mary' }, { id: 'slot-jon', name: 'Jon' }]}
    onConfirm={confirm} />);
  fireEvent.click(screen.getByRole('button', { name: /confirm quarters/i }));
  expect(confirm.mock.calls[0][0]['1']).toEqual({ 'slot-jon': 1, 'slot-mary': -1 });
});
