"""
OAuth2 Email Service for Gmail
Implements OAuth2 authentication for sending emails via Gmail API
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# OAuth2 Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_FILE = 'gmail_token.pickle'
CREDENTIALS_FILE = 'gmail_credentials.json'

class OAuth2EmailService:
    """Email service using Gmail API with OAuth2 authentication"""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.from_email = os.getenv("FROM_EMAIL", "")
        self.from_name = os.getenv("FROM_NAME", "Wolf Goat Pig")
        
        # Token storage path
        self.token_path = Path(__file__).parent.parent.parent / 'data' / TOKEN_FILE
        self.credentials_path = Path(__file__).parent.parent.parent / 'data' / CREDENTIALS_FILE
        
        # Ensure data directory exists
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to load existing credentials
        self.load_credentials()
    
    def load_credentials(self) -> bool:
        """Load existing OAuth2 credentials from storage"""
        try:
            if self.token_path.exists():
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
                    
            # If there are no (valid) credentials available, return False
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired OAuth2 token")
                    self.creds.refresh(Request())
                    self.save_credentials()
                    self._initialize_service()
                    return True
                return False
            
            self._initialize_service()
            return True
            
        except Exception as e:
            logger.error(f"Error loading OAuth2 credentials: {e}")
            return False
    
    def save_credentials(self):
        """Save OAuth2 credentials to storage"""
        try:
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
            logger.info("OAuth2 credentials saved successfully")
        except Exception as e:
            logger.error(f"Error saving OAuth2 credentials: {e}")
    
    def _initialize_service(self):
        """Initialize Gmail API service"""
        try:
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Gmail API service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gmail service: {e}")
            self.service = None
    
    def get_auth_url(self, redirect_uri: str = None) -> str:
        """Generate OAuth2 authorization URL"""
        try:
            # Auto-detect redirect URI based on environment
            if redirect_uri is None:
                import os
                # Determine backend URL based on environment
                if os.getenv("RENDER"):
                    # On Render, use the service URL
                    backend_url = "https://wolf-goat-pig-api.onrender.com"
                elif os.getenv("ENVIRONMENT") == "production":
                    backend_url = os.getenv("BACKEND_URL", "https://wolf-goat-pig-api.onrender.com")
                else:
                    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
                redirect_uri = f"{backend_url}/admin/oauth2-callback"
            
            # Check if credentials file exists
            if not self.credentials_path.exists():
                raise FileNotFoundError(
                    f"Gmail credentials file not found at {self.credentials_path}. "
                    "Please download it from Google Cloud Console."
                )
            
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
            
            # Note: Flow object can't be stored in memory for production environments
            # Each request must recreate the flow with the same parameters
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            raise
    
    def handle_oauth_callback(self, authorization_code: str, redirect_uri: str = None) -> bool:
        """Handle OAuth2 callback and save credentials"""
        try:
            # Auto-detect redirect URI if not provided
            if redirect_uri is None:
                import os
                # Determine backend URL based on environment
                if os.getenv("RENDER"):
                    # On Render, use the service URL
                    backend_url = "https://wolf-goat-pig-api.onrender.com"
                elif os.getenv("ENVIRONMENT") == "production":
                    backend_url = os.getenv("BACKEND_URL", "https://wolf-goat-pig-api.onrender.com")
                else:
                    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
                redirect_uri = f"{backend_url}/admin/oauth2-callback"
            
            # Always recreate flow with the same redirect_uri used in authorization
            # This is necessary because the flow object doesn't persist between requests in production
            flow = Flow.from_client_secrets_file(
                str(self.credentials_path),
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            
            # Exchange authorization code for credentials
            logger.info(f"Attempting to exchange authorization code for token with redirect_uri: {redirect_uri}")
            
            try:
                flow.fetch_token(code=authorization_code)
                logger.info("Successfully fetched token from Google")
            except Exception as token_error:
                logger.error(f"Failed to fetch token: {token_error}")
                logger.error(f"Authorization code: {authorization_code[:10]}...")
                logger.error(f"Redirect URI used: {redirect_uri}")
                raise
            
            self.creds = flow.credentials
            self.save_credentials()
            self._initialize_service()
            
            logger.info("OAuth2 callback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            logger.error(f"Full error details: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    @property
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return self.service is not None and self.creds is not None and self.creds.valid
    
    def create_message(self, to: str, subject: str, body_html: str, body_text: str = None) -> Dict[str, Any]:
        """Create an email message"""
        try:
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['from'] = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
            message['subject'] = subject
            
            # Add plain text part
            if body_text:
                text_part = MIMEText(body_text, 'plain')
                message.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(body_html, 'html')
            message.attach(html_part)
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            return {'raw': raw_message}
            
        except Exception as e:
            logger.error(f"Error creating email message: {e}")
            raise
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """Send an email using Gmail API"""
        if not self.is_configured:
            logger.error("OAuth2 email service not configured")
            return False
        
        try:
            message = self.create_message(to_email, subject, html_body, text_body)
            
            result = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            logger.info(f"Email sent successfully to {to_email}. Message ID: {result['id']}")
            return True
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def send_test_email(self, to_email: str, admin_name: str = "Admin") -> bool:
        """Send a test email to verify OAuth2 configuration"""
        subject = "Wolf Goat Pig - OAuth2 Test Email"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c5282;">🐺🐐🐷 Wolf Goat Pig OAuth2 Email Test</h2>
            <p>Hello {admin_name},</p>
            <p>This is a test email from your Wolf Goat Pig application using <strong>Gmail OAuth2</strong> authentication.</p>
            <div style="background-color: #e6f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #2d3748; margin-top: 0;">✅ OAuth2 Configuration Successful!</h3>
                <p style="color: #4a5568;">Your Gmail API integration is working correctly. You can now send emails through the Wolf Goat Pig application.</p>
            </div>
            <div style="background-color: #f7fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="color: #2d3748; margin-top: 0;">Configuration Details:</h4>
                <ul style="color: #4a5568;">
                    <li>Authentication: OAuth2</li>
                    <li>Service: Gmail API</li>
                    <li>From Email: {self.from_email or 'Not set'}</li>
                    <li>From Name: {self.from_name}</li>
                </ul>
            </div>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="color: #a0aec0; font-size: 12px;">
                This test was initiated by {admin_name}<br>
                Sent via Gmail API with OAuth2 authentication
            </p>
        </body>
        </html>
        """
        
        text_body = f"""
        Wolf Goat Pig OAuth2 Email Test
        
        Hello {admin_name},
        
        This is a test email from your Wolf Goat Pig application using Gmail OAuth2 authentication.
        
        ✅ OAuth2 Configuration Successful!
        Your Gmail API integration is working correctly.
        
        Configuration Details:
        - Authentication: OAuth2
        - Service: Gmail API
        - From Email: {self.from_email or 'Not set'}
        - From Name: {self.from_name}
        
        This test was initiated by {admin_name}
        Sent via Gmail API with OAuth2 authentication
        """
        
        return self.send_email(to_email, subject, html_body, text_body)
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get current configuration status"""
        return {
            "configured": self.is_configured,
            "has_credentials": self.creds is not None,
            "credentials_valid": self.creds.valid if self.creds else False,
            "credentials_expired": self.creds.expired if self.creds else None,
            "has_refresh_token": bool(self.creds.refresh_token) if self.creds else False,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "credentials_file_exists": self.credentials_path.exists(),
            "token_file_exists": self.token_path.exists()
        }

# Singleton instance
_oauth2_email_service = None

def get_oauth2_email_service() -> OAuth2EmailService:
    """Get or create OAuth2 email service instance"""
    global _oauth2_email_service
    if _oauth2_email_service is None:
        _oauth2_email_service = OAuth2EmailService()
    return _oauth2_email_service