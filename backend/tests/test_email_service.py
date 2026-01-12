"""
Unit tests for EmailService

Tests email sending functionality with different providers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.email_service import (
    EmailService,
    SMTPEmailProvider,
    EmailProvider
)


class TestSMTPEmailProvider:
    """Test SMTP email provider"""

    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'password123',
        'FROM_EMAIL': 'test@test.com',
        'FROM_NAME': 'Test App'
    })
    def test_smtp_provider_initialization(self):
        """Test SMTP provider initializes with env vars"""
        provider = SMTPEmailProvider()

        assert provider.smtp_host == 'smtp.test.com'
        assert provider.smtp_port == 587
        assert provider.smtp_user == 'test@test.com'
        assert provider.from_email == 'test@test.com'

    @patch.dict('os.environ', {
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'password123'
    })
    def test_smtp_provider_is_configured(self):
        """Test SMTP provider configuration check"""
        provider = SMTPEmailProvider()
        assert provider.is_configured() is True

    @patch.dict('os.environ', {}, clear=True)
    def test_smtp_provider_not_configured(self):
        """Test SMTP provider detects missing configuration"""
        provider = SMTPEmailProvider()
        assert provider.is_configured() is False

    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'password123'
    })
    @patch('emails.html')
    def test_send_email_success(self, mock_emails_html):
        """Test successful email sending"""
        provider = SMTPEmailProvider()

        # Mock the email message
        mock_message = Mock()
        mock_response = Mock()
        mock_response.status_code = 250
        mock_message.send.return_value = mock_response
        mock_emails_html.return_value = mock_message

        result = provider.send_email(
            to_email='recipient@test.com',
            subject='Test Subject',
            html_body='<p>Test Body</p>'
        )

        assert result is True
        mock_message.send.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    def test_send_email_not_configured(self):
        """Test sending email when not configured"""
        provider = SMTPEmailProvider()

        result = provider.send_email(
            to_email='recipient@test.com',
            subject='Test',
            html_body='<p>Test</p>'
        )

        assert result is False

    @patch.dict('os.environ', {
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'password123'
    })
    @patch('emails.html')
    def test_send_email_failure(self, mock_emails_html):
        """Test email sending failure"""
        provider = SMTPEmailProvider()

        # Mock failed response
        mock_message = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_message.send.return_value = mock_response
        mock_emails_html.return_value = mock_message

        result = provider.send_email(
            to_email='recipient@test.com',
            subject='Test',
            html_body='<p>Test</p>'
        )

        assert result is False

    def test_html_to_text_conversion(self):
        """Test HTML to text conversion"""
        provider = SMTPEmailProvider()

        html = '<p>Hello <strong>World</strong></p>'
        text = provider._html_to_text(html)

        assert 'Hello' in text
        assert 'World' in text
        assert '<' not in text


class TestEmailService:
    """Test unified email service"""

    @patch.dict('os.environ', {
        'EMAIL_PROVIDER': 'smtp',
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'password123'
    })
    @patch('app.services.email_service.SMTPEmailProvider')
    def test_email_service_initialization_smtp(self, mock_smtp_provider):
        """Test email service initializes with SMTP provider"""
        mock_provider_instance = Mock()
        mock_provider_instance.is_configured.return_value = True
        mock_smtp_provider.return_value = mock_provider_instance

        service = EmailService()

        assert service.provider is not None

    @patch.dict('os.environ', {}, clear=True)
    @patch('app.services.email_service.SMTPEmailProvider')
    def test_email_service_no_provider(self, mock_smtp_provider):
        """Test email service with no configured provider"""
        mock_provider_instance = Mock()
        mock_provider_instance.is_configured.return_value = False
        mock_smtp_provider.return_value = mock_provider_instance

        service = EmailService()

        # Provider might exist but not be configured
        assert service.provider is None or not service.provider.is_configured()

    @patch.dict('os.environ', {
        'EMAIL_PROVIDER': 'smtp',
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'password123'
    })
    @patch('app.services.email_service.SMTPEmailProvider')
    def test_send_email_through_service(self, mock_smtp_provider):
        """Test sending email through unified service"""
        mock_provider_instance = Mock()
        mock_provider_instance.is_configured.return_value = True
        mock_provider_instance.send_email.return_value = True
        mock_smtp_provider.return_value = mock_provider_instance

        service = EmailService()

        # Service should have a provider now
        assert service.provider is not None
