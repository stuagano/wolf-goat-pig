# ForeTees booking via Gemini Computer Use

Replaces the Node/Playwright microservice on Render
(`booking-service` → `wolf-goat-pig-booking.onrender.com`) with a GCP-native
**Computer Use** agent on Cloud Run.

## Decision (2026-07-28)

| Choice | Value |
|---|---|
| Approach | Full Computer Use rewrite (not lift-and-shift of scripted Playwright) |
| Speed | Not a hard requirement — multi-turn agent loop is OK |
| Safety | Hybrid: auto-run low-risk nav and login; **SPA must confirm final submit/cancel** |
| Credentials | Never sent through the model — custom tool `enter_foretees_credentials` |

Google’s Computer Use ToS: when the model returns `require_confirmation`, the
end user must confirm. We never auto-ack those. Separately, our policy always
pauses before irreversible ForeTees submit/cancel.

Login is deliberately **not** gated. The model never sees the credentials, so a
prompt there bought no safety — and it cost reliability: the job and its live
Playwright browser exist only in one instance's memory, so while the user read
the login prompt Cloud Run scaled the instance away and the confirm landed on a
cold instance that had never seen the job. Confirmations now happen seconds
before the submit the user just asked for. Two guards back that up:
`job_ttl_seconds` (600) expires a stalled job *before* Cloud Run's ~15min idle
reap, and an unknown `job_id` returns `status: "expired"` with a
"start the booking again" message rather than a bare failure.

## Architecture

```
SPA (Firebase)  →  Cloud Run API (FastAPI)
                        │  BOOKING_SERVICE_URL
                        ▼
                   Cloud Run booking-agent (Python)
                        │  Playwright Chromium (local)
                        │  Vertex Gemini Computer Use
                        ▼
                   Wingpoint / ForeTees v5
```

The agent still needs a real browser. Computer Use is the **decision layer**;
Playwright executes `click_at` / `type_text_at` / etc. from model function calls.

## HTTP contract (booking-agent)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness |
| `POST` | `/book` | Start book job |
| `POST` | `/cancel` | Start cancel job |
| `POST` | `/jobs/{job_id}/confirm` | Resume after SPA confirm (`{ "confirm": true\|false }`) |
| `POST` | `/tee-times` | List day sheet + players via httpx |

### Responses

```jsonc
// Pause for user
{
  "status": "needs_confirmation",
  "job_id": "…",
  "kind": "submit" | "safety",
  "explanation": "About to submit the 8:40 AM request…",
  "screenshot_b64": "…",   // optional PNG
  "success": false
}

// Done
{ "status": "completed", "success": true, "title": "…", "messages": ["…"] }

// Failed / denied
{ "status": "failed", "success": false, "error": "…" }
```

FastAPI proxies these shapes on `/api/foretees/book`, `/cancel`, and
`/api/foretees/book/confirm` (Auth0-protected). The SPA loops until
`completed` / `failed`, showing a confirm step when `needs_confirmation`.
Tee-time list reads use the separate path
SPA → FastAPI `GET /api/foretees/tee-times` → booking-agent `POST /tee-times`
(httpx, per-user creds).

## Agent tools

Built-in Computer Use (`ENVIRONMENT_BROWSER`) plus:

1. **`request_confirmation(kind, explanation)`** — pauses the job for the SPA.
   Required before Submit Request / Cancel Reservation. Not used for login.
2. **`enter_foretees_credentials()`** — fills Wingpoint login from job-scoped
   secrets (never included in model prompts or `type_text_at`).
3. **`report_booking_result(success, title, messages)`** — terminal structured
   result when ForeTees responds.

## Deploy notes

- Service: `wgp-booking` in `us-central1`, session affinity on, timeout ≥ 300s,
  memory ≥ 2Gi (Chromium).
- Runtime SA needs Vertex AI user + Secret Manager access to
  `BOOKING_SERVICE_SECRET`.
- Main API `BOOKING_SERVICE_URL` points at the booking-agent Cloud Run URL.
- After soak: suspend Render `wolf-goat-pig-booking`.

See `deploy/gcp/phase7-booking/`.

## Non-goals

- Same-origin Firebase `/api` rewrite.
- Book/cancel remain Computer Use on the agent; list is not Computer Use.
- Auto-acking Google `require_confirmation` (forbidden by ToS).
