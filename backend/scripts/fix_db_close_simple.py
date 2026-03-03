#!/usr/bin/env python3
"""
Simple fix for db.close() in endpoints using Depends(database.get_db)

This script:
1. Finds all functions with 'db: Session = Depends(' in their signature
2. Removes 'finally:\n        db.close()' blocks from those functions
3. Creates a backup before making changes
"""

import re
import sys
from pathlib import Path
from datetime import datetime

def fix_db_close():
    """Remove db.close() from FastAPI endpoints using Depends."""

    main_py = Path('app/main.py')

    if not main_py.exists():
        print("❌ Error: app/main.py not found")
        print("   Run this script from the backend/ directory")
        return False

    # Create backup
    backup_path = main_py.with_suffix(f'.py.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    print(f"📝 Creating backup: {backup_path}")
    backup_path.write_text(main_py.read_text())

    content = main_py.read_text()
    original_content = content

    # Count changes
    changes = []

    # Pattern 1: Remove standalone 'finally:' followed by 'db.close()' in endpoints
    # This matches:
    #     finally:
    #         db.close()
    #
    # But only in functions that have 'db: Session = Depends'

    # Split into lines for easier processing
    lines = content.split('\n')
    new_lines = []

    # Track which functions use Depends(database.get_db)
    in_depends_function = False
    function_name = None
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if we're entering a function with Depends
        if 'async def ' in line or 'def ' in line:
            # Look ahead to see if this function has db: Session = Depends
            lookahead = '\n'.join(lines[i:min(i+10, len(lines))])
            if 'db: Session = Depends(' in lookahead or 'db:Session=Depends(' in lookahead:
                in_depends_function = True
                match = re.search(r'def\s+(\w+)', line)
                function_name = match.group(1) if match else 'unknown'
            else:
                in_depends_function = False
                function_name = None

        # Check if this line starts a new function/class (indent level 0 or decorator)
        if line and not line[0].isspace() and ('def ' in line or 'class ' in line or '@' in line):
            # Reset tracking when entering new top-level definition
            if '@app.' not in line:  # Unless it's an endpoint decorator
                in_depends_function = False

        # If we're in a Depends function, check for finally: db.close() pattern
        if in_depends_function and line.strip() == 'finally:':
            # Check if next line is db.close()
            if i + 1 < len(lines) and lines[i + 1].strip() == 'db.close()':
                # Found the pattern! Skip both lines
                changes.append(f"  Line {i+1}: Removed 'finally: db.close()' from {function_name}()")
                i += 2  # Skip both the 'finally:' and 'db.close()' lines
                continue

        # Keep this line
        new_lines.append(line)
        i += 1

    # Reconstruct content
    new_content = '\n'.join(new_lines)

    if new_content != original_content:
        main_py.write_text(new_content)
        print(f"\n✅ Made {len(changes)} changes:\n")
        for change in changes:
            print(change)
        print(f"\n💾 Backup saved to: {backup_path}")
        print(f"✨ Fixed file: {main_py}")
        return True
    else:
        print("ℹ️  No changes needed - all endpoints look good!")
        backup_path.unlink()  # Remove unnecessary backup
        return False


def verify_fix():
    """Verify that the fix worked correctly."""
    main_py = Path('app/main.py')
    content = main_py.read_text()

    # Count remaining problematic patterns
    lines = content.split('\n')
    depends_functions = 0
    problematic_closes = []

    in_depends_func = False
    func_name = None

    for i, line in enumerate(lines, 1):
        if 'def ' in line:
            lookahead = '\n'.join(lines[i-1:min(i+10, len(lines))])
            if 'db: Session = Depends(' in lookahead:
                depends_functions += 1
                in_depends_func = True
                match = re.search(r'def\s+(\w+)', line)
                func_name = match.group(1) if match else 'unknown'
            else:
                in_depends_func = False

        if in_depends_func and line.strip() == 'finally:':
            if i < len(lines) and lines[i].strip() == 'db.close()':
                problematic_closes.append((i, func_name))

    print(f"\n📊 Verification Results:")
    print(f"   Functions with Depends(get_db): {depends_functions}")
    print(f"   Remaining db.close() in finally: {len(problematic_closes)}")

    if problematic_closes:
        print(f"\n⚠️  Still found {len(problematic_closes)} problematic close() calls:")
        for line_num, fname in problematic_closes:
            print(f"     Line {line_num}: {fname}()")
        return False
    else:
        print(f"   ✅ All good! No problematic db.close() found.")
        return True


if __name__ == '__main__':
    print("🔧 Database Session Cleanup Tool")
    print("=" * 50)
    print("\nThis will remove unnecessary db.close() calls from")
    print("FastAPI endpoints that use Depends(database.get_db)\n")

    try:
        if fix_db_close():
            print("\n" + "=" * 50)
            verify_fix()
            print("\n✅ Done! Review the changes and run tests.")
            sys.exit(0)
        else:
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
