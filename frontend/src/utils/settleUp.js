// League convention; change here if the stake changes.
export const DOLLARS_PER_QUARTER = 0.25;

// Quarters can be fractional (0.5); work in whole hundredths so sums are exact.
const SCALE = 100;

/**
 * Fewest payments that settle one round: the biggest loser pays the biggest
 * winner first. Returns { balanced: false } when any total is missing or the
 * quarters don't sum to zero — settling from a wrong card is worse than not.
 *
 * @param {{ id: string, name?: string, profile_id?: number|null, quarters: number|null }[]} players
 * @returns {{ balanced: boolean, payments: { from: object, to: object, quarters: number, dollars: number }[] }}
 */
export function settleUp(players, dollarsPerQuarter = DOLLARS_PER_QUARTER) {
  if (!players.length || players.some(p => !Number.isFinite(p.quarters))) return { balanced: false, payments: [] };
  const units = players.map(p => ({ player: p, left: Math.round(p.quarters * SCALE) }));
  if (units.reduce((sum, u) => sum + u.left, 0) !== 0) return { balanced: false, payments: [] };

  const payers = units.filter(u => u.left < 0).sort((a, b) => a.left - b.left);
  const payees = units.filter(u => u.left > 0).sort((a, b) => b.left - a.left);
  const payments = [];
  let i = 0;
  let j = 0;
  while (i < payers.length && j < payees.length) {
    const amount = Math.min(-payers[i].left, payees[j].left);
    payments.push({
      from: payers[i].player,
      to: payees[j].player,
      quarters: amount / SCALE,
      dollars: Math.round((amount / SCALE) * dollarsPerQuarter * 100) / 100,
    });
    payers[i].left += amount;
    payees[j].left -= amount;
    if (payers[i].left === 0) i += 1;
    if (payees[j].left === 0) j += 1;
  }
  return { balanced: true, payments };
}

/** Venmo's pay link: opens the app (or web) with recipient, amount and note filled in. */
export function venmoPayUrl(handle, dollars, note) {
  const params = new URLSearchParams({
    txn: 'pay',
    recipients: handle.replace(/^@/, ''),
    amount: dollars.toFixed(2),
    note,
  });
  return `https://venmo.com/?${params}`;
}
