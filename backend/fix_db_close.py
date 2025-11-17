#!/usr/bin/env python3
"""
Fix db.close() issues in main.py

Strategy:
1. Find all endpoints with db: Session = Depends(database.get_db)
2. Remove the finally: db.close() blocks from those endpoints
3. Keep finally blocks for manual SessionLocal() creations
"""

import re
import sys

def fix_db_close_in_main():
    """Remove unnecessary db.close() calls from FastAPI endpoints."""

    with open('app/main.py', 'r') as f:
        content = f.read()

    original_content = content
    changes_made = []

    # Pattern to find endpoints with Depends(database.get_db) followed by finally: db.close()
    # This is a complex pattern, so we'll do it line by line

    lines = content.split('\n')
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is a function with Depends
        if 'def ' in line:
            # Look ahead to see if it has db: Session = Depends
            func_block_end = min(i + 20, len(lines))
            func_block = '\n'.join(lines[i:func_block_end])

            has_depends = ('db: Session = Depends(database.get_db)' in func_block or
                          'db: Session = Depends(get_db)' in func_block)

            if has_depends:
                # This function uses Depends, look for finally: db.close()
                # Find the end of this function (next function or end of file)
                func_end = i + 1
                indent_level = len(line) - len(line.lstrip())

                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    if next_line.strip() and not next_line.strip().startswith('#'):
                        next_indent = len(next_line) - len(next_line.lstrip())
                        if next_indent <= indent_level and ('def ' in next_line or '@app.' in next_line):
                            func_end = j
                            break
                else:
                    func_end = len(lines)

                # Process this function
                func_name = re.search(r'def\s+(\w+)', line)
                func_name_str = func_name.group(1) if func_name else 'unknown'

                # Look for finally: db.close() pattern
                j = i
                while j < func_end:
                    current_line = lines[j]

                    # Check for the problematic pattern
                    if j + 1 < func_end:
                        # Pattern 1: finally:\n        db.close()
                        if current_line.strip() == 'finally:' and j + 1 < len(lines):
                            next_line = lines[j + 1].strip()
                            if next_line == 'db.close()':
                                # Found it! Remove both lines
                                changes_made.append(f"Removed db.close() from {func_name_str} (line {j+1})")
                                # Skip these two lines
                                j += 2
                                continue

                        # Pattern 2: finally: db.close() (single line)
                        if 'finally:' in current_line and 'db.close()' in current_line:
                            changes_made.append(f"Removed db.close() from {func_name_str} (line {j+1})")
                            j += 1
                            continue

                    new_lines.append(lines[j])
                    j += 1

                i = func_end
                continue

        new_lines.append(line)
        i += 1

    new_content = '\n'.join(new_lines)

    if new_content != original_content:
        # Write the fixed content
        with open('app/main.py', 'w') as f:
            f.write(new_content)

        print(f"✅ Made {len(changes_made)} changes:")
        for change in changes_made:
            print(f"  - {change}")

        return True
    else:
        print("ℹ️  No changes needed")
        return False

if __name__ == '__main__':
    try:
        if fix_db_close_in_main():
            print("\n✅ Successfully fixed db.close() issues")
            sys.exit(0)
        else:
            print("\nℹ️  No changes were necessary")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
