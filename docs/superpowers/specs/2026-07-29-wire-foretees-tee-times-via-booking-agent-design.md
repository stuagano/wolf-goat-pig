# Wire FastAPI tee-times through booking-agent

**Date:** 2026-07-29  
**Status:** Approved for implementation planning  
**Depends on:** `docs/superpowers/specs/2026-07-28-booking-agent-tee-times-design.md` (live `POST /tee-times` on `wgp-booking`)

## Problem

The SPA lists ForeTees day sheets via `GET /api/foretees/tee-times`, which still scrapes `Member_sheet` inside the main FastAPI process. The booking agent already exposes a per-member `POST /tee-times` (httpx scrape under the caller's ForeTees login). Listing and booking should share that path so identity and parsing stay consistent.

## Goals

- Replace the FastAPI in-process list scrape with a proxy to booking-agent `POST /tee-times`.
- Require **per-user** ForeTees credentials on the Auth0 member profile (no env singleton fallback for listing).
- Keep the SPA contract: same `GET /api/foretees/tee-times?date=` and existing `ApiResponse` / slot shape.
- Surface agent auth/sheet failures as real HTTP errors — never as an empty day.

## Non-goals

- Changing the SPA hook or UI (`useTeeTimes` / `ForeTeesTeeSheet`).
- Moving book/cancel confirm flow (already on the agent).
- Proxying `GET /api/foretees/bookings` (my upcoming list) in this pass.
- Feature-flag dual path (explicitly rejected: full replace).
- Extracting a shared scrape library between services.

## Decision summary

| Choice | Value |
|---|---|
| Cutover | Replace FastAPI scrape for listing |
| Credentials | Per-user profile only |
| SPA | Unchanged |
| Layer | `ForeteesService.get_tee_times` proxies to agent |
| Failures | Map agent `502` / transport errors to HTTP errors (not `[]`) |

## Architecture

```
SPA (unchanged)
  GET /api/foretees/tee-times?date=YYYY-MM-DD
        │  Auth0 Bearer
        ▼
FastAPI foretees router
        │  require foretees_username + decrypt password
        │  else 400 configure credentials
        ▼
ForeteesService.get_tee_times(date, username, password)
        │  POST BOOKING_SERVICE_URL/tee-times
        │  Authorization: Bearer BOOKING_SERVICE_SECRET
        │  body: { username, password, date }
        ▼
wgp-booking POST /tee-times
        │  httpx Wingpoint login + SSO + Member_sheet
        ▼
{ status: "ok", date, slots: [...] }
        ▼
ApiResponse.success(data=slots, …)
```

## API / behavior contract (product-facing)

### Unchanged

- `GET /api/foretees/tee-times?date=YYYY-MM-DD` (Auth0 required).
- Success: existing `ApiResponse.success` with `data` = list of slots (`date`, `time`, `front_back`, `players`, `open_slots`, `max_players`, `ttdata`, `jump`, `p5_allowed`).

### New / changed

| Condition | HTTP | Behavior |
|---|---|---|
| No per-user ForeTees username/password on profile | `400` | Clear message to configure credentials in Account (do **not** use env singleton). |
| Decrypt failure | `400` or `500` | Prefer `400` “re-save ForeTees credentials” if decrypt fails; log detail server-side. |
| Booking service `401` (bad `BOOKING_SERVICE_SECRET`) | `502` | Message that booking service auth failed. |
| Booking service `502` `foretees_auth_failed` | `502` | ForeTees login failed for this member. |
| Booking service `502` `foretees_sheet_failed` | `502` | Sheet fetch failed. |
| Booking service unreachable / timeout | `502` | Explicit unavailable/timeout message. |
| Success with zero slots | `200` | Empty list only when agent returned `status: ok` and empty `slots`. |

`FORETEES_ENABLED=false` continues to return success with `data=[]` and a disabled message (existing behavior).

## Components

### `backend/app/routers/foretees.py` — `get_tee_times`

1. Resolve credentials from `current_user` only (no `_get_user_service` env fallback for this endpoint).
2. If missing → `HTTPException(400, detail=…)`.
3. Call a service method that takes explicit `username`, `password`, `date`.
4. Map typed failures to HTTP status codes above.
5. On success return `ApiResponse.success(data=slots, …)` as today.

Book/cancel may keep using `_get_user_service` (including env fallback) unless a follow-up tightens those too — **out of scope** for this spec.

### `backend/app/services/foretees_service.py`

1. Change listing to call booking-agent:
   - `POST /tee-times` with `{username, password, date}`.
   - Reuse Bearer secret / URL from env (`BOOKING_SERVICE_URL`, `BOOKING_SERVICE_SECRET`).
2. Use a **read-oriented timeout** (recommend connect 30s, total ~60s) — not the 300s Computer Use book timeout.
3. Prefer a dedicated helper (e.g. `_call_booking_tee_times`) rather than overloading `_call_booking_service`’s soft `{success: false}` dict shape, so list errors raise or return a typed result the router can map cleanly.
4. Stop calling the in-process `_ensure_session` + `Member_sheet` path from `get_tee_times`. Leave unused scrape helpers in place for this pass (cleanup follow-up) **or** delete only if tests do not depend on them — prefer leave helpers, remove the call site.

### Frontend

No changes.

### Config / deploy

No new secrets. Production already has `BOOKING_SERVICE_URL` and `BOOKING_SERVICE_SECRET` on the API.

## Testing

1. **Router unit tests** (`test_foretees_router.py`):
   - No profile creds → `400`.
   - Mock service returning slots → `200` with data.
   - Mock agent auth failure → `502` (not empty list).
2. **Service unit tests** (mock httpx / booking URL):
   - Happy path parses agent `{status: ok, slots}` → list.
   - Agent `502` body / non-JSON / timeout → typed failure.
3. **Regression:** existing book/cancel confirm tests still pass.
4. **Manual smoke after deploy:** authenticated SPA tee sheet for a member with saved ForeTees creds; member without creds sees configure prompt/error.

## Rollout

1. Implement + unit tests; merge → Cloud Run API auto-deploy.
2. Smoke SPA day sheet with a real profile that has ForeTees creds.
3. Confirm Cloud Logging shows booking-agent `/tee-times` calls from the API.

## Follow-ups (deferred)

- Same per-user-only rule for book/cancel (drop env singleton).
- Proxy `GET /bookings` through the agent if/when that endpoint exists.
- Delete dead in-process scrape helpers once unused.
- SPA UX polish for “configure ForeTees credentials” on 400.
