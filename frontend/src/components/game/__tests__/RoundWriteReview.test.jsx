import React from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen, fireEvent } from '@testing-library/react';
import ScorecardReview from '../ScorecardReview';
import syncManager from '../../../services/syncManager';

afterEach(() => { cleanup(); syncManager.clearQueue(); localStorage.clear(); vi.useRealTimers(); });
const names = ['One', 'Two', 'Three', 'Four'];
const reversed = {
  players: [...names].reverse().map(name => ({ name })),
  running_totals: Array.from({ length: 4 }, (_, player_index) => Array.from({ length: 18 }, (_, h) => ({ player_index, hole: h + 1, value: 0 }))).flat(),
};

it('edits the displayed mapped player total, not the positional picked player', () => {
  const confirm = vi.fn();
  render(<ScorecardReview extraction={reversed} players={[]} pickedPlayers={names} mode="new-round" onConfirm={confirm} />);
  fireEvent.change(screen.getByLabelText('One final total'), { target: { value: '7' } });
  fireEvent.click(screen.getByRole('button', { name: /Confirm Totals/ }));
  expect(confirm.mock.calls[0][0].players.find(p => p.name === 'One').quarters).toBe(7);
});

it('edits attach cells by displayed mapped slot after reversed OCR', () => {
  const confirm = vi.fn();
  render(<ScorecardReview extraction={reversed} players={names.map((name, i) => ({ id: `p${i + 1}`, name }))} onConfirm={confirm} />);
  fireEvent.change(screen.getByLabelText('One hole 18 running total'), { target: { value: '2' } });
  fireEvent.change(screen.getByLabelText('Two hole 18 running total'), { target: { value: '-2' } });
  fireEvent.click(screen.getByRole('button', { name: /Confirm/ }));
  expect(confirm.mock.calls[0][0]['18']).toMatchObject({ p1: 2, p2: -2, p3: 0, p4: 0 });
});

it('interactive conflict with existing pending work holds the merged evidence', async () => {
  vi.useFakeTimers();
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: { code: 'stale_round', revision: 7 } }), { status: 409 }));
  const stop = syncManager.setupAutoSync(fetcher);
  syncManager.queueSync('round', 'scores', { hole_quarters: { 1: { p1: 1 } }, expected_revision: 2 });
  await syncManager.syncHoleData('round', { 1: { p1: 5 } }, {}, 2, 2);
  expect(syncManager.getSyncQueue().every(item => item.reviewRequired)).toBe(true);
  expect(syncManager.getSyncQueue().some(item => item.payload.hole_quarters['1'].p1 === 5 && item.review.code === 'stale_round')).toBe(true);
  await syncManager.processQueue();
  expect(fetcher).toHaveBeenCalledTimes(1);
  stop();
});

it('does not rebase a same-round replacement with an unrelated stale baseline', async () => {
  vi.useFakeTimers();
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
  let acknowledge;
  const fetcher = vi.fn().mockImplementationOnce(() => new Promise(resolve => { acknowledge = resolve; }))
    .mockImplementation(async (_, options) => JSON.parse(options.body).expected_revision === 3
      ? new Response(JSON.stringify({ revision: 4 }))
      : new Response(JSON.stringify({ detail: { code: 'stale_round', revision: 3 } }), { status: 409 }));
  const stop = syncManager.setupAutoSync(fetcher);
  syncManager.queueSync('round', 'scores', { hole_quarters: { 1: { p1: 1 } }, expected_revision: 2 });
  const draining = syncManager.processQueue();
  syncManager.queueSync('round', 'scores', { hole_quarters: { 1: { p1: 8 } }, expected_revision: 1 });
  acknowledge(new Response(JSON.stringify({ revision: 3 })));
  await draining;
  expect(syncManager.getSyncQueue()[0]).toMatchObject({ version: 2, payload: { expected_revision: 1, hole_quarters: { 1: { p1: 8 } } } });
  await syncManager.processQueue();
  expect(syncManager.getSyncQueue()[0]).toMatchObject({ reviewRequired: true, payload: { expected_revision: 1 } });
  stop();
});

it('only a proven in-flight descendant advances its server baseline', async () => {
  vi.useFakeTimers();
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
  let acknowledge;
  let revision = 2;
  const fetcher = vi.fn().mockImplementationOnce(() => new Promise(resolve => { acknowledge = resolve; })).mockImplementation(async (_, options) => {
    const body = JSON.parse(options.body);
    if (body.expected_revision !== revision) return new Response('{}', { status: 409 });
    return new Response(JSON.stringify({ revision: ++revision }));
  });
  const stop = syncManager.setupAutoSync(fetcher);
  const id = syncManager.queueSync('round', 'scores', { hole_quarters: { 1: { p1: 1 } }, expected_revision: 2 });
  const draining = syncManager.processQueue();
  syncManager.queueSync('round', 'scores', { hole_quarters: { 1: { p1: 3 } }, expected_revision: 2 });
  syncManager.queueSync('unrelated', 'scores', { hole_quarters: { 1: { p1: 8 } }, expected_revision: 1 }, { reviewRequired: true });
  revision = 3;
  acknowledge(new Response(JSON.stringify({ revision })));
  await draining;
  expect(syncManager.getSyncQueue().find(item => item.id === id)).toMatchObject({ version: 2, payload: { expected_revision: 3, hole_quarters: { 1: { p1: 3 } } } });
  expect(syncManager.getSyncQueue().find(item => item.gameId === 'unrelated').payload.expected_revision).toBe(1);
  await syncManager.processQueue();
  expect(syncManager.getSyncQueue().some(item => item.id === id)).toBe(false);
  stop();
});
