export const BANQUET_QUALIFICATION_ROUNDS = 20;

export const SORT_COLUMNS = [
  { key: 'rank', label: 'Rank' },
  { key: 'member', label: 'Player' },
  { key: 'quarters', label: 'Quarters' },
  { key: 'rounds', label: 'Rounds' },
  { key: 'average', label: 'Avg / Round' },
];

export function compareStandings(a, b, sortKey) {
  if (sortKey === 'member') {
    return (a.member || '').localeCompare(b.member || '', undefined, { sensitivity: 'base' });
  }
  const av = Number(a[sortKey] ?? 0);
  const bv = Number(b[sortKey] ?? 0);
  return av - bv;
}

/** Default is rank ascending. Missing ranks sort after stored ranks. */
export function sortStandings(entries, sortKey, sortDir) {
  const dir = sortDir === 'desc' ? -1 : 1;
  return [...entries].sort((a, b) => {
    if (sortKey === 'rank') {
      const ar = a.rank == null ? Number.POSITIVE_INFINITY : a.rank;
      const br = b.rank == null ? Number.POSITIVE_INFINITY : b.rank;
      return (ar - br) * dir;
    }
    return compareStandings(a, b, sortKey) * dir;
  });
}

export function banquetEligible(entry) {
  return (entry.rounds || 0) >= BANQUET_QUALIFICATION_ROUNDS;
}
