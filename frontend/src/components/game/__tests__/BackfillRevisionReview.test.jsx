import React from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';
import ScorecardBackfill from '../ScorecardBackfill';
const fetcher = vi.fn();
vi.mock('../../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => fetcher }));
vi.mock('../ScorecardPhotoButton', () => ({ default: () => null }));
const players = ['One', 'Two', 'Three', 'Four'].map((name, i) => ({ id: `p${i}`, name }));
const props = { gameId: 'round', players, holeHistory: [], standings: { p0: 0, p1: 0, p2: 0, p3: 0 }, onSaved: vi.fn(), onCancel: vi.fn(), expectedRevision: 4 };
afterEach(() => { cleanup(); localStorage.clear(); fetcher.mockReset(); });
function fill() {
  players.forEach(p => { for (let h = 1; h <= 18; h++) fireEvent.change(screen.getByLabelText(`running total ${p.name} hole ${h}`), { target: { value: '0' } }); });
}
it('does not fabricate missing participant holes', async () => {
  render(<ScorecardBackfill {...props} />);
  fireEvent.change(screen.getByLabelText('running total One hole 18'), { target: { value: '0' } });
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  expect(fetcher).not.toHaveBeenCalled();
});
it.each(['reordered', 'changed'])('holds original nonzero draft through a %s roster remount and later edit', roster => {
  const first = render(<ScorecardBackfill {...props} />);
  fireEvent.change(screen.getByLabelText('running total One hole 1'), { target: { value: '7' } });
  fireEvent.change(screen.getByLabelText('running total Four hole 18'), { target: { value: '-9' } });
  const key = 'wgp_round_draft:round:backfill';
  const original = localStorage.getItem(key);
  first.unmount();
  const nextPlayers = roster === 'reordered' ? [...players].reverse()
    : [players[1], players[0], players[2], { id: 'p4', name: 'Five' }];
  const next = render(<ScorecardBackfill {...props} players={nextPlayers} expectedRevision={8} />);
  fireEvent.change(screen.getByLabelText('running total Two hole 2'), { target: { value: '11' } });
  expect(localStorage.getItem(key)).toBe(original);
  expect(screen.getByRole('alert')).toHaveTextContent(/roster changed/i);
  expect(JSON.parse(screen.getByLabelText('Retained backfill draft JSON').value)).toEqual(JSON.parse(original));
  expect(screen.queryByRole('button', { name: 'Reload accepted round' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  expect(localStorage.getItem(key)).toBe(original);
  expect(fetcher).not.toHaveBeenCalled();
  next.unmount();
  render(<ScorecardBackfill {...props} players={nextPlayers} expectedRevision={8} />);
  const recovered = JSON.parse(screen.getByLabelText('Retained backfill draft JSON').value);
  expect(recovered.slots).toEqual(['p0', 'p1', 'p2', 'p3']);
  expect(recovered.values).toMatchObject({ '0-1': 7, '3-18': -9 });
  expect(fetcher).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: /Discard retained draft/ }));
  fireEvent.change(screen.getByLabelText('running total Two hole 2'), { target: { value: '12' } });
  expect(JSON.parse(localStorage.getItem(key)).slots).toEqual(nextPlayers.map(p => p.id));
  expect(fetcher).not.toHaveBeenCalled();
});

it('submits observed revision, retains stale edited draft across remount, and explicitly reloads before resubmit', async () => {
  fetcher.mockResolvedValueOnce(new Response(JSON.stringify({ detail: { code: 'stale_round', revision: 5, issue_ids: [] } }), { status: 409 }));
  const view = render(<ScorecardBackfill {...props} />);
  fill();
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  await waitFor(() => expect(fetcher).toHaveBeenCalledOnce());
  expect(JSON.parse(fetcher.mock.calls[0][1].body).expected_revision).toBe(4);
  await screen.findByRole('button', { name: 'Reload accepted round' });
  view.unmount();
  render(<ScorecardBackfill {...props} />);
  expect(screen.getByLabelText('running total One hole 18')).toHaveValue(0);
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  expect(fetcher).toHaveBeenCalledOnce();
  fetcher.mockResolvedValueOnce(new Response(JSON.stringify({ revision: 5, standings: props.standings })));
  fireEvent.click(screen.getByRole('button', { name: 'Reload accepted round' }));
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
  fetcher.mockResolvedValueOnce(new Response(JSON.stringify({ revision: 6 })));
  fireEvent.click(screen.getByLabelText('Save hole detail'));
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));
  expect(JSON.parse(fetcher.mock.calls[2][1].body).expected_revision).toBe(5);
});
