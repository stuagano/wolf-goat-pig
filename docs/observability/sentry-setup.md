# Observability (GCP-only)

> **Sentry was removed.** See this page + [uptime-setup.md](./uptime-setup.md).
> Historical filename kept so existing links in docs still resolve.

Production monitoring lives entirely in Google Cloud project
`seventh-country-232522`. There is **no third-party error SaaS** — fewer
dependencies, and anyone with GCP project access can see alerts and logs
(bus factor > 1).

| Signal | Tool | Where |
|---|---|---|
| Site / API down | Cloud Monitoring uptime | [Uptime](https://console.cloud.google.com/monitoring/uptime?project=seventh-country-232522) |
| Sustained API 5xx | Alert policy | [Alerting](https://console.cloud.google.com/monitoring/alerting?project=seventh-country-232522) |
| Scheduler job failed | Alert policy | same |
| Swallowed integration errors (GHIN, Sheets, ForeTees, email) | Cloud Logging (`report_exception` / `report_message`) | [Logs Explorer](https://console.cloud.google.com/logs?project=seventh-country-232522) |
| Frontend React crash | Browser console only (`ErrorBoundary`) | User device |

## Day-to-day failures

| User action | Alert path |
|---|---|
| Can't open the site | Uptime → email |
| Can't sign up (500) | Cloud Run 5xx policy + request logs |
| Signup works but confirmation email fails | Cloud Logging ERROR from `app.observability.report` |
| Nightly GHIN / emails / pairings fail | Scheduler failure policy |

Provision scripts: [`deploy/gcp/phase6-monitoring/`](../../deploy/gcp/phase6-monitoring/).

## Code

Silent-failure call sites use `backend/app/observability/report.py` so events
still land in Cloud Logging without an external vendor.
