"""
Random team formation service for creating balanced 4-player groups from daily signups.
Handles scenarios where more than 4 players are signed up for a given day.
"""

from typing import List, Dict, Optional, Tuple
import random
import logging
from datetime import datetime
from itertools import combinations

logger = logging.getLogger(__name__)

class TeamFormationService:
    """Service for creating random team formations from daily signups."""
    
    @staticmethod
    def generate_random_teams(
        players: List[Dict], 
        seed: Optional[int] = None,
        max_teams: Optional[int] = None
    ) -> List[Dict]:
        """
        Generate random 4-player teams from a list of signed-up players.
        
        Args:
            players: List of player dictionaries with player info
            seed: Optional random seed for reproducible results
            max_teams: Maximum number of teams to create (default: all possible)
            
        Returns:
            List of team dictionaries with 4 players each
        """
        if len(players) < 4:
            logger.warning(f"Not enough players for team formation: {len(players)} < 4")
            return []
        
        # Set random seed if provided for reproducible results
        if seed is not None:
            random.seed(seed)
        
        # Create a copy to avoid modifying original list
        available_players = players.copy()
        random.shuffle(available_players)
        
        teams = []
        team_number = 1
        
        # Create teams of 4 players
        while len(available_players) >= 4:
            team_players = available_players[:4]
            available_players = available_players[4:]
            
            team = {
                "team_id": team_number,
                "players": team_players,
                "created_at": datetime.now().isoformat(),
                "formation_method": "random"
            }
            teams.append(team)
            team_number += 1
            
            # Check if we've reached max teams limit
            if max_teams and len(teams) >= max_teams:
                break
        
        # Log remaining players who couldn't form a complete team
        if available_players:
            logger.info(f"Remaining players not assigned to teams: {len(available_players)}")
        
        return teams
    
    @staticmethod
    def create_team_pairings_with_rotations(
        players: List[Dict],
        num_rotations: int = 3,
        seed: Optional[int] = None
    ) -> List[Dict]:
        """
        Create multiple team pairing rotations for variety throughout the day.
        
        Args:
            players: List of player dictionaries
            num_rotations: Number of different team rotations to create
            seed: Optional random seed for reproducible results
            
        Returns:
            List of rotation dictionaries, each containing teams for that rotation
        """
        if len(players) < 4:
            return []
        
        rotations = []
        
        for rotation in range(num_rotations):
            # Use different seed for each rotation to ensure variety
            rotation_seed = (seed + rotation) if seed is not None else None
            
            teams = TeamFormationService.generate_random_teams(
                players, 
                seed=rotation_seed,
                max_teams=None
            )
            
            if teams:
                rotations.append({
                    "rotation_number": rotation + 1,
                    "teams": teams,
                    "created_at": datetime.now().isoformat(),
                    "total_teams": len(teams),
                    "total_players_assigned": len(teams) * 4
                })
        
        return rotations
    
    @staticmethod
    def generate_balanced_teams(
        players: List[Dict],
        skill_key: str = "handicap",
        seed: Optional[int] = None
    ) -> List[Dict]:
        """
        Generate teams with balanced skill levels using handicap or skill ratings.
        
        Args:
            players: List of player dictionaries
            skill_key: Key to use for skill-based balancing (e.g., 'handicap')
            seed: Optional random seed
            
        Returns:
            List of balanced team dictionaries
        """
        if len(players) < 4:
            return []
        
        # Set random seed if provided
        if seed is not None:
            random.seed(seed)
        
        # Sort players by skill level (lower handicap = better player)
        players_with_skill = []
        players_without_skill = []
        
        for player in players:
            if skill_key in player and player[skill_key] is not None:
                players_with_skill.append(player)
            else:
                # Assign default handicap for balancing
                player_copy = player.copy()
                player_copy[skill_key] = 18.0  # Default handicap
                players_without_skill.append(player_copy)
        
        # Combine lists and sort by skill
        all_players = players_with_skill + players_without_skill
        all_players.sort(key=lambda p: p.get(skill_key, 18.0))
        
        teams = []
        team_number = 1
        
        # Snake draft approach for balanced teams
        while len(all_players) >= 4:
            # Take players from different skill levels
            if len(all_players) >= 8:
                # Take best, worst, middle-low, middle-high
                team_players = [
                    all_players.pop(0),      # Best player
                    all_players.pop(-1),     # Worst player  
                    all_players.pop(len(all_players)//2),  # Middle player
                    all_players.pop(len(all_players)//2)   # Another middle player
                ]
            else:
                # Just take first 4 remaining players
                team_players = all_players[:4]
                all_players = all_players[4:]
            
            # Calculate team average handicap
            team_avg_handicap = sum(p.get(skill_key, 18.0) for p in team_players) / 4
            
            team = {
                "team_id": team_number,
                "players": team_players,
                "average_handicap": round(team_avg_handicap, 1),
                "created_at": datetime.now().isoformat(),
                "formation_method": "balanced"
            }
            teams.append(team)
            team_number += 1
        
        return teams
    
    @staticmethod
    def create_team_summary(teams: List[Dict]) -> Dict:
        """
        Create a summary of the team formation results.
        
        Args:
            teams: List of team dictionaries
            
        Returns:
            Summary dictionary with statistics
        """
        if not teams:
            return {
                "total_teams": 0,
                "total_players_assigned": 0,
                "formation_method": None,
                "created_at": datetime.now().isoformat()
            }
        
        total_players = sum(len(team["players"]) for team in teams)
        formation_method = teams[0].get("formation_method", "unknown")
        
        summary = {
            "total_teams": len(teams),
            "total_players_assigned": total_players,
            "formation_method": formation_method,
            "created_at": datetime.now().isoformat(),
            "teams": teams
        }
        
        # Add average handicap info if available
        if formation_method == "balanced":
            handicaps = [team.get("average_handicap") for team in teams if team.get("average_handicap")]
            if handicaps:
                summary["average_team_handicap"] = round(sum(handicaps) / len(handicaps), 1)
                summary["handicap_range"] = {
                    "min": min(handicaps),
                    "max": max(handicaps)
                }
        
        return summary
    
    @staticmethod
    def validate_team_formation(teams: List[Dict]) -> Dict:
        """
        Validate that team formation results are correct.
        
        Args:
            teams: List of team dictionaries
            
        Returns:
            Validation result dictionary
        """
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check each team has exactly 4 players
        for i, team in enumerate(teams):
            if len(team["players"]) != 4:
                validation["is_valid"] = False
                validation["errors"].append(f"Team {i+1} has {len(team['players'])} players, expected 4")
        
        # Check for duplicate players across teams
        all_player_ids = []
        for team in teams:
            for player in team["players"]:
                player_id = player.get("id") or player.get("player_profile_id")
                if player_id in all_player_ids:
                    validation["is_valid"] = False
                    validation["errors"].append(f"Player ID {player_id} appears in multiple teams")
                all_player_ids.append(player_id)
        
        # Check team formation timestamp consistency
        creation_times = [team.get("created_at") for team in teams if team.get("created_at")]
        if len(set(creation_times)) > 1:
            validation["warnings"].append("Teams have different creation timestamps")
        
        return validation