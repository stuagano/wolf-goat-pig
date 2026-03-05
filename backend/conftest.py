"""Root conftest for backend — delegates to tests/conftest.py.

When pytest is invoked from the backend/ directory, this file ensures the
backend directory is on sys.path so that ``from app import ...`` works.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
