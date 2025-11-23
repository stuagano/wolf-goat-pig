"""
Unified Email Service for Wolf Goat Pig Application

Handles all email functionality using a provider-based strategy (SMTP or Gmail OAuth2).
"""

import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import emails
from jinja2 import Template

# Import the Gmail OAuth2 provider
from .providers.gmail_oauth2_provider import create_gmail_oauth2_provider

logger = logging.getLogger(__name__)

# --- Provider Abstract Base Class ---

class EmailProvider(ABC):
    """Abstract base class for an email provider."""
    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    def get_configuration_status(self) -> Dict[str, Any]:
        return {"provider": self.__class__.__name__, "configured": self.is_configured()}

# --- SMTP Provider Implementation ---

class SMTPEmailProvider(EmailProvider):
    """Email provider for sending emails via SMTP."""
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "Wolf Goat Pig")

    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_password and self.smtp_host)

    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        if not self.is_configured():
            logger.error("SMTP provider is not configured. Cannot send email.")
            return False
        try:
            message = emails.html(
                html=html_body,
                text=text_body or self._html_to_text(html_body),
                subject=subject,
                mail_from=(self.from_name, self.from_email)
            )
            response = message.send(
                to=to_email,
                smtp={
                    'host': self.smtp_host,
                    'port': self.smtp_port,
                    'tls': True,
                    'user': self.smtp_user,
                    'password': self.smtp_password
                }
            )
            if response.status_code in [250, 251, 252]:
                logger.info(f"Email sent successfully to {to_email} via SMTP.")
                return True
            else:
                logger.error(f"Failed to send email to {to_email} via SMTP. Status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error sending email via SMTP to {to_email}: {e}")
            return False

    def _html_to_text(self, html: str) -> str:
        text = re.sub('<[^<]+?>', '', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

# --- Unified Email Service ---

class EmailService:
    """A unified service for sending emails using a configured provider."""

    def __init__(self):
        self.provider: Optional[EmailProvider] = self._get_configured_provider()
        if not self.provider:
            logger.warning("No email provider is configured. Email functionality will be disabled.")

    def _get_configured_provider(self) -> Optional[EmailProvider]:
        """Determines which email provider to use based on environment variables."""
        email_provider_type = os.getenv("EMAIL_PROVIDER", "smtp").lower()

        if email_provider_type == "gmail_oauth2":
            logger.info("Using Gmail OAuth2 email provider.")
            return create_gmail_oauth2_provider()  # type: ignore[return-value]

        logger.info("Using SMTP email provider.")
        return SMTPEmailProvider()

    def is_configured(self) -> bool:
        return self.provider is not None and self.provider.is_configured()

    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        if not self.is_configured() or self.provider is None:
            logger.error("Email service is not configured. Cannot send email.")
            return False
        return self.provider.send_email(to_email, subject, html_body, text_body)

    def send_test_email(self, to_email: str, admin_name: str = "Admin") -> bool:
        """Sends a test email to verify the current provider's configuration."""
        provider_name = self.provider.__class__.__name__ if self.provider else "None"
        subject = f"Wolf Goat Pig - Test Email ({provider_name})"

        html_body = f"""
        <html><body>
            <h2>Wolf Goat Pig Email Test</h2>
            <p>Hello {admin_name},</p>
            <p>This is a test email from your Wolf Goat Pig application to verify that the <strong>{provider_name}</strong> is working correctly.</p>
            <p>If you received this, your configuration is correct!</p>
        </body></html>
        """
        text_body = f"Wolf Goat Pig Email Test\nHello {admin_name},\nThis is a test email to verify that the {provider_name} is working."

        return self._send_email(to_email, subject, html_body, text_body)

    def _get_base_template(self) -> str:
        """Returns the base HTML email template."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ subject }}</title>
        </head>
        <body>
            <div class="container">
                <div class="header"><h1>Wolf Goat Pig</h1></div>
                <div class="content">{{ content }}</div>
                <div class="footer"><p>Wing Point Golf & Country Club</p></div>
            </div>
        </body>
        </html>
        """

    def send_signup_confirmation(self, to_email: str, player_name: str, signup_date: str) -> bool:
        """Sends a signup confirmation email."""
        content = f"""
        <h2>Signup Confirmed!</h2>
        <p>Hi {player_name},</p>
        <p>You're all set for Wolf Goat Pig on <strong>{signup_date}</strong>.</p>
        """
        template = Template(self._get_base_template())
        html_body = template.render(subject="Golf Signup Confirmed", content=content)

        return self._send_email(
            to_email=to_email,
            subject=f"You're signed up for Wolf Goat Pig - {signup_date}",
            html_body=html_body
        )

    def send_daily_signup_reminder(self, to_email: str, player_name: str, available_dates: list[str]) -> bool:
        """Sends a daily signup reminder email."""
        dates_list = "".join([f"<li>{date}</li>" for date in available_dates])
        content = f"""
        <h2>Golf Signup Reminder</h2>
        <p>Hi {player_name},</p>
        <p>Don't forget to sign up for upcoming Wolf Goat Pig games:</p>
        <ul>{dates_list}</ul>
        """
        template = Template(self._get_base_template())
        html_body = template.render(subject="Golf Signup Reminder", content=content)

        return self._send_email(
            to_email=to_email,
            subject="Wolf Goat Pig - Signup Reminder",
            html_body=html_body
        )

    def send_weekly_summary(self, to_email: str, player_name: str, summary_data: dict[str, Any]) -> bool:
        """Sends a weekly summary email."""
        content = f"""
        <h2>Your Weekly Golf Summary</h2>
        <p>Hi {player_name},</p>
        <p>Here's your weekly performance summary:</p>
        <ul>
            <li>Games played: {summary_data.get('games_played', 0)}</li>
            <li>Total earnings: ${summary_data.get('total_earnings', 0):.2f}</li>
            <li>Win rate: {summary_data.get('win_rate', 0):.1f}%</li>
        </ul>
        """
        template = Template(self._get_base_template())
        html_body = template.render(subject="Weekly Golf Summary", content=content)

        return self._send_email(
            to_email=to_email,
            subject="Wolf Goat Pig - Weekly Summary",
            html_body=html_body
        )

    def send_game_invitation(self, to_email: str, player_name: str, inviter_name: str, game_date: str) -> bool:
        """Sends a game invitation email."""
        content = f"""
        <h2>You're Invited!</h2>
        <p>Hi {player_name},</p>
        <p>{inviter_name} has invited you to play Wolf Goat Pig on <strong>{game_date}</strong>.</p>
        <p>Join the game and have fun!</p>
        """
        template = Template(self._get_base_template())
        html_body = template.render(subject="Game Invitation", content=content)

        return self._send_email(
            to_email=to_email,
            subject=f"Wolf Goat Pig - Game Invitation for {game_date}",
            html_body=html_body
        )

    def get_provider_status(self) -> Dict[str, Any]:
        """Returns the configuration status of the current provider."""
        if not self.provider:
            return {"provider": "None", "configured": False}
        return self.provider.get_configuration_status()


# --- Global Service Instance ---

_email_service_instance: Optional[EmailService] = None

def get_email_service() -> EmailService:
    """Provides a singleton instance of the EmailService."""
    global _email_service_instance
    if _email_service_instance is None:
        _email_service_instance = EmailService()
    return _email_service_instance
