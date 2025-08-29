from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum

# Forward references will be handled by string literals in field types

class EscalationPolicyBase(BaseModel):
    """Base schema for escalation policy."""
    name: str = Field(..., description="Unique name for the escalation policy")
    description: Optional[str] = Field(None, description="Description of the escalation policy")
    conditions: Dict[str, Any] = Field(
        default={},
        description="Conditions that trigger this policy (e.g., severity, service)"
    )
    steps: List[Dict[str, Any]] = Field(
        default=[],
        description="List of escalation steps with actions and delays"
    )
    is_active: bool = Field(True, description="Whether the escalation policy is active")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "High Severity Escalation",
                "description": "Policy for high severity incidents",
                "conditions": {"severity": "high"},
                "steps": [{"delay_minutes": 15, "action": "notify_team"}],
                "is_active": True
            }
        }
    )

    @validator('conditions')
    def validate_conditions(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError("Conditions must be a dictionary")
        return v or {}

    @validator('steps')
    def validate_steps(cls, v):
        if not isinstance(v, list):
            raise ValueError("Steps must be a list")
        
        for step in v:
            if not isinstance(step, dict):
                raise ValueError("Each step must be a dictionary")
            
            if 'delay_minutes' not in step:
                raise ValueError("Each step must have a 'delay_minutes' field")
                
            if 'actions' not in step:
                raise ValueError("Each step must have an 'actions' list")
                
            if not isinstance(step['actions'], list):
                raise ValueError("Each step must have an 'actions' list")
                
            if not step['actions']:
                raise ValueError("Each step must have at least one action")
                
            for action in step['actions']:
                if not isinstance(action, dict):
                    raise ValueError("Each action must be a dictionary")
                if 'type' not in action:
                    raise ValueError("Each action must have a 'type' field")
        
        return v

class EscalationPolicyCreate(EscalationPolicyBase):
    """Schema for creating a new escalation policy."""
    pass

class EscalationPolicyUpdate(EscalationPolicyBase):
    """Schema for updating an existing escalation policy."""
    name: Optional[str] = None
    is_active: Optional[bool] = None

class EscalationPolicyInDBBase(EscalationPolicyBase):
    """Base schema with common fields for DB models."""
    id: int = Field(..., description="Unique identifier for the escalation policy")
    created_at: datetime = Field(..., description="When the policy was created")
    updated_at: Optional[datetime] = Field(None, description="When the policy was last updated")
    
    model_config = ConfigDict(
        from_attributes=True
    )

class EscalationPolicy(EscalationPolicyInDBBase):
    """Schema for returning an escalation policy."""
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Critical Incident Policy",
                "description": "Policy for critical incidents",
                "conditions": {"severity": "critical"},
                "steps": [{"delay_minutes": 5, "actions": [{"type": "notify"}]}],
                "is_active": True,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }

class EscalationEventStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class EscalationEventBase(BaseModel):
    """Base schema for escalation events."""
    policy_id: int = Field(..., description="ID of the associated escalation policy")
    incident_id: int = Field(..., description="ID of the incident being escalated")
    step: int = Field(..., description="Current step in the escalation process")
    status: EscalationEventStatus = Field(
        default=EscalationEventStatus.PENDING,
        description="Current status of the escalation event"
    )
    metadata: Dict[str, Any] = Field(
        default={},
        description="Additional metadata for the escalation event"
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "policy_id": 1,
                "incident_id": 1,
                "step": 1,
                "status": "pending",
                "metadata": {}
            }
        }
    )

class EscalationEventCreate(EscalationEventBase):
    """Schema for creating a new escalation event."""
    pass

class EscalationEventInDBBase(EscalationEventBase):
    """Base schema with common fields for DB models."""
    id: int = Field(..., description="Unique identifier for the escalation event")
    triggered_at: datetime = Field(..., description="When the escalation was triggered")
    completed_at: Optional[datetime] = Field(None, description="When the escalation was completed")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class EscalationEvent(EscalationEventInDBBase):
    """Schema for returning an escalation event."""
    pass

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "incident_id": 1,
                "policy_id": 1,
                "step": 1,
                "status": "completed",
                "triggered_at": "2023-01-01T00:00:00",
                "completed_at": "2023-01-01T00:05:00",
                "metadata": {}
            }
        }
