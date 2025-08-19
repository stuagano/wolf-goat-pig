# Wolf-Goat-Pig Project Structure

## Directory Organization

```
wolf-goat-pig/
├── backend/              # Backend application code
│   ├── app/             # Main application modules
│   │   ├── domain/      # Domain models and business logic
│   │   ├── services/    # Service layer
│   │   └── state/       # State management
│   └── archive/         # Archived/deprecated code
│
├── frontend/            # Frontend React application
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── context/     # React context providers
│   │   ├── hooks/       # Custom React hooks
│   │   ├── pages/       # Page components
│   │   ├── theme/       # Theme configuration
│   │   └── utils/       # Utility functions
│   └── build/           # Production build files
│
├── tests/               # All test files
│   ├── backend/         # Backend-specific tests
│   ├── frontend/        # Frontend-specific tests
│   ├── integration/     # Integration tests
│   ├── unit/           # Unit tests
│   ├── features/       # BDD feature files
│   └── fixtures/       # Test data and fixtures
│
├── scripts/            # Utility scripts
│   ├── deployment/     # Deployment scripts
│   └── development/    # Development tools and scripts
│
├── config/             # Configuration files
│   ├── pytest.ini      # Pytest configuration
│   ├── render.yaml     # Render deployment config
│   └── vercel.json     # Vercel deployment config
│
├── docs/               # Documentation
│   ├── architecture/   # Architecture documentation
│   ├── prd/           # Product requirement documents
│   ├── qa/            # QA documentation
│   └── stories/       # User stories
│
└── reports/           # Generated reports, logs, and databases
```

## Key Directories

### Backend (`/backend`)
Contains the Python FastAPI application with game logic, API endpoints, and database models.

### Frontend (`/frontend`)
React application providing the user interface for the Wolf-Goat-Pig game.

### Tests (`/tests`)
Organized test suite separated by type and scope for better maintainability.

### Scripts (`/scripts`)
Utility scripts for deployment, development, database operations, and automation.

### Config (`/config`)
Centralized configuration files for various tools and deployment platforms.

### Documentation (`/docs`)
Comprehensive documentation including architecture decisions, requirements, and development guides.