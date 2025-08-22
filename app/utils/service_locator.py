from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.escalation import get_escalation_service as _get_escalation_service


def get_escalation_service(db: Session = Depends(get_db)):
    """Forwarder to the canonical escalation service provider."""
    return _get_escalation_service(db)
