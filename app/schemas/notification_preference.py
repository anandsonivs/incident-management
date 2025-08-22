from typing import Optional
from pydantic import BaseModel, Field

class NotificationPreferenceBase(BaseModel):
    channel: str = Field(..., description="Notification channel (email, sms, whatsapp, push)")
    enabled: bool = Field(True, description="Whether notifications are enabled for this channel")

class NotificationPreferenceCreate(NotificationPreferenceBase):
    user_id: int = Field(..., description="ID of the user this preference belongs to")

class NotificationPreferenceUpdate(NotificationPreferenceBase):
    enabled: Optional[bool] = Field(None, description="Whether notifications are enabled for this channel")

class NotificationPreferenceInDBBase(NotificationPreferenceBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class NotificationPreference(NotificationPreferenceInDBBase):
    pass
