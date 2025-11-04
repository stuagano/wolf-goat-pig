"""
Achievement Service - Unified Badge and Achievement Management

This service unifies the existing Badge system (BadgeEngine) and PlayerAchievement model,
providing a single interface for all achievement-related operations.

Features:
- Badge awarding and tracking
- Badge eligibility checking
- Progress tracking toward badges
- Legacy PlayerAchievement support (backward compatibility)
- Migration from PlayerAchievement to Badge system
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime
import logging

from ..models import (
    PlayerProfile, Badge, PlayerBadgeEarned, BadgeProgress,
    PlayerAchievement, BadgeSeries, PlayerSeriesProgress
)
from ..badge_engine import BadgeEngine

logger = logging.getLogger(__name__)


class AchievementService:
    """
    Service class for unified achievement and badge management.

    This service provides a single interface for working with both the new Badge system
    and the legacy PlayerAchievement system, with methods to migrate between them.
    """

    def __init__(self, db: Session):
        """
        Initialize the AchievementService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.badge_engine = BadgeEngine(db)

    # ====================================================================================
    # BADGE SYSTEM METHODS
    # ====================================================================================

    def award_badge(
        self,
        player_profile_id: int,
        badge_name: str,
        game_record_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Award a badge to a player by badge name.

        Args:
            player_profile_id: ID of the player to award badge to
            badge_name: Name of the badge to award
            game_record_id: Optional ID of the game where badge was earned

        Returns:
            Dict containing badge info if awarded, None if already earned or badge not found
        """
        try:
            # Get badge by name
            badge = self.db.query(Badge).filter(
                and_(Badge.name == badge_name, Badge.is_active == True)
            ).first()

            if not badge:
                logger.warning(f"Badge '{badge_name}' not found or inactive")
                return None

            # Check if player already has this badge
            existing = self.db.query(PlayerBadgeEarned).filter(
                and_(
                    PlayerBadgeEarned.player_profile_id == player_profile_id,
                    PlayerBadgeEarned.badge_id == badge.id
                )
            ).first()

            if existing:
                logger.info(f"Player {player_profile_id} already has badge '{badge_name}'")
                return None

            # Award the badge using BadgeEngine
            earned_badge = self.badge_engine._award_badge(
                player_profile_id=player_profile_id,
                badge_id=badge.id,
                game_record_id=game_record_id
            )

            if earned_badge:
                logger.info(
                    f"Awarded badge '{badge_name}' to player {player_profile_id} "
                    f"(serial #{earned_badge.serial_number})"
                )

                return {
                    "badge_id": badge.id,
                    "badge_name": badge.name,
                    "description": badge.description,
                    "category": badge.category,
                    "rarity": badge.rarity,
                    "earned_at": earned_badge.earned_at,
                    "serial_number": earned_badge.serial_number,
                    "image_url": badge.image_url,
                    "points_value": badge.points_value
                }

            return None

        except Exception as e:
            logger.error(f"Error awarding badge '{badge_name}' to player {player_profile_id}: {e}")
            self.db.rollback()
            raise

    def get_player_badges(self, player_profile_id: int) -> List[Dict[str, Any]]:
        """
        Get all badges earned by a player.

        Args:
            player_profile_id: ID of the player

        Returns:
            List of dicts containing badge information
        """
        try:
            # Query all badges earned by player
            earned_badges = self.db.query(PlayerBadgeEarned, Badge).join(
                Badge, PlayerBadgeEarned.badge_id == Badge.id
            ).filter(
                PlayerBadgeEarned.player_profile_id == player_profile_id
            ).order_by(desc(PlayerBadgeEarned.earned_at)).all()

            badges_list = []
            for earned, badge in earned_badges:
                badges_list.append({
                    "badge_id": badge.id,
                    "badge_name": badge.name,
                    "description": badge.description,
                    "category": badge.category,
                    "rarity": badge.rarity,
                    "earned_at": earned.earned_at,
                    "serial_number": earned.serial_number,
                    "game_record_id": earned.game_record_id,
                    "image_url": badge.image_url,
                    "points_value": badge.points_value,
                    "is_favorited": earned.is_favorited,
                    "showcase_position": earned.showcase_position
                })

            logger.info(f"Retrieved {len(badges_list)} badges for player {player_profile_id}")
            return badges_list

        except Exception as e:
            logger.error(f"Error getting badges for player {player_profile_id}: {e}")
            raise

    def get_available_badges(self) -> List[Dict[str, Any]]:
        """
        Get all available badges that can be earned.

        Returns:
            List of dicts containing badge information
        """
        try:
            badges = self.db.query(Badge).filter(Badge.is_active == True).all()

            badges_list = []
            for badge in badges:
                badges_list.append({
                    "badge_id": badge.id,
                    "badge_name": badge.name,
                    "description": badge.description,
                    "category": badge.category,
                    "rarity": badge.rarity,
                    "trigger_type": badge.trigger_type,
                    "image_url": badge.image_url,
                    "points_value": badge.points_value,
                    "max_supply": badge.max_supply,
                    "current_supply": badge.current_supply,
                    "series_id": badge.series_id,
                    "tier": badge.tier
                })

            logger.info(f"Retrieved {len(badges_list)} available badges")
            return badges_list

        except Exception as e:
            logger.error(f"Error getting available badges: {e}")
            raise

    def check_badge_eligibility(
        self,
        player_profile_id: int,
        badge_name: str
    ) -> bool:
        """
        Check if a player is eligible for a specific badge.

        Args:
            player_profile_id: ID of the player
            badge_name: Name of the badge to check

        Returns:
            True if player is eligible, False otherwise
        """
        try:
            # Get badge by name
            badge = self.db.query(Badge).filter(
                and_(Badge.name == badge_name, Badge.is_active == True)
            ).first()

            if not badge:
                logger.warning(f"Badge '{badge_name}' not found or inactive")
                return False

            # Check if already earned
            already_earned = self.db.query(PlayerBadgeEarned).filter(
                and_(
                    PlayerBadgeEarned.player_profile_id == player_profile_id,
                    PlayerBadgeEarned.badge_id == badge.id
                )
            ).first()

            if already_earned:
                return False

            # Check supply limit
            if badge.max_supply and badge.current_supply >= badge.max_supply:
                return False

            # For progression badges, check progress
            if badge.trigger_type in ['career_milestone', 'progression']:
                progress = self.calculate_badge_progress(player_profile_id, badge_name)
                return progress.get('progress_percentage', 0) >= 100

            # For other badge types, return True (actual eligibility determined by BadgeEngine)
            return True

        except Exception as e:
            logger.error(f"Error checking badge eligibility for player {player_profile_id}: {e}")
            raise

    def calculate_badge_progress(
        self,
        player_profile_id: int,
        badge_name: str
    ) -> Dict[str, Any]:
        """
        Calculate progress toward earning a badge.

        Args:
            player_profile_id: ID of the player
            badge_name: Name of the badge

        Returns:
            Dict containing progress information (current, target, percentage, requirements)
        """
        try:
            # Get badge by name
            badge = self.db.query(Badge).filter(
                and_(Badge.name == badge_name, Badge.is_active == True)
            ).first()

            if not badge:
                return {
                    "badge_name": badge_name,
                    "error": "Badge not found or inactive"
                }

            # Check if already earned
            already_earned = self.db.query(PlayerBadgeEarned).filter(
                and_(
                    PlayerBadgeEarned.player_profile_id == player_profile_id,
                    PlayerBadgeEarned.badge_id == badge.id
                )
            ).first()

            if already_earned:
                return {
                    "badge_id": badge.id,
                    "badge_name": badge.name,
                    "earned": True,
                    "earned_at": already_earned.earned_at,
                    "progress_percentage": 100.0
                }

            # Get or create progress record
            progress = self.badge_engine._get_or_create_progress(
                player_profile_id=player_profile_id,
                badge_id=badge.id
            )

            # Build response
            result = {
                "badge_id": badge.id,
                "badge_name": badge.name,
                "description": badge.description,
                "category": badge.category,
                "rarity": badge.rarity,
                "earned": False,
                "current_progress": progress.current_progress,
                "target_progress": progress.target_progress,
                "progress_percentage": progress.progress_percentage,
                "requirements": badge.trigger_condition or {},
                "trigger_type": badge.trigger_type
            }

            logger.info(
                f"Player {player_profile_id} progress on '{badge_name}': "
                f"{progress.current_progress}/{progress.target_progress} "
                f"({progress.progress_percentage:.1f}%)"
            )

            return result

        except Exception as e:
            logger.error(f"Error calculating badge progress for player {player_profile_id}: {e}")
            raise

    # ====================================================================================
    # LEGACY PLAYERACHIEVEMENT METHODS (Backward Compatibility)
    # ====================================================================================

    def get_player_achievements(self, player_profile_id: int) -> List[Dict[str, Any]]:
        """
        Get PlayerAchievement records for a player (legacy system).

        Args:
            player_profile_id: ID of the player

        Returns:
            List of dicts containing achievement information
        """
        try:
            achievements = self.db.query(PlayerAchievement).filter(
                PlayerAchievement.player_profile_id == player_profile_id
            ).order_by(desc(PlayerAchievement.earned_date)).all()

            achievements_list = []
            for achievement in achievements:
                achievements_list.append({
                    "id": achievement.id,
                    "achievement_type": achievement.achievement_type,
                    "achievement_name": achievement.achievement_name,
                    "description": achievement.description,
                    "earned_date": achievement.earned_date,
                    "game_record_id": achievement.game_record_id,
                    "achievement_data": achievement.achievement_data
                })

            logger.info(
                f"Retrieved {len(achievements_list)} legacy achievements "
                f"for player {player_profile_id}"
            )
            return achievements_list

        except Exception as e:
            logger.error(
                f"Error getting legacy achievements for player {player_profile_id}: {e}"
            )
            raise

    def create_achievement(
        self,
        player_profile_id: int,
        achievement_type: str,
        description: str,
        achievement_name: Optional[str] = None,
        game_record_id: Optional[int] = None,
        achievement_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new PlayerAchievement record (legacy system).

        Args:
            player_profile_id: ID of the player
            achievement_type: Type/category of achievement
            description: Achievement description
            achievement_name: Optional name for the achievement
            game_record_id: Optional ID of game where achievement was earned
            achievement_data: Optional additional data

        Returns:
            Dict containing the created achievement information
        """
        try:
            achievement = PlayerAchievement(
                player_profile_id=player_profile_id,
                achievement_type=achievement_type,
                achievement_name=achievement_name or achievement_type.replace('_', ' ').title(),
                description=description,
                earned_date=datetime.now().isoformat(),
                game_record_id=game_record_id,
                achievement_data=achievement_data or {}
            )

            self.db.add(achievement)
            self.db.commit()
            self.db.refresh(achievement)

            logger.info(
                f"Created legacy achievement '{achievement_type}' "
                f"for player {player_profile_id}"
            )

            return {
                "id": achievement.id,
                "achievement_type": achievement.achievement_type,
                "achievement_name": achievement.achievement_name,
                "description": achievement.description,
                "earned_date": achievement.earned_date,
                "game_record_id": achievement.game_record_id,
                "achievement_data": achievement.achievement_data
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error creating legacy achievement for player {player_profile_id}: {e}"
            )
            raise

    # ====================================================================================
    # MIGRATION METHODS
    # ====================================================================================

    def sync_achievements_to_badges(self, player_profile_id: int) -> int:
        """
        Migrate PlayerAchievement records to the Badge system.

        This method maps legacy PlayerAchievement records to corresponding Badge records
        and awards badges that match the achievement types.

        Args:
            player_profile_id: ID of the player to migrate

        Returns:
            Number of achievements successfully migrated to badges
        """
        try:
            # Get all achievements for this player
            achievements = self.db.query(PlayerAchievement).filter(
                PlayerAchievement.player_profile_id == player_profile_id
            ).all()

            if not achievements:
                logger.info(f"No legacy achievements found for player {player_profile_id}")
                return 0

            migrated_count = 0

            # Define mapping from achievement_type to badge_name
            achievement_to_badge_map = {
                'first_win': 'Lone Wolf',
                'big_earner': 'The Gambler',
                'partnership_master': 'Dynamic Duo',
                'solo_warrior': 'Wolf Pack Leader',
                'betting_expert': 'High Roller',
                'veteran': 'Veteran',
                'consistent_winner': 'Pestilence'
            }

            for achievement in achievements:
                # Check if there's a corresponding badge
                badge_name = achievement_to_badge_map.get(achievement.achievement_type)

                if not badge_name:
                    logger.debug(
                        f"No badge mapping for achievement type '{achievement.achievement_type}'"
                    )
                    continue

                # Try to award the badge
                result = self.award_badge(
                    player_profile_id=player_profile_id,
                    badge_name=badge_name,
                    game_record_id=achievement.game_record_id
                )

                if result:
                    migrated_count += 1
                    logger.info(
                        f"Migrated achievement '{achievement.achievement_type}' "
                        f"to badge '{badge_name}' for player {player_profile_id}"
                    )

            logger.info(
                f"Migration complete: {migrated_count}/{len(achievements)} "
                f"achievements migrated to badges for player {player_profile_id}"
            )

            return migrated_count

        except Exception as e:
            logger.error(
                f"Error migrating achievements to badges for player {player_profile_id}: {e}"
            )
            raise


# ====================================================================================
# SINGLETON PATTERN
# ====================================================================================

_achievement_service_instance = None


def get_achievement_service(db: Session) -> AchievementService:
    """
    Get or create the singleton AchievementService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        AchievementService instance
    """
    global _achievement_service_instance

    if _achievement_service_instance is None:
        _achievement_service_instance = AchievementService(db)
        logger.info("Created new AchievementService singleton instance")
    else:
        # Update the database session for the existing instance
        _achievement_service_instance.db = db
        _achievement_service_instance.badge_engine.db = db

    return _achievement_service_instance
