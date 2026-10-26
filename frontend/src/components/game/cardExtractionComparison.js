// Compare raw quarter balances only. Scanner-derived deltas impute unread cells.
export const finite = (value) => typeof value === 'number' && Number.isFinite(value);
export const confident = (value) => finite(value) && value >= 0.85 && value <= 1;
const nameKey = (name) => typeof name === 'string' ? name.trim().replace(/\s+/g, ' ').toLocaleLowerCase() : '';

export function initialMapping(extracted, players) {
  return extracted.map((entry) => {
    const key = nameKey(entry?.name);
    const matches = players.map((p, i) => nameKey(p.name) === key ? i : -1).filter(i => i >= 0);
    return key && confident(entry?.confidence) && matches.length === 1 && extracted.filter(p => nameKey(p?.name) === key).length === 1
      ? String(matches[0]) : '';
  });
}

export function savedBalances(holeHistory, playerId) {
  let total = 0;
  return Array.from({ length: 18 }, (_, i) => {
    const entries = holeHistory.filter(h => h?.hole === i + 1);
    const value = entries.length === 1 ? entries[0].points_delta?.[playerId] : undefined;
    total = finite(total) && finite(value) ? total + value : null;
    return total;
  });
}

export function comparisonRows(totals, playerIndex, balances) {
  return balances.map((saved, i) => {
    const entries = totals.filter(t => t?.player_index === playerIndex && t?.hole === i + 1);
    const entry = entries.length === 1 ? entries[0] : null;
    const value = entry?.value;
    const extracted = finite(value) ? value : null;
    const uncertain = !confident(entry?.confidence);
    let status;
    if (entries.length > 1) status = 'Ambiguous extraction';
    else if (!finite(value)) status = 'Missing extraction';
    else if (!finite(saved)) status = 'Saved quarters unavailable';
    else if (Math.abs(saved - value) > 1e-9) status = 'Possible extraction error';
    else status = uncertain ? 'Equal · uncertain extraction' : 'Match';
    return { hole: i + 1, saved, extracted, status, uncertain };
  });
}
