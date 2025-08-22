from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class TeamBase(BaseModel):
    """Base schema for team data."""
    name: str = Field(..., description="Team name")
    description: Optional[str] = Field(None, description="Team description")
    is_active: bool = Field(True, description="Whether the team is active")

    model_config = ConfigDict(
        from_attributes=True
    )

class TeamCreate(TeamBase):
    """Schema for creating a new team."""
    pass

class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    name: Optional[str] = Field(None, description="Team name")
    description: Optional[str] = Field(None, description="Team description")
    is_active: Optional[bool] = Field(None, description="Whether the team is active")

    model_config = ConfigDict(
        from_attributes=True
    )

class Team(TeamBase):
    """Schema for returning a team with system fields."""
    id: int = Field(..., description="Unique identifier for the team")
    created_at: datetime = Field(..., description="When the team was created")
    updated_at: Optional[datetime] = Field(None, description="When the team was last updated")
    user_count: Optional[int] = Field(None, description="Number of users in the team")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Platform Team",
                "description": "Platform infrastructure and services team",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "user_count": 5
            }
        }
    )
