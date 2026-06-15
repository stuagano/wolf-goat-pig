# Sentry setup (Phase 2a)

The code ships **no-op until the DSN env vars are set**. Sentry's **free tier**
(5k errors/mo, 1 dev) covers this project at **$0** — no paid plan needed.

Org: `o4511570300502016` (created 2026-06-15). Backend project DSN is committed
in `render.yaml` (a Sentry DSN is a public-safe ingestion key).

## 1. Create Sentry projects (under the existing org)
- **wolf-goat-pig-backend** — Platform: **Python / FastAPI** (its DSN is the one in `render.yaml`).
- **wolf-goat-pig-frontend** — Platform: **React** (separate DSN; not yet wired).
- A DSN is at **Settings → Projects → [project] → Client Keys (DSN)**. The org id alone is NOT a DSN.

## 2. Where the DSNs live
- **Backend** — `SENTRY_DSN` is in **`render.yaml`** (version-controlled). It applies once the service is Blueprint-connected (see `render-blueprint.md`); until then, set `SENTRY_DSN` once in the Render dashboard to activate it now.
- **Frontend** — `VITE_SENTRY_DSN` goes in **Vercel** (frontend build var) once a frontend Sentry project exists; redeploy so Vite inlines it. It's public-safe (ships in the browser), so it can also be committed to `vercel.json` `build.env`.

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
