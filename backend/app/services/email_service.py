"""
Email Service for Wolf Goat Pig Application

Handles all email functionality including signup notifications, reminders, and summaries.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import emails
from jinja2 import Template

logger = logging.getLogger(__name__)

# Email configuration from environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.getenv("FROM_NAME", "Wolf Goat Pig - Wing Point Golf Club")

class EmailService:
    """Service for sending various types of emails"""
    
    def __init__(self):
        self.smtp_config = {
            'host': SMTP_HOST,
            'port': SMTP_PORT,
            'tls': True,
            'user': SMTP_USER,
            'password': SMTP_PASSWORD
        }
        self.from_email = FROM_EMAIL
        self.from_name = FROM_NAME
        
        # Check if email is properly configured
        self.is_configured = bool(SMTP_USER and SMTP_PASSWORD and SMTP_HOST)
        
        if not self.is_configured:
            logger.warning("Email service is not fully configured. Check environment variables: SMTP_USER, SMTP_PASSWORD, SMTP_HOST")
    
    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """Send an email using the configured SMTP settings"""
        
        if not self.is_configured:
            logger.error("Email service not configured. Cannot send email.")
            return False
            
        try:
            # Create email message
            message = emails.html(
                html=html_body,
                text=text_body or self._html_to_text(html_body),
                subject=subject,
                mail_from=(self.from_name, self.from_email)
            )
            
            # Send email
            response = message.send(
                to=to_email,
                smtp=self.smtp_config
            )
            
            if response.status_code == 250:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (basic implementation)"""
        import re
        # Remove HTML tags
        text = re.sub('<.*?>', '', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def send_test_email(self, to_email: str, admin_name: str = "Admin") -> bool:
        """Send a test email to verify configuration"""
        subject = "Wolf Goat Pig - Test Email"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c5282;">🐺🐐🐷 Wolf Goat Pig Email Test</h2>
            <p>Hello {admin_name},</p>
            <p>This is a test email from your Wolf Goat Pig application to verify that email configuration is working correctly.</p>
            <div style="background-color: #f7fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #2d3748; margin-top: 0;">Configuration Details:</h3>
                <ul style="color: #4a5568;">
                    <li>SMTP Host: {self.smtp_config['host']}</li>
                    <li>SMTP Port: {self.smtp_config['port']}</li>
                    <li>From Email: {self.from_email}</li>
                    <li>From Name: {self.from_name}</li>
                </ul>
            </div>
            <p style="color: #718096;">If you received this email, your email service is configured correctly!</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="color: #a0aec0; font-size: 12px;">This test was initiated by {admin_name}</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Wolf Goat Pig Email Test
        
        Hello {admin_name},
        
        This is a test email from your Wolf Goat Pig application.
        
        Configuration Details:
        - SMTP Host: {self.smtp_config['host']}
        - SMTP Port: {self.smtp_config['port']}
        - From Email: {self.from_email}
        - From Name: {self.from_name}
        
        If you received this email, your email service is configured correctly!
        
        This test was initiated by {admin_name}
        """
        
        return self._send_email(to_email, subject, html_body, text_body)
    
    def _get_base_template(self) -> str:
        """Get the base HTML email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ subject }}</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }
                .container { 
                    max-width: 600px; 
                    margin: 0 auto; 
                    background: white; 
                    border-radius: 8px; 
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .header { 
                    background: linear-gradient(135deg, #047857, #059669); 
                    color: white; 
                    padding: 30px; 
                    text-align: center; 
                }
                .header h1 { 
                    margin: 0; 
                    font-size: 28px; 
                    font-weight: 700;
                }
                .header p { 
                    margin: 10px 0 0; 
                    opacity: 0.9; 
                    font-size: 16px;
                }
                .content { 
                    padding: 30px; 
                }
                .footer { 
                    background: #f8f9fa; 
                    padding: 20px; 
                    text-align: center; 
                    border-top: 1px solid #dee2e6;
                    color: #6c757d;
                    font-size: 14px;
                }
                .button { 
                    display: inline-block; 
                    background: #047857; 
                    color: white; 
                    padding: 12px 24px; 
                    text-decoration: none; 
                    border-radius: 6px; 
                    font-weight: 600;
                    margin: 10px 0;
                }
                .button:hover { 
                    background: #065f46; 
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏌️ Wolf Goat Pig</h1>
                    <p>Wing Point Golf & Country Club</p>
                </div>
                <div class="content">
                    {{ content }}
                </div>
                <div class="footer">
                    <p>Wing Point Golf & Country Club • Est. 1903</p>
                    <p>You're receiving this because you're signed up for Wolf Goat Pig notifications.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def send_signup_confirmation(self, to_email: str, player_name: str, signup_date: str) -> bool:
        """Send email confirmation when someone signs up for a game"""
        
        content = f"""
        <h2>🎯 Signup Confirmed!</h2>
        <p>Hi {player_name},</p>
        <p>You're all set for Wolf Goat Pig on <strong>{signup_date}</strong>.</p>
        <p>We'll see you on the course! Remember:</p>
        <ul>
            <li>🐺 <strong>Wolf</strong> - Choose your partners wisely</li>
            <li>🐐 <strong>Goat</strong> - Every hole is a new opportunity</li>
            <li>🐷 <strong>Pig</strong> - "We accept bad golf, but not bad betting"</li>
        </ul>
        <p>Good luck and may the best player win!</p>
        """
        
        template = Template(self._get_base_template())
        html_body = template.render(
            subject="Golf Signup Confirmed",
            content=content
        )
        
        return self._send_email(
            to_email=to_email,
            subject=f"🏌️ You're signed up for Wolf Goat Pig - {signup_date}",
            html_body=html_body
        )
    
    def send_daily_signup_reminder(self, to_email: str, player_name: str, available_dates: List[str]) -> bool:
        """Send daily reminder about available signup dates"""
        
        if not available_dates:
            return True  # No need to send if no dates available
        
        dates_html = ""
        for signup_date in available_dates[:5]:  # Limit to 5 upcoming dates
            dates_html += f"<li><strong>{signup_date}</strong></li>"
        
        content = f"""
        <h2>🏌️ Daily Golf Signup Reminder</h2>
        <p>Good morning {player_name}!</p>
        <p>The following Wolf Goat Pig games are open for signup:</p>
        <ul>
            {dates_html}
        </ul>
        <p>Don't miss out on the action! Sign up early to secure your spot.</p>
        <a href="https://your-app-url.com/signup" class="button">Sign Up Now</a>
        """
        
        template = Template(self._get_base_template())
        html_body = template.render(
            subject="Daily Golf Signup Reminder",
            content=content
        )
        
        return self._send_email(
            to_email=to_email,
            subject="🏌️ Wolf Goat Pig games available for signup",
            html_body=html_body
        )
    
    def send_weekly_summary(self, to_email: str, player_name: str, summary_data: Dict[str, Any]) -> bool:
        """Send weekly summary of games and performance"""
        
        games_played = summary_data.get('games_played', 0)
        total_earnings = summary_data.get('total_earnings', 0)
        rank = summary_data.get('current_rank', 'N/A')
        
        content = f"""
        <h2>📊 Your Weekly Wolf Goat Pig Summary</h2>
        <p>Hi {player_name},</p>
        <p>Here's how you did this week at Wing Point:</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; margin: 20px 0;">
            <h3 style="margin: 0 0 15px 0; color: #047857;">📈 Your Stats</h3>
            <p><strong>Games Played:</strong> {games_played}</p>
            <p><strong>Total Earnings:</strong> {total_earnings} quarters</p>
            <p><strong>Current Rank:</strong> #{rank}</p>
        </div>
        
        <p>Keep up the great play! See you on the course next week.</p>
        <a href="https://your-app-url.com/leaderboard" class="button">View Full Leaderboard</a>
        """
        
        template = Template(self._get_base_template())
        html_body = template.render(
            subject="Weekly Wolf Goat Pig Summary",
            content=content
        )
        
        return self._send_email(
            to_email=to_email,
            subject=f"📊 Weekly Summary - {total_earnings} quarters earned",
            html_body=html_body
        )
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send a generic email with custom subject and body"""
        try:
            # Create message
            message = emails.Message(
                subject=subject,
                html=f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    {body.replace(chr(10), '<br>')}
                </body>
                </html>
                """,
                mail_from=(self.sender_email, self.sender_name)
            )
            
            # Send using appropriate method
            if self.use_oauth2:
                response = self.oauth2_service.send_email(
                    to_email=to_email,
                    subject=subject,
                    body=body
                )
                return response
            else:
                response = message.send(
                    to=to_email,
                    smtp={
                        "host": self.smtp_host,
                        "port": self.smtp_port,
                        "tls": self.smtp_tls,
                        "user": self.smtp_user,
                        "password": self.smtp_password
                    }
                )
                
                if response.status_code == 250:
                    logger.info(f"Email sent successfully to {to_email}")
                    return True
                else:
                    logger.error(f"Failed to send email: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def send_game_invitation(self, to_email: str, player_name: str, inviter_name: str, game_date: str) -> bool:
        """Send invitation to join a specific game"""
        
        content = f"""
        <h2>🎯 You're Invited to Play!</h2>
        <p>Hi {player_name},</p>
        <p><strong>{inviter_name}</strong> has invited you to join a Wolf Goat Pig game on <strong>{game_date}</strong>.</p>
        
        <div style="background: #e8f5e8; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #047857;">
            <p style="margin: 0;"><strong>Game Details:</strong></p>
            <p style="margin: 5px 0;">📅 Date: {game_date}</p>
            <p style="margin: 5px 0;">🏌️ Game: Wolf Goat Pig</p>
            <p style="margin: 5px 0;">📍 Location: Wing Point Golf Club</p>
        </div>
        
        <p>Will you accept the challenge?</p>
        <a href="https://your-app-url.com/signup" class="button">Accept Invitation</a>
        """
        
        template = Template(self._get_base_template())
        html_body = template.render(
            subject="Game Invitation",
            content=content
        )
        
        return self._send_email(
            to_email=to_email,
            subject=f"🏌️ {inviter_name} invited you to play Wolf Goat Pig",
            html_body=html_body
        )

# Global email service instance
email_service = EmailService()

def get_email_service() -> EmailService:
    """Get the global email service instance"""
    return email_service