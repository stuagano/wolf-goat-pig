# Phase 8 — Scorecard vision agent (Vertex Gemini on Cloud Run)

Moves scorecard photo extraction from inline Groq Vision to a dedicated
Cloud Run service using Vertex Gemini multimodal + OpenCV preprocessing.

## Deploy

**Auto on push to `main`** when `GCP_AUTO_DEPLOY=true` and `scorecard-agent/**`
(or this directory / `cloudbuild-scorecard.yaml`) changes.

Manual:

```bash
source deploy/gcp/config.env
./deploy/gcp/phase8-scorecard/10-deploy.sh
```

Or **Actions → Deploy to GCP → Run workflow** with `deploy_scorecard = true`.

Then point the main API at the new service:

```bash
gcloud run services update wolf-goat-pig-api --region=us-central1 \
  --update-env-vars=SCORECARD_SERVICE_URL=https://wgp-scorecard-….run.app,SCORECARD_VISION_PROVIDER=agent
```

Or set those keys in `phase1-cloud-run/env.production.yaml` and redeploy the API.

## Requirements

- Vertex AI API enabled (`aiplatform.googleapis.com`)
- Runtime SA `wgp-run` needs `roles/aiplatform.user` (same as booking agent)
- Secret `SCORECARD_SERVICE_SECRET` in Secret Manager (Bearer auth from main API)

## Verify

```bash
curl -sS "$SCORECARD_URL/health"
# Upload a test card:
curl -sS -X POST "$SCORECARD_URL/scan" \
  -H "Authorization: Bearer $SCORECARD_SERVICE_SECRET" \
  -F "file=@path/to/scorecard.jpg"
```

## Cutover

1. Deploy `wgp-scorecard`, smoke `/health` and one `/scan`.
2. Set `SCORECARD_SERVICE_URL` + `SCORECARD_VISION_PROVIDER=agent` on `wolf-goat-pig-api`.
3. Scan a real card in the app and confirm review screen populates.
4. Keep `GROQ_API_KEY` until you're confident — flip provider back to `groq` to rollback.
