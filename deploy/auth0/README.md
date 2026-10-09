# Auth0 config

Tenant: `dev-jm88n088hpt7oe48.us.auth0.com`. Changes here are applied by hand in the Auth0 dashboard; this folder is the source of truth for what should be there.

## Action: link accounts by email

`actions/link-accounts-by-email.js` stops one player ending up with two Auth0 accounts (e.g. email + password, then later "Continue with Google"). On a new account's **first** login it links it into the existing account with the same **verified** email and switches the session to that account, so the app keeps seeing the user id its player profile is tied to.

It does nothing for logins with no email (some Facebook accounts) — link those by hand (below). If linking fails, the login still goes through.

### Install (one time)

1. **Machine-to-machine app** — Applications → Applications → Create Application → *Machine to Machine*, name it `Account Linking Action`, authorize it for **Auth0 Management API** with scopes `read:users` and `update:users`. Note its Client ID and Client Secret.
2. **Action** — Actions → Library → Create Action → *Build from scratch*, name `Link accounts by email`, trigger **Login / Post Login**. Paste the contents of `actions/link-accounts-by-email.js`.
   - **Dependencies:** add `auth0` version `4.x`.
   - **Secrets:** `DOMAIN` = `dev-jm88n088hpt7oe48.us.auth0.com`, `CLIENT_ID`, `CLIENT_SECRET` from step 1.
   - Click **Deploy**.
3. **Flow** — Actions → Flows → Login → drag `Link accounts by email` into the flow → **Apply**.

To turn it off, remove it from the Login flow.

### Test

`node --test deploy/auth0/actions/link-accounts-by-email.test.js` runs the local checks. After installing, sign in to the app with a second method for an account that already exists (same verified email): you should land on the same player profile, and Auth0 → User Management → Users should show one user with two identities.

## Linking two existing accounts by hand

Needed when the accounts already exist (the Action only handles new ones) or a login has no email. Get a token from Applications → APIs → Auth0 Management API → API Explorer, `export AUTH0_MGMT_TOKEN=...` in your own terminal, then:

```bash
curl -sS -X POST "https://dev-jm88n088hpt7oe48.us.auth0.com/api/v2/users/<PRIMARY_USER_ID_URL_ENCODED>/identities" \
  -H "Authorization: Bearer $AUTH0_MGMT_TOKEN" -H "Content-Type: application/json" \
  -d '{"provider":"<secondary provider>","user_id":"<secondary id without the provider| prefix>"}'
```

The **primary** must be the account the player's app profile is linked to (see Admin → Account links). URL-encode the `|` in the primary id as `%7C`.
