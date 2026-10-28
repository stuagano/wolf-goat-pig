import React from 'react';
import { describe, test, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import RoundStoryPage from '../RoundStoryPage';

const GAME_ID = '4a7f1c20-5d9e-4a1b-8c33-0f9c2d6b7e81';
function renderAlias(result) {
  fetch.mockResolvedValue({ ok: true, json: async () => result });
  return render(<MemoryRouter initialEntries={['/rounds/2026-10-25/A?location=Wing%20Point']}><Routes>
    <Route path="/rounds/:date/:group" element={<RoundStoryPage />} />
    <Route path="/game/:gameId" element={<div>scorecard for {GAME_ID}</div>} />
  </Routes></MemoryRouter>);
}
describe('old scorecard alias navigation', () => {
  test('resolved aliases navigate directly to the existing UUID page', async () => {
    renderAlias({ status: 'resolved', game_ids: [GAME_ID] });
    expect(await screen.findByText(`scorecard for ${GAME_ID}`)).toBeVisible();
    const url = new URL(fetch.mock.calls[0][0], 'http://localhost');
    expect(url.pathname).toBe('/round-reconciliation/aliases');
    expect(Object.fromEntries(url.searchParams)).toEqual({ date: '2026-10-25', group: 'A', location: 'Wing Point' });
  });
  test('missing aliases remain honest and never render sheet-only scores or guessed links', async () => {
    renderAlias({ status: 'missing', game_ids: [] });
    expect(await screen.findByText(/Round not found/)).toBeVisible();
    expect(document.querySelector('a[href^="/game/"]')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Post comment' })).toBeNull();
  });
});
