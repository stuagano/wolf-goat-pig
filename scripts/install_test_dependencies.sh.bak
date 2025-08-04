#!/bin/bash

# Install testing dependencies for Wolf Goat Pig BDD tests
echo "🔧 Installing testing dependencies for Wolf Goat Pig..."

# Install Python test dependencies
echo "📦 Installing Python testing packages..."
pip install -r requirements-test.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Install additional system dependencies for headless Chrome
echo "🖥️  Installing system dependencies for headless Chrome..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y \
        libnss3 \
        libgconf-2-4 \
        libxss1 \
        libasound2 \
        libxtst6 \
        libgtk-3-0 \
        libdrm2 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libxkbcommon0 \
        libatspi2.0-0
elif command -v yum &> /dev/null; then
    # CentOS/RHEL/Fedora
    sudo yum install -y \
        nss \
        atk \
        at-spi2-atk \
        gtk3 \
        cups-libs \
        libdrm \
        libXt \
        libXrandr \
        alsa-lib \
        mesa-libgbm \
        libXScrnSaver
elif command -v brew &> /dev/null; then
    # macOS
    echo "ℹ️  macOS detected. Playwright should work without additional dependencies."
else
    echo "⚠️  Unable to detect package manager. You may need to install dependencies manually."
fi

# Create test reports directory
echo "📁 Creating test reports directory..."
mkdir -p reports

# Make scripts executable
chmod +x scripts/*.sh

echo "✅ Testing dependencies installed successfully!"
echo ""
echo "🧪 To run the tests:"
echo "  • All tests:           pytest"
echo "  • BDD tests only:      pytest -m bdd"
echo "  • API tests only:      pytest tests/test_monte_carlo_api.py"
echo "  • Smoke tests:         pytest -m smoke"
echo "  • With HTML report:    pytest --html=reports/test_report.html"
echo ""
echo "🚀 Make sure your servers are running:"
echo "  • Backend:  cd backend && python -m uvicorn app.main:app --reload"
echo "  • Frontend: cd frontend && npm start"