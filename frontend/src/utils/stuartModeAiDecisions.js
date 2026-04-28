// Stuart Mode — heuristic AI decision logic. Used when Stuart is playing
// solo and an AI player is rotation captain: the AI picks team mode and
// (in partners mode) a teammate. Decisions are deterministic given the
// inputs, so the same hole state always yields the same call.

const SOLO_HCP_THRESHOLD = 15; // captain handicap above this rarely solos
const SOLO_QUARTERS_FLOOR = -5; // already deeply down — partner up
const HUNGRY_THRESHOLD = -5; // quarters at or below = "hungry"
const STRONG_PLAYER_HCP = 10; // below this = always backs themselves

export function aiPartnerResponse({
  aiPlayer,
  currentHole,
  strokeAllocation,
  playerStandings,
}) {
  const strokes = strokeAllocation?.[aiPlayer.id]?.[currentHole] ?? 0;
  const quarters = playerStandings?.[aiPlayer.id]?.quarters ?? 0;
  const handicap = Number(aiPlayer.handicap) || 18;

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
  const handicap = Number(aiPlayer.handicap) || 18;

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
    const handicap = Number(ai.handicap) || 18;
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
