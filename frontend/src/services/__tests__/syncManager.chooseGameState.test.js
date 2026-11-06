import syncManager, { chooseGameState, localHasUnsyncedHoles } from '../syncManager';

const local = { holeHistory: [{ hole: 1 }, { hole: 1 }, { hole: 2 }] }; // longer + duplicate, same hole NUMBERS as server
const server = { holeHistory: [{ hole: 1 }, { hole: 2 }] };
const localAhead = { holeHistory: [{ hole: 1 }, { hole: 2 }, { hole: 3 }] }; // has hole 3 the server lacks

beforeEach(() => {
  syncManager.clearQueue();
  syncManager.clearLocalGameState('g1');
});

describe('localHasUnsyncedHoles', () => {
  test('false when local holes are a subset of server (duplicates do not count)', () => {
    expect(localHasUnsyncedHoles(local, server)).toBe(false);
  });

  test('true when local has a hole the server lacks', () => {
    expect(localHasUnsyncedHoles(localAhead, server)).toBe(true);
  });
});

describe('chooseGameState', () => {
  test('no local -> server', () => {
    expect(chooseGameState('g1', server)).toBe(server);
  });

  test('local + no pending edits, not ahead -> server (heals, even when longer/duplicated)', () => {
    syncManager.saveLocalGameState('g1', local);
    expect(chooseGameState('g1', server)).toBe(server);
  });

  test('local has a hole the server lacks + no pending edits -> local (in-flight sync preserved)', () => {
    syncManager.saveLocalGameState('g1', localAhead);
    expect(chooseGameState('g1', server).holeHistory).toEqual(localAhead.holeHistory);
  });

  test('local + pending edits -> local (unsynced work is preserved)', () => {
    syncManager.saveLocalGameState('g1', local);
    syncManager.queueSync('g1', 'scores', { holes: [] });
    expect(chooseGameState('g1', server).holeHistory).toEqual(local.holeHistory);
  });

  test('pending edits but no local -> server (nothing to prefer)', () => {
    syncManager.queueSync('g1', 'scores', { holes: [] });
    expect(chooseGameState('g1', server)).toBe(server);
  });
});
