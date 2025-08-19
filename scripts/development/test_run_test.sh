#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
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

# Test counter
passed=0
failed=0

echo "Testing run_test function..."

# Test 1: Should pass
run_test "Always Pass" "echo 'success'" && ((passed++)) || ((failed++))
echo "After test 1: passed=$passed, failed=$failed"

# Test 2: Should pass
run_test "Python Version" "python --version" && ((passed++)) || ((failed++))
echo "After test 2: passed=$passed, failed=$failed"

# Test 3: Should pass
run_test "Dictionary References" "python test_dict_references.py" && ((passed++)) || ((failed++))
echo "After test 3: passed=$passed, failed=$failed"

echo ""
echo "Final results:"
echo "Passed: $passed"
echo "Failed: $failed" 