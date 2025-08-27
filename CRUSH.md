# Wolf Goat Pig Project - CRUSH.md

This file outlines essential commands and code style guidelines for agentic coding.

## Build/Lint/Test Commands

### Backend (Python)
- Run all tests: `cd backend && pytest tests/ -v`
- Run a single test file: `cd backend && pytest tests/path/to/your_test_file.py -v`
- Run tests with coverage: `cd backend && pytest tests/ -v --cov=app`
- Format code: `cd backend && black app/ tests/ && isort app/ tests/`
- Type checking: `cd backend && mypy app/`

### Frontend (JavaScript/React)
- Install dependencies: `cd frontend && npm install`
- Run all tests: `cd frontend && npm test`
- Run a single test file: `cd frontend && npm test -- src/components/__tests__/YourComponent.test.js`
- Build for production: `cd frontend && npm run build`
- Run development server: `cd frontend && npm start`
- Format code: `cd frontend && npm run format`

## Code Style Guidelines

### Python Backend
- Follow PEP 8, use type hints, and write docstrings.
- Keep functions concise (<50 lines); use `async/await` for DB ops.
- Business logic in services; error handling and logging always.
- Prefer functional patterns; use JAX/NumPy for simulation calculations.
- Use vectorized operations for performance.

### JavaScript/React Frontend
- Use functional components with hooks, follow React best practices for state.
- Keep components small; use meaningful names.
- Implement error boundaries, PropTypes/TypeScript types.
- Follow existing patterns; handle API calls with loading states/error boundaries.
- Ensure responsive design and consistent styling.

## Agent Guidelines (from .cursorrules & CLAUDE.md)

### Interactive Simulation Flow (CRITICAL)
- **Exact chronological pattern:** Hole Setup -> Tee Shots -> Captain Decision (if human, backend returns `interaction_needed`) -> Partnership Response (if human, backend returns `interaction_needed`) -> Hole Completion -> Betting -> Educational Summary.
- **Decision Timing:** NEVER make decisions before seeing shot results. All decisions are contextual and informed.
- **Backend-Frontend Sync:** Backend returns `interaction_needed` for human decisions; Frontend shows UI and continues simulation after decision.
- **Comments:** Add comments sparingly, focusing on _why_ complex logic is implemented.
