# Uptime monitoring (GCP Cloud Monitoring)

Production uptime and operational alerts are **Google Cloud Monitoring** only
(no Sentry, no UptimeRobot). Scripts:
[`deploy/gcp/phase6-monitoring/`](../../deploy/gcp/phase6-monitoring/).

## What gets probed / alerted

| Check / policy | Signal | Alert if |
|---|---|---|
| `WGP API /health` | Cloud Run health | non-2xx ~2+ minutes |
| `WGP Firebase Hosting` | SPA | non-2xx ~2+ minutes |
| Cloud Run 5xx spike | Sustained 500s | 5xx for 5 minutes |
| Scheduler job failed | Cron jobs | ERROR log from Scheduler |
| Reported app error | `report_*` helpers | matching ERROR logs (email/GHIN/etc.) |

Email → `MONITOR_ALERT_EMAIL` (default `stuagano@gmail.com`).

## Provision

```bash
gcloud auth login   # needs Monitoring Admin on seventh-country-232522
./deploy/gcp/phase6-monitoring/10-notification-channel.sh
./deploy/gcp/phase6-monitoring/20-uptime-checks.sh
./deploy/gcp/phase6-monitoring/30-alert-policies.sh
```

Verify the notification channel email the first time Google asks.

## `/health/external`

Still available for manual debugging of GHIN / Sheets / ForeTees. Down services
are logged via `report_message` (Cloud Logging). `MONITOR_KEY` may stay unset
on GCP.
