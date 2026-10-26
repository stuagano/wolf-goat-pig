import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { clearQueue, setupAutoSync, syncHoleData } from '../syncManager';

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

test('untrusted correlation headers are never reflected in the error', async () => {
  cleanup = setupAutoSync(async () => new Response('{}', {
    status: 422, headers: { 'X-Request-ID': 'unsafe personal data' },
  }));
  const result = await syncHoleData('g1', {}, {}, 19);
  expect(result.requestId).toBeUndefined();
  expect(result.error).not.toContain('unsafe');
});
