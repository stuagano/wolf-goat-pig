# Frontend Google Sheets Sync Testing Guide

## Quick Access

Your app already has Google Sheets reading fully integrated! Here's how to use it:

### 1. Access the Live Sync Interface

**Local Development:**
```
http://localhost:3000/live-sync
```

**Production (Vercel):**
```
https://your-vercel-app.vercel.app/live-sync
```

### 2. Using the Sync Interface

The `GoogleSheetsLiveSync` component provides a user-friendly interface:

**Features:**
- ✅ Pre-configured with your Google Sheet URL
- ✅ Manual "Sync Now" button
- ✅ Optional auto-sync (configurable intervals: 10s, 30s, 1m, 5m)
- ✅ Real-time sync status (connecting → syncing → success/error)
- ✅ Data preview table (shows first 5 rows)
- ✅ Last sync timestamp
- ✅ Error messages if sync fails

**Default Sheet URL:**
```
https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/edit
```

### 3. Viewing Synced Data

After syncing, navigate to the leaderboard to see the data:

**Local:**
```
http://localhost:3000/leaderboard
```

**Production:**
```
https://your-vercel-app.vercel.app/leaderboard
```

---

## Component Usage

If you want to use the sync functionality in your own components:

### Using SheetSyncContext Hook

```javascript
import { useSheetSync } from './context';

function MyComponent() {
  const {
    sheetUrl,           // Current Google Sheet URL
    setSheetUrl,        // Update sheet URL
    syncStatus,         // 'idle' | 'connecting' | 'syncing' | 'error' | 'success'
    lastSync,           // Date of last sync
    syncData,           // Array of synced player data
    error,              // Error message (if any)
    performLiveSync,    // Function to trigger sync
    autoSync,           // Boolean: is auto-sync enabled?
    setAutoSync,        // Enable/disable auto-sync
    syncInterval,       // Auto-sync interval (seconds)
    setSyncInterval     // Update auto-sync interval
  } = useSheetSync();

  const handleSync = () => {
    performLiveSync();
  };

  return (
    <div>
      <button onClick={handleSync} disabled={syncStatus === 'syncing'}>
        {syncStatus === 'syncing' ? 'Syncing...' : 'Sync Now'}
      </button>

      {syncStatus === 'success' && (
        <p>✅ Sync successful! {syncData.length} players loaded</p>
      )}

      {syncStatus === 'error' && (
        <p>❌ Error: {error}</p>
      )}

      {syncData.length > 0 && (
        <ul>
          {syncData.map(player => (
            <li key={player.id}>
              {player.player_name}: ${player.total_earnings}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### Direct API Call (Without Context)

```javascript
async function syncGoogleSheet() {
  const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
  const csvUrl = "https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=0";

  try {
    const response = await fetch(`${API_URL}/sheet-integration/sync-wgp-sheet`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ csv_url: csvUrl })
    });

    if (!response.ok) {
      throw new Error(`Sync failed: ${response.statusText}`);
    }

    const result = await response.json();
    console.log('Sync results:', result);

    // result contains:
    // - sync_results: { players_processed, players_created, players_updated, errors }
    // - player_count: number
    // - synced_at: timestamp
    // - players_synced: array of player names

    return result;
  } catch (error) {
    console.error('Sync error:', error);
    throw error;
  }
}
```

---

## Testing Scenarios

### Scenario 1: First-Time Sync

**Steps:**
1. Navigate to `/live-sync`
2. Click "Sync Now"
3. Watch status: idle → connecting → syncing → success
4. Verify data preview table appears
5. Navigate to `/leaderboard`
6. Confirm players appear with correct scores

**Expected:**
- All players from Google Sheet appear
- Scores match sheet data
- No error messages

### Scenario 2: Re-Sync (Update Data)

**Steps:**
1. Update player scores in Google Sheet
2. Navigate to `/live-sync`
3. Click "Sync Now"
4. Navigate to `/leaderboard`
5. Confirm updated scores

**Expected:**
- Updated scores reflect in leaderboard
- Player rankings adjust accordingly
- Last sync timestamp updates

### Scenario 3: Auto-Sync

**Steps:**
1. Navigate to `/live-sync`
2. Check "Enable Auto Sync"
3. Set interval to "30 seconds"
4. Wait 30 seconds
5. Observe automatic sync

**Expected:**
- Sync triggers automatically every 30 seconds
- Status updates without user interaction
- Data refreshes in background

### Scenario 4: Error Handling

**Steps:**
1. Modify sheet URL to invalid URL
2. Click "Sync Now"
3. Observe error handling

**Expected:**
- Status changes to 'error'
- Error message displays
- No crash or blank screen

### Scenario 5: Rate Limiting

**Steps:**
1. Trigger manual sync
2. Immediately trigger another sync
3. Observe rate limit message

**Expected:**
- Second sync is blocked (rate limited)
- Error message: "Rate limit: once per hour"
- Can bypass with scheduled job header (backend only)

---

## Browser Testing

### Manual Testing Steps

**1. Open Browser DevTools (F12)**

**2. Navigate to `/live-sync`**

**3. Click "Sync Now" and observe:**

**Console Output:**
```javascript
// Should see:
performLiveSync called with: {...}
Leaderboard data transformed: {
  headers: [...],
  rowCount: 50,
  playersFound: 10,
  sampleData: [...]
}
```

**Network Tab:**
```
POST /sheet-integration/sync-wgp-sheet
Status: 200 OK
Response: {
  "sync_results": {...},
  "player_count": 10,
  ...
}
```

**React DevTools (if installed):**
```
SheetSyncContext:
  syncStatus: "success"
  syncData: Array(10)
  lastSync: Date
```

### Automated Testing (Playwright)

A test already exists at:
```
scripts/diagnostics/test_google_sheets_live_sync.js
```

**Run it:**
```bash
node scripts/diagnostics/test_google_sheets_live_sync.js
```

**What it tests:**
- ✅ Component renders
- ✅ Sync button is present
- ✅ Sheet URL input exists
- ✅ Sync functionality works
- ✅ Status updates correctly

---

## Environment Configuration

### Local Development

**frontend/.env.local:**
```env
REACT_APP_API_URL=http://localhost:8000
```

**Start backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Start frontend:**
```bash
cd frontend
npm start
```

**Access:**
```
http://localhost:3000/live-sync
```

### Production (Vercel)

**Environment Variable (Vercel Dashboard):**
```
REACT_APP_API_URL=https://wolf-goat-pig.onrender.com
```

**Verify in `vercel.json`:**
```json
{
  "env": {
    "REACT_APP_API_URL": "https://wolf-goat-pig.onrender.com"
  }
}
```

---

## Troubleshooting

### Issue: "Sync Now" button does nothing

**Check:**
1. Browser console for errors
2. Network tab for failed requests
3. API_URL environment variable

**Solution:**
```javascript
// In browser console:
console.log(process.env.REACT_APP_API_URL);
// Should output: "http://localhost:8000" or production URL
```

### Issue: Data syncs but doesn't appear in leaderboard

**Check:**
1. Navigate directly to leaderboard API:
   ```
   http://localhost:8000/leaderboard/total_earnings
   ```
2. Verify data is in database

**Solution:**
- Clear browser cache
- Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
- Check leaderboard component is fetching latest data

### Issue: CORS errors in console

**Error:**
```
Access to fetch at 'http://localhost:8000/...' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**Solution:**
Backend should have CORS configured in `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-vercel-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "Invalid Google Sheets URL"

**Check sheet URL format:**
```
✅ https://docs.google.com/spreadsheets/d/SHEET_ID/edit
✅ https://docs.google.com/spreadsheets/d/SHEET_ID/edit?gid=0
❌ https://docs.google.com/document/...  (wrong type)
❌ docs.google.com/...  (missing https://)
```

---

## Data Verification

After sync completes, verify data integrity:

### Check Synced Data Structure

```javascript
// In browser console on /live-sync page:
const { syncData } = window.__REACT_DEVTOOLS_GLOBAL_HOOK__.renderers.get(1).getCurrentFiber().return.memoizedState;
console.table(syncData);

// Expected structure:
[
  {
    id: "player-0",
    player_name: "Brett Saks",
    total_earnings: 1804,
    games_played: 25,
    win_percentage: 68.5,
    last_played: "2024-01-10"
  },
  ...
]
```

### Check Backend Database

```bash
# Via backend API:
curl http://localhost:8000/leaderboard/total_earnings | python3 -m json.tool

# Expected: players with stats matching Google Sheet
```

---

## Performance Considerations

### Auto-Sync Intervals

**Recommendations:**
- **Development:** 30 seconds (for testing)
- **Production:** 5 minutes or disabled (use scheduled backend sync instead)

**Why?**
- Frontend auto-sync adds unnecessary API calls
- Backend scheduled sync (2 AM daily) is more efficient
- Manual sync available for immediate updates

### Rate Limiting

**Frontend rate limit:** None (unlimited manual syncs)
**Backend rate limit:** 1 sync per hour (unless scheduled job)

**To bypass rate limit (backend only):**
```javascript
fetch('/sheet-integration/sync-wgp-sheet', {
  headers: {
    'X-Scheduled-Job': 'true'  // Bypasses rate limit
  }
})
```

---

## Summary: Testing Checklist

Before deploying to production, verify:

- [ ] `/live-sync` page loads without errors
- [ ] Sheet URL is pre-filled correctly
- [ ] "Sync Now" button triggers sync
- [ ] Sync status updates (idle → connecting → syncing → success)
- [ ] Data preview table shows player data
- [ ] Last sync timestamp displays
- [ ] Navigate to `/leaderboard` shows synced data
- [ ] Player names and scores match Google Sheet
- [ ] No console errors
- [ ] No network errors (check DevTools)
- [ ] Works in both local and production environments

✅ **If all checks pass, your sync is working correctly!**
