#!/bin/bash

# Wolf-Goat-Pig Docker Development Script
# Starts local development environment using Docker containers that mirror cloud deployments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🐺🐐🐷 Wolf-Goat-Pig Docker Development Environment"
echo "=================================================="
echo ""
echo "This will start containers that mirror your Render/Vercel deployments:"
echo "  • PostgreSQL database (matches Render)"
echo "  • Backend API using render-startup.py (matches Render)"
echo "  • Frontend built with npm and served with nginx (matches Vercel)"
echo ""

# Check if .env exists, create from example if not
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file - please update with your values"
    else
        echo "⚠️  .env.example not found, creating basic .env..."
        cat > .env << EOF
POSTGRES_PASSWORD=wgp_password_change_me
ENVIRONMENT=production
REACT_APP_API_URL=http://localhost:8000
EOF
    fi
fi

# Validate critical environment variables
echo "🔍 Validating environment variables..."
if [ -f ".env" ]; then
    # Source .env file to check variables (handle comments and empty lines)
    set -a
    source .env 2>/dev/null || true
    set +a
    
    # Check for critical variables
    if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "wgp_password_change_me" ]; then
        echo "⚠️  WARNING: POSTGRES_PASSWORD is not set or using default value"
        echo "   Please update .env file with a secure password"
    fi
    
    if [ -z "$DATABASE_URL" ] && [ -z "$POSTGRES_PASSWORD" ]; then
        echo "⚠️  WARNING: Database configuration may be incomplete"
    fi
else
    echo "⚠️  WARNING: .env file not found, using defaults"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available (prefer newer 'docker compose' syntax)
if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

echo "🔧 Building and starting containers..."
echo ""

# Build and start services
$DOCKER_COMPOSE up --build -d

echo ""
echo "⏳ Waiting for services to be healthy..."
echo ""

# Wait for backend to be healthy
MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -f http://localhost:8000/ready > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo ""
    echo "⚠️  Backend health check timed out, but containers are running"
    echo "   Check logs with: docker-compose logs backend"
fi

echo ""
echo "========================================="
echo "✅ Development environment is ready!"
echo "========================================="
echo ""
echo "🔗 Frontend:  http://localhost:3000"
echo "🔗 Backend:   http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo "🗄️  Database: localhost:5432"
echo ""
echo "📋 Useful commands:"
echo "   View logs:        docker-compose logs -f [service]"
echo "   Stop services:   docker-compose down"
echo "   Restart:         docker-compose restart [service]"
echo "   Shell access:    docker-compose exec backend bash"
echo "   Database shell:  docker-compose exec postgres psql -U wolf_goat_pig_user -d wolf_goat_pig"
echo ""
echo "Press Ctrl+C to stop all services"

# Follow logs
$DOCKER_COMPOSE logs -f

