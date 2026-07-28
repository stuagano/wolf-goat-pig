# Phase 3 — Hosting (React SPA on Firebase Hosting)

Moves the Vite-built SPA from Vercel to Firebase Hosting (design doc D3/§6).
Static assets are edge-cached with free SSL; no compute wakes to serve HTML.

## Deploy

**Auto on push to `main`** when `GCP_AUTO_DEPLOY=true` and `frontend/**` (or
this directory) changes. Manual: **Actions → Deploy to GCP → Run workflow** with
`deploy_frontend = true`. The job builds `frontend/` and runs `firebase deploy
--only hosting`. `firebase.json` here is copied to the repo root at deploy time
because Firebase resolves `hosting.public` relative to the config file's location.

`firebaserc.example` → copy to `.firebaserc` (or pass `--project`) to pin the
Firebase project.

## API connectivity: two options

### A. Cross-origin to Cloud Run (what this scaffolding uses) ✅ simplest, correct today
The SPA calls the backend at its Cloud Run URL via the build-time `VITE_API_URL`
(set as a repo Actions Variable). The backend already does CORS off `FRONTEND_URL`
— set that to the Firebase Hosting URL. This mirrors today's Vercel→Render setup
exactly, so it needs no backend change.

### B. Same-origin `/api/**` rewrite (doc's D3 ideal) — needs a backend prefix change
The doc favors a Firebase Hosting **rewrite** so `/api/**` proxies to Cloud Run
and the browser sees one origin (no CORS). That requires the backend routes to
live under a shared `/api` prefix — today they are mounted at the root
(`/players/me`, `/signups`, `/tee-sheet`, …), and a broad rewrite would collide
with the SPA's own client-side routes. Adopting option B means:

1. Mount all API routers under `/api` in `backend/app/main.py` (and update
   `VITE_API_URL` to `/api`), then
2. add this to `firebase.json` **before** the `"**" → /index.html` rewrite:
   ```json
   { "source": "/api/**", "run": { "serviceId": "wolf-goat-pig-api", "region": "us-central1" } }
   ```

That backend refactor is out of scope for this infra PR; option A is wired up and
works now.

## After deploy

- Set the backend's `FRONTEND_URL` (in `env.production.yaml`) to the Firebase
  Hosting URL and redeploy the backend so CORS + email links are correct.
- Add the Firebase Hosting domain to the **Auth0 Allowed Callback/Logout/Web
  Origins** (Auth0 stays — D4).
- Decommission the Vercel project only after the Firebase URL is verified.
