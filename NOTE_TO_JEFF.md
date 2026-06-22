# Wolf Goat Pig — Ready for You to Test

**To:** Jeff Green
**From:** Stuart
**Scope:** Player sign-up, account creation, onboarding. (Scoring/wagering is out of scope for this pass.)
**Companion doc:** `CAPABILITIES_ONBOARDING.md` has the full capability breakdown — this note is the "please try it" version.

---

## The one thing to know first: your tee sheet stays the single source of truth

The new sign-up page is a **thin skin over your existing tee sheet**, not a competing system:

- It **reads live** from your sheet (`wgp_tee_sheet.cgi`) — so it shows everyone, including people who signed up on the old page.
- It **writes straight back** to your sheet (`wgp_add_tee_sheet_ajax.cgi`) — a sign-up in the new app *is* a sign-up on your sheet.
- It keeps **no second copy** of sign-up data on our side. There is nothing to reconcile and no way for the two to drift, because they're the same list.
- It signs you up under your **confirmed legacy name** (the name on your dropdown), so posts land under the right person.

So the new and old pages can run **side by side** with zero data divergence. That's the property that makes the rollout low-risk.

---

## What we'd like you to test

Pre-req: open the app and log in once (Auth0 — Google or email). A profile is created automatically.

**Sign-up round-trip (the big one)**
1. On the new page, sign up for an upcoming date. Then open your normal tee sheet and **confirm your name landed there.** *(We've already verified this live — a sign-up made through the new page is currently readable on your tee sheet — but please confirm it from your side.)*
2. Reverse it: have someone sign up on the **old page**, then refresh the new page and **confirm they show up** in the new list.
3. Cancel/remove a sign-up and confirm it disappears from the tee sheet too.

> If #1 and #2 both work, the "one source of truth" claim is proven end-to-end.

**Onboarding & identity**
4. As a **returning player**, check that the app guessed your **legacy name correctly** at first login. Try the searchable dropdown to change it. Then try **"Skip for now."**
5. As a **brand-new golfer not on your dropdown**, sign up — confirm (a) login still works, and (b) an **admin alert email** arrives so they can be added to your sheet.
6. If you have any **near-duplicate names** on the sheet (e.g. "Jon" vs "John Smith"), tell us — we want to test that the matcher doesn't link the wrong person (see Q3).

**Admin tools**
7. Visit `/admin/roster`: promote a pending new player onto the roster, dismiss a misspelling, and add a name directly.

**Emails**
8. Confirm the **welcome email** (first login) and **sign-up confirmation email** arrive.

> Email plumbing is live and verified end-to-end (sent via Resend). The three
> notifications wired today are: welcome, sign-up confirmation, and the
> **headcount/"matchmaking" callout** (emails opt-in players when a date is short
> of a full foursome). We've sent a sample callout to ourselves to confirm it
> lands.

**Known/expected for now**
- New players show a **handicap of 18.0** until GHIN sync is finished (see Q2).
- Adding a brand-new name to *your* dropdown is still **manual on your end** (see Q1).

---

## Open questions where your input changes what we build

1. **Adding a new golfer to your dropdown — automatable?** Today, when a brand-new golfer signs up, we capture them and email an admin; you then add them to your thousand-cranes dropdown by hand. **Is that dropdown-add doable via a URL/form we could call?** If yes, we'll wire the push so even that step disappears. If it's a hand-edit, our capture-and-promote flow is the clean handoff and we'll leave it there.
2. **Handicap source of truth:** GHIN sync, the legacy sheet, or manual entry — which should drive a player's handicap?
3. **Name matching (a real correctness risk):** at first login we fuzzy-match the Auth0 name to your roster. A new "Jon Smith" could get auto-linked to an existing "John Smith" and then post sign-ups under the wrong person. **How clean/distinct are the names on your sheet? Any known aliases or near-duplicates to harden against?**
4. **Bulk onboarding:** worth importing the whole roster in one pass, or is per-player self-claim enough?
5. **Write contract — confirmed, just want your eyes on it:** the new page posts to `wgp_add_tee_sheet_ajax.cgi` with `name` / `date` / `type=add`, and we've verified a sign-up lands and reads back correctly. If you ever see a sign-up *not* land (wrong field, wrong action value for cancel, etc.), tell us what the CGI actually expects and we'll adjust.

---

## Proposed sign-up migration / cutover plan

Because the new page shares your tee sheet rather than copying it, we can move in stages with an easy rollback at every step.

- **Phase 0 — Pilot (now).** Your tee sheet stays canonical and is the only store. The new page is a read/write skin over it. You and a few players try it; both pages stay live simultaneously. **Rollback = stop using the new page; nothing to undo.**
- **Phase 1 — Opt-in banner.** We add a small "🚀 Try the new sign-up experience" banner to the top of your legacy page (a snippet you or your host paste in — we can't edit the CGI from here). Players self-select in. We watch the logs and your sheet for any mismatches.
- **Phase 2 — New page becomes the default.** Once Phase 1 is clean, the primary link points at the new page; the old page stays as fallback. Still the same single tee sheet underneath.
- **Phase 3 — Retire the old UI (optional, your call).** Keep the CGI as the backing store with the new app reading/writing it, *or* migrate the store entirely — we decide this based on your answer to Q1 (programmatic dropdown-add). No rush; Phase 2 is a perfectly good resting state.

**Risks we're tracking**
- ~~The CGI write contract must be confirmed live~~ — **confirmed:** sign-ups read and write against your live sheet (Q5 / Test #1).
- New golfers still need the manual dropdown-add until Q1 is resolved.
- Name-matching correctness (Q3).
- *(Internal, not yours):* the new page is a thin client over your sheet, but our notification features (confirmation email, headcount/callout alerts) read an internal table. A sign-up through the **new page** now mirrors into that table automatically, so those features fire. The one remaining gap: a sign-up made **directly on your old page** isn't yet counted by those notifications — that needs a periodic reconcile job (planned). Until then, headcount alerts may undercount on dates where people used the old page.

---

Happy to walk any of this live, or sit with you while you run Test #1 so we confirm the round-trip together.
