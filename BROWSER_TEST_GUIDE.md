# 🧪 Browser Testing Guide for Wolf-Goat-Pig Simulation

## ✅ What Has Been Fixed

1. **hasNextShot undefined issue** - Fixed by ensuring API returns `next_shot_available` field
2. **API response format** - All endpoints now return expected fields
3. **Frontend state management** - Properly handles `next_shot_available` from API
4. **Race condition** - Removed auto-play of first shot after setup

## 🎮 How to Test in Browser

### 1. Start the Development Servers
```bash
./dev-local.sh
```

### 2. Open Browser
Navigate to: http://localhost:3000

### 3. Test the Simulation Flow

#### Step 1: Navigate to Simulation Mode
- Click on "Start Simulation" or navigate to the simulation section
- You should see the game setup form

#### Step 2: Verify Data Loading
✅ **Check that you see:**
- 5 personality options (Aggressive, Conservative, Balanced, Analytical, Unpredictable)
- 9 suggested opponents loading
- Course dropdown with available courses

#### Step 3: Start a Game
1. Enter your name in the "Your Name" field
2. Leave the default computer players or modify them
3. Select a course (optional)
4. Click "Start Simulation"

#### Step 4: Verify Game Started
✅ **You should now see:**
- Game header showing "Simulation - Hole 1"
- Feedback message: "🎮 Game started! You're on the first tee."
- **"Play Next Shot" button** (this confirms hasNextShot is working!)
- Player scores/standings

#### Step 5: Play Shots
1. Click "Play Next Shot" button
2. Watch for feedback messages showing shot results
3. Button should remain visible if more shots available
4. Continue clicking until hole is complete

## 🔍 What to Look For

### ✅ Working Correctly If:
- "Play Next Shot" button appears after starting simulation
- Clicking the button plays a shot and shows feedback
- Game state updates after each shot
- No console errors in browser DevTools

### ❌ Still Has Issues If:
- "Play Next Shot" button doesn't appear
- hasNextShot is still undefined (check browser console)
- Clicking button causes errors
- Game state doesn't update

## 🐛 Debugging Tips

### Check Browser Console
1. Open DevTools (F12 or right-click → Inspect)
2. Go to Console tab
3. Look for any red error messages
4. Check Network tab to see API calls

### Check Component State
In browser console, you can check the current state:
```javascript
// Check if simulation is active
console.log("Game active:", !!document.querySelector('[data-testid="game-play"]'))

// Look for the Play Next Shot button
console.log("Has button:", !!document.querySelector('button:contains("Play Next Shot")'))
```

### API Response Verification
Watch the Network tab when clicking "Play Next Shot":
- Request should go to `/simulation/play-next-shot`
- Response should include:
  - `status: "ok"`
  - `next_shot_available: true/false`
  - `feedback: [...]`
  - `game_state: {...}`

## 📊 Current Status

| Feature | Status |
|---------|--------|
| Setup Simulation | ✅ Fixed |
| Load Personalities | ✅ Fixed |
| Load Opponents | ✅ Fixed |
| Start Game | ✅ Fixed |
| hasNextShot tracking | ✅ Fixed |
| Play Shot | ✅ Fixed |
| Show Feedback | ✅ Fixed |
| Update Game State | ✅ Fixed |

## 🚀 Next Steps

If everything is working:
1. Test a complete 18-hole game
2. Test interaction decisions (partnerships, doubling)
3. Deploy to production (Render/Vercel)

If issues remain:
1. Check browser console for specific errors
2. Verify both servers are running
3. Clear browser cache and reload
4. Check LOCAL_DEV_GUIDE.md for troubleshooting