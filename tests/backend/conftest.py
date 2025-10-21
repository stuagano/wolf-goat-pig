"""Backend test configuration.

Ensures the backend package is importable from the repository root and keeps
test-only endpoints disabled by default so unit suites reflect production
behavior.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
BACKEND_STR = str(BACKEND_ROOT)

if BACKEND_STR not in sys.path:
    sys.path.insert(0, BACKEND_STR)

# Harden default environment for backend tests.
os.environ.setdefault("ENABLE_TEST_ENDPOINTS", "false")
