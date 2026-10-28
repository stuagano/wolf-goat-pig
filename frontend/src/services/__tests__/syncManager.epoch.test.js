import syncManager, { reconcileOnLoad } from '../syncManager';

beforeEach(() => {
  syncManager.clearQueue();
  syncManager.clearLocalGameState('epoch-game');
});

test('cutover retains stale queued edits and pauses replay for review', () => {
  syncManager.saveLocalGameState('epoch-game', { writerEpoch: 3, expectedRevision: 1, currentHole: 2 });
  syncManager.queueSync('epoch-game', 'scores', {
    expected_epoch: 3, expected_revision: 1, hole_quarters: { 1: { p1: 2 } },
  });
  reconcileOnLoad('epoch-game', { writerEpoch: 4, expectedRevision: 1, currentHole: 1 });
  const retained = syncManager.getSyncQueue()[0];
  expect(retained.reviewRequired).toBe(true);
  expect(retained.payload.expected_epoch).toBe(3);
  expect(retained.payload.hole_quarters).toEqual({ 1: { p1: 2 } });
  expect(syncManager.loadLocalGameState('epoch-game').writerEpoch).toBe(3);
});

test('new epoch payload cannot merge into an old epoch request', () => {
  syncManager.queueSync('epoch-game', 'scores', { expected_epoch: 3, expected_revision: 1 });
  syncManager.queueSync('epoch-game', 'scores', { expected_epoch: 4, expected_revision: 1 });
  expect(syncManager.getSyncQueue().map(item => item.payload.expected_epoch)).toEqual([3, 4]);
});
