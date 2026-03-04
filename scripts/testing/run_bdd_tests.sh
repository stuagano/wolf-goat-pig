#!/bin/bash

# Run BDD tests for Wolf Goat Pig Monte Carlo simulation
echo "🧪 Running BDD tests for Wolf Goat Pig Monte Carlo simulation..."

# Check if required dependencies are installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Please install testing dependencies first:"
    echo "   ./scripts/install_test_dependencies.sh"
    exit 1
fi

# Check if backend is running
echo "🔍 Checking if backend server is running..."
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo "❌ Backend server not responding on port 8000"
    echo "   Please start the backend server:"
    echo "   cd backend && python -m uvicorn app.main:app --reload"
    exit 1
fi

# Check if frontend is running
echo "🔍 Checking if frontend server is running..."
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ Frontend server not responding on port 3000"
    echo "   Please start the frontend server:"
    echo "   cd frontend && npm start"
    exit 1
fi

echo "✅ Both servers are running!"

# Create reports directory if it doesn't exist
mkdir -p reports

# Set default test options
TEST_OPTIONS=""
HTML_REPORT="--html=reports/bdd_test_report.html --self-contained-html"
JUNIT_REPORT="--junitxml=reports/bdd_junit.xml"

# Parse command line arguments
HEADLESS=true
VERBOSE=false
MARKERS="bdd"
PARALLEL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --headed)
            HEADLESS=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            TEST_OPTIONS="$TEST_OPTIONS -v"
            shift
            ;;
        --smoke)
            MARKERS="bdd and smoke"
            shift
            ;;
        --slow)
            MARKERS="bdd"
            shift
            ;;
        --parallel|-n)
            PARALLEL="-n auto"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --headed      Run tests with visible browser (default: headless)"
            echo "  --verbose,-v  Verbose output"
            echo "  --smoke       Run only smoke tests"
            echo "  --slow        Include slow tests"
            echo "  --parallel,-n Run tests in parallel"
            echo "  --help,-h     Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set environment variables
if [ "$HEADLESS" = false ]; then
    export HEADLESS=false
    echo "🖥️  Running tests with visible browser"
else
    export HEADLESS=true
    echo "👻 Running tests in headless mode"
fi

if [ "$VERBOSE" = true ]; then
    echo "📢 Verbose output enabled"
fi

# Run the tests
echo "🚀 Starting BDD tests..."
echo "📋 Test markers: $MARKERS"

pytest \
    -m "$MARKERS" \
    $TEST_OPTIONS \
    $HTML_REPORT \
    $JUNIT_REPORT \
    $PARALLEL \
    tests/

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All BDD tests passed!"
    echo "📊 Test report available at: reports/bdd_test_report.html"
    echo "📄 JUnit report available at: reports/bdd_junit.xml"
else
    echo ""
    echo "❌ Some tests failed. Check the reports for details:"
    echo "📊 HTML report: reports/bdd_test_report.html"
    echo "📄 JUnit report: reports/bdd_junit.xml"
    exit 1
fi

echo ""
echo "🎯 Test Summary:"
echo "   • Feature tests: Gherkin scenarios testing user workflows"
echo "   • API tests: Direct endpoint validation"
echo "   • Integration tests: Full stack testing"
echo "   • Visual tests: UI component verification"
echo ""
echo "💡 To run specific test types:"
echo "   pytest -m 'bdd and smoke'     # Quick smoke tests"
echo "   pytest -m 'bdd and slow'      # Long-running tests"
echo "   pytest tests/test_monte_carlo_api.py  # API tests only"