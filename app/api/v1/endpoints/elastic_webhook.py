import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime

from app import crud, models, schemas
from app.db.session import get_db
from app.models.incident import IncidentStatus, TimelineEventType
from app.schemas.incident import IncidentCreate
from app.core.config import get_settings

router = APIRouter()

def extract_incident_data(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and transform Elastic APM alert data into our incident format.
    """
    # Default values
    incident_data = {
        "title": "New Alert",
        "description": "No description provided",
        "severity": "medium",
        "service": "unknown",
        "metadata": {}
    }
    
    try:
        # Extract basic alert information
        if "alert_name" in alert_data:
            incident_data["title"] = alert_data["alert_name"]
        
        if "message" in alert_data:
            incident_data["description"] = alert_data["message"]
        
        # Extract service information
        if "service" in alert_data and "name" in alert_data["service"]:
            incident_data["service"] = alert_data["service"]["name"]
        
        # Extract severity if available
        if "severity" in alert_data:
            severity = alert_data["severity"].lower()
            if severity in ["critical", "high", "medium", "low"]:
                incident_data["severity"] = severity
        
        # Include the full alert in metadata for reference
        incident_data["metadata"]["raw_alert"] = alert_data
        
        # Try to extract a unique alert ID
        if "alert_id" in alert_data:
            incident_data["alert_id"] = alert_data["alert_id"]
        elif "id" in alert_data:
            incident_data["alert_id"] = alert_data["id"]
        
        return incident_data
    except Exception as e:
        # If parsing fails, return the default with error info
        incident_data["metadata"]["parse_error"] = str(e)
        incident_data["metadata"]["raw_alert"] = alert_data
        return incident_data

@router.post("", status_code=status.HTTP_201_CREATED)
async def handle_elastic_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    settings = get_settings()
    """
    Handle incoming webhooks from Elastic APM.
    This endpoint processes alerts and creates/updates incidents accordingly.
    """
    try:
        # Parse the incoming alert data
        alert_data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Extract and transform the alert data
    incident_data = extract_incident_data(alert_data)
    
    # Check if this is a recovery/resolved alert
    is_recovery = alert_data.get("state", {}).get("state", "").lower() in ["resolved", "recovered"]
    
    # Check if we already have an incident for this alert
    alert_id = incident_data.get("alert_id")
    existing_incident = None
    
    if alert_id:
        existing_incident = crud.incident.get_by_alert_id(db, alert_id=alert_id)
    
    if is_recovery:
        # Handle recovery/resolved alerts
        if existing_incident and existing_incident.status != IncidentStatus.RESOLVED:
            # Update the existing incident as resolved
            incident = await crud.incident.update_status(
                db, db_obj=existing_incident, status=IncidentStatus.RESOLVED
            )
            
            # Add timeline event
            crud.incident.add_timeline_event(
                db,
                incident_id=incident.id,
                event_type=TimelineEventType.RESOLVED,
                data={"source": "elastic_apm", "alert_id": alert_id},
                user_id=None  # System action
            )
            
            return {"status": "incident_resolved", "incident_id": incident.id}
        
        return {"status": "no_matching_active_incident"}
    
    # This is a new alert or an update to an existing one
    if existing_incident:
        # Update existing incident
        update_data = {}
        if "title" in incident_data:
            update_data["title"] = incident_data["title"]
        if "description" in incident_data:
            update_data["description"] = incident_data["description"]
        if "severity" in incident_data:
            update_data["severity"] = incident_data["severity"]
        
        # Only update metadata if we have new data
        if "metadata" in incident_data and incident_data["metadata"]:
            current_metadata = existing_incident.metadata_ or {}
            current_metadata.update(incident_data["metadata"])
            update_data["metadata_"] = current_metadata
        
        if update_data:
            incident = crud.incident.update(
                db, db_obj=existing_incident, obj_in=update_data
            )
            
            # Add timeline event for the update
            crud.incident.add_timeline_event(
                db,
                incident_id=incident.id,
                event_type=TimelineEventType.UPDATED,
                data={"source": "elastic_apm", "alert_id": alert_id, "updates": update_data},
                user_id=None  # System action
            )
            
            return {"status": "incident_updated", "incident_id": incident.id}
        
        return {"status": "no_changes", "incident_id": existing_incident.id}
    
    # Create a new incident
    incident_in = IncidentCreate(
        title=incident_data["title"],
        description=incident_data["description"],
        severity=incident_data["severity"],
        service=incident_data["service"],
        metadata=incident_data.get("metadata", {}),
        alert_id=alert_id
    )
    
    incident = crud.incident.create(db, obj_in=incident_in)
    
    # Add timeline event for creation
    crud.incident.add_timeline_event(
        db,
        incident_id=incident.id,
        event_type=TimelineEventType.CREATED,
        data={"source": "elastic_apm", "alert_id": alert_id},
        user_id=None  # System action
    )
    
    return {"status": "incident_created", "incident_id": incident.id}
