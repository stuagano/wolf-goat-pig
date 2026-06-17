import syncManager, {
  hasPendingSyncForGame,
  reconcileOnLoad,
} from '../syncManager';

beforeEach(() => {
  syncManager.clearQueue();
  syncManager.clearLocalGameState('g1');
  syncManager.clearLocalGameState('g2');
});

describe('hasPendingSyncForGame', () => {
  test('false when the queue has no item for this game', () => {
    expect(hasPendingSyncForGame('g1')).toBe(false);
  });

  test('true only for the game with a queued item (isolates games)', () => {
    syncManager.queueSync('g1', 'scores', { holes: [] });
    expect(hasPendingSyncForGame('g1')).toBe(true);
    expect(hasPendingSyncForGame('g2')).toBe(false);
  });
});

describe('reconcileOnLoad', () => {
  test('no pending edits -> overwrites the cache with server state (heals)', () => {
    syncManager.saveLocalGameState('g1', {
      holeHistory: [{ hole: 1 }, { hole: 1 }, { hole: 2 }],
    });
    const server = { holeHistory: [{ hole: 1 }, { hole: 2 }], currentHole: 3 };

    reconcileOnLoad('g1', server);

    const healed = syncManager.loadLocalGameState('g1');
    expect(healed.holeHistory).toEqual(server.holeHistory);
    expect(healed.currentHole).toBe(3);
  });

  test('pending edits -> leaves the local cache untouched (no lost work)', () => {
    syncManager.saveLocalGameState('g1', { holeHistory: [{ hole: 1 }, { hole: 2 }] });
    syncManager.queueSync('g1', 'scores', { holes: [] });

    reconcileOnLoad('g1', { holeHistory: [{ hole: 1 }] });

    const kept = syncManager.loadLocalGameState('g1');
    expect(kept.holeHistory).toEqual([{ hole: 1 }, { hole: 2 }]);
  });

  test('no queue item but local has a hole the server lacks -> not overwritten (in-flight sync)', () => {
    // local has hole 3 the server doesn't, and NO queued item (the online POST
    // was in flight when the page reloaded) — must not drop hole 3.
    syncManager.saveLocalGameState('g1', {
      holeHistory: [{ hole: 1 }, { hole: 2 }, { hole: 3 }],
    });

    reconcileOnLoad('g1', { holeHistory: [{ hole: 1 }, { hole: 2 }] });

    const kept = syncManager.loadLocalGameState('g1');
    expect(kept.holeHistory).toEqual([{ hole: 1 }, { hole: 2 }, { hole: 3 }]);
  });
});
