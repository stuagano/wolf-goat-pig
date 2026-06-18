# Deployment Troubleshooting

Diagnosing and fixing deployment issues on Render (backend) and Vercel (frontend).
For the deploy process itself, see [DEPLOYMENT.md](./DEPLOYMENT.md).

> Most deployment problems are environment-configuration problems. Check env vars
> first (and remember Render does **not** read them from `render.yaml` — they live
> in the dashboard).

## Quick diagnostics

```bash
# Backend health (environment must read "production")
curl https://wolf-goat-pig.onrender.com/health

# Scripted verification (backend + frontend + integration)
python scripts/deployment/verify-deployments.py \
  --backend https://wolf-goat-pig.onrender.com \
  --frontend https://wolf-goat-pig.vercel.app

# Local production-build smoke test before pushing
./scripts/deployment/test-prod-all.sh
```

## Backend (Render)

### Service won't start / deploy fails

Symptoms: "Deploy failed", module import errors, crash on startup.

- Verify `requirements.txt` is complete: `cd backend && python -c "from app.main import app"`.
- Test the production server locally: `./scripts/deployment/test-prod-backend.sh`.
- Check the Render build/runtime logs for the failing import or migration.

### Database connection fails

Symptoms: "could not connect to server", "relation does not exist", timeouts.

- Confirm `DATABASE_URL` is set in the Render dashboard.
- Use the internal connection string for same-region databases.
- Migrations run automatically at startup (`render-startup.py` → `app/migrations_runner.py`);
  a missing table usually means a migration failed — check the logs for the first error.

### Environment variables missing

Symptoms: Auth0 failures, `KeyError` in logs, 500s on protected routes.

Required backend variables (set in the Render dashboard):

```
ENVIRONMENT=production
DATABASE_URL=<postgres-url>
AUTH0_DOMAIN=<tenant-domain>
AUTH0_API_AUDIENCE=<api-audience>
AUTH0_CLIENT_ID=<client-id>
AUTH0_CLIENT_SECRET=<secret>
FRONTEND_URL=<vercel-url>
```

A junk Bearer token to `/players/me` should return **401, not 500** — a 500 means
auth config is broken, not just the token.

### CORS errors

Ensure the backend's allowed origins include the Vercel hostname and any custom
domain. Confirm `FRONTEND_URL` is set and `VITE_API_URL` (frontend) points at
the right backend.

## Frontend (Vercel)

### Build fails

- Test locally first: `cd frontend && npm install --legacy-peer-deps && npm run build`.
- Watch for **case-sensitive imports** — these work on macOS but fail on Vercel's Linux builders.
- Clear caches if needed: `npm cache clean --force`, then reinstall.

### npm / "Missing script: build" errors

Vercel builds from the repo root. The root `package.json` delegates `build` and
`install` to `frontend/`, and the root `vercel.json` sets explicit `buildCommand`
and `installCommand`. If you see "Missing script: build", confirm those root
scripts and `vercel.json` commands are intact.

### Peer dependency / ERESOLVE errors

Some dependencies declare peer ranges that predate React 19, so installs rely on
`legacy-peer-deps`:

- `.npmrc` contains `legacy-peer-deps=true`.
- The `vercel.json` install command includes `--legacy-peer-deps`.

If you hit "ERESOLVE unable to resolve dependency tree", verify both are present.

### API calls fail

- Confirm `VITE_API_URL` is set in the Vercel dashboard (remember `VITE_*`
  is baked in at build time — change it and **redeploy**).
- Avoid HTTP-vs-HTTPS mismatches and trailing slashes in the URL.

### Blank page / app won't load

- Check the build output exists: `ls -la frontend/build/static/`.
- Serve the build locally to reproduce: `npx serve -s frontend/build`.
- Inspect the browser console for the first error.

### Auth0 / login issues

- Callback URLs in Auth0 must include the Vercel production URL (and preview URLs).
- The audience must match exactly between `AUTH0_API_AUDIENCE` (backend) and
  `VITE_AUTH0_AUDIENCE` (frontend).

## Docker (local production parity)

See [DOCKER-SETUP.md](./DOCKER-SETUP.md) for the full local-container workflow.

```bash
# Inspect logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## Common error patterns

| Error | Likely cause | Quick fix |
|-------|-------------|-----------|
| `ModuleNotFoundError` | Missing dependency | Add to `requirements.txt` |
| `Connection refused` | Wrong port/host | Check `DATABASE_URL` |
| `401 Unauthorized` | Auth misconfiguration | Verify Auth0 settings |
| `500` on protected route | Broken auth config (not just bad token) | Check `AUTH0_*` env vars |
| `CORS blocked` | Missing origin | Add Vercel URL to allowed origins |
| `ERESOLVE` on install | Peer-dep conflict | Confirm `.npmrc` + `--legacy-peer-deps` |
| `Missing script: build` | Root scripts/`vercel.json` changed | Restore root `build`/`install` + Vercel commands |

## Emergency rollback

- **Render** — Dashboard → service → Rollback (or Manual Deploy → previous commit).
- **Vercel** — Dashboard → Deployments → Promote a previous working deployment.
- **Either** — `git revert HEAD && git push origin main`.

## Collecting debug info

When asking for help, include: the exact error text, the last ~100 log lines,
the env var **names** present (not values), and the output of
`python scripts/deployment/verify-deployments.py`.
