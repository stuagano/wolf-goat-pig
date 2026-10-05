// Club identity is authoritative; Auth0 may return the login email as its name.
export const playerDisplayName = (profile, user) => {
  const candidates = [profile?.legacy_name, profile?.name, user?.name];
  return candidates.find(name => typeof name === 'string' && name.trim() && !name.includes('@') && name !== 'Unknown Player')?.trim() || 'Player';
};
