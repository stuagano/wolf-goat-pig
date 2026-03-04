# Quick Google Sheets Sync Reference

## TL;DR - Your Sync is Already Working! ✅

Your application **already has full Google Sheets reading integration**. Here's everything you need to know:

---

## 🚀 Quick Start

### Access the Sync UI

**Production:** `https://your-vercel-app.vercel.app/live-sync`
**Local:** `http://localhost:3000/live-sync`

### One-Button Sync

1. Click "Sync Now" button
2. Wait ~5 seconds
3. Data syncs from your Google Sheet
4. View results at `/leaderboard`

**That's it!** No configuration needed.

---

## 📊 What Gets Synced

**From:** Your Google Sheet
```
https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM
```

**To:** PostgreSQL database → Leaderboard API → Frontend

**Data:**
- Player names
- Game scores
- Total earnings
- Games played
- Win/loss records

---

## 🔄 Sync Methods

### 1. **Manual Sync (Frontend UI)**
- Navigate to `/live-sync`
- Click "Sync Now"
- Instant feedback

### 2. **Scheduled Sync (Automatic)**
- Runs daily at 2:00 AM
- No action needed
- Already configured

### 3. **API Sync (Programmatic)**
```bash
curl -X POST https://wolf-goat-pig.onrender.com/sheet-integration/sync-wgp-sheet \
  -H "Content-Type: application/json" \
  -d '{"csv_url":"https://docs.google.com/spreadsheets/d/YOUR_SHEET/export?format=csv"}'
```

---

## ✅ Verification Commands

### Quick Health Check
```bash
# Check if backend is up
curl https://wolf-goat-pig.onrender.com/health

# Check if data exists
curl https://wolf-goat-pig.onrender.com/leaderboard/total_earnings

# Run full test
./scripts/test-production-sync.sh
```

### Expected Output
```json
{
  "leaderboard": [
    {"rank": 1, "player_name": "Brett Saks", "value": 1804.0},
    {"rank": 2, "player_name": "Mike Goldsberry", "value": 1091.0},
    ...
  ],
  "player_count": 10
}
```

---

## 🎯 Key Files

### Backend
```
backend/app/routers/sheet_integration.py          ← API endpoints
backend/app/services/sheet_integration_service.py ← Data transformation
backend/app/services/email_scheduler.py           ← Scheduled sync (2 AM)
```

### Frontend
```
frontend/src/context/SheetSyncContext.js          ← State management
frontend/src/components/GoogleSheetsLiveSync.js   ← Sync UI
frontend/src/components/Leaderboard.js            ← Display data
```

---

## 🔧 Configuration

### Environment Variables

**Frontend (Vercel):**
```env
REACT_APP_API_URL=https://wolf-goat-pig.onrender.com
```

**Backend (Render.com):**
```env
DATABASE_URL=postgresql://...
```

### Google Sheet Setup

**Requirements:**
1. ✅ Sheet is publicly viewable (Share → Anyone with link can view)
2. ✅ Has proper column headers (Member, Score, etc.)
3. ✅ CSV export URL works

**Test CSV export:**
```
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv&gid=0
```

---

## 🐛 Troubleshooting

### Backend Not Responding
**Cause:** Render.com free tier cold start
**Fix:** Wait 15 seconds, retry

### No Data in Leaderboard
**Fix:** Run manual sync
```bash
./scripts/test-production-sync.sh
```

### Rate Limit Error
**Cause:** Max 1 sync per hour
**Fix:** Add header `X-Scheduled-Job: true` or wait 1 hour

### CORS Errors
**Fix:** Verify `REACT_APP_API_URL` in Vercel dashboard

---

## 📖 Documentation

**Detailed Guides:**
- `docs/PRODUCTION_SYNC_VERIFICATION.md` - Production testing
- `docs/FRONTEND_SYNC_TESTING.md` - Frontend testing
- `GOOGLE_SHEETS_LEADERBOARD_SETUP.md` - Initial setup

**Test Script:**
```bash
./scripts/test-production-sync.sh
```

---

## 🎓 Example Usage

### In React Component
```javascript
import { useSheetSync } from './context';

function MyComponent() {
  const { performLiveSync, syncData, syncStatus } = useSheetSync();

  return (
    <button onClick={performLiveSync}>
      {syncStatus === 'syncing' ? 'Syncing...' : 'Sync Now'}
    </button>
  );
}
```

### Direct API Call
```javascript
const response = await fetch(
  `${API_URL}/sheet-integration/sync-wgp-sheet`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ csv_url: '...' })
  }
);
const result = await response.json();
console.log(`Synced ${result.player_count} players`);
```

---

## ✨ Features

✅ **CSV-based** - No Google API credentials needed
✅ **Automatic data transformation** - Maps sheet columns to database fields
✅ **Player aggregation** - Combines multiple games per player
✅ **Win/loss tracking** - Auto-calculates from scores
✅ **Error handling** - Robust validation and error messages
✅ **Caching** - 1-hour cache prevents excessive API calls
✅ **Rate limiting** - Prevents abuse
✅ **Scheduled sync** - Daily automatic updates

---

## 🚨 Quick Troubleshooting Decision Tree

```
Is backend responding?
├─ No  → Wait 15s (cold start), retry
└─ Yes → Is leaderboard empty?
          ├─ Yes → Run manual sync
          └─ No  → Is data stale?
                   ├─ Yes → Check last_updated timestamp
                   └─ No  → ✅ Everything working!
```

---

## 📞 Support

**Can't find what you need?**

1. Run test script: `./scripts/test-production-sync.sh`
2. Check backend logs on Render.com dashboard
3. Check browser console for frontend errors
4. Review detailed docs in `docs/` folder

**Common Issues:**
- Backend cold start → Wait 15 seconds
- No data → Run manual sync
- CORS errors → Check environment variables
- Rate limit → Wait 1 hour or use scheduled job header

---

## ✅ Your Sync Status Checklist

Quick verification:

```bash
# All these should work:
✅ curl https://wolf-goat-pig.onrender.com/health
✅ curl https://wolf-goat-pig.onrender.com/leaderboard/total_earnings
✅ Navigate to your-app.vercel.app/live-sync
✅ Click "Sync Now" → Success
✅ Navigate to your-app.vercel.app/leaderboard → See players
```

**If all ✅ pass:** Your sync is working perfectly! 🎉

---

## 🎯 Next Steps

Your Google Sheets sync is fully functional. Here's what you might want to do next:

1. **Monitor**: Check Render.com logs occasionally
2. **Verify**: Run test script weekly
3. **Update**: Modify Google Sheet, sync, verify
4. **Enhance**: Add more metrics or visualizations

**Optional Enhancements:**
- Multiple sheet support
- Historical data tracking
- Real-time WebSocket updates
- Advanced filtering/sorting

Need help with any of these? Just ask!
