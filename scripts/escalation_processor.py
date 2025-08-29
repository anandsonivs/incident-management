#!/usr/bin/env python3
"""
Background Escalation Processor

This script processes escalation policies for incidents that need escalation.
It should be run periodically (e.g., every 5 minutes) to check for incidents
that need escalation based on their age and escalation policies.

Usage:
    python scripts/escalation_processor.py
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import List, Set, Dict

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.incident import Incident, IncidentStatus
from app.models.escalation import EscalationPolicy, EscalationEvent
from app.services.escalation import EscalationService
from app.crud import escalation_policy # Corrected import
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EscalationProcessor:
    """Background processor for handling incident escalations."""

    def __init__(self):
        self.db = SessionLocal()
        self.escalation_service = EscalationService(
            db=self.db,
            crud=escalation_policy # Corrected reference
        )

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

    def get_escalatable_incidents(self) -> List[Incident]:
        """Get incidents that need escalation processing."""
        # Get incidents that are not resolved or snoozed
        incidents = self.db.query(Incident).filter(
            Incident.status.in_([IncidentStatus.TRIGGERED, IncidentStatus.ACKNOWLEDGED])
        ).all()
        
        logger.info(f"Found {len(incidents)} active incidents to check for escalation")
        return incidents
    
    def get_processed_escalation_steps(self, incident_id: int, policy_id: int) -> set:
        """Get the escalation steps that have already been processed for an incident."""
        events = self.db.query(EscalationEvent).filter(
            EscalationEvent.incident_id == incident_id,
            EscalationEvent.policy_id == policy_id
        ).all()
        
        return {event.step for event in events}
    
    def get_notified_users_for_step(self, incident_id: int, policy_id: int, step: int) -> Set[int]:
        """Get the user IDs that have already been notified for a specific step."""
        events = self.db.query(EscalationEvent).filter(
            EscalationEvent.incident_id == incident_id,
            EscalationEvent.policy_id == policy_id,
            EscalationEvent.step == step
        ).all()
        
        notified_users = set()
        for event in events:
            if event.event_metadata and "target_users" in event.event_metadata:
                for user_info in event.event_metadata["target_users"]:
                    if isinstance(user_info, dict) and "id" in user_info:
                        notified_users.add(user_info["id"])
        
        return notified_users
    
    def should_notify_user(self, user_id: int, incident_id: int, policy_id: int, step: int) -> bool:
        """Check if a user should be notified for this step (prevents duplicate notifications)."""
        notified_users = self.get_notified_users_for_step(incident_id, policy_id, step)
        return user_id not in notified_users

    async def process_incident_escalations(self, incident: Incident):
        """Process escalations for a single incident."""
        logger.info(f"Processing escalations for incident {incident.id}")
        
        # Get matching escalation policies
        policies = self.escalation_service._get_matching_policies(incident)
        
        if not policies:
            logger.info(f"No matching escalation policies for incident {incident.id}")
            return
        
        logger.info(f"Found {len(policies)} matching policies for incident {incident.id}")
        
        for policy in policies:
            await self.process_policy_escalations(incident, policy)
    
    async def process_policy_escalations(self, incident: Incident, policy: EscalationPolicy):
        """Process escalations for a specific policy and incident."""
        logger.info(f"Processing policy {policy.id} for incident {incident.id}")
        
        # Get already processed steps
        processed_steps = self.get_processed_escalation_steps(incident.id, policy.id)
        
        # Check each step in the policy
        for step_index, step in enumerate(policy.steps):
            if step_index in processed_steps:
                logger.info(f"Step {step_index} already processed for incident {incident.id}, policy {policy.id}")
                continue
            
            # Check if it's time for this step
            step_delay = timedelta(minutes=step.get("delay_minutes", 0))
            incident_age = datetime.now(timezone.utc) - incident.created_at
            
            if incident_age >= step_delay:
                logger.info(f"Triggering step {step_index} for incident {incident.id}, policy {policy.id}")
                
                # Process the step with user-level tracking
                await self.process_escalation_step(incident, policy, step_index, step)
                break
            else:
                logger.info(f"Step {step_index} not ready yet for incident {incident.id} (age: {incident_age}, required: {step_delay})")
    
    async def process_escalation_step(self, incident: Incident, policy: EscalationPolicy, step_index: int, step: Dict):
        """Process a single escalation step with user-level tracking to prevent duplicate notifications."""
        logger.info(f"Processing escalation step {step_index} for incident {incident.id}, policy {policy.id}")
        
        # Get users that have already been notified for this step
        notified_users = self.get_notified_users_for_step(incident.id, policy.id, step_index)
        logger.info(f"Users already notified for step {step_index}: {notified_users}")
        
        # Create escalation event
        try:
            from app.schemas.escalation import EscalationEventCreate, EscalationEventStatus
            from datetime import timezone
            incident_age = datetime.now(timezone.utc) - incident.created_at
            
            metadata = {
                "policy_name": policy.name,
                "policy_description": policy.description,
                "step": step,
                "severity": incident.severity,
                "service": incident.service,
                "incident_age_minutes": int(incident_age.total_seconds() / 60),
                "delay_minutes": step.get("delay_minutes", 0),
                "triggered_by": "system",
                "triggered_for": [],
                "target_users": [],
                "already_notified_users": list(notified_users)
            }
            
            event_create_data = EscalationEventCreate(
                incident_id=incident.id,
                policy_id=policy.id,
                step=step_index,
                status=EscalationEventStatus.PENDING,
                metadata=metadata,
            )
            
            from app.crud import escalation_event
            event = escalation_event.create(self.db, obj_in=event_create_data)
            
        except Exception as e:
            logger.error(f"Error creating escalation event: {e}")
            return
        
        # Process actions with user-level tracking
        try:
            triggered_for = []
            target_users = []
            new_notifications = 0
            
            for action in step.get("actions", []):
                action_result = await self._process_action_with_tracking(
                    incident, action, step, step_index, policy.id, notified_users
                )
                if action_result:
                    triggered_for.extend(action_result.get("triggered_for", []))
                    target_users.extend(action_result.get("target_users", []))
                    new_notifications += action_result.get("new_notifications", 0)
            
            # Update event metadata
            current_metadata = event.event_metadata or {}
            updated_metadata = {
                **current_metadata,
                "triggered_for": triggered_for,
                "target_users": target_users,
                "new_notifications": new_notifications
            }
            event.event_metadata = updated_metadata
            self.db.commit()
            
            escalation_event.mark_as_completed(self.db, db_obj=event)
            logger.info(f"Completed escalation event {event.id} with {new_notifications} new notifications")
            
        except Exception as e:
            logger.error(f"Escalation step processing failed: {e}")
            escalation_event.mark_as_failed(self.db, db_obj=event, error=str(e))
    
    async def _process_action_with_tracking(
        self, incident: Incident, action: Dict, step: Dict, step_index: int, 
        policy_id: int, already_notified_users: Set[int]
    ) -> Dict:
        """Process an escalation action with user-level tracking to prevent duplicate notifications."""
        action_type = action.get("type")
        new_notifications = 0
        
        if action_type == "notify":
            return await self._process_notification_action_with_tracking(
                incident, action, step, step_index, policy_id, already_notified_users
            )
        elif action_type.startswith("notify_"):
            return await self._process_role_notification_action_with_tracking(
                incident, action, step, step_index, policy_id, already_notified_users
            )
        elif action_type == "assign":
            return await self._process_assign_action_with_tracking(
                incident, action, step, step_index, policy_id, already_notified_users
            )
        
        return {"triggered_for": [], "target_users": [], "new_notifications": 0}
    
    async def _process_notification_action_with_tracking(
        self, incident: Incident, action: Dict, step: Dict, step_index: int, 
        policy_id: int, already_notified_users: Set[int]
    ) -> Dict:
        """Process a notification action with user-level tracking."""
        message = action.get("message", f"Incident {incident.id} requires attention")
        recipients = action.get("recipients")
        if recipients is None and "target" in action:
            recipients = [action.get("target")]
        recipients = recipients or ["assignees"]
        
        triggered_for = []
        target_users = []
        new_notifications = 0
        
        for recipient in recipients:
            users = self.escalation_service._get_escalation_targets(incident, recipient)
            triggered_for.append(recipient)
            
            for user in users:
                target_users.append({
                    "id": user.id,
                    "name": user.full_name,
                    "email": user.email,
                    "role": "responder"
                })
                
                # Only notify if user hasn't been notified for this step
                if self.should_notify_user(user.id, incident.id, policy_id, step_index):
                    await self.escalation_service.notification_service.send_notification(
                        recipient=user.email,
                        message=message,
                        incident_id=incident.id,
                        action_type="escalation",
                        metadata={"step": step, "user_id": user.id, "step_index": step_index},
                    )
                    new_notifications += 1
                    logger.info(f"Sent notification to user {user.id} ({user.email}) for step {step_index}")
                else:
                    logger.info(f"Skipping notification to user {user.id} ({user.email}) - already notified for step {step_index}")
        
        return {"triggered_for": triggered_for, "target_users": target_users, "new_notifications": new_notifications}
    
    async def _process_role_notification_action_with_tracking(
        self, incident: Incident, action: Dict, step: Dict, step_index: int, 
        policy_id: int, already_notified_users: Set[int]
    ) -> Dict:
        """Process a role-based notification action with user-level tracking."""
        action_type = action.get("type")
        target_roles = action.get("target_roles", [])
        
        if action_type and action_type.startswith("notify_"):
            role = action_type.replace("notify_", "")
            target_roles = [role]
        
        message = f"Escalation: Incident {incident.id} ({incident.title}) requires {role} attention"
        
        triggered_for = []
        target_users = []
        new_notifications = 0
        
        for role in target_roles:
            users = self.escalation_service._get_users_by_role_and_team(role, incident.team_id)
            triggered_for.append(role)
            
            for user in users:
                target_users.append({
                    "id": user.id,
                    "name": user.full_name,
                    "email": user.email,
                    "role": role
                })
                
                # Only notify if user hasn't been notified for this step
                if self.should_notify_user(user.id, incident.id, policy_id, step_index):
                    await self.escalation_service.notification_service.send_notification(
                        recipient=user.email,
                        message=message,
                        incident_id=incident.id,
                        action_type="escalation",
                        metadata={"step": step, "user_id": user.id, "role": role, "step_index": step_index},
                    )
                    new_notifications += 1
                    logger.info(f"Sent role notification to user {user.id} ({user.email}) for step {step_index}")
                else:
                    logger.info(f"Skipping role notification to user {user.id} ({user.email}) - already notified for step {step_index}")
        
        return {"triggered_for": triggered_for, "target_users": target_users, "new_notifications": new_notifications}
    
    async def _process_assign_action_with_tracking(
        self, incident: Incident, action: Dict, step: Dict, step_index: int, 
        policy_id: int, already_notified_users: Set[int]
    ) -> Dict:
        """Process an assign action with user-level tracking."""
        # For assignment actions, we might want to track differently
        # For now, just return empty result
        return {"triggered_for": [], "target_users": [], "new_notifications": 0}

    async def run(self):
        """Main processing loop."""
        logger.info("Starting escalation processor...")
        
        try:
            # Get incidents that need escalation processing
            incidents = self.get_escalatable_incidents()
            
            # Process each incident
            for incident in incidents:
                try:
                    await self.process_incident_escalations(incident)
                except Exception as e:
                    logger.error(f"Error processing escalations for incident {incident.id}: {e}")
            
            logger.info(f"Completed escalation processing for {len(incidents)} incidents")
            
        except Exception as e:
            logger.error(f"Error in escalation processor: {e}")
            raise

async def main():
    """Main entry point."""
    processor = EscalationProcessor()
    await processor.run()

if __name__ == "__main__":
    asyncio.run(main())
