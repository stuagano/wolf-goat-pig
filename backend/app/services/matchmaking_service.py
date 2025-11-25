"""
Matchmaking service for automatically finding compatible golf groups.
Analyzes player availability to create 4-player groups with overlapping schedules.
"""

import logging
from collections import defaultdict
from datetime import datetime, time, timedelta
from itertools import combinations
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MatchmakingService:
    """Service for finding compatible 4-player golf groups based on availability."""

    @staticmethod
    def parse_time_string(time_str: Optional[str]) -> Optional[time]:
        """Convert time string like '9:00 AM' to time object."""
        if not time_str:
            return None
        try:
            return datetime.strptime(time_str, "%I:%M %p").time()
        except ValueError:
            logger.warning(f"Could not parse time string: {time_str}")
            return None

    @staticmethod
    def get_time_overlap(
        players_availability: List[Dict]
    ) -> Optional[Tuple[time, time]]:
        """
        Find the overlapping time window for a group of players on a specific day.
        
        Args:
            players_availability: List of availability dicts for players on same day
            
        Returns:
            Tuple of (start_time, end_time) if overlap exists, None otherwise
        """
        latest_start = None
        earliest_end = None

        for avail in players_availability:
            start = MatchmakingService.parse_time_string(avail.get('available_from_time'))
            end = MatchmakingService.parse_time_string(avail.get('available_to_time'))

            # If no times specified, assume all day availability
            if not start:
                start = time(6, 0)  # 6:00 AM
            if not end:
                end = time(20, 0)  # 8:00 PM

            # Track the latest start time
            if latest_start is None or start > latest_start:
                latest_start = start

            # Track the earliest end time
            if earliest_end is None or end < earliest_end:
                earliest_end = end

        # Check if there's actual overlap
        if latest_start and earliest_end and latest_start < earliest_end:
            return (latest_start, earliest_end)

        return None

    @staticmethod
    def calculate_overlap_duration(start: time, end: time) -> float:
        """Calculate duration of overlap in hours."""
        start_delta = timedelta(hours=start.hour, minutes=start.minute)
        end_delta = timedelta(hours=end.hour, minutes=end.minute)
        duration = end_delta - start_delta
        return duration.total_seconds() / 3600

    @staticmethod
    def find_matches(
        all_players_availability: List[Dict],
        min_overlap_hours: float = 2.0,
        preferred_days: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Find all possible 4-player groups with overlapping availability.
        
        Args:
            all_players_availability: List of all players with their availability
            min_overlap_hours: Minimum hours of overlap required (default 2 hours)
            preferred_days: List of preferred days of week (0=Monday, 6=Sunday)
            
        Returns:
            List of match suggestions with player groups and available times
        """
        matches = []

        # Group players by day availability
        players_by_day = defaultdict(list)

        for player in all_players_availability:
            for avail in player.get('availability', []):
                if avail.get('is_available'):
                    day = avail.get('day_of_week')
                    if preferred_days is None or day in preferred_days:
                        players_by_day[day].append({
                            'player_id': player['player_id'],
                            'player_name': player['player_name'],
                            'email': player['email'],
                            'available_from_time': avail.get('available_from_time'),
                            'available_to_time': avail.get('available_to_time'),
                            'notes': avail.get('notes')
                        })

        # Find 4-player combinations for each day
        for day, available_players in players_by_day.items():
            if len(available_players) < 4:
                continue

            # Try all combinations of 4 players
            for group in combinations(available_players, 4):
                # Check if these 4 players have overlapping times
                overlap = MatchmakingService.get_time_overlap(list(group))

                if overlap:
                    start_time, end_time = overlap
                    duration = MatchmakingService.calculate_overlap_duration(start_time, end_time)

                    # Only include if overlap is sufficient
                    if duration >= min_overlap_hours:
                        matches.append({
                            'day_of_week': day,
                            'players': list(group),
                            'overlap_start': start_time.strftime("%I:%M %p"),
                            'overlap_end': end_time.strftime("%I:%M %p"),
                            'overlap_duration_hours': duration,
                            'suggested_tee_time': MatchmakingService.suggest_tee_time(
                                start_time, end_time
                            ),
                            'match_quality': MatchmakingService.calculate_match_quality(
                                list(group), duration
                            )
                        })

        # Sort by match quality (best matches first)
        matches.sort(key=lambda x: x['match_quality'], reverse=True)

        # Remove duplicate player groups (same 4 players on different days)
        unique_matches = []
        seen_groups = set()

        for match in matches:
            player_ids = tuple(sorted([p['player_id'] for p in match['players']]))
            if player_ids not in seen_groups:
                seen_groups.add(player_ids)
                unique_matches.append(match)

        return unique_matches

    @staticmethod
    def suggest_tee_time(start: time, end: time) -> str:
        """Suggest an optimal tee time within the overlap window."""
        # Prefer morning tee times (9-11 AM) if possible
        preferred_start = time(9, 0)
        preferred_end = time(11, 0)

        # If overlap includes preferred window
        if start <= preferred_start and end >= preferred_end:
            return "9:00 AM"
        elif start <= time(10, 0) and end >= time(12, 0):
            return "10:00 AM"
        else:
            # Return start of overlap window
            return start.strftime("%I:%M %p")

    @staticmethod
    def calculate_match_quality(players: List[Dict], duration: float) -> float:
        """
        Calculate a quality score for a match based on various factors.
        Higher score = better match.
        """
        score = 0.0

        # Base score from overlap duration (more overlap = better)
        score += min(duration / 4, 1.0) * 50  # Max 50 points for 4+ hour overlap

        # Bonus for no time restrictions (all day availability)
        all_day_count = sum(
            1 for p in players
            if not p.get('available_from_time') and not p.get('available_to_time')
        )
        score += all_day_count * 5  # 5 points per flexible player

        # Bonus for morning availability (preferred golf time)
        morning_available = 0
        for p in players:
            start = MatchmakingService.parse_time_string(p.get('available_from_time'))
            if not start or start <= time(10, 0):
                morning_available += 1
        score += morning_available * 3  # 3 points per morning-available player

        return score

    @staticmethod
    def create_match_notification(match: Dict) -> Dict:
        """
        Create email notification content for a matched group.
        
        Args:
            match: Match dictionary with players and times
            
        Returns:
            Dictionary with email subject and body
        """
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                     'Friday', 'Saturday', 'Sunday']
        day_name = day_names[match['day_of_week']]

        player_names = [p['player_name'] for p in match['players']]
        player_list = ", ".join(player_names[:-1]) + f" and {player_names[-1]}"

        subject = f"⛳ Golf Match Found for {day_name}!"

        body = f"""
Great news! We've found a perfect golf match for your group.

🏌️ **Matched Players:**
{chr(10).join([f"  • {p['player_name']}" for p in match['players']])}

📅 **Day:** {day_name}
⏰ **Available Window:** {match['overlap_start']} - {match['overlap_end']}
🎯 **Suggested Tee Time:** {match['suggested_tee_time']}

Everyone in this group is available during this time window. This would be a great opportunity to get together for a round!

**Next Steps:**
1. Reply to this email to confirm your interest
2. Coordinate with the group on exact tee time
3. Book your tee time at your preferred course

Happy golfing! ⛳
"""

        return {
            'subject': subject,
            'body': body,
            'recipients': [p['email'] for p in match['players']]
        }

    @staticmethod
    def filter_recent_matches(
        matches: List[Dict],
        recent_match_history: List[Dict],
        days_between_matches: int = 3
    ) -> List[Dict]:
        """
        Filter out matches that include players who were recently matched.
        
        Args:
            matches: List of potential matches
            recent_match_history: List of recent matches with timestamps
            days_between_matches: Minimum days between matches for same players
            
        Returns:
            Filtered list of matches
        """
        if not recent_match_history:
            return matches

        # Get players who were recently matched
        recently_matched = set()
        cutoff_date = datetime.now() - timedelta(days=days_between_matches)

        for past_match in recent_match_history:
            match_date = past_match.get('created_at')
            if isinstance(match_date, str):
                match_date = datetime.fromisoformat(match_date)

            if match_date is not None and match_date > cutoff_date:
                for player in past_match.get('players', []):
                    recently_matched.add(player['player_id'])

        # Filter out matches with recently matched players
        filtered_matches = []
        for match in matches:
            player_ids = {p['player_id'] for p in match['players']}
            if not player_ids.intersection(recently_matched):
                filtered_matches.append(match)

        return filtered_matches
