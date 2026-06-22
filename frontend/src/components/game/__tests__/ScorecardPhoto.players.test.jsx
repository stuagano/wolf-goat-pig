import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ScorecardPhoto from '../ScorecardPhoto';

vi.mock('../ScorecardCapture', () => ({
  default: ({ onCapture }) => <button onClick={() => onCapture(new File(['x'], 'c.jpg', { type: 'image/jpeg' }))}>capture</button>,
}));
vi.mock('../ScorecardReview', () => ({ default: ({ onConfirm }) => <button onClick={() => onConfirm({})}>confirm</button> }));
vi.mock('../../../utils/scorecardImage', () => ({
  preprocessScorecardImage: async (f) => f,
  downscaleToBase64: async () => 'data:image/jpeg;base64,QQ==',
}));

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

test('new-round save includes image_base64 in the from-scorecard POST', async () => {
  render(
    <ScorecardPhoto mode="new-round" pickedPlayers={[]} rosterNames={[]} players={[]} onSaved={() => {}} onCancel={() => {}} />,
  );
  // Trigger capture → scan
  screen.getByText('capture').click();
  await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

  // Reset fetch so we can detect the save call separately
  global.fetch.mockClear();
  global.fetch = vi.fn(async () => ({
    ok: true,
    json: async () => ({ id: 'round-1' }),
  }));

  // Confirm the review to trigger the from-scorecard save
  screen.getByText('confirm').click();
  await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

  const [url, opts] = global.fetch.mock.calls[0];
  expect(url).toMatch(/games\/from-scorecard/);
  const sentBody = JSON.parse(opts.body);
  expect(sentBody.image_base64).toBe('data:image/jpeg;base64,QQ==');
});
