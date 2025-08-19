# Coding Standards

## Overview
This document defines the coding standards and best practices for the Wolf Goat Pig project, ensuring consistency, maintainability, and quality across the codebase.

## Python Backend Standards

### Code Style
- **PEP 8** compliance for all Python code
- **Black** formatter with 88 character line length
- **isort** for import organization

### Naming Conventions
```python
# Classes: PascalCase
class GameState:
    pass

# Functions/Methods: snake_case
def calculate_betting_odds():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_PLAYERS = 4
DEFAULT_HANDICAP = 10.0

# Private methods: leading underscore
def _validate_action():
    pass
```

### Type Hints
Always use type hints for function signatures:
```python
from typing import List, Dict, Optional

def process_action(
    action: str,
    payload: Dict[str, Any],
    game_state: Optional[GameState] = None
) -> ActionResponse:
    pass
```

### Docstrings
Use Google-style docstrings for all public functions and classes:
```python
def calculate_press(current_bet: int, press_count: int) -> int:
    """Calculate the pressed bet amount.
    
    Args:
        current_bet: The current bet amount
        press_count: Number of times to press
        
    Returns:
        The new bet amount after pressing
        
    Raises:
        ValueError: If press_count is negative
    """
    pass
```

### Error Handling
- Use specific exception types
- Always include context in error messages
- Log errors appropriately
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed for user {user_id}: {e}")
    raise APIException(
        status_code=400,
        detail=f"Could not complete operation: {str(e)}"
    )
```

## JavaScript/React Frontend Standards

### Code Style
- **ESLint** configuration for consistency
- **Prettier** for automatic formatting
- Semicolons optional but consistent within files

### Component Structure
```javascript
// Functional components with hooks
const GameComponent = ({ gameId, onUpdate }) => {
  const [state, setState] = useState(null);
  const theme = useTheme();
  
  useEffect(() => {
    // Effect logic
  }, [gameId]);
  
  return (
    <div className="game-component">
      {/* JSX content */}
    </div>
  );
};

// PropTypes or TypeScript for type checking
GameComponent.propTypes = {
  gameId: PropTypes.string.isRequired,
  onUpdate: PropTypes.func
};
```

### Naming Conventions
```javascript
// Components: PascalCase
const PlayerCard = () => {};

// Functions: camelCase
const calculateScore = () => {};

// Constants: UPPER_SNAKE_CASE
const MAX_RETRIES = 3;
const API_TIMEOUT = 30000;

// Files: 
// - Components: PascalCase.js (PlayerCard.js)
// - Utilities: camelCase.js (apiHelpers.js)
```

### State Management
- Use React Context for global state
- Keep component state minimal
- Lift state up when shared between components
```javascript
// Good: Centralized game state
const GameContext = createContext();

const GameProvider = ({ children }) => {
  const [gameState, setGameState] = useState(null);
  // ... provider logic
};

// Avoid: Duplicate state across components
```

## API Design Standards

### Endpoint Naming
- Use RESTful conventions
- Plural nouns for resources
- Clear action verbs for operations
```
GET    /api/games          # List games
POST   /api/games          # Create game
GET    /api/games/{id}     # Get specific game
POST   /api/games/action   # Unified action endpoint
```

### Request/Response Format
- Always use JSON
- Consistent field naming (snake_case for Python, camelCase for JS)
- Include metadata in responses
```json
{
  "success": true,
  "data": {
    "game_id": "abc123",
    "current_hole": 5
  },
  "message": "Action completed successfully",
  "timestamp": "2025-08-18T12:00:00Z"
}
```

### Error Responses
Consistent error format:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_ACTION",
    "message": "Cannot make partnership request at this time",
    "details": {
      "current_phase": "scoring",
      "expected_phase": "betting"
    }
  }
}
```

## Testing Standards

### Test Organization
```python
# Test file naming: test_<module>.py
tests/
  test_game_state.py
  test_betting_logic.py
  test_api_endpoints.py
```

### Test Structure
```python
class TestGameState:
    """Test game state management."""
    
    def test_initialization(self):
        """Test game state initialization with default values."""
        # Arrange
        players = create_test_players()
        
        # Act
        game_state = GameState(players=players)
        
        # Assert
        assert game_state.current_hole == 1
        assert len(game_state.players) == 4
```

### Coverage Requirements
- Minimum 70% code coverage
- 100% coverage for critical game logic
- Integration tests for all API endpoints

## Git Standards

### Commit Messages
Follow conventional commits:
```
feat: Add partnership request validation
fix: Correct betting calculation for presses
docs: Update API documentation for new endpoints
test: Add integration tests for game flow
refactor: Simplify action processing logic
```

### Branch Naming
```
feature/partnership-rules
fix/betting-calculation
docs/api-updates
test/integration-suite
```

### Pull Request Guidelines
- Clear description of changes
- Link to related issues
- Include test results
- Update documentation

## Documentation Standards

### Code Comments
- Explain WHY, not WHAT
- Document complex algorithms
- Include examples for tricky logic
```python
# Calculate press multiplier using geometric progression
# This ensures exponential bet growth for dramatic gameplay
press_multiplier = 2 ** press_count
```

### README Files
Each major directory should have a README:
- Purpose of the module
- Key components
- Usage examples
- Dependencies

### API Documentation
- Use FastAPI's automatic documentation
- Include request/response examples
- Document all error cases
- Provide curl examples

## Performance Standards

### Backend Performance
- API responses < 200ms
- Database queries optimized with indexes
- Pagination for large result sets
- Caching for expensive calculations

### Frontend Performance
- Page load < 2 seconds
- Code splitting for large components
- Lazy loading for routes
- Optimized images and assets

## Security Standards

### Input Validation
- Validate all user inputs
- Use Pydantic models for type safety
- Sanitize data before storage
- Prevent SQL injection

### Authentication & Authorization
- Secure session management
- Environment variables for secrets
- HTTPS only in production
- CORS properly configured

### Data Protection
- No sensitive data in logs
- Encrypt sensitive information
- Regular security audits
- Follow OWASP guidelines

## Code Review Checklist

Before submitting code:
- [ ] Passes all tests
- [ ] Follows naming conventions
- [ ] Includes appropriate comments
- [ ] Updates documentation
- [ ] No console.log or print statements
- [ ] Handles errors gracefully
- [ ] Performance considerations addressed
- [ ] Security best practices followed

## Continuous Improvement

These standards are living documents:
- Review quarterly
- Update based on team feedback
- Incorporate new best practices
- Document exceptions and rationale

---

*Version: 1.0*
*Last Updated: 2025-08-18*
*Next Review: Q1 2025*