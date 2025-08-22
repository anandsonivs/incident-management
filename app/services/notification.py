from typing import List, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app import crud, models, schemas
from app.core.config import get_settings

# Initialize settings
settings = get_settings()
from app.db.session import get_db
from app.models.incident import Incident, IncidentStatus, IncidentSeverity

class NotificationService:
	def __init__(self, db: Session):
		self.db = db
	
	async def send_incident_notification(
		self,
		incident: models.Incident,
		event_type: str,
		message: Optional[str] = None,
		**kwargs
	) -> None:
		"""
		Send notifications about incident events to relevant users.
		
		Args:
			incident: The incident to notify about
			event_type: Type of event (e.g., 'created', 'acknowledged', 'resolved')
			message: Custom message to include in the notification
			**kwargs: Additional data for the notification
		"""
		# Get all users who should be notified about this incident
		users_to_notify = self._get_users_to_notify(incident, event_type)
		
		# Prepare notification content
		notification_data = self._prepare_notification(incident, event_type, message, **kwargs)
		
		# Send notifications to each user through their preferred channels
		for user in users_to_notify:
			await self._notify_user(user, notification_data)
	
	async def send_notification(
		self,
		recipient: str,
		message: str,
		incident_id: int,
		action_type: str,
		metadata: Optional[dict] = None,
	) -> None:
		"""
		Generic notification interface used by escalation actions.
		This can be expanded to resolve recipients and channels.
		"""
		print(f"[Notification:{action_type}] incident={incident_id} to={recipient} msg={message}")
		# In a real implementation, map recipient to users/channels and dispatch via _send_email/_send_sms/etc.
	
	def _get_users_to_notify(
		self, incident: models.Incident, event_type: str
	) -> List[models.User]:
		"""
		Get list of users who should be notified about this incident event.
		"""
		# Always notify assigned users
		users = [assignment.user for assignment in incident.assignments]
		
		# For critical incidents, also notify on-call users or team leads
		if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
			# TODO: Implement logic to get on-call users or team leads
			pass
			
		return users
	
	def _prepare_notification(
		self,
		incident: models.Incident,
		event_type: str,
		message: Optional[str] = None,
		**kwargs
	) -> dict:
		"""
		Prepare notification content based on incident and event type.
		"""
		# Default notification template
		notification = {
			"title": f"Incident {event_type.capitalize()}: {incident.title}",
			"message": message or f"Incident {incident.id} has been {event_type}.",
			"incident_id": incident.id,
			"incident_title": incident.title,
			"incident_status": incident.status,
			"incident_severity": incident.severity,
			"event_type": event_type,
			"timestamp": incident.updated_at.isoformat() if incident.updated_at else datetime.utcnow().isoformat(),
			"metadata": kwargs
		}
		
		# Customize based on event type
		if event_type == "created":
			notification["title"] = f"🚨 New Incident: {incident.title}"
			notification["message"] = (
				f"A new {incident.severity} severity incident has been created.\n"
				f"Status: {incident.status}\n"
				f"Service: {incident.service or 'N/A'}\n"
				f"{incident.description or ''}"
			)
		elif event_type == "acknowledged":
			notification["title"] = f"✅ Incident Acknowledged: {incident.title}"
			notification["message"] = f"Incident has been acknowledged by {kwargs.get('acknowledged_by', 'a user')}."
		elif event_type == "resolved":
			notification["title"] = f"✅ Incident Resolved: {incident.title}"
			notification["message"] = f"Incident has been resolved by {kwargs.get('resolved_by', 'a user')}."
		
		return notification
	
	async def _notify_user(
		self, user: models.User, notification_data: dict
	) -> None:
		"""
		Send notification to a user through their preferred channels.
		"""
		# Get user's notification preferences
		prefs = crud.notification_preference.get_for_user(self.db, user_id=user.id)
		
		# Send via each enabled channel
		for pref in prefs:
			if pref.channel == "email" and pref.enabled and user.email:
				await self._send_email(user.email, notification_data)
			elif pref.channel == "sms" and pref.enabled and user.phone_number:
				await self._send_sms(user.phone_number, notification_data)
			elif pref.channel == "whatsapp" and pref.enabled and user.phone_number:
				await self._send_whatsapp(user.phone_number, notification_data)
	
	async def _send_email(self, email: str, data: dict) -> None:
		"""Send notification via email."""
		# TODO: Implement email sending logic
		# Example: Use SendGrid, AWS SES, etc.
		print(f"[Email to {email}] {data['title']}\n{data['message']}")
	
	async def _send_sms(self, phone_number: str, data: dict) -> None:
		"""Send notification via SMS."""
		# TODO: Implement SMS sending logic using Twilio or similar service
		print(f"[SMS to {phone_number}] {data['title']}: {data['message']}")
	
	async def _send_whatsapp(self, phone_number: str, data: dict) -> None:
		"""Send notification via WhatsApp."""
		# TODO: Implement WhatsApp sending logic using Twilio or similar service
		print(f"[WhatsApp to {phone_number}] {data['title']}: {data['message']}")

# Dependency
def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
	return NotificationService(db)
