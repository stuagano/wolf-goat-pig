# Phase 6 — Monitoring & alerting (GCP only)

Day-to-day user failures are handled **inside this GCP project** — no Sentry.

| Layer | Tool | What it catches | Where you look |
|---|---|---|---|
| Site / API down | Cloud Monitoring uptime | Hosting or `/health` failing | [Uptime](https://console.cloud.google.com/monitoring/uptime?project=seventh-country-232522) |
| Sustained 5xx | Alert policy | Signup/login outages returning 500 | [Alerting](https://console.cloud.google.com/monitoring/alerting?project=seventh-country-232522) |
| Reported app errors | Log-based alert | Swallowed email/GHIN/Sheets/ForeTees failures | same + Logs Explorer |
| Scheduler jobs | Alert policy | Nightly emails / GHIN / pairings | Cloud Scheduler + Alerting |

Email: `MONITOR_ALERT_EMAIL` (default `stuagano@gmail.com`). Anyone with
Monitoring Viewer/Editor on the project can manage this — bus factor > 1.

## Provision

```bash
./deploy/gcp/phase6-monitoring/10-notification-channel.sh
./deploy/gcp/phase6-monitoring/20-uptime-checks.sh
./deploy/gcp/phase6-monitoring/30-alert-policies.sh
```

## Code path for silent failures

`backend/app/observability/report.py` → Cloud Logging. Prefer Logs Explorer
filter:

```
resource.type="cloud_run_revision"
resource.labels.service_name="wolf-goat-pig-api"
severity>=ERROR
```
