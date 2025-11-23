"""Utilities for synchronizing daily sign-up activity with the legacy CGI sheet.

The production workflow still depends on https://thousand-cranes.com/WolfGoatPig/
wgp_tee_sheet.cgi. We expose a light-weight client that can mirror create, update,
and cancel operations back to that system so that operators can trial the new
application without breaking the existing sign-up board.

All configuration is handled through environment variables so we do not have to
hardcode any deployment-specific constants. The client is intentionally
extensible—field mappings, constant form values, and payload format (JSON vs.
`application/x-www-form-urlencoded`) can all be tuned without code changes.

Example configuration (added to ``.env``)::

    LEGACY_SIGNUP_SYNC_ENABLED=true
    LEGACY_SIGNUP_CREATE_URL=https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi
    LEGACY_SIGNUP_CANCEL_URL=https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi
    LEGACY_SIGNUP_FIELD_MAP={"player_name": "player", "date": "signup_date"}
    LEGACY_SIGNUP_EXTRA_FIELDS={"sheet_id": "wing-point"}

The service is best-effort; failures are logged but never bubble up to the API
layer. This ensures we never block modern clients just because the legacy CGI is
offline.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


def _load_json_env(var_name: str) -> Dict[str, Any]:
    """Parse a JSON object from an environment variable.

    Returns an empty dictionary when the variable is not set or contains invalid
    JSON. We log malformed content because it usually indicates a configuration
    typo.
    """

    raw_value = os.getenv(var_name, "")
    if not raw_value:
        return {}

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        logger.warning("Unable to parse %s as JSON. Raw value: %s", var_name, raw_value)
        return {}

    if isinstance(parsed, dict):
        return parsed

    logger.warning(
        "Expected a JSON object for %s but received %s. Defaulting to empty mapping.",
        var_name,
        type(parsed).__name__,
    )
    return {}


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    """Coerce an environment string into a boolean value."""

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: Optional[str], default: float) -> float:
    """Safely parse a floating point configuration value."""

    if not value:
        return default

    try:
        return float(value)
    except ValueError:
        logger.warning("Invalid float value '%s'; using default %s", value, default)
        return default


@dataclass(frozen=True)
class LegacySignupConfig:
    """Runtime configuration for :class:`LegacySignupSyncService`."""

    enabled: bool = False
    create_url: Optional[str] = None
    update_url: Optional[str] = None
    cancel_url: Optional[str] = None
    timeout_seconds: float = 10.0
    api_key: Optional[str] = None
    payload_format: str = "form"  # ``form`` or ``json``
    field_map: Dict[str, str] = field(default_factory=dict)
    extra_fields: Dict[str, Any] = field(default_factory=dict)
    create_action_field: Optional[str] = "action"
    create_action_value: Optional[str] = "add"
    update_action_field: Optional[str] = "action"
    update_action_value: Optional[str] = "update"
    cancel_action_field: Optional[str] = "action"
    cancel_action_value: Optional[str] = "cancel"

    @classmethod
    def from_env(cls) -> LegacySignupConfig:
        """Construct configuration from process environment variables."""

        payload_format = os.getenv("LEGACY_SIGNUP_PAYLOAD_FORMAT", "form").strip().lower()
        if payload_format not in {"form", "json"}:
            logger.warning(
                "Unsupported LEGACY_SIGNUP_PAYLOAD_FORMAT '%s'; defaulting to 'form'",
                payload_format,
            )
            payload_format = "form"

        config = cls(
            enabled=_as_bool(os.getenv("LEGACY_SIGNUP_SYNC_ENABLED")),
            create_url=os.getenv("LEGACY_SIGNUP_CREATE_URL"),
            update_url=os.getenv("LEGACY_SIGNUP_UPDATE_URL") or os.getenv("LEGACY_SIGNUP_CREATE_URL"),
            cancel_url=os.getenv("LEGACY_SIGNUP_CANCEL_URL") or os.getenv("LEGACY_SIGNUP_CREATE_URL"),
            timeout_seconds=_as_float(os.getenv("LEGACY_SIGNUP_TIMEOUT_SECONDS"), 10.0),
            api_key=os.getenv("LEGACY_SIGNUP_API_KEY"),
            payload_format=payload_format,
            field_map=_load_json_env("LEGACY_SIGNUP_FIELD_MAP"),
            extra_fields=_load_json_env("LEGACY_SIGNUP_EXTRA_FIELDS"),
            create_action_field=os.getenv("LEGACY_SIGNUP_CREATE_ACTION_FIELD", "action"),
            create_action_value=os.getenv("LEGACY_SIGNUP_CREATE_ACTION_VALUE", "add"),
            update_action_field=os.getenv("LEGACY_SIGNUP_UPDATE_ACTION_FIELD", "action"),
            update_action_value=os.getenv("LEGACY_SIGNUP_UPDATE_ACTION_VALUE", "update"),
            cancel_action_field=os.getenv("LEGACY_SIGNUP_CANCEL_ACTION_FIELD", "action"),
            cancel_action_value=os.getenv("LEGACY_SIGNUP_CANCEL_ACTION_VALUE", "cancel"),
        )

        return config


class LegacySignupSyncService:
    """Best-effort synchronization client for the legacy tee sheet."""

    def __init__(self, config: LegacySignupConfig) -> None:
        self.config = config

    def sync_signup_created(self, signup: Any) -> bool:
        """Mirror a newly created signup to the legacy CGI."""

        return self._sync(
            signup,
            target_url=self.config.create_url,
            action_field=self.config.create_action_field,
            action_value=self.config.create_action_value,
        )

    def sync_signup_updated(self, signup: Any) -> bool:
        """Mirror updates for an existing signup."""

        return self._sync(
            signup,
            target_url=self.config.update_url,
            action_field=self.config.update_action_field,
            action_value=self.config.update_action_value,
        )

    def sync_signup_cancelled(self, signup: Any) -> bool:
        """Mirror a cancellation event to the legacy CGI."""

        return self._sync(
            signup,
            target_url=self.config.cancel_url,
            action_field=self.config.cancel_action_field,
            action_value=self.config.cancel_action_value,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _sync(
        self,
        signup: Any,
        *,
        target_url: Optional[str],
        action_field: Optional[str],
        action_value: Optional[str],
    ) -> bool:
        if not self.config.enabled:
            return False

        if not target_url:
            logger.debug("Legacy signup sync skipped: no target URL configured")
            return False

        payload = self.build_payload(signup, action_field, action_value)

        if not payload:
            logger.debug("Legacy signup sync skipped: empty payload for signup id=%s", getattr(signup, "id", "<unknown>"))
            return False

        headers: Dict[str, str] = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        try:
            with httpx.Client(timeout=self.config.timeout_seconds, follow_redirects=True) as client:
                if self.config.payload_format == "json":
                    response = client.post(target_url, json=payload, headers=headers)
                else:
                    response = client.post(target_url, data=payload, headers=headers)

                response.raise_for_status()

            logger.debug(
                "Legacy signup sync succeeded for signup id=%s (fields=%s)",
                getattr(signup, "id", "<unknown>"),
                sorted(payload.keys()),
            )
            return True
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Legacy signup sync returned HTTP %s for signup id=%s: %s",
                exc.response.status_code,
                getattr(signup, "id", "<unknown>"),
                exc.response.text,
            )
        except httpx.RequestError as exc:
            logger.warning(
                "Legacy signup sync failed for signup id=%s: %s",
                getattr(signup, "id", "<unknown>"),
                exc,
            )

        return False

    def build_payload(
        self,
        signup: Any,
        action_field: Optional[str],
        action_value: Optional[str],
    ) -> Dict[str, Any]:
        """Translate our signup model into the legacy CGI payload schema."""

        base_payload: Dict[str, Any] = {}

        attribute_map = {
            "date": getattr(signup, "date", None),
            "player_name": getattr(signup, "player_name", None),
            "player_profile_id": getattr(signup, "player_profile_id", None),
            "preferred_start_time": getattr(signup, "preferred_start_time", None),
            "notes": getattr(signup, "notes", None),
            "status": getattr(signup, "status", None),
        }

        for attribute, value in attribute_map.items():
            if value is None or value == "":
                continue

            field_name = self.config.field_map.get(attribute, attribute)
            base_payload[field_name] = value

        # Only add the action marker if both the field and value are provided.
        if action_field and action_value is not None:
            resolved_field = self.config.field_map.get(action_field, action_field)
            base_payload[resolved_field] = action_value

        # Merge any static extra fields (e.g., sheet identifier)
        for key, value in self.config.extra_fields.items():
            if key not in base_payload and value is not None:
                base_payload[key] = value

        return base_payload


_legacy_signup_service: Optional[LegacySignupSyncService] = None


def get_legacy_signup_service() -> LegacySignupSyncService:
    """Return a process-wide singleton instance of the sync service."""

    global _legacy_signup_service
    if _legacy_signup_service is None:
        _legacy_signup_service = LegacySignupSyncService(LegacySignupConfig.from_env())
    return _legacy_signup_service


def reset_legacy_signup_service() -> None:
    """Reset the cached service instance.

    Primarily used in tests where we want to re-read environment variables after
    mutating ``os.environ``.
    """

    global _legacy_signup_service
    _legacy_signup_service = None

