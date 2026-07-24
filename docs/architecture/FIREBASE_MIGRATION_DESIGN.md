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
  Vercel (frontend), Render (backend + Postgres), and Auth0 (identity). A single
  Google Cloud project would unify hosting, compute, database, auth, secrets,
  logging, and scheduling under one bill and one IAM model.
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

### Recommendation
Start with **Option A** for the cutover (de-risk the platform move), then adopt
**Option C** opportunistically where realtime/offline UX benefits justify it.
Treat **Option B (full Firestore)** as explicitly out of scope unless a later,
separate decision revisits it.

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
| Vercel static hosting | Firebase Hosting | **Low** — `vite build` → `firebase deploy`. Rewrite `vercel.json` routing as `firebase.json` rewrites. |
| Auth0 (`@auth0/auth0-react`) | Firebase Auth (`firebase/auth`) | **Medium** — see [§7](#7-authentication-migration). |
| FastAPI on Render | FastAPI on Cloud Run | **Low–Medium** — reuse `backend/Dockerfile`; swap Render env wiring for Cloud Run + Secret Manager; add Cloud SQL connector. |
| PostgreSQL on Render | Cloud SQL Postgres | **Low** — `pg_dump`/restore; change `DATABASE_URL`. Code path in `database.py` already branches on `postgresql://`. |
| WebSocket game broadcasts | Cloud Run WebSockets (Option A) **or** Firestore listeners (Option C) | **Low** (A) / **Medium** (C). |
| In-process `schedule` jobs | Cloud Scheduler → Cloud Run endpoints/jobs | **Medium** — extract scheduler triggers into HTTP-invoked jobs so they don't rely on a long-lived process. |
| Scorecard OCR (OpenCV) | Cloud Run (same container) | **Low** — stays in the monolith; store images in Cloud Storage. |
| Resend email | Unchanged (or FCM/Cloud Tasks for queueing) | **None** initially. |
| GHIN / GroupMe / ForeTees / Sheets | Unchanged (outbound HTTP) | **None** — verify egress + Secret Manager wiring. |
| Sentry | Unchanged; add Cloud Logging | **None**. |

---

## 7. Authentication Migration

Auth0 → Firebase Auth is the highest-touch edge change because it affects both
clients and every protected endpoint.

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
- **Phase 3 — Hosting.** Move the React SPA to Firebase Hosting; repoint API base
  URL to Cloud Run.
- **Phase 4 — Auth.** Migrate Auth0 → Firebase Auth (§7). Highest risk — do it
  last, with a user-import dry run and comms.
- **Phase 5 — Scheduling.** Replace in-process `schedule` jobs with Cloud
  Scheduler → Cloud Run jobs.
- **Phase 6 (optional) — Firestore realtime.** Adopt Firestore listeners for live
  game state / notifications where it improves UX (Option C).
- **Phase 7 — Decommission** Render + Vercel + Auth0 after a soak period.

---

## 10. Cost Considerations

- **Cloud Run:** scales to zero — pay per request/CPU-second. Likely cheaper than
  an always-on Render instance at low traffic, but cold starts matter for a large
  OpenCV container (mitigate with min-instances=1 if latency-sensitive).
- **Cloud SQL:** the main fixed cost — an always-on instance (no scale-to-zero for
  the standard tiers). Size to current Postgres usage; this is the line item to
  watch.
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

1. **Database target** — accept the recommended Cloud SQL-first path, or is there
   an appetite for a Firestore rewrite despite the aggregation risk?
2. **Frontend hosting** — is moving off Vercel worth it, or keep Vercel and only
   migrate backend + auth + DB? (Vercel + Cloud Run is a valid end state.)
3. **Auth cutover UX** — acceptable to require a password reset for password-based
   Auth0 users, or must migration be fully transparent?
4. **WebSockets vs Firestore** — keep Cloud Run WebSockets, or invest in Firestore
   listeners to also replace the offline sync layer?
5. **Region / data residency** — which GCP region? Any residency constraints?
6. **Budget ceiling** — what's the acceptable monthly floor given Cloud SQL is
   always-on?
7. **Timeline & ownership** — who owns each phase, and is there a hard cutover
   deadline?

---

## 12. Risks & Non-Goals

**Risks**
- **Auth migration** is the highest-risk phase — user lockout is user-visible and
  hard to undo. Dry-run and stage it.
- **Cold starts** on a heavy OpenCV container could hurt scorecard-scan latency.
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
