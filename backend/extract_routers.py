#!/usr/bin/env python3
"""
Extract routers from main.py

This script automatically breaks up the monolithic main.py into separate router modules.
It preserves all imports, dependencies, and docstrings.
"""

import re
import os
import sys
from pathlib import Path
from datetime import datetime

# Router configuration
ROUTERS = {
    'health': {
        'patterns': [r'/health', r'/healthz'],
        'description': 'Health check endpoints'
    },
    'game_flow': {
        'patterns': [r'/games', r'/game[^s]', r'/wgp'],
        'description': 'Game creation, gameplay, and scoring'
    },
    'simulation': {
        'patterns': [r'/simulation', r'/personalities', r'/suggested_opponents'],
        'description': 'Simulation mode endpoints'
    },
    'players': {
        'patterns': [r'/players'],
        'description': 'Player profile management'
    },
    'analytics': {
        'patterns': [r'/analytics', r'/leaderboard'],
        'description': 'Analytics and leaderboards'
    },
    'sheet_integration': {
        'patterns': [r'/sheet-integration'],
        'description': 'Google Sheets integration'
    },
    'courses': {
        'patterns': [r'/courses'],
        'description': 'Course management'
    },
    'ghin': {
        'patterns': [r'/ghin'],
        'description': 'GHIN handicap integration'
    },
    'admin': {
        'patterns': [r'/admin', r'/banner'],
        'description': 'Admin and configuration'
    },
    'scheduling': {
        'patterns': [r'/signup', r'/availability', r'/match'],
        'description': 'Daily signups and matchmaking'
    },
}

def extract_endpoint_function(content, start_line):
    """
    Extract a complete endpoint function starting from a decorator line.
    Returns (function_text, end_line)
    """
    lines = content.split('\n')

    # Find function definition
    func_start = start_line
    while func_start < len(lines) and not lines[func_start].strip().startswith('def '):
        func_start += 1

    if func_start >= len(lines):
        return None, start_line

    # Get function indentation
    func_line = lines[func_start]
    base_indent = len(func_line) - len(func_line.lstrip())

    # Find function end (next function or class at same/lower indent)
    func_end = func_start + 1
    while func_end < len(lines):
        line = lines[func_end]
        if line.strip():
            current_indent = len(line) - len(line.lstrip())
            # Check if we've hit another top-level definition
            if current_indent <= base_indent and (line.strip().startswith('@') or
                                                   line.strip().startswith('def ') or
                                                   line.strip().startswith('class ')):
                break
        func_end += 1

    # Include decorators before function
    decorator_start = start_line
    while decorator_start > 0 and (lines[decorator_start - 1].strip().startswith('@') or
                                    lines[decorator_start - 1].strip() == ''):
        decorator_start -= 1
        if lines[decorator_start].strip().startswith('@'):
            break

    function_text = '\n'.join(lines[decorator_start:func_end])
    return function_text, func_end


def categorize_endpoint(path):
    """Determine which router an endpoint belongs to."""
    for router_name, config in ROUTERS.items():
        for pattern in config['patterns']:
            if re.search(pattern, path):
                return router_name
    return 'misc'


def extract_routers_from_main():
    """Main extraction logic."""
    main_py = Path('app/main.py')

    if not main_py.exists():
        print("❌ app/main.py not found")
        return False

    # Create backup
    backup_path = main_py.with_suffix(f'.py.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    print(f"📝 Creating backup: {backup_path}")
    backup_path.write_text(main_py.read_text())

    content = main_py.read_text()
    lines = content.split('\n')

    # Extract endpoints by category
    router_endpoints = {name: [] for name in ROUTERS.keys()}
    router_endpoints['misc'] = []

    # Find all endpoint decorators
    for i, line in enumerate(lines):
        match = re.match(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', line.strip())
        if match:
            method, path = match.groups()
            category = categorize_endpoint(path)

            # Extract the complete function
            func_text, end_line = extract_endpoint_function(content, i)
            if func_text:
                router_endpoints[category].append({
                    'path': path,
                    'method': method,
                    'code': func_text,
                    'line': i + 1
                })

    # Report
    print(f"\n📊 Endpoint Distribution:")
    for category, endpoints in sorted(router_endpoints.items()):
        if endpoints:
            print(f"  {category}: {len(endpoints)} endpoints")

    return router_endpoints, content


def create_router_file(router_name, config, endpoints):
    """Create a router module file."""
    router_file = Path(f'app/routers/{router_name}.py')

    # Generate imports
    imports = """from fastapi import APIRouter, Depends, HTTPException, Query, Header, Body, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from ..database import get_db
from .. import models, schemas
from ..services import *

"""

    # Create router instance
    router_code = f'''logger = logging.getLogger(f"app.routers.{router_name}")

router = APIRouter(
    prefix="",
    tags=["{router_name}"]
)

'''

    # Add endpoints (replace @app. with @router.)
    endpoint_code = ""
    for endpoint in endpoints:
        # Replace @app. with @router.
        code = endpoint['code'].replace('@app.', '@router.')
        endpoint_code += code + "\n\n"

    full_code = imports + router_code + endpoint_code

    router_file.write_text(full_code)
    print(f"  ✅ Created {router_file} ({len(endpoints)} endpoints)")

    return str(router_file)


def create_minimal_main(original_content):
    """Create a minimal main.py that just registers routers."""

    lines = original_content.split('\n')

    # Find where FastAPI app is created
    app_creation_line = None
    for i, line in enumerate(lines):
        if 'FastAPI(' in line and 'app =' in line:
            app_creation_line = i
            break

    if app_creation_line is None:
        print("❌ Could not find FastAPI app creation")
        return None

    # Extract everything before first endpoint
    first_endpoint_line = None
    for i, line in enumerate(lines):
        if re.match(r'@app\.(get|post|put|delete|patch)', line.strip()):
            first_endpoint_line = i
            break

    # Keep: imports, app creation, startup/shutdown, exception handlers
    keep_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Keep everything before first endpoint
        if first_endpoint_line and i < first_endpoint_line:
            keep_lines.append(line)
        # Keep event handlers
        elif '@app.on_event' in line or '@app.exception_handler' in line:
            # Include this decorator and its function
            keep_lines.append(line)
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('@'):
                keep_lines.append(lines[i])
                i += 1
            continue

        i += 1

    # Add router imports and registration
    router_registration = '''
# Import routers
from app.routers import (
    health,
    game_flow,
    simulation,
    players,
    analytics,
    sheet_integration,
    courses,
    ghin,
    admin,
    scheduling,
)

# Register routers
app.include_router(health.router)
app.include_router(game_flow.router)
app.include_router(simulation.router)
app.include_router(players.router)
app.include_router(analytics.router)
app.include_router(sheet_integration.router)
app.include_router(courses.router)
app.include_router(ghin.router)
app.include_router(admin.router)
app.include_router(scheduling.router)

logger.info("✅ All routers registered")
'''

    new_main = '\n'.join(keep_lines) + '\n' + router_registration

    return new_main


if __name__ == '__main__':
    print("🔧 Router Extraction Tool")
    print("=" * 50)

    try:
        # Extract endpoints
        router_endpoints, original_content = extract_routers_from_main()

        # Create router files
        print(f"\n📁 Creating router files...")
        created_files = []
        for router_name, config in ROUTERS.items():
            endpoints = router_endpoints.get(router_name, [])
            if endpoints:
                file_path = create_router_file(router_name, config, endpoints)
                created_files.append(file_path)

        # Handle misc endpoints
        if router_endpoints.get('misc'):
            print(f"\n⚠️  Found {len(router_endpoints['misc'])} uncategorized endpoints:")
            for ep in router_endpoints['misc'][:5]:
                print(f"    {ep['method'].upper()} {ep['path']}")

        # Create router __init__.py
        init_file = Path('app/routers/__init__.py')
        router_names = [name for name in ROUTERS.keys() if router_endpoints.get(name)]
        init_content = f"""\"\"\"
Routers module - organized API endpoints.

Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
\"\"\"

from . import {', '.join(router_names)}

__all__ = [{', '.join(repr(name) for name in router_names)}]
"""
        init_file.write_text(init_content)
        print(f"  ✅ Created {init_file}")

        print(f"\n✅ Router extraction complete!")
        print(f"   Created {len(created_files)} router files")
        print(f"\n⚠️  Next step: Review the generated files and update main.py")
        print(f"   To apply: Run the generated routers and test thoroughly")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    sys.exit(0)
