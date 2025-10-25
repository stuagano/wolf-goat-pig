#!/bin/bash
# Wolf-Goat-Pig Podman Testing Script
# Simulates Render (backend) and Vercel (frontend) environments locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.local"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_podman() {
    if ! command -v podman &> /dev/null; then
        print_error "Podman is not installed"
        echo "Install with: brew install podman"
        exit 1
    fi
    print_success "Podman is installed"
}

check_podman_compose() {
    if ! command -v podman-compose &> /dev/null; then
        print_error "podman-compose is not installed"
        echo "Install with: pip install podman-compose"
        exit 1
    fi
    print_success "podman-compose is installed"
}

check_podman_machine() {
    if ! podman machine list | grep -q "Currently running"; then
        print_info "Starting Podman machine..."
        podman machine start || {
            print_info "No Podman machine found. Initializing..."
            podman machine init
            podman machine start
        }
    fi
    print_success "Podman machine is running"
}

# Command handlers
start_services() {
    print_header "Starting Production-like Environment"

    check_podman
    check_podman_compose
    check_podman_machine

    print_info "Using environment file: $ENV_FILE"
    print_info "Using compose file: $COMPOSE_FILE"

    # Build and start services
    print_info "Building and starting services..."
    podman-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up --build -d

    print_success "Services started!"
    print_info ""
    print_info "Access points:"
    print_info "  Backend API: http://localhost:8000"
    print_info "  Frontend:    http://localhost:3000"
    print_info "  API Docs:    http://localhost:8000/docs"
    print_info "  Health:      http://localhost:8000/health"
    print_info ""
    print_info "View logs with: ./podman-test.sh logs"
    print_info "Stop services with: ./podman-test.sh stop"
}

stop_services() {
    print_header "Stopping Services"
    podman-compose -f "$COMPOSE_FILE" down
    print_success "Services stopped"
}

restart_services() {
    print_header "Restarting Services"
    podman-compose -f "$COMPOSE_FILE" restart
    print_success "Services restarted"
}

view_logs() {
    SERVICE=$1
    if [ -z "$SERVICE" ]; then
        print_header "Viewing All Logs"
        podman-compose -f "$COMPOSE_FILE" logs -f
    else
        print_header "Viewing Logs for $SERVICE"
        podman-compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
    fi
}

show_status() {
    print_header "Service Status"
    podman-compose -f "$COMPOSE_FILE" ps
}

run_tests() {
    print_header "Running Tests in Production Environment"

    print_info "Running backend tests..."
    podman-compose -f "$COMPOSE_FILE" exec backend pytest tests/ -v

    print_success "Tests completed"
}

shell_backend() {
    print_header "Opening Shell in Backend Container"
    podman-compose -f "$COMPOSE_FILE" exec backend bash
}

rebuild() {
    print_header "Rebuilding Services"
    podman-compose -f "$COMPOSE_FILE" down
    podman-compose -f "$COMPOSE_FILE" build --no-cache
    podman-compose -f "$COMPOSE_FILE" up -d
    print_success "Services rebuilt"
}

clean_all() {
    print_header "Cleaning Up Everything"
    print_info "This will remove all containers, images, and volumes"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        podman-compose -f "$COMPOSE_FILE" down -v
        podman system prune -af --volumes
        print_success "Cleanup complete"
    else
        print_info "Cancelled"
    fi
}

show_help() {
    cat << EOF
Wolf-Goat-Pig Podman Testing Script

Usage: $0 [command]

Commands:
  start       Start all services (backend, frontend, postgres)
  stop        Stop all services
  restart     Restart all services
  status      Show service status
  logs        View logs for all services
  logs <svc>  View logs for specific service (backend/frontend/postgres)
  test        Run tests in production environment
  shell       Open bash shell in backend container
  rebuild     Rebuild all services from scratch
  clean       Remove all containers, images, and volumes
  help        Show this help message

Environment:
  - Uses $COMPOSE_FILE for service definitions
  - Uses $ENV_FILE for environment variables
  - Simulates Render (backend) and Vercel (frontend) deployments

Examples:
  $0 start              # Start all services
  $0 logs backend       # View backend logs
  $0 test               # Run tests
  $0 shell              # Open shell in backend
  $0 clean              # Clean everything

EOF
}

# Main command dispatcher
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        view_logs "$2"
        ;;
    test)
        run_tests
        ;;
    shell)
        shell_backend
        ;;
    rebuild)
        rebuild
        ;;
    clean)
        clean_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
