// Fake Auth0 cache for LOCAL fixture tests only. No real credentials.
if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
  const clientId = 'test-e2e-client-id';
  const scope = 'openid profile email offline_access';
  const expiresAt = Math.floor(Date.now() / 1000) + 86400;
  const user = { sub: 'auth0|123456789', email: 'test@example.com', name: 'Test User' };
  localStorage.setItem(`@@auth0spajs@@::${clientId}::default::${scope}`, JSON.stringify({
    body: { access_token: 'e2e-fixture', token_type: 'Bearer', expires_in: 86400, scope, audience: 'default', client_id: clientId }, expiresAt,
  }));
  localStorage.setItem(`@@auth0spajs@@::${clientId}::@@user@@`, JSON.stringify({
    id_token: 'e2e-fixture', decodedToken: { claims: { ...user, __raw: 'e2e-fixture', exp: expiresAt }, user },
  }));
}
