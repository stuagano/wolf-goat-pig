import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { clearQueue, setupAutoSync, syncHoleData, saveLocalGameState, loadLocalGameState } from '../syncManager';

let cleanup;
beforeEach(() => {
  vi.useFakeTimers();
  clearQueue();
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
});
afterEach(() => {
  cleanup?.();
  vi.useRealTimers();
});

test('rejected score request returns a safe correlation reference from the API', async () => {
  cleanup = setupAutoSync(async () => new Response(JSON.stringify({ detail: 'Scores must balance' }), {
    status: 400, headers: { 'X-Request-ID': 'score-request-123' },
  }));
  const result = await syncHoleData('g1', { 1: { p1: 1 } }, {}, 19);
  expect(result).toMatchObject({ success: false, permanent: true, requestId: 'score-request-123' });
  expect(result.error).toContain('Reference: score-request-123');
});

test('a confirmed save retains the new server revision separately from the local draft', async () => {
  saveLocalGameState('g-revision', { expectedRevision: 2, holeHistory: [{ hole: 1 }], currentHole: 2 });
  cleanup = setupAutoSync(async () => new Response(JSON.stringify({ revision: 3, game_status: 'in_progress' })));
  await syncHoleData('g-revision', { 1: { p1: 1 } }, {}, 2);
  expect(loadLocalGameState('g-revision')).toMatchObject({ expectedRevision: 3, holeHistory: [{ hole: 1 }] });
});

test('untrusted correlation headers are never reflected in the error', async () => {
  cleanup = setupAutoSync(async () => new Response('{}', {
    status: 422, headers: { 'X-Request-ID': 'unsafe personal data' },
  }));
  const result = await syncHoleData('g1', {}, {}, 19);
  expect(result.requestId).toBeUndefined();
  expect(result.error).not.toContain('unsafe');
});
