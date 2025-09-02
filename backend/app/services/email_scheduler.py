"""
Email Scheduler Service for Wolf Goat Pig Application

This module handles scheduling and sending automated emails based on user preferences.
"""

import logging
import asyncio
from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Optional
import schedule
import threading
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import PlayerProfile, EmailPreferences
from .email_service import email_service

logger = logging.getLogger(__name__)

class EmailScheduler:
    """Service for scheduling and sending automated emails"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self._setup_schedules()
        
    def _setup_schedules(self):
        """Set up the email scheduling jobs"""
        # Schedule daily signup reminders at different times based on user preferences
        schedule.every().day.at("06:00").do(self._send_daily_reminders, time_slot="6:00 AM")
        schedule.every().day.at("07:00").do(self._send_daily_reminders, time_slot="7:00 AM")
        schedule.every().day.at("08:00").do(self._send_daily_reminders, time_slot="8:00 AM")
        schedule.every().day.at("09:00").do(self._send_daily_reminders, time_slot="9:00 AM")
        schedule.every().day.at("10:00").do(self._send_daily_reminders, time_slot="10:00 AM")
        schedule.every().day.at("12:00").do(self._send_daily_reminders, time_slot="12:00 PM")
        schedule.every().day.at("13:00").do(self._send_daily_reminders, time_slot="1:00 PM")
        schedule.every().day.at("17:00").do(self._send_daily_reminders, time_slot="5:00 PM")
        schedule.every().day.at("18:00").do(self._send_daily_reminders, time_slot="6:00 PM")
        schedule.every().day.at("19:00").do(self._send_daily_reminders, time_slot="7:00 PM")
        
        # Schedule weekly summaries on Sunday at 9 AM
        schedule.every().sunday.at("09:00").do(self._send_weekly_summaries)
        
        # Schedule daily matchmaking at 10 AM
        schedule.every().day.at("10:00").do(self._run_matchmaking)
        
        logger.info("Email schedules set up successfully")
    
    def _get_db(self) -> Session:
        """Get a database session"""
        return SessionLocal()
    
    def _send_daily_reminders(self, time_slot: str):
        """Send daily signup reminders to users who have opted in"""
        db = self._get_db()
        
        try:
            # Get all players with email preferences for this time slot
            players_with_prefs = db.query(
                PlayerProfile, EmailPreferences
            ).join(
                EmailPreferences, 
                PlayerProfile.id == EmailPreferences.player_profile_id
            ).filter(
                EmailPreferences.daily_signups_enabled == 1,
                EmailPreferences.preferred_notification_time == time_slot,
                EmailPreferences.email_frequency != 'never',
                PlayerProfile.email.isnot(None)
            ).all()
            
            logger.info(f"Found {len(players_with_prefs)} players for {time_slot} daily reminder")
            
            # Get available signup dates (mock data for now)
            available_dates = self._get_available_signup_dates()
            
            for player, prefs in players_with_prefs:
                try:
                    if player.email:
                        success = email_service.send_daily_signup_reminder(
                            to_email=player.email,
                            player_name=player.name,
                            available_dates=available_dates
                        )
                        
                        if success:
                            logger.info(f"Daily reminder sent to {player.name} ({player.email})")
                        else:
                            logger.error(f"Failed to send daily reminder to {player.name}")
                            
                except Exception as e:
                    logger.error(f"Error sending daily reminder to {player.name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in daily reminder job: {str(e)}")
        finally:
            db.close()
    
    def _send_weekly_summaries(self):
        """Send weekly summary emails to users who have opted in"""
        db = self._get_db()
        
        try:
            # Get all players with weekly summaries enabled
            players_with_prefs = db.query(
                PlayerProfile, EmailPreferences
            ).join(
                EmailPreferences,
                PlayerProfile.id == EmailPreferences.player_profile_id
            ).filter(
                EmailPreferences.weekly_summary_enabled == 1,
                EmailPreferences.email_frequency.in_(['daily', 'weekly']),
                PlayerProfile.email.isnot(None)
            ).all()
            
            logger.info(f"Found {len(players_with_prefs)} players for weekly summary")
            
            for player, prefs in players_with_prefs:
                try:
                    if player.email:
                        # Get player's weekly stats (mock data for now)
                        summary_data = self._get_player_weekly_summary(player.id)
                        
                        success = email_service.send_weekly_summary(
                            to_email=player.email,
                            player_name=player.name,
                            summary_data=summary_data
                        )
                        
                        if success:
                            logger.info(f"Weekly summary sent to {player.name} ({player.email})")
                        else:
                            logger.error(f"Failed to send weekly summary to {player.name}")
                            
                except Exception as e:
                    logger.error(f"Error sending weekly summary to {player.name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in weekly summary job: {str(e)}")
        finally:
            db.close()
    
    def _get_available_signup_dates(self) -> List[str]:
        """Get available signup dates for the next week"""
        # Mock implementation - replace with actual logic
        dates = []
        today = datetime.now()
        
        for i in range(1, 8):  # Next 7 days
            date = today + timedelta(days=i)
            dates.append(date.strftime("%B %d, %Y"))
            
        return dates
    
    def _get_player_weekly_summary(self, player_id: int) -> Dict[str, Any]:
        """Get weekly summary data for a player"""
        # Mock implementation - replace with actual stats from database
        return {
            'games_played': 3,
            'total_earnings': 12,
            'current_rank': 5,
            'best_hole': 4,
            'worst_hole': 15
        }
    
    def _run_scheduler(self):
        """Run the scheduler in a loop"""
        while self.is_running:
            schedule.run_pending()
            # Sleep for 1 minute between checks
            threading.Event().wait(60)
    
    def start(self):
        """Start the email scheduler"""
        if not self.is_running:
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logger.info("Email scheduler started")
    
    def stop(self):
        """Stop the email scheduler"""
        if self.is_running:
            self.is_running = False
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5)
            logger.info("Email scheduler stopped")
    
    def send_signup_confirmation_now(self, player_email: str, player_name: str, signup_date: str) -> bool:
        """Send an immediate signup confirmation email"""
        try:
            return email_service.send_signup_confirmation(
                to_email=player_email,
                player_name=player_name,
                signup_date=signup_date
            )
        except Exception as e:
            logger.error(f"Error sending signup confirmation: {str(e)}")
            return False
    
    def send_game_invitation_now(self, to_email: str, player_name: str, inviter_name: str, game_date: str) -> bool:
        """Send an immediate game invitation email"""
        try:
            return email_service.send_game_invitation(
                to_email=to_email,
                player_name=player_name,
                inviter_name=inviter_name,
                game_date=game_date
            )
        except Exception as e:
            logger.error(f"Error sending game invitation: {str(e)}")
            return False
    
    def _run_matchmaking(self):
        """Run the matchmaking process and send notifications"""
        logger.info("Running scheduled matchmaking...")
        
        try:
            import requests
            # Call the matchmaking endpoint (assumes backend is running)
            response = requests.post("http://localhost:8000/matchmaking/create-and-notify")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Matchmaking completed: {result.get('matches_created', 0)} matches created, "
                           f"{result.get('notifications_sent', 0)} notifications sent")
            else:
                logger.error(f"Matchmaking endpoint returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error running scheduled matchmaking: {str(e)}")

# Global email scheduler instance
email_scheduler = EmailScheduler()

def get_email_scheduler() -> EmailScheduler:
    """Get the global email scheduler instance"""
    return email_scheduler