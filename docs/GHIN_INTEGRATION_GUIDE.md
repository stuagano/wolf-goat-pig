# GHIN Integration Setup Guide

## Overview

Your Wolf Goat Pig application has full GHIN (Golf Handicap and Information Network) integration capabilities. This allows you to:

- Sync player handicap indexes from GHIN
- Fetch recent scores from GHIN
- Display GHIN-enhanced leaderboards
- Track handicap history over time

---

## Quick Access

**Admin Interface:** `/admin` → "⛳ GHIN" tab

This provides a user-friendly interface to:
- Check GHIN service status
- Add GHIN IDs to players
- Sync individual player handicaps
- Sync all player handicaps at once
- View GHIN-enhanced leaderboard

---

## 🔑 Step 1: Get GHIN API Credentials

You need a GHIN.com account with API access.

### Option A: GHIN.com Account
1. Go to https://www.ghin.com
2. Create an account or log in
3. Note your email and password

### Option B: Contact Your Golf Association
- Contact your regional golf association
- Request GHIN API credentials
- They may provide a dedicated API user account

**Important:** The GHIN API uses your ghin.com login credentials (email + password).

---

## 🔧 Step 2: Configure Environment Variables

### Backend Configuration

You need to set these environment variables where your backend is deployed:

**For Render.com (Production):**
1. Go to Render.com dashboard
2. Select your backend service
3. Go to "Environment" section
4. Add these variables:

```env
GHIN_USERNAME=your-email@example.com
GHIN_PASSWORD=your-ghin-password
```

**For Local Development:**

Create or update `.env` file in the `backend/` directory:

```env
# GHIN Integration
GHIN_USERNAME=your-email@example.com
GHIN_PASSWORD=your-ghin-password
```

### Environment Variable Names

The backend looks for these variables (either name works):
- `GHIN_USERNAME` or `GHIN_API_USER` - Your GHIN.com email
- `GHIN_PASSWORD` or `GHIN_API_PASS` - Your GHIN.com password

---

## ✅ Step 3: Verify Configuration

### Method 1: Admin UI

1. Navigate to `/admin`
2. Click "⛳ GHIN" tab
3. Look for the "GHIN Service Status" section
4. Should show:
   - ✅ Email Configured
   - ✅ Password Configured
   - ✅ Service Available

### Method 2: API Endpoint

```bash
curl https://wolf-goat-pig.onrender.com/ghin/diagnostic
```

**Expected Response (when configured):**
```json
{
  "email_configured": true,
  "password_configured": true,
  "static_token_configured": false,
  "all_configured": true,
  "environment": "production"
}
```

**Response (when NOT configured):**
```json
{
  "email_configured": false,
  "password_configured": false,
  "static_token_configured": false,
  "all_configured": false,
  "environment": "production"
}
```

---

## 👤 Step 4: Add GHIN IDs to Players

Players need GHIN IDs associated with their profiles before you can sync handicaps.

### Using Admin UI

1. Go to `/admin` → "⛳ GHIN" tab
2. In the "Add GHIN ID to Player" section:
   - Select a player from the dropdown
   - Enter their GHIN ID (7-8 digit number)
   - Click "Add GHIN ID"
3. Success message will confirm

### Using API

```bash
curl -X PUT https://wolf-goat-pig.onrender.com/players/{player_id} \
  -H "Content-Type: application/json" \
  -d '{"ghin_id": "12345678", "name": "Player Name"}'
```

### Where to Find GHIN IDs

**Option 1: GHIN.com Lookup**
1. Go to https://www.ghin.com
2. Use the "Golfer Lookup" feature
3. Search by player name
4. Note their GHIN ID

**Option 2: Ask Players**
- Players can find their GHIN ID on the GHIN mobile app
- Or on their golf club handicap card

---

## 🔄 Step 5: Sync Handicaps

### Sync Individual Player

**Using Admin UI:**
1. Go to `/admin` → "⛳ GHIN" tab
2. Scroll to "Sync Player Handicaps" section
3. Click "Sync Handicap" button next to a player's name
4. Wait for confirmation

**Using API:**
```bash
curl -X POST https://wolf-goat-pig.onrender.com/ghin/sync-player-handicap/1
```

### Sync All Players

**Using Admin UI:**
1. Go to `/admin` → "⛳ GHIN" tab
2. Click "Sync All Player Handicaps" button
3. Wait for all syncs to complete

**Using API:**
```bash
curl -X POST https://wolf-goat-pig.onrender.com/ghin/sync-handicaps
```

---

## 📊 Step 6: View GHIN-Enhanced Leaderboard

After syncing handicaps, you can view the GHIN-enhanced leaderboard.

**Access:**
- Admin UI: `/admin` → "⛳ GHIN" tab → "GHIN-Enhanced Leaderboard" section
- API: `GET /leaderboard/ghin-enhanced`

**What it shows:**
- Player rankings
- Current handicap index from GHIN
- Total earnings
- Games played
- Win percentage

---

## 🔍 How It Works

### Authentication Flow

1. Backend calls GHIN API with credentials:
   ```
   POST https://api2.ghin.com/api/v1/golfer_login.json
   ```
2. Receives JWT token for authenticated requests
3. Uses token for subsequent API calls

### Data Sync Flow

1. **Fetch from GHIN:**
   ```
   GET https://api2.ghin.com/api/v1/golfers/{ghin_id}.json
   ```

2. **Extract Data:**
   - Handicap Index
   - Effective Date
   - Revision Reason
   - Number of scores used

3. **Update Local Database:**
   - Update `PlayerProfile.handicap`
   - Create `GHINHandicapHistory` record
   - Set `ghin_last_updated` timestamp

4. **Store Historical Data:**
   - All handicap changes are stored
   - Track when and why handicap changed
   - Maintain full history for analytics

---

## 📁 Database Schema

### PlayerProfile Table
```sql
- ghin_id: VARCHAR (player's GHIN ID)
- handicap: DECIMAL (current handicap index)
- ghin_last_updated: TIMESTAMP (last sync time)
```

### GHINHandicapHistory Table
```sql
- player_profile_id: FK to PlayerProfile
- ghin_id: VARCHAR
- effective_date: DATE (when handicap took effect)
- handicap_index: DECIMAL
- revision_reason: VARCHAR (e.g., "Manual", "Scheduled")
- scores_used_count: INTEGER
- synced_at: TIMESTAMP
```

### GHINScore Table
```sql
- player_profile_id: FK to PlayerProfile
- ghin_id: VARCHAR
- score_date: DATE
- course_name: VARCHAR
- course_rating: DECIMAL
- slope_rating: INTEGER
- adjusted_gross_score: INTEGER
- score_differential: DECIMAL
- handicap_index_used: DECIMAL
```

---

## 🎯 Usage Examples

### Example 1: Weekly Handicap Sync

**Scenario:** Sync all player handicaps before Sunday game

**Steps:**
1. Go to `/admin` → "⛳ GHIN" tab
2. Click "Sync All Player Handicaps"
3. Wait for completion
4. Review any errors
5. Updated handicaps are ready for game setup

### Example 2: Add New Player with GHIN

**Scenario:** New player joins the group

**Steps:**
1. Create player profile (if not exists)
2. Go to `/admin` → "⛳ GHIN" tab
3. Select new player from dropdown
4. Enter their GHIN ID
5. Click "Add GHIN ID"
6. Click "Sync Handicap" for that player
7. Player now has current GHIN handicap

### Example 3: View Handicap History

**Scenario:** Check how a player's handicap has changed

**Query database:**
```sql
SELECT effective_date, handicap_index, revision_reason
FROM ghin_handicap_history
WHERE player_profile_id = 1
ORDER BY effective_date DESC;
```

---

## 🐛 Troubleshooting

### Issue: "GHIN service not available"

**Symptoms:**
- Red error message in admin UI
- Sync buttons don't work
- Diagnostic shows credentials not configured

**Solution:**
1. Check environment variables are set:
   ```bash
   echo $GHIN_USERNAME
   echo $GHIN_PASSWORD
   ```
2. Restart backend service after adding variables
3. Verify at `/ghin/diagnostic` endpoint

### Issue: "Failed to sync handicap"

**Possible Causes:**
1. **Invalid GHIN ID:**
   - Check GHIN ID is correct
   - Verify on ghin.com

2. **Player not found in GHIN:**
   - Player may not have active GHIN membership
   - Check with player or golf association

3. **GHIN API credentials invalid:**
   - Verify username/password are correct
   - Try logging into ghin.com manually

4. **Rate limiting:**
   - GHIN API may have rate limits
   - Wait a few minutes and try again

### Issue: "Authentication failed"

**Solutions:**
1. **Verify credentials:**
   ```bash
   curl -X POST https://api2.ghin.com/api/v1/golfer_login.json \
     -H "Content-Type: application/json" \
     -d '{
       "user": {
         "email_or_ghin": "your-email@example.com",
         "password": "your-password"
       },
       "source": "GHINcom"
     }'
   ```

2. **Check password:**
   - Ensure password doesn't have special characters causing issues
   - Try resetting password on ghin.com

3. **Account status:**
   - Ensure GHIN.com account is active
   - Check if account needs verification

### Issue: Handicap not updating

**Check:**
1. **Last sync time:**
   - Look at `ghin_last_updated` field
   - May need to sync again

2. **GHIN data freshness:**
   - GHIN updates handicaps twice a month
   - Recent scores may not be reflected yet

3. **Database connection:**
   - Check backend logs for errors
   - Verify database is accessible

---

## 🔒 Security Considerations

### Credential Storage

**✅ DO:**
- Store credentials in environment variables
- Use secrets management (Render.com secrets, etc.)
- Rotate credentials periodically

**❌ DON'T:**
- Commit credentials to git
- Hardcode in source code
- Share credentials publicly

### API Rate Limiting

- GHIN API may have rate limits
- Space out bulk syncs (use delays)
- Monitor for 429 errors (Too Many Requests)

### Data Privacy

- GHIN data is personal information
- Handicap info is generally considered public (golf purposes)
- Don't share GHIN credentials
- Log access appropriately

---

## 📊 Monitoring & Maintenance

### Check Sync Health

**Weekly:**
```bash
# Check how many players have synced handicaps
curl https://wolf-goat-pig.onrender.com/leaderboard/ghin-enhanced | \
  grep -o '"handicap_index"' | wc -l
```

**Monthly:**
```bash
# Check when handicaps were last updated
# Query database for ghin_last_updated timestamps
```

### Log Monitoring

**What to look for:**
- "GHIN service initialized successfully" (good)
- "Failed to initialize GHIN service" (bad - check credentials)
- "Synced handicap for player X" (good)
- "Failed to sync handicap" (investigate player GHIN ID)

**Render.com logs:**
1. Go to dashboard
2. Select backend service
3. Click "Logs"
4. Search for "GHIN"

---

## 🚀 Advanced Features

### Scheduled Handicap Sync

**Coming Soon:** Automatic daily handicap sync

**Current:** Manual sync via admin UI or cron job

**DIY Cron Job:**
```bash
# Add to crontab for weekly sync (Sunday 6 AM)
0 6 * * 0 curl -X POST https://wolf-goat-pig.onrender.com/ghin/sync-handicaps
```

### Handicap Trending

**Query handicap history:**
```sql
SELECT
  p.name,
  h.effective_date,
  h.handicap_index,
  LAG(h.handicap_index) OVER (
    PARTITION BY p.id
    ORDER BY h.effective_date
  ) as previous_handicap
FROM players p
JOIN ghin_handicap_history h ON p.id = h.player_profile_id
ORDER BY p.name, h.effective_date DESC;
```

### Score Posting Integration

**Future Enhancement:** Automatically post Wolf Goat Pig scores to GHIN

**Requirements:**
- GHIN API write access
- Course ratings for all courses
- Player consent
- Compliance with GHIN rules

---

## 📚 API Reference

### Endpoints

**`GET /ghin/diagnostic`**
- Check GHIN configuration status
- No authentication required
- Returns credential status

**`POST /ghin/sync-player-handicap/{player_id}`**
- Sync individual player handicap
- Requires player to have GHIN ID
- Returns handicap data

**`POST /ghin/sync-handicaps`**
- Sync all player handicaps
- Processes all players with GHIN IDs
- Returns summary

**`GET /leaderboard/ghin-enhanced`**
- Get leaderboard with GHIN data
- Includes current handicap indexes
- Sorted by total earnings

**`GET /ghin/lookup`** (if implemented)
- Look up golfer by name
- Search GHIN database
- Returns GHIN ID and handicap

---

## ✅ Setup Checklist

Use this checklist to verify GHIN integration is working:

- [ ] GHIN credentials obtained (email + password)
- [ ] Environment variables set on backend (`GHIN_USERNAME`, `GHIN_PASSWORD`)
- [ ] Backend restarted after adding variables
- [ ] Diagnostic endpoint shows `all_configured: true`
- [ ] Admin UI "⛳ GHIN" tab accessible
- [ ] GHIN service status shows as available
- [ ] At least one player has GHIN ID added
- [ ] Test sync on one player succeeds
- [ ] Handicap updates in player profile
- [ ] GHIN-enhanced leaderboard shows data
- [ ] No errors in backend logs

**If all items checked:** Your GHIN integration is fully functional! 🎉

---

## 🆘 Support

**Can't get it working?**

1. **Check diagnostic endpoint:**
   ```bash
   curl https://wolf-goat-pig.onrender.com/ghin/diagnostic
   ```

2. **Check backend logs:**
   - Render.com → Service → Logs
   - Search for "GHIN" or "authentication"

3. **Test credentials manually:**
   - Try logging into ghin.com
   - Verify email and password work

4. **Common issues:**
   - Credentials not set → Set environment variables
   - Backend not restarted → Restart service
   - Invalid GHIN ID → Check on ghin.com
   - Rate limiting → Wait and retry

**Still stuck?** Check the backend service logs for detailed error messages.

---

## 🎯 Summary

**Your GHIN integration is ready to use!** Just need to:

1. **Set credentials** (environment variables)
2. **Add player GHIN IDs** (via admin UI)
3. **Sync handicaps** (one button click)
4. **Enjoy!** Updated handicaps for your games

**Quick Start:**
```
1. Go to /admin → ⛳ GHIN
2. Check status (should show all configured)
3. Add GHIN IDs to players
4. Click "Sync All Player Handicaps"
5. View GHIN-enhanced leaderboard
```

Happy golfing! ⛳🏌️
