import { reconcileGameState } from '../gameReconcile';

const local = { holeHistory: [{ hole: 1 }, { hole: 1 }, { hole: 2 }] }; // longer + duplicate
const server = { holeHistory: [{ hole: 1 }, { hole: 2 }] };

describe('reconcileGameState', () => {
  test('no local -> server', () => {
    expect(reconcileGameState({ serverState: server, localState: null, hasPendingEdits: false }))
      .toBe(server);
  });

  test('local + no pending edits -> server (heals, even when local is longer/duplicated)', () => {
    expect(reconcileGameState({ serverState: server, localState: local, hasPendingEdits: false }))
      .toBe(server);
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
