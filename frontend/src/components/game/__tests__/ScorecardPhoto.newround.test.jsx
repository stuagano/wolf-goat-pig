import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ScorecardPhoto from '../ScorecardPhoto';

// Render directly into review by mocking ScorecardCapture to immediately
// hand back a file is overkill — instead drive handleConfirm via the review.
vi.mock('../ScorecardReview', () => ({
  default: ({ onConfirm }) => (
    <button onClick={() => onConfirm({
      players: [{ name: 'Jon Smith', player_profile_id: null }],
      per_hole_quarters: [{ player_index: 0, hole: 1, quarters: 1 }],
      played_at: '2026-06-18',
    })}>confirm</button>
  ),
}));
vi.mock('../ScorecardCapture', () => ({ default: () => <div /> }));
vi.mock('../GHINPostModal', () => ({ default: () => <div data-testid="ghin" /> }));

beforeEach(() => {
  global.fetch = vi.fn(async () => ({ ok: true, json: async () => ({ game_id: 'g1', status: 'completed' }) }));
});

test('new-round confirm POSTs to /games/from-scorecard and skips GHIN', async () => {
  const onSaved = vi.fn();
  render(
    <ScorecardPhoto
      mode="new-round"
      rosterNames={['Jon Smith']}
      players={[]}
      onSaved={onSaved}
      onCancel={() => {}}
      initialStage="review"
      initialExtraction={{ players: [], running_totals: [] }}
    />,
  );
  // force into review stage
  // (ScorecardPhoto starts at 'capture'; expose review via initialStage prop — see Step 3)
  screen.getByText('confirm').click();
  await waitFor(() => expect(onSaved).toHaveBeenCalled());
  const [url, opts] = global.fetch.mock.calls[0];
  expect(url).toMatch(/\/games\/from-scorecard$/);
  expect(JSON.parse(opts.body).course_name).toBe('Wing Point');
  expect(screen.queryByTestId('ghin')).toBeNull();
});
