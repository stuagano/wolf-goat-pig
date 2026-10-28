// frontend/src/hooks/__tests__/useGameData.test.js
import { act, renderHook, waitFor } from '@testing-library/react';
import useGameData, { normalizeGameState } from '../useGameData';
import syncManager from '../../services/syncManager';

const players = [{ id: 'p1', name: 'Alice' }];

describe('normalizeGameState', () => {
  test('completed round with no current_hole is complete and past hole 18', () => {
    const game = normalizeGameState({ players, game_status: 'completed', hole_history: [] });
    expect(game.isComplete).toBe(true);
    expect(game.currentHole).toBeGreaterThan(18);
  });

  test('in-progress round with no current_hole starts at hole 1', () => {
    const game = normalizeGameState({ players, game_status: 'in_progress' });
    expect(game.isComplete).toBe(false);
    expect(game.currentHole).toBe(1);
  });

  test('mid-round keeps the server current_hole and maps fields to camelCase', () => {
    const game = normalizeGameState({
      players,
      game_status: 'in_progress',
      current_hole: 7,
      hole_history: [{ hole: 1 }],
      standings: { p1: 2 },
      base_wager: 2,
      course_name: 'Test GC',
      stroke_allocation: { p1: {} },
    });
    expect(game).toEqual({
      players,
      currentHole: 7,
      holeHistory: [{ hole: 1 }],
      standings: { p1: 2 },
      strokeAllocation: { p1: {} },
      courseName: 'Test GC',
      baseWager: 2,
      isComplete: false,
      gameStatus: 'in_progress',
      expectedRevision: undefined,
    });
  });
});

describe('useGameData', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(syncManager, 'reconcileOnLoad').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('loads completed state without live reconciliation', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ players, game_status: 'completed', hole_history: [] }),
    });

    const { result } = renderHook(() => useGameData('g1'));
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBeNull();
    expect(result.current.game.isComplete).toBe(true);
    // A round completed after the page's lifecycle read must not be reconciled
    // through the active offline write buffer.
    expect(syncManager.reconcileOnLoad).not.toHaveBeenCalled();
  });

  test('reconciles and normalizes an active round', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ players, game_status: 'in_progress', current_hole: 3, hole_history: [] }),
    });

    const { result } = renderHook(() => useGameData('g1'));
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.game).toMatchObject({ isComplete: false, currentHole: 3 });
    expect(syncManager.reconcileOnLoad).toHaveBeenCalledWith('g1', expect.objectContaining({ players }));
  });

  test('never serves a cached completed round as server truth', async () => {
    global.fetch.mockRejectedValueOnce(new Error('offline'));
    vi.spyOn(syncManager, 'loadLocalGameState').mockReturnValue({ players, currentHole: 19, gameStatus: 'completed', holeHistory: [] });

    const { result } = renderHook(() => useGameData('g1'));
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.game).toBeNull();
    expect(result.current.error).toBe('offline');
  });

  test('falls back to the local write-buffer when the server is unreachable', async () => {
    global.fetch.mockRejectedValueOnce(new Error('offline'));
    vi.spyOn(syncManager, 'loadLocalGameState').mockReturnValue({ players, currentHole: 4, holeHistory: [] });
    vi.spyOn(syncManager, 'ensureScoresQueued').mockImplementation(() => {});

    const { result } = renderHook(() => useGameData('g1'));
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBeNull();
    expect(result.current.game).toMatchObject({ players, currentHole: 4, isComplete: false });
  });

  test.each(['offline', 'server reconciliation'])('retains the cached round when only queue storage fails during %s', async (mode) => {
    const cached = {
      players,
      currentHole: 2,
      holeHistory: [{ hole: 1, quarters: { p1: 2 }, gross_scores: { p1: 5 } }],
      playerStandings: { p1: 2 },
      courseName: 'Cached GC',
      baseWager: 3,
    };
    localStorage.clear();
    expect(syncManager.saveLocalGameState('queue-storage-failure', cached)).toBe(true);
    syncManager.reconcileOnLoad.mockRestore();
    if (mode === 'offline') {
      global.fetch.mockRejectedValueOnce(new Error('offline'));
    } else {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ players, current_hole: 1, hole_history: [] }),
      });
    }
    const setItem = localStorage.setItem.getMockImplementation();
    localStorage.setItem.mockImplementation((key, value) => {
      if (key === 'wgp-sync_sync-queue') throw new Error('Queue storage full');
      return setItem(key, value);
    });
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    try {
      const { result } = renderHook(() => useGameData('queue-storage-failure'));
      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.game).toMatchObject({
        players,
        holeHistory: cached.holeHistory,
        standings: cached.playerStandings,
        currentHole: 2,
        courseName: 'Cached GC',
        baseWager: 3,
      });
      // A fatal error would make SimpleScorekeeperPage hide this usable round.
      expect(result.current.error).toBeNull();
      expect(result.current.syncError).toMatch(/reload before submitting/i);
      expect(result.current.syncError).not.toMatch(/will retry|pending sync/i);
      expect(syncManager.getSyncQueue()).toEqual([]);
      expect(syncManager.loadLocalGameState('queue-storage-failure')).toMatchObject(cached);
      expect(localStorage.getItem('wgp_current_game')).toBe('queue-storage-failure');
    } finally {
      localStorage.setItem.mockImplementation(setItem);
      localStorage.clear();
    }
  });

  test.each([true, false])('retrySync keeps the loaded game unchanged when queue persistence succeeds=%s', async (succeeds) => {
    const setItem = localStorage.setItem.getMockImplementation();
    let storageFails = true;
    localStorage.clear();
    const cached = {
      players, currentHole: 2,
      holeHistory: [{ hole: 1, quarters: { p1: 2 }, gross_scores: { p1: 5 } }],
    };
    syncManager.saveLocalGameState('retry-cache', cached);
    localStorage.setItem.mockImplementation((key, value) => {
      if (key === 'wgp-sync_sync-queue' && storageFails) throw new Error('Queue storage full');
      return setItem(key, value);
    });
    vi.stubGlobal('navigator', { onLine: false });
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    global.fetch.mockRejectedValueOnce(new Error('offline'));
    try {
      const { result } = renderHook(() => useGameData('retry-cache'));
      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(result.current.syncError).toMatch(/reload/i);
      const loadedGame = result.current.game;
      // Retry must re-read current saved scores, not the hook's older snapshot.
      syncManager.saveLocalGameState('retry-cache', {
        ...cached, holeHistory: [{ hole: 1, quarters: { p1: 3 }, gross_scores: { p1: 6 } }],
      });
      storageFails = !succeeds;
      let queued;
      act(() => { queued = result.current.retrySync(); });
      expect(queued).toBe(false);
      expect(result.current.loading).toBe(false);
      expect(result.current.game).toBe(loadedGame);
      expect(result.current.error).toBeNull();
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(result.current.syncError).toMatch(/reload/i);
      expect(syncManager.getSyncQueue()).toEqual([]);
      expect(syncManager.loadLocalGameState('retry-cache').holeHistory[0].gross_scores.p1).toBe(6);
    } finally {
      localStorage.setItem.mockImplementation(setItem);
      localStorage.clear();
      vi.unstubAllGlobals();
    }
  });

  test('surfaces an error when the server fails and there is no local roster', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    vi.spyOn(syncManager, 'loadLocalGameState').mockReturnValue(null);

    const { result } = renderHook(() => useGameData('g1'));
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Failed to load game');
    expect(result.current.game).toBeNull();
  });
});
