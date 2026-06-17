import { reconcileGameState, localHasUnsyncedHoles } from '../gameReconcile';

const local = { holeHistory: [{ hole: 1 }, { hole: 1 }, { hole: 2 }] }; // longer + duplicate, same hole NUMBERS as server
const server = { holeHistory: [{ hole: 1 }, { hole: 2 }] };
const localAhead = { holeHistory: [{ hole: 1 }, { hole: 2 }, { hole: 3 }] }; // has hole 3 the server lacks

describe('localHasUnsyncedHoles', () => {
  test('false when local holes are a subset of server (duplicates do not count)', () => {
    expect(localHasUnsyncedHoles(local, server)).toBe(false);
  });

  test('true when local has a hole the server lacks', () => {
    expect(localHasUnsyncedHoles(localAhead, server)).toBe(true);
  });
});

describe('reconcileGameState', () => {
  test('no local -> server', () => {
    expect(reconcileGameState({ serverState: server, localState: null, hasPendingEdits: false }))
      .toBe(server);
  });

  test('local + no pending edits, not ahead -> server (heals, even when longer/duplicated)', () => {
    expect(reconcileGameState({ serverState: server, localState: local, hasPendingEdits: false }))
      .toBe(server);
  });

  test('local has a hole the server lacks + no pending edits -> local (in-flight sync preserved)', () => {
    expect(reconcileGameState({ serverState: server, localState: localAhead, hasPendingEdits: false }))
      .toBe(localAhead);
  });

  test('local + pending edits -> local (unsynced work is preserved)', () => {
    expect(reconcileGameState({ serverState: server, localState: local, hasPendingEdits: true }))
      .toBe(local);
  });

  test('pending edits but no local -> server (nothing to prefer)', () => {
    expect(reconcileGameState({ serverState: server, localState: null, hasPendingEdits: true }))
      .toBe(server);
  });
});
