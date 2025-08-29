from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class EscalationEvent(BaseModel):
    id: int
    incident_id: int
    policy_id: int
    step: int
    status: str  # pending, completed, failed
    created_at: datetime
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class EscalationEventCreate(BaseModel):
    incident_id: int
    policy_id: int
    step: int
    status: str
    metadata: Optional[Dict[str, Any]] = None
