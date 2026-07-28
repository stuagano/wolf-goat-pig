# Booking-agent tee-times read API

**Date:** 2026-07-28  
**Status:** Approved for implementation planning  
**Scope:** Add a read-only day sheet endpoint to `wgp-booking` (Computer Use booking agent). Do **not** change the SPA or FastAPI list path in this pass.

## Problem

The booking agent (`booking-agent` / Cloud Run `wgp-booking`) only books and cancels. Listing available tee times and who is already on them lives entirely on the main FastAPI ForeTees scrape (`GET /api/foretees/tee-times`). Callers that talk only to the booking service cannot browse the day sheet under a member’s ForeTees identity.

## Goals

- Expose **available tee times for a given date** and **who is playing on each slot** from the booking agent.
- Run the read **as the calling member** (caller-supplied ForeTees username/password), matching `/book` and `/cancel`.
- Keep the existing SPA → FastAPI → httpx scrape path unchanged.

## Non-goals

- Wiring FastAPI or the SPA to call the new booking-agent endpoint.
- Gemini Computer Use / Playwright for listing (too slow/fragile for structured reads).
- Shared library extraction between FastAPI and booking-agent (defer until a second consumer needs DRY).
- `GET`/`POST` “my bookings” (`Member_teelist_list`) — out of this pass unless added as a follow-up.
- Changing book/cancel Computer Use behavior.

## Decision summary

| Choice | Value |
|---|---|
| Surface | `POST /tee-times` on booking-agent |
| Auth | Bearer `BOOKING_SERVICE_SECRET` (same as `/book`) |
| Credentials | Body: `username`, `password`, `date` |
| Fetch | httpx login + SSO + `Member_sheet` HTML scrape |
| Identity | Per-user ForeTees session (not a shared service account) |
| Consumers this pass | Direct API callers / future FastAPI proxy; SPA stays on FastAPI |

## Architecture

```
Caller (API client / future proxy)
        │  Authorization: Bearer BOOKING_SERVICE_SECRET
        │  POST /tee-times { username, password, date }
        ▼
wgp-booking (Cloud Run)
        │  httpx (no Chromium, no Gemini)
        ├─ Wingpoint login (UserLOGIN / UserPWD)
        ├─ Tee page → ftSSOKey / ftSSOIV
        ├─ ForeTees Member_select SSO → JSESSIONID
        └─ GET Member_sheet?calDate=MM/DD/YYYY
                ▼
        Parse data-ftjson Member_slot rows
                ▼
        { status, date, slots: [ time, players, open_slots, … ] }
```

Existing book/cancel path is unchanged and remains Computer Use + Playwright.

## API contract

### Request

`POST /tee-times`

Headers:

- `Authorization: Bearer <BOOKING_SERVICE_SECRET>` (required when secret is configured)

Body:

```json
{
  "username": "member@example.com",
  "password": "…",
  "date": "2026-07-28"
}
```

- `date` must be `YYYY-MM-DD`.
- Empty username/password → `400`.

### Success response

HTTP `200`:

```json
{
  "status": "ok",
  "date": "2026-07-28",
  "slots": [
    {
      "date": "2026-07-28",
      "time": "11:00 AM",
      "front_back": "F",
      "players": [
        { "name": "Jane D", "transport": "WLK" }
      ],
      "open_slots": 3,
      "max_players": 4,
      "ttdata": "…",
      "jump": 0,
      "p5_allowed": false
    }
  ]
}
```

Slot field semantics match FastAPI’s `_parse_tee_sheet` output so a future FastAPI proxy can drop in without reshaping.

### Error responses

| Condition | HTTP | Body |
|---|---|---|
| Missing/invalid Bearer | `401` | `{ "detail": "Unauthorized" }` |
| Invalid/missing date or creds | `400` | `{ "detail": "…" }` |
| ForeTees login / SSO failure | `502` | `{ "status": "failed", "error": "foretees_auth_failed" }` |
| Sheet fetch/parse failure after auth | `502` | `{ "status": "failed", "error": "foretees_sheet_failed" }` |

Unlike FastAPI’s current list path (which often returns `[]` on auth failure), this endpoint **must not** disguise auth failure as an empty day. Empty `slots` is only valid when auth succeeded and the sheet truly has no `Member_slot` rows.

## Components

### `booking-agent/app/main.py`

- Add `TeeTimesRequest` Pydantic model.
- Add `POST /tee-times` handler: `_check_auth` → validate → call sheet fetcher → return contract above.

### `booking-agent/app/tee_sheet.py` (new)

Port the minimal ForeTees read path from `backend/app/services/foretees_service.py`:

1. Session establish (Wingpoint login → SSO → JSESSIONID).
2. `get_tee_times(date)` against `Member_sheet`.
3. `_parse_tee_sheet` equivalent for `data-ftjson` / `Member_slot` / `wasP1…wasP5` / open-slot CSS.

Use URLs from `Settings` (`wingpoint_base`, `login_page`, `tee_time_page`, `foretees_base`). Do **not** import backend packages into the booking-agent image.

Session handling: short-lived per request (or request-scoped httpx client). No need to share state with Computer Use jobs; listing must not require session affinity.

### Dependencies

- Ensure `httpx` is in `booking-agent/requirements.txt` if not already present.

## Testing

1. **Unit — parser:** Fixture HTML with known `data-ftjson` rows → expected players / open_slots / times.
2. **Unit — auth gate:** Missing Bearer → `401` when secret configured.
3. **Unit — validation:** Bad date / empty creds → `400`.
4. **Contract (optional, mocked httpx):** Login + sheet sequence returns shaped slots.
5. **Live (optional, env-gated):** Against real ForeTees with test member creds — not part of default CI.

## Rollout

1. Implement + unit tests in `booking-agent/`.
2. Auto-deploy via existing `booking-agent/**` → `deploy-booking` path.
3. Smoke: `POST /tee-times` with Bearer + member creds → non-empty or intentional empty slots; bad secret → `401`.
4. Document the endpoint in `booking-agent/README.md` and `docs/architecture/COMPUTER_USE_BOOKING.md` (amend non-goals: reads available via httpx on the agent; SPA still uses FastAPI).

## Follow-ups (explicitly deferred)

- FastAPI proxy option: `GET /api/foretees/tee-times` may call booking-agent `/tee-times` as primary or fallback.
- SPA unchanged until that proxy lands.
- Shared scrape package if both services should stay in sync without copy-paste drift.
- `POST /bookings` for the member’s upcoming list.
