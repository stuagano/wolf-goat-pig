# Scorecard Vision Agent

Vertex Gemini multimodal extraction for Wolf Goat Pig scorecard photos.
Runs as a separate Cloud Run service (`wgp-scorecard`) so the main API can
delegate vision work off Groq and stay on GCP.

## Flow

1. OpenCV preprocess (deskew → grid crop → circle annotation)
2. Vertex Gemini multimodal read (few-shot reference cards)
3. Zero-sum validation with up to 2 correction passes on bad holes

## Local dev

```bash
cd scorecard-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-testing.txt
export GCP_PROJECT_ID=seventh-country-232522
export GCP_LOCATION=global
export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/application_default_credentials.json
uvicorn app.main:app --reload --port 8081
```

```bash
curl -sS -X POST http://localhost:8081/scan \
  -F "file=@../backend/tests/live/data/your-card.jpg"
```

## Deploy

See `deploy/gcp/phase8-scorecard/README.md`.

After deploy, set on `wolf-goat-pig-api`:

- `SCORECARD_SERVICE_URL` — Cloud Run URL for `wgp-scorecard`
- `SCORECARD_VISION_PROVIDER=agent`
- `SCORECARD_SERVICE_SECRET` — same value as Secret Manager secret

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `GCP_PROJECT_ID` | `seventh-country-232522` | Vertex project |
| `GCP_LOCATION` | `global` | Vertex region |
| `SCORECARD_VISION_MODEL` | `gemini-2.5-flash` | Multimodal model |
| `SCORECARD_SERVICE_SECRET` | (empty) | Bearer auth from main API |
| `SCORECARD_MAX_CORRECTION_PASSES` | `2` | Zero-sum retry budget |
| `SCORECARD_SKIP_REFERENCE_EXAMPLES` | `0` | Set `1` to skip few-shot refs |
