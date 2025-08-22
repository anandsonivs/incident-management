from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, cast
import logging

from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import models, schemas, crud
from app.services.notification import NotificationService
from app.crud.base import CRUDBase

logger = logging.getLogger(__name__)

class EscalationService:
    """Service for handling incident escalations."""
    
    def __init__(self, db: Session, crud: CRUDBase, notification_service: Optional[NotificationService] = None):
        self.db = db
        self.crud = crud
        self.notification_service = notification_service or NotificationService(db)
    
    async def check_and_escalate_incident(self, incident: models.Incident) -> None:
        """Check if an incident needs escalation and process it."""
        if incident.status in [schemas.IncidentStatus.RESOLVED, schemas.IncidentStatus.SNOOZED]:
            return

        # Get active escalation policies that match this incident
        policies = self._get_matching_policies(incident)
        
        for policy in policies:
            await self.process_escalation_policy(incident, policy)
    
    def _policy_matches_incident(self, policy: models.EscalationPolicy, incident: models.Incident) -> bool:
        conditions = policy.conditions or {}
        severity_ok = True
        service_ok = True
        if "severity" in conditions:
            severities = set(map(lambda x: str(x).lower(), conditions.get("severity", [])))
            inc_sev = incident.severity
            inc_sev_str = inc_sev.name.lower() if hasattr(inc_sev, 'name') else str(inc_sev).lower()
            severity_ok = inc_sev_str in severities
        if "service" in conditions:
            services = set(map(str, conditions.get("service", [])))
            service_ok = (incident.service in services)
        return severity_ok and service_ok

    def _get_matching_policies(self, incident: models.Incident) -> List[models.EscalationPolicy]:
        """Get escalation policies that match the incident's conditions."""
        # Use injected policy CRUD for easier testing
        try:
            active = self.crud.get_active_policies(self.db)  # type: ignore[attr-defined]
        except AttributeError:
            # Fallback to global CRUD if a different CRUD is passed
            active = crud.escalation_policy.get_active_policies(self.db)
        return [p for p in active if self._policy_matches_incident(p, incident)]
    
    async def process_escalation_policy(
        self, incident: models.Incident, policy: models.EscalationPolicy
    ) -> None:
        """Process an escalation policy for an incident."""
        processed_steps: set[int] = set()
        while True:
            step_index, current_step = self._get_current_escalation_step(incident, policy, processed_steps)
            if current_step is None or step_index is None:
                break
            
            # Create an event in pending state
            event = crud.escalation_event.create(
                self.db,
                obj_in=schemas.EscalationEventCreate(
                    incident_id=incident.id,
                    policy_id=policy.id,
                    step=step_index,
                    status=schemas.EscalationEventStatus.PENDING,
                    metadata={"policy_name": policy.name, "step": current_step},
                ),
            )
            
            # Process all actions in the current step
            try:
                for action in current_step.get("actions", []):
                    await self._process_action(incident, action, current_step)
                crud.escalation_event.mark_as_completed(self.db, db_obj=event)
            except Exception as e:
                logger.error("Escalation step processing failed", exc_info=True)
                crud.escalation_event.mark_as_failed(self.db, db_obj=event, error=str(e))
            
            processed_steps.add(step_index)
    
    def _get_current_escalation_step(
        self, incident: models.Incident, policy: models.EscalationPolicy, processed_steps: set[int]
    ) -> (Optional[int], Optional[Dict[str, Any]]):
        """Determine the current escalation step index and data based on incident age and policy."""
        incident_age = datetime.utcnow() - incident.created_at
        
        for index, step in enumerate(policy.steps):
            if index in processed_steps:
                continue
            step_delay = timedelta(minutes=step.get("delay_minutes", 0))
            if incident_age >= step_delay:
                return index, step
        
        return None, None
    
    async def _process_action(
        self, incident: models.Incident, action: Dict[str, Any], step: Dict[str, Any]
    ) -> None:
        """Process a single escalation action."""
        action_type = action.get("type")
        
        if action_type == "notify":
            await self._process_notification_action(incident, action, step)
        elif action_type == "assign":
            await self._process_assign_action(incident, action, step)
        elif action_type in ("status_change", "change_status"):
            await self._process_status_change_action(incident, action, step)
    
    async def _process_notification_action(
        self, incident: models.Incident, action: Dict[str, Any], step: Dict[str, Any]
    ) -> None:
        """Process a notification action."""
        message = action.get("message", f"Incident {incident.id} requires attention")
        recipients = action.get("recipients")
        if recipients is None and "target" in action:
            recipients = [action.get("target")]
        recipients = recipients or ["assignees"]
        
        for recipient in recipients:
            await self.notification_service.send_notification(
                recipient=recipient,
                message=message,
                incident_id=incident.id,
                action_type="escalation",
                metadata={"step": step},
            )
    
    async def _process_assign_action(
        self, incident: models.Incident, action: Dict[str, Any], step: Dict[str, Any]
    ) -> None:
        """Process an assign action."""
        assignee_id = action.get("assignee_id")
        if not assignee_id:
            return
        
        # Ensure assignment exists
        existing = crud.incident.get_assignment_by_incident_and_user(
            self.db, incident_id=incident.id, user_id=assignee_id
        )
        if not existing:
            await crud.incident.assign_user(
                self.db, incident_id=incident.id, user_id=assignee_id
            )
    
    async def _process_status_change_action(
        self, incident: models.Incident, action: Dict[str, Any], step: Dict[str, Any]
    ) -> None:
        """Process a status change action."""
        status = action.get("status")
        if not status:
            return

        try:
            status_enum = schemas.IncidentStatus[status.upper()]
            await crud.incident.update_status(
                db=self.db,
                db_obj=incident,
                status=status_enum,
            )
        except (KeyError, ValueError):
            logger.error(f"Invalid status value for status change: {status}")
