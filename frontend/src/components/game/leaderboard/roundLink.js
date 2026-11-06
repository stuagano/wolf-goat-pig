// Only the backend's saved-game identity may select a scorecard. Never infer
// one from dates, groups, sheet row IDs, or local-storage keys.
export function scorecardPath({ game_id } = {}) {
  return typeof game_id === 'string' && game_id.trim()
    ? `/game/${encodeURIComponent(game_id)}`
    : null;
}

export function roundPath({ game_id, date, date_sortable, group, location }) {
  const resolved = scorecardPath({ game_id });
  if (resolved) return resolved;
  const params = new URLSearchParams();
  if (location) params.set('location', location);
  const query = params.toString();
  // Sheet dates look like "6-Oct". The round page looks up YYYY-MM-DD.
  const key = date_sortable || date;
  return `/rounds/${encodeURIComponent(key)}/${encodeURIComponent(group || '')}${query ? `?${query}` : ''}`;
}
