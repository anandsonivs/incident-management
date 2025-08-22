from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base import Base

class EscalationPolicy(Base):
    """Model for storing escalation policies."""
    __tablename__ = "escalation_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    conditions = Column(JSON, nullable=False, default=dict)
    steps = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    escalation_events = relationship("EscalationEvent", back_populates="policy")

    def __repr__(self):
        return f"<EscalationPolicy {self.name}>"


class EscalationEvent(Base):
    """Model for tracking escalation events for incidents."""
    __tablename__ = "escalation_events"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("escalation_policies.id"), nullable=False)
    step = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # pending, in_progress, completed, failed
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    metadata_ = Column("metadata", JSON, default=dict)

    # Relationships
    incident = relationship("Incident", back_populates="escalation_events")
    policy = relationship("EscalationPolicy", back_populates="escalation_events")

    def __repr__(self):
        return f"<EscalationEvent {self.id} for Incident {self.incident_id}>"
