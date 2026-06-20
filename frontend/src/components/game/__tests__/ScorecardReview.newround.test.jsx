// frontend/src/components/game/__tests__/ScorecardReview.newround.test.jsx
import React from 'react';
import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import ScorecardReview from '../ScorecardReview';

const extraction = {
  players: [{ name: 'Jon', confidence: 0.9 }, { name: 'Mary', confidence: 0.9 }],
  running_totals: (() => {
    const t = [];
    for (let h = 1; h <= 18; h++) {
      t.push({ player_index: 0, hole: h, value: h, confidence: 1 });
      t.push({ player_index: 1, hole: h, value: -h, confidence: 1 });
    }
    return t;
  })(),
};

test('new-round mode maps names to roster and confirms profile-less payload', () => {
  const onConfirm = vi.fn();
  render(
    <ScorecardReview
      extraction={extraction}
      players={[]}
      mode="new-round"
      rosterNames={['Jon Smith', 'Mary Jones']}
      onConfirm={onConfirm}
      onCancel={() => {}}
    />,
  );
  // default fuzzy match selects "Jon Smith" for "Jon"
  const selects = screen.getAllByRole('combobox');
  expect(selects[0].value).toBe('Jon Smith');

  fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
  expect(onConfirm).toHaveBeenCalledTimes(1);
  const arg = onConfirm.mock.calls[0][0];
  expect(arg.players[0]).toEqual({ name: 'Jon Smith', player_profile_id: null });
  expect(arg.per_hole_quarters.find(q => q.player_index === 0 && q.hole === 1).quarters).toBe(1);
  expect(arg.played_at).toMatch(/^\d{4}-\d{2}-\d{2}$/);
});

test('pickedPlayers: scanned order reversed from picked order aligns scores by name, not index', () => {
  const onConfirm = vi.fn();
  // Scan returned players in OPPOSITE order: SS first, CK second
  // CK's scores: hole 1 = 10 (delta = 10), hole 2 = 20 (delta = 10)
  // SS's scores: hole 1 = 1 (delta = 1), hole 2 = 2 (delta = 1)
  const reversedExtraction = {
    players: [{ name: 'SS', confidence: 0.9 }, { name: 'CK', confidence: 0.9 }],
    running_totals: (() => {
      const t = [];
      // SS is at scan index 0, CK is at scan index 1
      for (let h = 1; h <= 18; h++) {
        t.push({ player_index: 0, hole: h, value: h * 1, confidence: 1 });      // SS: 1,2,...18
        t.push({ player_index: 1, hole: h, value: h * 10, confidence: 1 });     // CK: 10,20,...180
      }
      return t;
    })(),
  };

  render(
    <ScorecardReview
      extraction={reversedExtraction}
      players={[]}
      mode="new-round"
      pickedPlayers={['CK', 'SS']}
      onConfirm={onConfirm}
      onCancel={() => {}}
    />,
  );

  fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
  expect(onConfirm).toHaveBeenCalledTimes(1);
  const arg = onConfirm.mock.calls[0][0];

  // pickedPlayers[0] = 'CK' → must have CK's scores (delta=10 per hole)
  expect(arg.players[0]).toEqual({ name: 'CK', player_profile_id: null });
  const ckHole1 = arg.per_hole_quarters.find(q => q.player_index === 0 && q.hole === 1);
  expect(ckHole1.quarters).toBe(10);

  // pickedPlayers[1] = 'SS' → must have SS's scores (delta=1 per hole)
  expect(arg.players[1]).toEqual({ name: 'SS', player_profile_id: null });
  const ssHole1 = arg.per_hole_quarters.find(q => q.player_index === 1 && q.hole === 1);
  expect(ssHole1.quarters).toBe(1);
});

test('choosing "keep as typed (unlinked)" sends unlinked:true with the typed name', () => {
  const onConfirm = vi.fn();
  render(
    <ScorecardReview
      extraction={extraction}
      players={[]}
      mode="new-round"
      rosterNames={['Jon Smith', 'Mary Jones']}
      onConfirm={onConfirm}
      onCancel={() => {}}
    />,
  );
  const selects = screen.getAllByRole('combobox');
  fireEvent.change(selects[0], { target: { value: '__unlinked__' } });

  fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
  const arg = onConfirm.mock.calls[0][0];
  // keeps the SCANNED name (not a roster name) and flags it unlinked
  expect(arg.players[0]).toEqual({ name: 'Jon', player_profile_id: null, unlinked: true });
});
