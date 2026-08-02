/**
 * Carry-over + sync integration: after a hole-1 push, reload/reconcile must still
 * open hole 2 at 2× with the carry badge (or re-queue the push for sync).
 */
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { resolveCarryOverForHole } from '../../utils/carryOver';
import { reconcileGameState } from '../gameReconcile';
import syncManager, {
  buildScoresPayloadFromLocal,
  hasPendingSyncForGame,
  reconcileOnLoad,
} from '../syncManager';

const GAME_ID = 'carry-sync-g1';
const BASE_WAGER = 1;

const PUSH_HOLE_1 = {
  hole: 1,
  points_delta: {
    p1: 0,
    p2: 0,
    p3: 0,
    p4: 0,
  },
  winner: 'push',
  wager: 1,
};

const PLAYERS = [
  { id: 'p1', name: 'A' },
  { id: 'p2', name: 'B' },
  { id: 'p3', name: 'C' },
  { id: 'p4', name: 'D' },
];

/** Mirrors SimpleScorekeeperPage reconcile + SimpleScorekeeper restoredState. */
function holeStateAfterReload(gameId, serverState, baseWager = BASE_WAGER) {
  reconcileOnLoad(gameId, serverState);
  const localState = syncManager.loadLocalGameState(gameId);
  const chosen = reconcileGameState({
    serverState,
    localState,
    hasPendingEdits: hasPendingSyncForGame(gameId),
  });
  const holeHistory = chosen?.holeHistory ?? serverState.holeHistory ?? [];
  const currentHole = chosen?.currentHole ?? serverState.currentHole ?? 1;
  const carry = resolveCarryOverForHole({
    holeHistory,
    baseWager,
    holeNumber: currentHole,
  });
  return { holeHistory, currentHole, carry, localState, chosen };
}

beforeEach(() => {
  syncManager.clearQueue();
  syncManager.clearLocalGameState(GAME_ID);
  vi.stubGlobal('navigator', { onLine: true });
});

afterEach(() => {
  vi.unstubAllGlobals();
  syncManager.clearQueue();
  syncManager.clearLocalGameState(GAME_ID);
});

describe('carry-over survives reload/reconcile', () => {
  test('local push ahead of server opens hole 2 at 2q with carry badge', () => {
    syncManager.saveLocalGameState(GAME_ID, {
      holeHistory: [PUSH_HOLE_1],
      currentHole: 2,
      playerStandings: {},
      players: PLAYERS,
      baseWager: BASE_WAGER,
      courseName: 'Wing Point Golf & Country Club',
    });

    const server = { holeHistory: [], currentHole: 1 };
    const { currentHole, carry } = holeStateAfterReload(GAME_ID, server);

    expect(currentHole).toBe(2);
    expect(carry).toEqual({
      wager: 2,
      carryOver: true,
      fromHole: 1,
      consecutiveBlocked: false,
    });
    expect(hasPendingSyncForGame(GAME_ID)).toBe(true);
  });

  test('server synced push still opens hole 2 at 2q after reload heals stale local cache', () => {
    // Duplicate hole-1 rows (same hole numbers as server) — local should NOT win.
    syncManager.saveLocalGameState(GAME_ID, {
      holeHistory: [PUSH_HOLE_1, { ...PUSH_HOLE_1 }],
      currentHole: 2,
    });

    const server = {
      holeHistory: [PUSH_HOLE_1],
      currentHole: 2,
      players: PLAYERS,
      baseWager: BASE_WAGER,
    };

    const { holeHistory, currentHole, carry } = holeStateAfterReload(GAME_ID, server);

    expect(holeHistory).toEqual([PUSH_HOLE_1]);
    expect(currentHole).toBe(2);
    expect(carry.carryOver).toBe(true);
    expect(carry.wager).toBe(2);
  });

  test('in-flight push (no queue item yet) is not overwritten by stale server', () => {
    syncManager.saveLocalGameState(GAME_ID, {
      holeHistory: [PUSH_HOLE_1],
      currentHole: 2,
      players: PLAYERS,
      baseWager: BASE_WAGER,
    });

    const server = { holeHistory: [], currentHole: 1 };
    const { carry, localState } = holeStateAfterReload(GAME_ID, server);

    expect(localState.holeHistory).toEqual([PUSH_HOLE_1]);
    expect(carry).toMatchObject({ wager: 2, carryOver: true, fromHole: 1 });
    expect(hasPendingSyncForGame(GAME_ID)).toBe(true);
  });

  test('re-seeded sync payload preserves push hole for POST /scores', () => {
    syncManager.saveLocalGameState(GAME_ID, {
      holeHistory: [PUSH_HOLE_1],
      currentHole: 2,
      players: PLAYERS,
    });

    reconcileOnLoad(GAME_ID, { holeHistory: [], currentHole: 1 });

    const payload = buildScoresPayloadFromLocal(
      syncManager.loadLocalGameState(GAME_ID),
    );

    expect(payload.hole_quarters['1']).toEqual(PUSH_HOLE_1.points_delta);
    expect(payload.optional_details['1']).toMatchObject({
      winner: 'push',
      wager: 1,
    });
    expect(payload.current_hole).toBe(2);
  });

  test('hole 2 submit after reload carries carry_over_applied in local payload shape', () => {
    const holeHistory = [PUSH_HOLE_1];
    const carry = resolveCarryOverForHole({
      holeHistory,
      baseWager: BASE_WAGER,
      holeNumber: 2,
    });

    expect(carry.carryOver).toBe(true);

    const hole2Result = {
      hole: 2,
      points_delta: { p1: 3, p2: 3, p3: -3, p4: -3 },
      wager: carry.wager,
      carry_over_applied: true,
      winner: null,
    };

    syncManager.saveLocalGameState(GAME_ID, {
      holeHistory: [...holeHistory, hole2Result],
      currentHole: 3,
      players: PLAYERS,
    });

    const payload = buildScoresPayloadFromLocal(
      syncManager.loadLocalGameState(GAME_ID),
    );

    expect(payload.optional_details['2']).toMatchObject({
      carry_over_applied: true,
      wager: 2,
    });
    expect(payload.hole_quarters['2']).toEqual(hole2Result.points_delta);
  });
});
