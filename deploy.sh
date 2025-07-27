#!/bin/bash

# Wolf Goat Pig Golf Simulation - Deployment Script

set -e

echo "🚀 Wolf Goat Pig Golf Simulation - Deployment Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "render.yaml" ] || [ ! -f "vercel.json" ]; then
    print_error "Please run this script from the root directory of the project"
    exit 1
fi

# Function to setup backend
setup_backend() {
    print_status "Setting up backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Initialize database
    print_status "Initializing database..."
    python -c "from app.database import init_db; init_db()"
    
    print_success "Backend setup complete!"
    cd ..
}

# Function to setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    cd frontend
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    print_success "Frontend setup complete!"
    cd ..
}

# Function to run tests
run_tests() {
    print_status "Running comprehensive test suite..."
    
    cd backend
    source venv/bin/activate
    
    # Run tests
    python -m pytest tests/test_unified_action_api.py -v
    
    print_success "All tests passed!"
    cd ..
}

# Function to start development servers
start_dev() {
    print_status "Starting development servers..."
    
    # Start backend in background
    cd backend
    source venv/bin/activate
    print_status "Starting backend server on http://localhost:8000"
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend
    cd frontend
    print_status "Starting frontend server on http://localhost:3000"
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    print_success "Development servers started!"
    print_status "Backend: http://localhost:8000"
    print_status "Frontend: http://localhost:3000"
    print_status "API Docs: http://localhost:8000/docs"
    
    # Wait for user to stop servers
    echo ""
    print_warning "Press Ctrl+C to stop all servers"
    
    # Function to cleanup on exit
    cleanup() {
        print_status "Stopping servers..."
        kill $BACKEND_PID 2>/dev/null || true
        kill $FRONTEND_PID 2>/dev/null || true
        print_success "Servers stopped!"
        exit 0
    }
    
    # Set trap to cleanup on exit
    trap cleanup SIGINT SIGTERM
    
    # Wait for background processes
    wait
}

# Function to build for production
build_production() {
    print_status "Building for production..."
    
    # Build frontend
    cd frontend
    print_status "Building frontend..."
    npm run build
    cd ..
    
    print_success "Production build complete!"
}

# Function to start production server
start_production() {
    print_status "Starting production server..."
    
    cd backend
    source venv/bin/activate
    
    # Start production server
    print_status "Starting production backend server on http://localhost:8000"
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     - Setup both backend and frontend"
    echo "  backend   - Setup backend only"
    echo "  frontend  - Setup frontend only"
    echo "  test      - Run comprehensive test suite"
    echo "  dev       - Start development servers"
    echo "  build     - Build for production"
    echo "  prod      - Start production server"
    echo "  deploy    - Full deployment (setup + build + prod)"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup     # Setup everything"
    echo "  $0 dev       # Start development servers"
    echo "  $0 deploy    # Full deployment"
}

# Main script logic
case "${1:-help}" in
    "setup")
        setup_backend
        setup_frontend
        print_success "Complete setup finished!"
        ;;
    "backend")
        setup_backend
        ;;
    "frontend")
        setup_frontend
        ;;
    "test")
        run_tests
        ;;
    "dev")
        start_dev
        ;;
    "build")
        build_production
        ;;
    "prod")
        start_production
        ;;
    "deploy")
        setup_backend
        setup_frontend
        run_tests
        build_production
        print_success "Deployment complete! Run '$0 prod' to start production server"
        ;;
    "help"|*)
        show_help
        ;;
esac 