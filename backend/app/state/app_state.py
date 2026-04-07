"""Application-level shared state — lazy-initialized singletons.

Routers import getters from here instead of reaching into main.py globals.
main.py lifespan sets values at startup via the setters.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..post_hole_analytics import PostHoleAnalyzer
    from ..state.course_manager import CourseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Post-Hole Analyzer
# ---------------------------------------------------------------------------
_post_hole_analyzer: PostHoleAnalyzer | None = None


def get_post_hole_analyzer() -> PostHoleAnalyzer | None:
    return _post_hole_analyzer


def set_post_hole_analyzer(v: PostHoleAnalyzer) -> None:
    global _post_hole_analyzer
    _post_hole_analyzer = v


# ---------------------------------------------------------------------------
# Course Manager
# ---------------------------------------------------------------------------
_course_manager: CourseManager | None = None


def get_course_manager() -> CourseManager | None:
    return _course_manager


def set_course_manager(v: CourseManager) -> None:
    global _course_manager
    _course_manager = v


# ---------------------------------------------------------------------------
# Email Scheduler (initialized on demand)
# ---------------------------------------------------------------------------
_email_scheduler: Any = None


def get_email_scheduler() -> Any:
    return _email_scheduler


def set_email_scheduler(v: Any) -> None:
    global _email_scheduler
    _email_scheduler = v


# ---------------------------------------------------------------------------
# Email Service Instance
# ---------------------------------------------------------------------------
_email_service_instance: Any = None


def get_email_service_instance() -> Any:
    return _email_service_instance


def set_email_service_instance(v: Any) -> None:
    global _email_service_instance
    _email_service_instance = v
