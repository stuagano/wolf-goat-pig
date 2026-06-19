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
