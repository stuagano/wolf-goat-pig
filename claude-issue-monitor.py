#!/usr/bin/env python3
"""
Claude Issue Monitor - Polls for GitHub issue triggers and starts Claude sessions
"""

import os
import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

class ClaudeIssueMonitor:
    def __init__(self, repo_path=None, poll_interval=30):
        self.repo_path = Path(repo_path or os.getcwd())
        self.triggers_dir = self.repo_path / '.claude-triggers'
        self.processed_dir = self.triggers_dir / 'processed'
        self.poll_interval = poll_interval
        
        # Create directories if they don't exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
    def check_git_updates(self):
        """Pull latest changes from git"""
        try:
            result = subprocess.run(
                ['git', 'pull', '--quiet'], 
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error pulling git updates: {e}")
            return False
    
    def get_new_triggers(self):
        """Find new trigger files that haven't been processed"""
        if not self.triggers_dir.exists():
            return []
        
        new_triggers = []
        for trigger_file in self.triggers_dir.glob('issue-*.json'):
            processed_file = self.processed_dir / trigger_file.name
            if not processed_file.exists():
                new_triggers.append(trigger_file)
        
        return sorted(new_triggers)
    
    def process_trigger(self, trigger_file):
        """Process a single trigger file and start Claude session"""
        try:
            with open(trigger_file, 'r') as f:
                trigger_data = json.load(f)
            
            print(f"📝 New issue trigger: #{trigger_data['issue_number']}")
            print(f"   Title: {trigger_data['issue_title']}")
            print(f"   User: {trigger_data['user']}")
            print(f"   URL: {trigger_data['issue_url']}")
            
            # Create Claude prompt from issue
            prompt = self.create_claude_prompt(trigger_data)
            
            # Start Claude session
            self.start_claude_session(prompt, trigger_data)
            
            # Mark as processed
            processed_file = self.processed_dir / trigger_file.name
            trigger_file.rename(processed_file)
            
            return True
            
        except Exception as e:
            print(f"Error processing trigger {trigger_file}: {e}")
            return False
    
    def create_claude_prompt(self, trigger_data):
        """Create a prompt for Claude based on the issue data"""
        prompt = f"""GitHub Issue #{trigger_data['issue_number']}: {trigger_data['issue_title']}

From: {trigger_data['user']}
URL: {trigger_data['issue_url']}

Issue Description:
{trigger_data['issue_body']}

---

Please help me address this GitHub issue. Analyze the request and implement any necessary changes to the codebase."""
        
        return prompt
    
    def start_claude_session(self, prompt, trigger_data):
        """Start a new Claude session with the given prompt"""
        try:
            # Option 1: Use Claude Code CLI directly
            cmd = ['claude', '--prompt', prompt]
            
            print(f"🚀 Starting Claude session for issue #{trigger_data['issue_number']}")
            
            # Start Claude in a new terminal/session
            if sys.platform == 'darwin':  # macOS
                # Open new Terminal window with Claude
                applescript = f'''
                tell application "Terminal"
                    do script "cd '{self.repo_path}' && echo '{prompt}' | claude"
                    activate
                end tell
                '''
                subprocess.run(['osascript', '-e', applescript])
            else:
                # For Linux/Windows, just run in current terminal
                subprocess.run(cmd, cwd=self.repo_path)
                
        except Exception as e:
            print(f"Error starting Claude session: {e}")
            print("Falling back to manual prompt...")
            print("="*50)
            print(prompt)
            print("="*50)
    
    def run(self):
        """Main monitoring loop"""
        print(f"🔍 Monitoring {self.repo_path} for Claude triggers...")
        print(f"📁 Watching: {self.triggers_dir}")
        print(f"⏱️  Poll interval: {self.poll_interval}s")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                # Pull latest changes
                self.check_git_updates()
                
                # Check for new triggers
                new_triggers = self.get_new_triggers()
                
                for trigger_file in new_triggers:
                    self.process_trigger(trigger_file)
                
                if new_triggers:
                    print(f"✅ Processed {len(new_triggers)} trigger(s)")
                
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\n👋 Stopping Claude Issue Monitor")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor GitHub issues and start Claude sessions')
    parser.add_argument('--repo-path', help='Path to repository (default: current directory)')
    parser.add_argument('--interval', type=int, default=30, help='Poll interval in seconds (default: 30)')
    
    args = parser.parse_args()
    
    monitor = ClaudeIssueMonitor(
        repo_path=args.repo_path,
        poll_interval=args.interval
    )
    
    monitor.run()

if __name__ == '__main__':
    main()