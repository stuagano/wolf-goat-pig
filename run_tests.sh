#!/bin/bash

echo "🧪 Wolf Goat Pig Functional Test Runner"
echo "========================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if setup has been run
if [ ! -f "requirements-testing.txt" ]; then
    echo "❌ Testing requirements not found. Please run setup first."
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
python3 -c "import selenium, requests, webdriver_manager" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    python3 -m pip install -r requirements-testing.txt
fi

# Run the functional test suite
echo "🚀 Starting functional tests..."
python3 functional_test_suite.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed! Your deployment is working correctly."
    echo "📊 Check functional_test_report.json for detailed results."
else
    echo ""
    echo "⚠️ Some tests failed. Check the report for details."
    echo "📊 Check functional_test_report.json for detailed results."
fi 