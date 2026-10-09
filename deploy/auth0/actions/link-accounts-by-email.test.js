// Run: node --test deploy/auth0/actions/link-accounts-by-email.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const { pickPrimary, onExecutePostLogin } = require('./link-accounts-by-email');

const existing = { user_id: 'auth0|old', email: 'Kev@Example.com', email_verified: true, created_at: '2026-09-03T00:00:00Z' };
const fresh = {
  user_id: 'google-oauth2|new', email: 'kev@example.com', email_verified: true, created_at: '2026-10-01T00:00:00Z',
  identities: [{ provider: 'google-oauth2', user_id: 'new' }],
};

test('links a new login into the existing account with the same verified email', () => {
  assert.equal(pickPrimary(fresh, [fresh, existing]).user_id, 'auth0|old');
});

test('skips when either email is unverified', () => {
  assert.equal(pickPrimary({ ...fresh, email_verified: false }, [existing]), null);
  assert.equal(pickPrimary(fresh, [{ ...existing, email_verified: false }]), null);
});

test('skips logins without an email and when there is no other account', () => {
  assert.equal(pickPrimary({ ...fresh, email: undefined }, [existing]), null);
  assert.equal(pickPrimary(fresh, [fresh]), null);
});

test('picks the oldest when several accounts share the email', () => {
  const older = { ...existing, user_id: 'facebook|older', created_at: '2026-01-01T00:00:00Z' };
  assert.equal(pickPrimary(fresh, [existing, older, fresh]).user_id, 'facebook|older');
});

test('never folds an older account into a newer one', () => {
  // Signing in with the original account while a newer duplicate exists: no link.
  const newer = { ...fresh, created_at: '2026-11-01T00:00:00Z' };
  assert.equal(pickPrimary({ ...existing, identities: [{}] }, [existing, newer]), null);
});

test('links on a later login once a password sign-up has verified its email', () => {
  // First login (unverified) is skipped; a later, verified login links.
  assert.equal(pickPrimary({ ...fresh, email_verified: false }, [existing]), null);
  assert.equal(pickPrimary({ ...fresh, email_verified: true }, [existing]).user_id, 'auth0|old');
});

test('does nothing for unverified or already-linked users', async () => {
  let called = false;
  const api = { authentication: { setPrimaryUser: () => { called = true; } } };
  await onExecutePostLogin({ user: { ...fresh, email_verified: false }, secrets: {} }, api);
  await onExecutePostLogin({ user: { ...fresh, identities: [{}, {}] }, secrets: {} }, api);
  assert.equal(called, false);
});
