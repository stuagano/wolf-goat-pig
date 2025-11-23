"""
Statistics Service for Advanced Player Analytics

This service provides advanced statistical analysis and insights for player performance:
- Performance trend analysis
- Statistical modeling and predictions
- Comparative analytics
- Advanced metrics calculation
- Data visualization support
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from ..models import GamePlayerResult, GameRecord, PlayerProfile, PlayerStatistics

logger = logging.getLogger(__name__)

@dataclass
class TrendPoint:
    """Data class for trend analysis points."""
    timestamp: str
    value: float
    game_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

@dataclass
class PerformanceMetric:
    """Data class for performance metrics."""
    name: str
    value: float
    percentile: float
    trend: str  # 'improving', 'stable', 'declining'
    confidence: float
    description: str

@dataclass
class InsightRecommendation:
    """Data class for performance insights and recommendations."""
    category: str
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    data_support: Dict[str, Any]
    suggested_actions: List[str]

class StatisticsService:
    """Advanced statistics and analytics service."""

    def __init__(self, db: Session):
        self.db = db

    def get_advanced_player_metrics(self, player_id: int) -> Dict[str, PerformanceMetric]:
        """Calculate advanced performance metrics for a player."""
        try:
            # Get player data
            player_stats = self.db.query(PlayerStatistics).filter(
                PlayerStatistics.player_id == player_id
            ).first()

            if not player_stats:
                return {}

            # Get all players for comparison
            all_stats = self.db.query(PlayerStatistics).filter(
                PlayerStatistics.games_played >= 5
            ).all()

            metrics = {}

            # Win Rate Analysis
            win_rate = (player_stats.games_won / max(1, player_stats.games_played)) * 100
            win_rates = [(s.games_won / max(1, s.games_played)) * 100 for s in all_stats]
            win_rate_percentile = self._calculate_percentile(win_rate, win_rates)
            win_rate_trend = self._analyze_win_rate_trend(player_id)

            metrics["win_rate"] = PerformanceMetric(
                name="Win Rate",
                value=win_rate,
                percentile=win_rate_percentile,
                trend=win_rate_trend,
                confidence=0.8 if player_stats.games_played >= 20 else 0.5,
                description=f"You win {win_rate:.1f}% of your games"
            )

            # Earnings Efficiency
            earnings_per_game = player_stats.total_earnings / max(1, player_stats.games_played)
            all_earnings_per_game = [s.total_earnings / max(1, s.games_played) for s in all_stats]
            earnings_percentile = self._calculate_percentile(earnings_per_game, all_earnings_per_game)
            earnings_trend = self._analyze_earnings_trend(player_id)

            metrics["earnings_efficiency"] = PerformanceMetric(
                name="Earnings Efficiency",
                value=earnings_per_game,
                percentile=earnings_percentile,
                trend=earnings_trend,
                confidence=0.9 if player_stats.games_played >= 15 else 0.6,
                description=f"You earn {earnings_per_game:.2f} quarters per game on average"
            )

            # Betting Accuracy
            betting_accuracy = player_stats.betting_success_rate * 100
            all_betting_accuracy = [s.betting_success_rate * 100 for s in all_stats if s.total_bets > 0]
            betting_percentile = self._calculate_percentile(betting_accuracy, all_betting_accuracy)

            metrics["betting_accuracy"] = PerformanceMetric(
                name="Betting Accuracy",
                value=betting_accuracy,
                percentile=betting_percentile,
                trend="stable",  # Would need more detailed analysis
                confidence=0.8 if player_stats.total_bets >= 50 else 0.4,
                description=f"You make successful bets {betting_accuracy:.1f}% of the time"
            )

            # Partnership Synergy
            partnership_success = player_stats.partnership_success_rate * 100
            all_partnership_success = [s.partnership_success_rate * 100 for s in all_stats if s.partnerships_formed > 0]
            partnership_percentile = self._calculate_percentile(partnership_success, all_partnership_success)

            metrics["partnership_synergy"] = PerformanceMetric(
                name="Partnership Synergy",
                value=partnership_success,
                percentile=partnership_percentile,
                trend="stable",
                confidence=0.7 if player_stats.partnerships_formed >= 10 else 0.3,
                description=f"Your partnerships succeed {partnership_success:.1f}% of the time"
            )

            # Consistency Score (inverse of variance)
            consistency_score = self._calculate_consistency_score(player_id)
            all_consistency = [self._calculate_consistency_score(s.player_id) for s in all_stats]
            consistency_percentile = self._calculate_percentile(consistency_score, all_consistency)

            metrics["consistency"] = PerformanceMetric(
                name="Consistency",
                value=consistency_score,
                percentile=consistency_percentile,
                trend="stable",
                confidence=0.8 if player_stats.games_played >= 25 else 0.5,
                description=f"Your consistency score is {consistency_score:.1f}/100"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating advanced metrics for player {player_id}: {e}")
            return {}

    def get_performance_trends(self, player_id: int, days: int = 30) -> Dict[str, List[TrendPoint]]:
        """Get performance trends over time."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get recent game results
            results = self.db.query(GamePlayerResult).filter(
                and_(
                    GamePlayerResult.player_profile_id == player_id,
                    GamePlayerResult.created_at >= cutoff_date
                )
            ).order_by(GamePlayerResult.created_at).all()

            trends: Dict[str, List[TrendPoint]] = {
                "earnings": [],
                "position": [],
                "betting_success": [],
                "holes_won": []
            }

            for result in results:
                timestamp = result.created_at

                # Earnings trend
                trends["earnings"].append(TrendPoint(
                    timestamp=timestamp,
                    value=result.total_earnings,
                    game_id=str(result.game_record_id),
                    context={"position": result.final_position}
                ))

                # Position trend (inverted for better visualization)
                trends["position"].append(TrendPoint(
                    timestamp=timestamp,
                    value=5 - result.final_position,  # Invert so higher is better
                    game_id=str(result.game_record_id),
                    context={"actual_position": result.final_position}
                ))

                # Betting success trend
                betting_rate = result.successful_bets / max(1, result.total_bets)
                trends["betting_success"].append(TrendPoint(
                    timestamp=timestamp,
                    value=betting_rate * 100,
                    game_id=str(result.game_record_id),
                    context={"successful_bets": result.successful_bets, "total_bets": result.total_bets}
                ))

                # Holes won trend
                trends["holes_won"].append(TrendPoint(
                    timestamp=timestamp,
                    value=result.holes_won,
                    game_id=str(result.game_record_id)
                ))

            return trends

        except Exception as e:
            logger.error(f"Error getting performance trends for player {player_id}: {e}")
            return {}

    def get_player_insights(self, player_id: int) -> List[InsightRecommendation]:
        """Generate personalized insights and recommendations."""
        try:
            insights: List[InsightRecommendation] = []

            # Get player metrics
            metrics = self.get_advanced_player_metrics(player_id)
            player_stats = self.db.query(PlayerStatistics).filter(
                PlayerStatistics.player_id == player_id
            ).first()

            if not player_stats:
                return insights

            # Betting Performance Insight
            if "betting_accuracy" in metrics:
                betting_metric = metrics["betting_accuracy"]
                if betting_metric.percentile < 25 and betting_metric.confidence > 0.5:
                    insights.append(InsightRecommendation(
                        category="betting",
                        priority="high",
                        title="Improve Betting Strategy",
                        description=f"Your betting accuracy ({betting_metric.value:.1f}%) is in the bottom 25% of players.",
                        data_support={
                            "current_rate": betting_metric.value,
                            "percentile": betting_metric.percentile,
                            "total_bets": player_stats.total_bets
                        },
                        suggested_actions=[
                            "Be more conservative with your betting decisions",
                            "Study the odds before placing bets",
                            "Focus on partnerships rather than risky solo plays"
                        ]
                    ))
                elif betting_metric.percentile > 75:
                    insights.append(InsightRecommendation(
                        category="betting",
                        priority="low",
                        title="Excellent Betting Skills",
                        description=f"Your betting accuracy ({betting_metric.value:.1f}%) is in the top 25% of players.",
                        data_support={
                            "current_rate": betting_metric.value,
                            "percentile": betting_metric.percentile
                        },
                        suggested_actions=[
                            "Consider more aggressive betting strategies",
                            "Look for opportunities to double or raise stakes",
                            "Share your betting insights with partners"
                        ]
                    ))

            # Partnership Analysis
            if player_stats.partnerships_formed >= 5:
                partnership_rate = player_stats.partnership_success_rate
                if partnership_rate < 0.4:
                    insights.append(InsightRecommendation(
                        category="partnership",
                        priority="medium",
                        title="Partnership Selection",
                        description=f"Your partnerships succeed only {partnership_rate*100:.1f}% of the time.",
                        data_support={
                            "success_rate": partnership_rate,
                            "partnerships_formed": player_stats.partnerships_formed,
                            "partnerships_won": player_stats.partnerships_won
                        },
                        suggested_actions=[
                            "Be more selective when choosing partners",
                            "Consider handicap compatibility when partnering",
                            "Communicate better with your partners during games"
                        ]
                    ))

            # Consistency Analysis
            recent_results = self._get_recent_position_variance(player_id)
            if recent_results["variance"] > 2.0:
                insights.append(InsightRecommendation(
                    category="consistency",
                    priority="medium",
                    title="Improve Consistency",
                    description="Your performance varies significantly between games.",
                    data_support={
                        "variance": recent_results["variance"],
                        "games_analyzed": recent_results["games_analyzed"]
                    },
                    suggested_actions=[
                        "Focus on maintaining steady performance",
                        "Develop a consistent pre-game routine",
                        "Avoid extreme risk-taking that leads to volatile results"
                    ]
                ))

            # Experience-based insights
            if player_stats.games_played < 10:
                insights.append(InsightRecommendation(
                    category="experience",
                    priority="high",
                    title="Build Experience",
                    description="Play more games to develop reliable strategies.",
                    data_support={"games_played": player_stats.games_played},
                    suggested_actions=[
                        "Play at least 20 games to establish patterns",
                        "Try different strategies to find what works",
                        "Focus on learning rather than winning initially"
                    ]
                ))

            # Solo vs Partnership Balance
            solo_rate = player_stats.solo_attempts / max(1, player_stats.games_played)
            solo_success = player_stats.solo_wins / max(1, player_stats.solo_attempts)

            if solo_rate > 0.3 and solo_success < 0.2:
                insights.append(InsightRecommendation(
                    category="strategy",
                    priority="high",
                    title="Reduce Solo Play Risk",
                    description=f"You go solo {solo_rate*100:.1f}% of the time but only win {solo_success*100:.1f}% of those attempts.",
                    data_support={
                        "solo_rate": solo_rate,
                        "solo_success": solo_success,
                        "solo_attempts": player_stats.solo_attempts
                    },
                    suggested_actions=[
                        "Be more selective about going solo",
                        "Only go solo when you have a significant advantage",
                        "Focus more on partnership strategies"
                    ]
                ))

            return insights

        except Exception as e:
            logger.error(f"Error generating insights for player {player_id}: {e}")
            return []

    def get_comparative_leaderboard(self, metric: str = "total_earnings", limit: int = 100) -> List[Dict[str, Any]]:
        """Get comparative leaderboard for different metrics."""
        try:
            # Define available metrics and their queries
            metric_queries = {
                "total_earnings": (PlayerStatistics.total_earnings, desc),
                "win_rate": (func.cast(PlayerStatistics.games_won, float) / func.cast(PlayerStatistics.games_played, float), desc),
                "avg_earnings": (PlayerStatistics.avg_earnings_per_hole, desc),
                "betting_success": (PlayerStatistics.betting_success_rate, desc),
                "partnership_success": (PlayerStatistics.partnership_success_rate, desc),
                "consistency": (PlayerStatistics.games_played, desc)  # Placeholder - would need calculated field
            }

            if metric not in metric_queries:
                metric = "total_earnings"  # Default fallback

            query_field, order_func = metric_queries[metric]

            # Query for leaderboard
            query = self.db.query(
                PlayerProfile.id,
                PlayerProfile.name,
                PlayerStatistics.games_played,
                PlayerStatistics.games_won,
                PlayerStatistics.total_earnings,
                PlayerStatistics.avg_earnings_per_hole,
                PlayerStatistics.betting_success_rate,
                PlayerStatistics.partnership_success_rate,
                query_field.label("metric_value")
            ).join(
                PlayerStatistics, PlayerProfile.id == PlayerStatistics.player_id
            ).filter(
                and_(
                    PlayerProfile.is_active == 1,
                    PlayerProfile.is_ai == 0,  # Exclude AI players from leaderboard
                    PlayerStatistics.games_played >= 5
                )
            ).order_by(order_func(query_field)).limit(limit)

            results = query.all()

            leaderboard = []
            for rank, result in enumerate(results, 1):
                win_rate = (result.games_won / max(1, result.games_played)) * 100

                leaderboard.append({
                    "rank": rank,
                    "player_id": result.id,
                    "player_name": result.name,
                    "games_played": result.games_played,
                    "win_rate": round(win_rate, 1),
                    "total_earnings": round(result.total_earnings, 2),
                    "avg_earnings": round(result.avg_earnings_per_hole, 2),
                    "betting_success": round(result.betting_success_rate * 100, 1),
                    "partnership_success": round(result.partnership_success_rate * 100, 1),
                    "metric_value": float(result.metric_value) if result.metric_value else 0.0
                })

            return leaderboard

        except Exception as e:
            logger.error(f"Error generating leaderboard for metric {metric}: {e}")
            return []

    def get_game_mode_analytics(self, player_id: Optional[int] = None) -> Dict[str, Any]:
        """Get analytics for different game modes and player counts."""
        try:
            base_query = self.db.query(GamePlayerResult).join(
                GameRecord, GamePlayerResult.game_record_id == GameRecord.id
            )

            if player_id:
                base_query = base_query.filter(GamePlayerResult.player_profile_id == player_id)

            results = base_query.all()

            # Group by game mode and player count
            mode_analytics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
                "games_played": 0,
                "total_earnings": 0.0,
                "wins": 0,
                "avg_position": 0.0,
                "player_count_breakdown": defaultdict(int)
            })

            for result in results:
                game_record = self.db.query(GameRecord).filter(GameRecord.id == result.game_record_id).first()
                if game_record:
                    mode_key = f"{game_record.game_mode}_{game_record.player_count}p"

                    mode_analytics[mode_key]["games_played"] += 1
                    mode_analytics[mode_key]["total_earnings"] += result.total_earnings
                    if result.final_position == 1:
                        mode_analytics[mode_key]["wins"] += 1
                    mode_analytics[mode_key]["avg_position"] += result.final_position
                    mode_analytics[mode_key]["player_count_breakdown"][game_record.player_count] += 1

            # Calculate averages
            for mode_data in mode_analytics.values():
                if mode_data["games_played"] > 0:
                    mode_data["avg_earnings"] = mode_data["total_earnings"] / mode_data["games_played"]
                    mode_data["win_rate"] = (mode_data["wins"] / mode_data["games_played"]) * 100
                    mode_data["avg_position"] /= mode_data["games_played"]

            return dict(mode_analytics)

        except Exception as e:
            logger.error(f"Error getting game mode analytics: {e}")
            return {}

    def calculate_skill_rating(self, player_id: int) -> Dict[str, float]:
        """Calculate skill ratings similar to ELO or Glicko systems."""
        try:
            player_stats = self.db.query(PlayerStatistics).filter(
                PlayerStatistics.player_id == player_id
            ).first()

            if not player_stats:
                return {"overall": 1200.0, "confidence": 0.0}  # Default rating

            # Base rating calculation
            base_rating = 1200.0  # Starting rating

            # Win rate component (max 400 points)
            win_rate = player_stats.games_won / max(1, player_stats.games_played)
            win_rating = (win_rate - 0.25) * 800  # Scale so 25% = 0, 100% = 600

            # Earnings component (max 300 points)
            avg_earnings = player_stats.avg_earnings_per_hole
            earnings_rating = min(avg_earnings * 30, 300)  # Cap at 300 points

            # Betting component (max 200 points)
            betting_rating = (player_stats.betting_success_rate - 0.5) * 400  # 50% = 0, 100% = 200

            # Partnership component (max 100 points)
            partnership_rating = (player_stats.partnership_success_rate - 0.5) * 200  # 50% = 0, 100% = 100

            # Experience multiplier
            experience_factor = min(player_stats.games_played / 50.0, 1.0)  # Full weight at 50+ games

            # Calculate overall rating
            overall_rating = base_rating + (
                (win_rating + earnings_rating + betting_rating + partnership_rating) * experience_factor
            )

            # Confidence based on games played
            confidence = min(player_stats.games_played / 25.0, 1.0)  # Full confidence at 25+ games

            return {
                "overall": round(overall_rating, 1),
                "win_component": round(win_rating * experience_factor, 1),
                "earnings_component": round(earnings_rating * experience_factor, 1),
                "betting_component": round(betting_rating * experience_factor, 1),
                "partnership_component": round(partnership_rating * experience_factor, 1),
                "confidence": round(confidence, 2),
                "games_played": player_stats.games_played
            }

        except Exception as e:
            logger.error(f"Error calculating skill rating for player {player_id}: {e}")
            return {"overall": 1200.0, "confidence": 0.0}

    # Helper methods
    def _calculate_percentile(self, value: float, values: List[float]) -> float:
        """Calculate percentile rank for a value."""
        if not values:
            return 50.0

        sorted_values = sorted(values)
        rank = sum(1 for v in sorted_values if v <= value)
        return (rank / len(sorted_values)) * 100

    def _analyze_win_rate_trend(self, player_id: int) -> str:
        """Analyze win rate trend over recent games."""
        recent_results = self.db.query(GamePlayerResult.final_position).filter(
            GamePlayerResult.player_profile_id == player_id
        ).order_by(desc(GamePlayerResult.created_at)).limit(10).all()

        if len(recent_results) < 5:
            return "stable"

        positions = [result.final_position for result in recent_results]
        first_half = positions[:len(positions)//2]
        second_half = positions[len(positions)//2:]

        first_half_avg = sum(first_half) / len(first_half)
        second_half_avg = sum(second_half) / len(second_half)

        # Lower position is better, so improving means decreasing average position
        if second_half_avg < first_half_avg - 0.3:
            return "improving"
        elif second_half_avg > first_half_avg + 0.3:
            return "declining"
        else:
            return "stable"

    def _analyze_earnings_trend(self, player_id: int) -> str:
        """Analyze earnings trend over recent games."""
        recent_results = self.db.query(GamePlayerResult.total_earnings).filter(
            GamePlayerResult.player_profile_id == player_id
        ).order_by(desc(GamePlayerResult.created_at)).limit(10).all()

        if len(recent_results) < 5:
            return "stable"

        earnings = [result.total_earnings for result in recent_results]
        first_half = earnings[:len(earnings)//2]
        second_half = earnings[len(earnings)//2:]

        first_half_avg = sum(first_half) / len(first_half)
        second_half_avg = sum(second_half) / len(second_half)

        if second_half_avg > first_half_avg * 1.15:
            return "improving"
        elif second_half_avg < first_half_avg * 0.85:
            return "declining"
        else:
            return "stable"

    def _calculate_consistency_score(self, player_id: int) -> float:
        """Calculate consistency score (0-100, higher is more consistent)."""
        recent_results = self.db.query(GamePlayerResult.final_position).filter(
            GamePlayerResult.player_profile_id == player_id
        ).order_by(desc(GamePlayerResult.created_at)).limit(20).all()

        if len(recent_results) < 5:
            return 50.0  # Default for insufficient data

        positions = [result.final_position for result in recent_results]

        # Calculate variance (lower variance = higher consistency)
        mean_position = sum(positions) / len(positions)
        variance = sum((p - mean_position) ** 2 for p in positions) / len(positions)

        # Convert to 0-100 score (inverse of variance, scaled)
        consistency_score = max(0, 100 - (variance * 25))

        return float(min(100, consistency_score))

    def _get_recent_position_variance(self, player_id: int) -> Dict[str, Any]:
        """Get variance in recent finishing positions."""
        recent_results = self.db.query(GamePlayerResult.final_position).filter(
            GamePlayerResult.player_profile_id == player_id
        ).order_by(desc(GamePlayerResult.created_at)).limit(15).all()

        if len(recent_results) < 3:
            return {"variance": 0.0, "games_analyzed": len(recent_results)}

        positions = [result.final_position for result in recent_results]

        try:
            variance = statistics.variance(positions)
        except statistics.StatisticsError:
            variance = 0.0

        return {
            "variance": variance,
            "games_analyzed": len(recent_results),
            "mean_position": statistics.mean(positions),
            "best_position": min(positions),
            "worst_position": max(positions)
        }
