# Import Base from db.base to make it available as models.Base
from app.db.base import Base

# Import all models here so they're properly registered with SQLAlchemy
from .user import User
from .incident import (
    Incident,
    IncidentStatus,
    IncidentSeverity,
    IncidentAssignment,
    IncidentComment,
    TimelineEvent,
    TimelineEventType,
)
from .notification_preference import NotificationPreference
from .notification import Notification, NotificationStatus, NotificationChannel
from .escalation import EscalationPolicy, EscalationEvent

# This ensures that all models are imported and SQLAlchemy can discover them
__all__ = [
    'Base',
    'Incident',
    'IncidentStatus',
    'IncidentSeverity',
    'IncidentAssignment',
    'IncidentComment',
    'TimelineEvent',
    'TimelineEventType',
    'User',
    'NotificationPreference',
    'Notification',
    'NotificationStatus',
    'NotificationChannel',
    'EscalationPolicy',
    'EscalationEvent',
]
