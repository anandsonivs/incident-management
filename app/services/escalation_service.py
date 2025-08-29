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
        print(f"Checking escalation for incident {incident.id} (status: {incident.status})")
        
        if incident.status in [schemas.IncidentStatus.RESOLVED, schemas.IncidentStatus.SNOOZED]:
            print(f"Incident {incident.id} is resolved or snoozed, skipping escalation")
            return

        # Get active escalation policies that match this incident
        policies = self._get_matching_policies(incident)
        print(f"Found {len(policies)} matching policies for incident {incident.id}")
        
        for policy in policies:
            print(f"Processing escalation policy {policy.id} ({policy.name}) for incident {incident.id}")
            await self.process_escalation_policy(incident, policy)
    
    def _policy_matches_incident(self, policy: models.EscalationPolicy, incident: models.Incident) -> bool:
        conditions = policy.conditions or {}
        severity_ok = True
        service_ok = True
        team_ok = True
        
        print(f"Checking policy {policy.id} against incident {incident.id}")
        print(f"Policy conditions: {conditions}")
        print(f"Incident severity: {incident.severity}, service: {incident.service}, team_id: {incident.team_id}")
        
        if "severity" in conditions:
            severity_condition = conditions.get("severity", [])
            # Handle both single string and list of strings
            if isinstance(severity_condition, str):
                severities = {severity_condition.lower()}
            else:
                severities = set(map(lambda x: str(x).lower(), severity_condition))
            
            inc_sev = incident.severity
            inc_sev_str = inc_sev.name.lower() if hasattr(inc_sev, 'name') else str(inc_sev).lower()
            severity_ok = inc_sev_str in severities
            print(f"Severity check: {inc_sev_str} in {severities} = {severity_ok}")
            
        if "service" in conditions:
            service_condition = conditions.get("service", [])
            # Handle both single string and list of strings
            if isinstance(service_condition, str):
                services = {service_condition}
            else:
                services = set(map(str, service_condition))
            service_ok = (incident.service in services)
            print(f"Service check: {incident.service} in {services} = {service_ok}")
            
        if "team_id" in conditions:
            team_id_value = conditions.get("team_id")
            if isinstance(team_id_value, list):
                team_ids = set(map(int, team_id_value))
                team_ok = (incident.team_id in team_ids)
            else:
                # Handle single team_id as integer
                team_ok = (incident.team_id == int(team_id_value))
            print(f"Team check: {incident.team_id} == {team_id_value} = {team_ok}")
            
        result = severity_ok and service_ok and team_ok
        print(f"Policy {policy.id} matches incident {incident.id}: {result}")
        return result

    def _get_matching_policies(self, incident: models.Incident) -> List[models.EscalationPolicy]:
        """Get escalation policies that match the incident's conditions."""
        # Use injected policy CRUD for easier testing
        try:
            active = self.crud.get_active_policies(self.db)  # type: ignore[attr-defined]
        except AttributeError:
            # Fallback to global CRUD if a different CRUD is passed
            active = crud.escalation_policy.get_active_policies(self.db)
        
        print(f"Found {len(active)} active escalation policies")
        
        matching_policies = [p for p in active if self._policy_matches_incident(p, incident)]
        print(f"Found {len(matching_policies)} matching policies for incident {incident.id}")
        
        for policy in matching_policies:
            print(f"Matching policy: {policy.id} - {policy.name} (conditions: {policy.conditions})")
        
        return matching_policies
    
    def _get_users_by_role_and_team(self, role: str, team_id: int) -> List[models.User]:
        """Get users by role and team."""
        from app.models.user import UserRole
        
        # Map escalation targets to user roles
        role_mapping = {
            "team_lead": UserRole.TEAM_LEAD,
            "manager": UserRole.MANAGER,
            "vp": UserRole.VP,
            "cto": UserRole.CTO,
            "oncall_engineer": UserRole.ONCALL_ENGINEER,
        }
        
        user_role = role_mapping.get(role)
        if not user_role:
            return []
        
        return crud.user.get_by_role_and_team(self.db, role=user_role, team_id=team_id)
    
    def _get_escalation_targets(self, incident: models.Incident, target: str) -> List[models.User]:
        """Get escalation targets based on role and team."""
        if not incident.team_id:
            logger.warning(f"Incident {incident.id} has no team assigned")
            return []
        
        # Handle special targets
        if target == "assignees":
            return [assignment.user for assignment in incident.assignments]
        elif target == "team_lead":
            return self._get_users_by_role_and_team("team_lead", incident.team_id)
        elif target == "manager":
            return self._get_users_by_role_and_team("manager", incident.team_id)
        elif target == "vp":
            return self._get_users_by_role_and_team("vp", incident.team_id)
        elif target == "cto":
            return self._get_users_by_role_and_team("cto", incident.team_id)
        elif target == "oncall_engineer":
            return self._get_users_by_role_and_team("oncall_engineer", incident.team_id)
        else:
            # Try to find user by email or ID
            try:
                user_id = int(target)
                user = crud.user.get(self.db, id=user_id)
                return [user] if user else []
            except ValueError:
                # Assume it's an email
                user = crud.user.get_by_email(self.db, email=target)
                return [user] if user else []
    
    async def process_escalation_policy(
        self, incident: models.Incident, policy: models.EscalationPolicy
    ) -> None:
        """Process an escalation policy for an incident."""
        print(f"Processing escalation policy {policy.id} for incident {incident.id}")
        processed_steps: set[int] = set()
        while True:
            step_index, current_step = self._get_current_escalation_step(incident, policy, processed_steps)
            if current_step is None or step_index is None:
                print(f"No more steps to process for policy {policy.id}")
                break
            
            print(f"Processing step {step_index} for policy {policy.id}")
            
            # Create an event in pending state
            try:
                from app.schemas.escalation import EscalationEventCreate, EscalationEventStatus
                # Calculate incident age
                from datetime import timezone
                incident_age = datetime.now(timezone.utc) - incident.created_at
                
                # Prepare detailed metadata
                metadata = {
                    "policy_name": policy.name,
                    "policy_description": policy.description,
                    "step": current_step,
                    "severity": incident.severity,
                    "service": incident.service,
                    "incident_age_minutes": int(incident_age.total_seconds() / 60),
                    "delay_minutes": current_step.get("delay_minutes", 0),
                    "triggered_by": "system",  # or could be "manual" for manual escalations
                    "triggered_for": [],  # Will be populated when processing actions
                    "target_users": []  # Will be populated when processing actions
                }
                
                event_create_data = EscalationEventCreate(
                    incident_id=incident.id,
                    policy_id=policy.id,
                    step=step_index,
                    status=EscalationEventStatus.PENDING,
                    metadata=metadata,
                )
                event = crud.escalation_event.create(
                    self.db,
                    obj_in=event_create_data,
                )
            except Exception as e:
                print(f"Error creating escalation event: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Process all actions in the current step
            try:
                triggered_for = []
                target_users = []
                
                for action in current_step.get("actions", []):
                    action_result = await self._process_action(incident, action, current_step, event)
                    if action_result:
                        triggered_for.extend(action_result.get("triggered_for", []))
                        target_users.extend(action_result.get("target_users", []))
                
                # Update event metadata with target information
                # Use the model field 'event_metadata'
                current_metadata = event.event_metadata or {}
                updated_metadata = {
                    **current_metadata,
                    "triggered_for": triggered_for,
                    "target_users": target_users
                }
                event.event_metadata = updated_metadata
                self.db.commit()
                
                crud.escalation_event.mark_as_completed(self.db, db_obj=event)
                print(f"Completed escalation event {event.id}")
            except Exception as e:
                print(f"Escalation step processing failed: {e}")
                import traceback
                traceback.print_exc()
                crud.escalation_event.mark_as_failed(self.db, db_obj=event, error=str(e))
            
            processed_steps.add(step_index)
    
    def _get_current_escalation_step(
        self, incident: models.Incident, policy: models.EscalationPolicy, processed_steps: set[int]
    ) -> (Optional[int], Optional[Dict[str, Any]]):
        """Determine the current escalation step index and data based on incident age and policy."""
        from datetime import timezone
        incident_age = datetime.now(timezone.utc) - incident.created_at
        
        for index, step in enumerate(policy.steps):
            if index in processed_steps:
                continue
            step_delay = timedelta(minutes=step.get("delay_minutes", 0))
            if incident_age >= step_delay:
                return index, step
        
        return None, None
    
    async def _process_action(
        self, incident: models.Incident, action: Dict[str, Any], step: Dict[str, Any], event: models.EscalationEvent
    ) -> Dict[str, Any]:
        """Process a single escalation action."""
        action_type = action.get("type")
        
        if action_type == "notify":
            return await self._process_notification_action(incident, action, step)
        elif action_type.startswith("notify_"):
            # Handle role-based notifications like notify_team_lead, notify_manager
            return await self._process_role_notification_action(incident, action, step)
        elif action_type == "assign":
            return await self._process_assign_action(incident, action, step)
        elif action_type in ("status_change", "change_status"):
            return await self._process_status_change_action(incident, action, step)
        
        return {"triggered_for": [], "target_users": []}
    
    async def _process_notification_action(
        self, incident: models.Incident, action: Dict[str, Any], step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a notification action."""
        message = action.get("message", f"Incident {incident.id} requires attention")
        recipients = action.get("recipients")
        if recipients is None and "target" in action:
            recipients = [action.get("target")]
        recipients = recipients or ["assignees"]
        
        triggered_for = []
        target_users = []
        
        for recipient in recipients:
            # Get actual users for this target
            users = self._get_escalation_targets(incident, recipient)
            triggered_for.append(recipient)
            
            for user in users:
                target_users.append({
                    "id": user.id,
                    "name": user.full_name,
                    "email": user.email,
                    "role": "responder"
                })
                
                await self.notification_service.send_notification(
                    recipient=user.email,
                    message=message,
                    incident_id=incident.id,
                    action_type="escalation",
                    metadata={"step": step, "user_id": user.id},
                )
        
        return {"triggered_for": triggered_for, "target_users": target_users}
    
    async def _process_role_notification_action(
        self, incident: models.Incident, action: Dict[str, Any], step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a role-based notification action."""
        action_type = action.get("type")
        target_roles = action.get("target_roles", [])
        
        # Extract role from action type (e.g., "notify_team_lead" -> "team_lead")
        if action_type and action_type.startswith("notify_"):
            role = action_type.replace("notify_", "")
            target_roles = [role]
        
        message = f"Escalation: Incident {incident.id} ({incident.title}) requires {role} attention"
        
        triggered_for = []
        target_users = []
        
        for role in target_roles:
            # Get users for this role and team
            users = self._get_users_by_role_and_team(role, incident.team_id)
            triggered_for.append(role)
            
            for user in users:
                target_users.append({
                    "id": user.id,
                    "name": user.full_name,
                    "email": user.email,
                    "role": role
                })
                
                await self.notification_service.send_notification(
                    recipient=user.email,
                    message=message,
                    incident_id=incident.id,
                    action_type="escalation",
                    metadata={"step": step, "user_id": user.id, "role": role},
                )
        
        return {"triggered_for": triggered_for, "target_users": target_users}
    
    async def _process_assign_action(
        self, incident: models.Incident, action: Dict[str, Any], step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an assign action."""
        target = action.get("target")
        if not target:
            return {"triggered_for": [], "target_users": []}
        
        # Get users for this target
        users = self._get_escalation_targets(incident, target)
        triggered_for = [target]
        target_users = []
        
        for user in users:
            target_users.append({
                "id": user.id,
                "name": user.full_name,
                "email": user.email,
                "role": "assignee"
            })
            
            # Ensure assignment exists
            existing = crud.incident.get_assignment_by_incident_and_user(
                self.db, incident_id=incident.id, user_id=user.id
            )
            if not existing:
                await crud.incident.assign_user(
                    self.db, incident_id=incident.id, user_id=user.id
                )
            else:
                print(f"User {user.id} already assigned to incident {incident.id}")
        
        return {"triggered_for": triggered_for, "target_users": target_users}
    
    async def _process_status_change_action(
        self, incident: models.Incident, action: Dict[str, Any], step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a status change action."""
        status = action.get("status")
        if not status:
            return {"triggered_for": [], "target_users": []}

        try:
            status_enum = schemas.IncidentStatus[status.upper()]
            await crud.incident.update_status(
                db=self.db,
                db_obj=incident,
                status=status_enum,
            )
        except (KeyError, ValueError):
            logger.error(f"Invalid status value for status change: {status}")
        
        return {"triggered_for": [f"status_change_to_{status}"], "target_users": []}
