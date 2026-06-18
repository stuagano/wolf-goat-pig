"""Fixtures for the live external-service suite.

Every test here is marked `live` and hits a REAL external API, read-only.
Tests skip (never fail) when their service's credentials/targets are absent
(see _helpers.require_env), so a partial or empty credential set runs cleanly.
"""

import pytest


@pytest.fixture(autouse=True)
def _mark_all_live(request):
    # Defense in depth: ensure everything in tests/live is treated as live
    # even if a module forgets the module-level marker.
    request.node.add_marker(pytest.mark.live)
