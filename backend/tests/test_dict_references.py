#!/usr/bin/env python3
"""
Dictionary Reference Detector
Searches for old dictionary-style access patterns that should be using Player object attributes
"""

import os
import re
import sys
from pathlib import Path

class DictReferenceDetector:
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def log_error(self, file_path: str, line_num: int, line: str, pattern: str):
        self.errors.append({
            'file': file_path,
            'line': line_num,
            'content': line.strip(),
            'pattern': pattern
        })
        
    def log_warning(self, file_path: str, line_num: int, line: str, pattern: str):
        self.warnings.append({
            'file': file_path,
            'line': line_num,
            'content': line.strip(),
            'pattern': pattern
        })
    
    def scan_file(self, file_path: str):
        """Scan a single file for dictionary reference patterns"""
        if not file_path.endswith('.py'):
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                # Skip comments and docstrings
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                    
                # Pattern 1: player["key"] - should be player.key
                if re.search(r'player\[["\']\w+["\']\]', line):
                    self.log_error(file_path, line_num, line, 'player["key"] should be player.key')
                
                # Pattern 2: p["key"] for p in players - should be p.key for p in players
                if re.search(r'p\[["\']\w+["\']\]\s+for\s+p\s+in', line):
                    self.log_error(file_path, line_num, line, 'p["key"] for p in should be p.key for p in')
                
                # Pattern 3: next(p for p in ... if p["key"] == ...) - should be p.key
                if re.search(r'next\(.*p\[["\']\w+["\']\].*\)', line):
                    self.log_error(file_path, line_num, line, 'next(...p["key"]...) should be next(...p.key...)')
                
                # Pattern 4: game_state.players - should be game_state.player_manager.players
                if re.search(r'game_state\.players\[', line):
                    self.log_error(file_path, line_num, line, 'game_state.players should be game_state.player_manager.players')
                
                # Pattern 5: player.get("key") - should be hasattr(player, 'key') and player.key
                if re.search(r'player\.get\(["\']\w+["\']\)', line):
                    self.log_warning(file_path, line_num, line, 'player.get("key") should be hasattr(player, "key") and player.key')
                
                # Pattern 6: Dictionary access in list comprehensions
                if re.search(r'\[.*\[["\']\w+["\']\].*for.*in.*players', line):
                    self.log_error(file_path, line_num, line, 'Dictionary access in list comprehension with players')
                
                # Pattern 7: Lambda functions with dictionary access on player objects specifically
                if re.search(r'lambda\s+\w+:\s*\w+\[["\']\w+["\']\]', line):
                    if ('players' in line or 'player' in line) and not ('summary' in line or 'statistics' in line):
                        self.log_error(file_path, line_num, line, 'Lambda with dictionary access on player objects')
                
                # Pattern 8: f-strings with dictionary access on player objects specifically
                if re.search(r'f["\'].*\{.*\[["\']\w+["\']\].*\}.*["\']', line):
                    if ('player' in line or 'players' in line) and not ('details' in line or 'summary' in line or 'statistics' in line):
                        self.log_error(file_path, line_num, line, 'f-string with dictionary access on player objects')
        except Exception as e:
            print(f"Warning: Could not scan {file_path}: {e}")
    
    def scan_directory(self, directory: str):
        """Scan all Python files in a directory recursively"""
        for root, dirs, files in os.walk(directory):
            # Skip virtual environments and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', '__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.scan_file(file_path)
    
    def print_results(self):
        """Print scan results"""
        print("🔍 Dictionary Reference Scan Results")
        print("=" * 50)
        
        if self.errors:
            print(f"\n❌ ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"  File: {error['file']}:{error['line']}")
                print(f"  Pattern: {error['pattern']}")
                print(f"  Line: {error['content']}")
                print()
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  File: {warning['file']}:{warning['line']}")
                print(f"  Pattern: {warning['pattern']}")
                print(f"  Line: {warning['content']}")
                print()
        
        if not self.errors and not self.warnings:
            print("✅ No dictionary reference issues found!")
        
        print(f"\n📊 Summary:")
        print(f"  Errors: {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        
        return len(self.errors) == 0

def main():
    """Main function"""
    detector = DictReferenceDetector()
    
    # Scan the app directory
    app_dir = os.path.join(os.path.dirname(__file__), 'app')
    if os.path.exists(app_dir):
        print(f"🔍 Scanning {app_dir} for dictionary references...")
        detector.scan_directory(app_dir)
    else:
        print(f"❌ App directory not found: {app_dir}")
        sys.exit(1)
    
    # Print results
    success = detector.print_results()
    
    if not success:
        print("\n🚨 Dictionary reference issues found - deployment may fail!")
        sys.exit(1)
    else:
        print("\n✅ No dictionary reference issues found!")

if __name__ == "__main__":
    main() 