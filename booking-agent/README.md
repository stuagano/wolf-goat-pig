# ForeTees booking agent (Gemini Computer Use)

Python FastAPI service that books/cancels Wingpoint ForeTees tee times using
Vertex Gemini Computer Use + local Playwright Chromium.

See [`docs/architecture/COMPUTER_USE_BOOKING.md`](../docs/architecture/COMPUTER_USE_BOOKING.md)
and [`deploy/gcp/phase7-booking/README.md`](../deploy/gcp/phase7-booking/README.md).

## Local run

```bash
cd booking-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
export GCP_PROJECT_ID=seventh-country-232522
export BOOKING_SERVICE_SECRET=dev-secret
# ADC: gcloud auth application-default login
uvicorn app.main:app --reload --port 8080
```

## Endpoints

- `GET /health`
- `POST /book` — start book job (Bearer `BOOKING_SERVICE_SECRET`)
- `POST /cancel` — start cancel job
- `POST /jobs/{job_id}/confirm` — `{ "confirm": true|false }`
