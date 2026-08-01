# Google Sheets Sync

Wolf Goat Pig syncs leaderboard data with a Google Sheet over CSV — no Google API
credentials required. This is the canonical guide: how it works, how to trigger a
sync, how to verify it, and how to push data back to a sheet.

- **Pull** (sheet → app): import player data from the Google Sheet into PostgreSQL,
  surfaced via the leaderboard API and frontend.
- **Push** (app → sheet): an optional Apps Script writes the live leaderboard back
  into a sheet tab.

**Default sheet:** `https://docs.google.com/spreadsheets/d/141s8V_UACdBc8Xg17W0UhWxd08BMbEImkXOSPa66RfQ`

> **Scheduling.** Sheet → DB sync runs every 2 hours via `.github/workflows/sheet-sync.yml`
> against the Cloud Run API. In-process schedulers are disabled in production
> (`RUN_INPROCESS_SCHEDULERS=false`). The admin UI / API sync remains available
> for an immediate refresh.

## How it works

```
Google Sheet (public CSV)
        ↓  POST /sheet-integration/sync-wgp-sheet
Backend parses CSV → transforms → aggregates per player
        ↓
PostgreSQL (PlayerProfile, PlayerStatistics)
        ↓  GET /leaderboard/*
Frontend leaderboard
```

**Sheet requirements:** publicly viewable ("Anyone with link can view"), a header
row (e.g. `Member`, `Score`), player names in the first column, numeric score
columns, and no merged cells / summary rows inside the data range.

## Triggering a sync

### 1. Admin UI (recommended)

`/admin` → **📊 Sheets Integration** tab → **Sync Now**. Admin sync bypasses rate
limiting (it sends `X-Scheduled-Job: true`) and shows detailed results: players
processed / created / updated, the synced names, sample stats, and a timestamp.
Use **View Leaderboard** to confirm. There is also a `/live-sync` page with a
preview table and optional auto-sync interval.

### 2. API

```bash
curl -X POST https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app/sheet-integration/sync-wgp-sheet \
  -H "Content-Type: application/json" \
  -H "X-Scheduled-Job: true" \
  -d '{"csv_url":"https://docs.google.com/spreadsheets/d/141s8V_UACdBc8Xg17W0UhWxd08BMbEImkXOSPa66RfQ/export?format=csv&gid=0"}'
```

The `X-Scheduled-Job: true` header bypasses the one-sync-per-hour rate limit on
the public endpoint. The response includes `sync_results`
(`players_processed`, `players_created`, `players_updated`, `errors`),
`player_count`, `synced_at`, and `players_synced`.

### 3. Test script

```bash
./scripts/deployment/test-production-sync.sh
```

## Verifying a sync

```bash
# Backend up? (environment must read "production")
curl https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app/health

# Data present?
curl https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app/leaderboard/total_earnings
```

Expected leaderboard shape:

```json
{
  "leaderboard": [
    {"rank": 1, "player_name": "Brett Saks", "value": 1804.0}
  ],
  "leaderboard_type": "total_earnings",
  "player_count": 10,
  "last_updated": "..."
}
```

In Cloud Run logs, a successful sync looks like:
`Sheet sync completed: {'players_processed': 10, 'players_created': 0, 'players_updated': 10}`.

## Using the sync from the frontend

State lives in `SheetSyncContext`; the UI is `GoogleSheetsLiveSync`.

```javascript
import { useSheetSync } from './context';

function SyncButton() {
  const { performLiveSync, syncStatus, syncData, error } = useSheetSync();
  // syncStatus: 'idle' | 'connecting' | 'syncing' | 'success' | 'error'
  return (
    <button onClick={performLiveSync} disabled={syncStatus === 'syncing'}>
      {syncStatus === 'syncing' ? 'Syncing…' : 'Sync Now'}
    </button>
  );
}
```

Direct API call (no context):

```javascript
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const csvUrl = "https://docs.google.com/spreadsheets/d/141s8V_UACdBc8Xg17W0UhWxd08BMbEImkXOSPa66RfQ/export?format=csv&gid=0";
const res = await fetch(`${API_URL}/sheet-integration/sync-wgp-sheet`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ csv_url: csvUrl }),
});
const result = await res.json(); // { sync_results, player_count, synced_at, players_synced }
```

A Playwright smoke test lives at `scripts/diagnostics/test_google_sheets_live_sync.js`.

## Push: write the leaderboard back to a sheet (optional)

To display the live leaderboard inside a Google Sheet, install an Apps Script that
pulls from the API. In the sheet: **Extensions → Apps Script**, paste the script
below, save, and run `testAPIConnection` once to grant permissions.

```javascript
const API_URL = 'https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app';
const LEADERBOARD_SHEET_NAME = 'Leaderboard';
const LEADERBOARD_TYPE = 'total_earnings';
// types: total_earnings | win_rate | games_played | average_score | partnerships_won

function onOpen() {
  SpreadsheetApp.getUi().createMenu('🏆 WGP Leaderboard')
    .addItem('🔄 Refresh Leaderboard', 'refreshLeaderboard')
    .addToUi();
}

function fetchLeaderboardData() {
  const res = UrlFetchApp.fetch(`${API_URL}/leaderboard/${LEADERBOARD_TYPE}`, {
    method: 'get', contentType: 'application/json', muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) {
    throw new Error(`API ${res.getResponseCode()}: ${res.getContentText()}`);
  }
  return JSON.parse(res.getContentText());
}

function refreshLeaderboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(LEADERBOARD_SHEET_NAME) || ss.insertSheet(LEADERBOARD_SHEET_NAME);
  const data = fetchLeaderboardData();
  if (!data || !data.leaderboard) return;

  const last = sheet.getLastRow();
  if (last > 1) sheet.getRange(2, 1, last - 1, sheet.getLastColumn()).clearContent();
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, 4).setValues([['Rank', 'Player Name', 'Total Earnings', 'Last Updated']])
      .setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  const rows = data.leaderboard.map(p => [p.rank, p.player_name, `$${p.value.toFixed(2)}`, new Date()]);
  if (rows.length) {
    sheet.getRange(2, 1, rows.length, 4).setValues(rows);
    sheet.getRange(2, 3, rows.length, 1).setNumberFormat('$#,##0.00');
    sheet.autoResizeColumns(1, 4);
  }
}

function testAPIConnection() {
  const data = fetchLeaderboardData();
  Logger.log(data && data.leaderboard ? `OK: ${data.leaderboard.length} players` : 'Failed');
}
```

For automatic push, add a time-driven trigger for `refreshLeaderboard` in the Apps
Script *Triggers* panel (e.g. every 6 hours).

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Backend not responding | Cloud Run cold start or revision failure | Check Cloud Run status and logs |
| Empty leaderboard | No sync has run | Trigger a manual sync (admin UI / API) |
| "Rate limit exceeded" | One sync/hour on public endpoint | Send `X-Scheduled-Job: true`, or wait |
| CORS error in console | Wrong `VITE_API_URL` | Fix the GitHub Actions variable and redeploy Firebase |
| Some players skipped | Summary rows / non-numeric scores / stray spaces | Clean the sheet data |
| "Invalid Google Sheets URL" | Wrong URL form | Use `.../d/SHEET_ID/edit` (full `https://`) |

Verify the sheet's CSV export is reachable (incognito):
`https://docs.google.com/spreadsheets/d/SHEET_ID/export?format=csv&gid=0`

## Key files

```
backend/app/routers/sheet_integration.py            ← API endpoints
backend/app/services/sheet_integration_service.py   ← CSV parse + transform
backend/app/services/email_scheduler.py             ← job implementations invoked by Cloud Scheduler
frontend/src/context/SheetSyncContext.js            ← sync state
frontend/src/components/GoogleSheetsLiveSync.js     ← sync UI
frontend/src/components/Leaderboard.js              ← display
```
