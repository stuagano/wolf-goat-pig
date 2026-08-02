/**
 * Carry-over rules for the live quarters scorekeeper.
 *
 * Halved hole → next hole starts at 2× that hole's wager (badge shown).
 * Consecutive halves do not stack — second straight push keeps the elevated
 * wager but clears the carry-over badge (matches backend update_carry_over_state).
 */

const EPS = 0.001;

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
