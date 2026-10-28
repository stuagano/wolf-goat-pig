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
it('real successful page read supplies the backfill PATCH revision', async () => {
  const players = ['One', 'Two', 'Three', 'Four'].map((name, i) => ({ id: `p${i}`, name }));
  const fetcher = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, options) => {
    const path = String(url);
    const data = options?.method === 'PATCH' ? { revision: 10 }
      : path.endsWith('/state') ? { game_status: 'completed' }
      : path.endsWith('/round-summary') ? { players: players.map(p => ({ ...p, participant_id: p.id, quarters: 0 })), revision: 9, hole_history: [], detail_coverage: 'totals_only' }
      : path.endsWith('/discussion') ? { comments: [], reactions: [] } : null;
    return new Response(JSON.stringify(data), { status: data ? 200 : 404 });
  });
  render(<MemoryRouter initialEntries={['/game/round']}><Routes><Route path="/game/:gameId" element={<SimpleScorekeeperPage />} /></Routes></MemoryRouter>);
  fireEvent.click(await screen.findByRole('button', { name: /Fill in holes/ }));
  players.forEach(p => { for (let h = 1; h <= 18; h++) fireEvent.change(screen.getByLabelText(`running total ${p.name} hole ${h}`), { target: { value: '0' } }); });
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  await waitFor(() => expect(fetcher.mock.calls.some(([, options]) => options?.method === 'PATCH')).toBe(true));
  const patch = fetcher.mock.calls.find(([, options]) => options?.method === 'PATCH');
  expect(JSON.parse(patch[1].body).expected_revision).toBe(9);
});
