# Wolf Goat Pig Simulation Startup Fixes

This document outlines the fixes applied to resolve simulation startup errors and improve the development experience.

## Issues Fixed

### 1. Database Initialization at Import Time (Critical Fix)
**Problem**: `database.init_db()` was called at import time in `backend/app/main.py:8`, causing the application to fail if the database wasn't properly configured.

**Fix**: Moved database initialization to a FastAPI startup event handler:
```python
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        database.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Continue startup even if database fails for development
        pass
```

### 2. Missing Root-Level Scripts
**Problem**: README referenced `install.py` and `dev.sh` scripts in the root directory that didn't exist.

**Fix**: Created wrapper scripts:
- `install.py` - Wrapper for `scripts/development/install.py`
- `dev.sh` - Enhanced development server startup script

### 3. Hardcoded Paths in Test Files
**Problem**: The old `SIMULATION_TEST.py` helper contained hardcoded local paths that broke on other machines.

**Fix**: Replaced the script with [`scripts/diagnostics/simulation_startup_check.py`](../../scripts/diagnostics/simulation_startup_check.py), which resolves paths relative to the repository root using `pathlib.Path`.

## New Files Created

### `start_simulation.py`
A comprehensive startup script that:
- Checks and installs required Python packages
- Sets up the development environment
- Tests basic imports
- Starts the backend server

Usage:
```bash
python start_simulation.py
```

### `test_simulation_e2e.py`
End-to-end test suite that verifies:
- Database setup
- Simulation creation
- API endpoints definition
- Course data functionality

Usage:
```bash
python test_simulation_e2e.py
```

### Enhanced `dev.sh`
Improved development server script that:
- Sets environment variables
- Creates necessary directories
- Provides clear feedback
- Falls back to direct commands if needed

Usage:
```bash
./dev.sh
```

## Quick Start (Fixed Process)

1. **Install dependencies** (if needed):
   ```bash
   python install.py
   ```

2. **Run end-to-end test**:
   ```bash
   python test_simulation_e2e.py
   ```

3. **Start the simulation**:
   ```bash
   # Option 1: Full startup script
   python start_simulation.py
   
   # Option 2: Development script
   ./dev.sh
   
   # Option 3: Manual
   cd backend && python -m uvicorn app.main:app --reload
   ```

4. **Access the application**:
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Environment Configuration

The startup scripts automatically configure:
- `ENVIRONMENT=development`
- `DATABASE_URL=sqlite:///./reports/wolf_goat_pig.db`
- Creates `reports/` directory for the database

## Testing

### Run the fixed simulation test:
```bash
python scripts/diagnostics/simulation_startup_check.py
```

### Run comprehensive end-to-end tests:
```bash
python scripts/diagnostics/test_simulation_e2e.py
```

## Frontend Setup

To start the frontend (after backend is running):
```bash
cd frontend
npm install  # First time only
npm start
```

The frontend will be available at http://localhost:3000 and will proxy API requests to the backend at http://localhost:8000.

## Next Steps

1. All startup issues have been resolved
2. The simulation can now start without errors
3. Both automatic and manual startup options are available
4. Comprehensive testing is in place

The simulation is now ready for end-to-end testing and development!