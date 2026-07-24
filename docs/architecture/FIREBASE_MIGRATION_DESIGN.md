# Firebase Migration Design

## Document Information
- **Project**: Wolf Goat Pig — Golf Wagering App
- **Status**: 🚧 Draft / Request for Comment
- **Author**: Engineering
- **Last Updated**: 2026-07-24

> This is a **starting-point design doc**. It frames the decision space, proposes a
> recommended path, and flags the hard problems. It is not a committed plan — the
> open questions in [§11](#11-open-questions) need answers before any migration
> ticket is cut.

### Decisions Log

| # | Decision | Status |
|---|----------|--------|
| D1 | **Database:** Cloud SQL for PostgreSQL — relational schema moves unchanged; Firestore-as-source-of-truth is out of scope ([§4](#4-the-central-decision-database)). | ✅ Decided |
| D2 | **Backend compute:** FastAPI container on Cloud Run (not Cloud Functions) ([§5](#5-target-architecture-recommended)). | ✅ Decided |
| D3 | **Frontend hosting:** Firebase Hosting, with an `/api/**` rewrite to Cloud Run for same-origin (no CORS). "Serve from Cloud Run" documented as the simpler alternative ([§6](#6-component-by-component-mapping)). | ✅ Decided |
| D4 | **Auth:** **Auth0 stays.** The Firebase Auth switch is decoupled from this migration and deferred indefinitely — not on the critical path ([§7](#7-authentication-migration)). | ✅ Decided |
| D5 | **DB-on-Render:** acceptable as the Phase-1 *interim* state; not the steady-state target (cross-cloud latency/egress) ([§4](#4-the-central-decision-database)). | ✅ Decided |
| D6 | **DB compute cost:** accept Cloud SQL's always-on floor (small instance, ~$10/mo). Scale-to-zero alternatives (AlloyDB — pricier; Neon — +vendor, compounding cold starts) rejected ([§10](#10-cost-considerations)). | ✅ Decided |

---

## Table of Contents
1. [Motivation & Goals](#1-motivation--goals)
2. [Current Architecture (What We're Migrating)](#2-current-architecture-what-were-migrating)
3. [What "Firebase" Actually Means Here](#3-what-firebase-actually-means-here)
4. [The Central Decision: Database](#4-the-central-decision-database)
5. [Target Architecture (Recommended)](#5-target-architecture-recommended)
6. [Component-by-Component Mapping](#6-component-by-component-mapping)
7. [Authentication Migration](#7-authentication-migration)
8. [Data Migration Strategy](#8-data-migration-strategy)
9. [Phased Rollout Plan](#9-phased-rollout-plan)
10. [Cost Considerations](#10-cost-considerations)
11. [Open Questions](#11-open-questions)
12. [Risks & Non-Goals](#12-risks--non-goals)

---

## 1. Motivation & Goals

**Why consider Firebase / Google Cloud?**

- **Consolidate the deployment surface.** Today the app spans three vendors:
  Vercel (frontend), Render (backend + Postgres), and Auth0 (identity). Moving
  hosting, compute, database, secrets, logging, and scheduling into a single
  Google Cloud project collapses that to essentially one platform. (**Auth0
  stays** — see D4/§7 — so identity remains a separate provider by choice, kept
  off the critical path.)
- **First-class real-time & offline.** The app already has WebSocket game
  broadcasts and a service-worker offline layer. Firestore's realtime listeners
  and offline persistence are a native fit for both.
- **Managed scaling.** Render's free/low tiers cap the Postgres connection pool
  (see `backend/app/database.py`: `pool_size=5`). Cloud-native services scale
  without hand-tuned pools.

**Goals**

1. No regression in features, latency, or data integrity.
2. Preserve the FastAPI domain/engine logic — the WGP rules engine is the crown
   jewels and must not be rewritten to chase a platform.
3. A **reversible, incremental** path — no big-bang cutover.

**Explicit non-goal:** rewriting the game engine, scoring, or betting logic. This
migration is about *platform*, not *product*.

---

## 2. Current Architecture (What We're Migrating)

| Layer | Today | Notes |
|-------|-------|-------|
| Frontend | React 19 + Vite, React Router 7, `@auth0/auth0-react` | Deployed on Vercel. Service worker + offline storage (`src/services/offlineStorage.jsx`, `syncManager.jsx`). |
| Auth | Auth0 (RS256 JWT) | Verified in `backend/app/services/auth_service.py`; linked to `PlayerProfile`. |
| Backend | FastAPI monolith | **33 routers**, **~40 services**. Deployed on Render via `render.yaml`. |
| Database | PostgreSQL (SQLAlchemy 2.0) | **~40 tables** (`backend/app/models.py`, 825 lines). Relational: joins, aggregations for stats/leaderboards. |
| Real-time | WebSockets | `ws/{game_id}` game broadcasts + `ws/user/{player_id}` notifications (`websocket_routes.py`). |
| Background jobs | In-process schedulers | Email, pairing, matchmaking, callouts, sheet-sync (`services/*_scheduler.py`, `schedule` lib). |
| Heavy compute | OpenCV + Pillow | Scorecard photo scan/OCR preprocessing (`scorecard_scan_service.py`). |
| External integrations | GHIN, GroupMe, ForeTees, Resend (email), Google Sheets, Sentry | Multiple `services/*_service.py`. |

**Data model shape matters.** The schema is deeply *relational*: `game_state` →
`game_players` → `hole_events`; `player_profiles` → `player_statistics` →
`game_player_results`; plus badges, series progress, GHIN history, matchmaking,
LivSow rosters/transactions. Leaderboards and statistics are **aggregation
queries across joins** — the single most important constraint on the target DB.

---

## 3. What "Firebase" Actually Means Here

"Firebase" is a product family inside Google Cloud. A realistic migration uses
some Firebase-branded products and some Google Cloud products. The relevant menu:

| Need | Firebase-branded | Google Cloud equivalent |
|------|------------------|-------------------------|
| Static hosting | Firebase Hosting | Cloud CDN + Cloud Storage |
| Auth | Firebase Authentication | Identity Platform (same engine, enterprise tier) |
| Document DB | Cloud Firestore | — |
| Relational DB | — | Cloud SQL (Postgres) |
| Serverless functions | Cloud Functions for Firebase | Cloud Run / Cloud Functions (2nd gen) |
| Container compute | — | **Cloud Run** |
| Object storage | Firebase Storage | Cloud Storage (same buckets) |
| Scheduling | — | Cloud Scheduler + Cloud Tasks |
| Secrets | — | Secret Manager |
| Push/messaging | Firebase Cloud Messaging (FCM) | Pub/Sub |

**Key insight:** a pure "Firebase" (Firestore + Cloud Functions) stack would
require a near-total backend rewrite — abandoning FastAPI, SQLAlchemy, the
synchronous rules engine, and the OpenCV pipeline. That is not viable as a first
step. The pragmatic target is **Firebase for the edges (Auth, Hosting, realtime,
storage, messaging) + Cloud Run for the FastAPI core**.

---

## 4. The Central Decision: Database

Everything else is comparatively mechanical. The database is the fork in the road.

> **✅ Decided: Cloud SQL for PostgreSQL (Option A).** The schema is deliberately
> relational — ~40 normalized tables, foreign-key integrity, and leaderboard/stat
> queries built on joins and `GROUP BY`. That is a *good* design for this app; it
> is simply not a document design. Firestore has no joins and no cross-collection
> aggregation, so making it the system of record would mean denormalizing
> everything, hand-maintaining rollup counters, and enforcing integrity in
> application code — a large rewrite with real regression risk and no product
> upside. Cloud SQL *is* Postgres, so the schema, `models.py`, the ORM queries,
> and the rules engine all move **unchanged**. Firestore may still be adopted
> later as a *derived* realtime read model (Option C), never as the source of
> truth for relational data.

### Option A — Cloud SQL for PostgreSQL (lift-and-shift) ✅ Recommended
Keep SQLAlchemy, keep the schema, keep every aggregation query. Point
`DATABASE_URL` at a Cloud SQL instance via the Cloud SQL Auth Proxy / connector.

- **Pros:** near-zero code change; relational joins & leaderboard aggregations
  keep working; `pg_dump`/`pg_restore` migration; reversible.
- **Cons:** not "serverless" in the Firestore sense; still a connection-pool to
  manage; you pay for an always-on instance (or use Cloud SQL's autoscaling).

### Option B — Firestore (full NoSQL rewrite)
Re-model ~40 relational tables as document collections.

- **Pros:** realtime listeners replace WebSockets for free; offline SDK replaces
  the hand-rolled service-worker sync; true pay-per-use; auto-scaling.
- **Cons:** **enormous rewrite risk.** Leaderboards/statistics are cross-entity
  aggregations — Firestore has no joins and no `GROUP BY`; you'd maintain
  denormalized rollups and counters, and every stat becomes eventually-consistent
  write-fan-out. The rules engine and every service/router touching the ORM would
  be rewritten. High chance of subtle scoring/stat regressions.

### Option C — Hybrid (recommended *eventual* state)
Cloud SQL stays the system of record for relational/transactional data (games,
scores, stats). Firestore is added **selectively** for what it's genuinely best
at: live game state fan-out and notification feeds, written by the backend and
read directly by clients via realtime listeners.

### Decision
**Option A (Cloud SQL) is the chosen path for the cutover** — it de-risks the
platform move and keeps the relational schema intact. **Option C** may be adopted
later, opportunistically, where realtime/offline UX benefits justify it.
**Option B (full Firestore) is explicitly out of scope** unless a later, separate
decision revisits it.

### Interim: keeping Postgres on Render (accepted for Phase 1)
During the migration, the FastAPI app runs on Cloud Run while still pointing at
the **existing Render Postgres** (just `DATABASE_URL`). This is a deliberate,
reversible stepping stone — it lets compute be validated before the data moves,
and rollback is a one-line env flip. It is **not** the steady state: Cloud Run →
Render is a cross-cloud hop that adds per-query latency (~10–50 ms vs. sub-ms
in-region), incurs GCP egress billing, requires exposing Postgres publicly, and
leaves Render's `pool_size=5` cap in place. Render Postgres is a fine *stepping
stone*, a poor *destination* — Phase 2 moves the data to Cloud SQL.

---

## 5. Target Architecture (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                     Google Cloud Project                     │
│                                                              │
│  Firebase Hosting ──► React SPA (built by Vite)             │
│        │                                                     │
│        │  Firebase Auth (ID token)                           │
│        ▼                                                     │
│  Cloud Run  ◄────────  FastAPI monolith (container as-is)    │
│     │  │  │            - verifies Firebase ID tokens         │
│     │  │  │            - rules engine, routers, services     │
│     │  │  │            - OpenCV scorecard pipeline           │
│     │  │  └──► Cloud SQL (PostgreSQL)  ◄── system of record  │
│     │  └─────► Cloud Storage (scorecard images, media)       │
│     └────────► Firestore (live game state, notif feeds) [C]  │
│                                                              │
│  Cloud Scheduler ──► Cloud Run jobs (email, pairing, sync)   │
│  Secret Manager ──► DATABASE_URL, API keys, GHIN creds       │
│  Cloud Logging / Monitoring  +  Sentry (unchanged)           │
└─────────────────────────────────────────────────────────────┘
```

**Why Cloud Run for the backend (not Cloud Functions):**
- The FastAPI app is a large stateful-ish monolith with WebSocket endpoints and
  heavy native deps (`opencv-python-headless`, `numpy`, `Pillow`). It already
  ships a `Dockerfile` — Cloud Run runs that container unchanged.
- Cloud Functions caps request duration, package size, and lacks first-class
  WebSocket support. Cloud Run supports WebSockets and long-lived connections.

---

## 6. Component-by-Component Mapping

| Current | Target | Migration effort |
|---------|--------|------------------|
| Vercel static hosting | Firebase Hosting | **Low** — `vite build` → `firebase deploy`. Translate `vercel.json` routing into `firebase.json` rewrites. |
| Auth0 (`@auth0/auth0-react`) | **Unchanged — Auth0 stays** | **None** for this migration — see [§7](#7-authentication-migration). |
| FastAPI on Render | FastAPI on Cloud Run | **Low–Medium** — reuse `backend/Dockerfile`; swap Render env wiring for Cloud Run + Secret Manager; add Cloud SQL connector. |
| PostgreSQL on Render | Cloud SQL Postgres | **Low** — `pg_dump`/restore; change `DATABASE_URL`. Code path in `database.py` already branches on `postgresql://`. |
| WebSocket game broadcasts | Cloud Run WebSockets (Option A) **or** Firestore listeners (Option C) | **Low** (A) / **Medium** (C). |
| In-process `schedule` jobs | Cloud Scheduler → Cloud Run endpoints/jobs | **Medium** — extract scheduler triggers into HTTP-invoked jobs so they don't rely on a long-lived process. |
| Scorecard OCR (OpenCV) | Cloud Run (same container) | **Low** — stays in the monolith; store images in Cloud Storage. |
| Resend email | Unchanged (or FCM/Cloud Tasks for queueing) | **None** initially. |
| GHIN / GroupMe / ForeTees / Sheets | Unchanged (outbound HTTP) | **None** — verify egress + Secret Manager wiring. |
| Sentry | Unchanged; add Cloud Logging | **None**. |

### Frontend hosting: Firebase Hosting vs. serve-from-Cloud-Run
Firebase Hosting is chosen (D3) because static SPA assets don't need compute and
shouldn't pay for it:
- **CDN + no cold start.** Assets are edge-cached globally with free SSL. Serving
  the SPA from the Cloud Run container instead would wake a *heavy* image
  (`opencv-python-headless`, `numpy`, `Pillow`) just to hand out `index.html` —
  cold-start latency on first paint, or `min-instances=1` paid 24/7 to avoid it.
- **Same-origin without CORS.** A Firebase Hosting **rewrite** sends `/api/**` to
  the Cloud Run service, so the browser sees one origin (static from the edge,
  API proxied to Cloud Run) — no CORS config at all.
- **Decoupled deploys.** A `vite build` deploy doesn't rebuild the backend container.

**Documented alternative — serve static from the Cloud Run FastAPI service.**
`main.py` already imports `StaticFiles`, so the built SPA could mount on the same
service: one service, one origin, no CORS. The trade is cold-start latency on the
heavy image and paying compute to serve static bytes. For a low-traffic app that
may be an acceptable simplicity win — it's a simplicity-vs-performance call, not a
right/wrong one.

> **Not in scope: a frontend *framework* change.** The app is on Vite + React 19,
> which is modern and correct for a dynamic, authenticated, real-time SPA.
> Build-time static generators (e.g. Gatsby) solve a content-site problem this app
> doesn't have and would be a downgrade-plus-rewrite for no benefit. Hosting is a
> deploy-target choice; the framework stays put.

---

## 7. Authentication Migration

> **✅ Decided (D4): Auth0 stays. This migration does not touch auth.** Auth is the
> most decoupled part of the stack — the backend simply verifies a JWT per request
> (`auth_service.py`); it does not care whether compute runs on Render or Cloud
> Run. Auth0 works unchanged in front of a GCP-hosted app, so moving auth is an
> **independent, deferred** decision, deliberately kept off the critical path. The
> rest of this section is the *if/when* plan, not committed work.

**Why we're deferring it (the annoying part):** Auth0 generally does **not** export
password hashes except on enterprise plans / via a support request. Without the
hashes, Firebase can't recreate password logins silently, so email+password users
would face a forced password reset — a real, user-visible disruption. Social
logins (Google, etc.) re-link transparently by verified email, so the actual cost
depends entirely on the user mix. Revisit only if there's a concrete driver (cost
at scale, single-bill consolidation) *and* after measuring how many users are
password-based.

### If/when auth is migrated later — the plan

**Backend** (`auth_service.py` today verifies Auth0 RS256 JWTs against
`AUTH0_DOMAIN`/`AUTH0_API_AUDIENCE`):
- Replace JWT verification with the Firebase Admin SDK
  (`firebase_admin.auth.verify_id_token`) or verify Firebase's public JWKS
  directly. The `PlayerProfile` linkage (currently keyed off the Auth0 `sub`)
  re-keys to the Firebase UID.
- Keep the fail-closed behavior (missing config → 401, never 500).

**Frontend:** swap `@auth0/auth0-react` for the Firebase JS SDK; rework
`src/context/AuthContext.jsx` and `src/services/authToken.js` to source ID tokens
from Firebase.

**User migration:** Auth0 users must be imported into Firebase Auth. Firebase's
user-import tool accepts hashed passwords, but **social logins (Google, etc.)
re-link by verified email** — mostly transparent, but password users may need a
reset flow. This needs a dedicated migration runbook and a comms plan.

**Fallback:** Google **Identity Platform** is the same engine as Firebase Auth
with enterprise features (multi-tenancy, SAML) if ever needed — no code change to
adopt later.

---

## 8. Data Migration Strategy

Assuming **Option A (Cloud SQL)**:

1. **Provision** a Cloud SQL Postgres instance (match major version to Render's).
2. **Dry-run dump/restore** into a staging instance; run the full pytest suite
   against it.
3. **Schema parity check** — the app already has `ensure_schema.py` /
   `migrations_runner.py`; run them against Cloud SQL to confirm.
4. **Cutover** via short maintenance window: freeze writes, final `pg_dump`,
   restore, flip `DATABASE_URL`, smoke-test (`/health` must report
   `environment=production`; junk Bearer to `/players/me` → 401 not 500).
5. **Rollback plan:** keep Render Postgres warm and read-only for N days; the
   `DATABASE_URL` flip is instantly reversible.

For any **Option C** Firestore adoption, backfill is one-directional (SQL → Firestore
projections) and owned by the backend — Firestore is a *derived read model*, never
the source of truth for relational data.

---

## 9. Phased Rollout Plan

Each phase is independently shippable and reversible.

- **Phase 0 — Foundation.** Create GCP project, enable APIs, wire Secret Manager,
  set up CI to build the backend container. No user-facing change.
- **Phase 1 — Compute.** Deploy the existing FastAPI container to Cloud Run,
  still pointing at Render Postgres. Validate WebSockets, OCR, schedulers behind
  a canary URL.
- **Phase 2 — Database.** Migrate Postgres → Cloud SQL (§8). Flip `DATABASE_URL`.
- **Phase 3 — Hosting.** Move the React SPA to Firebase Hosting; add the `/api/**`
  rewrite to Cloud Run (same-origin). Decommission the Vercel project.
- **Phase 4 — Scheduling.** Replace in-process `schedule` jobs with Cloud
  Scheduler → Cloud Run jobs.
- **Phase 5 (optional) — Firestore realtime.** Adopt Firestore listeners for live
  game state / notifications where it improves UX (Option C).
- **Phase 6 — Decommission** Render (compute + DB) after a soak period. **Auth0
  stays.**

**Deferred / out of core scope — Auth migration (§7).** Auth0 → Firebase Auth is
*not* part of this rollout (D4). If it is ever revisited, it becomes its own
project with a user-import dry run and comms plan, sequenced after everything
above — never bundled into the platform move.

---

## 10. Cost Considerations

- **Cloud Run:** scales to zero — pay per request/CPU-second. Likely cheaper than
  an always-on Render instance at low traffic, but cold starts matter for a large
  OpenCV container (mitigate with min-instances=1 if latency-sensitive).
- **Cloud SQL:** the main fixed cost — an always-on instance (no scale-to-zero for
  the standard tiers). **Decided (D6): accept the always-on floor** — a small
  shared-core instance runs in the single-digit-to-low-double-digit $/mo range,
  which is negligible at this app's scale and buys predictable sub-ms in-region
  latency with no DB cold start. Size to current Postgres usage.
  - *Scale-to-zero alternatives considered and rejected:* **AlloyDB** is a
    premium/high-performance tier (autoscales read pools, primary always on) — it
    *raises* the floor, so it's out for a cost-driven choice. **Neon** (serverless
    Postgres) genuinely scales to zero and is Postgres-compatible, but adds a
    second vendor (vs. the consolidation goal) and a DB cold-start that would
    *compound* with Cloud Run's own cold start on the first idle request. Not
    worth it for a single small production DB.
- **Firebase Auth:** free up to a generous MAU tier; Identity Platform bills
  beyond that.
- **Firestore (if adopted):** pay per read/write/delete + storage. Denormalized
  aggregation designs can generate surprising write fan-out — model carefully.
- **Firebase Hosting:** free tier likely covers current frontend traffic.
- **Egress:** external integrations (GHIN/GroupMe/Sheets) are outbound HTTP —
  negligible.

A proper cost model needs current traffic/MAU/DB-size numbers before committing.

---

## 11. Open Questions

1. ~~**Database target** — Cloud SQL-first vs. Firestore rewrite?~~ **✅ Resolved:
   Cloud SQL for PostgreSQL** (see [§4](#4-the-central-decision-database)). The
   relational schema moves unchanged; Firestore is out of scope as system of record.
2. ~~**Frontend hosting** — move off Vercel?~~ **✅ Resolved: Firebase Hosting**
   with an `/api/**` rewrite to Cloud Run ([§6](#6-component-by-component-mapping)).
3. ~~**Auth cutover UX** — password-reset vs. transparent?~~ **✅ Resolved: Auth0
   stays; auth migration deferred** off the critical path ([§7](#7-authentication-migration)).
   The password-hash question only matters if/when auth is revisited later.
4. **WebSockets vs Firestore** — keep Cloud Run WebSockets, or invest in Firestore
   listeners to also replace the offline sync layer?
5. **Region / data residency** — which GCP region? Any residency constraints?
6. ~~**Budget ceiling** — acceptable always-on floor?~~ **✅ Resolved: accept the
   Cloud SQL always-on floor** (D6, [§10](#10-cost-considerations)) — a small
   instance's ~$10/mo is negligible; scale-to-zero DBs rejected.
7. **Timeline & ownership** — who owns each phase, and is there a hard cutover
   deadline?

---

## 12. Risks & Non-Goals

**Risks**
- **Cold starts** on a heavy OpenCV container could hurt scorecard-scan latency
  (mitigate with `min-instances=1` if needed).
- **Auth migration** *would be* the highest-risk change (user lockout is
  user-visible and hard to undo) — which is exactly why it's **deferred and kept
  out of this migration** (D4). Not a risk we're taking on here.
- **Scheduler semantics** — moving from an in-process `schedule` loop to Cloud
  Scheduler changes at-least-once/at-most-once guarantees; audit idempotency.
- **Scope creep into Firestore** — the temptation to "do it properly in Firestore"
  is where this project balloons from weeks to quarters. Resist it in v1.

**Non-Goals**
- Rewriting the WGP rules/scoring/betting engine.
- Full Firestore adoption in the initial cutover.
- Changing external integrations (GHIN, GroupMe, ForeTees, Sheets, Resend).

---

*Draft — pending review. See [§11](#11-open-questions) before scheduling work.*
