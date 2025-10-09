"""Utility functions for preparing Sunday game pairings with randomness support."""

import logging
import os
from random import Random, SystemRandom
from typing import Dict, List, Optional

from .team_formation_service import TeamFormationService

logger = logging.getLogger(__name__)

SUNDAY_GAME_SEED_ENV = "SUNDAY_GAME_RANDOM_SEED"


def _resolve_seed(explicit_seed: Optional[int]) -> Optional[int]:
    """Determine the random seed from an explicit value or environment variable."""
    if explicit_seed is not None:
        return explicit_seed

    env_value = os.getenv(SUNDAY_GAME_SEED_ENV)
    if not env_value:
        return None

    try:
        return int(env_value)
    except ValueError:
        logger.warning(
            "Invalid %s value '%s'. Falling back to non-deterministic randomness.",
            SUNDAY_GAME_SEED_ENV,
            env_value
        )
        return None


def _build_rng(seed: Optional[int], salt: int = 0) -> Random:
    """Create a Random instance using the provided seed and optional salt."""
    if seed is None:
        system_seed = SystemRandom().randrange(0, 2**32)
        return Random(system_seed)

    return Random(seed + salt)


def generate_sunday_pairings(
    players: List[Dict],
    *,
    num_rotations: int = 3,
    seed: Optional[int] = None
) -> Dict:
    """Generate randomized Sunday pairings and select one rotation when multiple exist."""
    if len(players) < 4:
        logger.info("Sunday pairings requested with insufficient players: %s", len(players))
        resolved_seed = _resolve_seed(seed)
        return {
            "player_count": len(players),
            "remaining_players": len(players),
            "rotations": [],
            "selected_rotation": None,
            "total_rotations": 0,
            "random_seed": resolved_seed,
        }

    resolved_seed = _resolve_seed(seed)

    safe_rotation_count = max(num_rotations, 1)
    rotations = TeamFormationService.create_team_pairings_with_rotations(
        players,
        num_rotations=safe_rotation_count,
        seed=resolved_seed,
    )

    if not rotations:
        return {
            "player_count": len(players),
            "remaining_players": len(players) % 4,
            "rotations": [],
            "selected_rotation": None,
            "total_rotations": 0,
            "random_seed": resolved_seed,
        }

    selection_rng = _build_rng(resolved_seed, salt=len(rotations))
    selected_rotation = selection_rng.choice(rotations)

    logger.info(
        "Generated %s Sunday rotations (seed=%s). Selected rotation %s.",
        len(rotations),
        resolved_seed,
        selected_rotation.get("rotation_number") if isinstance(selected_rotation, dict) else "unknown",
    )

    return {
        "player_count": len(players),
        "remaining_players": len(players) % 4,
        "rotations": rotations,
        "selected_rotation": selected_rotation,
        "total_rotations": len(rotations),
        "random_seed": resolved_seed,
    }
