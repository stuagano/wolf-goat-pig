#!/usr/bin/env python3
"""Manually exercise the legacy tee sheet bridge.

This helper is intended for operators who want to verify that the backend can
POST to the remote CGI (or a proxy that fronts it) without booting the full
FastAPI stack. The script reuses :mod:`backend.app.services.legacy_signup_service`
configuration so we stay DRY—environment variables remain the single source of
truth.

Example::

    LEGACY_SIGNUP_SYNC_ENABLED=true \
    LEGACY_SIGNUP_CREATE_URL=https://example.com/wgp_tee_sheet.cgi \
    LEGACY_SIGNUP_FIELD_MAP='{"player_name": "player"}' \
    python scripts/legacy_sync_probe.py \
      --date 2024-05-01 \
      --player-name "Test Golfer" \
      --preferred-start-time "07:30" \
      --notes "Preview signup" \
      --preview

The ``--preview`` flag prints the resolved payload without sending it so you can
confirm field mappings before mirroring real data.
"""

from __future__ import annotations

import argparse
import logging
import sys
from types import SimpleNamespace
from pathlib import Path

# Ensure the backend package is importable when the script is executed from the
# repository root without adjusting PYTHONPATH manually.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.legacy_signup_service import (  # noqa: E402
    LegacySignupConfig,
    LegacySignupSyncService,
)


def _build_signup_namespace(args: argparse.Namespace) -> SimpleNamespace:
    """Return a lightweight object matching the attributes used by the service."""

    return SimpleNamespace(
        id=args.signup_id,
        date=args.date,
        player_name=args.player_name,
        player_profile_id=args.player_profile_id,
        preferred_start_time=args.preferred_start_time,
        notes=args.notes,
        status=args.status,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Send a synthetic signup to the legacy CGI using the existing "
            "bridge configuration."
        )
    )
    parser.add_argument("--date", required=True, help="Signup date (YYYY-MM-DD)")
    parser.add_argument("--player-name", required=True, help="Player display name")
    parser.add_argument(
        "--player-profile-id",
        type=int,
        default=None,
        help="Optional internal profile identifier",
    )
    parser.add_argument(
        "--preferred-start-time",
        default=None,
        help="Optional preferred start time (HH:MM)",
    )
    parser.add_argument("--notes", default=None, help="Optional notes field")
    parser.add_argument(
        "--status",
        default="signed_up",
        help="Signup status to send to the legacy sheet",
    )
    parser.add_argument(
        "--signup-id",
        type=int,
        default=0,
        help="Identifier included in logs to trace the test signup",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the payload without posting to the remote CGI",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress info logs; useful in shell pipelines",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    config = LegacySignupConfig.from_env()
    if not config.enabled:
        logging.error(
            "LEGACY_SIGNUP_SYNC_ENABLED is not true; enable it in the environment before probing."
        )
        return 1

    service = LegacySignupSyncService(config)
    signup = _build_signup_namespace(args)

    if args.preview:
        payload = service.build_payload(
            signup,
            action_field=config.create_action_field,
            action_value=config.create_action_value,
        )
        logging.info("Preview payload: %s", payload)
        return 0

    logging.info("Posting signup %s to %s", signup.id, config.create_url)
    success = service.sync_signup_created(signup)
    if success:
        logging.info("Legacy CGI responded successfully")
        return 0

    logging.error("Legacy CGI call failed; check logs above for details")
    return 2


if __name__ == "__main__":
    sys.exit(main())
