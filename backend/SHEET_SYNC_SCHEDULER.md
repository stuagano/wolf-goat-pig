# Google Sheets Sync - Background Job Configuration

## Overview

The Google Sheets sync is now implemented as a **daily background job** that runs at 2:00 AM, rather than being triggered by external HTTP requests every minute.

## Architecture

### Background Scheduler
- **Location**: `backend/app/services/email_scheduler.py`
- **Schedule**: Daily at 2:00 AM
- **Method**: `_sync_google_sheets()`
- **Purpose**: Fetch historical player data from the Wolf-Goat-Pig Google Sheets leaderboard

### HTTP Endpoint (Fallback/Manual Trigger)
- **Endpoint**: `POST /sheet-integration/sync-wgp-sheet`
- **Location**: `backend/app/routers/sheet_integration.py`
- **Rate Limit**: 1 request per hour (for external calls)
- **Bypass**: Scheduled jobs with `X-Scheduled-Job: true` header bypass rate limiting

## Why This Change?

### Before
- External service was calling the sync endpoint **every minute**
- This caused:
  - Excessive rate limit 429 errors (converted to 500s before fix)
  - Unnecessary API load
  - Wasted resources for data that only needs daily updates

### After
- Sync runs **once per day** at 2:00 AM
- Benefits:
  - Minimal server load during off-peak hours
  - Historical data stays fresh (updates daily)
  - No rate limit conflicts
  - Proper separation of concerns (background job vs HTTP API)

## Configuration

### Enabling the Scheduler

The email scheduler (which includes the sheet sync job) is initialized on-demand:

```python
# In main.py startup event
POST /email/initialize-scheduler
```

Or it's automatically started if email notifications are enabled in your configuration.

### Changing the Sync Time

To change when the sync runs, edit `backend/app/services/email_scheduler.py`:

```python
# Current: Daily at 2 AM
schedule.every().day.at("02:00").do(self._sync_google_sheets)

# Examples of alternatives:
schedule.every().day.at("06:00").do(self._sync_google_sheets)  # 6 AM
schedule.every().day.at("23:00").do(self._sync_google_sheets)  # 11 PM
```

### Manual Sync Trigger

To manually trigger a sync (bypassing the 1-hour rate limit):

```bash
curl -X POST https://wolf-goat-pig.onrender.com/sheet-integration/sync-wgp-sheet \
  -H "Content-Type: application/json" \
  -H "X-Scheduled-Job: true" \
  -d '{"csv_url": "https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=0"}'
```

## Monitoring

### Check Scheduler Status

```bash
GET /email/scheduler-status
```

### Check Sync Logs

Look for these log entries:
- `Running scheduled Google Sheets sync...` - Sync job started
- `✅ Google Sheets sync completed successfully: X players synced` - Success
- `⚠️ Sheet sync rate limited - will retry tomorrow` - Rate limited (shouldn't happen for scheduled jobs)
- `❌ Sheet sync failed with status XXX` - Failed with error

## Related Files

- `backend/app/services/email_scheduler.py` - Background job scheduler
- `backend/app/routers/sheet_integration.py` - HTTP endpoint for sync
- `backend/app/middleware/rate_limiting.py` - Rate limiting middleware
- `frontend/src/context/SheetSyncContext.js` - Frontend sync context (manual trigger)

## Stopping the External Caller

If you have an external service (n8n workflow, monitoring service, etc.) calling the sync endpoint every minute, you should:

1. Disable or remove that scheduled task
2. The background job will now handle the sync automatically
3. If you need to trigger a sync manually, use the endpoint with the `X-Scheduled-Job` header

## Future Improvements

- Add configuration for sync frequency (daily, weekly, etc.)
- Add monitoring/alerting for failed syncs
- Implement webhook notifications when sync completes
- Add admin UI to manually trigger syncs
