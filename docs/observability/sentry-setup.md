# Sentry setup (Phase 2a)

The code ships **no-op until these env vars are set**. One-time owner setup:

## 1. Create Sentry projects
- Create a Sentry org (free tier is fine).
- New project **wolf-goat-pig-backend** — Platform: **Python / FastAPI**.
- New project **wolf-goat-pig-frontend** — Platform: **React**.
- Copy each project's **DSN**.

## 2. Set the DSNs as env vars
- **Render** (backend service → Environment): `SENTRY_DSN = <backend DSN>`.
- **Vercel** (frontend project → Settings → Environment Variables): `VITE_SENTRY_DSN = <frontend DSN>` (Production; add Preview if desired). Redeploy so Vite inlines it at build time.

## 3. Email alerts to stuagano@gmail.com
- In each project: Settings → Alerts. Sentry's default rule emails on a new issue's first occurrence — confirm it's enabled and the email is verified.
- Recommended rules: **new issue**, **regression** (a resolved issue reappears), and a **spike**/event-frequency threshold.

## 4. Verify end-to-end
- Backend: with `SENTRY_DSN` set on Render, hit a route that errors (or temporarily add a throwaway `/debug/boom` that raises) → confirm an issue appears + an email arrives.
- Frontend: with `VITE_SENTRY_DSN` set, trigger a render error in a preview build → confirm an issue + email.
- Remove any throwaway debug route afterward.

## What's covered
- Every backend route's unhandled exceptions / 500s (FastAPI integration, auto-enabled by `sentry-sdk[fastapi]`).
- Frontend uncaught errors + unhandled promise rejections + React render errors (the existing `ErrorBoundary` now calls `captureException`).
- The 3 known **silent** failures — GHIN, Google Sheets, ForeTees — now report to Sentry even though they don't raise (they still return `False`/`None`; see the `external_service_silent_failures` memory). Phase 2b adds scheduled synthetic probes that route into this same Sentry.

## Security
- `send_default_pii=False` plus a `before_send` scrubber strips `Authorization`/`Cookie` headers and redacts `api_key`/`token`/`password`/`secret`-ish fields. Review `backend/app/observability/sentry.py::_scrub` before relying on it. Errors-only (no performance tracing / no session replay) keeps volume and cost low.
