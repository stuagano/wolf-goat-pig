# 🏆 Google Sheets Leaderboard Setup Guide

## Overview
Your Wolf Goat Pig app has two-way sync with Google Sheets for leaderboard data:
- **Pull**: Import historical player data from your Google Sheet (daily sync)
- **Push**: Export current leaderboard data to your Google Sheet (on-demand)

---

## ✅ Current Status

### Backend APIs Working
- ✅ Leaderboard API: `https://wolf-goat-pig.onrender.com/leaderboard/total_earnings`
- ✅ Returns real player data (10+ players with earnings)
- ✅ Daily sync scheduled at 2:00 AM

### What You Need to Set Up
The Google Sheet needs an **Apps Script** to:
1. Fetch leaderboard data from your API
2. Update the sheet automatically
3. Format and display the leaderboard

---

## 📊 Step 1: Prepare Your Google Sheet

### Required Sheet Structure

Create a sheet with these columns:

| Rank | Player Name | Games Played | Games Won | Win Rate % | Total Earnings | Avg Earnings/Game | Last Updated |
|------|-------------|--------------|-----------|------------|----------------|-------------------|--------------|

### Sheet Setup
1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/
2. Create a tab named "Leaderboard" (or rename existing)
3. Add the header row above

---

## 🔧 Step 2: Install Apps Script

### Open Script Editor
1. In your Google Sheet, click **Extensions** → **Apps Script**
2. Delete any existing code
3. Paste the script below

### Apps Script Code

```javascript
/**
 * Wolf Goat Pig - Leaderboard Sync Script
 * Fetches leaderboard data from the backend API and updates the sheet
 */

const API_URL = 'https://wolf-goat-pig.onrender.com';
const LEADERBOARD_SHEET_NAME = 'Leaderboard';
const LEADERBOARD_TYPE = 'total_earnings'; // Options: total_earnings, win_rate, games_played

/**
 * Creates custom menu when sheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🏆 WGP Leaderboard')
      .addItem('🔄 Refresh Leaderboard', 'refreshLeaderboard')
      .addItem('⚙️ Auto-Update Settings', 'showAutoUpdateDialog')
      .addToUi();
}

/**
 * Fetches leaderboard data from the API
 */
function fetchLeaderboardData() {
  try {
    const url = `${API_URL}/leaderboard/${LEADERBOARD_TYPE}`;
    const response = UrlFetchApp.fetch(url, {
      method: 'get',
      contentType: 'application/json',
      muteHttpExceptions: true
    });

    if (response.getResponseCode() !== 200) {
      throw new Error(`API returned status ${response.getResponseCode()}: ${response.getContentText()}`);
    }

    const data = JSON.parse(response.getContentText());
    return data;

  } catch (error) {
    Logger.log('Error fetching leaderboard: ' + error.toString());
    SpreadsheetApp.getUi().alert('❌ Error fetching leaderboard:\\n\\n' + error.toString());
    return null;
  }
}

/**
 * Updates the leaderboard sheet with fresh data
 */
function refreshLeaderboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(LEADERBOARD_SHEET_NAME);

  // Create sheet if it doesn't exist
  if (!sheet) {
    sheet = ss.insertSheet(LEADERBOARD_SHEET_NAME);
  }

  // Fetch data
  const data = fetchLeaderboardData();
  if (!data || !data.leaderboard) {
    return;
  }

  // Clear existing data (keep header)
  const lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).clearContent();
  }

  // Set headers if sheet is empty
  if (sheet.getLastRow() === 0) {
    const headers = ['Rank', 'Player Name', 'Total Earnings', 'Last Updated'];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }

  // Prepare data rows
  const rows = data.leaderboard.map(player => [
    player.rank,
    player.player_name,
    `$${player.value.toFixed(2)}`,
    new Date()
  ]);

  // Write data to sheet
  if (rows.length > 0) {
    sheet.getRange(2, 1, rows.length, 4).setValues(rows);

    // Format currency column
    sheet.getRange(2, 3, rows.length, 1).setNumberFormat('$#,##0.00');

    // Format date column
    sheet.getRange(2, 4, rows.length, 1).setNumberFormat('M/d/yyyy h:mm a');

    // Auto-resize columns
    sheet.autoResizeColumns(1, 4);

    // Add alternating row colors
    const dataRange = sheet.getRange(2, 1, rows.length, 4);
    dataRange.applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, false, false);
  }

  SpreadsheetApp.getUi().alert(`✅ Leaderboard updated!\\n\\n${rows.length} players synced at ${new Date().toLocaleString()}`);
}

/**
 * Shows dialog for auto-update settings
 */
function showAutoUpdateDialog() {
  const ui = SpreadsheetApp.getUi();

  const html = HtmlService.createHtmlOutput(`
    <h3>Auto-Update Settings</h3>
    <p>To set up automatic updates:</p>
    <ol>
      <li>Go to <b>Extensions</b> → <b>Apps Script</b></li>
      <li>Click the <b>clock icon</b> (Triggers) in the left sidebar</li>
      <li>Click <b>+ Add Trigger</b></li>
      <li>Configure:
        <ul>
          <li>Function: <b>refreshLeaderboard</b></li>
          <li>Event source: <b>Time-driven</b></li>
          <li>Type: <b>Hour timer</b> (or Day timer)</li>
          <li>Interval: <b>Every hour</b> (or preferred)</li>
        </ul>
      </li>
      <li>Click <b>Save</b></li>
    </ol>
    <p><b>Recommended:</b> Update every 6 hours or daily at 3:00 AM</p>
  `)
  .setWidth(400)
  .setHeight(350);

  ui.showModalDialog(html, 'Auto-Update Configuration');
}

/**
 * Test function - run this first to verify API connection
 */
function testAPIConnection() {
  Logger.log('Testing API connection...');
  const data = fetchLeaderboardData();

  if (data && data.leaderboard) {
    Logger.log(`✅ Success! Found ${data.leaderboard.length} players`);
    Logger.log('Top 3 players:');
    data.leaderboard.slice(0, 3).forEach(player => {
      Logger.log(`  ${player.rank}. ${player.player_name}: $${player.value}`);
    });
    return true;
  } else {
    Logger.log('❌ Failed to fetch data');
    return false;
  }
}
```

### Save and Test
1. Click **Save** (disk icon)
2. Click **Run** → Select `testAPIConnection`
3. Grant permissions when prompted
4. Check **View** → **Logs** to see results

---

## 🚀 Step 3: Use the Leaderboard

### Manual Refresh
1. In your Google Sheet, click **🏆 WGP Leaderboard** → **🔄 Refresh Leaderboard**
2. The sheet will update with current data

### Automatic Updates
1. Click **🏆 WGP Leaderboard** → **⚙️ Auto-Update Settings**
2. Follow the instructions to set up a trigger
3. Recommended: Update every 6 hours or daily at 3 AM

---

## 📊 Alternative: Get Other Leaderboard Types

Change the `LEADERBOARD_TYPE` constant in the Apps Script:

```javascript
const LEADERBOARD_TYPE = 'total_earnings'; // Current
// Options:
// - 'total_earnings' - Total money earned
// - 'win_rate' - Win percentage
// - 'games_played' - Most active players
// - 'average_score' - Best average scores
// - 'partnerships_won' - Partnership success
```

---

## 🔄 Backend Sync (Already Configured)

### How It Works
- **Daily Sync**: Backend pulls from your sheet at 2:00 AM
- **Purpose**: Import historical player data
- **CSV URL**: Uses sheet export URL
- **Status Check**: `GET https://wolf-goat-pig.onrender.com/email/scheduler-status`

### Manual Trigger (if needed)
```bash
curl -X POST https://wolf-goat-pig.onrender.com/sheet-integration/sync-wgp-sheet \
  -H "Content-Type: application/json" \
  -H "X-Scheduled-Job: true" \
  -d '{"csv_url": "https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=0"}'
```

---

## ✅ Verification Checklist

- [ ] Apps Script installed in Google Sheet
- [ ] Script runs without errors (`testAPIConnection()`)
- [ ] Custom menu appears ("🏆 WGP Leaderboard")
- [ ] Manual refresh works
- [ ] (Optional) Automatic trigger configured
- [ ] Backend sync scheduled (2:00 AM daily)

---

## 🐛 Troubleshooting

### "Script execution failed"
- **Cause**: Need to grant permissions
- **Fix**: Run script manually, click "Review permissions", grant access

### "API returned status 404"
- **Cause**: Wrong leaderboard type
- **Fix**: Use one of: total_earnings, win_rate, games_played, average_score, partnerships_won

### "No data returned"
- **Cause**: No players in database yet
- **Fix**: Create test games or wait for backend sync to complete

### Sheet doesn't update automatically
- **Cause**: No trigger configured
- **Fix**: Follow Step 3 "Automatic Updates" instructions

---

## 📞 Support

**API Endpoints:**
- Leaderboard: `https://wolf-goat-pig.onrender.com/leaderboard/{type}`
- Health: `https://wolf-goat-pig.onrender.com/health`
- Docs: `https://wolf-goat-pig.onrender.com/docs`

**Current Players in System:**
- Brett Saks: $1,804
- Mike Goldsberry: $1,091
- Steve Sutorius: $1,001
- (7 more players...)

Your leaderboard API is working perfectly! Just add the Apps Script to your Google Sheet and you're all set. 🎉
