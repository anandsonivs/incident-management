from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.notification import NotificationHistory
from app.crud import crud_notification

router = APIRouter()

@router.get("/", response_model=List[NotificationHistory])
def get_all_notifications(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get all notifications, sorted by most recent first."""
    notifications = crud_notification.get_all_notifications(
        db, skip=skip, limit=limit
    )
    return notifications

@router.get("/history", response_model=List[NotificationHistory])
def get_notification_history(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get notification history for the current user."""
    notifications = crud_notification.get_user_notifications(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return notifications

@router.get("/incidents/{incident_id}/notifications", response_model=List[NotificationHistory])
def get_incident_notifications(
    incident_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get notification history for a specific incident."""
    notifications = crud_notification.get_incident_notifications(
        db, incident_id=incident_id, skip=skip, limit=limit
    )
    return notifications
