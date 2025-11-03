from typing import List, Dict
import random
import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import GameStateModel, GameRecord, GamePlayerResult
from .domain.player import Player
from .state.betting_state import BettingState
from .state.shot_state import ShotState
from .state.player_manager import PlayerManager
from .state.course_manager import CourseManager, DEFAULT_COURSES

# Default player names for MVP
DEFAULT_PLAYERS = [
    Player(id="p1", name="Bob", handicap=10.5),
    Player(id="p2", name="Scott", handicap=15),
    Player(id="p3", name="Vince", handicap=8),
    Player(id="p4", name="Mike", handicap=20.5),
]

# Example stroke index for 18 holes (1 = hardest, 18 = easiest)


class GameState:
    def __init__(self, game_id=None):
        self._db_session = SessionLocal()
        # Generate or use provided game_id
        self.game_id = game_id or str(uuid.uuid4())
        self._game_start_time = datetime.utcnow().isoformat()
        self._load_from_db()
        self.course_manager = getattr(self, 'course_manager', CourseManager())
        if not hasattr(self, 'player_manager') or self.player_manager is None:
            self.player_manager = PlayerManager(DEFAULT_PLAYERS.copy())
        self.current_hole = getattr(self, 'current_hole', 1)
        self.betting_state = getattr(self, 'betting_state', BettingState())
        self.hole_scores = getattr(self, 'hole_scores', {p.id: None for p in self.player_manager.players})
        self.gross_scores = getattr(self, 'gross_scores', {p.id: None for p in self.player_manager.players})
        self.game_status_message = getattr(self, 'game_status_message', "Time to toss the tees!")
        self.player_float_used = getattr(self, 'player_float_used', {p.id: False for p in self.player_manager.players})
        self.carry_over = getattr(self, 'carry_over', False)
        self.hole_history = getattr(self, 'hole_history', [])
        self._last_points = getattr(self, '_last_points', {p.id: 0 for p in self.player_manager.players})
        self.shot_state = getattr(self, 'shot_state', ShotState())
        self.tee_shot_results = getattr(self, 'tee_shot_results', None)
        self._game_completed = getattr(self, '_game_completed', False)

    def reset(self):
        self.player_manager = PlayerManager(DEFAULT_PLAYERS.copy())
        self.current_hole = 1
        self.betting_state = BettingState()
        self.hole_scores = {p.id: None for p in self.player_manager.players}
        self.gross_scores = {p.id: None for p in self.player_manager.players}
        self.game_status_message = "Time to toss the tees!"
        self.player_float_used = {p.id: False for p in self.player_manager.players}
        self.carry_over = False
        self.hole_history = []
        self._last_points = {p.id: 0 for p in self.player_manager.players}
        self.course_manager = CourseManager()
        self.shot_state = ShotState()
        self.tee_shot_results = None
        self._save_to_db()

    def dispatch_action(self, action, payload):
        # Betting actions are delegated to BettingState
        betting_actions = ["request_partner", "accept_partner", "decline_partner", "go_solo",
                          "offer_double", "accept_double", "decline_double", "concede_hole"]
        if action in betting_actions:
            result = self.betting_state.dispatch_action(action, payload, self.player_manager.players)
            self.game_status_message = f"Captain {self._player_name(payload.get('captain_id', ''))} {result.split('.')[0].lower()}." if 'captain_id' in payload else result
            self._save_to_db()
            return result
        elif action == "invoke_float":
            return self.invoke_float(payload.get("captain_id"))
        elif action == "toggle_option":
            return self.toggle_option(payload.get("captain_id"))
        elif action == "record_gross_score":
            return self.record_gross_score(payload.get("player_id"), payload.get("score"))
        elif action == "record_net_score":
            return self.record_net_score(payload.get("player_id"), payload.get("score"))
        elif action == "calculate_hole_points":
            return self.calculate_hole_points()
        elif action == "next_hole":
            return self.next_hole()
        else:
            raise ValueError(f"Unknown action: {action}")



    def invoke_float(self, captain_id):
        # Find the player and use their float
        for player in self.player_manager.players:
            if player.id == captain_id:
                if not player.use_float():
                    raise ValueError("Float already used by this captain.")
                self.betting_state.base_wager *= 2
                self.player_float_used[captain_id] = True  # Keep for backward compatibility
                self.game_status_message = f"{self._player_name(captain_id)} invoked the float! Wager doubled."
                return "Float invoked."
        raise ValueError("Captain not found.")

    def toggle_option(self, captain_id):
        # For MVP, just double wager if captain is eligible
        self.betting_state.base_wager *= 2
        self.game_status_message = f"{self._player_name(captain_id)} toggled the option. Wager doubled."
        return "Option toggled."

    def record_gross_score(self, player_id, gross_score):
        """
        Record a player's gross score (actual strokes) and automatically calculate net score.
        Net score = gross score - handicap strokes for this hole.
        """
        if player_id not in self.hole_scores:
            raise ValueError("Invalid player ID.")

        # Record gross score
        self.gross_scores[player_id] = gross_score

        # Get handicap strokes for this hole
        player_strokes = self.get_player_strokes()
        strokes_for_hole = player_strokes.get(player_id, {}).get(self.current_hole, 0)

        # Calculate net score: gross - strokes
        net_score = gross_score - strokes_for_hole
        self.hole_scores[player_id] = net_score

        # Also record in the Player object (using net score)
        for player in self.player_manager.players:
            if player.id == player_id:
                player.record_hole_score(self.current_hole, net_score)
                break

        player_name = self._player_name(player_id)
        if strokes_for_hole > 0:
            self.game_status_message = f"{player_name}: {gross_score} gross, {net_score} net ({strokes_for_hole} stroke{'s' if strokes_for_hole != 1 else ''})"
        else:
            self.game_status_message = f"{player_name}: {gross_score} (scratch)"

        return f"Score recorded: {gross_score} gross → {net_score} net"

    def record_net_score(self, player_id, score):
        """
        Legacy method - record net score directly (for backward compatibility).
        This assumes the score is already adjusted for handicap.
        """
        if player_id not in self.hole_scores:
            raise ValueError("Invalid player ID.")

        # Record net score
        self.hole_scores[player_id] = score
        # We don't know the gross score in this case
        self.gross_scores[player_id] = score

        # Also record the score in the Player object
        for player in self.player_manager.players:
            if player.id == player_id:
                player.record_hole_score(self.current_hole, score)
                break

        self.game_status_message = f"Score recorded for {self._player_name(player_id)}."
        return "Score recorded."

    def calculate_hole_points(self):
        # Delegate to BettingState for points calculation
        msg = self.betting_state.calculate_hole_points(self.hole_scores, self.player_manager.players)
        
        # Record hole history
        points_now = {p.id: p.points for p in self.player_manager.players}
        points_delta = {pid: points_now[pid] - self._last_points.get(pid, 0) for pid in points_now}

        # Create player scores with names for better readability
        player_scores = {}
        for player in self.player_manager.players:
            player_scores[player.id] = {
                "name": player.name,
                "gross_score": self.gross_scores.get(player.id),
                "net_score": self.hole_scores.get(player.id),
                "points_delta": points_delta.get(player.id, 0),
                "total_points": points_now.get(player.id, 0)
            }

        self.hole_history.append({
            "hole": self.current_hole,
            "captain_id": self.player_manager.captain_id,
            "captain_name": self._player_name(self.player_manager.captain_id),
            "hitting_order": list(self.player_manager.hitting_order),
            "net_scores": dict(self.hole_scores),
            "gross_scores": dict(self.gross_scores),
            "player_scores": player_scores,
            "points_delta": dict(points_delta),
            "teams": dict(self.betting_state.teams),
        })
        self._last_points = dict(points_now)
        self.game_status_message = msg
        self._save_to_db()
        return msg



    def next_hole(self):
        self.current_hole += 1
        self.player_manager.rotate_captain()
        self.betting_state.reset_hole()
        self.hole_scores = {p.id: None for p in self.player_manager.players}
        self.gross_scores = {p.id: None for p in self.player_manager.players}

        # Reset shot state for new hole
        if hasattr(self, 'shot_state'):
            self.shot_state.reset_for_hole()
        else:
            self.shot_state = ShotState()

        # Reset float usage for all players
        for player in self.player_manager.players:
            player.reset_float()

        self.game_status_message = f"Hole {self.current_hole}. {self.player_manager.captain_id} is captain."
        self._save_to_db()
        return "Advanced to next hole."

    def _player_name(self, pid):
        for p in self.player_manager.players:
            if p.id == pid:
                return p.name
        return pid

    def get_hole_history(self):
        return self.hole_history

    def _serialize(self):
        # Return a dict of all stateful fields
        players = getattr(self, "player_manager", PlayerManager()).players
        # Convert Player objects to dicts for serialization
        players_data = [p.to_dict() if hasattr(p, 'to_dict') else p for p in players]
        
        # Get betting state data
        betting_state_data = getattr(self, "betting_state", BettingState()).to_dict()
        
        return {
            "player_manager": self.player_manager.to_dict(),
            "current_hole": getattr(self, "current_hole", 1),
            "betting_state": betting_state_data,
            "hole_scores": getattr(self, "hole_scores", {}),
            "gross_scores": getattr(self, "gross_scores", {}),
            "game_status_message": getattr(self, "game_status_message", "Time to toss the tees!"),
            "player_float_used": getattr(self, "player_float_used", {}),
            "carry_over": getattr(self, "carry_over", False),
            "hole_history": getattr(self, "hole_history", []),
            "_last_points": getattr(self, "_last_points", {}),
            "course_manager": getattr(self, "course_manager", CourseManager()).to_dict(),
            # Event-driven simulation state
            "shot_state": getattr(self, "shot_state", ShotState()).to_dict(),
            "tee_shot_results": getattr(self, "tee_shot_results", None),
            # Backward compatibility - keep old betting fields for migration
            "players": players_data,
            "hitting_order": list(self.player_manager.hitting_order),
            "captain_id": self.player_manager.captain_id,
            "teams": betting_state_data.get("teams", {}),
            "base_wager": betting_state_data.get("base_wager", 1),
            "doubled_status": betting_state_data.get("doubled_status", False),
            "game_phase": betting_state_data.get("game_phase", 'Regular'),
        }

    def _deserialize(self, data):
        # Convert player data to Player objects
        if "player_manager" in data:
            self.player_manager = PlayerManager()
            self.player_manager.from_dict(data["player_manager"])
        else:
            # Backward compatibility
            players_data = data.get("players", [])
            if players_data and isinstance(players_data[0], dict):
                self.player_manager = PlayerManager([Player.from_dict(p) for p in players_data])
            else:
                self.player_manager = PlayerManager(DEFAULT_PLAYERS.copy())
            self.player_manager.hitting_order = data.get("hitting_order", [p.id for p in self.player_manager.players])
            self.player_manager.captain_id = data.get("captain_id", self.player_manager.hitting_order[0] if self.player_manager.hitting_order else None)
        
        self.current_hole = data.get("current_hole", 1)
        # Handle betting state - check for new format first, then fall back to old format
        if "betting_state" in data:
            self.betting_state = BettingState()
            self.betting_state.from_dict(data["betting_state"])
        else:
            # Backward compatibility - migrate from old format
            self.betting_state = BettingState()
            self.betting_state.teams = data.get("teams", {})
            self.betting_state.base_wager = data.get("base_wager", 1)
            self.betting_state.doubled_status = data.get("doubled_status", False)
            self.betting_state.game_phase = data.get("game_phase", 'Regular')
        
        self.hole_scores = data.get("hole_scores", {p.id: None for p in self.player_manager.players})
        self.gross_scores = data.get("gross_scores", {p.id: None for p in self.player_manager.players})
        self.game_status_message = data.get("game_status_message", "Time to toss the tees!")
        self.player_float_used = data.get("player_float_used", {p.id: False for p in self.player_manager.players})
        self.carry_over = data.get("carry_over", False)
        self.hole_history = data.get("hole_history", [])
        self._last_points = data.get("_last_points", {p.id: 0 for p in self.player_manager.players})
        # Handle course manager - check for new format first, then fall back to old format
        if "course_manager" in data:
            self.course_manager = CourseManager()
            self.course_manager.from_dict(data["course_manager"])
        else:
            # Backward compatibility - migrate from old format
            self.course_manager = CourseManager()
            self.course_manager.selected_course = data.get("selected_course", None)
            self.course_manager.hole_stroke_indexes = data.get("hole_stroke_indexes", [h["stroke_index"] for h in DEFAULT_COURSES["Wing Point Golf & Country Club"]])
            self.course_manager.hole_pars = data.get("hole_pars", [h["par"] for h in DEFAULT_COURSES["Wing Point Golf & Country Club"]])
            self.course_manager.hole_yards = data.get("hole_yards", [h["yards"] for h in DEFAULT_COURSES["Wing Point Golf & Country Club"]])
            # Note: hole_descriptions not preserved in CourseManager, but can be reconstructed from course_data
        # Event-driven simulation state
        if "shot_state" in data:
            self.shot_state = ShotState()
            self.shot_state.from_dict(data["shot_state"])
        else:
            # Backward compatibility - migrate from old shot_sequence format
            self.shot_state = ShotState()
            if "shot_sequence" in data and data["shot_sequence"]:
                old_seq = data["shot_sequence"]
                self.shot_state.phase = old_seq.get("phase", "tee_shots")
                self.shot_state.current_player_index = old_seq.get("current_player_index", 0)
                self.shot_state.pending_decisions = old_seq.get("pending_decisions", [])
                # Convert old completed_shots format
                for shot_data in old_seq.get("completed_shots", []):
                    self.shot_state.add_completed_shot(
                        shot_data.get("player_id", ""),
                        shot_data.get("shot_result", {}),
                        shot_data.get("probabilities")
                    )
        self.tee_shot_results = data.get("tee_shot_results", None)
        # Defensive: always ensure course_manager is set
        if not hasattr(self, 'course_manager'):
            self.course_manager = CourseManager()
        if not hasattr(self, 'shot_state'):
            self.shot_state = ShotState()
        if not hasattr(self, 'tee_shot_results'):
            self.tee_shot_results = None
        if not hasattr(self, 'betting_state'):
            self.betting_state = BettingState()

    def _save_to_db(self):
        """Save the current state as JSON in the DB with unique game_id"""
        try:
            state_json = self._serialize()
            session = self._db_session
            # Try to find existing game by game_id
            obj = session.query(GameStateModel).filter(GameStateModel.game_id == self.game_id).first()
            current_time = datetime.utcnow().isoformat()

            if obj:
                obj.state = state_json
                obj.updated_at = current_time
            else:
                obj = GameStateModel(
                    game_id=self.game_id,
                    state=state_json,
                    created_at=self._game_start_time,
                    updated_at=current_time
                )
                session.add(obj)
            session.commit()
        except Exception as e:
            print(f"⚠️ Database save failed: {e}")
            # Continue without saving - this allows the app to work even if DB is down
            pass

    def _load_from_db(self):
        """Load the state from DB by game_id if present with error handling"""
        try:
            session = self._db_session
            # Try to load by game_id
            obj = session.query(GameStateModel).filter(GameStateModel.game_id == self.game_id).first()
            if obj and obj.state:
                self._deserialize(obj.state)
                # Don't override the game_id from deserialization
                self.game_id = obj.game_id
                self._game_start_time = obj.created_at
            else:
                # New game, don't reset - keep the generated game_id
                pass
        except Exception as e:
            print(f"⚠️ Database load failed: {e}")
            # Fall back to new game state if DB is unavailable
            pass

    def get_betting_tips(self):
        return self.betting_state.get_betting_tips(self.player_manager.players, self.current_hole, self.player_float_used, self.carry_over)

    def complete_game(self):
        """Mark game as completed and save permanent game results to database"""
        if self._game_completed:
            return "Game already completed"

        try:
            session = self._db_session
            current_time = datetime.utcnow().isoformat()

            # Calculate game duration
            start_time = datetime.fromisoformat(self._game_start_time)
            end_time = datetime.utcnow()
            duration_minutes = int((end_time - start_time).total_seconds() / 60)

            # Get final scores (player points/earnings)
            final_scores = {p.id: p.points for p in self.player_manager.players}

            # Create GameRecord
            game_record = GameRecord(
                game_id=self.game_id,
                course_name=self.course_manager.course_name or "Unknown Course",
                game_mode="wolf_goat_pig",
                player_count=len(self.player_manager.players),
                total_holes_played=len(self.hole_history),
                game_duration_minutes=duration_minutes,
                created_at=self._game_start_time,
                completed_at=current_time,
                game_settings={
                    "base_wager": self.betting_state.base_wager,
                    "game_phase": self.betting_state.game_phase
                },
                final_scores=final_scores
            )
            session.add(game_record)
            session.flush()  # Get the game_record.id

            # Sort players by final earnings (descending)
            sorted_players = sorted(
                self.player_manager.players,
                key=lambda p: p.points,
                reverse=True
            )

            # Create GamePlayerResult for each player
            for position, player in enumerate(sorted_players, start=1):
                # Calculate player statistics
                holes_won = sum(1 for hole in self.hole_history
                              if hole.get('points_delta', {}).get(player.id, 0) > 0)

                # Count partnerships and solo attempts
                partnerships_formed = 0
                partnerships_won = 0
                solo_attempts = 0
                solo_wins = 0

                for hole in self.hole_history:
                    teams = hole.get('teams', {})
                    points_delta = hole.get('points_delta', {})

                    if teams.get('type') == 'partners':
                        team1 = teams.get('team1', [])
                        team2 = teams.get('team2', [])
                        if player.id in team1 or player.id in team2:
                            partnerships_formed += 1
                            if points_delta.get(player.id, 0) > 0:
                                partnerships_won += 1
                    elif teams.get('type') == 'solo':
                        if player.id == teams.get('solo_player') or player.id == teams.get('captain'):
                            solo_attempts += 1
                            if points_delta.get(player.id, 0) > 0:
                                solo_wins += 1

                # Build hole scores dict
                hole_scores_dict = {}
                for hole in self.hole_history:
                    hole_num = hole.get('hole')
                    net_score = hole.get('net_scores', {}).get(player.id)
                    gross_score = hole.get('gross_scores', {}).get(player.id)
                    points = hole.get('points_delta', {}).get(player.id, 0)

                    if hole_num:
                        hole_scores_dict[str(hole_num)] = {
                            "net_score": net_score,
                            "gross_score": gross_score,
                            "points_won": points
                        }

                # Build betting history
                betting_history = []
                for hole in self.hole_history:
                    hole_num = hole.get('hole')
                    teams = hole.get('teams', {})
                    betting_history.append({
                        "hole": hole_num,
                        "team_type": teams.get('type'),
                        "was_captain": hole.get('captain_id') == player.id,
                        "points_result": hole.get('points_delta', {}).get(player.id, 0)
                    })

                # Calculate performance metrics
                score_performance = {"eagles": 0, "birdies": 0, "pars": 0,
                                   "bogeys": 0, "double_bogeys": 0, "worse": 0}

                for hole in self.hole_history:
                    net_score = hole.get('net_scores', {}).get(player.id)
                    hole_num = hole.get('hole')
                    if net_score and hole_num:
                        # Get par for this hole
                        hole_par = self.course_manager.hole_pars.get(hole_num - 1, 4)
                        diff = net_score - hole_par

                        if diff <= -2:
                            score_performance["eagles"] += 1
                        elif diff == -1:
                            score_performance["birdies"] += 1
                        elif diff == 0:
                            score_performance["pars"] += 1
                        elif diff == 1:
                            score_performance["bogeys"] += 1
                        elif diff == 2:
                            score_performance["double_bogeys"] += 1
                        else:
                            score_performance["worse"] += 1

                performance_metrics = {
                    "score_performance": score_performance,
                    "average_points_per_hole": player.points / len(self.hole_history) if self.hole_history else 0,
                    "best_hole": max(hole_scores_dict.items(),
                                   key=lambda x: x[1].get('points_won', 0))[0] if hole_scores_dict else None,
                    "worst_hole": min(hole_scores_dict.items(),
                                    key=lambda x: x[1].get('points_won', 0))[0] if hole_scores_dict else None
                }

                # Create GamePlayerResult
                player_result = GamePlayerResult(
                    game_record_id=game_record.id,
                    player_profile_id=0,  # TODO: Link to actual player profile
                    player_name=player.name,
                    final_position=position,
                    total_earnings=player.points,
                    holes_won=holes_won,
                    successful_bets=holes_won,  # Simplified
                    total_bets=len(self.hole_history),
                    partnerships_formed=partnerships_formed,
                    partnerships_won=partnerships_won,
                    solo_attempts=solo_attempts,
                    solo_wins=solo_wins,
                    hole_scores=hole_scores_dict,
                    betting_history=betting_history,
                    performance_metrics=performance_metrics,
                    created_at=current_time
                )
                session.add(player_result)

            # Commit all records
            session.commit()

            # Mark game as completed
            self._game_completed = True
            self._save_to_db()

            return f"Game completed and saved. Game ID: {self.game_id}"

        except Exception as e:
            print(f"⚠️ Error completing game: {e}")
            session.rollback()
            return f"Error completing game: {e}"



    def get_player_strokes(self):
        """
        Returns a dict: {player_id: {hole_number: stroke_type}}, where stroke_type is 1 (full stroke), 0.5 (half), or 0 (none)
        Uses relative handicaps - strokes are calculated relative to the lowest handicap in the group.
        """
        n_holes = len(self.course_manager.hole_stroke_indexes)
        result = {}

        # Find the lowest handicap in the group for relative handicap calculation
        min_handicap = min(p.handicap for p in self.player_manager.players)

        for player in self.player_manager.players:
            pid = player.id
            # Calculate relative handicap (difference from lowest handicap)
            relative_hcap = player.handicap - min_handicap
            strokes = {i+1: 0 for i in range(n_holes)}
            full_strokes = int(relative_hcap)
            half_stroke = (relative_hcap - full_strokes) >= 0.5

            # Full strokes
            for i, idx in enumerate(self.course_manager.hole_stroke_indexes):
                if idx <= full_strokes:
                    strokes[i+1] = 1
            # If handicap > n_holes, assign extra strokes (second stroke) to lowest index holes
            if full_strokes > n_holes:
                extra = full_strokes - n_holes
                hardest = sorted(range(n_holes), key=lambda i: self.course_manager.hole_stroke_indexes[i])[:extra]
                for i in hardest:
                    strokes[i+1] += 1
            # Half stroke: assign to next hardest hole
            if half_stroke:
                # Find the next hardest hole not already getting an extra stroke
                eligible = sorted([(i, self.course_manager.hole_stroke_indexes[i]) for i in range(n_holes) if strokes[i+1] == 0], key=lambda x: x[1])
                if eligible:
                    strokes[eligible[0][0]+1] = 0.5
            result[pid] = strokes
        return result

    def setup_players(self, players: list[dict], course_name: str = None):
        """
        Set custom players (id, name, handicap, strength) and reset the game state. Optionally set course.
        """
        if len(players) != 4:
            raise ValueError("Exactly 4 players required.")
        for p in players:
            if not all(k in p for k in ("id", "name", "handicap", "strength")):
                raise ValueError("Each player must have id, name, handicap, and strength.")
        self.reset()  # <-- This ensures ALL state is cleared!
        
        # Convert dict players to Player objects
        player_objs = [
            Player(
                id=p["id"], 
                name=p["name"], 
                handicap=float(p["handicap"]), 
                strength=p["strength"]
            ) for p in players
        ]
        
        self.player_manager.setup_players(player_objs)
        
        self.current_hole = 1
        self.betting_state.reset()
        self.hole_scores = {p.id: None for p in self.player_manager.players}
        self.gross_scores = {p.id: None for p in self.player_manager.players}
        self.game_status_message = "Players set. Time to toss the tees!"
        self.player_float_used = {p.id: False for p in self.player_manager.players}
        self.carry_over = False
        self.hole_history = []
        self._last_points = {p.id: 0 for p in self.player_manager.players}
        if course_name:
            self.course_manager.load_course(course_name)
        else:
            self.course_manager = CourseManager()
        self._save_to_db()

    def get_courses(self):
        return self.course_manager.get_courses()

    def add_course(self, course_data):
        """Add a new course with validation"""
        name = course_data["name"]
        courses = self.course_manager.get_courses()
        if name in courses:
            raise ValueError(f"Course '{name}' already exists")
        
        holes = course_data["holes"]
        if len(holes) != 18:
            raise ValueError("Course must have exactly 18 holes")
        
        # Validate hole data
        for hole in holes:
            if not all(k in hole for k in ["hole_number", "par", "yards", "stroke_index"]):
                raise ValueError("Each hole must have hole_number, par, yards, and stroke_index")
        
        # Check for unique handicaps and hole numbers
        handicaps = [h["stroke_index"] for h in holes]
        hole_numbers = [h["hole_number"] for h in holes]
        
        if len(set(handicaps)) != 18 or set(handicaps) != set(range(1, 19)):
            raise ValueError("Stroke indexes must be unique and range from 1 to 18")
        
        if len(set(hole_numbers)) != 18 or set(hole_numbers) != set(range(1, 19)):
            raise ValueError("Hole numbers must be unique and range from 1 to 18")
        
        # Sort holes by hole number for consistency
        sorted_holes = sorted(holes, key=lambda h: h["hole_number"])
        self.course_manager.add_course(name, sorted_holes)
        return True

    def delete_course(self, course_name):
        """Delete a course"""
        self.course_manager.delete_course(course_name)
        return True

    def update_course(self, course_name, course_data):
        """Update an existing course"""
        courses = self.course_manager.get_courses()
        if course_name not in courses:
            raise ValueError(f"Course '{course_name}' not found")
        
        # If renaming, check new name doesn't exist
        new_name = course_data.get("name", course_name)
        if new_name != course_name and new_name in courses:
            raise ValueError(f"Course '{new_name}' already exists")
        
        # Update course data
        if "holes" in course_data:
            holes = course_data["holes"]
            if len(holes) != 18:
                raise ValueError("Course must have exactly 18 holes")
            
            # Validate as in add_course
            handicaps = [h["stroke_index"] for h in holes]
            hole_numbers = [h["hole_number"] for h in holes]
            
            if len(set(handicaps)) != 18 or set(handicaps) != set(range(1, 19)):
                raise ValueError("Stroke indexes must be unique and range from 1 to 18")
            
            if len(set(hole_numbers)) != 18 or set(hole_numbers) != set(range(1, 19)):
                raise ValueError("Hole numbers must be unique and range from 1 to 18")
            
            sorted_holes = sorted(holes, key=lambda h: h["hole_number"])
            
            # If renaming, delete old and add new
            if new_name != course_name:
                self.course_manager.delete_course(course_name)
                self.course_manager.add_course(new_name, sorted_holes)
            else:
                self.course_manager.update_course(course_name, sorted_holes)
        
        return True

    def get_course_stats(self, course_name):
        """Get statistics for a course"""
        return self.course_manager.get_course_stats(course_name)

    def get_current_hole_info(self):
        """Get detailed information about the current hole"""
        if not hasattr(self, 'current_hole') or self.current_hole is None:
            return None
        
        return self.course_manager.get_current_hole_info(self.current_hole)

    def get_hole_difficulty_factor(self, hole_number):
        """Calculate difficulty factor for a specific hole for simulation"""
        return self.course_manager.get_hole_difficulty_factor(hole_number)
    
    def get_human_player_id(self) -> str:
        """Get the human player ID using centralized utility"""
        return Player.get_human_player_id(self.player_manager.players)

    def get_state(self):
        """Get the current game state as a dictionary"""
        return self._serialize()

# Singleton game state for MVP (in-memory)
game_state = GameState() 