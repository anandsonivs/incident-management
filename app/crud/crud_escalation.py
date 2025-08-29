from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import models, schemas
from app.crud.base import CRUDBase

ModelType = TypeVar("ModelType", bound=models.Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=schemas.BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=schemas.BaseModel)

class CRUDEscalationPolicy(CRUDBase[models.EscalationPolicy, schemas.EscalationPolicyCreate, schemas.EscalationPolicyUpdate]):
    """CRUD operations for EscalationPolicy"""
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[models.EscalationPolicy]:
        """Get an escalation policy by name."""
        return db.query(models.EscalationPolicy).filter(models.EscalationPolicy.name == name).first()
    
    def get_active_policies(self, db: Session) -> List[models.EscalationPolicy]:
        """Get all active escalation policies."""
        return db.query(models.EscalationPolicy).filter(
            models.EscalationPolicy.is_active == True
        ).all()


class CRUDEscalationEvent(CRUDBase[models.EscalationEvent, schemas.EscalationEventCreate, dict]):
    """CRUD operations for EscalationEvent"""
    
    def get_by_incident(
        self, db: Session, *, incident_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.EscalationEvent]:
        """Get all escalation events for an incident."""
        from sqlalchemy.orm import joinedload
        return (
            db.query(models.EscalationEvent)
            .options(
                joinedload(models.EscalationEvent.incident).joinedload(models.Incident.team),
                joinedload(models.EscalationEvent.policy)
            )
            .filter(models.EscalationEvent.incident_id == incident_id)
            .order_by(models.EscalationEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_all_events(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[models.EscalationEvent]:
        """Get all escalation events, sorted by most recent first."""
        from sqlalchemy.orm import joinedload
        return (
            db.query(models.EscalationEvent)
            .options(
                joinedload(models.EscalationEvent.incident).joinedload(models.Incident.team),
                joinedload(models.EscalationEvent.policy)
            )
            .order_by(models.EscalationEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_pending_events(
        self, db: Session, *, before: Optional[datetime] = None
    ) -> List[models.EscalationEvent]:
        """Get all pending escalation events, optionally before a specific time."""
        query = db.query(models.EscalationEvent).filter(
            models.EscalationEvent.status == schemas.EscalationEventStatus.PENDING
        )
        
        if before:
            query = query.filter(models.EscalationEvent.triggered_at <= before)
            
        return query.all()
    
    def has_event_for_step(
        self, db: Session, *, incident_id: int, policy_id: int, step_index: int
    ) -> bool:
        """Return True if an event exists for a given incident/policy/step."""
        return db.query(models.EscalationEvent).filter(
            models.EscalationEvent.incident_id == incident_id,
            models.EscalationEvent.policy_id == policy_id,
            models.EscalationEvent.step == step_index,
        ).first() is not None
    
    def mark_as_completed(
        self, db: Session, *, db_obj: models.EscalationEvent, metadata: Optional[Dict[str, Any]] = None
    ) -> models.EscalationEvent:
        """Mark an escalation event as completed."""
        db_obj.status = schemas.EscalationEventStatus.COMPLETED
        db_obj.completed_at = datetime.utcnow()
        if metadata is not None:
            db_obj.metadata_ = {**db_obj.metadata_, **metadata}
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def mark_as_failed(
        self, db: Session, *, db_obj: models.EscalationEvent, error: str
    ) -> models.EscalationEvent:
        """Mark an escalation event as failed."""
        db_obj.status = schemas.EscalationEventStatus.FAILED
        db_obj.completed_at = datetime.utcnow()
        db_obj.metadata_ = {**db_obj.metadata_, "error": error}
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


escalation_policy = CRUDEscalationPolicy(models.EscalationPolicy)
escalation_event = CRUDEscalationEvent(models.EscalationEvent)
