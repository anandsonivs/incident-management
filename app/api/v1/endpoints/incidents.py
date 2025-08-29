import json
import os
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db
from app.models.incident import IncidentStatus, TimelineEventType
from app.schemas.incident import (
    Incident, IncidentCreate, IncidentUpdate, IncidentWithRelations,
    Assignment, AssignmentCreate, AssignmentRequest, Comment, CommentCreate, TimelineEvent
)

router = APIRouter()

def load_team_mapping():
    """Load service to team mapping from config file."""
    try:
        # Try multiple possible paths
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "team_mapping.json"),
            os.path.join(os.getcwd(), "config", "team_mapping.json"),
            "config/team_mapping.json"
        ]
        
        for config_path in possible_paths:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        
        return {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_team_by_service(db: Session, service: str) -> Optional[models.team.Team]:
    """Get team by service name using the team mapping."""
    if not service:
        return None
    
    team_mapping = load_team_mapping()
    
    # Try exact match first
    if service in team_mapping:
        team_name = team_mapping[service]["team_name"]
        return db.query(models.team.Team).filter(models.team.Team.name == team_name).first()
    
    # Try with hyphen (common pattern)
    service_with_hyphen = service.replace(" ", "-")
    if service_with_hyphen in team_mapping:
        team_name = team_mapping[service_with_hyphen]["team_name"]
        return db.query(models.team.Team).filter(models.team.Team.name == team_name).first()
    
    # Try without hyphen
    service_without_hyphen = service.replace("-", " ")
    if service_without_hyphen in team_mapping:
        team_name = team_mapping[service_without_hyphen]["team_name"]
        return db.query(models.team.Team).filter(models.team.Team.name == team_name).first()
    
    return None

def incident_to_dict(incident):
    """Convert incident model to dictionary for API response."""
    result = {
        "id": incident.id,
        "title": incident.title,
        "description": incident.description,
        "status": incident.status,
        "severity": incident.severity,
        "service": incident.service,
        "team_id": incident.team_id,
        "alert_id": incident.alert_id,
        "metadata_": incident.metadata_,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
        "resolved_at": incident.resolved_at,
        "acknowledged_at": incident.acknowledged_at,
        "snoozed_until": incident.snoozed_until
    }
    
    # Add team information if available
    if incident.team:
        result["team"] = {
            "id": incident.team.id,
            "name": incident.team.name,
            "description": incident.team.description
        }
    
    return result

def incident_with_relations_to_dict(incident):
    """Convert incident model to dictionary with relations for API response."""
    result = incident_to_dict(incident)
    
    # Add assignments if available
    result["assignments"] = []
    if hasattr(incident, 'assignments') and incident.assignments:
        result["assignments"] = [
            {
                "id": assignment.id,
                "user_id": assignment.user_id,
                "assigned_at": assignment.assigned_at,
                "user": {
                    "id": assignment.user.id,
                    "email": assignment.user.email,
                    "full_name": assignment.user.full_name,
                    "role": assignment.user.role
                } if assignment.user else None
            }
            for assignment in incident.assignments
        ]
    
    # Add comments if available
    if hasattr(incident, 'comments') and incident.comments:
        result["comments"] = [
            {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at,
                "user": {
                    "id": comment.user.id,
                    "email": comment.user.email,
                    "full_name": comment.user.full_name
                } if comment.user else None
            }
            for comment in incident.comments
        ]
    else:
        result["comments"] = []
    
    # Add timeline events if available
    if hasattr(incident, 'timeline_events') and incident.timeline_events:
        result["timeline_events"] = [
            {
                "id": event.id,
                "event_type": event.event_type,
                "data": event.data,
                "created_at": event.created_at,
                "created_by": event.created_by
            }
            for event in incident.timeline_events
        ]
    else:
        result["timeline_events"] = []
    
    return result

@router.get("/")
def read_incidents(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[IncidentStatus] = None,
    service: Optional[str] = None,
    severity: Optional[str] = None,
    team_id: Optional[int] = None,
    include_assignments: bool = False,
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
    if team_id:
        query = query.filter(models.Incident.team_id == team_id)
    
    # Load relationships based on what's needed
    if include_assignments:
        query = query.options(
            joinedload(models.Incident.team),
            selectinload(models.Incident.assignments).selectinload("user")
        )
    else:
        query = query.options(joinedload(models.Incident.team))
    
    incidents = query.order_by(models.Incident.created_at.desc()).offset(skip).limit(limit).all()
    
    if include_assignments:
        # Load assignments separately for each incident
        for incident in incidents:
            assignments = db.query(models.IncidentAssignment).options(
                joinedload("user")
            ).filter(models.IncidentAssignment.incident_id == incident.id).all()
            setattr(incident, 'assignments', assignments)
        return [incident_with_relations_to_dict(incident) for incident in incidents]
    else:
        return [incident_to_dict(incident) for incident in incidents]

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
    # Auto-assign team based on service if not provided
    if not incident_in.team_id and incident_in.service:
        team = get_team_by_service(db, incident_in.service)
        if team:
            incident_in.team_id = team.id
    
    incident = crud.incident.create(db, obj_in=incident_in)
    
    # Add timeline event
    crud.incident.add_timeline_event(
        db,
        incident_id=incident.id,
        event_type=TimelineEventType.CREATED,
        data={"status": incident.status},
        user_id=current_user.id
    )
    
    # Auto-assign to oncall engineer in the same team
    if incident.team_id:
        try:
            from app.models.user import UserRole
            oncall_engineers = db.query(models.User).filter(
                models.User.role == UserRole.ONCALL_ENGINEER,
                models.User.team_id == incident.team_id,
                models.User.is_active == True
            ).all()
            
            if oncall_engineers:
                # Assign to the first available oncall engineer
                oncall_engineer = oncall_engineers[0]
                crud.incident.assign_user(db, incident_id=incident.id, user_id=oncall_engineer.id)
                
                # Add assignment timeline event
                crud.incident.add_timeline_event(
                    db,
                    incident_id=incident.id,
                    event_type=TimelineEventType.ASSIGNED,
                    data={"assigned_to": oncall_engineer.full_name, "assigned_by": "system"},
                    user_id=oncall_engineer.id
                )
                
                # Send notification to the assigned oncall engineer
                try:
                    from app.services.notification import NotificationService
                    notification_service = NotificationService(db)
                    # Create a simple notification message
                    message = f"🚨 You have been assigned to incident #{incident.id}: {incident.title} (Severity: {incident.severity})"
                    # For now, we'll call it synchronously to avoid async issues
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(notification_service.send_notification(
                            recipient=oncall_engineer.email,
                            message=message,
                            incident_id=incident.id,
                            action_type="assignment",
                            metadata={"assigned_user_id": oncall_engineer.id, "assigned_by": "system"}
                        ))
                    finally:
                        loop.close()
                except Exception as e:
                    print(f"Warning: Failed to send assignment notification: {e}")
                
                print(f"Auto-assigned incident {incident.id} to oncall engineer {oncall_engineer.full_name}")
            else:
                print(f"No oncall engineers found for team {incident.team_id}")
        except Exception as e:
            print(f"Warning: Failed to auto-assign to oncall engineer: {e}")
    
    # Trigger escalation service for escalation policies (as fallback)
    # Note: Escalation will be handled by background tasks or scheduled jobs
    # For now, we'll skip the async escalation to avoid blocking the response
    print(f"Incident {incident.id} created and assigned. Escalation will be handled by background processes.")
    
    # Load team relationship for response
    db.refresh(incident)
    incident = db.query(models.Incident).options(joinedload(models.Incident.team)).filter(models.Incident.id == incident.id).first()
    
    return incident_to_dict(incident)

@router.get("/{incident_id}", response_model=IncidentWithRelations)
def read_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get incident by ID.
    """
    incident = db.query(models.Incident).options(
        joinedload(models.Incident.team),
        joinedload(models.Incident.assignments).joinedload(models.IncidentAssignment.user),
        joinedload(models.Incident.comments).joinedload(models.IncidentComment.user)
    ).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return incident_with_relations_to_dict(incident)

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
    
    return incident_to_dict(updated)

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
        return incident_to_dict(incident)
    
    # Check if user is already assigned to this incident
    existing_assignment = db.query(models.IncidentAssignment).filter(
        models.IncidentAssignment.incident_id == incident_id,
        models.IncidentAssignment.user_id == current_user.id
    ).first()
    
    # If not assigned, automatically assign the incident to the current user
    if not existing_assignment:
        assignment = models.IncidentAssignment(
            incident_id=incident_id,
            user_id=current_user.id,
            assigned_at=datetime.utcnow()
        )
        db.add(assignment)
        db.commit()
        
        # Add assignment timeline event
        crud.incident.add_timeline_event(
            db,
            incident_id=incident_id,
            event_type=TimelineEventType.ASSIGNED,
            data={"assigned_to_user_id": current_user.id},
            user_id=current_user.id
        )
    
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
    
    return incident_to_dict(incident)

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
        return incident_to_dict(incident)
    
    # Check if user is already assigned to this incident
    existing_assignment = db.query(models.IncidentAssignment).filter(
        models.IncidentAssignment.incident_id == incident_id,
        models.IncidentAssignment.user_id == current_user.id
    ).first()
    
    # If not assigned, automatically assign the incident to the current user
    if not existing_assignment:
        assignment = models.IncidentAssignment(
            incident_id=incident_id,
            user_id=current_user.id,
            assigned_at=datetime.utcnow()
        )
        db.add(assignment)
        db.commit()
        
        # Add assignment timeline event
        crud.incident.add_timeline_event(
            db,
            incident_id=incident_id,
            event_type=TimelineEventType.ASSIGNED,
            data={"assigned_to_user_id": current_user.id},
            user_id=current_user.id
        )
    
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
    
    return incident_to_dict(incident)

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
    
    return incident_to_dict(incident)

@router.post("/{incident_id}/assign")
def assign_incident(
    *,
    db: Session = Depends(get_db),
    incident_id: int,
    assignment_in: AssignmentRequest,
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
