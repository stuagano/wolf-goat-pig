"""
Messages Router

Daily message board for player communication.
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from .. import database, models, schemas
from ..utils.time import utc_now

logger = logging.getLogger("app.routers.messages")

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/daily", response_model=list[schemas.DailyMessageResponse])
def get_daily_messages(date: str = Query(description="YYYY-MM-DD format")):  # type: ignore
    """Get all messages for a specific date."""
    try:
        db = database.SessionLocal()

        messages = (
            db.query(models.DailyMessage)
            .filter(models.DailyMessage.date == date, models.DailyMessage.is_active == 1)
            .order_by(models.DailyMessage.message_time)
            .all()
        )

        return [schemas.DailyMessageResponse.from_orm(message) for message in messages]

    except Exception as e:
        logger.error(f"Error getting messages for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {e!s}")
    finally:
        db.close()


@router.post("", response_model=schemas.DailyMessageResponse)
def create_message(message: schemas.DailyMessageCreate):  # type: ignore
    """Create a new daily message."""
    try:
        db = database.SessionLocal()

        db_message = models.DailyMessage(
            date=message.date,
            player_profile_id=message.player_profile_id or 1,
            player_name=message.player_name or "Anonymous",
            message=message.message,
            message_time=utc_now().isoformat(),
            is_active=1,
            created_at=utc_now().isoformat(),
            updated_at=utc_now().isoformat(),
        )

        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        logger.info(f"Created message {db_message.id} for date {message.date}")
        return schemas.DailyMessageResponse.from_orm(db_message)

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create message: {e!s}")
    finally:
        db.close()


@router.put("/{message_id}", response_model=schemas.DailyMessageResponse)
def update_message(message_id: int, message_update: schemas.DailyMessageUpdate):  # type: ignore
    """Update an existing message."""
    try:
        db = database.SessionLocal()

        db_message = db.query(models.DailyMessage).filter(models.DailyMessage.id == message_id).first()
        if not db_message:
            raise HTTPException(status_code=404, detail="Message not found")

        if message_update.message is not None:
            db_message.message = message_update.message  # type: ignore
            db_message.updated_at = utc_now().isoformat()  # type: ignore

        db.commit()
        db.refresh(db_message)

        logger.info(f"Updated message {message_id}")
        return schemas.DailyMessageResponse.from_orm(db_message)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update message: {e!s}")
    finally:
        db.close()


@router.delete("/{message_id}")
def delete_message(message_id: int):  # type: ignore
    """Delete (deactivate) a message."""
    try:
        db = database.SessionLocal()

        db_message = db.query(models.DailyMessage).filter(models.DailyMessage.id == message_id).first()
        if not db_message:
            raise HTTPException(status_code=404, detail="Message not found")

        db_message.is_active = 0  # type: ignore
        db_message.updated_at = utc_now().isoformat()  # type: ignore

        db.commit()

        logger.info(f"Deleted message {message_id}")
        return {"message": "Message deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {e!s}")
    finally:
        db.close()
