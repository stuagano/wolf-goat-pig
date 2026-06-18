"""Live probe for GroupMe: the access token is valid and the configured group
is visible. Skips unless GROUPME_ACCESS_TOKEN + GROUPME_GROUP_ID are set.
Read-only — never posts a message."""

import pytest
from ctk import claim_vs_reality

from app.services import groupme_service
from tests.live._helpers import require_env

pytestmark = pytest.mark.live


def test_groupme_token_valid_and_group_visible():
    env = require_env("GROUPME_ACCESS_TOKEN", "GROUPME_GROUP_ID")
    groups = groupme_service.list_groups()  # real read-only call

    def group_is_visible():
        ids = {str(g.get("id")) for g in groups}
        assert env["GROUPME_GROUP_ID"] in ids, f"configured group {env['GROUPME_GROUP_ID']} not in visible groups {ids}"

    claim_vs_reality(
        claimed_success=bool(groups),
        verifier=group_is_visible,
        claim_label="groupme list_groups",
    )
