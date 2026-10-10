export function roundPath({ date, group, location }) {
  const params = new URLSearchParams();
  if (location) params.set('location', location);
  const query = params.toString();
  return `/rounds/${encodeURIComponent(date)}/${encodeURIComponent(group || '')}${query ? `?${query}` : ''}`;
}
