from typing import Dict, List
from dataclasses import dataclass, field
from ..domain.player import Player

@dataclass
class BettingState:
    """Manages all betting-related state and logic for Wolf Goat Pig"""
    teams: Dict = field(default_factory=dict)
    base_wager: int = 1
    doubled_status: bool = False
    game_phase: str = 'Regular'

    def reset(self):
        """Reset betting state for a new game"""
        self.teams = {}
        self.base_wager = 1
        self.doubled_status = False
        self.game_phase = 'Regular'

    def reset_hole(self):
        """Reset betting state for a new hole"""
        self.teams = {}
        self.doubled_status = False

    def request_partner(self, captain_id: str, partner_id: str) -> str:
        """Captain requests a specific player as partner"""
        self.teams = {"type": "pending", "captain": captain_id, "requested": partner_id}
        return "Partner requested."

    def accept_partner(self, partner_id: str, players: List[Player]) -> str:
        if self.teams.get("type") != "pending" or self.teams.get("requested") != partner_id:
            raise ValueError("No pending partner request for this player.")
        captain_id = self.teams["captain"]
        others = [p.id for p in players if p.id not in [captain_id, partner_id]]
        self.teams = {"type": "partners", "team1": [captain_id, partner_id], "team2": others}
        return "Partnership accepted."

    def decline_partner(self, partner_id: str, players: List[Player]) -> str:
        if self.teams.get("type") != "pending" or self.teams.get("requested") != partner_id:
            raise ValueError("No pending partner request for this player.")
        captain_id = self.teams["captain"]
        others = [p.id for p in players if p.id != captain_id]
        self.teams = {"type": "solo", "captain": captain_id, "opponents": others}
        self.base_wager *= 2  # On your own rule
        return "Partnership declined. Captain goes solo."

    def go_solo(self, captain_id: str, players: List[Player]) -> str:
        others = [p.id for p in players if p.id != captain_id]
        self.teams = {"type": "solo", "captain": captain_id, "opponents": others}
        self.base_wager *= 2
        return "Captain goes solo."

    def offer_double(self, offering_team_id: str, target_team_id: str) -> str:
        if self.doubled_status:
            raise ValueError("Double already offered or accepted on this hole.")
        self.doubled_status = True
        return "Double offered."

    def accept_double(self, team_id: str) -> str:
        if not self.doubled_status:
            raise ValueError("No double to accept.")
        self.base_wager *= 2
        self.doubled_status = False
        return "Double accepted."

    def decline_double(self, team_id: str) -> str:
        if not self.doubled_status:
            raise ValueError("No double to decline.")
        self.doubled_status = False
        return "Double declined. Offering team wins hole."

    def calculate_hole_points(self, hole_scores: Dict[str, int], players: List[Player]) -> str:
        if any(v is None for v in hole_scores.values()):
            raise ValueError("Not all scores entered.")
        if not self.teams or self.teams.get("type") not in ("partners", "solo"):
            raise ValueError("Teams not set for this hole.")
        base = self.base_wager
        msg = ""
        if self.teams["type"] == "partners":
            team1 = self.teams["team1"]
            team2 = self.teams["team2"]
            team1_score = min(hole_scores[pid] for pid in team1)
            team2_score = min(hole_scores[pid] for pid in team2)
            if team1_score < team2_score:
                msg = self._distribute_points_karl_marx(winners=team1, losers=team2, base=base, players=players)
            elif team2_score < team1_score:
                msg = self._distribute_points_karl_marx(winners=team2, losers=team1, base=base, players=players)
            else:
                msg = "Hole halved. No points awarded."
        elif self.teams["type"] == "solo":
            captain = self.teams["captain"]
            opponents = self.teams["opponents"]
            captain_score = hole_scores[captain]
            opp_score = min(hole_scores[pid] for pid in opponents)
            if captain_score < opp_score:
                msg = self._distribute_points_karl_marx(winners=[captain], losers=opponents, base=base, players=players)
            elif opp_score < captain_score:
                msg = self._distribute_points_karl_marx(winners=opponents, losers=[captain], base=base, players=players)
            else:
                msg = "Hole halved. No points awarded."
        else:
            msg = "Invalid team type for scoring."
        return msg

    def _distribute_points_karl_marx(self, winners: List[str], losers: List[str], base: int, players: List[Player]) -> str:
        n_win = len(winners)
        n_lose = len(losers)
        # Use the larger team size when calculating total quarters so that
        # asymmetric matchups (e.g., solo captain versus three opponents)
        # grant the expected base wager to each winner. This aligns the game
        # logic with the scoring rules exercised in the backend tests.
        total_quarters = base * max(n_win, n_lose)
        per_winner = total_quarters // n_win
        odd_quarters = total_quarters % n_win
        for p in players:
            if p.id in winners:
                p.add_points(per_winner)
            elif p.id in losers:
                p.add_points(-base)
        msg = f"{' & '.join(self._player_name(pid, players) for pid in winners)} win {per_winner} quarter(s) each."
        if odd_quarters > 0:
            winner_points = [(p.id, p.points) for p in players if p.id in winners]
            min_points = min(points for _, points in winner_points)
            lowest = [pid for pid, points in winner_points if points == min_points]
            if len(lowest) == 1:
                for p in players:
                    if p.id == lowest[0]:
                        p.add_points(odd_quarters)
                msg += f" Karl Marx rule: {self._player_name(lowest[0], players)} receives {odd_quarters} extra quarter(s)."
            else:
                msg += f" Karl Marx rule: Odd quarter(s) ({odd_quarters}) in limbo (tie among: {' & '.join(self._player_name(pid, players) for pid in lowest)})."
        return msg

    def _player_name(self, pid: str, players: List[Player]) -> str:
        for p in players:
            if p.id == pid:
                return p.name
        return pid

    def dispatch_action(self, action: str, payload: dict, players: List[Player]) -> str:
        if action == "request_partner":
            return self.request_partner(payload.get("captain_id"), payload.get("partner_id"))
        elif action == "accept_partner":
            return self.accept_partner(payload.get("partner_id"), players)
        elif action == "decline_partner":
            return self.decline_partner(payload.get("partner_id"), players)
        elif action == "go_solo":
            return self.go_solo(payload.get("captain_id"), players)
        elif action == "offer_double":
            return self.offer_double(payload.get("offering_team_id"), payload.get("target_team_id"))
        elif action == "accept_double":
            return self.accept_double(payload.get("team_id"))
        elif action == "decline_double":
            return self.decline_double(payload.get("team_id"))
        else:
            raise ValueError(f"Unknown betting action: {action}")

    def get_betting_tips(self, players: List[Player], current_hole: int, player_float_used: Dict[str, bool], carry_over: bool) -> List[str]:
        tips = []
        if self.doubled_status:
            tips.append("A double has been offered. If you're ahead, accepting can increase your winnings, but beware of a comeback! If you're behind, declining gives the other team the hole at the current stake.")
        if self.teams and self.teams.get("type") in ("partners", "solo") and not self.doubled_status:
            tips.append("Consider offering a double if you feel confident in your team's position, or to pressure the opponents.")
        if self.teams and self.teams.get("type") == "solo":
            tips.append("Going solo doubles the wager, but you must beat the best ball of the other three. Only go solo if you're confident in your shot or need to catch up.")
        points = [p.points for p in players]
        max_points = max(points)
        min_points = min(points)
        if max_points - min_points >= 6:
            leader = [p.name for p in players if p.points == max_points][0]
            trailer = [p.name for p in players if p.points == min_points][0]
            tips.append(f"{leader} is ahead by a large margin. Consider playing conservatively to protect your lead, or offer a double to pressure opponents. {trailer}, if you're behind, taking more risks (like going solo or accepting a double) can help you catch up.")
        captain_id = None
        for p in players:
            if hasattr(p, 'is_captain') and p.is_captain:
                captain_id = p.id
                break
        if captain_id and not player_float_used.get(captain_id, False):
            tips.append("You haven't used your float yet. Consider saving it for a high-stakes hole or when you're behind.")
            tips.append("The Option can be powerful if you're the captain and have lost the most quarters. Use it to double the wager and turn the tide.")
        if carry_over:
            tips.append("There's a carry-over in effect. The current hole is worth extra—play aggressively if you need to catch up, or defensively if you're ahead.")
        if current_hole >= 13:
            tips.append("On Hoepfinger or double-value holes, consider your risk tolerance before accepting or offering a double.")
        if current_hole >= 16:
            tips.append("On the final holes, consider the overall standings. Sometimes it's better to lock in a win than risk it all.")
            tips.append("If you're in contention for the Pettit Trophy, play conservatively on the last few holes.")
        if self.teams and self.teams.get("type") in ("partners", "solo"):
            n_win = 2 if self.teams["type"] == "partners" else 1
            n_lose = 2 if self.teams["type"] == "partners" else 3
            total_quarters = self.base_wager * n_lose
            if total_quarters % n_win != 0:
                tips.append("If quarters can't be divided evenly, the Karl Marx rule applies. The player furthest down will owe fewer quarters—factor this into your risk calculations.")
        tips.append("If the other team is offering a double, they may be bluffing. Consider their recent performance before accepting.")
        tips.append("Use table talk to gauge your opponents' confidence before making a big bet.")
        tips.append("Remember: If you decline a double, the offering team wins the hole at the current wager.")
        if current_hole >= 17:
            tips.append("Hoepfinger phase: The player furthest down chooses their spot in the rotation. Strategic position can be crucial!")
        return tips

    def to_dict(self) -> dict:
        return {
            "teams": self.teams,
            "base_wager": self.base_wager,
            "doubled_status": self.doubled_status,
            "game_phase": self.game_phase
        }

    def from_dict(self, data: dict):
        self.teams = data.get("teams", {})
        self.base_wager = data.get("base_wager", 1)
        self.doubled_status = data.get("doubled_status", False)
        self.game_phase = data.get("game_phase", 'Regular') 
