import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ScorecardPhoto from '../ScorecardPhoto';

vi.mock('../ScorecardCapture', () => ({
  default: ({ onCapture }) => <button onClick={() => onCapture(new File(['x'], 'c.jpg', { type: 'image/jpeg' }))}>capture</button>,
}));
vi.mock('../ScorecardReview', () => ({ default: () => <div data-testid="review" /> }));
vi.mock('../../../utils/scorecardImage', () => ({ preprocessScorecardImage: async (f) => f }));

beforeEach(() => {
  global.fetch = vi.fn(async () => ({
    ok: true,
    json: async () => ({ players: [], running_totals: [], per_hole_quarters: [], method: 'single' }),
  }));
});

test('new-round scan posts the picked players as a form field', async () => {
  render(
    <ScorecardPhoto mode="new-round" pickedPlayers={['CK', 'SS', 'SG']} rosterNames={[]} players={[]} onSaved={() => {}} onCancel={() => {}} />,
  );
  screen.getByText('capture').click();
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  const body = global.fetch.mock.calls[0][1].body; // FormData
  expect(body.get('players')).toBe('["CK","SS","SG"]');
});
