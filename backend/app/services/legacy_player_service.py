"""Service for managing and validating players against the legacy tee sheet system.

The legacy system at thousand-cranes.com/WolfGoatPig only accepts signups for
players that exist in its dropdown list. This service provides:

1. A cached list of known legacy players
2. Validation to check if a player name will work with the legacy system
3. Fuzzy matching to suggest corrections for misspelled names
"""

from __future__ import annotations

import json
import logging
from difflib import get_close_matches
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Path to the static player list
_PLAYERS_FILE = Path(__file__).parent.parent / "data" / "legacy_players.json"

# Cached player data
_players_cache: Optional[List[str]] = None
_players_cache_lower: Optional[dict] = None  # lowercase -> original mapping


def _load_players() -> List[str]:
    """Load the player list from the JSON file."""
    global _players_cache, _players_cache_lower

    if _players_cache is not None:
        return _players_cache

    try:
        with open(_PLAYERS_FILE, "r") as f:
            data = json.load(f)
            _players_cache = data.get("players", [])
            # Build lowercase lookup for case-insensitive matching
            _players_cache_lower = {p.lower(): p for p in _players_cache}
            logger.info(f"Loaded {len(_players_cache)} legacy players from {_PLAYERS_FILE}")
            return _players_cache
    except FileNotFoundError:
        logger.warning(f"Legacy players file not found: {_PLAYERS_FILE}")
        _players_cache = []
        _players_cache_lower = {}
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in legacy players file: {e}")
        _players_cache = []
        _players_cache_lower = {}
        return []


def get_legacy_players() -> List[str]:
    """Return the list of all known legacy players."""
    return _load_players()


def is_valid_legacy_player(name: str) -> bool:
    """Check if a player name exists in the legacy system (case-insensitive)."""
    _load_players()
    return name.lower() in _players_cache_lower


def get_canonical_name(name: str) -> Optional[str]:
    """Get the canonical (correctly cased) name for a player.

    Returns None if the player is not found.
    """
    _load_players()
    return _players_cache_lower.get(name.lower())


def find_similar_players(name: str, max_results: int = 5) -> List[str]:
    """Find players with names similar to the given name.

    Useful for suggesting corrections when a name doesn't match exactly.
    """
    players = _load_players()
    if not players:
        return []

    # Use difflib for fuzzy matching
    matches = get_close_matches(name.lower(), [p.lower() for p in players], n=max_results, cutoff=0.6)

    # Return the original-cased versions
    return [_players_cache_lower[m] for m in matches]


def validate_player_for_legacy(name: str) -> dict:
    """Validate a player name for legacy system compatibility.

    Returns a dict with:
    - valid: bool - whether the name is valid
    - canonical_name: str or None - the correctly-cased name if valid
    - suggestions: list - similar names if not valid
    - message: str - human-readable explanation
    """
    canonical = get_canonical_name(name)

    if canonical:
        return {
            "valid": True,
            "canonical_name": canonical,
            "suggestions": [],
            "message": f"Player '{canonical}' found in legacy system",
        }

    suggestions = find_similar_players(name)

    if suggestions:
        return {
            "valid": False,
            "canonical_name": None,
            "suggestions": suggestions,
            "message": f"Player '{name}' not found. Did you mean: {', '.join(suggestions)}?",
        }

    return {
        "valid": False,
        "canonical_name": None,
        "suggestions": [],
        "message": f"Player '{name}' not found in legacy system",
    }


def reload_players() -> int:
    """Force reload of the player list from disk.

    Returns the number of players loaded.
    """
    global _players_cache, _players_cache_lower
    _players_cache = None
    _players_cache_lower = None
    players = _load_players()
    return len(players)
