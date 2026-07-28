# Phase 7 — ForeTees booking agent (Computer Use)

Moves tee-time book/cancel from Render Node/Playwright
(`wolf-goat-pig-booking`) to a GCP Cloud Run service driven by Gemini
Computer Use. Design: [`docs/architecture/COMPUTER_USE_BOOKING.md`](../../../docs/architecture/COMPUTER_USE_BOOKING.md).

## Deploy

**Auto on push to `main`** when `GCP_AUTO_DEPLOY=true` and `booking-agent/**`
(or this directory / `cloudbuild-booking.yaml`) changes.

Manual:

```bash
source deploy/gcp/config.env
./deploy/gcp/phase7-booking/10-deploy.sh
```

Or **Actions → Deploy to GCP → Run workflow** with `deploy_booking = true`
(uses `deploy/gcp/cloudbuild-booking.yaml`).

Then point the main API at the new service (already set in
`phase1-cloud-run/env.production.yaml` for production):

```bash
# After first deploy prints the URL:
gcloud run services update wolf-goat-pig-api --region=us-central1 \
  --update-env-vars=BOOKING_SERVICE_URL=https://wgp-booking-….run.app
```

Or set `BOOKING_SERVICE_URL` in `phase1-cloud-run/env.production.yaml` and redeploy the API.

## Requirements

- Vertex AI API enabled (`aiplatform.googleapis.com`) — Phase 0 already enables
  core APIs; this script enables Vertex if missing.
- Runtime SA `wgp-run` needs `roles/aiplatform.user`.
- Same `BOOKING_SERVICE_SECRET` as today (Secret Manager).
- **Session affinity** is required so `/jobs/{id}/confirm` hits the instance
  holding the Playwright browser.

## Verify

```bash
curl -sS "$BOOKING_URL/health"
# From a logged-in SPA: book a tee time → expect login confirm → submit confirm.
```

## Cutover

1. Deploy `wgp-booking`, smoke `/health`.
2. Flip `BOOKING_SERVICE_URL` on `wolf-goat-pig-api`.
3. Book + cancel once in production with confirm gates.
4. Suspend Render `wolf-goat-pig-booking`.
