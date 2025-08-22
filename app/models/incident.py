from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, JSON, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum
from datetime import datetime

class IncidentStatus(str, enum.Enum):
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SNOOZED = "snoozed"

class IncidentSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.TRIGGERED, nullable=False)
    severity = Column(Enum(IncidentSeverity), default=IncidentSeverity.MEDIUM, nullable=False)
    source = Column(String, default="elastic_apm")
    service = Column(String, index=True)
    alert_id = Column(String, unique=True, index=True)  # External alert ID from Elastic APM
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    snoozed_until = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    
    # Relationships
    assignments = relationship("IncidentAssignment", back_populates="incident")
    comments = relationship("IncidentComment", back_populates="incident")
    timeline_events = relationship("TimelineEvent", back_populates="incident")
    escalation_events = relationship("EscalationEvent", back_populates="incident")

class IncidentAssignment(Base):
    __tablename__ = "incident_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    incident = relationship("Incident", back_populates="assignments")
    user = relationship("User", back_populates="incident_assignments")

class IncidentComment(Base):
    __tablename__ = "incident_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    incident = relationship("Incident", back_populates="comments")
    user = relationship("User")

class TimelineEventType(str, enum.Enum):
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"
    COMMENT_ADDED = "comment_added"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"

class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    event_type = Column(Enum(TimelineEventType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    data = Column(JSON, default=dict)
    
    incident = relationship("Incident", back_populates="timeline_events")
    
# User model is defined in user.py
