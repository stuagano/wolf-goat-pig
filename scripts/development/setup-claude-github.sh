#!/bin/bash

# Setup script for Claude GitHub Actions integration
# This script helps configure the necessary secrets for Claude Code

set -e

echo "🤖 Claude Code GitHub Actions Setup"
echo "===================================="
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "Please install it first: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated with gh
if ! gh auth status &> /dev/null; then
    echo "❌ You are not authenticated with GitHub CLI."
    echo "Please run: gh auth login"
    exit 1
fi

# Get repository information
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
if [ -z "$REPO" ]; then
    echo "❌ Could not detect repository. Make sure you're in a git repository."
    exit 1
fi

echo "📦 Repository: $REPO"
echo ""

# Function to set a secret
set_secret() {
    local secret_name=$1
    local secret_value=$2
    
    echo "Setting secret: $secret_name"
    echo "$secret_value" | gh secret set "$secret_name" --repo "$REPO"
}

# Check for Anthropic API key
echo "🔑 Anthropic API Key Setup"
echo "--------------------------"
echo "You need an Anthropic API key to use Claude Code."
echo "Get one at: https://console.anthropic.com/settings/keys"
echo ""

if gh secret list --repo "$REPO" | grep -q "ANTHROPIC_API_KEY"; then
    echo "✅ ANTHROPIC_API_KEY already exists"
    read -p "Do you want to update it? (y/N): " update_key
    if [[ ! "$update_key" =~ ^[Yy]$ ]]; then
        echo "Keeping existing key."
    else
        read -s -p "Enter your Anthropic API key: " api_key
        echo ""
        set_secret "ANTHROPIC_API_KEY" "$api_key"
        echo "✅ ANTHROPIC_API_KEY updated"
    fi
else
    read -s -p "Enter your Anthropic API key: " api_key
    echo ""
    if [ -z "$api_key" ]; then
        echo "❌ API key cannot be empty"
        exit 1
    fi
    set_secret "ANTHROPIC_API_KEY" "$api_key"
    echo "✅ ANTHROPIC_API_KEY set"
fi

echo ""
echo "🔧 Optional Configuration"
echo "------------------------"

# Optional: Docker Hub credentials
read -p "Do you want to configure Docker Hub credentials? (y/N): " setup_docker
if [[ "$setup_docker" =~ ^[Yy]$ ]]; then
    read -p "Enter Docker Hub username: " docker_user
    read -s -p "Enter Docker Hub password/token: " docker_pass
    echo ""
    set_secret "DOCKER_USERNAME" "$docker_user"
    set_secret "DOCKER_PASSWORD" "$docker_pass"
    echo "✅ Docker Hub credentials set"
fi

# Optional: Other services
echo ""
read -p "Do you want to configure additional services (Codecov, SonarCloud, etc.)? (y/N): " setup_additional

if [[ "$setup_additional" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Additional service setup:"
    
    # Codecov
    read -p "Codecov token (press Enter to skip): " codecov_token
    if [ ! -z "$codecov_token" ]; then
        set_secret "CODECOV_TOKEN" "$codecov_token"
        echo "✅ CODECOV_TOKEN set"
    fi
    
    # SonarCloud
    read -p "SonarCloud token (press Enter to skip): " sonar_token
    if [ ! -z "$sonar_token" ]; then
        set_secret "SONAR_TOKEN" "$sonar_token"
        echo "✅ SONAR_TOKEN set"
    fi
    
    # Netlify
    read -p "Netlify auth token (press Enter to skip): " netlify_token
    if [ ! -z "$netlify_token" ]; then
        set_secret "NETLIFY_AUTH_TOKEN" "$netlify_token"
        read -p "Netlify site ID: " netlify_site
        set_secret "NETLIFY_SITE_ID" "$netlify_site"
        echo "✅ Netlify credentials set"
    fi
fi

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📝 Next Steps:"
echo "1. The Claude GitHub Action is configured in .github/workflows/claude.yml"
echo "2. You can now use @claude in issues and PR comments"
echo "3. Check CLAUDE.md for project-specific guidelines"
echo ""
echo "💡 Example usage in a GitHub issue or PR:"
echo "   @claude can you help me fix the test failures?"
echo "   @claude please review this PR and suggest improvements"
echo "   @claude implement user authentication with JWT tokens"
echo ""
echo "📚 For more information, visit:"
echo "   https://docs.anthropic.com/en/docs/claude-code/github-actions"