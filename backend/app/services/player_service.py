"""
Player Profile Management Service

This service handles all player profile operations including:
- Profile creation, retrieval, update, and deletion
- Profile statistics management
- Game result tracking
- Achievement system
- Performance analytics
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func
from datetime import datetime, timedelta
import json
import logging
from ..models import (
    PlayerProfile, PlayerStatistics, GameRecord, GamePlayerResult, 
    PlayerAchievement
)
from ..schemas import (
    PlayerProfileCreate, PlayerProfileUpdate, PlayerProfileResponse,
    PlayerStatisticsResponse, GameRecordCreate, GamePlayerResultCreate,
    PlayerPerformanceAnalytics, LeaderboardEntry
)

logger = logging.getLogger(__name__)

class PlayerService:
    """Service class for player profile management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Profile Management
    def create_player_profile(self, profile_data: PlayerProfileCreate) -> PlayerProfileResponse:
        """Create a new player profile with default statistics."""
        try:
            # Check if player name already exists
            existing_player = self.db.query(PlayerProfile).filter(
                PlayerProfile.name == profile_data.name
            ).first()
            
            if existing_player:
                raise ValueError(f"Player with name '{profile_data.name}' already exists")
            
            # Create player profile
            player_profile = PlayerProfile(
                name=profile_data.name,
                handicap=profile_data.handicap,
                avatar_url=profile_data.avatar_url,
                created_date=datetime.now().isoformat(),
                preferences=profile_data.preferences or {
                    "ai_difficulty": "medium",
                    "preferred_game_modes": ["wolf_goat_pig"],
                    "preferred_player_count": 4,
                    "betting_style": "conservative",
                    "display_hints": True
                }
            )
            
            self.db.add(player_profile)
            self.db.flush()  # Get the ID before committing
            
            # Create initial statistics record
            player_stats = PlayerStatistics(
                player_id=player_profile.id,
                last_updated=datetime.now().isoformat()
            )
            
            self.db.add(player_stats)
            self.db.commit()
            self.db.refresh(player_profile)
            
            logger.info(f"Created player profile for {profile_data.name} with ID {player_profile.id}")
            
            return PlayerProfileResponse.model_validate(player_profile)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating player profile: {e}")
            raise
    
    def get_player_profile(self, player_id: int) -> Optional[PlayerProfileResponse]:
        """Get a player profile by ID."""
        try:
            player = self.db.query(PlayerProfile).filter(
                and_(PlayerProfile.id == player_id, PlayerProfile.is_active == 1)
            ).first()
            
            if player:
                return PlayerProfileResponse.model_validate(player)
            return None
            
        except Exception as e:
            logger.error(f"Error getting player profile {player_id}: {e}")
            raise
    
    def get_player_profile_by_name(self, name: str) -> Optional[PlayerProfileResponse]:
        """Get a player profile by name."""
        try:
            player = self.db.query(PlayerProfile).filter(
                and_(PlayerProfile.name == name, PlayerProfile.is_active == 1)
            ).first()
            
            if player:
                return PlayerProfileResponse.model_validate(player)
            return None
            
        except Exception as e:
            logger.error(f"Error getting player profile by name {name}: {e}")
            raise
    
    def get_all_player_profiles(self, active_only: bool = True) -> List[PlayerProfileResponse]:
        """Get all player profiles."""
        try:
            query = self.db.query(PlayerProfile)
            if active_only:
                query = query.filter(PlayerProfile.is_active == 1)
            
            players = query.order_by(PlayerProfile.last_played.desc(), PlayerProfile.name).all()
            return [PlayerProfileResponse.model_validate(player) for player in players]
            
        except Exception as e:
            logger.error(f"Error getting all player profiles: {e}")
            raise
    
    def update_player_profile(self, player_id: int, update_data: PlayerProfileUpdate) -> Optional[PlayerProfileResponse]:
        """Update a player profile."""
        try:
            player = self.db.query(PlayerProfile).filter(
                and_(PlayerProfile.id == player_id, PlayerProfile.is_active == 1)
            ).first()
            
            if not player:
                return None
            
            # Update fields that are provided
            if update_data.name is not None:
                # Check for name conflicts (excluding current player)
                existing_player = self.db.query(PlayerProfile).filter(
                    and_(PlayerProfile.name == update_data.name, PlayerProfile.id != player_id)
                ).first()
                if existing_player:
                    raise ValueError(f"Player with name '{update_data.name}' already exists")
                player.name = update_data.name
                
            if update_data.handicap is not None:
                player.handicap = update_data.handicap
                
            if update_data.avatar_url is not None:
                player.avatar_url = update_data.avatar_url
                
            if update_data.preferences is not None:
                player.preferences = update_data.preferences
                
            if update_data.last_played is not None:
                player.last_played = update_data.last_played
            
            self.db.commit()
            self.db.refresh(player)
            
            logger.info(f"Updated player profile {player_id}")
            return PlayerProfileResponse.model_validate(player)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating player profile {player_id}: {e}")
            raise
    
    def delete_player_profile(self, player_id: int) -> bool:
        """Soft delete a player profile (mark as inactive)."""
        try:
            player = self.db.query(PlayerProfile).filter(PlayerProfile.id == player_id).first()
            if not player:
                return False
            
            player.is_active = 0
            self.db.commit()
            
            logger.info(f"Deleted (deactivated) player profile {player_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting player profile {player_id}: {e}")
            raise
    
    # Statistics Management
    def get_player_statistics(self, player_id: int) -> Optional[PlayerStatisticsResponse]:
        """Get player statistics."""
        try:
            stats = self.db.query(PlayerStatistics).filter(
                PlayerStatistics.player_id == player_id
            ).first()
            
            if stats:
                return PlayerStatisticsResponse.model_validate(stats)
            return None
            
        except Exception as e:
            logger.error(f"Error getting player statistics {player_id}: {e}")
            raise
    
    def update_last_played(self, player_id: int) -> None:
        """Update the last played timestamp for a player."""
        try:
            player = self.db.query(PlayerProfile).filter(PlayerProfile.id == player_id).first()
            if player:
                player.last_played = datetime.now().isoformat()
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Error updating last played for player {player_id}: {e}")
            raise
    
    # Game Results and Statistics Updates
    def record_game_result(self, game_result: GamePlayerResultCreate) -> bool:
        """Record a game result and update player statistics."""
        try:
            # Create game player result record
            result_record = GamePlayerResult(**game_result.model_dump())
            result_record.created_at = datetime.now().isoformat()
            self.db.add(result_record)
            
            # Update player statistics
            self._update_player_statistics_from_game(game_result)
            
            # Update last played
            self.update_last_played(game_result.player_profile_id)
            
            self.db.commit()
            logger.info(f"Recorded game result for player {game_result.player_profile_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording game result: {e}")
            raise
    
    def _update_player_statistics_from_game(self, game_result: GamePlayerResultCreate) -> None:
        """Update player statistics based on a completed game."""
        stats = self.db.query(PlayerStatistics).filter(
            PlayerStatistics.player_id == game_result.player_profile_id
        ).first()
        
        if not stats:
            # Create new statistics record if none exists
            stats = PlayerStatistics(player_id=game_result.player_profile_id)
            self.db.add(stats)
            self.db.flush()
        
        # Update game counts
        stats.games_played += 1
        if game_result.final_position == 1:
            stats.games_won += 1
        
        # Update earnings
        stats.total_earnings += game_result.total_earnings
        stats.holes_played += len(game_result.hole_scores or {})
        stats.holes_won += game_result.holes_won
        
        # Calculate average earnings per hole
        if stats.holes_played > 0:
            stats.avg_earnings_per_hole = stats.total_earnings / stats.holes_played
        
        # Update betting statistics
        stats.successful_bets += game_result.successful_bets
        stats.total_bets += game_result.total_bets
        if stats.total_bets > 0:
            stats.betting_success_rate = stats.successful_bets / stats.total_bets
        
        # Update partnership statistics
        stats.partnerships_formed += game_result.partnerships_formed
        stats.partnerships_won += game_result.partnerships_won
        if stats.partnerships_formed > 0:
            stats.partnership_success_rate = stats.partnerships_won / stats.partnerships_formed
        
        # Update solo statistics
        stats.solo_attempts += game_result.solo_attempts
        stats.solo_wins += game_result.solo_wins
        
        # Update performance trends
        performance_point = {
            "game_date": datetime.now().isoformat(),
            "earnings": game_result.total_earnings,
            "position": game_result.final_position,
            "holes_won": game_result.holes_won,
            "betting_success": game_result.successful_bets / max(1, game_result.total_bets)
        }
        
        trends = stats.performance_trends or []
        trends.append(performance_point)
        
        # Keep only last 50 games for performance
        if len(trends) > 50:
            trends = trends[-50:]
        
        stats.performance_trends = trends
        stats.last_updated = datetime.now().isoformat()
    
    # Analytics and Insights
    def get_player_performance_analytics(self, player_id: int) -> Optional[PlayerPerformanceAnalytics]:
        """Get comprehensive performance analytics for a player."""
        try:
            profile = self.get_player_profile(player_id)
            stats = self.get_player_statistics(player_id)
            
            if not profile or not stats:
                return None
            
            # Calculate performance summary
            win_rate = (stats.games_won / max(1, stats.games_played)) * 100
            avg_position = self._calculate_average_position(player_id)
            recent_form = self._calculate_recent_form(player_id)
            
            performance_summary = {
                "games_played": stats.games_played,
                "win_rate": round(win_rate, 1),
                "avg_earnings": round(stats.avg_earnings_per_hole, 2),
                "total_earnings": round(stats.total_earnings, 2),
                "avg_position": round(avg_position, 2),
                "recent_form": recent_form
            }
            
            # Trend analysis
            trend_analysis = self._analyze_performance_trends(stats.performance_trends or [])
            
            # Strength analysis
            strength_analysis = {
                "betting": "Strong" if stats.betting_success_rate > 0.6 else "Weak" if stats.betting_success_rate < 0.4 else "Average",
                "partnerships": "Strong" if stats.partnership_success_rate > 0.6 else "Weak" if stats.partnership_success_rate < 0.4 else "Average",
                "solo_play": "Strong" if (stats.solo_wins / max(1, stats.solo_attempts)) > 0.3 else "Risky",
                "consistency": self._calculate_consistency_rating(stats.performance_trends or [])
            }
            
            # Improvement recommendations
            recommendations = self._generate_improvement_recommendations(stats)
            
            # Comparative analysis (vs other players)
            comparative_analysis = self._get_comparative_analysis(player_id, stats)
            
            return PlayerPerformanceAnalytics(
                player_id=player_id,
                player_name=profile.name,
                performance_summary=performance_summary,
                trend_analysis=trend_analysis,
                strength_analysis=strength_analysis,
                improvement_recommendations=recommendations,
                comparative_analysis=comparative_analysis
            )
            
        except Exception as e:
            logger.error(f"Error getting performance analytics for player {player_id}: {e}")
            raise
    
    def get_leaderboard(self, limit: int = 10) -> List[LeaderboardEntry]:
        """Get the player leaderboard."""
        try:
            # Query for active players with statistics (removed games_played filter to show all players)
            query = self.db.query(PlayerProfile, PlayerStatistics).join(
                PlayerStatistics, PlayerProfile.id == PlayerStatistics.player_id
            ).filter(
                PlayerProfile.is_active == 1  # Only filter for active players, show everyone regardless of games played
            ).order_by(desc(PlayerStatistics.total_earnings))
            
            players_with_stats = query.limit(limit).all()
            
            leaderboard = []
            for rank, (profile, stats) in enumerate(players_with_stats, 1):
                win_percentage = (stats.games_won / max(1, stats.games_played)) * 100
                avg_earnings = stats.avg_earnings_per_hole
                
                leaderboard.append(LeaderboardEntry(
                    rank=rank,
                    player_name=profile.name,
                    games_played=stats.games_played,
                    win_percentage=round(win_percentage, 1),
                    avg_earnings=round(avg_earnings, 2),
                    total_earnings=round(stats.total_earnings, 2),
                    partnership_success=round(stats.partnership_success_rate * 100, 1)
                ))
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            raise
    
    # Helper methods for analytics
    def _calculate_average_position(self, player_id: int) -> float:
        """Calculate average finishing position for a player."""
        results = self.db.query(GamePlayerResult.final_position).filter(
            GamePlayerResult.player_profile_id == player_id
        ).all()
        
        if not results:
            return 0.0
        
        positions = [result.final_position for result in results]
        return sum(positions) / len(positions)
    
    def _calculate_recent_form(self, player_id: int, games: int = 5) -> str:
        """Calculate recent form based on last N games."""
        results = self.db.query(GamePlayerResult.final_position).filter(
            GamePlayerResult.player_profile_id == player_id
        ).order_by(desc(GamePlayerResult.created_at)).limit(games).all()
        
        if not results:
            return "No recent games"
        
        positions = [result.final_position for result in results]
        avg_position = sum(positions) / len(positions)
        
        if avg_position <= 1.5:
            return "Excellent"
        elif avg_position <= 2.0:
            return "Good"
        elif avg_position <= 2.5:
            return "Average"
        else:
            return "Poor"
    
    def _analyze_performance_trends(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if not trends or len(trends) < 3:
            return {"status": "insufficient_data"}
        
        recent_trends = trends[-10:] if len(trends) >= 10 else trends
        
        # Calculate trend direction for earnings
        earnings = [t["earnings"] for t in recent_trends]
        earnings_trend = "improving" if earnings[-1] > earnings[0] else "declining"
        
        # Calculate trend direction for position (lower is better)
        positions = [t["position"] for t in recent_trends]
        position_trend = "improving" if positions[-1] < positions[0] else "declining"
        
        return {
            "status": "sufficient_data",
            "earnings_trend": earnings_trend,
            "position_trend": position_trend,
            "games_analyzed": len(recent_trends),
            "volatility": self._calculate_volatility(earnings)
        }
    
    def _calculate_consistency_rating(self, trends: List[Dict[str, Any]]) -> str:
        """Calculate consistency rating based on performance variance."""
        if not trends or len(trends) < 5:
            return "Unknown"
        
        positions = [t["position"] for t in trends]
        variance = sum((p - sum(positions)/len(positions))**2 for p in positions) / len(positions)
        
        if variance < 0.5:
            return "Very Consistent"
        elif variance < 1.0:
            return "Consistent"
        elif variance < 2.0:
            return "Moderate"
        else:
            return "Inconsistent"
    
    def _calculate_volatility(self, values: List[float]) -> str:
        """Calculate volatility rating for earnings."""
        if not values or len(values) < 3:
            return "Unknown"
        
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val)**2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        if std_dev < mean_val * 0.3:
            return "Low"
        elif std_dev < mean_val * 0.6:
            return "Medium"
        else:
            return "High"
    
    def _generate_improvement_recommendations(self, stats: PlayerStatisticsResponse) -> List[str]:
        """Generate personalized improvement recommendations."""
        recommendations = []
        
        # Betting recommendations
        if stats.betting_success_rate < 0.4:
            recommendations.append("Focus on conservative betting until you improve your success rate")
        elif stats.betting_success_rate > 0.7:
            recommendations.append("You're a strong bettor - consider more aggressive strategies")
        
        # Partnership recommendations
        if stats.partnership_success_rate < 0.4 and stats.partnerships_formed > 5:
            recommendations.append("Consider being more selective when choosing partners")
        
        # Solo play recommendations
        solo_success = stats.solo_wins / max(1, stats.solo_attempts)
        if solo_success < 0.2 and stats.solo_attempts > 3:
            recommendations.append("Solo play is risky for you - focus on partnerships")
        elif solo_success > 0.4:
            recommendations.append("You excel at solo play - use it strategically")
        
        # General recommendations
        if stats.games_played < 10:
            recommendations.append("Play more games to establish reliable performance patterns")
        
        if not recommendations:
            recommendations.append("Keep up the good work! Continue refining your strategy")
        
        return recommendations
    
    def _get_comparative_analysis(self, player_id: int, stats: PlayerStatisticsResponse) -> Dict[str, Any]:
        """Get comparative analysis against other players."""
        try:
            # Get average stats for all players
            all_stats = self.db.query(PlayerStatistics).filter(
                PlayerStatistics.games_played >= 5
            ).all()
            
            if not all_stats:
                return {"status": "insufficient_data"}
            
            # Calculate percentiles
            earnings_values = sorted([s.total_earnings for s in all_stats])
            win_rates = sorted([(s.games_won / max(1, s.games_played)) for s in all_stats])
            
            player_earnings_percentile = self._calculate_percentile(stats.total_earnings, earnings_values)
            player_win_rate = stats.games_won / max(1, stats.games_played)
            player_win_rate_percentile = self._calculate_percentile(player_win_rate, win_rates)
            
            return {
                "status": "available",
                "earnings_percentile": round(player_earnings_percentile, 1),
                "win_rate_percentile": round(player_win_rate_percentile, 1),
                "players_compared": len(all_stats),
                "ranking_summary": self._get_ranking_summary(player_earnings_percentile, player_win_rate_percentile)
            }
            
        except Exception as e:
            logger.error(f"Error in comparative analysis: {e}")
            return {"status": "error"}
    
    def _calculate_percentile(self, value: float, sorted_values: List[float]) -> float:
        """Calculate percentile rank for a value in a sorted list."""
        if not sorted_values:
            return 0.0
        
        rank = sum(1 for v in sorted_values if v <= value)
        return (rank / len(sorted_values)) * 100
    
    def _get_ranking_summary(self, earnings_percentile: float, win_rate_percentile: float) -> str:
        """Generate a ranking summary based on percentiles."""
        avg_percentile = (earnings_percentile + win_rate_percentile) / 2
        
        if avg_percentile >= 90:
            return "Elite Player"
        elif avg_percentile >= 75:
            return "Strong Player"
        elif avg_percentile >= 50:
            return "Average Player"
        elif avg_percentile >= 25:
            return "Developing Player"
        else:
            return "Beginner Player"
    
    # Achievement System
    def check_and_award_achievements(self, player_id: int, game_result: GamePlayerResultCreate) -> List[str]:
        """Check for new achievements and award them."""
        try:
            awarded_achievements = []
            
            # Get current stats
            stats = self.get_player_statistics(player_id)
            if not stats:
                return awarded_achievements
            
            # Check various achievement conditions
            achievements_to_check = [
                ("first_win", "First Victory", "Won your first game", lambda: stats.games_won == 1),
                ("big_earner", "Big Earner", "Earned over 20 quarters in a single game", 
                 lambda: game_result.total_earnings >= 20),
                ("partnership_master", "Partnership Master", "Won 10 games with partners",
                 lambda: stats.partnerships_won >= 10),
                ("solo_warrior", "Solo Warrior", "Won 5 games going solo",
                 lambda: stats.solo_wins >= 5),
                ("betting_expert", "Betting Expert", "Achieved 70% betting success rate with 20+ bets",
                 lambda: stats.betting_success_rate >= 0.7 and stats.total_bets >= 20),
                ("veteran", "Veteran Player", "Played 50 games", lambda: stats.games_played >= 50),
                ("consistent_winner", "Consistent Winner", "Won 5 games in a row", 
                 lambda: self._check_win_streak(player_id, 5))
            ]
            
            for achievement_type, name, description, condition in achievements_to_check:
                # Check if already awarded
                existing = self.db.query(PlayerAchievement).filter(
                    and_(
                        PlayerAchievement.player_profile_id == player_id,
                        PlayerAchievement.achievement_type == achievement_type
                    )
                ).first()
                
                if not existing and condition():
                    # Award achievement
                    achievement = PlayerAchievement(
                        player_profile_id=player_id,
                        achievement_type=achievement_type,
                        achievement_name=name,
                        description=description,
                        earned_date=datetime.now().isoformat(),
                        achievement_data={"game_result": game_result.model_dump()}
                    )
                    
                    self.db.add(achievement)
                    awarded_achievements.append(name)
            
            if awarded_achievements:
                self.db.commit()
                logger.info(f"Awarded achievements to player {player_id}: {awarded_achievements}")
            
            return awarded_achievements
            
        except Exception as e:
            logger.error(f"Error checking achievements for player {player_id}: {e}")
            return []
    
    def _check_win_streak(self, player_id: int, streak_length: int) -> bool:
        """Check if player has a current win streak of specified length."""
        recent_results = self.db.query(GamePlayerResult.final_position).filter(
            GamePlayerResult.player_profile_id == player_id
        ).order_by(desc(GamePlayerResult.created_at)).limit(streak_length).all()
        
        if len(recent_results) < streak_length:
            return False
        
        return all(result.final_position == 1 for result in recent_results)