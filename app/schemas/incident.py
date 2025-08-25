from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Type, TypeVar, get_type_hints, Union, TYPE_CHECKING
from datetime import datetime
from enum import Enum
import sys
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Import type variables
from .types import ModelType, CreateSchemaType, UpdateSchemaType

# Use string literals for forward references
if TYPE_CHECKING:
    from .user import UserBase

# Forward references will be handled by string literals

class IncidentStatus(str, Enum):
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SNOOZED = "snoozed"
    
    def __str__(self):
        return self.value

class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
    def __str__(self):
        return self.value

class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: IncidentStatus = Field(default="triggered")
    severity: IncidentSeverity = Field(default="medium")
    service: Optional[str] = None
    team_id: Optional[int] = Field(None, description="ID of the team responsible for this incident")
    alert_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default={}, alias="metadata_")

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    severity: Optional[IncidentSeverity] = None
    title: Optional[str] = None
    description: Optional[str] = None
    team_id: Optional[int] = Field(None, description="ID of the team responsible for this incident")
    
    metadata: Optional[Dict[str, Any]] = None

class IncidentInDBBase(IncidentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    
    # Ensure status has a default value from IncidentStatus enum
    status: IncidentStatus = IncidentStatus.TRIGGERED

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Database Connection Error",
                "description": "Unable to connect to the database",
                "status": "triggered",
                "severity": "high",
                "service": "api-service",
                "team_id": 1,
                "alert_id": "db-error-123",
                "created_at": "2024-01-20T10:30:00Z",
                "updated_at": "2024-01-20T10:30:00Z",
                "metadata_": {"error_code": "ECONNREFUSED", "retry_count": 3}
            }
        }
    )

class Incident(IncidentInDBBase):
    pass

class IncidentWithRelations(IncidentInDBBase):
    assignments: List[Any] = Field(default_factory=list)
    comments: List[Any] = Field(default_factory=list)
    timeline_events: List[Any] = Field(default_factory=list)
    
    # Ensure status has a default value from IncidentStatus enum
    status: IncidentStatus = IncidentStatus.TRIGGERED
    
    class Config:
        orm_mode = True
        use_enum_values = True

class AssignmentBase(BaseModel):
    """Base schema for incident assignments."""
    user_id: int
    incident_id: int
    role: Optional[str] = "responder"

    model_config = ConfigDict(
        from_attributes=True
    )

class AssignmentCreate(AssignmentBase):
    """Schema for creating a new assignment."""
    pass

class AssignmentRequest(BaseModel):
    """Schema for assignment request (without incident_id since it comes from URL)."""
    user_id: int
    role: Optional[str] = "responder"

    model_config = ConfigDict(
        from_attributes=True
    )

class Assignment(BaseModel):
    """Schema for returning an assignment with system fields."""
    id: int
    assigned_at: datetime
    user: Optional[Any] = None
    
    model_config = ConfigDict(
        from_attributes=True,

        json_schema_extra={
            "example": {
                "id": 1,
                "assigned_at": "2023-01-01T00:00:00",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "John Doe"
                }
            }
        }
    )

class CommentBase(BaseModel):
    """Base schema for comment data."""
    content: str = Field(..., description="The comment text")
    incident_id: int = Field(..., description="The ID of the incident this comment belongs to")
    user_id: Optional[int] = Field(None, description="The ID of the user who created the comment")
    
    model_config = ConfigDict(
        from_attributes=True
    )

class CommentCreate(CommentBase):
    """Schema for creating a new comment."""
    pass

class Comment(CommentBase):
    """Schema for returning a comment with system fields and user information."""
    id: int = Field(..., description="Unique identifier for the comment")
    created_at: datetime = Field(..., description="When the comment was created")
    updated_at: Optional[datetime] = Field(None, description="When the comment was last updated")
    user: Optional[Any] = Field(None, description="The user who created the comment")
    
    # Use string literals for forward references
    __annotations__ = {
        **CommentBase.__annotations__,
        'id': int,
        'created_at': datetime,
        'updated_at': Optional[datetime],
        'user': Optional[Any]  # Will be updated in update_forward_refs
    }
    
    model_config = ConfigDict(
        from_attributes=True,

        json_schema_extra={
            "example": {
                "id": 1,
                "content": "This is a comment on the incident",
                "incident_id": 1,
                "user_id": 1,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "John Doe"
                }
            }
        }
    )
    
    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if 'user' in data and hasattr(data['user'], 'model_dump'):
            data['user'] = data['user'].model_dump()
        return data

class TimelineEventType(str, Enum):
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"
    COMMENT_ADDED = "comment_added"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"
    
    def __str__(self):
        return self.value

class TimelineEventBase(BaseModel):
    """Base schema for timeline events."""
    event_type: str  # Changed from TimelineEventType to str to avoid serialization issues
    data: Dict[str, Any] = Field(default={})
    incident_id: int
    user_id: Optional[int] = None

    class Config:
        orm_mode = True
        use_enum_values = True  # This will store the enum values instead of enum objects

class TimelineEventCreate(TimelineEventBase):
    """Schema for creating a new timeline event."""
    pass

class TimelineEvent(TimelineEventBase):
    """Schema for returning a timeline event with system fields."""
    id: int
    created_at: datetime
    created_by: Optional[int] = None
    
    model_config = ConfigDict(
        from_attributes=True,

        json_schema_extra={
            "example": {
                "id": 1,
                "event_type": "status_changed",
                "data": {"from": "triggered", "to": "acknowledged"},
                "incident_id": 1,
                "user_id": 1,
                "created_at": "2023-01-01T00:00:00",
                "created_by": 1
            }
        }
    )
    
    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Ensure all values are JSON serializable
        for key, value in data.items():
            if hasattr(value, 'isoformat'):  # Handle datetime objects
                data[key] = value.isoformat()
            elif hasattr(value, 'model_dump'):  # Handle nested models
                data[key] = value.model_dump()
        return data

# Re-export models that might be used by other modules
__all__ = [
    'Incident', 'IncidentBase', 'IncidentCreate', 'IncidentUpdate', 'IncidentInDBBase',
    'IncidentWithRelations', 'IncidentStatus', 'IncidentSeverity',
    'Assignment', 'AssignmentBase', 'AssignmentCreate',
    'Comment', 'CommentBase', 'CommentCreate',
    'TimelineEvent', 'TimelineEventBase', 'TimelineEventCreate', 'TimelineEventType'
]
