from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db
from app.models.incident import IncidentStatus, TimelineEventType
from app.schemas.incident import (
    Incident, IncidentCreate, IncidentUpdate, IncidentWithRelations,
    Assignment, AssignmentCreate, Comment, CommentCreate, TimelineEvent
)

router = APIRouter()

@router.get("/", response_model=List[Incident])
def read_incidents(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[IncidentStatus] = None,
    service: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Retrieve incidents with optional filtering.
    """
    query = db.query(models.Incident)
    
    if status:
        query = query.filter(models.Incident.status == status)
    if service:
        query = query.filter(models.Incident.service == service)
    if severity:
        query = query.filter(models.Incident.severity == severity)
    
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=Incident, status_code=status.HTTP_201_CREATED)
def create_incident(
    *,
    db: Session = Depends(get_db),
    incident_in: IncidentCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Create new incident.
    """
    incident = crud.incident.create(db, obj_in=incident_in)
    
    # Add timeline event
    crud.incident.add_timeline_event(
        db,
        incident_id=incident.id,
        event_type=TimelineEventType.CREATED,
        data={"status": incident.status},
        user_id=current_user.id
    )
    
    return incident

@router.get("/{incident_id}", response_model=IncidentWithRelations)
def read_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get incident by ID.
    """
    incident = crud.incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return incident

@router.put("/{incident_id}", response_model=Incident)
def update_incident(
    *,
    db: Session = Depends(get_db),
    incident_id: int,
    incident_in: IncidentUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Update an incident.
    """
    incident = crud.incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    # Track status changes
    if incident_in.status and incident_in.status != incident.status:
        crud.incident.add_timeline_event(
            db,
            incident_id=incident_id,
            event_type=TimelineEventType.STATUS_CHANGED,
            data={"from": incident.status, "to": incident_in.status},
            user_id=current_user.id
        )
    
    updated = crud.incident.update(db, db_obj=incident, obj_in=incident_in)
    
    # If status changed to non-terminal, escalate via service
    if incident_in.status and incident_in.status not in [IncidentStatus.RESOLVED, IncidentStatus.SNOOZED]:
        from app.services.escalation import get_escalation_service
        escalation_service = get_escalation_service(db)
        escalation_service.check_and_escalate_incident(updated)
    
    return updated

@router.post("/{incident_id}/acknowledge", response_model=Incident)
def acknowledge_incident(
    *,
    db: Session = Depends(get_db),
    incident_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Acknowledge an incident.
    """
    incident = crud.incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    if incident.status == IncidentStatus.ACKNOWLEDGED:
        return incident
    
    incident = crud.incident.update_status(
        db, db_obj=incident, status=IncidentStatus.ACKNOWLEDGED
    )
    
    crud.incident.add_timeline_event(
        db,
        incident_id=incident_id,
        event_type=TimelineEventType.ACKNOWLEDGED,
        data={"by_user_id": current_user.id},
        user_id=current_user.id
    )
    
    return incident

@router.post("/{incident_id}/resolve", response_model=Incident)
def resolve_incident(
    *,
    db: Session = Depends(get_db),
    incident_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Resolve an incident.
    """
    incident = crud.incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    if incident.status == IncidentStatus.RESOLVED:
        return incident
    
    incident = crud.incident.update_status(
        db, db_obj=incident, status=IncidentStatus.RESOLVED
    )
    
    crud.incident.add_timeline_event(
        db,
        incident_id=incident_id,
        event_type=TimelineEventType.RESOLVED,
        data={"by_user_id": current_user.id},
        user_id=current_user.id
    )
    
    return incident

@router.post("/{incident_id}/snooze", response_model=Incident)
def snooze_incident(
    *,
    db: Session = Depends(get_db),
    incident_id: int,
    hours: int,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Snooze an incident for a specified number of hours.
    """
    incident = crud.incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    snooze_until = datetime.utcnow() + timedelta(hours=hours)
    incident = crud.incident.snooze_incident(
        db, db_obj=incident, snooze_until=snooze_until
    )
    
    crud.incident.add_timeline_event(
        db,
        incident_id=incident_id,
        event_type=TimelineEventType.SNOOZED,
        data={"until": snooze_until.isoformat(), "by_user_id": current_user.id},
        user_id=current_user.id
    )
    
    return incident

@router.post("/{incident_id}/assign")
def assign_incident(
    *,
    db: Session = Depends(get_db),
    incident_id: int,
    assignment_in: AssignmentCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Assign an incident to a user.
    """
    incident = crud.incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    user = crud.user.get(db, id=assignment_in.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if already assigned
    existing_assignment = (
        db.query(models.IncidentAssignment)
        .filter(
            models.IncidentAssignment.incident_id == incident_id,
            models.IncidentAssignment.user_id == assignment_in.user_id,
        )
        .first()
    )
    
    if existing_assignment:
        return existing_assignment
    
    assignment = crud.incident.assign_user(
        db, incident_id=incident_id, user_id=assignment_in.user_id, assigned_by=current_user.id
    )
    
    crud.incident.add_timeline_event(
        db,
        incident_id=incident_id,
        event_type=TimelineEventType.ASSIGNED,
        data={"user_id": assignment_in.user_id, "by_user_id": current_user.id},
        user_id=current_user.id
    )
    
    return assignment

@router.post("/{incident_id}/comments")
def create_comment(
    *,
    db: Session = Depends(get_db),
    incident_id: int,
    comment_in: CommentCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Add a comment to an incident.
    """
    incident = crud.incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    comment = crud.incident.add_comment(
        db, incident_id=incident_id, user_id=current_user.id, content=comment_in.content
    )
    
    crud.incident.add_timeline_event(
        db,
        incident_id=incident_id,
        event_type=TimelineEventType.COMMENT_ADDED,
        data={"comment_id": comment.id},
        user_id=current_user.id
    )
    
    return comment

@router.get("/{incident_id}/timeline")
def get_incident_timeline(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get timeline events for an incident.
    """
    incident = crud.incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    return db.query(models.TimelineEvent)\
        .filter(models.TimelineEvent.incident_id == incident_id)\
        .order_by(models.TimelineEvent.created_at.desc())\
        .all()
