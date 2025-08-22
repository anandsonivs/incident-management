from typing import Optional
from sqlalchemy.orm import Session

from app.services.escalation_service import EscalationService
from app import crud


def get_escalation_service(db: Session) -> EscalationService:
    """Get a new escalation service instance bound to the provided DB session."""
    return EscalationService(db=db, crud=crud.escalation_policy)
