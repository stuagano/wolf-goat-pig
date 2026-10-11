// frontend/src/hooks/__tests__/useGameData.test.js
import { renderHook, waitFor } from '@testing-library/react';
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

  test('loads, reconciles, and normalizes server state', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ players, game_status: 'completed', hole_history: [] }),
    });

    const { result } = renderHook(() => useGameData('g1'));
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBeNull();
    expect(result.current.game.isComplete).toBe(true);
    expect(syncManager.reconcileOnLoad).toHaveBeenCalledWith('g1', expect.objectContaining({ players }));
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

  test('surfaces an error when the server fails and there is no local roster', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    vi.spyOn(syncManager, 'loadLocalGameState').mockReturnValue(null);

    const { result } = renderHook(() => useGameData('g1'));
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Failed to load game');
    expect(result.current.game).toBeNull();
  });
});
