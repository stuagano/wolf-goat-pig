#!/usr/bin/env python3
"""
Consolidated installer for Wolf Goat Pig application
Wrapper for the real installer in scripts/development/
"""

import sys
import os
from pathlib import Path

# Add scripts/development to path and run the real installer
scripts_dir = Path(__file__).parent / "scripts" / "development"
sys.path.insert(0, str(scripts_dir))

try:
    from install import main
    sys.exit(main())
except ImportError as e:
    print(f"❌ Error importing installer: {e}")
    print("💡 Make sure scripts/development/install.py exists")
    sys.exit(1)