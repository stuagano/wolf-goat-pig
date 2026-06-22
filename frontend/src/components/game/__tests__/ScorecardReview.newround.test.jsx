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

  // covers the per-hole grid path → switch out of the default totals-first mode
  fireEvent.click(screen.getByRole('button', { name: /hole-by-hole/i }));
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

  // covers per-hole alignment → switch out of the default totals-first mode
  fireEvent.click(screen.getByRole('button', { name: /hole-by-hole/i }));
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

test('pickedPlayers: garbled OCR name uses positional fallback so scores are NOT dropped', () => {
  const onConfirm = vi.fn();
  // Scan garbled "CK" → "CKgarbled"; "SS" scanned correctly.
  // CKgarbled is at scan index 0: hole values 100, 200, ... (delta = 100 per hole)
  // SS is at scan index 1: hole values 10, 20, ...   (delta = 10 per hole)
  const garbledExtraction = {
    players: [{ name: 'CKgarbled', confidence: 0.4 }, { name: 'SS', confidence: 0.9 }],
    running_totals: (() => {
      const t = [];
      for (let h = 1; h <= 18; h++) {
        t.push({ player_index: 0, hole: h, value: h * 100, confidence: 1 }); // CKgarbled scan index 0
        t.push({ player_index: 1, hole: h, value: h * 10, confidence: 1 });  // SS scan index 1
      }
      return t;
    })(),
  };

  render(
    <ScorecardReview
      extraction={garbledExtraction}
      players={[]}
      mode="new-round"
      pickedPlayers={['CK', 'SS']}
      onConfirm={onConfirm}
      onCancel={() => {}}
    />,
  );

  // covers per-hole positional fallback → switch out of the default totals-first mode
  fireEvent.click(screen.getByRole('button', { name: /hole-by-hole/i }));
  fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
  expect(onConfirm).toHaveBeenCalledTimes(1);
  const arg = onConfirm.mock.calls[0][0];

  // 'CK' had no name match → positional fallback: scan index 0 (CKgarbled row, delta=100)
  expect(arg.players[0]).toEqual({ name: 'CK', player_profile_id: null });
  const ckHole1 = arg.per_hole_quarters.find(q => q.player_index === 0 && q.hole === 1);
  expect(ckHole1.quarters).toBe(100); // NOT zero/dropped

  // 'SS' matched by name: scan index 1 (delta=10)
  expect(arg.players[1]).toEqual({ name: 'SS', player_profile_id: null });
  const ssHole1 = arg.per_hole_quarters.find(q => q.player_index === 1 && q.hole === 1);
  expect(ssHole1.quarters).toBe(10);
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

test('totals-first: new-round defaults to totals and confirms each total as the hole-18 delta', () => {
  const onConfirm = vi.fn();
  const ext = {
    players: [{ name: 'CK' }, { name: 'SS' }],
    running_totals: [
      { player_index: 0, hole: 18, value: 6 },
      { player_index: 1, hole: 18, value: -6 },
    ],
  };
  render(
    <ScorecardReview extraction={ext} players={[]} mode="new-round"
      rosterNames={[]} pickedPlayers={['CK', 'SS']} onConfirm={onConfirm} onCancel={() => {}} />,
  );
  // defaults to totals-first; totals pre-fill from the scan, so confirm works as-is
  fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
  const arg = onConfirm.mock.calls[0][0];
  const ck18 = arg.per_hole_quarters.find(q => q.player_index === 0 && q.hole === 18);
  const ss18 = arg.per_hole_quarters.find(q => q.player_index === 1 && q.hole === 18);
  expect(ck18.quarters).toBe(6);
  expect(ss18.quarters).toBe(-6);
  // standings = sum of quarters → settle-up correct from totals alone
  const ckSum = arg.per_hole_quarters.filter(q => q.player_index === 0).reduce((a, q) => a + q.quarters, 0);
  expect(ckSum).toBe(6);
  expect(arg.players.map(p => p.name)).toEqual(['CK', 'SS']);
});
