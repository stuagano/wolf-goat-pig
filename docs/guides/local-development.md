# 🚀 Local Development Guide for Wolf-Goat-Pig

## Quick Start

```bash
# Start both servers
./dev-local.sh

# In another terminal, test the setup
./scripts/diagnostics/test-local.sh
```

## URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Development Workflow

### 1. Start Local Servers
```bash
cd path/to/wolf-goat-pig
./dev-local.sh
```

### 2. Test Your Setup
```bash
# In another terminal
./scripts/diagnostics/test-local.sh
```

### 3. Development Cycle
1. Make changes to code
2. Save files (auto-reload happens)
3. Test in browser at http://localhost:3000
4. Check console for errors
5. Fix and repeat

### 4. Manual Server Start (if needed)

**Backend Only:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend Only:**
```bash
cd frontend
npm start
```

## Testing the Simulation Flow

1. Open http://localhost:3000
2. Click "Start Simulation" or navigate to simulation mode
3. You should see:
   - Personalities loading (5 options)
   - Suggested opponents loading (9 options)
   - Course selection dropdown
4. Configure players and start game
5. Test shot-by-shot gameplay

## Common Issues & Solutions

### Frontend won't compile
- Check for import errors in console
- Run `npm install` in frontend directory
- Clear browser cache

### Backend API errors
- Check terminal for Python errors
- Ensure database exists: `wolf_goat_pig.db`
- Check `backend/app/main.py` for issues

### API calls failing
- Verify proxy in `frontend/package.json` is `"proxy": "http://localhost:8000"`
- Check backend is running on port 8000
- Check frontend is running on port 3000

## File Locations

- **Backend API**: `backend/app/main.py`
- **Frontend Components**: `frontend/src/components/`
- **Simulation Logic**: `backend/app/wolf_goat_pig_simulation.py`
- **Database**: `wolf_goat_pig.db` (SQLite)

## Making Changes

### Backend Changes
- Edit files in `backend/app/`
- Server auto-reloads on save
- Check terminal for errors

### Frontend Changes
- Edit files in `frontend/src/`
- Browser auto-refreshes on save
- Check browser console for errors

## Before Deploying

1. Test locally thoroughly
2. Run `npm run build` to check for build errors
3. Commit and push to GitHub
4. Deployment happens automatically on Render/Vercel

## Current Status

✅ Fixed:
- API endpoints `/personalities` and `/suggested_opponents`
- Response format compatibility
- Frontend import errors

🔧 To Test:
- Complete simulation flow from setup to gameplay
- Shot-by-shot progression
- Team formation and betting

## Quick Commands

```bash
# Start development
./dev-local.sh

# Test endpoints
./scripts/diagnostics/test-local.sh

# Stop all servers
pkill -f uvicorn && pkill -f "npm start"

# Check what's running
ps aux | grep -E "uvicorn|npm"
```

## Tips for Fast Iteration

1. **Use two terminals**: One for servers, one for testing
2. **Keep browser console open**: See errors immediately
3. **Use API docs**: http://localhost:8000/docs to test endpoints
4. **Hot reload**: Both frontend and backend auto-reload on save
5. **Test incrementally**: Fix one error at a time

---

Remember: Always test locally before pushing to production!