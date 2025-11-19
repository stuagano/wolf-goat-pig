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
        
        # Update each hole's par and handicap in the history
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
        
        # Save updated game state
        if holes_updated > 0:
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
                f"{holes_updated} holes updated"
            )
        
        return {
            "success": True,
            "game_id": game_id,
            "holes_updated": holes_updated,
            "total_holes": len(hole_history),
            "message": f"Updated {holes_updated} hole(s) with latest Wing Point course data"
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
        
        games_updated = 0
        total_holes_updated = 0
        game_details = []
        
        for game in games:
            game_state = game.state or {}
            hole_history = game_state.get("hole_history", [])
            
            if not hole_history:
                continue
            
            holes_updated_this_game = 0
            
            # Update each hole's par and handicap
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
            
            # Save if any holes were updated
            if holes_updated_this_game > 0:
                game.state = game_state
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(game, "state")
                
                from datetime import datetime
                game.updated_at = datetime.utcnow().isoformat()
                
                games_updated += 1
                total_holes_updated += holes_updated_this_game
                
                game_details.append({
                    "game_id": game.game_id,
                    "holes_updated": holes_updated_this_game
                })
        
        # Commit all changes
        if games_updated > 0:
            db.commit()
            logger.info(
                f"Bulk update complete: {games_updated} games, "
                f"{total_holes_updated} total holes updated"
            )
        
        return {
            "success": True,
            "games_updated": games_updated,
            "total_games_checked": len(games),
            "total_holes_updated": total_holes_updated,
            "game_details": game_details,
            "message": f"Updated {games_updated} game(s) with latest Wing Point course data"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk course data update: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating course data: {str(e)}"
        )
