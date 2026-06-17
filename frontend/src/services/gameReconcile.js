// Decide which game state to display on load.
//
// Local is an offline write-buffer: trust it over the server ONLY when this
// game has edits not yet pushed. Otherwise the server (DB) is authoritative —
// this is what heals stale/duplicated local state instead of letting a
// longer-but-wrong cache win. See
// docs/superpowers/specs/2026-06-16-cross-device-game-sync-design.md
export function reconcileGameState({ serverState, localState, hasPendingEdits }) {
  if (hasPendingEdits && localState) return localState;
  return serverState;
}
