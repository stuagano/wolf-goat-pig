#!/bin/bash

echo "🚀 Setting up Claude GitHub Automation"
echo "======================================"

# Check if claude command exists
if ! command -v claude &> /dev/null; then
    echo "❌ Claude CLI not found. Please install Claude Code first:"
    echo "   Visit: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

echo "✅ Claude CLI found"

# Create .claude-triggers directory
mkdir -p .claude-triggers/processed
echo "✅ Created trigger directories"

# Add .claude-triggers to .gitignore if not already there
if ! grep -q ".claude-triggers" .gitignore 2>/dev/null; then
    echo -e "\n# Claude automation triggers" >> .gitignore
    echo ".claude-triggers/processed/" >> .gitignore
    echo "✅ Updated .gitignore"
fi

# Make monitor script executable
chmod +x claude-issue-monitor.py
echo "✅ Made monitor script executable"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To use this automation:"
echo "1. Push the changes to GitHub:"
echo "   git add . && git commit -m 'Add Claude automation' && git push"
echo ""
echo "2. Start the monitor on your local machine:"
echo "   ./claude-issue-monitor.py"
echo ""
echo "3. Create a GitHub issue from your phone with label 'claude-session'"
echo "   (or any issue will trigger if you don't add labels)"
echo ""
echo "4. The monitor will detect the issue and start a Claude session!"
echo ""
echo "Optional: Set up as a service to run automatically:"
echo "  - macOS: Use launchd"
echo "  - Linux: Use systemd"
echo "  - Or run in tmux/screen session"