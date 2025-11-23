"""
Gmail OAuth2 Email Provider
Implements OAuth2 authentication for sending emails via Gmail API.
This provider is intended to be used by the unified EmailService.
"""

import base64
import logging
import os
import pickle
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_FILE = 'gmail_token.pickle'
CREDENTIALS_FILE = 'gmail_credentials.json'

class GmailOAuth2Provider:
    """Provider for sending emails using Gmail API with OAuth2 authentication."""

    def __init__(self, from_email: str, from_name: str, data_dir: Path):
        self.creds: Optional[Credentials] = None
        self.service = None
        self.from_email = from_email
        self.from_name = from_name

        self.token_path = data_dir / TOKEN_FILE
        self.credentials_path = data_dir / CREDENTIALS_FILE

        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.load_credentials()

    def load_credentials(self) -> bool:
        """Load or refresh OAuth2 credentials."""
        try:
            if self.token_path.exists():
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired OAuth2 token.")
                    self.creds.refresh(Request())
                    self.save_credentials()
                else:
                    logger.warning("OAuth2 credentials not found or invalid. Authorization required.")
                    return False

            self._initialize_service()
            return True
        except Exception as e:
            logger.error(f"Error loading OAuth2 credentials: {e}")
            self.creds = None
            self.service = None
            return False

    def save_credentials(self):
        """Save OAuth2 credentials to a file."""
        if not self.creds:
            return
        try:
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
            logger.info("OAuth2 credentials saved.")
        except Exception as e:
            logger.error(f"Error saving OAuth2 credentials: {e}")

    def _initialize_service(self):
        """Initialize the Gmail API service."""
        if not self.creds:
            logger.error("Cannot initialize Gmail service without credentials.")
            return
        try:
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Gmail API service initialized.")
        except Exception as e:
            logger.error(f"Error initializing Gmail service: {e}")
            self.service = None

    def get_auth_url(self, redirect_uri: str) -> Optional[str]:
        """Generate the OAuth2 authorization URL."""
        if not self.credentials_path.exists():
            logger.error(f"Gmail credentials file not found at {self.credentials_path}.")
            return None
        try:
            flow = Flow.from_client_secrets_file(
                str(self.credentials_path),
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            return auth_url
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            return None

    def handle_oauth_callback(self, authorization_code: str, redirect_uri: str) -> bool:
        """Handle the OAuth2 callback to exchange the code for credentials."""
        if not self.credentials_path.exists():
            logger.error(f"Gmail credentials file not found at {self.credentials_path}.")
            return False
        try:
            flow = Flow.from_client_secrets_file(
                str(self.credentials_path),
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            flow.fetch_token(code=authorization_code)
            self.creds = flow.credentials
            self.save_credentials()
            self._initialize_service()
            logger.info("OAuth2 callback handled successfully.")
            return True
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            return False

    @property
    def is_configured(self) -> bool:
        """Check if the provider is fully configured and ready to send emails."""
        return self.service is not None and self.creds is not None and self.creds.valid

    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """Send an email using the Gmail API."""
        if not self.is_configured:
            logger.error("Gmail OAuth2 provider is not configured. Cannot send email.")
            return False

        try:
            message = self._create_message(to_email, subject, html_body, text_body)
            self.service.users().messages().send(userId='me', body=message).execute()
            logger.info(f"Email sent successfully to {to_email} via Gmail.")
            return True
        except HttpError as error:
            logger.error(f"An error occurred while sending email via Gmail: {error}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return False

    def _create_message(self, to: str, subject: str, body_html: str, body_text: Optional[str]) -> Dict[str, Any]:
        """Create a MIME message for the Gmail API."""
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['from'] = f"{self.from_name} <{self.from_email}>"
        message['subject'] = subject

        if body_text:
            message.attach(MIMEText(body_text, 'plain'))
        message.attach(MIMEText(body_html, 'html'))

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw_message}

    def get_configuration_status(self) -> Dict[str, Any]:
        """Get the current configuration status of the provider."""
        self.load_credentials()  # Ensure status is up-to-date
        return {
            "provider": "gmail_oauth2",
            "configured": self.is_configured,
            "credentials_file_exists": self.credentials_path.exists(),
            "token_file_exists": self.token_path.exists(),
            "has_credentials": self.creds is not None,
            "credentials_valid": self.creds.valid if self.creds else False,
        }

def create_gmail_oauth2_provider() -> Optional[GmailOAuth2Provider]:
    """Factory function to create a GmailOAuth2Provider instance."""
    from_email = os.getenv("FROM_EMAIL")
    from_name = os.getenv("FROM_NAME", "Wolf Goat Pig")

    if not from_email:
        logger.warning("FROM_EMAIL environment variable is not set. Cannot create Gmail OAuth2 provider.")
        return None

    # Use a common data directory for all services
    data_dir = Path(__file__).parent.parent.parent.parent / 'data'

    return GmailOAuth2Provider(
        from_email=from_email,
        from_name=from_name,
        data_dir=data_dir
    )
