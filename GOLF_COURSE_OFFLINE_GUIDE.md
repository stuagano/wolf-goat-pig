# Golf Course Offline Mode Guide

## The Problem: Poor Cell Signal on the Golf Course 🏌️📱

Out on the golf course, cell phone connectivity is often poor or non-existent. Trees, elevation changes, and remote locations make it hard to maintain a stable connection to the backend server. This guide explains how Wolf-Goat-Pig handles these conditions.

## The Solution: Progressive Web App (PWA) with Offline Support

Wolf-Goat-Pig is now a **Progressive Web App** that works completely offline. You can:

1. ✅ **Install it on your phone** - Works like a native app
2. ✅ **Play entirely offline** - All game logic runs on your device
3. ✅ **Sync when back online** - Game data uploads when signal returns
4. ✅ **Never lose progress** - Everything saves to your device

## How to Install the App on Your Phone

### iPhone/Safari:

1. Open Safari and go to the Wolf-Goat-Pig website
2. Tap the **Share** button (square with arrow)
3. Scroll down and tap **"Add to Home Screen"**
4. Tap **"Add"** in the top right
5. The app icon will appear on your home screen

### Android/Chrome:

1. Open Chrome and go to the Wolf-Goat-Pig website
2. Tap the **⋮** menu button
3. Tap **"Add to Home Screen"** or **"Install App"**
4. Tap **"Install"** or **"Add"**
5. The app icon will appear on your home screen

## Using the App on the Course

### Before You Head Out:

1. **Open the app at home/clubhouse** (with good WiFi)
2. **Create or join your game** - This downloads all necessary data
3. **Wait for "Ready for Offline Use"** indicator
4. **Close and reopen the app** - Verify it works without WiFi

Now you're ready to play offline!

### On the Course:

#### Starting a Hole:
- All game logic runs on your device
- No internet needed
- Instant response times

#### Recording Scores:
- Enter scores normally
- Saves to your phone instantly
- Syncs to server when signal returns

#### What Works Offline:
- ✅ Score tracking
- ✅ Wolf rotation
- ✅ Betting calculations
- ✅ Game state
- ✅ All game features

#### What Needs Connection (Optional):
- ⚠️ Joining new games
- ⚠️ Real-time updates from other players
- ⚠️ Syncing to other devices

### Connection Status Indicators:

The app shows your connection status at the top:

| Indicator | Meaning | What It Means |
|-----------|---------|---------------|
| 🟢 **Online** | Green badge | Full connection - syncing to server |
| 🟠 **Offline** | Orange badge | No connection - using cached data |
| 🟡 **Syncing** | Yellow badge | Connection restored - uploading data |

### Back at the Clubhouse:

When you return to good WiFi/cell coverage:

1. **App automatically detects connection**
2. **Shows "Back Online" notification**
3. **Syncs all game data to server**
4. **Other players can now see your scores**

You don't need to do anything - it's automatic!

## Troubleshooting

### "App won't load offline"

**Problem:** You didn't open the app with connection first

**Solution:**
1. Connect to WiFi
2. Open the app
3. Wait 5-10 seconds for cache
4. Look for "Ready for Offline Use" message
5. Now you can go offline

### "Scores aren't syncing"

**Problem:** Still no connection, or sync pending

**Solution:**
- Check connection status indicator
- Move to area with better signal
- App will automatically retry sync
- In worst case, scores are saved on your device

### "Lost all my game data"

**Problem:** Cleared browser cache or app data

**Prevention:**
- Don't use "Clear All Data" in phone settings
- The app uses persistent storage
- Data survives app close/reopen
- Only clearing cache/site data will delete it

**Recovery:**
- If game was synced to server before, rejoin by game code
- Otherwise, game data is unfortunately lost

### "Install option not showing up"

**iPhone:**
- Must use Safari (not Chrome or other browsers)
- Some corporate/school devices block this

**Android:**
- Use Chrome browser
- Update Chrome to latest version
- Check that Chrome site settings allow installation

## Technical Details

### What Gets Cached:

The service worker caches:
- 📄 All HTML, CSS, JavaScript
- 🎨 Images and logos
- 🎯 Game logic and calculations
- 💾 Last game state

### What Gets Stored Locally:

Your device stores:
- Active game state (localStorage)
- Player information
- Scores for current round
- Betting history
- Game preferences

### Storage Limits:

- **localStorage:** ~5-10MB (plenty for scores)
- **Service Worker Cache:** ~50MB (holds app files)
- **Typical game data:** ~100KB

A full 18-hole game with 4 players uses about 100KB. You can store hundreds of rounds.

### Data Sync Strategy:

```
1. Action happens (e.g., enter score)
   ↓
2. Save to localStorage immediately
   ↓
3. Try to send to server
   ↓
4a. Success → Mark as synced
4b. Failure → Queue for later sync
   ↓
5. When connection returns → Auto-sync queue
```

### Network Strategy:

**API Calls:** Network-first, fallback to cache
- Tries server first
- Falls back to cached response if offline
- Shows offline indicator

**Static Assets:** Cache-first
- Loads from cache instantly
- Updates cache in background
- Fast app loads

## Privacy & Data

### What's Stored on Your Device:
- Your active games
- Your scores
- Your preferences
- No other players' personal data

### What's Synced to Server:
- Game results (when online)
- Scores and betting outcomes
- Anonymized game stats (optional)

### Data Security:
- All local data is on your device only
- Sync uses HTTPS encryption
- Server doesn't store data unless you sync
- You can clear all data anytime

## Best Practices for Golf Course Use

### 🏌️ Pre-Round Checklist:
- [ ] Install app on home screen
- [ ] Open app with good WiFi
- [ ] Create/join game
- [ ] Verify offline mode works
- [ ] Check battery level

### 🔋 Battery Saving Tips:
- Put phone in Low Power Mode
- Close background apps
- Reduce screen brightness
- App uses minimal battery (no constant syncing)

### 📱 During Round:
- Keep phone in pocket between holes
- Only open when recording scores
- App saves automatically
- Don't worry about connection

### ✅ Post-Round:
- Return to clubhouse WiFi
- Open app to trigger sync
- Wait for "Sync Complete" message
- View final leaderboard

## Advantages Over Other Golf Apps

| Feature | Wolf-Goat-Pig | Typical Golf Apps |
|---------|---------------|-------------------|
| Works offline | ✅ Fully | ⚠️ Limited/No |
| Betting tracking | ✅ Built-in | ❌ Manual |
| Wolf rotation | ✅ Automatic | ❌ Not supported |
| Instant saves | ✅ localStorage | ⚠️ Requires network |
| Battery usage | ✅ Low | ⚠️ High (GPS, sync) |
| Installation | ✅ 1-tap PWA | ⚠️ App Store download |

## Frequently Asked Questions

**Q: Do I need to download from the App Store?**
A: No! It's a Progressive Web App - install directly from the browser.

**Q: Will it drain my battery?**
A: No. The app only runs when you open it. No background GPS or syncing.

**Q: What if two people enter different scores offline?**
A: Last sync wins. Best practice: one person enters scores per group.

**Q: Can I use this without internet at all?**
A: Yes! After initial setup, you can play completely offline forever (just can't sync).

**Q: Does it work on both iPhone and Android?**
A: Yes! Works on any modern smartphone browser.

**Q: How much data does syncing use?**
A: Tiny. A full 18-hole game is ~100KB (less than loading a single photo).

## Support

Having issues on the course?

1. **Check the connection indicator** - Orange = offline is normal
2. **Verify scores are saving** - They should appear immediately
3. **Don't panic about sync** - It will happen when signal returns
4. **If truly stuck** - Screenshot your scores, can enter manually later

## Updates

The app auto-updates when:
- You open it with WiFi
- Service worker detects new version
- You see "New version available" banner

Tap "Refresh" to get latest features immediately.

---

**Enjoy your round! 🏌️⛳**

The app is designed for the realities of golf course connectivity. Focus on your game, not your phone. Everything else is handled automatically.
