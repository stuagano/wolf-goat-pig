import React from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import SimpleScorekeeperPage from '../SimpleScorekeeperPage';
vi.mock('../../hooks/useRoundCard', () => ({ default: () => ({ card: { can_edit: true } }) }));
vi.mock('../../components/game', () => ({ SimpleScorekeeper: () => null }));
vi.mock('../../components/game/ScorecardPhotoButton', () => ({ default: () => null }));
vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => fetch }));
afterEach(() => { cleanup(); localStorage.clear(); vi.restoreAllMocks(); });
const roster = [{ id: 'removed', name: 'Removed' }, { id: 'a', name: 'Avery' }, { id: 'b', name: 'Blair' }];
const summaryPlayers = [roster[2], roster[0], roster[1]].map(p => ({ participant_id: p.id, name: p.name, quarters: p.id === 'b' ? 36 : -36, is_retracted: p.id === 'removed' }));
function renderPage() {
  return render(<MemoryRouter initialEntries={['/game/round']}><Routes><Route path="/game/:gameId" element={<SimpleScorekeeperPage />} /></Routes></MemoryRouter>);
}
function network({ stale = false, missing = false } = {}) {
  let revision = 9;
  let stateRoster = missing ? [roster[0], roster[1]] : roster;
  const interpreted = [];
  const fetcher = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, options) => {
    const path = String(url);
    if (options?.method === 'PATCH') {
      const body = JSON.parse(options.body);
      // Same interpretation as the actual PATCH/build_hole_history contract:
      // player_index addresses the FULL state.players array, not summary order.
      interpreted.push({ revision: body.expected_revision, cells: body.per_hole_quarters.map(q => ({ id: stateRoster[q.player_index]?.id, hole: q.hole, quarters: q.quarters })) });
      if (stale && interpreted.length === 1) { revision = 10; stateRoster = [roster[2], roster[0], roster[1]]; return new Response('{}', { status: 409 }); }
      return new Response(JSON.stringify({ revision: revision + 1 }), { status: 200 });
    }
    const data = path.endsWith('/state') ? { game_status: 'completed', players: stateRoster, revision, standings: { a: -36, b: 36 } }
      : path.endsWith('/round-summary') ? { players: summaryPlayers, revision, hole_history: [], detail_coverage: 'totals_only' }
      : path.endsWith('/discussion') ? { comments: [], reactions: [] } : null;
    return new Response(JSON.stringify(data), { status: data ? 200 : 404 });
  });
  return { fetcher, interpreted };
}
async function edit() {
  fireEvent.click(await screen.findByRole('button', { name: /Fill in holes/ }));
  expect(screen.queryByLabelText('running total Removed hole 1')).toBeNull();
  for (let h = 1; h <= 18; h++) {
    fireEvent.change(screen.getByLabelText(`running total Blair hole ${h}`), { target: { value: String(2 * h) } });
    fireEvent.change(screen.getByLabelText(`running total Avery hole ${h}`), { target: { value: String(-2 * h) } });
  }
}
function expectAttribution(write, revision) {
  expect(write.revision).toBe(revision);
  expect(write.cells).toHaveLength(36);
  expect(write.cells.filter(q => q.id === 'b')).toEqual(Array.from({ length: 18 }, (_, i) => ({ id: 'b', hole: i + 1, quarters: 2 })));
  expect(write.cells.filter(q => q.id === 'a')).toEqual(Array.from({ length: 18 }, (_, i) => ({ id: 'a', hole: i + 1, quarters: -2 })));
}
it('actual page maps reversed result order and a filtered earlier state slot to stable participants', async () => {
  const { interpreted } = network();
  renderPage(); await edit();
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  await waitFor(() => expect(interpreted).toHaveLength(1));
  expectAttribution(interpreted[0], 9);
});
it('stale retained draft keeps stable visible slots and remaps to fresh full-state indices only after explicit reload', async () => {
  const { interpreted } = network({ stale: true });
  const view = renderPage(); await edit();
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  await screen.findByText(/Round changed/);
  view.unmount(); renderPage();
  fireEvent.click(await screen.findByRole('button', { name: /Fill in holes/ }));
  expect(screen.getByLabelText('running total Blair hole 1')).toHaveValue(2);
  expect(screen.getByLabelText('running total Avery hole 1')).toHaveValue(-2);
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  expect(interpreted).toHaveLength(1);
  fireEvent.click(screen.getByRole('button', { name: 'Reload accepted round' }));
  await screen.findByText(/Accepted round reloaded/);
  expect(interpreted).toHaveLength(1);
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  await waitFor(() => expect(interpreted).toHaveLength(2));
  expectAttribution(interpreted[0], 9);
  expectAttribution(interpreted[1], 10);
});
it('blocks missing stable roster mappings instead of guessing by display order or name', async () => {
  const { interpreted } = network({ missing: true });
  renderPage(); await edit();
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  await screen.findByText(/participant mapping unavailable/i);
  expect(interpreted).toHaveLength(0);
});
