"""
Database migrations management endpoint.

This provides a secure endpoint for running database migrations in production.
Useful for manual schema changes during development and deployment.
"""

import logging
import os
from typing import Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import inspect, text
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/migrations", tags=["migrations"])
logger = logging.getLogger(__name__)


def verify_admin_key(x_admin_key: str = Header(...)) -> bool:
    """Verify the admin key for migrations endpoint access.

    In production, set the ADMIN_KEY environment variable.
    In development, uses a default key (INSECURE - for dev only).
    """
    expected_key = os.getenv("ADMIN_KEY", "dev-admin-key-INSECURE")

    if x_admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid admin key. Set X-Admin-Key header.")
    return True


@router.get("/status")
async def get_migration_status(db: Session = Depends(get_db), _: bool = Depends(verify_admin_key)) -> Dict[str, Any]:
    """Get current database schema status.

    Returns information about existing tables and columns to help
    determine which migrations need to be applied.

    Headers:
        X-Admin-Key: Admin key for authentication
    """
    try:
        inspector = cast(Inspector, inspect(db.bind))

        # Get all tables
        tables = inspector.get_table_names()

        # Get detailed info for critical tables
        table_info = {}

        for table_name in ["game_state", "game_players", "game_records"]:
            if table_name in tables:
                columns = inspector.get_columns(table_name)
                indexes = inspector.get_indexes(table_name)

                # Serialize column details to make them JSON-compatible
                serialized_columns = []
                for col in columns:
                    serialized_col = {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "default": str(col.get("default")) if col.get("default") is not None else None,
                    }
                    serialized_columns.append(serialized_col)

                table_info[table_name] = {
                    "columns": [col["name"] for col in columns],
                    "column_details": serialized_columns,
                    "indexes": [idx["name"] for idx in indexes],
                }

        return {"success": True, "all_tables": tables, "critical_tables": table_info}

    except Exception as e:
        logger.error(f"Error getting migration status: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/run")
async def run_migration(
    migration_name: str, db: Session = Depends(get_db), _: bool = Depends(verify_admin_key)
) -> Dict[str, Any]:
    """Run a specific migration by name.

    Available migrations:
    - add_tee_order: Adds tee_order column to game_players table
    - add_game_id: Adds game_id column to game_state table
    - add_timestamps: Adds created_at/updated_at columns

    Headers:
        X-Admin-Key: Admin key for authentication

    Query Parameters:
        migration_name: Name of the migration to run
    """
    migrations = {
        "add_tee_order": _add_tee_order_migration,
        "add_game_id": _add_game_id_migration,
        "add_timestamps": _add_timestamps_migration,
        "add_join_code": _add_join_code_migration,
        "add_creator_user_id": _add_creator_user_id_migration,
        "add_game_status": _add_game_status_migration,
        "add_legacy_name": _add_legacy_name_migration,
    }

    if migration_name not in migrations:
        raise HTTPException(
            status_code=400, detail=f"Unknown migration: {migration_name}. Available: {list(migrations.keys())}"
        )

    try:
        result = migrations[migration_name](db)
        db.commit()

        logger.info(f"Migration {migration_name} completed successfully")

        return {
            "success": True,
            "migration": migration_name,
            "message": result.get("message", "Migration completed"),
            "changes": result.get("changes", []),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error running migration {migration_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.post("/run-all")
async def run_all_migrations(db: Session = Depends(get_db), _: bool = Depends(verify_admin_key)) -> Dict[str, Any]:
    """Run all migrations that haven't been applied yet.

    This is equivalent to the startup.py run_migrations() function but
    can be triggered manually via HTTP.

    Headers:
        X-Admin-Key: Admin key for authentication
    """
    try:
        from startup import run_migrations

        result = await run_migrations()

        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "migrations_applied": result.get("migrations_applied", []),
        }

    except Exception as e:
        logger.error(f"Error running all migrations: {e}")
        raise HTTPException(status_code=500, detail=f"Error running migrations: {str(e)}")


# Individual migration functions


def _add_tee_order_migration(db: Session) -> Dict[str, Any]:
    """Add tee_order column to game_players table."""
    inspector = cast(Inspector, inspect(db.bind))

    # Check if game_players table exists
    if "game_players" not in inspector.get_table_names():
        return {"message": "game_players table does not exist", "changes": []}

    # Check if tee_order column already exists
    columns = [col["name"] for col in inspector.get_columns("game_players")]

    changes = []

    if "tee_order" not in columns:
        # Add tee_order column
        if db.bind and "postgresql" in str(db.bind.dialect):
            db.execute(text("ALTER TABLE game_players ADD COLUMN tee_order INTEGER"))
        else:
            db.execute(text("ALTER TABLE game_players ADD COLUMN tee_order INTEGER"))

        changes.append("Added tee_order column to game_players")

        # Add index
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_game_players_tee_order ON game_players(game_id, tee_order)"))
        changes.append("Created index idx_game_players_tee_order")
    else:
        changes.append("tee_order column already exists")

    return {"message": "tee_order migration completed", "changes": changes}


def _add_game_id_migration(db: Session) -> Dict[str, Any]:
    """Add game_id column to game_state table."""
    inspector = cast(Inspector, inspect(db.bind))

    if "game_state" not in inspector.get_table_names():
        return {"message": "game_state table does not exist", "changes": []}

    columns = [col["name"] for col in inspector.get_columns("game_state")]
    changes = []

    if "game_id" not in columns:
        db.execute(text("ALTER TABLE game_state ADD COLUMN game_id VARCHAR"))
        db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id)"))
        changes.append("Added game_id column and index to game_state")
    else:
        changes.append("game_id column already exists")

    return {"message": "game_id migration completed", "changes": changes}


def _add_timestamps_migration(db: Session) -> Dict[str, Any]:
    """Add created_at and updated_at columns to game_state table."""
    inspector = cast(Inspector, inspect(db.bind))

    if "game_state" not in inspector.get_table_names():
        return {"message": "game_state table does not exist", "changes": []}

    columns = [col["name"] for col in inspector.get_columns("game_state")]
    changes = []

    if "created_at" not in columns:
        if db.bind and "postgresql" in str(db.bind.dialect):
            db.execute(text("ALTER TABLE game_state ADD COLUMN created_at TIMESTAMP"))
        else:
            db.execute(text("ALTER TABLE game_state ADD COLUMN created_at VARCHAR"))
        changes.append("Added created_at column to game_state")

    if "updated_at" not in columns:
        if db.bind and "postgresql" in str(db.bind.dialect):
            db.execute(text("ALTER TABLE game_state ADD COLUMN updated_at TIMESTAMP"))
        else:
            db.execute(text("ALTER TABLE game_state ADD COLUMN updated_at VARCHAR"))
        changes.append("Added updated_at column to game_state")

    if not changes:
        changes.append("Timestamp columns already exist")

    return {"message": "Timestamps migration completed", "changes": changes}


def _add_join_code_migration(db: Session) -> Dict[str, Any]:
    """Add join_code column to game_state table."""
    inspector = cast(Inspector, inspect(db.bind))

    if "game_state" not in inspector.get_table_names():
        return {"message": "game_state table does not exist", "changes": []}

    columns = [col["name"] for col in inspector.get_columns("game_state")]
    changes = []

    if "join_code" not in columns:
        db.execute(text("ALTER TABLE game_state ADD COLUMN join_code VARCHAR"))
        db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_join_code ON game_state(join_code)"))
        changes.append("Added join_code column and index to game_state")
    else:
        changes.append("join_code column already exists")

    return {"message": "join_code migration completed", "changes": changes}


def _add_creator_user_id_migration(db: Session) -> Dict[str, Any]:
    """Add creator_user_id column to game_state table."""
    inspector = cast(Inspector, inspect(db.bind))

    if "game_state" not in inspector.get_table_names():
        return {"message": "game_state table does not exist", "changes": []}

    columns = [col["name"] for col in inspector.get_columns("game_state")]
    changes = []

    if "creator_user_id" not in columns:
        db.execute(text("ALTER TABLE game_state ADD COLUMN creator_user_id VARCHAR"))
        changes.append("Added creator_user_id column to game_state")
    else:
        changes.append("creator_user_id column already exists")

    return {"message": "creator_user_id migration completed", "changes": changes}


def _add_game_status_migration(db: Session) -> Dict[str, Any]:
    """Add game_status column to game_state table."""
    inspector = cast(Inspector, inspect(db.bind))

    if "game_state" not in inspector.get_table_names():
        return {"message": "game_state table does not exist", "changes": []}

    columns = [col["name"] for col in inspector.get_columns("game_state")]
    changes = []

    if "game_status" not in columns:
        db.execute(text("ALTER TABLE game_state ADD COLUMN game_status VARCHAR DEFAULT 'setup'"))
        changes.append("Added game_status column to game_state")
    else:
        changes.append("game_status column already exists")

    return {"message": "game_status migration completed", "changes": changes}


def _add_legacy_name_migration(db: Session) -> Dict[str, Any]:
    """Add legacy_name column to player_profiles table.

    This column stores the player's name in the legacy tee sheet system.
    """
    inspector = cast(Inspector, inspect(db.bind))

    if "player_profiles" not in inspector.get_table_names():
        return {"message": "player_profiles table does not exist", "changes": []}

    columns = [col["name"] for col in inspector.get_columns("player_profiles")]
    changes = []

    if "legacy_name" not in columns:
        db.execute(text("ALTER TABLE player_profiles ADD COLUMN legacy_name VARCHAR"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_player_profiles_legacy_name ON player_profiles(legacy_name)"))
        changes.append("Added legacy_name column to player_profiles")
        changes.append("Created index ix_player_profiles_legacy_name")
    else:
        changes.append("legacy_name column already exists")

    return {"message": "legacy_name migration completed", "changes": changes}
