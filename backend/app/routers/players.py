"""Players router — aggregates the /players route modules.

Player profile management, statistics, analytics, availability, and preferences.
The routes live in players_directory, players_me, players_by_id, players_stats and
players_preferences (avatar helpers in players_avatar); this module includes them,
after the admin sub-routers, so ``app.include_router(players.router)`` registers the
same surface in the same order as before. Order matters: the static paths
(``/all``, ``/name/...``, ``/availability/all``, ``/me/...``) must be registered
before the parameterised ``/{player_id}`` routes.
Names are re-exported so existing ``from app.routers.players import X`` keeps working.
"""

from fastapi import APIRouter

from . import players_by_id, players_directory, players_me, players_preferences, players_stats
from .account_claims import router as account_claims_router
from .account_links import router as account_links_router
from .admin_grants import router as admin_grants_router
from .my_name import router as my_name_router
from .players_avatar import (
    AVATAR_ALLOWED_TYPES,
    AVATAR_MAX_DIM,
    AVATAR_MAX_UPLOAD_BYTES,
    _avatar_jpeg_for_player,
    _downscale_avatar_jpeg,
)
from .players_by_id import (
    delete_player_profile,
    get_player_avatar,
    get_player_profile,
    get_public_player_profile,
    update_player_profile,
)
from .players_directory import (
    create_player_profile,
    get_all_player_profiles,
    get_all_players,
    get_all_players_availability,
    get_player_profile_by_name,
)
from .players_me import (
    get_my_availability,
    get_my_email_preferences,
    get_my_profile,
    set_my_availability,
    update_my_description,
    update_my_email_preferences,
    update_my_legacy_name,
    update_my_venmo,
    upload_my_avatar,
)
from .players_preferences import (
    _require_self_or_admin,
    get_email_preferences,
    get_player_availability,
    set_player_availability,
    update_email_preferences,
)
from .players_stats import (
    get_all_head_to_head,
    get_head_to_head,
    get_player_advanced_metrics,
    get_player_analytics,
    get_player_insights,
    get_player_profile_with_stats,
    get_player_skill_rating,
    get_player_statistics,
    get_player_trends,
    get_score_performance_analytics,
    get_special_event_analytics,
    get_streak_analysis,
)

router = APIRouter()
# Admin sub-routers carry their own "/admin..." prefix; mount them under /players.
router.include_router(account_links_router, prefix="/players", tags=["players"])
router.include_router(admin_grants_router, prefix="/players", tags=["players"])
router.include_router(account_claims_router, prefix="/players", tags=["players"])
router.include_router(my_name_router, prefix="/players", tags=["players"])
# Static paths first, then the parameterised /{player_id} routes.
router.include_router(players_directory.router)
router.include_router(players_me.router)
router.include_router(players_by_id.router)
router.include_router(players_stats.router)
router.include_router(players_preferences.router)

__all__ = [
    "AVATAR_ALLOWED_TYPES",
    "AVATAR_MAX_DIM",
    "AVATAR_MAX_UPLOAD_BYTES",
    "_avatar_jpeg_for_player",
    "_downscale_avatar_jpeg",
    "_require_self_or_admin",
    "create_player_profile",
    "delete_player_profile",
    "get_all_head_to_head",
    "get_all_player_profiles",
    "get_all_players",
    "get_all_players_availability",
    "get_email_preferences",
    "get_head_to_head",
    "get_my_availability",
    "get_my_email_preferences",
    "get_my_profile",
    "get_player_advanced_metrics",
    "get_player_analytics",
    "get_player_availability",
    "get_player_avatar",
    "get_player_insights",
    "get_player_profile",
    "get_player_profile_by_name",
    "get_player_profile_with_stats",
    "get_player_skill_rating",
    "get_player_statistics",
    "get_player_trends",
    "get_public_player_profile",
    "get_score_performance_analytics",
    "get_special_event_analytics",
    "get_streak_analysis",
    "router",
    "set_my_availability",
    "set_player_availability",
    "update_email_preferences",
    "update_my_description",
    "update_my_email_preferences",
    "update_my_legacy_name",
    "update_my_venmo",
    "update_player_profile",
    "upload_my_avatar",
]
