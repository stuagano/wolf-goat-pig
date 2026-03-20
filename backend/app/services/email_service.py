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
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
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

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        if not self.is_configured():
            logger.error("SMTP provider is not configured. Cannot send email.")
            return False
        try:
            message = emails.html(
                html=html_body,
                text=text_body or self._html_to_text(html_body),
                subject=subject,
                mail_from=(self.from_name, self.from_email),
            )
            response = message.send(
                to=to_email,
                smtp={
                    "host": self.smtp_host,
                    "port": self.smtp_port,
                    "tls": True,
                    "user": self.smtp_user,
                    "password": self.smtp_password,
                },
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
        text = re.sub("<[^<]+?>", "", html)
        text = re.sub(r"\s+", " ", text).strip()
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
            gmail_provider = create_gmail_oauth2_provider()
            # GmailOAuth2Provider is a subtype of EmailProvider
            return gmail_provider  # type: ignore

        logger.info("Using SMTP email provider.")
        return SMTPEmailProvider()

    def is_configured(self) -> bool:
        return self.provider is not None and self.provider.is_configured()

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        if not self.is_configured():
            logger.error("Email service is not configured. Cannot send email.")
            return False
        if self.provider is not None:
            return self.provider.send_email(to_email, subject, html_body, text_body)
        return False

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
            html_body=html_body,
        )

    def send_pairing_notification(
        self,
        to_email: str,
        player_name: str,
        game_date: str,
        teams: list,
        player_team_number: int | None = None,
    ) -> bool:
        """Sends the RNG pairing results to a player.

        Args:
            to_email: Player's email address
            player_name: Player's display name
            game_date: The game date (YYYY-MM-DD)
            teams: List of team dicts with players
            player_team_number: Which team this player is on (1-indexed), None if alternate
        """
        from datetime import datetime

        # Format the date nicely
        try:
            date_obj = datetime.strptime(game_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
        except ValueError:
            formatted_date = game_date

        # Build team HTML
        teams_html = ""
        for i, team in enumerate(teams, 1):
            team_players = team.get("players", [])
            player_names = [p.get("player_name", "Unknown") for p in team_players]
            is_player_team = i == player_team_number

            team_style = "background: #e8f5e9; border: 2px solid #28a745;" if is_player_team else "background: #f8f9fa;"
            team_label = " (Your Team!)" if is_player_team else ""

            teams_html += f"""
            <div style="margin: 10px 0; padding: 15px; border-radius: 8px; {team_style}">
                <strong style="color: #333;">Group {i}{team_label}</strong>
                <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                    {"".join(f'<li style="margin: 5px 0;">{name}</li>' for name in player_names)}
                </ul>
            </div>
            """

        # Personalized message
        if player_team_number:
            assignment_msg = f"<p style='font-size: 18px; color: #28a745;'><strong>You're in Group {player_team_number}!</strong></p>"
        else:
            assignment_msg = "<p style='color: #856404;'><strong>You're listed as an alternate.</strong> You'll play if someone can't make it.</p>"

        content = f"""
        <h2>🎲 Sunday Pairings Are In!</h2>
        <p>Hi {player_name},</p>
        <p>The RNG calculator has spoken! Here are your pairings for <strong>{formatted_date}</strong>:</p>

        {assignment_msg}

        <h3 style="margin-top: 25px;">All Groups:</h3>
        {teams_html}

        <p style="margin-top: 20px; padding: 15px; background: #e3f2fd; border-radius: 6px;">
            See you on the course! 🏌️
        </p>
        """

        template = Template(self._get_base_template())
        html_body = template.render(subject="Sunday Pairings", content=content)

        return self._send_email(
            to_email=to_email,
            subject=f"🎲 Your Sunday Golf Pairings - {formatted_date}",
            html_body=html_body,
        )

    def send_tee_time_request(
        self,
        to_email: str,
        game_date: str,
        teams: list,
        player_count: int,
        remaining_players: int = 0,
    ) -> bool:
        """Sends a tee time reservation request to the golf course.

        Args:
            to_email: Golf course email address
            game_date: The game date (YYYY-MM-DD)
            teams: List of team dicts with players
            player_count: Total number of players
            remaining_players: Number of alternates not in a full group
        """
        from datetime import datetime

        # Format the date nicely
        try:
            date_obj = datetime.strptime(game_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
            day_of_week = date_obj.strftime("%A")
        except ValueError:
            formatted_date = game_date
            day_of_week = "Sunday"

        # Build team/group HTML
        groups_html = ""
        for i, team in enumerate(teams, 1):
            team_players = team.get("players", [])
            player_names = [p.get("player_name", "Unknown") for p in team_players]

            groups_html += f"""
            <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #28a745;">
                <strong style="color: #333;">Group {i} ({len(player_names)} players)</strong>
                <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                    {"".join(f'<li style="margin: 5px 0;">{name}</li>' for name in player_names)}
                </ul>
            </div>
            """

        # Summary info
        alternates_note = ""
        if remaining_players > 0:
            alternates_note = (
                f"<p style='color: #856404;'><em>Plus {remaining_players} alternate(s) if space allows.</em></p>"
            )

        content = f"""
        <h2>Tee Time Request - {day_of_week} Wolf Goat Pig</h2>

        <p>Hi Dominic,</p>

        <p>We have <strong>{player_count} players</strong> signed up for Wolf Goat Pig on <strong>{formatted_date}</strong>.</p>

        <p>Could you please reserve <strong>{len(teams)} tee time(s)</strong> for us? Here are the groups:</p>

        {groups_html}

        {alternates_note}

        <p style="margin-top: 25px; padding: 15px; background: #e3f2fd; border-radius: 6px;">
            <strong>Preferred time:</strong> Afternoon (we're flexible on exact times)<br>
            <strong>Course:</strong> Wing Point Golf & Country Club
        </p>

        <p style="margin-top: 20px;">Thanks!</p>
        <p><em>- Wolf Goat Pig Automated System</em></p>
        """

        template = Template(self._get_base_template())
        html_body = template.render(subject="Tee Time Request", content=content)

        return self._send_email(
            to_email=to_email,
            subject=f"Tee Time Request: {len(teams)} groups for {formatted_date}",
            html_body=html_body,
        )

    # ========================================================================
    # Match / Availability Flow Emails
    # ========================================================================

    def send_match_found(
        self,
        to_email: str,
        player_name: str,
        match_day: str,
        overlap_start: str,
        overlap_end: str,
        suggested_tee_time: str,
        group_players: list[str],
        match_id: int,
        app_url: str = "",
    ) -> bool:
        """Sends an email when a new match group is found.

        Args:
            to_email: Recipient email
            player_name: Recipient's display name
            match_day: Day name (e.g. "Saturday")
            overlap_start: Start of availability overlap (e.g. "9:00 AM")
            overlap_end: End of availability overlap (e.g. "1:00 PM")
            suggested_tee_time: Suggested tee time (e.g. "9:00 AM")
            group_players: List of all player names in the group
            match_id: Database ID for the match suggestion
            app_url: Base URL of the app for deep links
        """
        other_players = [n for n in group_players if n != player_name]
        others_str = ", ".join(other_players[:-1]) + f" and {other_players[-1]}" if len(other_players) > 1 else other_players[0] if other_players else ""

        match_url = f"{app_url}/signup?tab=my-matches" if app_url else ""
        cta_html = f'<a href="{match_url}" style="display:inline-block;padding:12px 24px;background:#047857;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;margin-top:10px;">View Match &amp; Respond</a>' if match_url else ""

        players_html = "".join(
            f'<li style="margin:5px 0;font-size:15px;">{name}</li>'
            for name in group_players
        )

        content = f"""
        <h2>⛳ Golf Match Found!</h2>
        <p>Hi {player_name},</p>
        <p>Great news — we found a group that works for <strong>{match_day}</strong>! You've been matched with {others_str}.</p>

        <div style="margin:20px 0;padding:20px;background:#f0fdf4;border-radius:10px;border:1px solid #bbf7d0;">
            <div style="margin-bottom:12px;">
                <strong style="font-size:16px;color:#047857;">📅 {match_day}</strong>
            </div>
            <div style="margin-bottom:8px;color:#4b5563;">
                ⏰ <strong>Available window:</strong> {overlap_start} – {overlap_end}
            </div>
            <div style="margin-bottom:16px;color:#4b5563;">
                🎯 <strong>Suggested tee time:</strong> {suggested_tee_time}
            </div>
            <div>
                <strong style="color:#374151;">🏌️ Your group:</strong>
                <ul style="margin:8px 0 0 0;padding-left:20px;">
                    {players_html}
                </ul>
            </div>
        </div>

        <p>Everyone in this group is available during this window. Accept the match in the app and once everyone confirms, you'll be able to book a tee time together.</p>

        <div style="text-align:center;margin:25px 0;">
            {cta_html}
        </div>

        <p style="font-size:13px;color:#9ca3af;margin-top:20px;">
            This match will expire in 7 days if not accepted.
        </p>
        """
        template = Template(self._get_base_template())
        html_body = template.render(subject="Golf Match Found", content=content)

        return self._send_email(
            to_email=to_email,
            subject=f"⛳ Golf match found for {match_day} — {others_str}",
            html_body=html_body,
        )

    def send_match_confirmed(
        self,
        to_email: str,
        player_name: str,
        match_day: str,
        overlap_start: str,
        overlap_end: str,
        suggested_tee_time: str,
        group_players: list[str],
        app_url: str = "",
    ) -> bool:
        """Sends an email when all players have accepted a match."""
        others = [n for n in group_players if n != player_name]
        others_str = ", ".join(others[:-1]) + f" and {others[-1]}" if len(others) > 1 else others[0] if others else ""

        match_url = f"{app_url}/signup?tab=my-matches" if app_url else ""
        cta_html = f'<a href="{match_url}" style="display:inline-block;padding:12px 24px;background:#10b981;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;margin-top:10px;">Book Your Tee Time</a>' if match_url else ""

        content = f"""
        <h2>🎉 Everyone's In!</h2>
        <p>Hi {player_name},</p>
        <p>All players have confirmed the <strong>{match_day}</strong> match. Your group with {others_str} is locked in!</p>

        <div style="margin:20px 0;padding:20px;background:#ecfdf5;border-radius:10px;border:2px solid #10b981;">
            <div style="font-size:16px;font-weight:700;color:#047857;margin-bottom:12px;">
                Match Confirmed ✓
            </div>
            <div style="color:#4b5563;margin-bottom:6px;">
                📅 <strong>{match_day}</strong> · {overlap_start} – {overlap_end}
            </div>
            <div style="color:#4b5563;">
                🎯 Suggested tee time: <strong>{suggested_tee_time}</strong>
            </div>
        </div>

        <p><strong>Next step:</strong> Head to the app to book your tee time on ForeTees. The booking page will show available slots within your group's time window.</p>

        <div style="text-align:center;margin:25px 0;">
            {cta_html}
        </div>
        """
        template = Template(self._get_base_template())
        html_body = template.render(subject="Match Confirmed", content=content)

        return self._send_email(
            to_email=to_email,
            subject=f"🎉 {match_day} golf match confirmed — time to book!",
            html_body=html_body,
        )

    def send_match_declined(
        self,
        to_email: str,
        player_name: str,
        decliner_name: str,
        match_day: str,
        app_url: str = "",
    ) -> bool:
        """Sends an email when someone declines a match."""
        match_url = f"{app_url}/signup?tab=my-matches" if app_url else ""
        cta_html = f'<a href="{match_url}" style="display:inline-block;padding:12px 24px;background:#047857;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;margin-top:10px;">Check for New Matches</a>' if match_url else ""

        content = f"""
        <h2>Match Update</h2>
        <p>Hi {player_name},</p>
        <p>{decliner_name} can't make the <strong>{match_day}</strong> match. No worries — we'll keep looking for new groups that work for your schedule.</p>

        <div style="text-align:center;margin:25px 0;">
            {cta_html}
        </div>

        <p style="font-size:13px;color:#9ca3af;">
            New matches are automatically found when players update their availability.
        </p>
        """
        template = Template(self._get_base_template())
        html_body = template.render(subject="Match Update", content=content)

        return self._send_email(
            to_email=to_email,
            subject=f"📋 {match_day} match update — {decliner_name} can't make it",
            html_body=html_body,
        )

    def send_match_player_accepted(
        self,
        to_email: str,
        player_name: str,
        accepter_name: str,
        match_day: str,
        accepted_count: int,
        total_count: int,
        app_url: str = "",
    ) -> bool:
        """Sends a nudge email when another player accepts (but not all yet)."""
        match_url = f"{app_url}/signup?tab=my-matches" if app_url else ""
        cta_html = f'<a href="{match_url}" style="display:inline-block;padding:12px 24px;background:#047857;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;margin-top:10px;">Accept Match</a>' if match_url else ""

        content = f"""
        <h2>⏳ Your {match_day} Match Needs You!</h2>
        <p>Hi {player_name},</p>
        <p>{accepter_name} just accepted the <strong>{match_day}</strong> match — that's {accepted_count} of {total_count} players confirmed.</p>
        <p>We're waiting on your response to lock in the group.</p>

        <div style="text-align:center;margin:25px 0;">
            {cta_html}
        </div>
        """
        template = Template(self._get_base_template())
        html_body = template.render(subject="Match Waiting", content=content)

        return self._send_email(
            to_email=to_email,
            subject=f"⏳ {accepter_name} accepted — your {match_day} match needs you!",
            html_body=html_body,
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
