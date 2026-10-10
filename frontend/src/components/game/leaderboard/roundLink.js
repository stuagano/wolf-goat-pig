export function roundPath({ date, date_sortable, group, location }) {
  const params = new URLSearchParams();
  if (location) params.set('location', location);
  const query = params.toString();
  // Sheet dates look like "6-Oct". The round page looks up YYYY-MM-DD.
  const key = date_sortable || date;
  return `/rounds/${encodeURIComponent(key)}/${encodeURIComponent(group || '')}${query ? `?${query}` : ''}`;
}
