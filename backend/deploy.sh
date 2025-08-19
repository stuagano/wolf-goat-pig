#!/bin/bash

# Wolf-Goat-Pig Deployment Script
# Supports multiple deployment targets: Render, Docker, local

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Display usage
show_usage() {
    echo "Wolf-Goat-Pig Deployment Script"
    echo "================================"
    echo ""
    echo "Usage: $0 [TARGET] [OPTIONS]"
    echo ""
    echo "Targets:"
    echo "  local       - Deploy locally using Python/uvicorn"
    echo "  docker      - Deploy using Docker"
    echo "  docker-dev  - Deploy using Docker with development settings"
    echo "  render      - Prepare for Render.com deployment"
    echo "  heroku      - Prepare for Heroku deployment"
    echo "  health      - Check deployment health"
    echo ""
    echo "Options:"
    echo "  --environment ENV  - Set environment (development, production, testing)"
    echo "  --port PORT       - Set port number (default: 8000)"
    echo "  --host HOST       - Set host address (default: 0.0.0.0)"
    echo "  --check-only      - Only check prerequisites, don't deploy"
    echo "  --force-seed      - Force data re-seeding"
    echo "  --skip-tests      - Skip running tests before deployment"
    echo "  --help           - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 local --environment development"
    echo "  $0 docker --port 3000"
    echo "  $0 render --environment production"
}

# Check prerequisites
check_prerequisites() {
    local target=$1
    
    log_info "Checking prerequisites for $target deployment..."
    
    # Common checks
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        return 1
    fi
    
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt not found"
        return 1
    fi
    
    # Target-specific checks
    case $target in
        "docker"|"docker-dev")
            if ! command -v docker &> /dev/null; then
                log_error "Docker is required but not installed"
                return 1
            fi
            
            if ! command -v docker-compose &> /dev/null; then
                log_warning "docker-compose not found, using docker compose instead"
            fi
            ;;
        
        "render")
            if [ -z "$RENDER_API_KEY" ]; then
                log_warning "RENDER_API_KEY not set - manual deployment required"
            fi
            ;;
        
        "heroku")
            if ! command -v heroku &> /dev/null; then
                log_error "Heroku CLI is required but not installed"
                return 1
            fi
            ;;
    esac
    
    log_success "Prerequisites check passed"
    return 0
}

# Run tests
run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log_warning "Skipping tests"
        return 0
    fi
    
    log_info "Running tests..."
    
    if [ -f "tests/test_bootstrapping.py" ]; then
        python -m pytest tests/test_bootstrapping.py -v
        if [ $? -eq 0 ]; then
            log_success "Bootstrap tests passed"
        else
            log_error "Bootstrap tests failed"
            return 1
        fi
    else
        log_warning "Bootstrap tests not found"
    fi
    
    return 0
}

# Deploy locally
deploy_local() {
    log_info "Deploying locally..."
    
    # Install dependencies
    log_info "Installing dependencies..."
    pip install -r requirements.txt
    
    # Run startup script
    python startup.py \
        --environment="${ENVIRONMENT:-development}" \
        --host="${HOST:-0.0.0.0}" \
        --port="${PORT:-8000}" \
        ${FORCE_SEED:+--force-seed}
}

# Deploy with Docker
deploy_docker() {
    local dev_mode=$1
    
    if [ "$dev_mode" = "true" ]; then
        log_info "Deploying with Docker (development mode)..."
        target="development"
    else
        log_info "Deploying with Docker (production mode)..."
        target="production"
    fi
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating .env file from example..."
        cp .env.example .env
    fi
    
    # Build and start services
    if command -v docker-compose &> /dev/null; then
        docker-compose build --target $target
        docker-compose up -d
    else
        docker compose build --target $target
        docker compose up -d
    fi
    
    log_success "Docker deployment started"
    
    # Show running containers
    log_info "Running containers:"
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
}

# Prepare for Render.com deployment
deploy_render() {
    log_info "Preparing for Render.com deployment..."
    
    # Create/update render.yaml if needed
    if [ ! -f "render.yaml" ]; then
        log_info "Creating render.yaml..."
        cat > render.yaml << EOF
services:
  - type: web
    name: wolf-goat-pig-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python startup.py --environment=production --no-reload
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: SKIP_SEEDING
        value: false
      - key: LOG_LEVEL
        value: INFO
    healthCheckPath: /health
EOF
        log_success "render.yaml created"
    fi
    
    # Validate Procfile
    if [ ! -f "Procfile" ]; then
        log_info "Creating Procfile..."
        echo "web: python startup.py --environment=production --host=0.0.0.0 --port=\$PORT --no-reload" > Procfile
        log_success "Procfile created"
    fi
    
    log_success "Render.com deployment preparation complete"
    log_info "Next steps:"
    log_info "1. Commit and push your changes to your repository"
    log_info "2. Connect your repository to Render.com"
    log_info "3. Set environment variables in Render dashboard"
    log_info "4. Deploy!"
}

# Prepare for Heroku deployment
deploy_heroku() {
    log_info "Preparing for Heroku deployment..."
    
    # Create/update Procfile
    if [ ! -f "Procfile" ]; then
        log_info "Creating Procfile..."
        echo "web: python startup.py --environment=production --host=0.0.0.0 --port=\$PORT --no-reload" > Procfile
        echo "release: python startup.py --seed-only" >> Procfile
    fi
    
    # Create runtime.txt
    if [ ! -f "runtime.txt" ]; then
        log_info "Creating runtime.txt..."
        echo "python-3.11.0" > runtime.txt
    fi
    
    # Create app.json for Heroku Button
    if [ ! -f "app.json" ]; then
        log_info "Creating app.json..."
        cat > app.json << EOF
{
  "name": "Wolf-Goat-Pig Golf Simulation API",
  "description": "A comprehensive golf betting simulation API",
  "keywords": ["golf", "simulation", "api", "python", "fastapi"],
  "env": {
    "ENVIRONMENT": {
      "description": "Environment type",
      "value": "production"
    },
    "LOG_LEVEL": {
      "description": "Logging level",
      "value": "INFO"
    },
    "SKIP_SEEDING": {
      "description": "Skip data seeding on startup",
      "value": "false"
    }
  },
  "formation": {
    "web": {
      "quantity": 1,
      "size": "hobby"
    }
  },
  "buildpacks": [
    {
      "url": "heroku/python"
    }
  ]
}
EOF
    fi
    
    log_success "Heroku deployment preparation complete"
    log_info "Next steps:"
    log_info "1. heroku create your-app-name"
    log_info "2. git push heroku main"
    log_info "3. heroku config:set ENVIRONMENT=production"
    log_info "4. heroku open"
}

# Check deployment health
check_health() {
    local url=${1:-"http://localhost:8000"}
    
    log_info "Checking deployment health at $url..."
    
    # Wait for service to be ready
    for i in {1..30}; do
        if curl -s "$url/health" > /dev/null 2>&1; then
            break
        fi
        log_info "Waiting for service to be ready... ($i/30)"
        sleep 2
    done
    
    # Get health status
    health_response=$(curl -s "$url/health" 2>/dev/null || echo '{"status":"error"}')
    health_status=$(echo "$health_response" | python -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "error")
    
    case $health_status in
        "healthy")
            log_success "Deployment is healthy"
            ;;
        "degraded")
            log_warning "Deployment is running with warnings"
            ;;
        "unhealthy"|"error")
            log_error "Deployment is unhealthy"
            return 1
            ;;
        *)
            log_error "Unable to determine health status"
            return 1
            ;;
    esac
    
    return 0
}

# Parse command line arguments
TARGET=""
ENVIRONMENT=""
PORT=""
HOST=""
CHECK_ONLY="false"
FORCE_SEED="false"
SKIP_TESTS="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --check-only)
            CHECK_ONLY="true"
            shift
            ;;
        --force-seed)
            FORCE_SEED="true"
            shift
            ;;
        --skip-tests)
            SKIP_TESTS="true"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        -*)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [ -z "$TARGET" ]; then
                TARGET="$1"
            else
                log_error "Multiple targets specified: $TARGET and $1"
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Default target
if [ -z "$TARGET" ]; then
    TARGET="local"
fi

# Main execution
log_info "Wolf-Goat-Pig Deployment Script"
log_info "Target: $TARGET"

# Check prerequisites
if ! check_prerequisites "$TARGET"; then
    exit 1
fi

if [ "$CHECK_ONLY" = "true" ]; then
    log_success "Prerequisites check passed - deployment ready"
    exit 0
fi

# Run tests
if ! run_tests; then
    log_error "Tests failed - aborting deployment"
    exit 1
fi

# Deploy based on target
case $TARGET in
    "local")
        deploy_local
        ;;
    "docker")
        deploy_docker false
        ;;
    "docker-dev")
        deploy_docker true
        ;;
    "render")
        deploy_render
        ;;
    "heroku")
        deploy_heroku
        ;;
    "health")
        check_health "${2:-http://localhost:8000}"
        ;;
    *)
        log_error "Unknown target: $TARGET"
        show_usage
        exit 1
        ;;
esac

log_success "Deployment complete!"

# Final health check for local and docker deployments
if [[ "$TARGET" == "local" || "$TARGET" == "docker"* ]]; then
    sleep 5  # Give service time to start
    check_health
fi