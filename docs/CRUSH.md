# Wolf Goat Pig Golf Simulation - CRUSH.md

## Build/Test/Lint Commands:

- **Backend (Python)**:
  - Install dependencies: `pip install -r backend/requirements.txt`
  - Run all tests: `pytest backend/tests/`
  - Run a specific test file: `pytest backend/tests/test_simulation_components.py`
  - Run a specific test case: `pytest backend/tests/test_simulation_components.py::test_shot_distance_calculation`
  - Run backend linter (ruff): `ruff check backend/`
  - Run backend type checker (mypy): `mypy backend/` (requires mypy to be installed)

- **Frontend (React.js)**:
  - Install dependencies: `npm install`
  - Run tests: `npm test`
  - Run frontend linter (ESLint): `npm run lint`

## Code Style Guidelines:

### Python (Backend):
- **Imports**: Organize imports using `isort` (e.g., `isort backend/`). Follow standard library, third-party, and then local imports, each group separated by a newline.
- **Formatting**: Adhere to `black` formatting standards (e.g., `black backend/`).
- **Types**: Use strict type hints for all function arguments and return types.
- **Naming Conventions**:
    - Variables/functions: `snake_case`
    - Classes: `PascalCase`
    - Constants: `SCREAMING_SNAKE_CASE`
- **Error Handling**: Use explicit `try...except` blocks for anticipated errors. Provide informative error messages.
- **Functional Programming**: Prefer functional programming patterns over classes where feasible, especially for simulation calculations (utilizing JAX/NumPy).
- **Vectorized Operations**: Use vectorized operations for performance-critical simulation calculations.

### JavaScript/React (Frontend):
- **Imports**: Use absolute paths for internal modules.
- **Formatting**: Adhere to Prettier formatting standards.
- **React Hooks**: Utilize React hooks for state management and side effects.
- **API Calls**: Handle asynchronous operations with loading states and error boundaries.
- **Responsive Design**: Ensure components are responsive and maintain consistent styling.

## Cursor/Copilot Rules & General Guidelines:

## Project Structure Preferences
- All documentation files (.md) should be located in the `docs/` directory.

- **Interactive Flow**: Maintain the exact chronological simulation pattern (Hole Setup -> Tee Shots -> Captain Decision -> Partnership Response -> Hole Completion -> Betting -> Educational Summary).
- **Decision Timing**: Never make decisions before seeing shot results. All decisions are contextual and informed.
- **Contextual Decisions**: Human decisions must always be- **GHIN Integration**: Ensure real golfer data integration is seamless and secure.
- **Comments**: Add comments sparingly, focusing on _why_ complex logic is implemented.

