// Local recovery evidence only: never an accepted score or an automatic retry.
const key = (gameId, kind) => `wgp_round_draft:${gameId}:${kind}`;
export function readDraft(gameId, kind) {
  try { return JSON.parse(localStorage.getItem(key(gameId, kind)) || 'null'); }
  catch { return null; }
}
export function keepDraft(gameId, kind, draft) {
  localStorage.setItem(key(gameId, kind), JSON.stringify(draft));
}
export function clearDraft(gameId, kind) {
  try { localStorage.removeItem(key(gameId, kind)); } catch { /* nothing retained to clear */ }
}

export function extractionFromQuarters(players, quarters) {
  const running_totals = [];
  players.forEach((player, player_index) => {
    let total = 0;
    for (let hole = 1; hole <= 18; hole++) {
      const delta = quarters[String(hole)]?.[player.id];
      if (!Number.isFinite(delta)) break;
      total += delta;
      running_totals.push({ player_index, hole, value: total, confidence: 1 });
    }
  });
  return { players: players.map(p => ({ name: p.name })), running_totals };
}
