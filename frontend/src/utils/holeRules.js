/**
 * Wolf Goat Pig hole rules for the live quarters scorekeeper — the one place
 * that decides push, carry-over, hole-18, quarters validity, net winner, and
 * standings. Components and hooks call these; they hold no rule logic.
 *
 * Carry-over: halved hole → next hole starts at 2× that hole's wager (badge
 * shown). Consecutive halves do not stack — second straight push keeps the
 * elevated wager but clears the carry-over badge.
 */

import { parseQuarter } from "./quarters";

const EPS = 0.001;

const playerMap = (players, getValue) =>
  Object.fromEntries(players.map((p) => [p.id, getValue(p)]));

/** True when every player took 0Q (or winner was explicitly "push"). */
export function isHolePush(hole) {
  if (!hole) return false;
  if (hole.winner === "push") return true;
  const delta = hole.points_delta;
  if (!delta || typeof delta !== "object") return false;
  const values = Object.values(delta);
  if (values.length === 0) return false;
  return values.every((v) => Math.abs(Number(v) || 0) < EPS);
}

/**
 * Starting wager + carry-over flag for the hole about to be played.
 *
 * @returns {{
 *   wager: number,
 *   carryOver: boolean,
 *   fromHole: number | null,
 *   consecutiveBlocked: boolean,
 * }}
 */
export function resolveCarryOverForHole({
  holeHistory = [],
  baseWager = 1,
  holeNumber,
}) {
  const prior = holeHistory.find((h) => h.hole === holeNumber - 1);
  if (!prior || !isHolePush(prior)) {
    return {
      wager: baseWager,
      carryOver: false,
      fromHole: null,
      consecutiveBlocked: false,
    };
  }

  const priorPrior = holeHistory.find((h) => h.hole === holeNumber - 2);
  if (priorPrior && isHolePush(priorPrior)) {
    // Second straight push: keep prior hole's start value, no new carry badge.
    return {
      wager: prior.wager ?? baseWager,
      carryOver: false,
      fromHole: null,
      consecutiveBlocked: true,
    };
  }

  return {
    wager: (prior.wager ?? baseWager) * 2,
    carryOver: true,
    fromHole: prior.hole,
    consecutiveBlocked: false,
  };
}

/**
 * Hole 18 cannot push when it opened under a carry-over (no hole 19).
 */
export function blocksHole18Push({ holeHistory, holeNumber, isPush }) {
  if (holeNumber !== 18 || !isPush) return false;
  return resolveCarryOverForHole({
    holeHistory,
    baseWager: 1,
    holeNumber: 18,
  }).carryOver;
}

/**
 * Validate entered quarters for one hole. Returns an error message, or null
 * when the hole can be submitted.
 */
export function validateHoleQuarters({ players, quarters, holeHistory, holeNumber }) {
  const isBlank = (v) => v === undefined || v === "" || v === null;
  // Flag a half-typed / malformed entry explicitly instead of silently
  // treating it as 0 and reporting a confusing "must sum to zero" error.
  const malformed = players.find(
    (p) => !isBlank(quarters[p.id]) && parseQuarter(quarters[p.id]) === null,
  );
  if (malformed) {
    return `Enter a quarters amount for ${malformed.name}, and choose Won or Lost.`;
  }
  if (players.some((p) => isBlank(quarters[p.id]))) {
    return "Please enter quarters for all players";
  }
  const delta = playerMap(players, (p) => parseQuarter(quarters[p.id]) ?? 0);
  const sum = Object.values(delta).reduce((a, b) => a + b, 0);
  if (Math.abs(sum) > EPS) {
    return `Quarters must sum to zero. Current sum: ${sum > 0 ? "+" : ""}${sum.toFixed(2)}`;
  }
  if (
    blocksHole18Push({
      holeHistory,
      holeNumber,
      isPush: isHolePush({ points_delta: delta }),
    })
  ) {
    return "Cannot push on hole 18 with a carry-over wager — someone must win this hole.";
  }
  return null;
}

/**
 * Net scores (gross − strokes received) and the best-ball suggested winner.
 * Returns empty results until every score is entered and teams are formed.
 */
export function netScoresAndWinner({
  players,
  scores,
  teamMode,
  team1,
  captain,
  opponents,
  strokeAllocation,
  holeNumber,
}) {
  const allScoresEntered = players.every(
    (p) => scores[p.id] !== undefined && scores[p.id] !== null,
  );
  const teamsFormed =
    teamMode === "partners"
      ? team1.length > 0 && team1.length < players.length
      : captain !== null;
  if (!allScoresEntered || !teamsFormed) {
    return { netScores: {}, suggestedWinner: null, team1Net: null, team2Net: null };
  }

  const netScores = playerMap(
    players,
    (p) => (scores[p.id] || 0) - (strokeAllocation?.[p.id]?.[holeNumber] || 0),
  );
  const bestBall = (ids) => {
    const nets = ids.map((id) => netScores[id]).filter((s) => s !== undefined);
    return nets.length > 0 ? Math.min(...nets) : 0;
  };

  let team1Net, team2Net;
  if (teamMode === "partners") {
    team1Net = bestBall(team1);
    team2Net = bestBall(players.filter((p) => !team1.includes(p.id)).map((p) => p.id));
  } else {
    team1Net = netScores[captain] ?? 0;
    team2Net = bestBall(opponents);
  }

  let suggestedWinner = "push"; // Tied = push
  if (team1Net < team2Net) {
    suggestedWinner = teamMode === "partners" ? "team1" : "captain";
  } else if (team2Net < team1Net) {
    suggestedWinner = teamMode === "partners" ? "team2" : "opponents";
  }
  return { netScores, suggestedWinner, team1Net, team2Net };
}

/** Rebuild standings from hole history — quarters plus usage counters. */
export function standingsFromHistory(players, history) {
  const standings = playerMap(players, (p) => ({
    quarters: 0,
    name: p.name,
    soloCount: 0,
    floatCount: 0,
    optionCount: 0,
  }));

  history.forEach((hole) => {
    const delta = hole.points_delta || {};
    Object.entries(delta).forEach(([playerId, points]) => {
      if (standings[playerId]) {
        standings[playerId].quarters += typeof points === "number" ? points : 0;
      }
    });
    if (hole.teams?.type === "solo" && hole.teams?.captain) {
      if (standings[hole.teams.captain]) {
        standings[hole.teams.captain].soloCount += 1;
      }
    }
    if (hole.float_invoked_by && standings[hole.float_invoked_by]) {
      standings[hole.float_invoked_by].floatCount += 1;
    }
    if (hole.option_invoked_by && standings[hole.option_invoked_by]) {
      standings[hole.option_invoked_by].optionCount += 1;
    }
  });

  return standings;
}
