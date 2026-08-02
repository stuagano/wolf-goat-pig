/**
 * Hitting-order nudge helper — same swap SimpleScorekeeper uses before
 * applyHittingOrder persists tee_order and resets captain/teams.
 */
export function nudgeHittingOrder(order, fromIndex, direction) {
  const toIndex = fromIndex + direction;
  if (toIndex < 0 || toIndex >= order.length) return order;
  const next = [...order];
  [next[fromIndex], next[toIndex]] = [next[toIndex], next[fromIndex]];
  return next;
}
