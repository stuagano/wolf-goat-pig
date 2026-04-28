// Stuart Mode — heuristic AI decision logic. Used when Stuart is playing
// solo and an AI player is rotation captain: the AI picks team mode and
// (in partners mode) a teammate. Decisions are deterministic given the
// inputs, so the same hole state always yields the same call.

const SOLO_HCP_THRESHOLD = 15; // captain handicap above this rarely solos
const SOLO_QUARTERS_FLOOR = -5; // already deeply down — partner up
const HUNGRY_THRESHOLD = -5; // quarters at or below = "hungry"
const STRONG_PLAYER_HCP = 10; // below this = always backs themselves
const SOLO_HCP_EDGE = 4; // captain hcp this many strokes below field avg → confident solo
const DOUBLE_OFFER_FREQ = 3; // 1-in-N hash gate so AI doesn't offer every favorable hole

// Tiny string hash used for deterministic per-(player, hole) gating. Same
// inputs always return the same boolean, so re-renders are stable.
const stableHash = (str) => {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
};

export function aiPartnerResponse({
  aiPlayer,
  currentHole,
  strokeAllocation,
  playerStandings,
}) {
  const strokes = strokeAllocation?.[aiPlayer.id]?.[currentHole] ?? 0;
  const quarters = playerStandings?.[aiPlayer.id]?.quarters ?? 0;
  const handicap = (Number.isFinite(Number(aiPlayer.handicap)) ? Number(aiPlayer.handicap) : 18);

  if (strokes >= 1) {
    return { decision: "accept", reason: "has a stroke on this hole" };
  }
  if (handicap < STRONG_PLAYER_HCP) {
    return { decision: "accept", reason: "strong player, takes the bet" };
  }
  if (quarters < HUNGRY_THRESHOLD) {
    return { decision: "accept", reason: "hungry, needs the points" };
  }
  return { decision: "decline", reason: "handicap too high to risk it" };
}

export function aiDoubleResponse({
  aiPlayer,
  currentHole,
  strokeAllocation,
  playerStandings,
  currentWager,
}) {
  const strokes = strokeAllocation?.[aiPlayer.id]?.[currentHole] ?? 0;
  const quarters = playerStandings?.[aiPlayer.id]?.quarters ?? 0;
  const handicap = (Number.isFinite(Number(aiPlayer.handicap)) ? Number(aiPlayer.handicap) : 18);

  // Accept if you have a stroke (favorable) or you're hungry and need a swing.
  if (strokes >= 1) {
    return { decision: "accept", reason: "stroke on the hole, take the double" };
  }
  if (quarters < HUNGRY_THRESHOLD) {
    return { decision: "accept", reason: "down too far, needs the swing" };
  }
  // Decline if no stroke and the wager is already large.
  if (currentWager >= 4 && handicap >= 12) {
    return { decision: "decline", reason: "wager too rich without a stroke" };
  }
  // Default: accept on small wagers, decline larger
  if (currentWager <= 2) {
    return { decision: "accept", reason: "wager small enough to call" };
  }
  return { decision: "decline", reason: "no stroke, wager too high" };
}

// Should an AI team initiate a double offer? Heuristic returns the AI player
// who would offer (and a reason), or null if nobody on the AI team wants to.
export function aiShouldOfferDouble({
  aiTeamPlayers,
  currentHole,
  strokeAllocation,
  playerStandings,
  currentWager,
}) {
  if (!aiTeamPlayers?.length) return null;
  for (const ai of aiTeamPlayers) {
    const strokes = strokeAllocation?.[ai.id]?.[currentHole] ?? 0;
    const quarters = playerStandings?.[ai.id]?.quarters ?? 0;
    const handicap = (Number.isFinite(Number(ai.handicap)) ? Number(ai.handicap) : 18);
    // Per-hole gate so a player who has strokes on every hole doesn't
    // offer doubles on every single hole. Roughly 1-in-DOUBLE_OFFER_FREQ.
    const gate = stableHash(`${ai.id}|${currentHole}|dbl`) % DOUBLE_OFFER_FREQ === 0;
    if (!gate) continue;
    // Offer when you have a stroke and the wager is still cheap.
    if (strokes >= 1 && currentWager <= 2) {
      return { player: ai, reason: "stroke on the hole, presses for value" };
    }
    // Or when ahead in standings and want to put pressure on
    if (quarters > 5 && handicap < STRONG_PLAYER_HCP && currentWager <= 4) {
      return { player: ai, reason: "ahead and confident, applies pressure" };
    }
  }
  return null;
}

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
      const handicap = (Number.isFinite(Number(p.handicap)) ? Number(p.handicap) : 18);
      const hungryPenalty = quarters < -5 ? 3 : 0;
      const score = handicap - strokes * 4 + hungryPenalty;
      return { player: p, score, strokes, quarters };
    })
    .sort((a, b) => a.score - b.score);

  const bestPartner = ranked[0]?.player;

  // Solo gate (tuned against ~17% historical solo rate observed in
  // backend/game_player_results): allow solo when EITHER the captain has
  // a stroke advantage OR their handicap is meaningfully better than
  // the field — both conditions also gated on not being deeply down.
  const captainHcp = (Number.isFinite(Number(captain.handicap)) ? Number(captain.handicap) : 18);
  const fieldAvgHcp =
    others.reduce(
      (s, p) =>
        s + (Number.isFinite(Number(p.handicap)) ? Number(p.handicap) : 18),
      0,
    ) / Math.max(1, others.length);
  const hcpEdge = fieldAvgHcp - captainHcp; // positive = captain better than field

  const eligibleToSolo =
    (captainStrokes >= 1 || hcpEdge >= SOLO_HCP_EDGE) &&
    captainHcp < SOLO_HCP_THRESHOLD &&
    captainQuarters > SOLO_QUARTERS_FLOOR;

  // Also require a per-hole gate so the same captain doesn't solo every
  // single time the conditions allow. Roughly 1-in-2 of eligible holes.
  const soloGate = stableHash(`${captain.id}|${currentHole}|solo`) % 2 === 0;

  if (eligibleToSolo && soloGate) {
    const reason =
      captainStrokes >= 1
        ? `${captain.name} has a stroke and favorable position`
        : `${captain.name} (hcp ${captainHcp}) has a clear edge on the field`;
    return { mode: "solo", partnerId: null, reason };
  }
  return {
    mode: "partners",
    partnerId: bestPartner?.id ?? null,
    reason: bestPartner
      ? `${captain.name} partners ${bestPartner.name} (hcp ${bestPartner.handicap})`
      : `${captain.name} partners (no clear pick)`,
  };
}
