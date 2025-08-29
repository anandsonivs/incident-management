from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.notification import Notification, NotificationStatus, NotificationChannel
from app.schemas.notification import NotificationCreate, NotificationHistory

def create_notification(
    db: Session,
    *,
    incident_id: int,
    recipient: str,
    title: str,
    message: str,
    channel: NotificationChannel = NotificationChannel.EMAIL,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    metadata: Optional[dict] = None
) -> Notification:
    """Create a new notification."""
    notification_data = {
        "incident_id": incident_id,
        "recipient": recipient,
        "title": title,
        "message": message,
        "channel": channel,
        "action_type": action_type,
        "metadata_": metadata or {}
    }
    
    if user_id:
        notification_data["user_id"] = user_id
    
    notification = Notification(**notification_data)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def get_user_notifications(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[NotificationHistory]:
    """Get notification history for a user."""
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        NotificationHistory(
            id=notification.id,
            user_id=notification.user_id,
            incident_id=notification.incident_id,
            title=notification.title,
            message=notification.message,
            channel=notification.channel.value,
            status=notification.status.value,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
            metadata=notification.metadata_
        )
        for notification in notifications
    ]

def get_all_notifications(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[NotificationHistory]:
    """Get all notifications, sorted by most recent first."""
    notifications = db.query(Notification).order_by(
        Notification.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        NotificationHistory(
            id=notification.id,
            user_id=notification.user_id,
            incident_id=notification.incident_id,
            title=notification.title,
            message=notification.message,
            channel=notification.channel.value,
            status=notification.status.value,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
            metadata=notification.metadata_
        )
        for notification in notifications
    ]

def get_incident_notifications(
    db: Session, 
    incident_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[NotificationHistory]:
    """Get notification history for a specific incident."""
    notifications = db.query(Notification).filter(
        Notification.incident_id == incident_id
    ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        NotificationHistory(
            id=notification.id,
            user_id=notification.user_id,
            incident_id=notification.incident_id,
            title=notification.title,
            message=notification.message,
            channel=notification.channel.value,
            status=notification.status.value,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
            metadata=notification.metadata_
        )
        for notification in notifications
    ]

def mark_notification_sent(
    db: Session,
    notification_id: int,
    sent_at: Optional[datetime] = None
) -> Notification:
    """Mark a notification as sent."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.status = NotificationStatus.SENT
        notification.sent_at = sent_at or datetime.utcnow()
        db.commit()
        db.refresh(notification)
    return notification

def mark_notification_delivered(
    db: Session,
    notification_id: int,
    delivered_at: Optional[datetime] = None
) -> Notification:
    """Mark a notification as delivered."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.status = NotificationStatus.DELIVERED
        notification.delivered_at = delivered_at or datetime.utcnow()
        db.commit()
        db.refresh(notification)
    return notification

def mark_notification_failed(
    db: Session,
    notification_id: int,
    error_message: str
) -> Notification:
    """Mark a notification as failed."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.status = NotificationStatus.FAILED
        notification.error_message = error_message
        db.commit()
        db.refresh(notification)
    return notification
