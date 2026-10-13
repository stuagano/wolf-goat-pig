"""
Email Scheduler Service for Wolf Goat Pig Application

This module handles scheduling and sending automated emails based on user preferences.
"""

import logging
import threading
from typing import Any

from sqlalchemy.orm import Session

import schedule

from ..database import SessionLocal
from . import sunday_reminder, weekly_highlights
from .email_service import get_email_service
from .pairing_scheduler_service import PairingSchedulerService

logger = logging.getLogger(__name__)


class EmailScheduler:
    """Service for scheduling and sending automated emails"""

    # Public job registry: maps a stable Cloud Scheduler job key to the bound
    # method that runs exactly ONE cycle. Each target method opens/closes its own
    # DB session and catches its own errors, so it is safe to invoke one-shot from
    # the /internal/jobs/* HTTP endpoints (Phase 4 — Cloud Scheduler drives these
    # instead of the in-process `schedule` thread). Keep keys in sync with
    # deploy/gcp/phase4-scheduling/10-create-scheduler-jobs.sh.
    JOB_METHODS: dict[str, str] = {
        "sunday-reminder": "_send_sunday_reminder",
        "weekly-summaries": "_send_weekly_summaries",
        "saturday-pairings": "_run_saturday_pairings",
        "legacy-rounds-sync": "_sync_legacy_rounds",
        "pending-sheet-syncs": "_process_pending_sheet_syncs",
        "ghin-sync": "_sync_ghin_handicaps",
    }

    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self._setup_schedules()

    def _setup_schedules(self):
        """Set up the email scheduling jobs"""
        # The Thursday Sunday-game nudge and Monday league highlights are driven only by
        # GitHub Actions crons (.github/workflows/sunday-reminder.yml, weekly-highlights.yml).

        # Schedule Saturday afternoon pairing generation for Sunday games
        # Runs at 2:00 PM every Saturday to generate pairings and notify players
        schedule.every().saturday.at("14:00").do(self._run_saturday_pairings)

        # Sync Google Sheets round history into legacy_rounds table every 2 hours.
        # Direct DB call — no HTTP, no deadlock risk.
        schedule.every(2).hours.do(self._sync_legacy_rounds)

        # Drain the pending sheet sync queue once daily at midnight.
        schedule.every().day.at("00:00").do(self._process_pending_sheet_syncs)

        # Sync GHIN handicaps daily at 6 AM. Keeps stored handicap data fresh
        # so /leaderboard/ghin-enhanced never needs a live API call.
        schedule.every().day.at("06:00").do(self._sync_ghin_handicaps)

        # DISABLED: These tasks make HTTP requests to the same server which causes deadlocks
        # Use external cron jobs or proper async background tasks instead
        # schedule.every().day.at("10:00").do(self._run_matchmaking)
        # schedule.every().day.at("02:00").do(self._sync_google_sheets)

        logger.info("Email schedules set up successfully")

    def _get_db(self) -> Session:
        """Get a database session"""
        return SessionLocal()

    def _send_sunday_reminder(self, dry_run: bool = False) -> dict[str, Any]:
        """Thursday nudge for the coming Sunday's game. Errors propagate so the cron fails loudly."""
        db = self._get_db()
        try:
            return sunday_reminder.run(db, dry_run=dry_run)
        finally:
            db.close()

    def _send_weekly_summaries(self, dry_run: bool = False) -> dict[str, Any]:
        """Email last week's league highlights to everyone not opted out.

        Unlike the other jobs, errors propagate so the cron run fails loudly.
        """
        db = self._get_db()
        try:
            return weekly_highlights.run(db, dry_run=dry_run)
        finally:
            db.close()

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

    # Jobs whose method accepts dry_run=True (compute + report, send nothing).
    DRY_RUN_JOBS = {"weekly-summaries", "sunday-reminder"}

    def run_job(self, job_name: str, dry_run: bool = False) -> dict:
        """Run a single scheduled job once, by its registry key.

        Used by the /internal/jobs/* endpoints so Cloud Scheduler can drive the
        periodic work instead of the in-process thread. Raises KeyError for an
        unknown job. The underlying method handles its own DB session and errors;
        because Cloud Scheduler is at-least-once, each target must stay idempotent
        (design doc §12). A dict returned by the job is merged into the response.
        """
        method_name = self.JOB_METHODS.get(job_name)
        if method_name is None:
            raise KeyError(job_name)
        logger.info("Running scheduled job '%s' one-shot via run_job()", job_name)
        method = getattr(self, method_name)
        result = method(dry_run=True) if dry_run else method()
        return {"job": job_name, "status": "completed", **(result if isinstance(result, dict) else {})}

    def send_signup_confirmation_now(self, player_email: str, player_name: str, signup_date: str) -> bool:
        """Send an immediate signup confirmation email"""
        try:
            return get_email_service().send_signup_confirmation(
                to_email=player_email, player_name=player_name, signup_date=signup_date
            )
        except Exception as e:
            logger.error(f"Error sending signup confirmation: {e!s}")
            return False

    def send_game_invitation_now(self, to_email: str, player_name: str, inviter_name: str, game_date: str) -> bool:
        """Send an immediate game invitation email"""
        try:
            result = get_email_service().send_game_invitation(  # type: ignore[attr-defined]
                to_email=to_email,
                player_name=player_name,
                inviter_name=inviter_name,
                game_date=game_date,
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Error sending game invitation: {e!s}")
            return False

    def _run_saturday_pairings(self):
        """
        Run the Saturday afternoon pairing job for Sunday games.

        Generates random pairings for the next Sunday and sends email notifications
        to all signed-up players with their group assignments.
        """
        logger.info("Running Saturday pairing job...")
        db = self._get_db()

        try:
            result = PairingSchedulerService.run_saturday_job(db)

            if result["success"]:
                logger.info(
                    f"Saturday pairing job completed: {result['team_count']} teams generated, "
                    f"{result['emails_sent']} emails sent for {result['game_date']}"
                )
            else:
                logger.warning(f"Saturday pairing job did not generate pairings: {result['message']}")

        except Exception as e:
            logger.error(f"Error in Saturday pairing job: {e!s}")
        finally:
            db.close()

    def _sync_legacy_rounds(self):
        """Sync Google Sheets round history into the legacy_rounds DB table.

        Runs every 2 hours. Direct DB call — safe to run in background thread.
        """
        from datetime import UTC
        from datetime import datetime as dt

        from ..models import LegacyRound
        from ..services.unified_data_service import get_unified_data_service

        logger.info("Syncing legacy rounds from Google Sheets...")
        db = self._get_db()
        try:
            svc = get_unified_data_service(db=db)
            rounds = svc.get_all_rounds(include_database=False, use_sheet_cache=False)
            if not rounds:
                logger.warning("Legacy rounds sync: no rounds returned from sheets")
                return

            synced_at = dt.now(UTC).isoformat()
            db.query(LegacyRound).filter(LegacyRound.source.in_(["primary_sheet", "writable_sheet"])).delete(
                synchronize_session=False
            )
            for r in rounds:
                db.add(
                    LegacyRound(
                        date=r.date_sortable,
                        group=r.group,
                        member=r.member,
                        score=r.score,
                        location=r.location or "",
                        duration=r.duration,
                        source=r.source,
                        synced_at=synced_at,
                    )
                )
            db.commit()
            logger.info("Legacy rounds sync complete: %d rows written", len(rounds))

            # Keep the canonical player roster in lockstep with the dropdown by
            # reconciling it against the players seen in round history. Isolated
            # so a roster-sync bug can never take down the load-bearing rounds
            # sync (rounds are already committed above).
            try:
                from ..services.legacy_player_service import sync_roster_from_members

                sync_roster_from_members({r.member for r in rounds}, db=db)
            except Exception as roster_exc:
                logger.warning("Roster reconcile skipped (rounds sync unaffected): %s", roster_exc)
        except Exception as exc:
            logger.error("Legacy rounds sync failed: %s", exc)
            db.rollback()
        finally:
            db.close()

    def _process_pending_sheet_syncs(self):
        """Drain the pending_sheet_syncs queue.

        For each pending row:
          1. Dedup against legacy_rounds (same date + group + player set)
             - All players present AND all scores match → "duplicate", skip
             - Players match but any score differs → "update", overwrite in sheet
             - No matching round found → "new", append to sheet
          2. Write to sheet if new/update
          3. Mark row processed; trigger a legacy_rounds refresh on any writes.

        The app records per-hole scores; the legacy sheet stores only round totals.
        player_scores in the queue are expected to be the summed totals.
        """
        from datetime import UTC
        from datetime import datetime as dt

        from ..models import PendingSheetSync
        from .spreadsheet_sync_service import get_spreadsheet_sync_service

        db = self._get_db()
        try:
            pending = (
                db.query(PendingSheetSync)
                .filter(PendingSheetSync.status == "pending")
                .order_by(PendingSheetSync.created_at)
                .all()
            )
            if not pending:
                return

            logger.info("Processing %d pending sheet sync(s)", len(pending))
            wrote_any = False

            for job in pending:
                job.status = "processing"
                db.commit()

                try:
                    action = self._dedup_action(db, job)
                    job.dedup_action = action

                    if action == "duplicate":
                        logger.info("Skipping duplicate round %s group=%s", job.date, job.group)
                    else:
                        logger.info(
                            "Writing %s round %s group=%s to sheet",
                            action,
                            job.date,
                            job.group,
                        )
                        game_date = dt.strptime(job.date, "%Y-%m-%d")
                        svc = get_spreadsheet_sync_service()
                        success = svc.sync_completed_game(
                            game_date=game_date,
                            group=job.group,
                            location=job.location,
                            player_scores=job.player_scores,
                            duration=job.duration,
                        )
                        if not success:
                            raise RuntimeError("sync_completed_game returned False")
                        wrote_any = True

                    job.status = "done"
                    job.processed_at = dt.now(UTC).isoformat()
                    db.commit()

                except Exception as exc:
                    logger.error("Sheet sync job %d failed: %s", job.id, exc)
                    job.status = "failed"
                    job.error = str(exc)
                    job.processed_at = dt.now(UTC).isoformat()
                    db.commit()

            if wrote_any:
                logger.info("Sheet writes completed — refreshing legacy_rounds cache")
                self._sync_legacy_rounds()

        except Exception as exc:
            logger.error("_process_pending_sheet_syncs failed: %s", exc)
        finally:
            db.close()

    def _dedup_action(self, db, job) -> str:
        """Return 'duplicate', 'update', or 'new' for a PendingSheetSync job.

        Dedup key: date + group + exact set of player names.
        Score comparison: app's summed player_scores vs. stored legacy scores.
        """
        from ..models import LegacyRound

        incoming_players = set(job.player_scores.keys())

        existing = db.query(LegacyRound).filter(LegacyRound.date == job.date, LegacyRound.group == job.group).all()
        if not existing:
            return "new"

        existing_players = {r.member for r in existing}
        if existing_players != incoming_players:
            # Different player set — treat as a new (distinct) round
            return "new"

        # Same player set — compare scores
        existing_scores = {r.member: r.score for r in existing}
        for player, score in job.player_scores.items():
            if existing_scores.get(player) != score:
                return "update"

        return "duplicate"

    def _sync_ghin_handicaps(self):
        """Sync GHIN handicaps for all players with GHIN IDs.

        Runs daily at 6 AM so /leaderboard/ghin-enhanced can serve
        from stored data without a live API call on every request.
        """
        import asyncio

        from ..services.ghin_service import GHINService

        db = self._get_db()
        try:
            ghin_service = GHINService(db)
            loop = asyncio.new_event_loop()
            try:
                initialized = loop.run_until_complete(ghin_service.initialize())
                if not initialized:
                    logger.warning("GHIN sync skipped: service not available (credentials missing or auth failed)")
                    return
                results = loop.run_until_complete(ghin_service.sync_all_players_handicaps())
                synced = results.get("synced", 0)
                failed = results.get("failed", 0)
                logger.info("GHIN handicap sync complete: %d synced, %d failed", synced, failed)
            finally:
                loop.close()
        except Exception as exc:
            logger.error("GHIN handicap sync failed: %s", exc)
        finally:
            db.close()

    def _run_matchmaking(self):
        """
        Run the matchmaking process and send notifications.

        DISABLED: This method makes HTTP requests to the same server which causes deadlocks
        when running in a background thread. Use external cron jobs to call the endpoint
        instead, or refactor to use proper async background tasks.
        """
        logger.warning("_run_matchmaking is disabled - use external scheduler to call /matchmaking/create-and-notify")
        return

        # COMMENTED OUT - CAUSES DEADLOCK
        # logger.info("Running scheduled matchmaking...")
        #
        # try:
        #     import requests
        #     # Call the matchmaking endpoint (assumes backend is running)
        #     response = requests.post("http://localhost:8000/matchmaking/create-and-notify")
        #
        #     if response.status_code == 200:
        #         result = response.json()
        #         logger.info(f"Matchmaking completed: {result.get('matches_created', 0)} matches created, "
        #                    f"{result.get('notifications_sent', 0)} notifications sent")
        #     else:
        #         logger.error(f"Matchmaking endpoint returned status {response.status_code}")
        #
        # except Exception as e:
        #     logger.error(f"Error running scheduled matchmaking: {str(e)}")

    def _sync_google_sheets(self):
        """
        Sync historical player data from Google Sheets once daily.

        DISABLED: This method makes HTTP requests to the same server which causes deadlocks
        when running in a background thread. Use external cron jobs to call the endpoint
        instead, or refactor to use proper async background tasks.

        Additionally, the original code had the wrong port (10000 instead of 8000).
        """
        logger.warning(
            "_sync_google_sheets is disabled - use external scheduler to call /sheet-integration/sync-wgp-sheet"
        )
        return

        # COMMENTED OUT - CAUSES DEADLOCK AND HAD WRONG PORT
        # logger.info("Running scheduled Google Sheets sync...")
        #
        # try:
        #     import httpx
        #
        #     # Hardcoded sheet URL (same as in SheetSyncContext)
        #     sheet_id = "141s8V_UACdBc8Xg17W0UhWxd08BMbEImkXOSPa66RfQ"
        #     gid = "0"
        #     csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        #
        #     # Call the sync endpoint directly (internal call, no rate limiting for scheduled jobs)
        #     # Use a special header to bypass rate limiting for scheduled jobs
        #     import requests
        #     # BUG: Port should be 8000 (or from env), not hardcoded 10000
        #     response = requests.post(
        #         "http://localhost:10000/sheet-integration/sync-wgp-sheet",
        #         json={"csv_url": csv_url},
        #         headers={"X-Scheduled-Job": "true"},
        #         timeout=60
        #     )
        #
        #     if response.status_code == 200:
        #         result = response.json()
        #         players_synced = result.get('player_count', 0)
        #         logger.info(f"✅ Google Sheets sync completed successfully: {players_synced} players synced")
        #     elif response.status_code == 429:
        #         logger.warning("⚠️ Sheet sync rate limited - will retry tomorrow")
        #     else:
        #         logger.error(f"❌ Sheet sync failed with status {response.status_code}: {response.text[:200]}")
        #
        # except Exception as e:
        #     logger.error(f"❌ Error running scheduled Google Sheets sync: {str(e)}")


# Global email scheduler instance
email_scheduler = EmailScheduler()


def get_email_scheduler() -> EmailScheduler:
    """Get the global email scheduler instance"""
    return email_scheduler
