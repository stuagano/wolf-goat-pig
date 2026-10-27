"""
Notifications Router

Exposes in-app notifications to the frontend:
- GET  /notifications       list unread (or all) notifications for the current user
- POST /notifications/{id}/read   mark one read
- POST /notifications/read-all    mark all read
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Notification, PlayerProfile
from ..services.auth_service import get_current_user
from ..utils.admin_auth import is_admin_profile

logger = logging.getLogger("app.routers.notifications")

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def get_notifications(
    unread_only: bool = True,
    limit: int = Query(default=20, ge=1, le=100),
    types: str | None = None,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(Notification.player_profile_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    if types:
        query = query.filter(Notification.notification_type.in_(types.split(",")))
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    # Expose channel trouble on the existing item, never enqueue recursively.
    from ..models import RoundDelivery

    issue_ids = [n.data.get("issue_id") for n in notifications if n.notification_type == "round_conflict" and n.data]
    trouble = {}
    if issue_ids:
        for row in (
            db.query(RoundDelivery)
            .filter(
                RoundDelivery.issue_id.in_(issue_ids),
                RoundDelivery.recipient_profile_id == current_user.id,
                RoundDelivery.status.in_(["failed", "uncertain", "unconfigured"]),
            )
            .all()
        ):
            trouble.setdefault(row.issue_id, {})[row.channel] = row.status
    return [
        {
            "id": n.id,
            "notification_type": n.notification_type,
            "message": n.message,
            "data": {**(n.data or {}), "delivery_health": trouble.get((n.data or {}).get("issue_id"), {})}
            if n.notification_type == "round_conflict"
            else n.data,
            "is_read": n.is_read,
            # Notification.created_at is a String column holding an ISO
            # timestamp, not a DateTime — it needs no further conversion.
            "created_at": n.created_at,
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
            Notification.is_read == False,
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
            Notification.is_read == False,
        )
        .update({"is_read": True})
    )
    db.commit()
    return {"marked_read": updated}


class RoundRequeue(BaseModel):
    issue_ids: list[str] = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=1000)


@router.post("/round-deliveries/requeue")
def requeue_round_alerts(
    request: RoundRequeue,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..services.round_delivery import requeue_round_deliveries

    if not is_admin_profile(current_user):
        raise HTTPException(403, "Administrator required")
    try:
        count = requeue_round_deliveries(
            db,
            request.issue_ids,
            actor_profile_id=current_user.id,
            reason=request.reason,
        )
        db.commit()
        return {"queued": count}
    except Exception:
        db.rollback()
        raise


@router.get("/round-deliveries/health")
def round_delivery_health(
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func

    from ..models import RoundDelivery
    from ..services.round_delivery import confirmed_recipient

    recipient = confirmed_recipient(db)
    if not is_admin_profile(current_user) and (not recipient or recipient.id != current_user.id):
        raise HTTPException(403, "Reviewer required")
    return {
        "configured": bool(recipient),
        "channels": [
            {"channel": channel, "status": status, "count": count}
            for channel, status, count in db.query(
                RoundDelivery.channel,
                RoundDelivery.status,
                func.count(RoundDelivery.id),
            )
            .group_by(RoundDelivery.channel, RoundDelivery.status)
            .all()
        ],
    }


@router.post("/{notification_id}/read")
def mark_read(
    notification_id: int,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.player_profile_id == current_user.id,
        )
        .first()
    )
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return {"ok": True}
