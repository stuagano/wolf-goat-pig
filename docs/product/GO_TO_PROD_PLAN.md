# Go-to-Prod Plan — Club Loop First

**Status:** Active  
**Last updated:** 2026-07-24  
**Scope:** Make the real club product safe on today’s stack, then move hosting.  
**Out of scope for “prod club loop”:** in-game WGP engine / quarters-only playground.

---

## 1. What “prod” means here

The production product is the **club loop**:

```
Sign up for a day  →  Post / attest a score  →  See standings (leaderboard)
```

Everything else (shot-by-shot engine, Monte Carlo, Stuart Mode, etc.) is a **playground**. It can stay, but it must not block or corrupt the club loop.

Platform move (Vercel → Firebase Hosting, Render → Cloud Run + Cloud SQL) is documented in [`FIREBASE_MIGRATION_DESIGN.md`](../architecture/FIREBASE_MIGRATION_DESIGN.md). **Do not start the platform move until the club loop P0s below are green.**

---

## 2. P0 incident — Signup as the wrong person

### Observed (2026-07-24)

- Logged in as **Stuart Gano** (Auth0 UI / nav).
- Daily Sign-ups for **Fri Jul 24** shows **Steve Sutorius (you)**.
- UI offers **Cancel My Signup** / **Replicate to Legacy** as if that row is Stuart’s.

### What that means technically

After the `player_profile_id: 1` fix, “(you)” is matched by:

`signup.player_profile_id === profile.id` (from `GET /players/me`).

So Stuart’s **PlayerProfile.id** matches the Steve row’s `player_profile_id`, and the row’s `player_name` is **Steve Sutorius**.

Most likely causes (in order):

1. **Stuart’s `PlayerProfile.legacy_name` is wrongly set to `Steve Sutorius`**  
   Signup posts `profile.legacy_name || profile.name`. Confirm UI shows that name. Bad onboarding / admin link / fuzzy match residue.
2. **`POST /signups` still trusts the client** — no Auth0 dependency; body can supply any `player_profile_id` + `player_name`. Identity must be server-derived from the JWT.
3. **Stale row from the old hardcoded-id bug** — less likely for “(you)” unless Stuart’s profile id equals that row’s id (e.g. profile id `1` and Steve’s name stuck on the row).

### Immediate remediation checklist

- [ ] Inspect Stuart’s `/players/me` in prod: `id`, `name`, `email`, `legacy_name`.
- [ ] Inspect `daily_signups` for `2026-07-24`: `id`, `player_profile_id`, `player_name`, `status`.
- [ ] If `legacy_name` is Steve → fix to `Stuart Gano` (or correct canonical) via Account / admin; cancel bad signup; re-sign.
- [ ] If profile ids collide / wrong email link → unlink/relink Auth0 → correct `PlayerProfile`.
- [ ] Data cleanup: cancel or re-attribute any Jul 24 (and nearby) rows created under wrong identity.

### Code fixes (required before calling signup “prod ready”)

| # | Fix | Why |
|---|-----|-----|
| S1 ✅ | **`POST /signups` requires `get_current_user`**; ignore client `player_profile_id` / use server profile id + `legacy_name` | Stops client spoofing / wrong body |
| S2 ✅ | **Confirm step shows the exact name** that will be posted (`Signing up as: {legacy_name}`) | Catches wrong `legacy_name` before write |
| S3 ✅ | **Refuse signup if `legacy_name` missing** (force Account linking) for club loop | Prevents Auth0 display-name-only rows |
| S4 ✅ | CTK `signup-server-owns-identity` proves server auth identity | Same class of bug as hardcoded id=1 |
| S5 ⚠️ | `SignupCalendar.jsx` is unmounted/dead but still contains hardcoded identity if revived | Delete or modernize before reuse |

---

## 3. Club-loop readiness matrix

| Path | Today | Prod gate before platform move |
|------|--------|--------------------------------|
| **Signup** | Create is authenticated and server-owned; linked club name is required; CGI tee-sheet dual path remains | Finish S5; decide canonical UI (Daily DB vs WGP CGI) |
| **Post / attest score** | `member_rounds` → `legacy_rounds` (pending → attested) | Add CTK capability for post+attest; sheet sync optional, not SoT |
| **Leaderboard / Standings** | UI uses **`GET /data/leaderboard`** (unified), not `/leaderboard` | Retarget CTK (`leaderboard-from-db` is misaimed); env-ify sheet IDs; Render cron → portable trigger |
| **Playground engine** | Quarters-only / `games_*` | Leave alone; optionally stop merging `GameRecord` into club standings |

---

## 4. Workstreams (ordered)

### Stream A — Signup identity (this week)

1. Diagnose Stuart/Steve row + profile (ops).
2. Ship S1–S3 (auth on create, server identity, confirm name).
3. CTK S4; clean S5.
4. Smoke: login as Stuart → signup → only Stuart appears as “(you)”.

### Stream B — Score post / attest

1. Add CTK: member posts round → pending → peer attest → appears in standings-eligible reads.
2. Document: Jeff sheet is sync/mirror, DB attested rounds are club truth for app standings.

### Stream C — Leaderboard truth

1. Point CTK at `/data/leaderboard` / `unified_data_service`.
2. Env-ify hardcoded sheet / quota project IDs.
3. Replace Render-hardcoded sheet sync cron with env-based URL (works on Cloud Run later).

### Stream D — Platform move (only after A–C)

Follow `FIREBASE_MIGRATION_DESIGN.md`:

0. De-socket / stateless (if not already).  
1. Cloud Run + existing DB.  
2. Cloud SQL cutover.  
3. Firebase Hosting + `/api/**` rewrite.  
4. Cloud Scheduler for jobs.

**Auth0 stays.**

---

## 5. Definition of done — club loop on current stack

Before any hosting cutover, all of these are true:

- [ ] Logged-in user cannot appear as another player on Daily Sign-ups.
- [ ] `POST /signups` is authenticated and uses server-side profile only.
- [ ] Confirm UI shows the name that will be written.
- [ ] Member post + attest has a green CTK capability.
- [ ] Standings CTK proves `/data/leaderboard` (or equivalent unified path).
- [ ] No Render-only hardcoded URLs left in the club-loop critical path (or they’re env-driven).
- [ ] Playground engine changes are not required for the above.

---

## 6. Explicit non-goals (for this plan)

- Rewriting the WGP rules engine / quarters-only scorekeeper for migration.
- Moving Auth0 → Firebase Auth.
- Making CGI thousand-cranes the system of record (mirror only, if kept).
- Big-bang Firestore rewrite of relational data.

---

## 7. Open questions

1. Is **Daily Sign-ups (DB)** the only club signup UI for prod, with WGP Tee Sheet deprecated/hidden?
2. Should standings include completed in-app `GameRecord` results, or **only** attested `legacy_rounds` (+ optional sheet cache)?
3. Who owns correcting wrong `legacy_name` links in prod (self-serve Account vs admin)?
