# Claude Code Guidelines for Wolf-Goat-Pig Project the best

## Project Overview
Wolf-Goat-Pig is a golf betting game application with a Python FastAPI backend and React frontend. The game involves team-based golf competitions with various betting strategies and scoring systems.

## Recent Fixes and Important Notes

### Frontend Component Import Paths (December 2024)
**Issue**: Module not found error when deploying to Vercel
- Error: `Can't resolve '../common/Card'` in EnhancedPracticeMode.js
- **Solution**: Fixed import path from `../common/Card` to `../ui/Card`
- **Important**: All UI components are located in `/frontend/src/components/ui/` not `/common/`
- **Files affected**: 
  - `/frontend/src/components/practice/EnhancedPracticeMode.js`
- **Key Learning**: Always verify component import paths match actual file structure, especially for:
  - Card component: `import { Card } from '../ui/Card'`
  - Button component: `import { Button } from '../ui/Button'`
  - Other UI components: Check `/frontend/src/components/ui/` directory

## Code Standards

### Python Backend (FastAPI)
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all classes and public methods
- Keep functions focused and under 50 lines when possible
- Use async/await for database operations
- Place business logic in service layers, not directly in routes
- Always add appropriate error handling and logging

### JavaScript/React Frontend
- Use functional components with hooks
- Follow React best practices for state management
- Keep components small and focused
- Use meaningful variable and function names
- Implement proper error boundaries
- Add PropTypes or TypeScript types for all components
- Follow existing patterns in the codebase

## Testing Requirements
- Write tests for all new features
- Maintain test coverage above 80%
- Backend: Use pytest for Python tests
- Frontend: Use Jest and React Testing Library
- Include both unit and integration tests
- Run tests before creating any PR

## Database Guidelines
- Use Alembic for database migrations
- Never modify migrations after they're committed
- Always test migrations on a copy of production data
- Use SQLAlchemy ORM for database operations
- Implement proper indexing for frequently queried fields

## API Design
- Follow RESTful conventions
- Use proper HTTP status codes
- Implement pagination for list endpoints
- Include proper validation for all inputs
- Return consistent error response formats
- Document all endpoints with OpenAPI/Swagger

## Security Practices
- Never commit secrets or API keys
- Use environment variables for configuration
- Implement proper authentication and authorization
- Validate and sanitize all user inputs
- Use HTTPS for all communications
- Follow OWASP guidelines for web security

## Performance Considerations
- Implement caching where appropriate
- Optimize database queries (avoid N+1 problems)
- Use lazy loading for large datasets
- Implement proper pagination
- Monitor and log performance metrics
- Consider implementing rate limiting

## Git Workflow
- Create feature branches from develop
- Write clear, descriptive commit messages
- Keep commits atomic and focused
- Squash commits before merging when appropriate
- Always create PRs for code review
- Update tests and documentation with code changes

## Common Commands

### Backend
```bash
cd backend
# Run tests
pytest tests/ -v
# Run with coverage
pytest tests/ -v --cov=app
# Format code
black app/ tests/
isort app/ tests/
# Type checking
mypy app/
```

### Frontend
```bash
cd frontend
# Install dependencies
npm install
# Run tests
npm test
# Build for production
npm run build
# Run development server
npm start
# Format code
npm run format
```

## Project Structure

### Backend Structure
```
backend/
├── app/
│   ├── api/          # API routes
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   ├── state/        # Game state management
│   └── main.py       # FastAPI application
├── tests/            # Test files
└── requirements.txt  # Python dependencies
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/   # React components
│   ├── hooks/        # Custom React hooks
│   ├── services/     # API services
│   ├── utils/        # Utility functions
│   └── App.js        # Main application
├── public/           # Static assets
└── package.json      # Node dependencies
```

## Important Files to Review
- `backend/app/wolf_goat_pig_simulation.py` - Core game logic
- `backend/app/state/course_manager.py` - Course management
- `frontend/src/components/game/UnifiedGameInterface.js` - Main game UI
- `frontend/src/hooks/useOddsCalculation.js` - Odds calculation logic

## Current Features
- Monte Carlo simulation for outcome predictions
- Player profiling and performance tracking
- Shot analysis and visualization
- Tutorial system for new players
- Real-time betting and scoring
- Team formation and management

## When Responding to Issues

1. **First, understand the context** by reviewing related files
2. **Check existing tests** to understand expected behavior
3. **Follow existing patterns** in the codebase
4. **Write tests** for any new functionality
5. **Update documentation** if changing APIs or adding features
6. **Consider edge cases** and error handling
7. **Ensure backward compatibility** when modifying existing features

## Performance and Scalability Notes
- The application uses SQLite for development, PostgreSQL for production
- Frontend uses React with hooks for state management
- Consider caching frequently accessed data
- Optimize database queries for large datasets
- Use pagination for list views

## Known Issues and Limitations
- Check the issues tab for known bugs
- Review recent PRs for context on recent changes
- Be aware of any technical debt noted in code comments

Remember: Always prioritize code quality, maintainability, and user experience in your implementations.
