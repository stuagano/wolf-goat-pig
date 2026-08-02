/**
 * Course-signal hardening for syncManager: queue merge, never-drop scores,
 * re-seed from local when ahead, payload flags survive toScoresPayload.
 */
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import syncManager, {
  buildScoresPayloadFromLocal,
  ensureScoresQueued,
  toScoresPayload,
} from '../syncManager';

beforeEach(() => {
  syncManager.clearQueue();
  syncManager.clearLocalGameState('g1');
  vi.stubGlobal('navigator', { onLine: true });
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: false,
      status: 503,
      json: async () => ({ detail: 'unavailable' }),
    })),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  syncManager.clearQueue();
  syncManager.clearLocalGameState('g1');
});

describe('toScoresPayload', () => {
  test('passes float / Duncan / carry-over flags through to /scores holes', () => {
    const { holes } = toScoresPayload({
      hole_quarters: { '3': { p1: 1, p2: -1, p3: 0, p4: 0 } },
      optional_details: {
        '3': {
          float_invoked_by: 'p1',
          duncan_invoked: true,
          carry_over_applied: true,
          wager: 2,
          winner: 'push',
        },
      },
      current_hole: 4,
    });

    expect(holes).toHaveLength(1);
    expect(holes[0]).toMatchObject({
      hole_number: 3,
      float_invoked_by: 'p1',
      duncan_invoked: true,
      carry_over_applied: true,
      wager: 2,
      winner: 'push',
    });
  });
});

describe('buildScoresPayloadFromLocal', () => {
  test('rebuilds hole_quarters and optional_details from holeHistory', () => {
    const payload = buildScoresPayloadFromLocal({
      currentHole: 3,
      holeHistory: [
        {
          hole: 1,
          points_delta: { p1: 0, p2: 0, p3: 0, p4: 0 },
          wager: 1,
          winner: 'push',
          float_invoked_by: null,
          carry_over_applied: false,
        },
        {
          hole: 2,
          points_delta: { p1: 2, p2: 2, p3: -2, p4: -2 },
          wager: 2,
          float_invoked_by: 'p1',
          carry_over_applied: true,
        },
      ],
    });

    expect(payload.current_hole).toBe(3);
    expect(payload.hole_quarters['1']).toEqual({ p1: 0, p2: 0, p3: 0, p4: 0 });
    expect(payload.hole_quarters['2']).toEqual({ p1: 2, p2: 2, p3: -2, p4: -2 });
    expect(payload.optional_details['2']).toMatchObject({
      float_invoked_by: 'p1',
      carry_over_applied: true,
      wager: 2,
    });
  });
});

describe('queueSync merge', () => {
  test('merges successive offline hole submits into one scores item', () => {
    vi.stubGlobal('navigator', { onLine: false });

    syncManager.queueSync('g1', 'scores', {
      hole_quarters: { '1': { p1: 1, p2: -1, p3: 0, p4: 0 } },
      optional_details: { '1': { wager: 1 } },
      current_hole: 2,
    });
    syncManager.queueSync('g1', 'scores', {
      hole_quarters: { '2': { p1: 0, p2: 0, p3: 0, p4: 0 } },
      optional_details: { '2': { wager: 1, winner: 'push' } },
      current_hole: 3,
    });

    const queue = syncManager.getSyncQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].payload.hole_quarters).toEqual({
      '1': { p1: 1, p2: -1, p3: 0, p4: 0 },
      '2': { p1: 0, p2: 0, p3: 0, p4: 0 },
    });
    expect(queue[0].payload.current_hole).toBe(3);
  });
});

describe('ensureScoresQueued', () => {
  test('re-seeds the queue from local when local is ahead and queue is empty', () => {
    syncManager.saveLocalGameState('g1', {
      currentHole: 4,
      holeHistory: [
        { hole: 1, points_delta: { p1: 1, p2: -1, p3: 0, p4: 0 }, wager: 1 },
        { hole: 2, points_delta: { p1: 0, p2: 0, p3: 0, p4: 0 }, wager: 1, winner: 'push' },
        { hole: 3, points_delta: { p1: 2, p2: 2, p3: -2, p4: -2 }, wager: 2 },
      ],
      players: [{ id: 'p1', name: 'A' }],
    });

    expect(syncManager.getPendingSyncCount()).toBe(0);

    const queued = ensureScoresQueued('g1', {
      holeHistory: [{ hole: 1 }, { hole: 2 }],
    });

    expect(queued).toBe(true);
    expect(syncManager.hasPendingSyncForGame('g1')).toBe(true);
    const item = syncManager.getSyncQueue()[0];
    expect(item.payload.hole_quarters['3']).toEqual({
      p1: 2,
      p2: 2,
      p3: -2,
      p4: -2,
    });
  });

  test('no-ops when local is not ahead and nothing is queued', () => {
    syncManager.saveLocalGameState('g1', {
      holeHistory: [{ hole: 1, points_delta: { p1: 1 } }],
    });
    expect(
      ensureScoresQueued('g1', { holeHistory: [{ hole: 1 }, { hole: 2 }] }),
    ).toBe(false);
    expect(syncManager.getPendingSyncCount()).toBe(0);
  });
});

describe('processQueue never drops scores', () => {
  test('scores items stay queued after burning through max attempts', async () => {
    syncManager.queueSync('g1', 'scores', {
      hole_quarters: { '1': { p1: 1, p2: -1, p3: 0, p4: 0 } },
      optional_details: {},
      current_hole: 2,
    });

    // Burn attempts with repeated 503s
    for (let i = 0; i < 6; i += 1) {
      // eslint-disable-next-line no-await-in-loop
      await syncManager.processQueue();
    }

    expect(syncManager.hasPendingSyncForGame('g1')).toBe(true);
    expect(syncManager.getSyncQueue()[0].type).toBe('scores');
    expect(syncManager.getSyncQueue()[0].attempts).toBe(5);
  });
});

describe('syncHoleData on flaky online', () => {
  test('queues on network failure even when navigator.onLine is true', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch');
      }),
    );

    const result = await syncManager.syncHoleData(
      'g1',
      { '5': { p1: 1, p2: -1, p3: 0, p4: 0 } },
      { '5': { wager: 1 } },
      6,
    );

    expect(result.success).toBe(true);
    expect(result.queued).toBe(true);
    expect(syncManager.hasPendingSyncForGame('g1')).toBe(true);
  });

  test('queues immediately when offline', async () => {
    vi.stubGlobal('navigator', { onLine: false });

    const result = await syncManager.syncHoleData(
      'g1',
      { '5': { p1: 0, p2: 0, p3: 0, p4: 0 } },
      { '5': { winner: 'push' } },
      6,
    );

    expect(result).toMatchObject({ success: true, queued: true });
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe('reconcileOnLoad re-seeds empty queue', () => {
  test('local ahead with empty queue gets a scores item', () => {
    syncManager.saveLocalGameState('g1', {
      holeHistory: [
        { hole: 1, points_delta: { p1: 1, p2: -1, p3: 0, p4: 0 } },
        { hole: 2, points_delta: { p1: 1, p2: -1, p3: 0, p4: 0 } },
      ],
      currentHole: 3,
    });

    syncManager.reconcileOnLoad('g1', {
      holeHistory: [{ hole: 1 }],
      currentHole: 2,
    });

    expect(syncManager.hasPendingSyncForGame('g1')).toBe(true);
  });
});
