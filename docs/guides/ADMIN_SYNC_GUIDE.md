# Admin Google Sheets Sync Guide

## Quick Access

Navigate to the Admin page and click on the "📊 Sheets Integration" tab to access the Google Sheets sync functionality.

**URL:** `/admin` → "Sheets Integration" tab

---

## 🚀 One-Click Sync Button

At the top of the Sheets Integration page, you'll see a prominent blue card with a "🚀 Sync Now" button.

### What It Does

Clicking this button will:
1. Connect to your Google Sheet
2. Fetch all player data (CSV export)
3. Parse and validate the data
4. Update the database with player statistics
5. Show detailed results

### Features

✅ **Instant sync** - No file upload needed
✅ **Bypasses rate limiting** - Admin sync uses `X-Scheduled-Job: true` header
✅ **Detailed results** - Shows exactly what was synced
✅ **Error handling** - Clear error messages if something fails
✅ **Last sync timestamp** - Track when data was last updated

---

## 📊 Sync Results Tab

After clicking "Sync Now", you'll automatically be taken to the **Sync Results** tab, which shows:

### Summary Cards
- **Players Processed** - Total number of players synced
- **Players Created** - New players added to database
- **Players Updated** - Existing players with updated stats
- **Total Players** - Current player count in system

### Detailed Information
- **Synced Players** - List of all player names that were synced
- **Sample Data** - Preview of first 3 players with their stats:
  - Quarters (total score)
  - Average score per game
  - Number of rounds played
  - Total earnings

- **Sync Information**
  - Timestamp of when sync occurred
  - Column headers found in the sheet
  - GHIN data (if available)

### Action Buttons
- **View Leaderboard** - Navigate to leaderboard to see updated data
- **Sync Again** - Trigger another sync immediately

---

## 🎯 How to Use

### Step-by-Step Instructions

1. **Navigate to Admin Page**
   ```
   Go to: /admin
   ```

2. **Click "📊 Sheets Integration" Tab**
   - Located in the top navigation of the admin page

3. **Click "🚀 Sync Now" Button**
   - Large blue button at the top of the page
   - Wait for sync to complete (~5-10 seconds)

4. **Review Results**
   - Automatically switches to "Sync Results" tab
   - Shows summary cards and detailed information
   - Success popup will appear with summary

5. **Verify Data**
   - Click "View Leaderboard" button
   - Or navigate to `/leaderboard`
   - Confirm player data is updated

---

## 💡 When to Use

### Recommended Use Cases

**Immediate Updates:**
- After updating player scores in Google Sheet
- Before starting a new game/round
- When players notice data is out of sync
- After adding new players to the sheet

**Regular Maintenance:**
- Weekly data verification
- Monthly data audit
- Before important events or tournaments

**Troubleshooting:**
- When leaderboard shows stale data
- After Google Sheet restructure
- To verify scheduled sync is working

---

## ⚠️ Important Notes

### Rate Limiting
- **Admin sync bypasses rate limiting** - You can sync as often as needed
- Regular API sync (non-admin) is limited to once per hour
- Scheduled sync runs daily at 2:00 AM automatically

### Data Safety
- Sync is **read-only** from Google Sheets
- Database is updated, not overwritten
- Existing player data is preserved and updated
- New players are added if not found

### Sheet Requirements
- Sheet must be publicly viewable
- CSV export must be enabled
- Column headers must be present
- Player names must be in first column

---

## 🔧 Troubleshooting

### Issue: "Sync Failed" Error

**Possible Causes:**
1. Backend is down or cold starting
2. Google Sheet is not accessible
3. Sheet format has changed

**Solutions:**
1. Wait 15 seconds and try again (cold start)
2. Verify sheet URL is accessible:
   ```
   https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=0
   ```
3. Check sheet permissions (must be "Anyone with link can view")

### Issue: Some Players Not Syncing

**Check:**
1. Player names in sheet match format (no extra spaces)
2. Rows are not summary rows (like "Total", "Average")
3. Score values are numeric (not text)

**Fix:**
- Clean up sheet data
- Remove summary rows from data section
- Ensure numeric columns contain only numbers

### Issue: Outdated Data Still Showing

**Solutions:**
1. Click "Sync Again" to force refresh
2. Clear browser cache and reload leaderboard
3. Check "Last synced" timestamp on admin page

### Issue: No Results After Sync

**Verify:**
1. Check browser console for JavaScript errors (F12)
2. Verify `REACT_APP_API_URL` environment variable is set correctly
3. Check backend logs on Render.com dashboard

---

## 📈 Monitoring Sync Health

### Check Sync Status

**In Admin UI:**
- Green "✅ Last synced" message appears after successful sync
- Shows timestamp of most recent sync

**Via API:**
```bash
curl https://wolf-goat-pig.onrender.com/leaderboard/total_earnings
# Check "last_updated" field in response
```

**Via Backend Logs:**
1. Go to Render.com dashboard
2. Select wolf-goat-pig service
3. Click "Logs" tab
4. Search for: "Sheet sync completed"

---

## 🎨 UI Features

### Visual Feedback

**Sync Button States:**
- **Default:** "🚀 Sync Now" (blue, clickable)
- **Loading:** "⏳ Syncing..." (animated spinner, disabled)
- **Success:** Popup alert + results tab opens
- **Error:** Red error message + popup alert

**Color-Coded Results:**
- 🔵 **Blue** - Players processed (total)
- 🟢 **Green** - Players created (new)
- 🟡 **Yellow** - Players updated (existing)
- 🟣 **Purple** - Total players (count)

---

## 🔄 Alternative Sync Methods

If the admin button doesn't work, you have other options:

### 1. Frontend Live Sync Page
```
Navigate to: /live-sync
Click "Sync Now" button
```

### 2. Backend API Call
```bash
curl -X POST https://wolf-goat-pig.onrender.com/sheet-integration/sync-wgp-sheet \
  -H "Content-Type: application/json" \
  -H "X-Scheduled-Job: true" \
  -d '{"csv_url":"https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=0"}'
```

### 3. Automated Script
```bash
./scripts/test-production-sync.sh
```

---

## 📝 Best Practices

### Before Syncing
- ✅ Update Google Sheet with latest scores
- ✅ Verify sheet is publicly accessible
- ✅ Check for data quality (no blank rows, correct formats)
- ✅ Wait for backend to be warm (if recently inactive)

### After Syncing
- ✅ Review sync results for errors
- ✅ Check leaderboard displays updated data
- ✅ Verify player count matches expectations
- ✅ Note the sync timestamp for records

### Regular Maintenance
- 🔄 Sync after each game session
- 📅 Review sync results weekly
- 🔍 Check for errors or anomalies
- 📊 Compare sheet data with leaderboard periodically

---

## 🎯 Success Indicators

Your sync is working correctly when you see:

✅ Success popup appears
✅ "Sync Results" tab shows data
✅ All summary cards display numbers
✅ "Synced Players" list shows player names
✅ Sample data displays player statistics
✅ No errors in the "Errors" section
✅ "Last synced" timestamp is current
✅ Leaderboard shows updated data

---

## 📞 Support

**Need Help?**

1. Check error message in admin UI
2. Review browser console (F12) for errors
3. Check backend logs on Render.com
4. Refer to main docs:
   - `docs/PRODUCTION_SYNC_VERIFICATION.md`
   - `docs/FRONTEND_SYNC_TESTING.md`
   - `docs/QUICK_SYNC_REFERENCE.md`

**Common Links:**
- Admin Page: `/admin`
- Leaderboard: `/leaderboard`
- Live Sync: `/live-sync`
- API Docs: `https://wolf-goat-pig.onrender.com/docs`

---

## ✨ Summary

**The admin sync button provides:**
- 🚀 One-click Google Sheets sync
- 📊 Detailed sync results and analytics
- ✅ No rate limiting for admins
- 🎯 Instant feedback and error handling
- 📈 Historical sync tracking

**To use it:**
1. Go to `/admin`
2. Click "📊 Sheets Integration" tab
3. Click "🚀 Sync Now" button
4. Review results and verify leaderboard

That's it! The simplest way to sync your Google Sheets data. 🎉
