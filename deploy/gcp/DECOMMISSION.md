# Decommission Render + Vercel (after GCP soak)

Do **not** run this until Firebase Hosting + Cloud Run + Cloud SQL have soaked
as production for at least a few days with no rollback need.

**Current canary (keep both stacks until soak is done):**

| Traffic | Frontend | API | DB |
|---|---|---|---|
| Production (users today) | Vercel | Render | Render Postgres |
| Canary | Firebase Hosting | Cloud Run | Cloud SQL (`db-f1-micro`) |

**Canary URLs**

- SPA: https://seventh-country-232522.web.app
- API: https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app
- Auth0 cutover checklist: [phase3-hosting/AUTH0_CUTOVER.md](phase3-hosting/AUTH0_CUTOVER.md)

## Before cutting users over

- [ ] Auth0 Allowed Callback / Logout / Web Origins include the Firebase domains
- [ ] Log in on the Firebase SPA; spot-check roster, games, scorecard
- [ ] Cloud Run `/health` shows `environment=production` and healthy DB
- [ ] Cloud Scheduler jobs exist and at least one manual run succeeded
- [ ] Rollback path known: restore `DATABASE_URL` from secret `RENDER_DATABASE_URL`

## Cutover checklist

1. **Point users at Firebase**
   - Share / bookmark https://seventh-country-232522.web.app (or custom domain later)
   - Optionally set Auth0 Application Login URI to the Firebase URL
2. **Freeze Render writes** (or put Render API in maintenance) once Cloud Run is primary
3. **Turn off Render web service** (keep Postgres warm for N days)
4. **Archive / delete the Vercel project** after Firebase is verified
5. **Remove Vercel URLs from Auth0** (keep Firebase + localhost)
6. **After soak (recommend ≥7 days): delete Render Postgres**
7. Leave **Auth0** as-is (design decision D4)

## Rollback (if needed during soak)

```bash
# Point Cloud Run back at Render Postgres
printf '%s' "$(gcloud secrets versions access latest --secret=RENDER_DATABASE_URL)" \
  | gcloud secrets versions add DATABASE_URL --data-file=-
gcloud run services update wolf-goat-pig-api --region=us-central1 \
  --update-secrets=DATABASE_URL=DATABASE_URL:latest
```

Users can keep using Vercel → Render until you are ready; nothing here is irreversible
until Render Postgres is deleted.
