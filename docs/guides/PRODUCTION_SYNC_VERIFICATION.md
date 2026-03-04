# Production Google Sheets Sync Verification Guide

## Overview

This guide helps you verify that Google Sheets data is syncing correctly in your production environment.

**Production URLs:**
- Backend API: `https://wolf-goat-pig.onrender.com`
- Frontend (Vercel): Check your Vercel dashboard for the URL
- Google Sheet: `https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM`

---

## Quick Verification

### Method 1: Automated Test Script

Run the provided test script:

```bash
./scripts/test-production-sync.sh
```

This script will:
1. ✅ Check backend health
2. ✅ Verify scheduler status
3. ✅ Check current leaderboard data
4. ✅ Trigger a manual sync
5. ✅ Verify updated data

### Method 2: Manual API Testing

**Step 1: Check Backend Health**
```bash
curl https://wolf-goat-pig.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Step 2: Check Leaderboard Data**
```bash
curl https://wolf-goat-pig.onrender.com/leaderboard/total_earnings
```

Expected response:
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "player_name": "Brett Saks",
      "value": 1804.0,
      ...
    },
    ...
  ],
  "leaderboard_type": "total_earnings",
  "player_count": 10,
  "last_updated": "2025-01-11T..."
}
```

**Step 3: Trigger Manual Sync**
```bash
curl -X POST https://wolf-goat-pig.onrender.com/sheet-integration/sync-wgp-sheet \
  -H "Content-Type: application/json" \
  -H "X-Scheduled-Job: true" \
  -d '{"csv_url":"https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=0"}'
```

Expected response:
```json
{
  "sync_results": {
    "players_processed": 10,
    "players_created": 2,
    "players_updated": 8,
    "errors": []
  },
  "player_count": 10,
  "synced_at": "2025-01-11T...",
  "players_synced": ["Brett Saks", "Mike Goldsberry", ...]
}
```

### Method 3: Frontend UI Testing

1. **Navigate to Live Sync Page:**
   ```
   https://your-vercel-app.vercel.app/live-sync
   ```

2. **The sheet URL should be pre-filled:**
   ```
   https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/edit
   ```

3. **Click "Sync Now" button**

4. **Expected behavior:**
   - Status changes: idle → connecting → syncing → success
   - Last sync timestamp updates
   - Preview table shows player data
   - No errors displayed

4. **Navigate to Leaderboard:**
   ```
   https://your-vercel-app.vercel.app/leaderboard
   ```

5. **Verify:**
   - Player names from Google Sheet appear
   - Scores match the sheet data
   - Rankings are correct

---

## Scheduled Sync Verification

### Check Scheduler Status

```bash
curl https://wolf-goat-pig.onrender.com/email/scheduler-status
```

Expected response:
```json
{
  "initialized": true,
  "running": true,
  "message": "Scheduler running"
}
```

### Scheduled Sync Details

**Schedule:** Daily at 2:00 AM (configured in `backend/app/services/email_scheduler.py`)

**What it does:**
1. Fetches CSV data from Google Sheet
2. Parses player data (name, scores, games)
3. Creates/updates player profiles in database
4. Updates player statistics
5. Calculates aggregated metrics (total earnings, win rate, etc.)

**To verify scheduled sync ran:**
```bash
# Check leaderboard last_updated timestamp
curl -s https://wolf-goat-pig.onrender.com/leaderboard/total_earnings | grep last_updated
```

---

## Troubleshooting

### Issue: Backend Returns 503 or No Response

**Cause:** Render.com free tier spins down after inactivity

**Solution:**
1. Wait 15-30 seconds for cold start
2. Retry the request
3. Backend will stay warm for ~15 minutes after first request

**Test command:**
```bash
# Wait for warmup
curl https://wolf-goat-pig.onrender.com/health
sleep 15
curl https://wolf-goat-pig.onrender.com/health
```

### Issue: Leaderboard Shows No Players

**Possible causes:**
1. Initial sync hasn't run yet
2. Google Sheet is empty or improperly formatted
3. Database connection issue

**Solution:**
```bash
# Trigger manual sync
curl -X POST https://wolf-goat-pig.onrender.com/sheet-integration/sync-wgp-sheet \
  -H "Content-Type: application/json" \
  -H "X-Scheduled-Job: true" \
  -d '{"csv_url":"https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=0"}'

# Wait 5 seconds, then check leaderboard
sleep 5
curl https://wolf-goat-pig.onrender.com/leaderboard/total_earnings
```

### Issue: "Rate Limit Exceeded" Error

**Cause:** Sync endpoint is rate-limited to once per hour (prevents abuse)

**Solution:**
1. Use `X-Scheduled-Job: true` header to bypass rate limit
2. Or wait 1 hour between manual syncs

**Bypass command:**
```bash
curl -X POST https://wolf-goat-pig.onrender.com/sheet-integration/sync-wgp-sheet \
  -H "Content-Type: application/json" \
  -H "X-Scheduled-Job: true" \
  -d '{"csv_url":"..."}'
```

### Issue: Frontend Shows "Sync Failed"

**Check browser console for errors:**
```javascript
// Open browser DevTools (F12) and look for:
// - CORS errors
// - Network errors (500, 404, etc.)
// - API_URL configuration issues
```

**Verify environment variable:**
```bash
# In Vercel dashboard, check:
REACT_APP_API_URL = https://wolf-goat-pig.onrender.com
```

### Issue: Data Not Updating from Sheet

**Verify Google Sheet is accessible:**
1. Open sheet in browser (logged out/incognito mode)
2. Try CSV export URL:
   ```
   https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=0
   ```
3. Should download CSV file with player data

**Check sheet format:**
- First row should contain headers (Member, Score, etc.)
- Player names in first column
- Numeric scores in appropriate columns
- No merged cells in data rows

---

## Integration Points

### Backend Files
- `backend/app/routers/sheet_integration.py` - API endpoints
- `backend/app/services/sheet_integration_service.py` - Data transformation
- `backend/app/services/email_scheduler.py` - Scheduled sync (2 AM daily)

### Frontend Files
- `frontend/src/context/SheetSyncContext.js` - Sync state management
- `frontend/src/components/GoogleSheetsLiveSync.js` - Sync UI
- `frontend/src/components/Leaderboard.js` - Display synced data

### Key Environment Variables
- `REACT_APP_API_URL` - Frontend API URL (set in Vercel)
- `DATABASE_URL` - PostgreSQL connection (set in Render.com)

---

## Data Flow Diagram

```
Google Sheet (Public CSV)
         ↓
Backend API (/sheet-integration/sync-wgp-sheet)
         ↓
Parse CSV → Transform Data
         ↓
PostgreSQL Database
    (PlayerProfile, PlayerStatistics tables)
         ↓
Leaderboard API (/leaderboard/*)
         ↓
Frontend (React Components)
         ↓
User sees updated leaderboard
```

---

## Expected Sync Results

After successful sync, you should see:

**In Database:**
- 10+ player profiles created/updated
- Statistics records for each player
- Aggregated metrics (total earnings, games played, win rate)

**In Leaderboard API:**
```json
{
  "leaderboard": [
    {"rank": 1, "player_name": "Brett Saks", "value": 1804.0},
    {"rank": 2, "player_name": "Mike Goldsberry", "value": 1091.0},
    {"rank": 3, "player_name": "Steve Sutorius", "value": 1001.0},
    ...
  ],
  "player_count": 10,
  "last_updated": "..."
}
```

**In Frontend:**
- Leaderboard page shows all players
- Scores match Google Sheet
- Rankings are correct
- Last sync time is recent (< 24 hours)

---

## Monitoring & Maintenance

### Daily Checks

**Automated:**
- Scheduled sync runs at 2:00 AM daily
- No manual intervention needed

**Manual verification (weekly):**
```bash
# Run the test script
./scripts/test-production-sync.sh

# Or quick check:
curl https://wolf-goat-pig.onrender.com/leaderboard/total_earnings | \
  grep -E "player_count|last_updated"
```

### Log Monitoring

**Render.com Backend Logs:**
1. Go to Render.com dashboard
2. Select "wolf-goat-pig" service
3. Click "Logs" tab
4. Search for: "Sheet sync" or "Synced"

**Expected log entries:**
```
INFO: Synced 10 players from sheet
INFO: Sheet sync completed: {'players_processed': 10, 'players_created': 0, 'players_updated': 10}
```

---

## Support & Additional Resources

**Documentation:**
- [GOOGLE_SHEETS_LEADERBOARD_SETUP.md](../GOOGLE_SHEETS_LEADERBOARD_SETUP.md) - Setup guide
- [Backend API Docs](https://wolf-goat-pig.onrender.com/docs) - Interactive API documentation

**Quick Links:**
- Backend Health: https://wolf-goat-pig.onrender.com/health
- Leaderboard API: https://wolf-goat-pig.onrender.com/leaderboard/total_earnings
- Scheduler Status: https://wolf-goat-pig.onrender.com/email/scheduler-status

**Test Script:**
```bash
./scripts/test-production-sync.sh
```

---

## Summary Checklist

Use this checklist to verify sync is working:

- [ ] Backend responds to `/health` endpoint
- [ ] Scheduler status shows `"running": true`
- [ ] Leaderboard API returns player data
- [ ] Manual sync completes successfully (no errors)
- [ ] Player count matches expected number (~10 players)
- [ ] Frontend `/live-sync` page can trigger sync
- [ ] Frontend `/leaderboard` page displays data
- [ ] Last sync timestamp is recent (< 24 hours)
- [ ] Google Sheet CSV URL is accessible
- [ ] No errors in browser console or backend logs

✅ **If all items are checked, your sync is working correctly!**
