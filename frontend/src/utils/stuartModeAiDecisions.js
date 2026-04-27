// Stuart Mode — heuristic AI decision logic. Used when Stuart is playing
// solo and an AI player is rotation captain: the AI picks team mode and
// (in partners mode) a teammate. Decisions are deterministic given the
// inputs, so the same hole state always yields the same call.

const SOLO_HCP_THRESHOLD = 15; // captain handicap above this rarely solos
const SOLO_QUARTERS_FLOOR = -5; // already deeply down — partner up

export function aiCaptainDecide({
  captain,
  players,
  currentHole,
  strokeAllocation,
  playerStandings,
}) {
  const captainStrokes =
    strokeAllocation?.[captain.id]?.[currentHole] ?? 0;
  const captainQuarters =
    playerStandings?.[captain.id]?.quarters ?? 0;

  const others = players.filter((p) => p.id !== captain.id);

  // Partner score: lower is better. Lower handicap, having a stroke on
  // this hole, and not being deeply hungry all help.
  const ranked = others
    .map((p) => {
      const strokes = strokeAllocation?.[p.id]?.[currentHole] ?? 0;
      const quarters = playerStandings?.[p.id]?.quarters ?? 0;
      const handicap = Number(p.handicap) || 18;
      const hungryPenalty = quarters < -5 ? 3 : 0;
      const score = handicap - strokes * 4 + hungryPenalty;
      return { player: p, score, strokes, quarters };
    })
    .sort((a, b) => a.score - b.score);

  const bestPartner = ranked[0]?.player;

  // Solo when the captain has a real stroke advantage AND isn't already
  // deep in a hole. Falls back to partners with the strongest available.
  const captainHcp = Number(captain.handicap) || 18;
  const canSolo =
    captainStrokes >= 1 &&
    captainHcp < SOLO_HCP_THRESHOLD &&
    captainQuarters > SOLO_QUARTERS_FLOOR;

  if (canSolo) {
    return {
      mode: "solo",
      partnerId: null,
      reason: `${captain.name} has a stroke and favorable position`,
    };
  }
  return {
    mode: "partners",
    partnerId: bestPartner?.id ?? null,
    reason: bestPartner
      ? `${captain.name} partners ${bestPartner.name} (hcp ${bestPartner.handicap})`
      : `${captain.name} partners (no clear pick)`,
  };
}
