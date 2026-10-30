import React from 'react';
import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import ScorecardReview from '../ScorecardReview';
import syncManager from '../../../services/syncManager';

const extraction = {
  players: ['One', 'Two', 'Three', 'Four'].map(name => ({ name, confidence: 1 })),
  running_totals: [3, -3, 0, 0].map((value, player_index) => ({ player_index, hole: 18, value })),
};
beforeEach(() => { localStorage.clear(); vi.useFakeTimers(); });
afterEach(() => { cleanup(); syncManager.clearQueue(); vi.clearAllTimers(); vi.useRealTimers(); });

it('totals-only confirmation sends explicit totals without fabricated holes', () => {
  const confirm = vi.fn();
  render(<ScorecardReview extraction={extraction} players={[]} mode="new-round" onConfirm={confirm} />);
  fireEvent.click(screen.getByRole('button', { name: /Confirm Totals/ }));
  expect(confirm).toHaveBeenCalledOnce();
  const body = confirm.mock.calls[0][0];
  expect(body.detail_coverage).toBe('totals_only');
  expect(body.per_hole_quarters || []).toEqual([]);
  expect(body.players.map(p => p.quarters)).toEqual([3, -3, 0, 0]);
});

it('garbled picked player mapping blocks submission instead of positional attribution', () => {
  render(<ScorecardReview extraction={extraction} players={[]} mode="new-round"
    pickedPlayers={['Unknown', 'Two', 'Three', 'Four']} onConfirm={vi.fn()} />);
  expect(screen.getByRole('button', { name: /continue|mapping/i })).toBeDisabled();
});

it('stale queue retains evidence and request key without automatic overwrite', async () => {
  const fetcher = vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ detail: { code: 'stale_round', revision: 7, issue_ids: ['issue'] } }) });
  const stop = syncManager.setupAutoSync(fetcher);
  syncManager.queueSync('round', 'scores', { hole_quarters: { 1: { p1: 3 } }, expected_revision: 2 }, { requestKey: 'stable-key' });
  await syncManager.processQueue();
  const pending = syncManager.getSyncQueue();
  expect(pending).toHaveLength(1);
  expect(pending[0]).toMatchObject({ requestKey: 'stable-key', reviewRequired: true, payload: { expected_revision: 2 } });
  await syncManager.processQueue();
  expect(fetcher).toHaveBeenCalledTimes(1);
  stop();
});

it('a network retry retains the original submission request key', async () => {
  const fetcher = vi.fn()
    .mockRejectedValueOnce(new TypeError('Network unavailable'))
    .mockResolvedValueOnce(new Response(JSON.stringify({ revision: 3 })));
  const stop = syncManager.setupAutoSync(fetcher);
  const result = await syncManager.syncHoleData('round', { 1: { p1: 3 } }, {}, 2, 2);
  expect(result.queued).toBe(true);
  const firstKey = fetcher.mock.calls[0][1].headers['Idempotency-Key'];
  expect(syncManager.getSyncQueue()[0].requestKey).toBe(firstKey);
  await syncManager.processQueue();
  expect(fetcher.mock.calls[1][1].headers['Idempotency-Key']).toBe(firstKey);
  expect(syncManager.getSyncQueue()).toEqual([]);
  stop();
});

it('a completed read or failed read never seeds an upload', () => {
  syncManager.saveLocalGameState('round', { holeHistory: [{ hole: 1, points_delta: { p1: 3 } }], currentHole: 19, gameStatus: 'completed' });
  expect(syncManager.ensureScoresQueued('round', null)).toBe(false);
  syncManager.reconcileOnLoad('round', { gameStatus: 'completed', holeHistory: [] });
  expect(syncManager.getSyncQueue()).toEqual([]);
});
