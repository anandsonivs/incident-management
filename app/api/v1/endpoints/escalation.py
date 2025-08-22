from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db
from app.services.escalation import get_escalation_service

router = APIRouter()

# Escalation Policy Endpoints

@router.get("/policies/")
def get_escalation_policies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Retrieve escalation policies.
    """
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    policies = crud.escalation_policy.get_multi(db, skip=skip, limit=limit)
    return policies

@router.post("/policies/", status_code=status.HTTP_201_CREATED)
def create_escalation_policy(
    *,
    db: Session = Depends(get_db),
    policy_in: schemas.EscalationPolicyCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Create a new escalation policy.
    """
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if policy with this name already exists
    existing_policy = crud.escalation_policy.get_by_name(db, name=policy_in.name)
    if existing_policy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An escalation policy with this name already exists",
        )
    
    return crud.escalation_policy.create(db, obj_in=policy_in)

@router.get("/policies/{policy_id}")
def get_escalation_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get a specific escalation policy by ID.
    """
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    policy = crud.escalation_policy.get(db, id=policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation policy not found",
        )
    
    return policy

@router.put("/policies/{policy_id}")
def update_escalation_policy(
    *,
    db: Session = Depends(get_db),
    policy_id: int,
    policy_in: schemas.EscalationPolicyUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Update an escalation policy.
    """
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    policy = crud.escalation_policy.get(db, id=policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation policy not found",
        )
    
    # Check if another policy with the same name exists
    if policy_in.name and policy_in.name != policy.name:
        existing_policy = crud.escalation_policy.get_by_name(db, name=policy_in.name)
        if existing_policy and existing_policy.id != policy_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An escalation policy with this name already exists",
            )
    
    return crud.escalation_policy.update(db, db_obj=policy, obj_in=policy_in)

@router.delete("/policies/{policy_id}")
def delete_escalation_policy(
    *,
    db: Session = Depends(get_db),
    policy_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Delete an escalation policy.
    """
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    policy = crud.escalation_policy.get(db, id=policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation policy not found",
        )
    
    return crud.escalation_policy.remove(db, id=policy_id)

# Escalation Event Endpoints

@router.get("/incidents/{incident_id}/escalation-events/")
def get_incident_escalation_events(
    incident_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get escalation events for a specific incident.
    """
    # Check if incident exists
    incident = crud.incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    # Check if user has permission to view this incident
    if not crud.user.is_superuser(current_user) and not any(
        a.user_id == current_user.id for a in incident.assignments
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this incident's escalation events",
        )
    
    return crud.escalation_event.get_by_incident(
        db, incident_id=incident_id, skip=skip, limit=limit
    )

# Manual Escalation Endpoint

@router.post("/incidents/{incident_id}/escalate/")
async def escalate_incident(
    *,
    db: Session = Depends(get_db),
    incident_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Manually trigger escalation for an incident.
    """
    # Check if incident exists
    incident = crud.incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    # Check if user has permission to escalate this incident
    if not crud.user.is_superuser(current_user) and not any(
        a.user_id == current_user.id for a in incident.assignments
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to escalate this incident",
        )
    
    # Trigger escalation check
    escalation_service = get_escalation_service(db)
    await escalation_service.check_and_escalate_incident(incident)
    
    # Refresh and return the incident
    db.refresh(incident)
    return incident
