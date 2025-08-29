from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class NotificationHistory(BaseModel):
    id: int
    user_id: Optional[int] = None
    incident_id: Optional[int] = None
    title: str
    message: str
    channel: str  # email, sms, etc.
    status: str  # sent, failed, pending
    created_at: datetime
    sent_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class NotificationCreate(BaseModel):
    user_id: int
    incident_id: Optional[int] = None
    title: str
    message: str
    channel: str
    metadata: Optional[Dict[str, Any]] = None
