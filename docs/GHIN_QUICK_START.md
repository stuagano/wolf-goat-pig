# GHIN Integration - Quick Start

## 🎯 Goal
Get GHIN handicap syncing working in 5 minutes.

---

## Step 1: Get Credentials (2 minutes)

You need a GHIN.com account.

**Option A: Use Existing Account**
- Email: your-ghin@example.com
- Password: (your ghin.com password)

**Option B: Create New Account**
1. Go to https://www.ghin.com
2. Click "Sign Up"
3. Complete registration
4. Note email and password

---

## Step 2: Set Environment Variables (1 minute)

### Production (Render.com)

1. Go to https://dashboard.render.com
2. Select your `wolf-goat-pig` backend service
3. Click "Environment" in left sidebar
4. Click "Add Environment Variable"
5. Add these two variables:

```
Key: GHIN_USERNAME
Value: your-email@example.com

Key: GHIN_PASSWORD
Value: your-ghin-password
```

6. Click "Save Changes"
7. Service will automatically restart

### Local Development

Edit `backend/.env`:
```env
GHIN_USERNAME=your-email@example.com
GHIN_PASSWORD=your-ghin-password
```

Then restart your backend:
```bash
cd backend
# Kill existing process
# Then restart
uvicorn app.main:app --reload
```

---

## Step 3: Verify Configuration (30 seconds)

Open in browser:
```
https://wolf-goat-pig.onrender.com/ghin/diagnostic
```

Should show:
```json
{
  "email_configured": true,
  "password_configured": true,
  "all_configured": true
}
```

✅ If `all_configured: true` → Success! Continue to Step 4.
❌ If `false` → Double-check environment variables and restart backend.

---

## Step 4: Add Player GHIN IDs (1 minute)

1. Navigate to: `https://your-app.vercel.app/admin`
2. Click **"⛳ GHIN"** tab
3. In "Add GHIN ID to Player" section:
   - Select a player from dropdown
   - Enter their 7-8 digit GHIN ID
   - Click "Add GHIN ID"

**Where to find GHIN IDs:**
- Search on https://www.ghin.com (use "Golfer Lookup")
- Ask the player (they can find it on GHIN mobile app)
- Check their golf club handicap card

Repeat for each player you want to sync.

---

## Step 5: Sync Handicaps (30 seconds)

Still in `/admin` → "⛳ GHIN" tab:

**Sync All Players:**
1. Scroll to "Sync Player Handicaps" section
2. Click **"Sync All Player Handicaps"** button
3. Wait 5-10 seconds
4. Success messages will appear

**Or sync individually:**
- Click "Sync Handicap" next to a specific player's name

---

## Step 6: View Results (30 seconds)

Scroll down to "GHIN-Enhanced Leaderboard" section.

You should see:
- Player names
- Current handicap indexes (from GHIN)
- Total earnings
- Games played

✅ **Success!** Your GHIN integration is working!

---

## Quick Verification Checklist

- [ ] GHIN credentials set in environment variables
- [ ] Backend restarted after setting variables
- [ ] Diagnostic shows `all_configured: true`
- [ ] At least one player has GHIN ID added
- [ ] Sync completed without errors
- [ ] GHIN-enhanced leaderboard shows handicaps

**All checked?** You're done! 🎉

---

## Common Issues

### "GHIN service not available"

**Fix:**
1. Check environment variables are set
2. Restart backend service
3. Wait 30 seconds for initialization
4. Check diagnostic endpoint again

### "Failed to sync handicap for player X"

**Fix:**
1. Verify player's GHIN ID is correct (check on ghin.com)
2. Ensure player has active GHIN membership
3. Try syncing just that player individually
4. Check backend logs for specific error

### Credentials not working

**Fix:**
1. Try logging into https://www.ghin.com manually
2. Reset password if needed
3. Update environment variables
4. Restart backend

---

## Next Steps

**Your GHIN integration is working!** Now you can:

1. **Weekly Sync:** Before each Sunday game, sync all handicaps
2. **Add More Players:** As new players join, add their GHIN IDs
3. **Monitor:** Check GHIN-enhanced leaderboard regularly
4. **Automate:** (Future) Set up automatic daily sync

---

## Quick Access Links

**Admin GHIN Page:**
```
https://your-vercel-app.vercel.app/admin
→ Click "⛳ GHIN" tab
```

**Diagnostic Endpoint:**
```
https://wolf-goat-pig.onrender.com/ghin/diagnostic
```

**Backend Logs (Render.com):**
```
https://dashboard.render.com
→ Select service
→ Click "Logs"
→ Search for "GHIN"
```

---

## Support

**Need help?** Check:
1. `docs/GHIN_INTEGRATION_GUIDE.md` - Comprehensive guide
2. Backend logs on Render.com
3. Browser console (F12) for frontend errors

**Still stuck?** Common fixes:
- Restart backend after setting env vars
- Check GHIN credentials work on ghin.com
- Verify GHIN IDs are correct (7-8 digits)
- Wait a few minutes if rate limited

---

That's it! You now have GHIN handicap syncing working. ⛳
