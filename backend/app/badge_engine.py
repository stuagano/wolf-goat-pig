"""
Badge Achievement Engine for Wolf Goat Pig
Detects when players earn badges and manages badge awarding logic.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union, cast

from sqlalchemy import and_
from sqlalchemy.orm import Session

from .models import (
    Badge,
    BadgeProgress,
    BadgeSeries,
    GamePlayerResult,
    GameRecord,
    PlayerBadgeEarned,
    PlayerSeriesProgress,
    PlayerStatistics,
)


class BadgeEngine:
    """Main engine for detecting and awarding badges"""

    def __init__(self, db: Session):
        self.db = db
        self.badge_checkers = self._initialize_badge_checkers()

    def _initialize_badge_checkers(self) -> Dict[str, Callable[..., Any]]:
        """Map badge trigger types to their checker functions"""
        return {
            # Achievement Badges - One-time unlocks
            'first_solo_win': self._check_first_solo_win,
            'triple_solo_streak': self._check_triple_solo_streak,
            'career_solo_50': self._check_career_solo_50,
            'solo_all_18': self._check_solo_all_18,

            # Partnership Excellence
            'first_partnership': self._check_first_partnership,
            'perfect_partnership_rate': self._check_perfect_partnership_rate,
            'partnership_streak_20': self._check_partnership_streak_20,

            # Betting Brilliance
            'high_roller': self._check_high_roller,
            'win_redoubled': self._check_win_redoubled,
            'big_earner_100': self._check_big_earner_100,
            'karl_marx_50': self._check_karl_marx_50,

            # Rare Events
            'hole_in_one': self._check_hole_in_one,
            'perfect_game': self._check_perfect_game,
            'comeback_20': self._check_comeback_20,

            # Progression Badges - Career milestones
            'earnings_milestone': self._check_earnings_milestone,
            'games_played_milestone': self._check_games_played_milestone,
            'holes_won_milestone': self._check_holes_won_milestone,
            'win_rate_badge': self._check_win_rate_badge,

            # Series Badges
            'four_horsemen_war': self._check_four_horsemen_war,
            'four_horsemen_famine': self._check_four_horsemen_famine,
            'four_horsemen_pestilence': self._check_four_horsemen_pestilence,
            'four_horsemen_death': self._check_four_horsemen_death,
        }

    # ====================================================================================
    # MAIN ENTRY POINTS
    # ====================================================================================

    def check_post_game_achievements(self, game_record_id: int, player_profile_id: int) -> List[PlayerBadgeEarned]:
        """
        Check all possible badge achievements after a game completes.
        Returns list of newly earned badges.
        """
        earned_badges: List[PlayerBadgeEarned] = []

        # Get game data
        game_record = self.db.query(GameRecord).filter_by(id=game_record_id).first()
        if not game_record:
            return earned_badges

        player_result = self.db.query(GamePlayerResult).filter(
            and_(
                GamePlayerResult.game_record_id == game_record_id,
                GamePlayerResult.player_profile_id == player_profile_id
            )
        ).first()

        if not player_result:
            return earned_badges

        # Get player statistics
        player_stats = self.db.query(PlayerStatistics).filter_by(
            player_id=player_profile_id
        ).first()

        if not player_stats:
            return earned_badges

        # Get all active badges
        active_badges = self.db.query(Badge).filter_by(is_active=True).all()

        # Check each badge
        for badge in active_badges:
            # Skip if player already has this badge (for one-time achievements)
            if badge.trigger_type == 'one_time' and self._player_has_badge(player_profile_id, int(badge.id)):
                continue

            # Check if badge trigger condition is in our checkers
            trigger = badge.trigger_condition.get('type') if badge.trigger_condition else None
            if trigger and trigger in self.badge_checkers:
                checker_func = self.badge_checkers[trigger]

                # Run the checker
                if checker_func(player_profile_id, player_stats, player_result, game_record, badge):
                    # Award the badge
                    earned_badge = self._award_badge(
                        player_profile_id=player_profile_id,
                        badge_id=int(badge.id),
                        game_record_id=game_record_id
                    )
                    if earned_badge:
                        earned_badges.append(earned_badge)

                        # Check if this completes a series
                        self._check_series_completion(player_profile_id, badge)

        # Update badge progress for progression badges
        self._update_progression_badges(player_profile_id, player_stats)

        return earned_badges

    def check_real_time_achievement(self, player_profile_id: int, event_type: str, event_data: Dict[str, Any]) -> Optional[PlayerBadgeEarned]:
        """
        Check for badges earned during gameplay (real-time).
        Example: Hole-in-one badge awarded immediately when it happens.
        """
        # Get badges that match this event type
        badges = self.db.query(Badge).filter(
            and_(
                Badge.is_active == True,
                Badge.trigger_condition.contains({'event': event_type})
            )
        ).all()

        for badge in badges:
            if self._player_has_badge(player_profile_id, int(badge.id)):
                continue

            # Check specific event criteria
            trigger_cond: Dict[Any, Any] = badge.trigger_condition if isinstance(badge.trigger_condition, dict) else {}
            if self._check_event_criteria(trigger_cond, event_data):
                return self._award_badge(
                    player_profile_id=player_profile_id,
                    badge_id=int(badge.id),
                    game_record_id=event_data.get('game_record_id')
                )

        return None

    # ====================================================================================
    # ACHIEVEMENT CHECKERS - One-Time Badges
    # ====================================================================================

    def _check_first_solo_win(self, player_id: int, stats: PlayerStatistics,
                             result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Lone Wolf - Win your first solo hole"""
        return bool(stats.solo_wins >= 1)

    def _check_triple_solo_streak(self, player_id: int, stats: PlayerStatistics,
                                  result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Alpha Predator - Win 3 consecutive solo holes in one game"""
        if result.solo_wins < 3:
            return False

        # Check betting history for consecutive solo wins
        betting_history: List[Any] = result.betting_history if isinstance(result.betting_history, list) else []
        consecutive_solo_wins = 0
        max_streak = 0

        for hole in betting_history:
            if hole.get('went_solo') and hole.get('won'):
                consecutive_solo_wins += 1
                max_streak = max(max_streak, consecutive_solo_wins)
            else:
                consecutive_solo_wins = 0

        return max_streak >= 3

    def _check_career_solo_50(self, player_id: int, stats: PlayerStatistics,
                             result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Wolf Pack Leader - Win 50 solo holes (career)"""
        return bool(stats.solo_wins >= 50)

    def _check_solo_all_18(self, player_id: int, stats: PlayerStatistics,
                          result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Apex Lone Wolf - Win a game going solo on every hole"""
        if result.solo_attempts < 18:
            return False

        betting_history: List[Any] = result.betting_history if isinstance(result.betting_history, list) else []

        # Check if all holes were solo and all won
        solo_count = 0
        solo_wins = 0

        for hole in betting_history:
            if hole.get('went_solo'):
                solo_count += 1
                if hole.get('won'):
                    solo_wins += 1

        return solo_count == 18 and solo_wins == 18

    def _check_first_partnership(self, player_id: int, stats: PlayerStatistics,
                                result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Dynamic Duo - Win 5 partnership holes with same partner"""
        # This would need more complex tracking - simplified here
        return bool(stats.partnerships_won >= 5)

    def _check_perfect_partnership_rate(self, player_id: int, stats: PlayerStatistics,
                                       result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Perfect Partnership - 100% partnership success rate (min 10 holes)"""
        if stats.partnerships_formed < 10:
            return False
        return bool(stats.partnership_success_rate >= 1.0)

    def _check_partnership_streak_20(self, player_id: int, stats: PlayerStatistics,
                                    result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: The Whisperer - Get partnership accepted 20 times consecutively"""
        # Would need additional tracking in progress_data
        return False  # Placeholder - needs implementation

    def _check_high_roller(self, player_id: int, stats: PlayerStatistics,
                          result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: High Roller - Accept 5 doubles in a single game"""
        betting_history: List[Any] = result.betting_history if isinstance(result.betting_history, list) else []
        doubles_accepted: int = sum(1 for h in betting_history if h.get('accepted_double'))
        return doubles_accepted >= 5

    def _check_win_redoubled(self, player_id: int, stats: PlayerStatistics,
                           result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Pressure Player - Win a redoubled hole (4x+ wager)"""
        betting_history: List[Any] = result.betting_history if isinstance(result.betting_history, list) else []
        for hole in betting_history:
            if hole.get('won') and hole.get('wager_multiplier', 1) >= 4:
                return True
        return False

    def _check_big_earner_100(self, player_id: int, stats: PlayerStatistics,
                            result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: The Gambler - Win 100 quarters in a single game"""
        return bool(result.total_earnings >= 100)

    def _check_karl_marx_50(self, player_id: int, stats: PlayerStatistics,
                          result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Karl Marx's Favorite - Receive 50 quarters via Karl Marx rule (career)"""
        # Would need specific tracking in progress_data
        progress = self._get_or_create_progress(player_id, int(badge.id))
        return bool(progress.current_progress >= 50)

    def _check_hole_in_one(self, player_id: int, stats: PlayerStatistics,
                         result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Unicorn - Make a hole-in-one"""
        hole_scores: Dict[str, Any] = result.hole_scores if isinstance(result.hole_scores, dict) else {}
        for hole_num, score_data in hole_scores.items():
            if score_data.get('score') == 1:
                return True
        return False

    def _check_perfect_game(self, player_id: int, stats: PlayerStatistics,
                          result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Perfect Game - Win every hole in a game"""
        return bool(result.holes_won >= 18)

    def _check_comeback_20(self, player_id: int, stats: PlayerStatistics,
                         result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Lazarus - Come back from 20+ quarters down to win"""
        performance_metrics: Dict[str, Any] = result.performance_metrics if isinstance(result.performance_metrics, dict) else {}
        max_deficit = performance_metrics.get('max_deficit', 0)
        return bool(max_deficit >= 20 and result.final_position == 1)

    # ====================================================================================
    # PROGRESSION BADGES - Career Milestones
    # ====================================================================================

    def _check_earnings_milestone(self, player_id: int, stats: PlayerStatistics,
                                 result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Check career earnings milestones (Bronze: 100, Silver: 500, Gold: 2000, etc.)"""
        threshold = badge.trigger_condition.get('earnings_threshold', 0)
        return bool(stats.total_earnings >= threshold)

    def _check_games_played_milestone(self, player_id: int, stats: PlayerStatistics,
                                     result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Check games played milestones"""
        threshold = badge.trigger_condition.get('games_threshold', 0)
        return bool(stats.games_played >= threshold)

    def _check_holes_won_milestone(self, player_id: int, stats: PlayerStatistics,
                                  result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Check holes won milestones"""
        threshold = badge.trigger_condition.get('holes_threshold', 0)
        return bool(stats.holes_won >= threshold)

    def _check_win_rate_badge(self, player_id: int, stats: PlayerStatistics,
                            result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Check win rate badges (requires minimum 100 holes played)"""
        if stats.holes_played < 100:
            return False

        win_rate_threshold = badge.trigger_condition.get('win_rate', 0)
        actual_win_rate = stats.holes_won / stats.holes_played if stats.holes_played > 0 else 0
        return bool(actual_win_rate >= win_rate_threshold)

    # ====================================================================================
    # SERIES BADGES - Four Horsemen
    # ====================================================================================

    def _check_four_horsemen_war(self, player_id: int, stats: PlayerStatistics,
                                result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: War - Win 10 redoubled holes (career)"""
        # Need to track redoubled wins in progress
        progress = self._get_or_create_progress(player_id, int(badge.id))

        # Check current game for redoubled wins
        betting_history: List[Any] = result.betting_history if isinstance(result.betting_history, list) else []
        redoubled_wins_this_game: int = sum(
            1 for h in betting_history
            if h.get('won') and h.get('wager_multiplier', 1) >= 4
        )

        setattr(progress, 'current_progress', int(progress.current_progress) + redoubled_wins_this_game)
        setattr(progress, 'target_progress', 10)
        setattr(progress, 'progress_percentage', float((int(progress.current_progress) / 10) * 100))
        setattr(progress, 'updated_at', datetime.now(timezone.utc).isoformat())
        self.db.commit()

        return bool(int(progress.current_progress) >= 10)

    def _check_four_horsemen_famine(self, player_id: int, stats: PlayerStatistics,
                                   result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Famine - Bankrupt opponent (reduce to -50 quarters)"""
        # Check if any opponent reached -50 quarters in this game
        final_scores: Dict[str, Any] = game.final_scores if isinstance(game.final_scores, dict) else {}
        for player_name, score_data in final_scores.items():
            if score_data.get('earnings', 0) <= -50:
                return True
        return False

    def _check_four_horsemen_pestilence(self, player_id: int, stats: PlayerStatistics,
                                       result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Pestilence - Win 5 games in a row"""
        # Query last 5 games for this player
        recent_games = self.db.query(GamePlayerResult).filter(
            GamePlayerResult.player_profile_id == player_id
        ).order_by(GamePlayerResult.created_at.desc()).limit(5).all()

        if len(recent_games) < 5:
            return False

        # Check if all 5 were wins (final_position == 1)
        return all(g.final_position == 1 for g in recent_games)

    def _check_four_horsemen_death(self, player_id: int, stats: PlayerStatistics,
                                  result: GamePlayerResult, game: GameRecord, badge: Badge) -> bool:
        """Badge: Death - Eliminate all 3 opponents in solo mode"""
        # Check if player went solo and all opponents have negative earnings
        if result.solo_attempts < 18:
            return False

        final_scores: Dict[str, Any] = game.final_scores if isinstance(game.final_scores, dict) else {}
        opponents = [s for name, s in final_scores.items()
                    if s.get('player_id') != player_id]

        return all(opp.get('earnings', 0) < 0 for opp in opponents) if len(opponents) == 3 else False

    # ====================================================================================
    # HELPER METHODS
    # ====================================================================================

    def _award_badge(self, player_profile_id: int, badge_id: int,
                    game_record_id: Optional[int] = None) -> Optional[PlayerBadgeEarned]:
        """Award a badge to a player"""
        badge = self.db.query(Badge).filter_by(id=badge_id).first()
        if not badge:
            return None

        # Check supply limit
        if badge.max_supply and badge.current_supply >= badge.max_supply:
            return None

        # Create badge earned record
        serial_number = badge.current_supply + 1

        earned = PlayerBadgeEarned(
            player_profile_id=player_profile_id,
            badge_id=badge_id,
            earned_at=datetime.now(timezone.utc).isoformat(),
            game_record_id=game_record_id,
            serial_number=serial_number,
            is_minted=False,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # Update badge supply
        setattr(badge, 'current_supply', int(badge.current_supply) + 1)
        setattr(badge, 'updated_at', datetime.now(timezone.utc).isoformat())

        self.db.add(earned)
        self.db.commit()
        self.db.refresh(earned)

        return earned

    def _player_has_badge(self, player_profile_id: int, badge_id: int) -> bool:
        """Check if player already has this badge"""
        count = self.db.query(PlayerBadgeEarned).filter(
            and_(
                PlayerBadgeEarned.player_profile_id == player_profile_id,
                PlayerBadgeEarned.badge_id == badge_id
            )
        ).count()
        return bool(count > 0)

    def _get_or_create_progress(self, player_profile_id: int, badge_id: int) -> BadgeProgress:
        """Get or create badge progress tracking"""
        progress = self.db.query(BadgeProgress).filter(
            and_(
                BadgeProgress.player_profile_id == player_profile_id,
                BadgeProgress.badge_id == badge_id
            )
        ).first()

        if not progress:
            badge = self.db.query(Badge).filter_by(id=badge_id).first()
            target = badge.trigger_condition.get('target', 0) if badge and badge.trigger_condition else 0

            progress = BadgeProgress(
                player_profile_id=player_profile_id,
                badge_id=badge_id,
                current_progress=0,
                target_progress=target,
                progress_percentage=0.0,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat()
            )
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)

        return progress

    def _update_progression_badges(self, player_profile_id: int, stats: PlayerStatistics) -> None:
        """Update progress for all progression badges"""
        progression_badges = self.db.query(Badge).filter(
            and_(
                Badge.trigger_type == 'career_milestone',
                Badge.is_active == True
            )
        ).all()

        for badge in progression_badges:
            if self._player_has_badge(player_profile_id, int(badge.id)):
                continue

            progress = self._get_or_create_progress(player_profile_id, int(badge.id))

            # Update progress based on badge type
            trigger = badge.trigger_condition.get('type') if badge.trigger_condition else None

            if trigger == 'earnings_milestone':
                setattr(progress, 'current_progress', int(float(stats.total_earnings)))
                setattr(progress, 'target_progress', badge.trigger_condition.get('earnings_threshold', 0))
            elif trigger == 'games_played_milestone':
                setattr(progress, 'current_progress', int(stats.games_played))
                setattr(progress, 'target_progress', badge.trigger_condition.get('games_threshold', 0))
            elif trigger == 'holes_won_milestone':
                setattr(progress, 'current_progress', int(stats.holes_won))
                setattr(progress, 'target_progress', badge.trigger_condition.get('holes_threshold', 0))

            if int(progress.target_progress) > 0:
                setattr(progress, 'progress_percentage', float(min(
                    (int(progress.current_progress) / int(progress.target_progress)) * 100,
                    100.0
                )))

            setattr(progress, 'updated_at', datetime.now(timezone.utc).isoformat())
            self.db.commit()

    def _check_series_completion(self, player_profile_id: int, newly_earned_badge: Badge) -> None:
        """Check if earning this badge completes a series"""
        if not newly_earned_badge.series_id:
            return

        series = self.db.query(BadgeSeries).filter_by(id=newly_earned_badge.series_id).first()
        if not series:
            return

        # Get all badges in this series
        series_badges = self.db.query(Badge).filter_by(series_id=series.id).all()
        series_badge_ids = [b.id for b in series_badges]

        # Count how many the player has earned
        earned_count = self.db.query(PlayerBadgeEarned).filter(
            and_(
                PlayerBadgeEarned.player_profile_id == player_profile_id,
                PlayerBadgeEarned.badge_id.in_(series_badge_ids)
            )
        ).count()

        # Update series progress
        series_progress = self.db.query(PlayerSeriesProgress).filter(
            and_(
                PlayerSeriesProgress.player_profile_id == player_profile_id,
                PlayerSeriesProgress.series_id == series.id
            )
        ).first()

        if not series_progress:
            series_progress = PlayerSeriesProgress(
                player_profile_id=player_profile_id,
                series_id=int(series.id),
                badges_earned=earned_count,
                badges_needed=int(series.badge_count),
                is_completed=False,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat()
            )
            self.db.add(series_progress)
        else:
            setattr(series_progress, 'badges_earned', earned_count)
            setattr(series_progress, 'updated_at', datetime.now(timezone.utc).isoformat())

        # Check if series is complete
        if earned_count >= int(series.badge_count) and not series_progress.is_completed:
            setattr(series_progress, 'is_completed', True)
            setattr(series_progress, 'completed_at', datetime.now(timezone.utc).isoformat())

            # Award completion badge if one exists
            if series.completion_badge_id:
                self._award_badge(
                    player_profile_id=player_profile_id,
                    badge_id=int(series.completion_badge_id)
                )

        self.db.commit()

    def _check_event_criteria(self, trigger_condition: Dict, event_data: Dict) -> bool:
        """Check if event data meets badge criteria"""
        # Implement specific event matching logic
        return True  # Placeholder
