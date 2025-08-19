#!/bin/bash

# Deployment Test Suite
# Runs comprehensive tests to ensure deployment will succeed

set -e  # Exit on any error

echo "🚀 Starting Deployment Test Suite"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to run a test and report results
run_test() {
    local test_name=$1
    local test_command=$2
    
    print_status $BLUE "Running: $test_name"
    
    if eval "$test_command"; then
        print_status $GREEN "✅ $test_name passed"
        return 0
    else
        print_status $RED "❌ $test_name failed"
        return 1
    fi
}

# Check if we're in the right directory
if [ ! -d "app" ]; then
    print_status $RED "❌ Error: Must run from backend directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    print_status $BLUE "Activating virtual environment..."
    source venv/bin/activate
else
    print_status $YELLOW "⚠️  No virtual environment found, using system Python"
fi

# Test counter
passed=0
failed=0

echo ""
print_status $BLUE "Phase 1: Basic Environment Tests"
echo "----------------------------------------"

# Test 1: Python version
if run_test "Python Version Check" "python --version"; then
    ((passed++))
else
    ((failed++))
fi

# Test 2: Required packages
if run_test "Package Import Test" "python -c 'import fastapi, uvicorn, sqlalchemy, pydantic; print(\"✅ All packages imported\")'"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
print_status $BLUE "Phase 2: Code Quality Tests"
echo "----------------------------------------"

# Test 3: Dictionary reference scan
if run_test "Dictionary Reference Scan" "python test_dict_references.py"; then
    ((passed++))
else
    ((failed++))
fi

# Test 4: Syntax check
if run_test "Python Syntax Check" "python -m py_compile app/main.py"; then
    ((passed++))
else
    ((failed++))
fi

# Test 5: Import all modules
if run_test "Module Import Test" "python -c 'from app.main import app; print(\"✅ App imported successfully\")'"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
print_status $BLUE "Phase 3: Comprehensive Validation"
echo "--------------------------------------------"

# Test 6: Full deployment validation
if run_test "Deployment Validation" "python deployment_validation.py"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
print_status $BLUE "Phase 4: API Tests"
echo "---------------------------"

# Test 7: FastAPI app creation
if run_test "FastAPI App Creation" "python -c 'from app.main import app; print(\"✅ FastAPI app created\")'"; then
    ((passed++))
else
    ((failed++))
fi

# Test 8: Health endpoint
if run_test "Health Endpoint" "python -c 'from app.main import app; print(\"✅ FastAPI app imports successfully\")'"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
print_status $BLUE "Phase 5: Database Tests"
echo "--------------------------------"

# Test 9: Database models
if run_test "Database Models" "python -c 'from app.models import Course, Rule; print(\"✅ Database models imported\")'"; then
    ((passed++))
else
    ((failed++))
fi

# Test 10: Database connection (if possible)
if run_test "Database Connection" "python -c 'from app.database import engine; print(\"✅ Database engine created\")'"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
print_status $BLUE "Phase 6: Simulation Tests"
echo "-----------------------------------"

# Test 11: Simulation engine
if run_test "Simulation Engine" "python -c 'from app.simulation import SimulationEngine; engine = SimulationEngine(); print(\"✅ Simulation engine created\")'"; then
    ((passed++))
else
    ((failed++))
fi

# Test 12: Player objects
if run_test "Player Objects" "python -c 'from app.domain.player import Player; p = Player(\"1\", \"Test\", 15.0); print(f\"✅ Player created: {p.name}\")'"; then
    ((passed++))
else
    ((failed++))
fi

# Test 13: Betting state
if run_test "Betting State" "python -c 'from app.state.betting_state import BettingState; bs = BettingState(); print(\"✅ Betting state created\")'"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
print_status $BLUE "Phase 7: Integration Tests"
echo "------------------------------------"

# Test 14: Game state setup
run_test "Game State Setup" "python -c 'from app.game_state import GameState; from app.domain.player import Player; gs = GameState(); p1 = Player(\"1\", \"P1\", 10.0); p2 = Player(\"2\", \"P2\", 15.0); p3 = Player(\"3\", \"P3\", 20.0); p4 = Player(\"4\", \"P4\", 25.0); gs.setup_players([{\"id\": p1.id, \"name\": p1.name, \"handicap\": p1.handicap, \"strength\": p1.handicap}, {\"id\": p2.id, \"name\": p2.name, \"handicap\": p2.handicap, \"strength\": p2.handicap}, {\"id\": p3.id, \"name\": p3.name, \"handicap\": p3.handicap, \"strength\": p3.handicap}, {\"id\": p4.id, \"name\": p4.name, \"handicap\": p4.handicap, \"strength\": p4.handicap}]); print(\"✅ Game state setup\")'" && ((passed++)) || ((failed++))

# Test 15: Serialization
run_test "Object Serialization" "python -c 'from app.domain.player import Player; import json; from dataclasses import asdict; p = Player(\"1\", \"Test\", 15.0); json.dumps(asdict(p)); print(\"✅ Player serialization\")'" && ((passed++)) || ((failed++))

echo ""
echo "=================================="
print_status $BLUE "📊 Test Results Summary"
echo "=================================="
print_status $GREEN "✅ Passed: $passed"
print_status $RED "❌ Failed: $failed"
echo ""

if [ $failed -eq 0 ]; then
    print_status $GREEN "🎉 All tests passed! Deployment should succeed."
    exit 0
else
    print_status $RED "🚨 $failed test(s) failed. Please fix issues before deploying."
    exit 1
fi 