from typing import Any

from pydantic import BaseModel


class GameSetupRequest(BaseModel):
    players: list[str]
    course_name: str
    game_settings: dict[str, Any] | None = None


class OddsCalculationRequest(BaseModel):
    players: list[dict[str, Any]]
    hole_info: dict[str, Any]
    current_state: dict[str, Any] | None = None


class ShotAnalysisRequest(BaseModel):
    player_id: str
    distance_to_pin: float
    lie_type: str
    club_options: list[str]
