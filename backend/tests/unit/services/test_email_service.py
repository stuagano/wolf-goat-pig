"""
Unit tests for EmailService

Tests email sending functionality with different providers.
"""

from unittest.mock import Mock, patch

from app.services.email_service import EmailService, SMTPEmailProvider


class TestSMTPEmailProvider:
    """Test SMTP email provider"""

    @patch.dict(
        "os.environ",
        {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "test@test.com",
            "SMTP_PASSWORD": "password123",
            "FROM_EMAIL": "test@test.com",
            "FROM_NAME": "Test App",
        },
    )
    def test_smtp_provider_initialization(self):
        """Test SMTP provider initializes with env vars"""
        provider = SMTPEmailProvider()

        assert provider.smtp_host == "smtp.test.com"
        assert provider.smtp_port == 587
        assert provider.smtp_user == "test@test.com"
        assert provider.from_email == "test@test.com"

    @patch.dict("os.environ", {"SMTP_USER": "test@test.com", "SMTP_PASSWORD": "password123"})
    def test_smtp_provider_is_configured(self):
        """Test SMTP provider configuration check"""
        provider = SMTPEmailProvider()
        assert provider.is_configured() is True

    @patch.dict("os.environ", {}, clear=True)
    def test_smtp_provider_not_configured(self):
        """Test SMTP provider detects missing configuration"""
        provider = SMTPEmailProvider()
        assert provider.is_configured() is False

    @patch.dict(
        "os.environ",
        {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_USER": "test@test.com",
            "SMTP_PASSWORD": "password123",
        },
    )
    @patch("emails.html")
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
            to_email="recipient@test.com",
            subject="Test Subject",
            html_body="<p>Test Body</p>",
        )

        assert result is True
        mock_message.send.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)
    def test_send_email_not_configured(self):
        """Test sending email when not configured"""
        provider = SMTPEmailProvider()

        result = provider.send_email(to_email="recipient@test.com", subject="Test", html_body="<p>Test</p>")

        assert result is False

    @patch.dict("os.environ", {"SMTP_USER": "test@test.com", "SMTP_PASSWORD": "password123"})
    @patch("emails.html")
    def test_send_email_failure(self, mock_emails_html):
        """Test email sending failure"""
        provider = SMTPEmailProvider()

        # Mock failed response
        mock_message = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_message.send.return_value = mock_response
        mock_emails_html.return_value = mock_message

        result = provider.send_email(to_email="recipient@test.com", subject="Test", html_body="<p>Test</p>")

        assert result is False

    def test_html_to_text_conversion(self):
        """Test HTML to text conversion"""
        provider = SMTPEmailProvider()

        html = "<p>Hello <strong>World</strong></p>"
        text = provider._html_to_text(html)

        assert "Hello" in text
        assert "World" in text
        assert "<" not in text


class TestEmailService:
    """Test unified email service"""

    @patch.dict(
        "os.environ",
        {
            "EMAIL_PROVIDER": "smtp",
            "SMTP_USER": "test@test.com",
            "SMTP_PASSWORD": "password123",
        },
    )
    @patch("app.services.email_service.SMTPEmailProvider")
    def test_email_service_initialization_smtp(self, mock_smtp_provider):
        """Test email service initializes with SMTP provider"""
        mock_provider_instance = Mock()
        mock_provider_instance.is_configured.return_value = True
        mock_smtp_provider.return_value = mock_provider_instance

        service = EmailService()

        assert service.provider is not None

    @patch.dict("os.environ", {}, clear=True)
    @patch("app.services.email_service.SMTPEmailProvider")
    def test_email_service_no_provider(self, mock_smtp_provider):
        """Test email service with no configured provider"""
        mock_provider_instance = Mock()
        mock_provider_instance.is_configured.return_value = False
        mock_smtp_provider.return_value = mock_provider_instance

        service = EmailService()

        # Provider might exist but not be configured
        assert service.provider is None or not service.provider.is_configured()

    @patch.dict(
        "os.environ",
        {
            "EMAIL_PROVIDER": "smtp",
            "SMTP_USER": "test@test.com",
            "SMTP_PASSWORD": "password123",
        },
    )
    @patch("app.services.email_service.SMTPEmailProvider")
    def test_send_email_through_service(self, mock_smtp_provider):
        """Test sending email through unified service"""
        mock_provider_instance = Mock()
        mock_provider_instance.is_configured.return_value = True
        mock_provider_instance.send_email.return_value = True
        mock_smtp_provider.return_value = mock_provider_instance

        service = EmailService()

        # Service should have a provider now
        assert service.provider is not None

    @patch.dict(
        "os.environ",
        {
            "EMAIL_PROVIDER": "smtp",
            "SMTP_USER": "test@test.com",
            "SMTP_PASSWORD": "password123",
            "FRONTEND_URL": "https://example.test",
        },
    )
    @patch("app.services.email_service.SMTPEmailProvider")
    def test_welcome_email_explains_club_player_setup(self, mock_smtp_provider):
        mock_provider = Mock()
        mock_provider.is_configured.return_value = True
        mock_provider.send_email.return_value = True
        mock_smtp_provider.return_value = mock_provider

        service = EmailService()

        assert service.send_welcome_email("new@example.com", "New Player") is True
        _, _, html_body, text_body = mock_provider.send_email.call_args.args
        club_player_url = "https://example.test/account#club-player"
        assert "Link your club player" in html_body
        assert club_player_url in html_body
        assert club_player_url in text_body
        assert "Nothing to download and nothing to set up" not in text_body

    @patch.dict(
        "os.environ",
        {"SMTP_USER": "test@test.com", "SMTP_PASSWORD": "password123", "FRONTEND_URL": "https://example.test"},
    )
    @patch("app.services.email_service.SMTPEmailProvider")
    def test_weekly_highlights_email_lists_highlights_and_preferences_link(self, mock_smtp_provider):
        mock_provider = Mock()
        mock_provider.is_configured.return_value = True
        mock_provider.send_email.return_value = True
        mock_smtp_provider.return_value = mock_provider
        highlights = {
            "rounds": 2,
            "courses": ["Wing Point"],
            "players": ["Bob", "Mike <script>"],
            "biggest_round": {"player": "Mike <script>", "quarters": 34.0, "course": "Wing Point"},
            "top_earner": {"player": "Mike <script>", "quarters": 24.0, "rounds": 2},
            "biggest_hole": {"player": "Bob", "hole": 18, "quarters": 16.0, "course": "Wing Point"},
            "ironman": None,
        }

        assert EmailService().send_weekly_highlights("a@x.com", "Al", highlights) is True
        _, _, html_body, text_body = mock_provider.send_email.call_args.args
        assert "+34 quarters at Wing Point" in html_body
        assert "took +16 quarters on #18" in html_body
        assert "Ironman" not in html_body
        assert "<script>" not in html_body  # player names are escaped
        assert "https://example.test/account" in html_body
        assert "Manage your email preferences: https://example.test/account" in text_body
        assert "Top earner of the week: Mike <script>, +24 quarters over 2 round(s)" in text_body

    @patch.dict("os.environ", {"SMTP_USER": "u", "SMTP_PASSWORD": "p", "FRONTEND_URL": "https://example.test/"})
    @patch("app.services.email_service.SMTPEmailProvider")
    def test_every_base_template_email_has_preferences_link(self, mock_smtp_provider):
        mock_provider = Mock()
        mock_provider.is_configured.return_value = True
        mock_provider.send_email.return_value = True
        mock_smtp_provider.return_value = mock_provider

        EmailService().send_callout_notification("a@x.com", "Al", "2026-10-18", 3, 1)
        html_body = mock_provider.send_email.call_args.args[2]
        assert '<a href="https://example.test/account">Manage your email preferences</a>' in html_body

    @patch.dict("os.environ", {"SMTP_USER": "u", "SMTP_PASSWORD": "p", "FRONTEND_URL": "https://example.test"})
    @patch("app.services.email_service.SMTPEmailProvider")
    def test_sunday_reminder_lists_signups_and_links_preferences_in_both_parts(self, mock_smtp_provider):
        mock_provider = Mock()
        mock_provider.is_configured.return_value = True
        mock_provider.send_email.return_value = True
        mock_smtp_provider.return_value = mock_provider

        assert EmailService().send_sunday_reminder("a@x.com", "Al", "2026-10-18", ["Bob", "Mike <b>"]) is True
        _, subject, html_body, text_body = mock_provider.send_email.call_args.args
        assert "2 signed up" in subject
        assert "Sunday, October 18" in html_body
        assert "Mike &lt;b&gt;" in html_body and "<b>" not in html_body.split("Mike")[1][:4]
        assert "https://example.test/signup" in html_body
        assert "https://example.test/signup" in text_body
        assert '<a href="https://example.test/account">Manage your email preferences</a>' in html_body
        assert "Manage your email preferences: https://example.test/account" in text_body

    @patch.dict("os.environ", {"SMTP_USER": "u", "SMTP_PASSWORD": "p"})
    @patch("app.services.email_service.SMTPEmailProvider")
    def test_sunday_reminder_with_no_signups_yet(self, mock_smtp_provider):
        mock_provider = Mock()
        mock_provider.is_configured.return_value = True
        mock_provider.send_email.return_value = True
        mock_smtp_provider.return_value = mock_provider

        EmailService().send_sunday_reminder("a@x.com", "Al", "2026-10-18", [])
        _, subject, html_body, text_body = mock_provider.send_email.call_args.args
        assert "Nobody's signed up yet" in html_body
        assert "be the first" in subject

    @patch.dict("os.environ", {"SMTP_USER": "u", "SMTP_PASSWORD": "p"})
    @patch("app.services.email_service.SMTPEmailProvider")
    def test_ai_intro_renders_escaped_in_both_parts_and_is_optional(self, mock_smtp_provider):
        mock_provider = Mock()
        mock_provider.is_configured.return_value = True
        mock_provider.send_email.return_value = True
        mock_smtp_provider.return_value = mock_provider
        svc = EmailService()

        svc.send_sunday_reminder("a@x.com", "Al", "2026-10-18", ["Bob"], intro="Bob's in. <Brave> man.")
        _, _, html_body, text_body = mock_provider.send_email.call_args.args
        assert "Bob&#x27;s in. &lt;Brave&gt; man." in html_body
        assert "Hi Al,\n\nBob's in. <Brave> man.\n\n" in text_body

        svc.send_sunday_reminder("a@x.com", "Al", "2026-10-18", ["Bob"])
        _, _, html_body, _ = mock_provider.send_email.call_args.args
        assert "font-style: italic" not in html_body

        highlights = {
            "rounds": 1,
            "courses": ["Wing Point"],
            "players": ["Bob"],
            "biggest_round": None,
            "top_earner": None,
            "biggest_hole": None,
            "ironman": None,
            "intro": "Quiet week. Suspicious.",
        }
        svc.send_weekly_highlights("a@x.com", "Al", highlights)
        _, _, html_body, text_body = mock_provider.send_email.call_args.args
        assert "Quiet week. Suspicious." in html_body
        assert "Hi Al,\n\nQuiet week. Suspicious.\n\n" in text_body
