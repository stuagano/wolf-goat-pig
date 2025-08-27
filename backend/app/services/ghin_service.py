"""
GHIN Service for integrating with Golf Handicap Information Network

This service handles:
- Syncing player handicaps from GHIN
- Fetching recent scores 
- Updating local database with GHIN data
- Joining GHIN data with existing player statistics
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
import logging
import os
import httpx # Added httpx for API calls
from ..models import PlayerProfile, PlayerStatistics, GHINScore, GHINHandicapHistory
from ..schemas import PlayerProfileResponse

# Note: The actual GHIN API integration would require proper authentication
# For now, we'll create a service structure that can be easily adapted
# when the official GHIN API access is available

logger = logging.getLogger(__name__)

class GHINService:
    """Service class for GHIN integration operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.initialized = False
        self.ghin_username = os.getenv('GHIN_USERNAME')
        self.ghin_password = os.getenv('GHIN_PASSWORD')
        self.jwt_token: Optional[str] = None # Store JWT token
        self.GHIN_API_BASE_URL = "https://api2.ghin.com/api/v1"
    
    async def initialize(self):
        """Initialize GHIN service with authentication."""
        try:
            if not self.ghin_username or not self.ghin_password:
                logger.warning("GHIN credentials not configured. GHIN integration disabled.")
                return False
            
            GHIN_AUTH_URL = "https://api2.ghin.com/api/v1/golfer_login.json"
            
            async with httpx.AsyncClient() as client:
                auth_response = await client.post(GHIN_AUTH_URL, json={
                    "user": {"email_or_ghin": self.ghin_username, "password": self.ghin_password},
                    "token": os.getenv('GHIN_API_STATIC_TOKEN'), # Static token if required
                    "source": "GHINcom"
                })
                auth_response.raise_for_status() # Raise an exception for HTTP errors
                
                auth_data = auth_response.json()
                self.jwt_token = auth_data["golfer_user"]["golfer_user_token"]
                
                if self.jwt_token:
                    self.initialized = True
                    logger.info("GHIN service initialized successfully and authenticated")
                    return True
                else:
                    logger.error("GHIN authentication failed: No JWT token received.")
                    self.initialized = False
                    return False
            
        except Exception as e:
            logger.error(f"Failed to initialize GHIN service: {e}")
            self.initialized = False
            return False
    
    def is_available(self) -> bool:
        """Check if GHIN service is available and initialized."""
        return self.initialized
    
    async def sync_player_handicap(self, player_id: int) -> Optional[Dict[str, Any]]:
        """
        Sync a single player's handicap from GHIN.
        
        Args:
            player_id: Local player profile ID
            
        Returns:
            Dict with handicap data or None if failed
        """
        try:
            player = self.db.query(PlayerProfile).filter(PlayerProfile.id == player_id).first()
            if not player or not player.ghin_id:
                logger.warning(f"Player {player_id} has no GHIN ID configured")
                return None
            
            if not self.is_available():
                logger.error("GHIN service is not initialized or available.")
                return None

            # Use the actual GHIN API call
            handicap_data = await self._fetch_handicap_from_ghin(player.ghin_id)
            
            if handicap_data:
                # Update player profile with latest handicap
                player.handicap = handicap_data.get('handicap_index', player.handicap)
                player.ghin_last_updated = datetime.now().isoformat()
                
                # Store handicap history
                handicap_history = GHINHandicapHistory(
                    player_profile_id=player_id,
                    ghin_id=player.ghin_id,
                    effective_date=handicap_data.get('effective_date', datetime.now().date().isoformat()),
                    handicap_index=handicap_data.get('handicap_index'),
                    revision_reason=handicap_data.get('revision_reason'),
                    scores_used_count=handicap_data.get('scores_used_count'),
                    synced_at=datetime.now().isoformat(),
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                self.db.add(handicap_history)
                self.db.commit()
                
                logger.info(f"Synced handicap for player {player.name}: {handicap_data.get('handicap_index')}")
                return handicap_data
                
        except Exception as e:
            logger.error(f"Failed to sync handicap for player {player_id}: {e}")
            self.db.rollback()
            return None
    
    async def sync_player_scores(self, player_id: int, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Sync a player's recent scores from GHIN.
        
        Args:
            player_id: Local player profile ID
            days_back: How many days back to fetch scores
            
        Returns:
            List of score records that were synced
        """
        try:
            player = self.db.query(PlayerProfile).filter(PlayerProfile.id == player_id).first()
            if not player or not player.ghin_id:
                logger.warning(f"Player {player_id} has no GHIN ID configured")
                return []
            
            if not self.is_available():
                logger.error("GHIN service is not initialized or available.")
                return []

            # Use the actual GHIN API call
            scores_data = await self._fetch_scores_from_ghin(player.ghin_id, days_back)
            
            synced_scores = []
            for score_data in scores_data:
                # Check if we already have this score
                existing_score = self.db.query(GHINScore).filter(
                    and_(
                        GHINScore.player_profile_id == player_id,
                        GHINScore.ghin_id == player.ghin_id,
                        GHINScore.score_date == score_data.get('date'),
                        GHINScore.course_name == score_data.get('course')
                    )
                ).first()
                
                if not existing_score:
                    # Create new score record
                    ghin_score = GHINScore(
                        player_profile_id=player_id,
                        ghin_id=player.ghin_id,
                        score_date=score_data.get('date'),
                        course_name=score_data.get('course'),
                        tees=score_data.get('tees'),
                        score=score_data.get('score'),
                        course_rating=score_data.get('course_rating'),
                        slope_rating=score_data.get('slope_rating'),
                        differential=score_data.get('differential'),
                        posted=1 if score_data.get('posted', True) else 0,
                        handicap_index_at_time=score_data.get('handicap_index_at_time'),
                        synced_at=datetime.now().isoformat(),
                        created_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat()
                    )
                    
                    self.db.add(ghin_score)
                    synced_scores.append(score_data)
            
            if synced_scores:
                self.db.commit()
                logger.info(f"Synced {len(synced_scores)} new scores for player {player.name}")
            
            return synced_scores
            
        except Exception as e:
            logger.error(f"Failed to sync scores for player {player_id}: {e}")
            self.db.rollback()
            return []
    
    async def sync_all_players_handicaps(self) -> Dict[str, Any]:
        """
        Sync handicaps for all players who have GHIN IDs.
        
        Returns:
            Summary of sync results
        """
        try:
            players_with_ghin = self.db.query(PlayerProfile).filter(
                and_(
                    PlayerProfile.ghin_id.isnot(None),
                    PlayerProfile.is_active == 1
                )
            ).all()
            
            if not players_with_ghin:
                logger.info("No players with GHIN IDs found for sync")
                return {"total_players": 0, "synced": 0, "errors": 0}
            
            synced_count = 0
            error_count = 0
            
            for player in players_with_ghin:
                try:
                    result = await self.sync_player_handicap(player.id)
                    if result:
                        synced_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"Error syncing player {player.name}: {e}")
                    error_count += 1
            
            summary = {
                "total_players": len(players_with_ghin),
                "synced": synced_count,
                "errors": error_count,
                "synced_at": datetime.now().isoformat()
            }
            
            logger.info(f"Bulk handicap sync completed: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to sync all player handicaps: {e}")
            return {"total_players": 0, "synced": 0, "errors": 1, "error": str(e)}
    
    async def search_golfers(self, last_name: str, first_name: Optional[str] = None, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Search for golfers by name using the GHIN API."""
        if not self.is_available():
            raise ConnectionError("GHIN service is not initialized or available.")

        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        url = f"{self.GHIN_API_BASE_URL}/golfer_search"
        
        params = {
            "last_name": last_name,
            "page": page,
            "per_page": per_page,
            "from_ghin": "true",
            "per_page": 100
        }
        if first_name:
            params["first_name"] = first_name
            
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    def get_player_ghin_data(self, player_id: int) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive GHIN data for a player from local database.
        
        Args:
            player_id: Local player profile ID
            
        Returns:
            Dict with GHIN data or None if not found
        """
        try:
            player = self.db.query(PlayerProfile).filter(PlayerProfile.id == player_id).first()
            if not player or not player.ghin_id:
                return None
            
            # Get recent scores
            recent_scores = self.db.query(GHINScore).filter(
                GHINScore.player_profile_id == player_id
            ).order_by(desc(GHINScore.score_date)).limit(20).all()
            
            # Get handicap history
            handicap_history = self.db.query(GHINHandicapHistory).filter(
                GHINHandicapHistory.player_profile_id == player_id
            ).order_by(desc(GHINHandicapHistory.effective_date)).limit(10).all()
            
            return {
                "ghin_id": player.ghin_id,
                "current_handicap": player.handicap,
                "last_updated": player.ghin_last_updated,
                "recent_scores": [
                    {
                        "date": score.score_date,
                        "course": score.course_name,
                        "tees": score.tees,
                        "score": score.score,
                        "differential": score.differential,
                        "posted": bool(score.posted)
                    }
                    for score in recent_scores
                ],
                "handicap_history": [
                    {
                        "effective_date": history.effective_date,
                        "handicap_index": history.handicap_index,
                        "revision_reason": history.revision_reason
                    }
                    for history in handicap_history
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get GHIN data for player {player_id}: {e}")
            return None
    
    def get_leaderboard_with_ghin_data(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get leaderboard data enhanced with GHIN information.
        Uses stored handicap data even if GHIN API is unavailable.
        
        Args:
            limit: Maximum number of players to return
            
        Returns:
            List of player records with GHIN data integrated
        """
        try:
            # Get basic leaderboard data (exclude AI players)
            query = self.db.query(PlayerProfile, PlayerStatistics).join(
                PlayerStatistics, PlayerProfile.id == PlayerStatistics.player_id
            ).filter(
                PlayerProfile.is_active == 1,
                PlayerProfile.is_ai == 0  # Exclude AI players from leaderboard
            ).order_by(desc(PlayerStatistics.total_earnings))
            
            players_with_stats = query.limit(limit).all()
            
            enhanced_leaderboard = []
            for profile, stats in players_with_stats:
                # Calculate win percentage
                win_percentage = (stats.games_won / max(1, stats.games_played)) * 100
                
                # Always try to get stored GHIN data, regardless of API availability
                ghin_data = None
                if profile.ghin_id:
                    ghin_data = self.get_player_ghin_data(profile.id)
                
                # Calculate recent form from stored GHIN scores if available
                recent_form = "N/A"
                if ghin_data and ghin_data.get('recent_scores'):
                    recent_scores = ghin_data['recent_scores'][:5]  # Last 5 rounds
                    if len(recent_scores) >= 3:
                        # Use stored handicap for comparison if available
                        comparison_handicap = profile.handicap if profile.handicap else 18.0
                        avg_differential = sum(s.get('differential', 0) for s in recent_scores if s.get('differential')) / len(recent_scores)
                        if avg_differential < comparison_handicap - 2:
                            recent_form = "Excellent"
                        elif avg_differential < comparison_handicap:
                            recent_form = "Good"
                        elif avg_differential > comparison_handicap + 2:
                            recent_form = "Poor"
                        else:
                            recent_form = "Average"
                
                enhanced_record = {
                    "rank": len(enhanced_leaderboard) + 1,
                    "player_name": profile.name,
                    "games_played": stats.games_played,
                    "win_percentage": round(win_percentage, 1),
                    "avg_earnings": round(stats.avg_earnings_per_hole, 2),
                    "total_earnings": round(stats.total_earnings, 2),
                    "partnership_success": round(stats.partnership_success_rate * 100, 1),
                    # Always include stored handicap (last known value)
                    "handicap": profile.handicap,
                    "ghin_id": profile.ghin_id,
                    "ghin_last_updated": profile.ghin_last_updated,
                    "recent_form": recent_form,
                    "ghin_data": ghin_data
                }
                
                enhanced_leaderboard.append(enhanced_record)
            
            return enhanced_leaderboard
            
        except Exception as e:
            logger.error(f"Failed to get enhanced leaderboard: {e}")
            # Even on error, try to return basic leaderboard structure with stored handicaps
            try:
                from .player_service import PlayerService
                player_service = PlayerService(self.db)
                basic_leaderboard = player_service.get_leaderboard(limit=limit)
                
                # Add stored handicap data to basic leaderboard
                for player in basic_leaderboard:
                    profile = self.db.query(PlayerProfile).filter(PlayerProfile.name == player.player_name).first()
                    if profile:
                        player.handicap = profile.handicap
                        player.ghin_id = profile.ghin_id
                        player.ghin_last_updated = profile.ghin_last_updated
                
                return [vars(player) for player in basic_leaderboard]
            except Exception as fallback_error:
                logger.error(f"Failed to get fallback leaderboard: {fallback_error}")
                return []
    
    # TODO: These methods would connect to the actual GHIN API
    # For now, they return mock data for testing
    
    async def _fetch_handicap_from_ghin(self, ghin_id: str) -> Optional[Dict[str, Any]]:
        """Fetch handicap from GHIN API."""
        logger.info(f"Fetching handicap for GHIN ID {ghin_id}")
        
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        url = f"{self.GHIN_API_BASE_URL}/golfers/{ghin_id}/handicap_index"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def _fetch_scores_from_ghin(self, ghin_id: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch scores from GHIN API."""
        logger.info(f"Fetching scores for GHIN ID {ghin_id} ({days_back} days)")
        
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        url = f"{self.GHIN_API_BASE_URL}/golfers/{ghin_id}/scores?days_back={days_back}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()