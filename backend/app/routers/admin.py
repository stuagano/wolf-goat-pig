"""
Admin Router

Admin endpoints for email configuration, banner management, database inspection,
cleanup utilities, and deployment testing.

Mechanical refactor from main.py — preserves exact signatures, error handling,
and response formats.
"""

import json
import logging
import os
from datetime import UTC, datetime, timedelta
from ..utils.time import utc_now
from typing import Any

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import database, models, schemas
from ..services.email_service import get_email_service
from ..state.app_state import set_email_service_instance
from ..utils.admin_auth import require_admin

logger = logging.getLogger("app.routers.admin")

router = APIRouter(tags=["admin"])


# =============================================================================
# EMAIL CONFIGURATION ENDPOINTS
# =============================================================================


@router.get("/admin/email-config")
def get_email_config(x_admin_email: str = Header(None)):  # type: ignore
    """Get current email configuration (admin only)"""
    require_admin(x_admin_email)

    # Return current config (without password)
    return {
        "config": {
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": os.getenv("SMTP_PORT", "587"),
            "smtp_username": os.getenv("SMTP_USER", ""),
            "from_email": os.getenv("FROM_EMAIL", ""),
            "from_name": os.getenv("FROM_NAME", "Wolf Goat Pig Admin"),
            # Don't return password
            "smtp_password": "••••••••" if os.getenv("SMTP_PASSWORD") else "",
        }
    }


@router.post("/admin/email-config")
def update_email_config(config: dict[str, Any], x_admin_email: str = Header(None)):  # type: ignore
    """Update email configuration (admin only)"""
    require_admin(x_admin_email)

    try:
        # Update environment variables (in memory for this session)
        if config.get("smtp_host"):
            os.environ["SMTP_HOST"] = config["smtp_host"]
        if config.get("smtp_port"):
            os.environ["SMTP_PORT"] = str(config["smtp_port"])
        if config.get("smtp_username"):
            os.environ["SMTP_USER"] = config["smtp_username"]
        if config.get("smtp_password") and not config["smtp_password"].startswith("•"):
            os.environ["SMTP_PASSWORD"] = config["smtp_password"]
        if config.get("from_email"):
            os.environ["FROM_EMAIL"] = config["from_email"]
        if config.get("from_name"):
            os.environ["FROM_NAME"] = config["from_name"]

        # Reinitialize email service with new config
        set_email_service_instance(None)  # Reset to force reinitialization

        return {"status": "success", "message": "Email configuration updated"}
    except Exception as e:
        logger.error(f"Error updating email config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/test-email")
async def test_admin_email(request: dict[str, Any], x_admin_email: str = Header(None)):  # type: ignore
    """Send a test email with provided configuration (admin only)"""
    require_admin(x_admin_email)

    try:
        test_email = request.get("test_email")
        config = request.get("config", {})

        if not test_email:
            raise HTTPException(status_code=400, detail="Test email address required")

        # Temporarily apply config if provided
        if config:
            # Save current values
            old_config = {
                "SMTP_HOST": os.getenv("SMTP_HOST"),
                "SMTP_PORT": os.getenv("SMTP_PORT"),
                "SMTP_USER": os.getenv("SMTP_USER"),
                "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
                "FROM_EMAIL": os.getenv("FROM_EMAIL"),
                "FROM_NAME": os.getenv("FROM_NAME"),
            }

            # Apply test config
            if config.get("smtp_host"):
                os.environ["SMTP_HOST"] = config["smtp_host"]
            if config.get("smtp_port"):
                os.environ["SMTP_PORT"] = str(config["smtp_port"])
            if config.get("smtp_username"):
                os.environ["SMTP_USER"] = config["smtp_username"]
            if config.get("smtp_password") and not config["smtp_password"].startswith("•"):
                os.environ["SMTP_PASSWORD"] = config["smtp_password"]
            if config.get("from_email"):
                os.environ["FROM_EMAIL"] = config["from_email"]
            if config.get("from_name"):
                os.environ["FROM_NAME"] = config["from_name"]

        # Create new email service with test config
        from ..services.email_service import EmailService

        test_service = EmailService()

        if not test_service.is_configured:  # type: ignore
            raise HTTPException(
                status_code=400,
                detail="Email service not configured. Please provide SMTP settings.",
            )

        # Send test email
        success = test_service.send_test_email(to_email=test_email, admin_name=x_admin_email)

        # Restore original config if we changed it
        if config and "old_config" in locals():
            for key, value in old_config.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

        if success:
            return {"status": "success", "message": f"Test email sent to {test_email}"}
        raise HTTPException(status_code=500, detail="Failed to send test email")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CREDENTIALS UPLOAD
# =============================================================================


@router.post("/admin/upload-credentials")
async def upload_gmail_credentials(file: UploadFile = File(...), x_admin_email: str = Header(None)):  # type: ignore
    """Upload Gmail API credentials file (admin only)"""
    require_admin(x_admin_email)

    try:
        # Validate file type
        if not file.filename or not file.filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="File must be a JSON file")

        # Read and validate JSON content
        content = await file.read()
        credentials_data = json.loads(content)

        # Validate it's a Google OAuth2 credentials file
        if "installed" not in credentials_data and "web" not in credentials_data:
            raise HTTPException(
                status_code=400,
                detail="Invalid credentials file format. Please ensure it's a Google OAuth2 credentials file.",
            )

        # Save credentials file
        oauth2_service = get_email_service()
        with open(oauth2_service.credentials_path, "w") as f:  # type: ignore
            json.dump(credentials_data, f)

        return {
            "status": "success",
            "message": "Gmail credentials file uploaded successfully",
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# BANNER MANAGEMENT ROUTES
# =============================================================================


@router.get("/banner")
async def get_active_banner(db: Session = Depends(database.get_db)):  # type: ignore
    """Get the currently active banner for display on game pages (public route)"""
    try:
        banner = (
            db.query(models.GameBanner)
            .filter(models.GameBanner.is_active == True)
            .order_by(models.GameBanner.id.desc())
            .first()
        )

        if not banner:
            return {"banner": None}

        return {
            "banner": {
                "id": banner.id,
                "title": banner.title,
                "message": banner.message,
                "banner_type": banner.banner_type,
                "background_color": banner.background_color,
                "text_color": banner.text_color,
                "show_icon": banner.show_icon,
                "dismissible": banner.dismissible,
            }
        }
    except Exception as e:
        logger.error(f"Error fetching active banner: {e}")
        return {"banner": None}


@router.get("/admin/banner")
async def get_banner_config(x_admin_email: str = Header(None), db: Session = Depends(database.get_db)):  # type: ignore
    """Get current banner configuration (admin only)"""
    require_admin(x_admin_email)

    try:
        banner = db.query(models.GameBanner).order_by(models.GameBanner.id.desc()).first()

        if not banner:
            return {"banner": None}

        return {
            "banner": {
                "id": banner.id,
                "title": banner.title,
                "message": banner.message,
                "banner_type": banner.banner_type,
                "is_active": banner.is_active,
                "background_color": banner.background_color,
                "text_color": banner.text_color,
                "show_icon": banner.show_icon,
                "dismissible": banner.dismissible,
                "created_at": banner.created_at,
                "updated_at": banner.updated_at,
            }
        }
    except Exception as e:
        logger.error(f"Error fetching banner config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/banner")
async def create_or_update_banner(  # type: ignore
    banner_data: schemas.GameBannerCreate,
    x_admin_email: str = Header(None),
    db: Session = Depends(database.get_db),
):
    """Create or update the game banner (admin only)"""
    require_admin(x_admin_email)

    try:
        # Deactivate all existing banners if creating a new active one
        if banner_data.is_active:
            db.query(models.GameBanner).update({"is_active": False})

        # Create new banner
        new_banner = models.GameBanner(
            title=banner_data.title,
            message=banner_data.message,
            banner_type=banner_data.banner_type,
            is_active=banner_data.is_active,
            background_color=banner_data.background_color,
            text_color=banner_data.text_color,
            show_icon=banner_data.show_icon,
            dismissible=banner_data.dismissible,
            created_at=utc_now().isoformat(),
            updated_at=utc_now().isoformat(),
        )

        db.add(new_banner)
        db.commit()
        db.refresh(new_banner)

        return {
            "status": "success",
            "message": "Banner created successfully",
            "banner": {
                "id": new_banner.id,
                "title": new_banner.title,
                "message": new_banner.message,
                "banner_type": new_banner.banner_type,
                "is_active": new_banner.is_active,
                "background_color": new_banner.background_color,
                "text_color": new_banner.text_color,
                "show_icon": new_banner.show_icon,
                "dismissible": new_banner.dismissible,
                "created_at": new_banner.created_at,
                "updated_at": new_banner.updated_at,
            },
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating banner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/banner/{banner_id}")
async def update_banner(  # type: ignore
    banner_id: int,
    banner_data: schemas.GameBannerUpdate,
    x_admin_email: str = Header(None),
    db: Session = Depends(database.get_db),
):
    """Update an existing banner (admin only)"""
    require_admin(x_admin_email)

    try:
        banner = db.query(models.GameBanner).filter(models.GameBanner.id == banner_id).first()

        if not banner:
            raise HTTPException(status_code=404, detail="Banner not found")

        # If activating this banner, deactivate all others
        if banner_data.is_active and banner_data.is_active != banner.is_active:
            db.query(models.GameBanner).filter(models.GameBanner.id != banner_id).update({"is_active": False})

        # Update banner fields
        update_data = banner_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(banner, field, value)

        banner.updated_at = utc_now().isoformat()

        db.commit()
        db.refresh(banner)

        return {
            "status": "success",
            "message": "Banner updated successfully",
            "banner": {
                "id": banner.id,
                "title": banner.title,
                "message": banner.message,
                "banner_type": banner.banner_type,
                "is_active": banner.is_active,
                "background_color": banner.background_color,
                "text_color": banner.text_color,
                "show_icon": banner.show_icon,
                "dismissible": banner.dismissible,
                "created_at": banner.created_at,
                "updated_at": banner.updated_at,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating banner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/banner/{banner_id}")
async def delete_banner(  # type: ignore
    banner_id: int,
    x_admin_email: str = Header(None),
    db: Session = Depends(database.get_db),
):
    """Delete a banner (admin only)"""
    require_admin(x_admin_email)

    try:
        banner = db.query(models.GameBanner).filter(models.GameBanner.id == banner_id).first()

        if not banner:
            raise HTTPException(status_code=404, detail="Banner not found")

        db.delete(banner)
        db.commit()

        return {"status": "success", "message": "Banner deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting banner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MATCH ADMIN
# =============================================================================


@router.delete("/admin/matches")
def admin_delete_all_matches(x_admin_email: str = Header(None)):  # type: ignore
    """Delete all match records (admin only, for testing)."""
    require_admin(x_admin_email)
    db = database.SessionLocal()
    try:
        deleted_players = db.query(models.MatchPlayer).delete()
        deleted_matches = db.query(models.MatchSuggestion).delete()
        db.commit()
        return {"deleted_matches": deleted_matches, "deleted_players": deleted_players}
    finally:
        db.close()


# =============================================================================
# DATABASE ADMIN ENDPOINTS
# =============================================================================


@router.get("/admin/db/schemas")
async def get_db_schemas(x_admin_email: str | None = Header(None), db: Session = Depends(database.get_db)):  # type: ignore
    """Get all database schemas."""
    require_admin(x_admin_email)
    try:
        query = text("SELECT schema_name FROM information_schema.schemata;")
        result = db.execute(query).fetchall()
        schemas_list = [row[0] for row in result]
        return {"schemas": schemas_list}
    except Exception as e:
        logger.error(f"Error getting db schemas: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get db schemas: {e!s}")


@router.get("/admin/db/schemas/{schema_name}/tables")
async def get_db_tables(
    schema_name: str,
    x_admin_email: str | None = Header(None),
    db: Session = Depends(database.get_db),
):  # type: ignore
    """Get all tables within a specific schema."""
    require_admin(x_admin_email)
    try:
        query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = :schema_name;")
        result = db.execute(query, {"schema_name": schema_name}).fetchall()
        tables = [row[0] for row in result]
        return {"schema": schema_name, "tables": tables}
    except Exception as e:
        logger.error(f"Error getting db tables for schema {schema_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get db tables: {e!s}")


@router.get("/admin/db/schemas/{schema_name}/tables/{table_name}")
async def get_table_content(
    schema_name: str,
    table_name: str,
    x_admin_email: str | None = Header(None),
    db: Session = Depends(database.get_db),
):  # type: ignore
    """Get the content of a specific table."""
    require_admin(x_admin_email)
    try:
        # Security check: verify table exists in the schema
        check_query = text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = :schema_name AND table_name = :table_name;"
        )
        result = db.execute(check_query, {"schema_name": schema_name, "table_name": table_name}).fetchone()
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table_name}' not found in schema '{schema_name}'",
            )

        query = text(f"SELECT * FROM \"{schema_name}\".\"{table_name}\" LIMIT 100;")
        table_content = db.execute(query).fetchall()
        columns = table_content[0].keys() if table_content else []
        rows = [dict(row._mapping) for row in table_content]
        return {
            "schema": schema_name,
            "table": table_name,
            "columns": list(columns),
            "rows": rows,
        }
    except Exception as e:
        logger.error(f"Error getting content for table {schema_name}.{table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get table content: {e!s}")


@router.get("/test-deployment")
async def test_deployment(x_admin_email: str | None = Header(None)):  # type: ignore
    """Test that new deployments are working."""
    require_admin(x_admin_email)
    return {"message": "Deployment is working", "timestamp": utc_now().isoformat()}


# =============================================================================
# DATABASE CLEANUP ENDPOINTS
# =============================================================================


@router.get("/admin/cleanup/orphaned-games")
async def get_orphaned_games(
    x_admin_email: str | None = Header(None),
    hours_old: int = Query(24, description="Only show games older than this many hours"),
    db: Session = Depends(database.get_db),
):  # type: ignore
    """Get a list of orphaned games (setup status, 0 players, older than specified hours)."""
    require_admin(x_admin_email)
    try:
        cutoff_time = utc_now() - timedelta(hours=hours_old)

        # Query for orphaned games
        orphaned = (
            db.query(models.GameStateModel)
            .filter(
                models.GameStateModel.game_status == "setup",
                models.GameStateModel.created_at < cutoff_time.isoformat(),
            )
            .all()
        )

        # Filter to those with 0 players (check game_players table)
        orphaned_games = []
        for game in orphaned:
            player_count = db.query(models.GamePlayer).filter(models.GamePlayer.game_id == game.game_id).count()
            if player_count == 0:
                orphaned_games.append(
                    {
                        "game_id": game.game_id,
                        "join_code": game.join_code,
                        "created_at": game.created_at,
                        "updated_at": game.updated_at,
                        "player_count": player_count,
                    }
                )

        return {
            "orphaned_count": len(orphaned_games),
            "hours_old_threshold": hours_old,
            "cutoff_time": cutoff_time.isoformat(),
            "orphaned_games": orphaned_games[:100],  # Limit response size
        }
    except Exception as e:
        logger.error(f"Error getting orphaned games: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get orphaned games: {e!s}")


@router.delete("/admin/cleanup/orphaned-games")
async def delete_orphaned_games(
    x_admin_email: str | None = Header(None),
    hours_old: int = Query(24, description="Only delete games older than this many hours"),
    dry_run: bool = Query(True, description="If true, only show what would be deleted"),
    db: Session = Depends(database.get_db),
):  # type: ignore
    """Delete orphaned games (setup status, 0 players, older than specified hours).

    Use dry_run=true (default) to preview what will be deleted.
    Set dry_run=false to actually delete the games.
    """
    require_admin(x_admin_email)
    try:
        cutoff_time = utc_now() - timedelta(hours=hours_old)

        # Find orphaned games
        orphaned = (
            db.query(models.GameStateModel)
            .filter(
                models.GameStateModel.game_status == "setup",
                models.GameStateModel.created_at < cutoff_time.isoformat(),
            )
            .all()
        )

        # Filter to those with 0 players
        games_to_delete = []
        for game in orphaned:
            player_count = db.query(models.GamePlayer).filter(models.GamePlayer.game_id == game.game_id).count()
            if player_count == 0:
                games_to_delete.append(game)

        if dry_run:
            return {
                "dry_run": True,
                "would_delete_count": len(games_to_delete),
                "hours_old_threshold": hours_old,
                "message": f"Would delete {len(games_to_delete)} orphaned games. Set dry_run=false to proceed.",
                "sample_games": [{"game_id": g.game_id, "created_at": g.created_at} for g in games_to_delete[:10]],
            }

        # Actually delete
        deleted_count = 0
        for game in games_to_delete:
            db.delete(game)
            deleted_count += 1

        db.commit()

        logger.info(f"Deleted {deleted_count} orphaned games older than {hours_old} hours")

        return {
            "dry_run": False,
            "deleted_count": deleted_count,
            "hours_old_threshold": hours_old,
            "message": f"Successfully deleted {deleted_count} orphaned games",
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting orphaned games: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete orphaned games: {e!s}")


@router.get("/admin/cleanup/database-stats")
async def get_database_stats(x_admin_email: str | None = Header(None), db: Session = Depends(database.get_db)):  # type: ignore
    """Get database statistics for health monitoring."""
    require_admin(x_admin_email)
    try:
        stats = {}

        # Game stats
        total_games = db.query(models.GameStateModel).count()
        setup_games = db.query(models.GameStateModel).filter(models.GameStateModel.game_status == "setup").count()
        in_progress_games = (
            db.query(models.GameStateModel).filter(models.GameStateModel.game_status == "in_progress").count()
        )
        completed_games = (
            db.query(models.GameStateModel).filter(models.GameStateModel.game_status == "completed").count()
        )

        stats["games"] = {
            "total": total_games,
            "setup": setup_games,
            "in_progress": in_progress_games,
            "completed": completed_games,
        }

        # Player stats
        total_players = db.query(models.PlayerProfile).count()
        players_with_email = (
            db.query(models.PlayerProfile)
            .filter(models.PlayerProfile.email.isnot(None), models.PlayerProfile.email != "")
            .count()
        )
        ai_players = db.query(models.PlayerProfile).filter(models.PlayerProfile.is_ai == True).count()

        stats["players"] = {
            "total": total_players,
            "with_email": players_with_email,
            "without_email": total_players - players_with_email,
            "ai_players": ai_players,
        }

        # Signup stats
        total_signups = db.query(models.DailySignup).count()
        active_signups = db.query(models.DailySignup).filter(models.DailySignup.status == "signed_up").count()

        stats["signups"] = {"total": total_signups, "active": active_signups}

        # Generated pairings
        total_pairings = db.query(models.GeneratedPairing).count()
        stats["pairings"] = {"total": total_pairings}

        # Game records (completed games)
        total_records = db.query(models.GameRecord).count()
        stats["game_records"] = {"total": total_records}

        # Notifications
        total_notifications = db.query(models.Notification).count()
        unread_notifications = db.query(models.Notification).filter(models.Notification.is_read == False).count()
        stats["notifications"] = {
            "total": total_notifications,
            "unread": unread_notifications,
        }

        return {"generated_at": utc_now().isoformat(), "stats": stats}
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get database stats: {e!s}")


@router.post("/admin/run-migration")
async def run_database_migration(
    migration: str = Query(..., description="Migration to run: 'add_statistics_columns'"),
    x_admin_email: str | None = Header(None),
    db: Session = Depends(database.get_db),
):  # type: ignore
    """
    Run a database migration to update schema.

    Available migrations:
    - add_statistics_columns: Adds missing columns to player_statistics table
    """
    require_admin(x_admin_email)

    if migration == "add_statistics_columns":
        try:
            from ..migrations.add_missing_statistics_columns import run_migration

            result = run_migration(db)
            return result
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise HTTPException(status_code=500, detail=f"Migration failed: {e!s}")
    elif migration == "add_missing_columns":
        try:
            from sqlalchemy import text
            stmts = [
                "ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS duration VARCHAR",
                "ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS hole_scores JSONB DEFAULT '{}'",
                "ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS betting_history JSONB DEFAULT '[]'",
                "ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS performance_metrics JSONB DEFAULT '{}'",
                "ALTER TABLE legacy_rounds ADD COLUMN IF NOT EXISTS created_at VARCHAR",
                "ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS hole_scores JSONB",
                "ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS betting_history JSONB",
                "ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS performance_metrics JSONB",
                "ALTER TABLE game_player_results ADD COLUMN IF NOT EXISTS created_at VARCHAR",
            ]
            applied = []
            for stmt in stmts:
                db.execute(text(stmt))
                applied.append(stmt.split("ADD COLUMN IF NOT EXISTS ")[1].split(" ")[0])
            db.commit()
            return {"status": "success", "columns_added": applied}
        except Exception as e:
            db.rollback()
            logger.error(f"Migration failed: {e}")
            raise HTTPException(status_code=500, detail=f"Migration failed: {e!s}")
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown migration: {migration}. Available: add_statistics_columns, add_missing_columns",
        )
