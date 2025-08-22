# Import the Base class from base_class
from app.db.base_class import Base

# Import the database engine and SessionLocal from session.py
from app.db.session import engine, SessionLocal

# Import all models here so they're properly registered with SQLAlchemy's metadata
# This is necessary for 'autogenerate' to work properly
from app.models.team import Team
from app.models.user import User, UserRole
from app.models.incident import (
    Incident, IncidentStatus, IncidentSeverity, IncidentAssignment, 
    IncidentComment, TimelineEvent, TimelineEventType
)
from app.models.notification_preference import NotificationPreference
from app.models.escalation import EscalationPolicy, EscalationEvent
