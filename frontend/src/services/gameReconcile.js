// Decide which game state to display on load.
//
// Local is an offline write-buffer: trust it over the server when this game
// holds work the server hasn't got. Otherwise the server (DB) is authoritative
// — this is what heals stale/duplicated local state instead of letting a
// longer-but-wrong cache win. See
// docs/superpowers/specs/2026-06-16-cross-device-game-sync-design.md

function holeSet(state) {
  return new Set((state?.holeHistory || []).map((h) => h.hole));
}

/**
 * True iff local holds a hole the server lacks (compared by hole NUMBER, not
 * entry count). This captures "local has unsynced work" even when the sync
 * queue is empty — e.g. a reload during an in-flight online POST that hasn't
 * landed yet. Because duplicates share a hole number, a duplicated-but-not-
 * ahead cache returns false here, so it still heals from the server.
 */
export function localHasUnsyncedHoles(localState, serverState) {
  const server = holeSet(serverState);
  for (const n of holeSet(localState)) {
    if (!server.has(n)) return true;
  }
  return false;
}

/**
 * Choose the state to display on load. Local wins when this game has a queued
 * edit OR local holds holes the server lacks; otherwise the server wins (heals
 * stale/duplicated local).
 */
export function reconcileGameState({ serverState, localState, hasPendingEdits }) {
  if (!localState) return serverState;
  if (hasPendingEdits) return localState;
  if (localHasUnsyncedHoles(localState, serverState)) return localState;
  return serverState;
}
