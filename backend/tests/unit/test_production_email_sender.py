"""Production must send from a verified domain, not Resend's sandbox sender.

`onboarding@resend.dev` only delivers to the Resend account owner; every other
recipient is rejected (and the provider swallows the failure). That silently
limited all production email to one person from March to October 2026.
"""

from pathlib import Path

import yaml

ENV_FILE = Path(__file__).resolve().parents[3] / "deploy/gcp/phase1-cloud-run/env.production.yaml"


def test_production_from_email_uses_verified_domain():
    env = yaml.safe_load(ENV_FILE.read_text())

    assert env["EMAIL_PROVIDER"] == "resend"
    domain = env["FROM_EMAIL"].rsplit("@", 1)[-1]
    assert domain != "resend.dev", "resend.dev is the sandbox sender; it only delivers to the account owner"
    assert domain == "wolfgoatpig.com"
