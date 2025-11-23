# Claude Agents and Skills for Wolf Goat Pig

This directory contains specialized Claude agents and reusable skills to help maintain and improve the Wolf Goat Pig golf betting simulation project.

## Structure

```
.claude/
├── agents/          # Specialized agents for specific tasks
│   ├── api-docs-agent.md
│   ├── cicd-improvement-agent.md
│   ├── component-testing-agent.md
│   ├── error-handling-agent.md
│   ├── rules-validation-agent.md
│   ├── test-coverage-agent.md
│   └── typescript-migration-agent.md
│
├── skills/          # Reusable skills for common tasks
│   ├── analyze-test-coverage.md
│   ├── check-code-quality.md
│   ├── deploy-to-staging.md
│   ├── generate-api-docs.md
│   └── run-all-tests.md
│
└── README.md       # This file
```

## Agents

Agents are specialized assistants focused on specific areas of the project. Each agent has deep knowledge of their domain and can work autonomously on complex tasks.

### Backend Agents

#### 1. Test Coverage Agent
**File**: `agents/test-coverage-agent.md`

**Purpose**: Improve test coverage for the backend

**Use When**:
- You need to identify untested code paths
- Writing new pytest tests for services and domain logic
- Increasing coverage for critical simulation logic
- Creating test fixtures and parametrized tests

**Key Capabilities**:
- Analyzes pytest coverage reports
- Generates tests for untested functions
- Creates reusable test fixtures
- Focuses on high-priority modules (simulation, betting, odds calculation)

**Example**:
> "Use the test-coverage-agent to analyze backend test coverage and generate tests for the odds_calculator service"

---

#### 2. API Documentation Agent
**File**: `agents/api-docs-agent.md`

**Purpose**: Generate comprehensive API documentation

**Use When**:
- Creating OpenAPI/Swagger specifications
- Adding docstrings to FastAPI endpoints
- Generating API reference guides
- Creating integration documentation

**Key Capabilities**:
- Generates OpenAPI 3.0 specs
- Adds endpoint docstrings with examples
- Creates Postman collections
- Builds integration guides

**Example**:
> "Use the api-docs-agent to document all endpoints in main.py and generate an OpenAPI spec"

---

#### 3. Error Handling Agent
**File**: `agents/error-handling-agent.md`

**Purpose**: Standardize error handling across the API

**Use When**:
- Implementing consistent error responses
- Adding input validation
- Creating custom exceptions
- Setting up structured logging

**Key Capabilities**:
- Creates standard error response schemas
- Implements custom exception classes
- Adds retry logic for external services
- Sets up structured logging with context

**Example**:
> "Use the error-handling-agent to standardize error responses and add validation to game initialization endpoints"

---

### Frontend Agents

#### 4. TypeScript Migration Agent
**File**: `agents/typescript-migration-agent.md`

**Purpose**: Convert frontend from JavaScript to TypeScript

**Use When**:
- Migrating JS components to TypeScript
- Adding type safety to the frontend
- Generating TypeScript types from backend Pydantic models
- Configuring tsconfig.json

**Key Capabilities**:
- Converts .js files to .tsx with proper types
- Generates API types from OpenAPI specs
- Types React components, hooks, and contexts
- Configures strict TypeScript compilation

**Example**:
> "Use the typescript-migration-agent to convert GamePage.js to TypeScript and add proper prop types"

---

#### 5. Component Testing Agent
**File**: `agents/component-testing-agent.md`

**Purpose**: Create frontend component tests

**Use When**:
- Writing Jest and React Testing Library tests
- Testing user interactions
- Creating test utilities and mock factories
- Running accessibility tests

**Key Capabilities**:
- Writes comprehensive component tests
- Tests user interactions (clicks, inputs, navigation)
- Creates reusable test utilities
- Runs accessibility audits with jest-axe

**Example**:
> "Use the component-testing-agent to write tests for the SimulationDecisionPanel component"

---

### Infrastructure & Quality Agents

#### 6. CI/CD Improvement Agent
**File**: `agents/cicd-improvement-agent.md`

**Purpose**: Enhance CI/CD pipeline

**Use When**:
- Setting up GitHub Actions workflows
- Adding automated deployment validation
- Implementing health checks
- Creating rollback procedures

**Key Capabilities**:
- Creates comprehensive CI workflows
- Adds deployment validation and smoke tests
- Implements health check endpoints
- Sets up monitoring and alerts

**Example**:
> "Use the cicd-improvement-agent to create a GitHub Actions workflow that runs all tests on pull requests"

---

#### 7. Rules Validation Agent
**File**: `agents/rules-validation-agent.md`

**Purpose**: Validate game rules implementation

**Use When**:
- Verifying simulation logic matches official rules
- Creating test matrices for rule combinations
- Writing BDD scenarios
- Documenting rule interpretations

**Key Capabilities**:
- Cross-references implementation with official rules
- Creates exhaustive test scenarios
- Writes Gherkin/BDD features
- Documents rule ambiguities

**Example**:
> "Use the rules-validation-agent to verify that the wolf selection logic correctly implements the rotation rules"

---

## Skills

Skills are reusable capabilities that can be invoked for common tasks. They provide step-by-step instructions for frequently performed operations.

### 1. Run All Tests
**File**: `skills/run-all-tests.md`

**Purpose**: Execute the complete test suite

**What It Does**:
- Runs backend pytest with coverage
- Runs BDD Behave tests
- Runs frontend Jest tests
- Runs E2E Playwright tests
- Generates coverage reports

**When to Use**:
- Before committing changes
- Before deploying to staging/production
- After major refactoring
- To verify all tests pass

**Usage**:
```bash
# Follow the steps in skills/run-all-tests.md
# Or invoke as a skill in conversation
```

---

### 2. Check Code Quality
**File**: `skills/check-code-quality.md`

**Purpose**: Run linters, formatters, and type checkers

**What It Does**:
- **Type checks with mypy and TypeScript** (see [Type Checking Guide](type-checking-guide.md))
- Lints backend code with ruff
- Formats with black
- Lints frontend with ESLint
- Runs security checks (safety, npm audit)
- Checks code complexity

**When to Use**:
- Before committing code
- During code review
- To maintain code quality standards
- Before pull requests

**Type Checking**:
```bash
npm run typecheck           # Both backend and frontend
npm run typecheck:backend   # Python with mypy
npm run typecheck:frontend  # TypeScript with tsc
```

See **[Type Checking Guide](type-checking-guide.md)** for detailed instructions.

---

### 3. Deploy to Staging
**File**: `skills/deploy-to-staging.md`

**Purpose**: Deploy application to staging environment

**What It Does**:
- Validates pre-deployment (tests, linting)
- Deploys backend to Render
- Deploys frontend to Vercel
- Runs smoke tests
- Executes E2E tests on staging
- Applies database migrations

**When to Use**:
- Testing new features before production
- Validating bug fixes
- Running integration tests
- Demonstrating to stakeholders

---

### 4. Generate API Docs
**File**: `skills/generate-api-docs.md`

**Purpose**: Create comprehensive API documentation

**What It Does**:
- Generates OpenAPI schema
- Creates markdown documentation
- Generates Postman collection
- Creates interactive HTML docs
- Adds endpoint examples

**When to Use**:
- After adding new endpoints
- When updating API contracts
- For onboarding new developers
- Before external API releases

---

### 5. Analyze Test Coverage
**File**: `skills/analyze-test-coverage.md`

**Purpose**: Analyze and report on test coverage

**What It Does**:
- Generates backend coverage reports
- Generates frontend coverage reports
- Identifies low-coverage files
- Highlights critical untested code
- Creates actionable recommendations
- Tracks coverage trends over time

**When to Use**:
- Planning testing efforts
- Identifying gaps in test coverage
- Prioritizing test writing
- Reporting on testing progress

---

## How to Use

### Using Agents

1. **Identify the Problem**: Determine which agent best matches your task
2. **Reference the Agent**: Mention the agent in your conversation
3. **Provide Context**: Give the agent necessary information
4. **Let It Work**: The agent will work autonomously

**Example Conversation**:
```
You: I need to improve test coverage for the backend simulation logic.

Claude: I'll use the test-coverage-agent to analyze your backend test coverage
and generate tests for untested code paths.

[Agent analyzes code, identifies gaps, generates tests]

Claude: I've added 15 new tests for wolf_goat_pig_simulation.py, increasing
coverage from 72% to 94%.
```

### Using Skills

1. **Identify the Task**: Find the skill that matches your needs
2. **Follow the Steps**: Execute the commands in the skill
3. **Verify Results**: Check that the skill completed successfully

**Example**:
```
You: Run all tests to make sure everything works before I commit.

Claude: I'll use the run-all-tests skill to execute the complete test suite.

[Runs backend pytest, frontend Jest, E2E Playwright tests]

Claude: All tests passed!
- Backend: 245 tests, 87% coverage
- Frontend: 89 tests, 81% coverage
- E2E: 31 tests, all passing
```

## Project-Specific Context

### Key Files and Locations

**Backend**:
- Main API: `/backend/app/main.py` (6,967 lines)
- Game Engine: `/backend/app/wolf_goat_pig_simulation.py` (3,868 lines)
- Services: `/backend/app/services/` (15 services)
- Tests: `/backend/tests/`

**Frontend**:
- Pages: `/frontend/src/pages/`
- Components: `/frontend/src/components/`
- Tests: `/frontend/src/__tests__/` (create if needed)

**E2E Tests**:
- Playwright: `/tests/e2e/tests/`
- BDD: `/tests/bdd/behave/features/`

### Known Issues

Agents are aware of these known issues:
- Python 3.12.0 requirement (some tests fail on 3.11)
- `ball_positions_replace` doesn't fully clear positions
- `ping_pong_count` field not exposed in API responses
- Most frontend is JavaScript (only 3 TypeScript files)
- Limited unit test coverage for components

### Technology Stack

**Backend**:
- FastAPI + Uvicorn
- SQLAlchemy + PostgreSQL (prod) / SQLite (dev)
- Python 3.12.0
- Pytest, Behave (BDD)

**Frontend**:
- React 19.1.1
- React Router 7.8.2
- Jest + React Testing Library
- Playwright (E2E)

**Infrastructure**:
- Render (backend hosting)
- Vercel (frontend hosting)
- GitHub Actions (CI/CD)
- Docker Compose (local development)

**Type Checking**:
- Backend: mypy with strict settings (see [Type Checking Guide](type-checking-guide.md))
- Frontend: TypeScript with strict mode enabled
- 13 core modules fully type-safe
- 874 remaining errors (down from 958)
- Run: `npm run typecheck`

## Guides and Documentation

### [Type Checking Guide](type-checking-guide.md)

Comprehensive guide for type checking in Wolf Goat Pig:
- **Quick Start**: `npm run typecheck`
- Python mypy configuration and best practices
- TypeScript strict mode settings
- Common errors and how to fix them
- Integration with VS Code and CI/CD
- Current status: 13 modules fully type-safe, 874 errors remaining

**Use When**:
- Adding type annotations to new code
- Fixing type errors
- Understanding mypy/TypeScript errors
- Setting up IDE integration

---

## Getting Help

### Agent Selection Guide

**Need to...**
- **Improve test coverage** → Test Coverage Agent
- **Add API documentation** → API Documentation Agent
- **Fix error handling** → Error Handling Agent
- **Add TypeScript** → TypeScript Migration Agent
- **Test components** → Component Testing Agent
- **Improve CI/CD** → CI/CD Improvement Agent
- **Validate game rules** → Rules Validation Agent

**Want to...**
- **Run all tests** → Run All Tests skill
- **Check code quality** → Check Code Quality skill
- **Check types** → [Type Checking Guide](type-checking-guide.md)
- **Deploy to staging** → Deploy to Staging skill
- **Generate API docs** → Generate API Docs skill
- **Analyze coverage** → Analyze Test Coverage skill

## Contributing

To add new agents or skills:

1. **Create a new markdown file** in `agents/` or `skills/`
2. **Follow the existing format**:
   - Clear title and description
   - Defined role/objective
   - Key responsibilities/steps
   - Examples and usage patterns
   - Success criteria
3. **Update this README** with the new agent/skill
4. **Test the agent/skill** to ensure it works as expected

## Maintenance

This `.claude` directory should be updated when:
- New major features are added to the project
- Technology stack changes
- New testing frameworks are adopted
- Deployment processes change
- Common tasks evolve

---

**Last Updated**: 2025-01-23

For questions or suggestions about these agents and skills, please create an issue in the repository.
