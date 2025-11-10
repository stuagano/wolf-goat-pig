#!/usr/bin/env python3
"""
Custom linter for catching PostgreSQL transaction issues.

Detects:
1. Datetime objects assigned to String columns (type mismatches)
2. Missing rollback in exception handlers within query loops
3. Potential transaction abort cascades

Usage:
    python lint_db_transactions.py [path]
    python lint_db_transactions.py app/
    python lint_db_transactions.py app/seed_data.py
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class LintIssue:
    """Represents a linting issue found in code."""
    file_path: str
    line_number: int
    severity: str  # 'error', 'warning'
    rule_id: str
    message: str
    code_snippet: str


class DatabaseTransactionLinter:
    """Linter for database transaction patterns."""

    def __init__(self):
        self.issues: List[LintIssue] = []

        # Pattern 1: Datetime objects assigned without .isoformat()
        self.datetime_assignment_pattern = re.compile(
            r'(created_at|updated_at|last_played|joined_at|completed_at|'
            r'earned_date|score_date|ghin_last_updated|signup_time|message_time)'
            r'\s*=\s*datetime\.(now|utcnow)\(\)(?!\s*\.isoformat)',
            re.IGNORECASE
        )

        # Pattern 2: Query in loop with exception handler
        self.loop_query_pattern = re.compile(
            r'for\s+\w+\s+in\s+.*?:',
            re.MULTILINE
        )

    def lint_file(self, file_path: str) -> List[LintIssue]:
        """Lint a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Check for datetime assignment issues
            self._check_datetime_assignments(file_path, lines)

            # Check for missing rollback in loops
            self._check_loop_rollbacks(file_path, content, lines)

            return self.issues

        except Exception as e:
            print(f"Error linting {file_path}: {e}", file=sys.stderr)
            return []

    def _check_datetime_assignments(self, file_path: str, lines: List[str]):
        """Check for datetime objects assigned to timestamp fields without .isoformat()."""
        for line_num, line in enumerate(lines, start=1):
            # Skip comments
            if line.strip().startswith('#'):
                continue

            match = self.datetime_assignment_pattern.search(line)
            if match:
                field_name = match.group(1)
                self.issues.append(LintIssue(
                    file_path=file_path,
                    line_number=line_num,
                    severity='error',
                    rule_id='DB001',
                    message=f"Datetime object assigned to '{field_name}' without .isoformat(). "
                            f"PostgreSQL String columns require ISO format strings.",
                    code_snippet=line.strip()
                ))

    def _check_loop_rollbacks(self, file_path: str, content: str, lines: List[str]):
        """Check for missing rollback in exception handlers within loops."""
        # Look for loops with queries and exception handlers
        loop_blocks = self._find_loop_blocks(content, lines)

        for loop_start, loop_end in loop_blocks:
            loop_content = '\n'.join(lines[loop_start:loop_end])

            # Check if loop contains database queries
            has_query = bool(re.search(r'(db|self\.db)\.query\(', loop_content))
            if not has_query:
                continue

            # Check for exception handlers
            exception_blocks = self._find_exception_handlers(loop_content)

            for exc_handler in exception_blocks:
                # Check if handler has 'continue' statement
                if 'continue' not in exc_handler:
                    continue

                # Check if handler has rollback
                has_rollback = bool(re.search(
                    r'(db|self\.db)\.rollback\(\)',
                    exc_handler
                ))

                if not has_rollback:
                    # Find the actual line number of the exception handler
                    exc_line = self._find_exception_line(lines, loop_start, exc_handler)

                    self.issues.append(LintIssue(
                        file_path=file_path,
                        line_number=exc_line,
                        severity='warning',
                        rule_id='DB002',
                        message="Database query in loop with exception handler missing rollback. "
                                "Failed queries abort transactions - add db.rollback() before 'continue'.",
                        code_snippet=lines[exc_line - 1].strip() if exc_line > 0 else ''
                    ))

    def _find_loop_blocks(self, content: str, lines: List[str]) -> List[Tuple[int, int]]:
        """Find all for-loop blocks in the code."""
        blocks = []
        in_loop = False
        loop_start = 0
        loop_indent = 0

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                continue

            current_indent = len(line) - len(stripped)

            # Detect loop start
            if re.match(r'for\s+\w+\s+in\s+.*?:', stripped):
                in_loop = True
                loop_start = i
                loop_indent = current_indent
                continue

            # Detect loop end (dedent)
            if in_loop and current_indent <= loop_indent and stripped:
                blocks.append((loop_start, i))
                in_loop = False

        # Handle loop at end of file
        if in_loop:
            blocks.append((loop_start, len(lines)))

        return blocks

    def _find_exception_handlers(self, code_block: str) -> List[str]:
        """Find exception handler blocks in code."""
        handlers = []
        lines = code_block.split('\n')
        in_handler = False
        handler_lines = []
        handler_indent = 0

        for line in lines:
            stripped = line.lstrip()
            if not stripped:
                if in_handler:
                    handler_lines.append(line)
                continue

            current_indent = len(line) - len(stripped)

            # Detect exception handler start
            if re.match(r'except\s+.*?:', stripped):
                in_handler = True
                handler_indent = current_indent
                handler_lines = [line]
                continue

            # Collect handler lines
            if in_handler:
                if current_indent > handler_indent or not stripped:
                    handler_lines.append(line)
                else:
                    # End of handler
                    handlers.append('\n'.join(handler_lines))
                    in_handler = False
                    handler_lines = []

        # Handle handler at end of block
        if in_handler and handler_lines:
            handlers.append('\n'.join(handler_lines))

        return handlers

    def _find_exception_line(self, lines: List[str], start_offset: int, exc_handler: str) -> int:
        """Find the line number of an exception handler."""
        exc_first_line = exc_handler.split('\n')[0]
        for i in range(start_offset, len(lines)):
            if exc_first_line.strip() in lines[i]:
                return i + 1
        return start_offset + 1

    def lint_directory(self, directory: str) -> List[LintIssue]:
        """Recursively lint all Python files in a directory."""
        path = Path(directory)

        if not path.exists():
            print(f"Error: Path '{directory}' does not exist", file=sys.stderr)
            return []

        if path.is_file():
            if path.suffix == '.py':
                return self.lint_file(str(path))
            return []

        # Recursively find all Python files
        python_files = list(path.rglob('*.py'))

        # Exclude test files, migrations, and archived code if desired
        python_files = [
            f for f in python_files
            if not any(exclude in str(f) for exclude in ['__pycache__', '.pyc', 'venv', 'env'])
        ]

        all_issues = []
        for py_file in python_files:
            file_issues = self.lint_file(str(py_file))
            all_issues.extend(file_issues)

        return all_issues

    def print_results(self, issues: List[LintIssue]):
        """Print linting results in a readable format."""
        if not issues:
            print("✓ No database transaction issues found!")
            return

        # Group by severity
        errors = [i for i in issues if i.severity == 'error']
        warnings = [i for i in issues if i.severity == 'warning']

        # Print errors
        if errors:
            print(f"\n{'='*80}")
            print(f"ERRORS ({len(errors)} found)")
            print(f"{'='*80}\n")

            for issue in errors:
                print(f"{issue.file_path}:{issue.line_number}")
                print(f"  [{issue.rule_id}] {issue.severity.upper()}: {issue.message}")
                print(f"  > {issue.code_snippet}")
                print()

        # Print warnings
        if warnings:
            print(f"\n{'='*80}")
            print(f"WARNINGS ({len(warnings)} found)")
            print(f"{'='*80}\n")

            for issue in warnings:
                print(f"{issue.file_path}:{issue.line_number}")
                print(f"  [{issue.rule_id}] {issue.severity.upper()}: {issue.message}")
                print(f"  > {issue.code_snippet}")
                print()

        # Summary
        print(f"\n{'='*80}")
        print(f"Summary: {len(errors)} errors, {len(warnings)} warnings")
        print(f"{'='*80}\n")

        # Exit with error code if errors found
        if errors:
            sys.exit(1)


def main():
    """Main entry point for the linter."""
    if len(sys.argv) < 2:
        # Default to current directory
        target = 'app/'
    else:
        target = sys.argv[1]

    linter = DatabaseTransactionLinter()

    print(f"Linting database transaction patterns in: {target}")
    print(f"{'='*80}\n")

    issues = linter.lint_directory(target)
    linter.print_results(issues)


if __name__ == '__main__':
    main()
