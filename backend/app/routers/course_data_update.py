"""
Endpoint to update course data for in-progress games
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..database import get_db
from .. import models
from ..data.wing_point_course_data import WING_POINT_COURSE_DATA

router = APIRouter()
logger = logging.getLogger(__name__)


@router.patch("/games/{game_id}/update-course-data")
async def update_game_course_data(
    game_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update course data (par and handicap) for an in-progress game.
    
    This endpoint updates the hole_par for each hole in the game's hole_history
    based on the latest Wing Point course data.
    
    Use this when course data has been updated and you need to sync in-progress games.
    """
    try:
        # Get the game
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()
        
        if not game:
            raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
        
        game_state = game.state or {}
        
        # Check if game has hole history
        hole_history = game_state.get("hole_history", [])
        if not hole_history:
            return {
                "success": True,
                "message": "No holes to update - game has no hole history yet",
                "holes_updated": 0
            }
        
        # Create mappings of hole number -> par and handicap from Wing Point data
        hole_data_map = {}
        for hole_data in WING_POINT_COURSE_DATA["holes"]:
            hole_num = hole_data["hole_number"]
            hole_data_map[hole_num] = {
                "par": hole_data["par"],
                "handicap": hole_data["handicap_men"]  # Using men's handicap (stroke index)
            }
        
        # Update hole_history (already played holes)
        holes_updated = 0
        for hole in hole_history:
            hole_number = hole.get("hole") or hole.get("hole_number")
            if hole_number and hole_number in hole_data_map:
                course_data = hole_data_map[hole_number]
                
                old_par = hole.get("hole_par")
                new_par = course_data["par"]
                old_handicap = hole.get("hole_handicap")
                new_handicap = course_data["handicap"]
                
                updated = False
                if old_par != new_par:
                    hole["hole_par"] = new_par
                    updated = True
                    logger.info(
                        f"Updated hole {hole_number} par from {old_par} to {new_par} "
                        f"in game {game_id}"
                    )
                
                if old_handicap != new_handicap:
                    hole["hole_handicap"] = new_handicap
                    updated = True
                    logger.info(
                        f"Updated hole {hole_number} handicap from {old_handicap} to {new_handicap} "
                        f"in game {game_id}"
                    )
                
                if updated:
                    holes_updated += 1
        
        # Create/update holes_config with ALL 18 holes
        holes_config = []
        for hole_num in range(1, 19):
            if hole_num in hole_data_map:
                course_data = hole_data_map[hole_num]
                holes_config.append({
                    "hole_number": hole_num,
                    "par": course_data["par"],
                    "handicap": course_data["handicap"]
                })
        
        game_state["holes_config"] = holes_config
        total_holes_configured = len(holes_config)
        
        # Save updated game state (always save to add holes_config)
        game.state = game_state
        
        # Mark state as modified for SQLAlchemy to detect JSON changes
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(game, "state")
        
        from datetime import datetime
        game.updated_at = datetime.utcnow().isoformat()
        
        db.commit()
        db.refresh(game)
        
        logger.info(
            f"Successfully updated course data for game {game_id}: "
            f"{holes_updated} holes in history updated, {total_holes_configured} holes configured"
        )
        
        return {
            "success": True,
            "game_id": game_id,
            "holes_in_history_updated": holes_updated,
            "total_holes_in_history": len(hole_history),
            "holes_configured": total_holes_configured,
            "message": f"Updated {holes_updated} played hole(s) and configured all {total_holes_configured} holes with Wing Point data"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating course data for game {game_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating course data: {str(e)}"
        )


@router.patch("/games/update-all-course-data")
async def update_all_games_course_data(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update course data for ALL in-progress games.
    
    Use this to bulk-update all active games after course data changes.
    """
    try:
        # Get all in-progress games
        games = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_status == "in_progress"
        ).all()
        
        if not games:
            return {
                "success": True,
                "message": "No in-progress games found",
                "games_updated": 0,
                "total_holes_updated": 0
            }
        
        # Create mappings of hole number -> par and handicap from Wing Point data
        hole_data_map = {}
        for hole_data in WING_POINT_COURSE_DATA["holes"]:
            hole_num = hole_data["hole_number"]
            hole_data_map[hole_num] = {
                "par": hole_data["par"],
                "handicap": hole_data["handicap_men"]  # Using men's handicap (stroke index)
            }
        
        # Create holes_config for all 18 holes
        holes_config_template = []
        for hole_num in range(1, 19):
            if hole_num in hole_data_map:
                course_data = hole_data_map[hole_num]
                holes_config_template.append({
                    "hole_number": hole_num,
                    "par": course_data["par"],
                    "handicap": course_data["handicap"]
                })
        
        games_updated = 0
        total_holes_updated = 0
        game_details = []
        
        for game in games:
            game_state = game.state or {}
            hole_history = game_state.get("hole_history", [])
            
            holes_updated_this_game = 0
            
            # Update each hole's par and handicap in hole_history
            for hole in hole_history:
                hole_number = hole.get("hole") or hole.get("hole_number")
                if hole_number and hole_number in hole_data_map:
                    course_data = hole_data_map[hole_number]
                    
                    old_par = hole.get("hole_par")
                    new_par = course_data["par"]
                    old_handicap = hole.get("hole_handicap")
                    new_handicap = course_data["handicap"]
                    
                    updated = False
                    if old_par != new_par:
                        hole["hole_par"] = new_par
                        updated = True
                    
                    if old_handicap != new_handicap:
                        hole["hole_handicap"] = new_handicap
                        updated = True
                    
                    if updated:
                        holes_updated_this_game += 1
            
            # Always add/update holes_config with all 18 holes
            game_state["holes_config"] = holes_config_template
            
            # Save game state (always save to add holes_config)
            game.state = game_state
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(game, "state")
            
            from datetime import datetime
            game.updated_at = datetime.utcnow().isoformat()
            
            games_updated += 1
            total_holes_updated += holes_updated_this_game
            
            game_details.append({
                "game_id": game.game_id,
                "holes_in_history_updated": holes_updated_this_game,
                "holes_configured": len(holes_config_template)
            })
        
        # Commit all changes
        db.commit()
        logger.info(
            f"Bulk update complete: {games_updated} games, "
            f"{total_holes_updated} total holes in history updated, "
            f"all games configured with 18 holes"
        )
        
        return {
            "success": True,
            "games_updated": games_updated,
            "total_games_checked": len(games),
            "total_holes_in_history_updated": total_holes_updated,
            "holes_configured_per_game": 18,
            "game_details": game_details,
            "message": f"Updated {games_updated} game(s): {total_holes_updated} played holes updated, all games configured with 18 Wing Point holes"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk course data update: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating course data: {str(e)}"
        )
