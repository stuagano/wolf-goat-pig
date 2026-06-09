"""
Notifications Router

Exposes in-app notifications to the frontend:
- GET  /notifications       list unread (or all) notifications for the current user
- POST /notifications/{id}/read   mark one read
- POST /notifications/read-all    mark all read
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Notification, PlayerProfile
from ..services.auth_service import get_current_user

logger = logging.getLogger("app.routers.notifications")

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def get_notifications(
    unread_only: bool = True,
    limit: int = 20,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(
        Notification.player_profile_id == current_user.id
    )
    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712
    notifications = (
        query.order_by(Notification.created_at.desc()).limit(limit).all()
    )
    return [
        {
            "id": n.id,
            "notification_type": n.notification_type,
            "message": n.message,
            "data": n.data,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]


@router.get("/unread-count")
def get_unread_count(
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = (
        db.query(Notification)
        .filter(
            Notification.player_profile_id == current_user.id,
            Notification.is_read == False,  # noqa: E712
        )
        .count()
    )
    return {"unread_count": count}


@router.post("/read-all")
def mark_all_read(
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = (
        db.query(Notification)
        .filter(
            Notification.player_profile_id == current_user.id,
            Notification.is_read == False,  # noqa: E712
        )
        .update({"is_read": True})
    )
    db.commit()
    return {"marked_read": updated}


@router.post("/{notification_id}/read")
def mark_read(
    notification_id: int,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.player_profile_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return {"ok": True}
