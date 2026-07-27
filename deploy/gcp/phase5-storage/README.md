# Phase 5 — Cloud Storage (avatars)

Private GCS bucket for uploaded profile photos. Scorecard scans are **not**
persisted here (ephemeral OCR only).

## Provision

```bash
source deploy/gcp/config.env
bash deploy/gcp/phase5-storage/10-provision-media-bucket.sh
```

Creates `gs://wgp-media-${GCP_PROJECT_ID}` (private, uniform access) and grants
`roles/storage.objectAdmin` to `wgp-run`.

## App wiring

- Env: `MEDIA_BUCKET=wgp-media-seventh-country-232522` on Cloud Run
  (`phase1-cloud-run/env.production.yaml`)
- Upload: `POST /players/me/avatar` → `gs://…/avatars/{id}.jpg`, sets
  `avatar_url=gcs:avatars/{id}.jpg`, clears DB `avatar_image`
- Serve: `GET /players/{id}/avatar` still proxies JPEG bytes (frontend unchanged)
- Without `MEDIA_BUCKET`, behavior falls back to the old base64 DB blob

## Migrate existing DB blobs

```bash
cd backend && source venv/bin/activate
pip install -r requirements.txt
export MEDIA_BUCKET=wgp-media-seventh-country-232522
# Point DATABASE_URL at Cloud SQL (proxy) or Render
python scripts/migrate_avatars_to_gcs.py
```
