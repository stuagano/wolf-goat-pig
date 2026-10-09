/**
 * Auth0 Post-Login Action: link a brand-new login to the player's existing account.
 *
 * When someone who already has an account signs in for the first time with a
 * different method (e.g. "Continue with Google" after using email + password),
 * Auth0 creates a second user. The app's player profile is tied to the FIRST
 * account's user id, so the new login would hit "This email is linked to a
 * different login". This Action folds the new account into the existing one and
 * switches the session to it, so the app always sees the original user id.
 *
 * Safety rules:
 * - Only runs on the new account's first login (it is the one being folded in).
 * - Both accounts must share the same VERIFIED email (no takeover by an
 *   unverified sign-up). Logins with no email (e.g. some Facebook accounts) are
 *   skipped and must be linked manually.
 * - If several existing accounts share the email, links into the oldest one.
 *
 * Setup: see deploy/auth0/README.md.
 *
 * Logging: console.log is the Auth0 Actions logger (shows in the Action's
 * real-time logs); this file runs in Auth0, not in the app.
 */

/** Pick the existing account to keep, or null if this login shouldn't be linked. */
function pickPrimary(user, candidates) {
  const email = (user.email || '').toLowerCase();
  if (!email || user.email_verified !== true) return null;
  const others = (candidates || []).filter(
    c => c.user_id !== user.user_id && c.email_verified === true && (c.email || '').toLowerCase() === email,
  );
  if (others.length === 0) return null;
  return [...others].sort((a, b) => String(a.created_at).localeCompare(String(b.created_at)))[0];
}

exports.onExecutePostLogin = async (event, api) => {
  const { user } = event;
  if (event.stats?.logins_count !== 1) return; // only fold in brand-new accounts
  if ((user.identities || []).length !== 1) return; // already linked

  const { ManagementClient } = require('auth0');
  const management = new ManagementClient({
    domain: event.secrets.DOMAIN,
    clientId: event.secrets.CLIENT_ID,
    clientSecret: event.secrets.CLIENT_SECRET,
  });

  let candidates;
  try {
    ({ data: candidates } = await management.usersByEmail.getByEmail({ email: user.email || '' }));
  } catch (err) {
    console.log(`account-link: lookup failed for ${user.user_id}: ${err.message}`);
    return; // never block a login because linking failed
  }

  const primary = pickPrimary(user, candidates);
  if (!primary) return;

  const [identity] = user.identities;
  try {
    await management.users.link({ id: primary.user_id }, { provider: identity.provider, user_id: identity.user_id });
  } catch (err) {
    console.log(`account-link: link ${user.user_id} -> ${primary.user_id} failed: ${err.message}`);
    return;
  }
  api.authentication.setPrimaryUser(primary.user_id);
  console.log(`account-link: linked ${user.user_id} into ${primary.user_id}`);
};

exports.pickPrimary = pickPrimary;
