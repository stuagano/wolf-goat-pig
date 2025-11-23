"""
Leaderboard Service for Wolf Goat Pig

This service provides comprehensive leaderboard functionality for the Wolf Goat Pig application:
- Multiple leaderboard types (earnings, win rate, games played, etc.)
- Time-based leaderboards (all-time, weekly, monthly)
- Player rank tracking
- In-memory caching with automatic refresh
- Comprehensive error handling and logging

Features:
- Singleton pattern for service-wide consistency
- Database-backed leaderboards with SQLAlchemy
- In-memory cache with 5-minute TTL
- Support for pagination
- Rank change tracking
- Multiple leaderboard metrics
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import and_, case, desc, func
from sqlalchemy.orm import Session

from ..models import GamePlayerResult, PlayerAchievement, PlayerBadgeEarned, PlayerProfile, PlayerStatistics

logger = logging.getLogger(__name__)


class LeaderboardCache:
    """In-memory cache for leaderboard data with TTL."""

    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        """
        Initialize the cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
        self._last_cleanup = time.time()

    def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached data if not expired.

        Args:
            key: Cache key

        Returns:
            Cached data or None if expired/missing
        """
        if key not in self.cache:
            return None

        timestamp, data = self.cache[key]
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            return None

        return data

    def set(self, key: str, data: List[Dict[str, Any]]) -> None:
        """
        Store data in cache.

        Args:
            key: Cache key
            data: Data to cache
        """
        self.cache[key] = (time.time(), data)
        self._cleanup_if_needed()

    def invalidate(self, pattern: Optional[str] = None) -> None:
        """
        Invalidate cache entries.

        Args:
            pattern: If provided, only invalidate keys containing this pattern.
                    If None, invalidate all.
        """
        if pattern is None:
            self.cache.clear()
            logger.info("Cleared all leaderboard cache")
        else:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
            logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching '{pattern}'")

    def _cleanup_if_needed(self) -> None:
        """Remove expired entries periodically."""
        now = time.time()
        if now - self._last_cleanup < 60:  # Cleanup at most once per minute
            return

        expired_keys = [
            k for k, (ts, _) in self.cache.items()
            if now - ts > self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]

        self._last_cleanup = now
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


class LeaderboardService:
    """
    Service class for leaderboard management and ranking operations.

    Provides comprehensive leaderboard functionality including multiple metrics,
    time-based filtering, caching, and rank tracking.
    """

    # Supported leaderboard types
    LEADERBOARD_TYPES = [
        'total_earnings',
        'win_rate',
        'games_played',
        'average_score',
        'partnerships_won',
        'achievements_earned',
        'handicap_improvement'
    ]

    def __init__(self, db: Session):
        """
        Initialize the LeaderboardService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.cache = LeaderboardCache(ttl_seconds=300)  # 5-minute cache

    def get_leaderboard(
        self,
        leaderboard_type: str,
        db: Session,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard by type.

        Args:
            leaderboard_type: Type of leaderboard (total_earnings, win_rate, etc.)
            db: Database session
            limit: Maximum number of entries to return
            offset: Number of entries to skip (for pagination)

        Returns:
            List of leaderboard entries sorted by rank

        Raises:
            HTTPException: If leaderboard type is invalid
        """
        try:
            # Validate leaderboard type
            if leaderboard_type not in self.LEADERBOARD_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid leaderboard type. Must be one of: {', '.join(self.LEADERBOARD_TYPES)}"
                )

            # Check cache
            cache_key = f"leaderboard:{leaderboard_type}:{limit}:{offset}"
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Returning cached leaderboard for {leaderboard_type}")
                return cached_data

            # Generate leaderboard based on type
            leaderboard_data = self._generate_leaderboard(
                leaderboard_type, db, limit, offset
            )

            # Cache the result
            self.cache.set(cache_key, leaderboard_data)

            logger.info(
                f"Generated {leaderboard_type} leaderboard with {len(leaderboard_data)} entries"
            )

            return leaderboard_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting leaderboard '{leaderboard_type}': {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve leaderboard: {str(e)}"
            )

    def get_player_rank(
        self,
        player_id: int,
        leaderboard_type: str,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Get player's rank in a specific leaderboard.

        Args:
            player_id: ID of the player
            leaderboard_type: Type of leaderboard
            db: Database session

        Returns:
            Dict with rank, player info, and value, or None if player not found

        Raises:
            HTTPException: If leaderboard type is invalid
        """
        try:
            # Validate leaderboard type
            if leaderboard_type not in self.LEADERBOARD_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid leaderboard type. Must be one of: {', '.join(self.LEADERBOARD_TYPES)}"
                )

            # Get full leaderboard (without limit to find player's rank)
            full_leaderboard = self._generate_leaderboard(
                leaderboard_type, db, limit=10000, offset=0
            )

            # Find player in leaderboard
            for entry in full_leaderboard:
                if entry['player_id'] == player_id:
                    logger.info(
                        f"Player {player_id} rank in {leaderboard_type}: {entry['rank']}"
                    )
                    return entry

            logger.warning(
                f"Player {player_id} not found in {leaderboard_type} leaderboard"
            )
            return None

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error getting player {player_id} rank for '{leaderboard_type}': {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve player rank: {str(e)}"
            )

    def get_all_leaderboards(
        self,
        db: Session,
        limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all leaderboards at once.

        Args:
            db: Database session
            limit: Maximum number of entries per leaderboard

        Returns:
            Dict mapping leaderboard type to list of entries
        """
        try:
            all_leaderboards = {}

            for leaderboard_type in self.LEADERBOARD_TYPES:
                all_leaderboards[leaderboard_type] = self.get_leaderboard(
                    leaderboard_type=leaderboard_type,
                    db=db,
                    limit=limit,
                    offset=0
                )

            logger.info(f"Retrieved all {len(self.LEADERBOARD_TYPES)} leaderboards")
            return all_leaderboards

        except Exception as e:
            logger.error(f"Error getting all leaderboards: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve all leaderboards: {str(e)}"
            )

    def get_weekly_leaderboard(
        self,
        leaderboard_type: str,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get weekly leaderboard (last 7 days).

        Args:
            leaderboard_type: Type of leaderboard
            db: Database session
            limit: Maximum number of entries

        Returns:
            List of leaderboard entries for the past week

        Raises:
            HTTPException: If leaderboard type is invalid
        """
        try:
            # Validate leaderboard type
            if leaderboard_type not in self.LEADERBOARD_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid leaderboard type. Must be one of: {', '.join(self.LEADERBOARD_TYPES)}"
                )

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            # Generate time-filtered leaderboard
            leaderboard_data = self._generate_time_filtered_leaderboard(
                leaderboard_type=leaderboard_type,
                db=db,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )

            logger.info(
                f"Generated weekly {leaderboard_type} leaderboard with {len(leaderboard_data)} entries"
            )

            return leaderboard_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting weekly leaderboard '{leaderboard_type}': {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve weekly leaderboard: {str(e)}"
            )

    def get_monthly_leaderboard(
        self,
        leaderboard_type: str,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get monthly leaderboard (last 30 days).

        Args:
            leaderboard_type: Type of leaderboard
            db: Database session
            limit: Maximum number of entries

        Returns:
            List of leaderboard entries for the past month

        Raises:
            HTTPException: If leaderboard type is invalid
        """
        try:
            # Validate leaderboard type
            if leaderboard_type not in self.LEADERBOARD_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid leaderboard type. Must be one of: {', '.join(self.LEADERBOARD_TYPES)}"
                )

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            # Generate time-filtered leaderboard
            leaderboard_data = self._generate_time_filtered_leaderboard(
                leaderboard_type=leaderboard_type,
                db=db,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )

            logger.info(
                f"Generated monthly {leaderboard_type} leaderboard with {len(leaderboard_data)} entries"
            )

            return leaderboard_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting monthly leaderboard '{leaderboard_type}': {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve monthly leaderboard: {str(e)}"
            )

    def refresh_leaderboard_cache(self) -> Dict[str, Any]:
        """
        Refresh the leaderboard cache by clearing all cached data.

        Returns:
            Dict with cache statistics
        """
        try:
            cache_size_before = len(self.cache.cache)
            self.cache.invalidate()

            logger.info(f"Refreshed leaderboard cache ({cache_size_before} entries cleared)")

            return {
                "entries_cleared": cache_size_before,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error refreshing leaderboard cache: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to refresh cache: {str(e)}"
            )

    # Private helper methods

    def _generate_leaderboard(
        self,
        leaderboard_type: str,
        db: Session,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """
        Generate leaderboard data based on type.

        Args:
            leaderboard_type: Type of leaderboard
            db: Database session
            limit: Maximum number of entries
            offset: Number of entries to skip

        Returns:
            List of leaderboard entries
        """
        # Map leaderboard type to query method
        query_methods = {
            'total_earnings': self._query_total_earnings,
            'win_rate': self._query_win_rate,
            'games_played': self._query_games_played,
            'average_score': self._query_average_score,
            'partnerships_won': self._query_partnerships_won,
            'achievements_earned': self._query_achievements_earned,
            'handicap_improvement': self._query_handicap_improvement
        }

        query_method = query_methods.get(leaderboard_type)
        if not query_method:
            raise ValueError(f"Unknown leaderboard type: {leaderboard_type}")

        return query_method(db, limit, offset)

    def _generate_time_filtered_leaderboard(
        self,
        leaderboard_type: str,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Generate time-filtered leaderboard data.

        Args:
            leaderboard_type: Type of leaderboard
            db: Database session
            start_date: Start of time range
            end_date: End of time range
            limit: Maximum number of entries

        Returns:
            List of leaderboard entries
        """
        # For time-filtered leaderboards, we need to query GamePlayerResult
        # and aggregate data for the specified time period

        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()

        # Query game results in date range
        results_query = db.query(
            GamePlayerResult.player_profile_id,
            PlayerProfile.name.label('player_name'),
            func.sum(GamePlayerResult.total_earnings).label('total_earnings'),
            func.count(GamePlayerResult.id).label('games_played'),
            func.sum(case((GamePlayerResult.final_position == 1, 1), else_=0)).label('wins'),
            func.sum(GamePlayerResult.partnerships_won).label('partnerships_won'),
            func.avg(GamePlayerResult.final_position).label('avg_position')
        ).join(
            PlayerProfile, PlayerProfile.id == GamePlayerResult.player_profile_id
        ).filter(
            and_(
                PlayerProfile.is_active == 1,
                PlayerProfile.is_ai == 0,
                GamePlayerResult.created_at >= start_iso,
                GamePlayerResult.created_at <= end_iso
            )
        ).group_by(
            GamePlayerResult.player_profile_id,
            PlayerProfile.name
        )

        # Apply ordering based on leaderboard type
        if leaderboard_type == 'total_earnings':
            results_query = results_query.order_by(desc('total_earnings'))
        elif leaderboard_type == 'win_rate':
            results_query = results_query.order_by(
                desc(func.cast('wins', float) / func.cast('games_played', float))
            )
        elif leaderboard_type == 'games_played':
            results_query = results_query.order_by(desc('games_played'))
        elif leaderboard_type == 'partnerships_won':
            results_query = results_query.order_by(desc('partnerships_won'))
        elif leaderboard_type == 'average_score':
            results_query = results_query.order_by('avg_position')
        else:
            # Default to total earnings
            results_query = results_query.order_by(desc('total_earnings'))

        results = results_query.limit(limit).all()

        # Format results
        leaderboard = []
        for rank, result in enumerate(results, start=1):
            games_played = result.games_played or 1
            wins = result.wins or 0
            win_rate = (wins / games_played) * 100 if games_played > 0 else 0.0

            # Determine value based on leaderboard type
            if leaderboard_type == 'total_earnings':
                value = float(result.total_earnings or 0)
            elif leaderboard_type == 'win_rate':
                value = round(win_rate, 1)
            elif leaderboard_type == 'games_played':
                value = int(games_played)
            elif leaderboard_type == 'partnerships_won':
                value = int(result.partnerships_won or 0)
            elif leaderboard_type == 'average_score':
                value = round(float(result.avg_position or 0), 2)
            else:
                value = float(result.total_earnings or 0)

            leaderboard.append({
                'rank': rank,
                'player_id': result.player_profile_id,
                'player_name': result.player_name,
                'value': value
            })

        return leaderboard

    def _query_total_earnings(
        self,
        db: Session,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """Query total earnings leaderboard."""
        query = db.query(
            PlayerProfile.id,
            PlayerProfile.name,
            PlayerStatistics.total_earnings
        ).join(
            PlayerStatistics, PlayerProfile.id == PlayerStatistics.player_id
        ).filter(
            and_(
                PlayerProfile.is_active == 1,
                PlayerProfile.is_ai == 0,
                PlayerStatistics.games_played >= 1
            )
        ).order_by(
            desc(PlayerStatistics.total_earnings)
        ).limit(limit).offset(offset)

        results = query.all()

        leaderboard = []
        for rank, result in enumerate(results, start=offset + 1):
            leaderboard.append({
                'rank': rank,
                'player_id': result.id,
                'player_name': result.name,
                'value': round(float(result.total_earnings), 2)
            })

        return leaderboard

    def _query_win_rate(
        self,
        db: Session,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """Query win rate leaderboard."""
        query = db.query(
            PlayerProfile.id,
            PlayerProfile.name,
            PlayerStatistics.games_played,
            PlayerStatistics.games_won
        ).join(
            PlayerStatistics, PlayerProfile.id == PlayerStatistics.player_id
        ).filter(
            and_(
                PlayerProfile.is_active == 1,
                PlayerProfile.is_ai == 0,
                PlayerStatistics.games_played >= 5  # Minimum games for win rate
            )
        ).order_by(
            desc(func.cast(PlayerStatistics.games_won, float) /
                 func.cast(PlayerStatistics.games_played, float))
        ).limit(limit).offset(offset)

        results = query.all()

        leaderboard = []
        for rank, result in enumerate(results, start=offset + 1):
            win_rate = (result.games_won / result.games_played) * 100
            leaderboard.append({
                'rank': rank,
                'player_id': result.id,
                'player_name': result.name,
                'value': round(win_rate, 1)
            })

        return leaderboard

    def _query_games_played(
        self,
        db: Session,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """Query games played leaderboard."""
        query = db.query(
            PlayerProfile.id,
            PlayerProfile.name,
            PlayerStatistics.games_played
        ).join(
            PlayerStatistics, PlayerProfile.id == PlayerStatistics.player_id
        ).filter(
            and_(
                PlayerProfile.is_active == 1,
                PlayerProfile.is_ai == 0,
                PlayerStatistics.games_played >= 1
            )
        ).order_by(
            desc(PlayerStatistics.games_played)
        ).limit(limit).offset(offset)

        results = query.all()

        leaderboard = []
        for rank, result in enumerate(results, start=offset + 1):
            leaderboard.append({
                'rank': rank,
                'player_id': result.id,
                'player_name': result.name,
                'value': int(result.games_played)
            })

        return leaderboard

    def _query_average_score(
        self,
        db: Session,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """Query average score (position) leaderboard."""
        # Calculate average finishing position from game results
        query = db.query(
            GamePlayerResult.player_profile_id,
            PlayerProfile.name,
            func.avg(GamePlayerResult.final_position).label('avg_position'),
            func.count(GamePlayerResult.id).label('games_count')
        ).join(
            PlayerProfile, PlayerProfile.id == GamePlayerResult.player_profile_id
        ).filter(
            and_(
                PlayerProfile.is_active == 1,
                PlayerProfile.is_ai == 0
            )
        ).group_by(
            GamePlayerResult.player_profile_id,
            PlayerProfile.name
        ).having(
            func.count(GamePlayerResult.id) >= 5  # Minimum games
        ).order_by(
            'avg_position'  # Lower is better
        ).limit(limit).offset(offset)

        results = query.all()

        leaderboard = []
        for rank, result in enumerate(results, start=offset + 1):
            leaderboard.append({
                'rank': rank,
                'player_id': result.player_profile_id,
                'player_name': result.name,
                'value': round(float(result.avg_position), 2)
            })

        return leaderboard

    def _query_partnerships_won(
        self,
        db: Session,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """Query partnerships won leaderboard."""
        query = db.query(
            PlayerProfile.id,
            PlayerProfile.name,
            PlayerStatistics.partnerships_won
        ).join(
            PlayerStatistics, PlayerProfile.id == PlayerStatistics.player_id
        ).filter(
            and_(
                PlayerProfile.is_active == 1,
                PlayerProfile.is_ai == 0,
                PlayerStatistics.partnerships_formed >= 1
            )
        ).order_by(
            desc(PlayerStatistics.partnerships_won)
        ).limit(limit).offset(offset)

        results = query.all()

        leaderboard = []
        for rank, result in enumerate(results, start=offset + 1):
            leaderboard.append({
                'rank': rank,
                'player_id': result.id,
                'player_name': result.name,
                'value': int(result.partnerships_won)
            })

        return leaderboard

    def _query_achievements_earned(
        self,
        db: Session,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """Query achievements/badges earned leaderboard."""
        # Count both legacy achievements and new badges
        achievements_query = db.query(
            PlayerAchievement.player_profile_id,
            func.count(PlayerAchievement.id).label('achievement_count')
        ).group_by(
            PlayerAchievement.player_profile_id
        ).subquery()

        badges_query = db.query(
            PlayerBadgeEarned.player_profile_id,
            func.count(PlayerBadgeEarned.id).label('badge_count')
        ).group_by(
            PlayerBadgeEarned.player_profile_id
        ).subquery()

        # Combine both sources
        query = db.query(
            PlayerProfile.id,
            PlayerProfile.name,
            func.coalesce(achievements_query.c.achievement_count, 0).label('achievements'),
            func.coalesce(badges_query.c.badge_count, 0).label('badges')
        ).outerjoin(
            achievements_query,
            PlayerProfile.id == achievements_query.c.player_profile_id
        ).outerjoin(
            badges_query,
            PlayerProfile.id == badges_query.c.player_profile_id
        ).filter(
            and_(
                PlayerProfile.is_active == 1,
                PlayerProfile.is_ai == 0
            )
        ).order_by(
            desc(
                func.coalesce(achievements_query.c.achievement_count, 0) +
                func.coalesce(badges_query.c.badge_count, 0)
            )
        ).limit(limit).offset(offset)

        results = query.all()

        leaderboard = []
        for rank, result in enumerate(results, start=offset + 1):
            total_achievements = (result.achievements or 0) + (result.badges or 0)
            if total_achievements > 0:  # Only include players with achievements
                leaderboard.append({
                    'rank': rank,
                    'player_id': result.id,
                    'player_name': result.name,
                    'value': int(total_achievements)
                })

        return leaderboard

    def _query_handicap_improvement(
        self,
        db: Session,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """Query handicap improvement leaderboard."""
        # Get players with GHIN handicap history to calculate improvement
        from ..models import GHINHandicapHistory

        # Subquery to get earliest handicap
        earliest_handicap = db.query(
            GHINHandicapHistory.player_profile_id,
            func.min(GHINHandicapHistory.handicap_index).label('min_handicap'),
            func.max(GHINHandicapHistory.handicap_index).label('max_handicap')
        ).group_by(
            GHINHandicapHistory.player_profile_id
        ).having(
            func.count(GHINHandicapHistory.id) >= 2  # At least 2 records
        ).subquery()

        # Calculate improvement (reduction is positive improvement)
        query = db.query(
            PlayerProfile.id,
            PlayerProfile.name,
            PlayerProfile.handicap.label('current_handicap'),
            earliest_handicap.c.max_handicap,
            (earliest_handicap.c.max_handicap - PlayerProfile.handicap).label('improvement')
        ).join(
            earliest_handicap,
            PlayerProfile.id == earliest_handicap.c.player_profile_id
        ).filter(
            and_(
                PlayerProfile.is_active == 1,
                PlayerProfile.is_ai == 0
            )
        ).order_by(
            desc('improvement')
        ).limit(limit).offset(offset)

        results = query.all()

        leaderboard = []
        for rank, result in enumerate(results, start=offset + 1):
            improvement = float(result.improvement or 0)
            if improvement > 0:  # Only include players who improved
                leaderboard.append({
                    'rank': rank,
                    'player_id': result.id,
                    'player_name': result.name,
                    'value': round(improvement, 1)
                })

        return leaderboard


# ====================================================================================
# SINGLETON PATTERN
# ====================================================================================

_leaderboard_service_instance: Optional[LeaderboardService] = None


def get_leaderboard_service(db: Session) -> LeaderboardService:
    """
    Get or create the singleton LeaderboardService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        LeaderboardService instance
    """
    global _leaderboard_service_instance

    if _leaderboard_service_instance is None:
        _leaderboard_service_instance = LeaderboardService(db)
        logger.info("Created new LeaderboardService singleton instance")
    else:
        # Update the database session for the existing instance
        _leaderboard_service_instance.db = db

    return _leaderboard_service_instance
