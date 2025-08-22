from .base import CRUDBase

# Import CRUD operations
from .crud_user import user as user_crud
from .crud_team import team as team_crud
from .crud_notification_preference import notification_preference as notification_preference_crud

# These imports are done last to avoid circular imports
from .crud_escalation import escalation_policy as escalation_policy_crud, escalation_event as escalation_event_crud
from .crud_incident import (
	incident as incident_crud,
	timeline_event as timeline_event_crud,
	assignment as assignment_crud,
	comment as comment_crud,
)

# Backward-compatible aliases expected by code using `from app import crud`
user = user_crud
team = team_crud
incident = incident_crud
escalation_policy = escalation_policy_crud
escalation_event = escalation_event_crud
notification_preference = notification_preference_crud
timeline_event = timeline_event_crud
assignment = assignment_crud
comment = comment_crud

__all__ = [
	"CRUDBase",
	"user_crud",
	"team_crud",
	"incident_crud",
	"escalation_policy_crud",
	"escalation_event_crud",
	"notification_preference_crud",
	"timeline_event_crud",
	"assignment_crud",
	"comment_crud",
	# Aliases
	"user",
	"team",
	"incident",
	"escalation_policy",
	"escalation_event",
	"notification_preference",
	"timeline_event",
	"assignment",
	"comment",
]
