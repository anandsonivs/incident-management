from typing import List, Optional, Any, Dict
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.crud.base import CRUDBase
from app.models.incident import (
    Incident, IncidentStatus, TimelineEvent, TimelineEventType, 
    IncidentAssignment, IncidentComment
)
from app.models.escalation import EscalationEvent
from app.schemas.incident import (
    IncidentCreate, IncidentUpdate, TimelineEventCreate, 
    AssignmentCreate, CommentCreate
)

class CRUDIncident(CRUDBase[Incident, IncidentCreate, IncidentUpdate]):
    def get_multi_by_status(
        self, db: Session, *, status: IncidentStatus, skip: int = 0, limit: int = 100
    ) -> List[Incident]:
        return (
            db.query(self.model)
            .filter(Incident.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
    def get_with_escalations(self, db: Session, id: int) -> Optional[Incident]:
        """Get an incident with its escalation events."""
        return (
            db.query(self.model)
            .options(joinedload(Incident.escalation_events).joinedload(EscalationEvent.policy))
            .filter(Incident.id == id)
            .first()
        )

    def get_by_alert_id(self, db: Session, *, alert_id: str) -> Optional[Incident]:
        return db.query(Incident).filter(Incident.alert_id == alert_id).first()

    def create_with_owner(
        self, db: Session, *, obj_in: IncidentCreate, owner_id: int
    ) -> Incident:
        db_obj = self.model(
            **obj_in.dict(),
            created_by=owner_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_status(
        self, db: Session, *, db_obj: Incident, status: IncidentStatus, user_id: Optional[int] = None
    ) -> Incident:
        previous_status = db_obj.status
        db_obj.status = status
        
        # Update timestamps based on status
        now = datetime.utcnow()
        if status == IncidentStatus.RESOLVED:
            db_obj.resolved_at = now
        elif status == IncidentStatus.ACKNOWLEDGED:
            db_obj.acknowledged_at = now
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def add_timeline_event(
        self, db: Session, *, incident_id: int, event_type: TimelineEventType, data: dict, user_id: Optional[int] = None
    ) -> TimelineEvent:
        event = TimelineEvent(
            incident_id=incident_id,
            event_type=event_type,
            data=data,
            created_by=user_id
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def get_assignment_by_incident_and_user(
        self, db: Session, *, incident_id: int, user_id: int
    ) -> Optional[IncidentAssignment]:
        return (
            db.query(IncidentAssignment)
            .filter(
                IncidentAssignment.incident_id == incident_id,
                IncidentAssignment.user_id == user_id
            )
            .first()
        )

    def assign_user(
        self, db: Session, *, incident_id: int, user_id: int, assigned_by: Optional[int] = None
    ) -> IncidentAssignment:
        # Check if assignment already exists
        existing = self.get_assignment_by_incident_and_user(
            db, incident_id=incident_id, user_id=user_id
        )
        
        if existing:
            return existing
            
        db_obj = IncidentAssignment(
            incident_id=incident_id,
            user_id=user_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def add_comment(
        self, db: Session, *, incident_id: int, user_id: int, content: str
    ) -> IncidentComment:
        comment = IncidentComment(
            incident_id=incident_id,
            user_id=user_id,
            content=content
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    def snooze_incident(
        self, db: Session, *, db_obj: Incident, snooze_until: datetime
    ) -> Incident:
        db_obj.status = IncidentStatus.SNOOZED
        db_obj.snoozed_until = snooze_until
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# Initialize CRUD instances
incident = CRUDIncident(Incident)
timeline_event = CRUDBase[TimelineEvent, TimelineEventCreate, TimelineEventCreate](TimelineEvent)
assignment = CRUDBase[IncidentAssignment, AssignmentCreate, AssignmentCreate](IncidentAssignment)
comment = CRUDBase[IncidentComment, CommentCreate, CommentCreate](IncidentComment)
