# Technology Stack

## Overview
Wolf Goat Pig is built with modern, production-ready technologies chosen for reliability, performance, and developer experience.

## Backend Stack

### Core Framework
- **FastAPI** (v0.110.0+) - Modern Python web framework
  - Automatic API documentation
  - Type safety with Pydantic
  - Async support
  - High performance

### Database
- **SQLAlchemy** (v2.0.30+) - ORM for database operations
- **PostgreSQL** - Production database (Render)
- **SQLite** - Local development database

### Python Dependencies
- **Pydantic** (v2.6.0+) - Data validation and settings management
- **Uvicorn** - ASGI server with hot reload
- **Python-multipart** - Form data handling
- **HTTPX** - HTTP client for external APIs
- **Python-dotenv** - Environment variable management

## Frontend Stack

### Core Framework
- **React** (v18.2.0) - Component-based UI framework
- **React Router** (v6) - Client-side routing
- **Create React App** - Build tooling and configuration

### State Management
- **React Context API** - Global state management
- **Custom Hooks** - Reusable stateful logic

### UI/UX
- **Custom Theme System** - Consistent design language
- **CSS-in-JS** - Dynamic styling
- **Responsive Design** - Mobile-first approach

### Build Tools
- **Webpack** (via CRA) - Module bundling
- **Babel** - JavaScript transpilation
- **ESLint** - Code quality enforcement

## Infrastructure

### Hosting
- **Render** - Backend hosting (Free tier with cold start handling)
  - PostgreSQL database
  - Auto-deploy from GitHub
  - Health monitoring
  
- **Vercel** - Frontend hosting
  - Edge network CDN
  - Automatic HTTPS
  - Preview deployments

### CI/CD
- **GitHub Actions** - Automated workflows
  - Issue-triggered Claude sessions
  - Deployment validation
  - Test automation

### Development Tools
- **BMad Method** - Agile AI-driven development framework
- **Claude Code** - AI pair programming
- **Git** - Version control
- **pytest** - Python testing framework
- **Jest** (via CRA) - JavaScript testing

## API Design

### Architecture Pattern
- **Unified Action API** - Single endpoint for all game actions
- **RESTful principles** - Resource-based URLs
- **JSON** - Data interchange format

### Security
- **CORS** - Cross-origin resource sharing
- **Input validation** - Pydantic models
- **Environment variables** - Secure configuration

## Testing Stack

### Backend Testing
- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **TestClient** - FastAPI testing

### Frontend Testing
- **React Testing Library** - Component testing
- **Jest** - Test runner and assertions

### Integration Testing
- **BDD scenarios** - Behavior-driven development
- **End-to-end testing** - Full stack validation

## Monitoring & Observability

### Health Checks
- Backend: `/health` endpoint
- Frontend: Cold start detection
- Database: Connection validation

### Performance
- Response time targets: <200ms API, <2s page load
- Cold start handling: Graceful UX during warmup
- Scalability: 100+ concurrent games

## Development Environment

### Required Tools
- **Python 3.12+** - Backend runtime
- **Node.js 18+** - Frontend build tools
- **npm/yarn** - Package management
- **Virtual environment** - Python dependency isolation

### IDE Support
- **VS Code** - Primary IDE
- **Claude Code** - AI assistance
- **ESLint** - Code formatting
- **Prettier** - Code style

## Version Management

### Versioning Strategy
- **Semantic Versioning** - Major.Minor.Patch
- **Git Flow** - Feature branches → main
- **Tagged Releases** - Production deployments

### Compatibility
- **Browser Support**: Chrome, Firefox, Safari, Edge (latest 2 versions)
- **Mobile Support**: Responsive design for all screen sizes
- **API Versioning**: Currently v1, backward compatible

## Future Technology Considerations

### Potential Upgrades
- **WebSocket** - Real-time multiplayer
- **Redis** - Session caching
- **GraphQL** - Flexible API queries
- **TypeScript** - Type safety for frontend
- **Next.js** - Server-side rendering

### Scalability Path
- **Kubernetes** - Container orchestration
- **AWS/GCP** - Enterprise cloud platform
- **CDN** - Global content delivery
- **Load Balancing** - Horizontal scaling

---

*Last Updated: 2025-08-18*