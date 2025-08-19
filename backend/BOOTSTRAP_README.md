# Wolf-Goat-Pig Bootstrap System

This document describes the comprehensive bootstrap system implemented to fix the "simulation not found" errors and ensure reliable application startup.

## Overview

The bootstrap system ensures that the Wolf-Goat-Pig application can start reliably in any environment with proper data seeding, error handling, and fallback mechanisms.

## Key Components

### 1. Data Seeding (`app/seed_data.py`)

Comprehensive data seeding script that initializes:

- **Golf Courses**: Default courses with realistic hole data
- **Game Rules**: Complete Wolf-Goat-Pig rules set  
- **AI Personalities**: 6 different AI players with unique playing styles
- **Sample Games**: Historical game data for testing
- **Default Players**: Fallback human player if none exist

**Features:**
- Idempotent seeding (safe to run multiple times)
- Comprehensive error handling
- Data verification and validation
- Status reporting and logging

**Usage:**
```bash
# Run complete seeding
python -m app.seed_data

# Check seeding status
python -m app.seed_data --status

# Force re-seeding
python -m app.seed_data --force
```

### 2. Enhanced Startup (`app/main.py`)

The main application startup has been enhanced with:

- **Automatic Seeding**: Checks and seeds data on startup
- **Error Recovery**: Continues operation even with partial failures
- **Simulation Verification**: Tests simulation initialization
- **Comprehensive Logging**: Detailed startup progress tracking

**Key Features:**
- Environment-aware seeding (skip with `SKIP_SEEDING=true`)
- Graceful fallbacks when systems fail
- Non-blocking startup (app starts even with warnings)

### 3. Health Check System (`/health` endpoint)

Comprehensive health checking that verifies:

- Database connectivity
- Course data availability  
- Rules and AI personalities
- Simulation engine functionality
- Game state management
- Data seeding status

**Health States:**
- `healthy`: All systems operational
- `degraded`: Some warnings but functional
- `unhealthy`: Critical systems failing

### 4. Robust Error Handling

The system includes multiple layers of error handling:

**Course Management:**
- Database fallback to in-memory courses
- Emergency course generation
- Automatic course reloading

**Game Initialization:**
- Smart player data defaults
- Course validation with fallbacks  
- Simulation engine recovery
- Minimal state creation for critical failures

**Database Operations:**
- Connection retry logic
- Transaction rollback handling
- Graceful degradation

### 5. Startup Script (`startup.py`)

Comprehensive startup script providing:

- Environment validation
- Dependency checking
- Database initialization
- Data seeding coordination  
- Health verification
- Server launching

**Usage Examples:**
```bash
# Complete startup with verification
python startup.py

# Health check only  
python startup.py --check-health

# Data seeding only
python startup.py --seed-only

# Force re-seeding
python startup.py --seed-only --force-seed

# Verify setup without starting server
python startup.py --verify-setup
```

### 6. Docker Support

Complete containerization support:

**Dockerfile:**
- Multi-stage build (builder + production)
- Security-focused (non-root user)
- Health check integration
- Development variant

**Docker Compose:**
- Full development environment
- PostgreSQL database option
- Redis cache support
- Admin interfaces

**Scripts:**
- `docker-startup.sh`: Container startup logic
- `deploy.sh`: Multi-target deployment

### 7. Deployment Support

Multi-platform deployment preparation:

- **Render.com**: `render.yaml` configuration
- **Heroku**: `Procfile` and `app.json`
- **Docker**: Production-ready containers
- **Local**: Development server

### 8. Testing Suite (`tests/test_bootstrapping.py`)

Comprehensive test coverage:

- Database initialization testing
- Data seeding validation
- Startup sequence verification
- Health check functionality
- Error recovery scenarios
- Game initialization resilience

**Test Categories:**
- `TestDatabaseBootstrapping`: Database setup and connection
- `TestDataSeeding`: Data initialization and validation
- `TestApplicationStartup`: Startup sequence testing
- `TestHealthChecks`: Health check endpoint testing
- `TestGameInitializationResilience`: Error handling testing
- `TestSystemRecovery`: Fallback mechanism testing

## Configuration

### Environment Variables

**Core Settings:**
- `ENVIRONMENT`: `development`, `production`, `testing`
- `LOG_LEVEL`: Logging verbosity
- `DATABASE_URL`: Database connection string
- `SKIP_SEEDING`: Skip automatic seeding

**Server Settings:**
- `HOST`: Server bind address (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)

**Feature Flags:**
- `ENABLE_DOCS`: API documentation endpoints
- `AUTO_RELOAD`: Development auto-reload
- `SEED_SAMPLE_DATA`: Include sample games

See `.env.example` for complete configuration options.

## Deployment

### Local Development

```bash
# Using startup script (recommended)
python startup.py --environment=development

# Using deployment script  
./deploy.sh local --environment=development

# Direct FastAPI (basic)
uvicorn app.main:app --reload
```

### Docker Deployment

```bash
# Development
./deploy.sh docker-dev

# Production
./deploy.sh docker

# Manual Docker
docker build -t wgp-api .
docker run -p 8000:8000 wgp-api
```

### Cloud Platforms

```bash
# Prepare for Render.com
./deploy.sh render

# Prepare for Heroku  
./deploy.sh heroku

# Check deployment health
./deploy.sh health http://your-app.com
```

## Troubleshooting

### Common Issues

**"simulation not found" errors:**
- Check health endpoint: `GET /health`
- Verify data seeding: `python startup.py --seed-only`
- Check logs for initialization errors

**Database connection issues:**
- Verify `DATABASE_URL` if using PostgreSQL
- Check SQLite file permissions for local development
- Run database health check

**Missing course data:**
- Force re-seeding: `python startup.py --seed-only --force-seed`  
- Check course endpoint: `GET /courses`
- Verify fallback course generation

**Health check failures:**
- Run comprehensive check: `python startup.py --check-health`
- Review component-specific errors in response
- Check application logs

### Debug Mode

Enable comprehensive logging:

```bash
export LOG_LEVEL=DEBUG
python startup.py --log-level=DEBUG
```

### Recovery Procedures

**Complete system reset:**
```bash
# Clear database and re-initialize
rm wolf_goat_pig.db
python startup.py --force-seed
```

**Partial recovery:**
```bash  
# Re-seed specific components
python -m app.seed_data --force
```

**Emergency fallback:**
```bash
# Start with minimal data
export SKIP_SEEDING=true
python startup.py
```

## API Endpoints

### Bootstrap-Related Endpoints

- `GET /health`: Comprehensive system health check
- `GET /courses`: Course data with fallback handling  
- `GET /rules`: Game rules with error recovery
- `POST /wgp/{game_id}/action`: Game actions with robust initialization

### Health Check Response

```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "environment": "development|production|testing", 
  "version": "1.0.0",
  "components": {
    "database": {"status": "healthy", "message": "Connection successful"},
    "courses": {"status": "healthy", "message": "3 courses available"},
    "simulation": {"status": "healthy", "message": "Engine operational"},
    "data_seeding": {"status": "healthy", "message": "All data seeded"}
  }
}
```

## Development

### Adding New Bootstrap Components

1. **Data Seeding**: Add to `seed_data.py`
2. **Health Checks**: Update `health_check()` in `main.py`  
3. **Tests**: Add to `test_bootstrapping.py`
4. **Fallbacks**: Implement in relevant managers

### Testing Bootstrap Changes

```bash
# Run bootstrap-specific tests
pytest tests/test_bootstrapping.py -v

# Test full startup sequence
python startup.py --verify-setup

# Test error scenarios  
SKIP_SEEDING=true python startup.py --check-health
```

## Monitoring

### Key Metrics to Monitor

- Health check response time
- Data seeding duration  
- Database connection stability
- Course data availability
- Simulation initialization success rate

### Logging

The system provides structured logging with these levels:

- `DEBUG`: Detailed component information
- `INFO`: Startup progress and status
- `WARNING`: Non-critical issues with fallbacks
- `ERROR`: Critical failures requiring attention

### Alerts

Consider setting up alerts for:

- Health check failures (`status != "healthy"`)
- Startup time > 60 seconds
- Database connection errors
- Missing critical data (courses, rules)

## Contributing

When making changes to the bootstrap system:

1. **Update Tests**: Add tests for new functionality
2. **Update Documentation**: Keep this README current  
3. **Test All Paths**: Verify success and failure scenarios
4. **Check Fallbacks**: Ensure graceful degradation
5. **Validate Health Checks**: Update health check logic

## Support

For bootstrap-related issues:

1. Check the health endpoint
2. Review application logs  
3. Run diagnostic commands
4. Consult troubleshooting section
5. Report issues with full logs and health check output