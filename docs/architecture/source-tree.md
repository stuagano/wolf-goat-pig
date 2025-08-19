# Source Tree Documentation

## Project Structure Overview

```
wolf-goat-pig/
├── .bmad-core/           # BMad Method framework
├── .claude/              # Claude AI agent configurations
├── .github/              # GitHub Actions workflows
├── backend/              # FastAPI backend application
├── frontend/             # React frontend application
├── docs/                 # BMad documentation
├── scripts/              # Utility scripts
└── [root files]          # Configuration and documentation
```

## Root Directory

### Configuration Files
- `render.yaml` - Render deployment configuration
- `vercel.json` - Vercel deployment configuration
- `package.json` - Root package for scripts
- `requirements.txt` - Python dependencies
- `pytest.ini` - Test configuration
- `.gitignore` - Git ignore patterns

### Scripts
- `deploy.sh` - Deployment automation script
- `dev.sh` - Development environment setup
- `deployment_check.py` - Pre-deployment validation
- `claude-issue-monitor.py` - GitHub issue automation
- `setup-claude-automation.sh` - Automation setup

### Documentation
- `README.md` - Project overview
- `DEPLOYMENT_BEST_PRACTICES.md` - Deployment guide
- `TODO.md` - Development roadmap

## Backend Structure (`/backend`)

```
backend/
├── app/                  # Main application code
│   ├── domain/          # Domain models and business logic
│   ├── services/        # Service layer
│   ├── state/           # State management
│   ├── main.py          # FastAPI application entry
│   ├── database.py      # Database configuration
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # Database operations
│   └── game_state.py    # Game state management
├── tests/               # Test suite
├── venv/                # Virtual environment
└── requirements.txt     # Python dependencies
```

### Key Backend Modules

#### `/app/domain`
Business domain models:
- `player.py` - Player management
- `shot_result.py` - Shot outcome calculations
- `shot_range_analysis.py` - Strategic shot analysis

#### `/app/state`
Game state management:
- `course_manager.py` - Golf course data
- `player_manager.py` - Player state
- `betting_state.py` - Betting logic
- `shot_state.py` - Shot tracking

#### `/app/services`
Service layer for complex operations (extensible)

#### `/tests`
Comprehensive test coverage:
- `test_unified_action_api.py` - API testing
- `test_game_flow.py` - Game flow validation
- `test_simulation_components.py` - Simulation testing

## Frontend Structure (`/frontend`)

```
frontend/
├── public/              # Static assets
├── src/                 # Source code
│   ├── components/      # React components
│   ├── context/         # React context providers
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page components
│   ├── theme/           # Theme configuration
│   ├── utils/           # Utility functions
│   ├── App.js           # Main app component
│   └── index.js         # Application entry
├── package.json         # Node dependencies
└── build/              # Production build output
```

### Key Frontend Modules

#### `/src/components`
Reusable UI components:
- `game/` - Game-specific components
  - `UnifiedGameInterface.js` - Main game UI
  - `WolfGoatPigGame.js` - Game controller
- `simulation/` - Simulation components
  - `SimulationMode.js` - Simulation interface
  - `MonteCarloSimulation.js` - Monte Carlo engine
- `ui/` - Generic UI components
  - `Button.js`, `Card.js`, `Input.js`, `Select.js`
- Specialized components:
  - `ColdStartHandler.js` - Backend warmup UX
  - `ShotRangeAnalyzer.js` - Shot analysis
  - `AnalyticsDashboard.js` - Game analytics

#### `/src/context`
Global state management:
- `GameProvider.js` - Game state context

#### `/src/hooks`
Custom React hooks:
- `useGameApi.js` - Game API interactions
- `useSimulationApi.js` - Simulation API

#### `/src/utils`
Utility functions:
- `api.js` - API client with cold start handling

## BMad Documentation (`/docs`)

```
docs/
├── prd.md               # Product Requirements Document
├── architecture.md      # System architecture
├── architecture/        # Technical documentation
│   ├── coding-standards.md
│   ├── tech-stack.md
│   └── source-tree.md
├── stories/             # User stories
└── qa/                  # QA documentation
```

## BMad Core (`/.bmad-core`)

```
.bmad-core/
├── agents/              # AI agent definitions
├── tasks/               # Task templates
├── templates/           # Document templates
├── checklists/          # Process checklists
├── workflows/           # Development workflows
├── data/                # Knowledge base
└── core-config.yaml     # BMad configuration
```

## File Naming Conventions

### Python Files
- Snake_case: `game_state.py`, `betting_logic.py`
- Test prefix: `test_<module>.py`

### JavaScript Files
- PascalCase for components: `GameDashboard.js`
- camelCase for utilities: `apiHelpers.js`
- Index files for exports: `index.js`

### Documentation
- UPPERCASE for root docs: `README.md`, `TODO.md`
- Lowercase for subdocs: `coding-standards.md`

## Import Patterns

### Python Imports
```python
# Absolute imports for app modules
from app.domain.player import Player
from app.state.game_state import GameState

# Relative imports within modules
from .betting_state import BettingState
```

### JavaScript Imports
```javascript
// Named exports from components
import { GameDashboard, PlayerCard } from './components';

// Default exports for pages
import HomePage from './pages/HomePage';

// Utility imports
import { apiGet, apiPost } from '../utils/api';
```

## Build Outputs

### Backend Build
- `__pycache__/` - Python bytecode cache
- `*.pyc` - Compiled Python files
- `.pytest_cache/` - Test cache

### Frontend Build
- `build/` - Production build output
- `node_modules/` - Node dependencies
- `.cache/` - Build cache

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://...
ENVIRONMENT=development|production
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
NODE_ENV=development|production
```

## Key Entry Points

### Backend Entry
- **File**: `backend/app/main.py`
- **Function**: FastAPI application initialization
- **Start Command**: `uvicorn app.main:app`

### Frontend Entry
- **File**: `frontend/src/index.js`
- **Function**: React app mounting
- **Start Command**: `npm start`

## Dependencies Management

### Python Dependencies
- **File**: `backend/requirements.txt`
- **Install**: `pip install -r requirements.txt`
- **Virtual Env**: `backend/venv/`

### Node Dependencies
- **File**: `frontend/package.json`
- **Install**: `npm install`
- **Lock File**: `package-lock.json`

## Testing Structure

### Backend Tests
```
backend/tests/
├── test_api_endpoints.py    # API integration tests
├── test_game_flow.py         # Game flow tests
├── test_simulation.py        # Simulation tests
└── test_unified_action.py    # Action API tests
```

### Frontend Tests
```
frontend/src/
├── *.test.js                 # Component tests
└── __tests__/               # Test utilities
```

## Deployment Artifacts

### Backend Deployment
- Render reads from root `render.yaml`
- Uses `backend/` directory
- PostgreSQL database connection

### Frontend Deployment
- Vercel reads from root `vercel.json`
- Builds from `frontend/` directory
- Static hosting with CDN

---

*This source tree documentation reflects the current project structure as of 2025-08-18.*