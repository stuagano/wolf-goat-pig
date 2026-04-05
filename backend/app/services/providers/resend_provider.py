"""
Resend Email Provider

Sends emails via the Resend API using the `resend` Python SDK.
Duck-typed provider consumed by the unified EmailService.
"""

import logging
import os
import re
from typing import Any

import resend

logger = logging.getLogger(__name__)


class ResendEmailProvider:
    """Provider for sending emails using the Resend API."""

    def __init__(self, api_key: str, from_email: str, from_name: str):
        self.from_email = from_email
        self.from_name = from_name
        resend.api_key = api_key

    def is_configured(self) -> bool:
        return bool(resend.api_key and self.from_email)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        if not self.is_configured():
            logger.error("Resend provider is not configured. Cannot send email.")
            return False

        try:
            params: resend.Emails.SendParams = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_body,
            }
            if text_body:
                params["text"] = text_body
            else:
                params["text"] = self._html_to_text(html_body)

            resend.Emails.send(params)
            logger.info(f"Email sent successfully to {to_email} via Resend.")
            return True
        except Exception as e:
            logger.error(f"Error sending email via Resend to {to_email}: {e}")
            return False

    def get_configuration_status(self) -> dict[str, Any]:
        return {
            "provider": "resend",
            "configured": self.is_configured(),
            "from_email": self.from_email,
        }

    def _html_to_text(self, html: str) -> str:
        text = re.sub("<[^<]+?>", "", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text


def create_resend_provider() -> ResendEmailProvider | None:
    """Factory function to create a ResendEmailProvider instance."""
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL")
    from_name = os.getenv("FROM_NAME", "Wolf Goat Pig")

    if not api_key or not from_email:
        logger.warning("RESEND_API_KEY or FROM_EMAIL not set. Cannot create Resend provider.")
        return None

    return ResendEmailProvider(api_key=api_key, from_email=from_email, from_name=from_name)
