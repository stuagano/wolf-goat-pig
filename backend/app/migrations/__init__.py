"""
Database migrations for Wolf-Goat-Pig application.

This package contains migration scripts for database schema changes.
"""

from .add_holes_from_json import migrate_holes_from_json

__all__ = ["migrate_holes_from_json"]
