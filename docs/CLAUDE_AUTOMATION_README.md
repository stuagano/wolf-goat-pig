# Claude GitHub Automation

This setup allows you to create GitHub issues from your phone and automatically start Claude Code sessions on your local machine.

## How It Works

1. **GitHub Actions**: When you create an issue (or add `claude-session` label), a GitHub Action creates a trigger file
2. **Local Monitor**: A Python script on your machine polls for new trigger files and starts Claude sessions
3. **Automatic Setup**: Claude receives the issue content as context and starts working

## Quick Start

1. Run the setup script:
   ```bash
   ./setup-claude-automation.sh
   ```

2. Push to GitHub:
   ```bash
   git add . && git commit -m "Add Claude automation" && git push
   ```

3. Start the monitor:
   ```bash
   ./claude-issue-monitor.py
   ```

4. Create a GitHub issue from your phone - Claude will automatically start!

## Advanced Setup (Auto-Start)

### macOS (launchd)
```bash
# Copy the service file
cp claude-automation.service ~/Library/LaunchAgents/com.claude.issue-monitor.plist

# Load the service
launchctl load ~/Library/LaunchAgents/com.claude.issue-monitor.plist

# Start the service
launchctl start com.claude.issue-monitor
```

### Linux (systemd)
Create `/etc/systemd/user/claude-monitor.service`:
```ini
[Unit]
Description=Claude Issue Monitor
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/wolf-goat-pig/claude-issue-monitor.py
WorkingDirectory=/path/to/wolf-goat-pig
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

Then:
```bash
systemctl --user enable claude-monitor.service
systemctl --user start claude-monitor.service
```

## Usage Tips

- **Trigger any issue**: All new issues trigger Claude by default
- **Specific trigger**: Add `claude-session` label to trigger only specific issues
- **Issue format**: Write clear descriptions - Claude receives the full issue content
- **Multiple sessions**: Each issue creates a separate Claude session

## Files Created

- `.github/workflows/claude-trigger.yml` - GitHub Actions workflow
- `claude-issue-monitor.py` - Local monitoring script
- `.claude-triggers/` - Trigger files directory (auto-created)
- `claude-automation.service` - Service template for auto-start

## Troubleshooting

- **Monitor not starting**: Check that `claude` command is available in PATH
- **No triggers**: Verify GitHub Actions are enabled for your repository
- **Issues not triggering**: Check GitHub Actions logs in your repository

## Security Notes

- Trigger files contain issue content - they're gitignored by default
- The monitor only reads from your own repository
- Claude sessions run with your local permissions