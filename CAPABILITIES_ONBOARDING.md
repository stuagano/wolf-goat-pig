# Wolf Goat Pig — Player Sign-Up & Onboarding Capabilities

**Prepared for:** Jeff Green
**Scope:** Player sign-up, account creation, and onboarding only. Game scoring/wagering mechanics are intentionally out of scope for this review.
**Status legend:** ✅ Live · ⚠️ Partial · ❌ Not built yet
**As of:** June 2026

---

## 1. How it works today (the happy path)

A player never fills out our own registration form. The flow is identity-first, and it
works for **both** returning players and brand-new golfers:

1. **Player visits the app and signs up / logs in via Auth0** (hosted login — Google or
   email, no password for us to manage). The same Auth0 screen has a **Sign Up** tab for
   first-timers and a **Log In** tab for returners. Auth0 returns name, email, and avatar.
2. **The backend auto-creates a player profile** on that first login — there is no
   separate form for us to maintain. Name, email, and avatar come straight from Auth0;
   handicap defaults to 18.0; email notification preferences are created with sane
   defaults. This happens for everyone, whether or not they exist on the legacy sheet.
3. **The app attempts to fuzzy-match the player to a name on the legacy tee sheet**
   (your system). If it finds a likely match, it pre-fills it.
4. **One optional onboarding step:** a modal asks the player to confirm/select their
   **legacy name** from a searchable dropdown of known tee-sheet players — this links
   the new account to their existing history on your system. A brand-new golfer with no
   match simply taps **"Skip for now"** and continues; they're fully functional without it.
   Behind the scenes, a golfer with no match is **captured and an admin is emailed** so
   they can be added to your tee sheet (see §2 and §5).
5. Player is in. From there, sign-ups for specific play dates flow back to the legacy
   tee sheet.

```
Visit app → Auth0 sign-up OR log in → profile auto-created (everyone)
   → fuzzy-match legacy name → confirm/select OR skip (optional) → done
   → daily sign-ups sync to legacy sheet
```

The design intent: **creating an account always works** — anyone can self-sign-up
through Auth0. The legacy-sheet link is an *optional enrichment* that ties a new account
to a returning player's history; it is not a prerequisite for using the app.

---

## 2. What's live today ✅

| Capability | What it does |
|---|---|
| **Auth0 sign-up & sign-in** | Self-service account creation (Sign Up tab) and login on the same hosted screen; token refresh; no passwords stored by us. |
| **Auto-create profile on account creation** | Name/email/avatar pulled from Auth0; profile is created for any new account, legacy match or not — no manual data entry to get started. |
| **Canonical roster (DB-backed, auto-updating)** | The set of valid player names — your tee-sheet dropdown — lives in the database (seeded from your roster) and **auto-reconciles every 2 hours** against players seen in round history, so it stays current instead of being a frozen file. Additive only (never deletes). |
| **New-player capture + admin alert** | When a brand-new golfer signs up with no match on your roster, they're **captured into a pending queue** and admins get an **email alert** to add them to your tee sheet. Login is never blocked by this. |
| **Admin roster management (API)** | Endpoints to add a name to the canonical roster, list pending new players, and **promote** one onto the roster (or dismiss a misspelling) once they're on your sheet. |
| **Admin roster management (UI)** | Organizer-facing screen at `/admin/roster` (linked from the Admin dashboard): lists pending sign-ups with Promote/Dismiss actions, plus a form to add a name directly to the canonical roster. |
| **Direct profile-create API** | A `POST /players` endpoint exists for programmatic/admin profile creation. |
| **Legacy-name fuzzy matching** | On first login, the app guesses the player's legacy tee-sheet name and suggests it. |
| **Onboarding modal (legacy-name link)** | One searchable step to confirm/select the legacy identity; "skip for now" supported. |
| **Daily sign-up → legacy sheet sync** | When a player signs up / changes / cancels for a date, it replicates to the legacy tee sheet. |
| **Sign-up confirmation email** | Player gets an email when they sign up for a date (via Resend/SMTP). |
| **Match & pairing notifications** | Availability-match and pairing emails are wired up. |
| **Profile self-service fields** | Players can set Venmo handle and a short bio/description after onboarding. |
| **ForeTees credentials (self-service, encrypted)** | Players set their own ForeTees username/password on the Account page. The app **verifies the login against ForeTees before saving**, stores the password Fernet-encrypted (per-user, in `player_profiles`), shows a configured/masked status, and supports removal. Used for that player's tee-time booking. |
| **GroupMe read/post** | Reads league GroupMe; can post pairing announcements (not used for sign-up). |

---

## 3. What's partial ⚠️

| Capability | State today | Gap |
|---|---|---|
| **GHIN / handicap integration** | Data model and a GHIN API service exist; profile has a `ghin_id` field. | The actual GHIN lookup/sync is a stub — endpoints are scaffolded but not fully wired. Handicap defaults to 18.0 until then. |

---

## 4. What's not built yet ❌

These are the onboarding gaps most relevant to you. Listing them plainly so we can
decide together what matters:

1. **No automated push of a new golfer onto *your* tee sheet.** The app now captures a
   brand-new golfer and alerts an admin (see §2), but actually adding them to your
   dropdown on thousand-cranes.com is still a **manual step on your side**. We chose this
   deliberately — see §5 and question 1.
2. **No handicap capture during sign-up.** There's no onboarding step that asks for or
   verifies a GHIN ID / handicap. New players sit at the 18.0 default until handicap
   sync is finished.
3. **No welcome / onboarding email.** Players get sign-up and match emails, but nothing
   on account creation — no "welcome to WGP, here's how it works" message.
4. **No magic-link / passwordless email sign-up.** Auth0 redirect is the only entry
   (note: Auth0 itself can be configured for passwordless if we want it).

---

## 5. Where this touches your legacy system

**Your tee sheet is canonical.** The app does not keep a competing roster of who's a
"real" WGP player — it treats your tee sheet as the single source of truth for player
identity and seeds from it. The app sits **on top of** your system, not beside it:

- **The tee sheet seeds the roster, and the roster now auto-updates.** The list of league
  players the app knows about started as a snapshot of your dropdown, and is now kept
  current automatically: the same 2-hourly sync that pulls round history also reconciles
  the canonical roster, adding any player who appears in recent rounds. So a golfer you
  added to the sheet who has since played shows up in the app without anyone touching a
  file. (This is *additive* — names are never removed, so a player who stops playing
  doesn't vanish.) Onboarding's job is matching a person's Auth0 login to their canonical
  name — that match is what makes them a recognized player.
- **Two distinct layers.** Auth0 handles *login* (anyone can authenticate); your tee
  sheet defines *who's a player*. A login with no matching canonical name is just an
  unseeded account — not a new roster entry to reconcile.
- **Your spreadsheet's round history is fully mirrored into our database.** A background
  job pulls the complete round history from the Google Sheet into our `LegacyRound`
  table **every 2 hours** (plus on startup, plus an on-demand admin trigger). That DB
  copy is what the app reads for leaderboards and history — so the app stays fast and
  keeps working even if the sheet is briefly unreachable, while your sheet remains the
  upstream source. (Note: the "copy" is the continuously-refreshed table, not a frozen
  CSV dump.)
- **Sign-ups and completed games replicate back to the tee sheet.** Create/update/cancel
  a date sign-up → it syncs to your system; completed app games queue and write back to
  the writable sheet nightly (with dedup), so the canonical sheet stays authoritative.
- **New golfers are captured, never silently promoted.** When someone signs up who isn't
  on your roster, the app queues them and emails an admin — but it does **not** invent
  them as a canonical player, because a name that isn't on your dropdown would just make
  their sign-ups fail at your CGI. They become canonical one of two ways: an admin
  *promotes* the queued entry, **or** the auto-sync above resolves it automatically once
  that golfer turns up in round history. The only manual step is adding them to your
  dropdown so they can actually sign up there.
- **One honest residual gap:** the auto-sync learns players from *round history*, so a
  golfer you add to the dropdown who hasn't played a round yet won't be auto-added — if
  they sign up in the app first, they'll be captured (and an admin can promote them).
  True real-time lockstep with the dropdown itself would require reading your CGI's
  player list directly, which is question 1 territory.
- **Why we didn't auto-write to your sheet:** your tee-sheet CGI accepts sign-ups only
  for names already in its dropdown, and we don't have a documented way to add a *new*
  name to it programmatically. Rather than guess at that and risk silent failures, we
  kept the dropdown-add on your side — see question 1.

---

## 6. Questions for you, Jeff

Where your input would most change priorities:

1. **New golfers — the one piece still on your side:** the app now captures a brand-new
   golfer and emails an admin to add them to your tee sheet; an admin then promotes them
   to canonical. Adding the name to your thousand-cranes.com dropdown is still manual.
   **Is that dropdown-add something that can be done via a URL/form we could automate, or
   is it a hand-edit on your end?** If the former, tell us the mechanism and we'll wire
   the push so even that step disappears. If the latter, the capture-and-promote flow we
   built is the clean handoff.
2. **Handicap source of truth:** GHIN sync, the legacy sheet, or manual entry — which
   should drive a player's handicap?
3. **Name matching (a real correctness risk worth your eyes):** at first login we
   fuzzy-match the player's Auth0 name to your roster. If a *new* golfer's name is close
   to an existing player's (e.g. "Jon Smith" vs "John Smith"), today the app may
   auto-link them to that other person's legacy identity — and their date sign-ups would
   then post under the wrong name. How clean/distinct are the names on your sheet? Any
   known near-duplicates or aliases we should harden the matching against?
4. **Bulk onboarding:** is there value in importing the full roster from a sheet in one
   pass, or is per-player self-claim sufficient?

---

*All capabilities above are traceable to the current codebase (Auth0 auth service,
player/sign-up routers, GHIN service, email/Resend provider, and the React onboarding
components). Happy to walk through any of it live.*
