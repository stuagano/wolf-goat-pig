"""
Email Routes Router

Email sending, scheduler management, and status endpoints.
"""

import logging

from fastapi import APIRouter, HTTPException

from ..services.email_service import get_email_service
from ..state.app_state import get_email_scheduler, set_email_scheduler

logger = logging.getLogger("app.routers.email_routes")

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/send-test")
async def send_test_email(email_data: dict):  # type: ignore
    """Send a test email to verify email service configuration"""
    try:
        email_service = get_email_service()

        if not email_service.is_configured:  # type: ignore
            raise HTTPException(
                status_code=503,
                detail="Email service not configured. Please set SMTP_USER, SMTP_PASSWORD, and SMTP_HOST environment variables.",
            )

        to_email = email_data.get("to_email")
        if not to_email:
            raise HTTPException(status_code=400, detail="to_email is required")

        success = email_service.send_signup_confirmation(
            to_email=to_email,
            player_name=email_data.get("player_name", "Test Player"),
            signup_date=email_data.get("signup_date", "Tomorrow"),
        )

        if success:
            return {"message": "Test email sent successfully", "to_email": to_email}
        raise HTTPException(status_code=500, detail="Failed to send test email")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {e!s}")


@router.get("/status")
async def get_email_service_status():
    """Check if email service is properly configured"""
    try:
        email_service = get_email_service()
        return email_service.get_provider_status()

    except Exception as e:
        logger.error(f"Error checking email service status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check email status: {e!s}")


@router.post("/signup-confirmation")
async def send_signup_confirmation_email(email_data: dict):  # type: ignore
    """Send signup confirmation email"""
    try:
        email_service = get_email_service()

        if not email_service.is_configured:  # type: ignore
            raise HTTPException(status_code=503, detail="Email service not configured")

        required_fields = ["to_email", "player_name", "signup_date"]
        missing_fields = [field for field in required_fields if not email_data.get(field)]

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}",
            )

        success = email_service.send_signup_confirmation(
            to_email=email_data["to_email"],
            player_name=email_data["player_name"],
            signup_date=email_data["signup_date"],
        )

        if success:
            return {
                "message": "Signup confirmation email sent",
                "to_email": email_data["to_email"],
            }
        raise HTTPException(status_code=500, detail="Failed to send signup confirmation email")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending signup confirmation email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e!s}")


@router.post("/daily-reminder")
async def send_daily_reminder_email(email_data: dict):  # type: ignore
    """Send daily signup reminder email"""
    try:
        email_service = get_email_service()

        if not email_service.is_configured:  # type: ignore
            raise HTTPException(status_code=503, detail="Email service not configured")

        required_fields = ["to_email", "player_name"]
        missing_fields = [field for field in required_fields if not email_data.get(field)]

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}",
            )

        success = email_service.send_daily_signup_reminder(  # type: ignore
            to_email=email_data["to_email"],
            player_name=email_data["player_name"],
            available_dates=email_data.get("available_dates", []),
        )

        if success:
            return {
                "message": "Daily reminder email sent",
                "to_email": email_data["to_email"],
            }
        raise HTTPException(status_code=500, detail="Failed to send daily reminder email")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending daily reminder email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e!s}")


@router.post("/weekly-summary")
async def send_weekly_summary_email(email_data: dict):  # type: ignore
    """Send weekly summary email"""
    try:
        email_service = get_email_service()

        if not email_service.is_configured:  # type: ignore
            raise HTTPException(status_code=503, detail="Email service not configured")

        required_fields = ["to_email", "player_name"]
        missing_fields = [field for field in required_fields if not email_data.get(field)]

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}",
            )

        success = email_service.send_weekly_summary(  # type: ignore
            to_email=email_data["to_email"],
            player_name=email_data["player_name"],
            summary_data=email_data.get("summary_data", {}),
        )

        if success:
            return {
                "message": "Weekly summary email sent",
                "to_email": email_data["to_email"],
            }
        raise HTTPException(status_code=500, detail="Failed to send weekly summary email")

    except HTTPException:
        raise


@router.post("/initialize-scheduler")
async def initialize_email_scheduler():
    """Initialize the email scheduler on demand"""
    try:
        # Check if already initialized
        if get_email_scheduler() is not None:
            return {  # type: ignore
                "status": "already_initialized",
                "message": "Email scheduler is already running",
            }

        # Import and initialize the scheduler
        from ..services.email_scheduler import email_scheduler as scheduler_instance

        set_email_scheduler(scheduler_instance)
        scheduler_instance.start()

        logger.info("📧 Email scheduler initialized on demand")

        return {
            "status": "success",
            "message": "Email scheduler initialized successfully",
            "scheduled_jobs": ["daily_reminders", "weekly_summaries"],
        }

    except Exception as e:
        logger.error(f"Failed to initialize email scheduler: {e!s}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize email scheduler: {e!s}")


@router.get("/scheduler-status")
async def get_email_scheduler_status():
    """Get the status of the email scheduler"""
    _scheduler = get_email_scheduler()
    return {
        "initialized": _scheduler is not None,
        "running": _scheduler is not None and hasattr(_scheduler, "_started") and _scheduler._started,
        "message": (
            "Scheduler running"
            if _scheduler
            else "Scheduler not initialized. Call /email/initialize-scheduler to start."
        ),
    }
