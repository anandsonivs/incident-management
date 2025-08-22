from __future__ import annotations
import logging
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Any, Dict, Type, TypeVar, get_type_hints, TYPE_CHECKING
from datetime import datetime
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# Import type variables
from .types import ModelType, CreateSchemaType, UpdateSchemaType

# Use string literals for forward references
if TYPE_CHECKING:
    from .incident import Assignment, Comment, IncidentWithRelations

class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ONCALL_ENGINEER = "oncall_engineer"
    TEAM_LEAD = "team_lead"
    MANAGER = "manager"
    VP = "vp"
    CTO = "cto"
    ADMIN = "admin"
    
    def __str__(self):
        return self.value

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(..., description="User's email address, must be unique")
    full_name: Optional[str] = Field(None, description="User's full name")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    is_active: bool = Field(True, description="Whether the user account is active")
    is_superuser: bool = Field(False, description="Whether the user has superuser privileges")
    team_id: Optional[int] = Field(None, description="ID of the team the user belongs to")
    role: UserRole = Field(default="user", description="User's role in the system")
    
    model_config = ConfigDict(
        from_attributes=True,

    )

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100, description="User's password")
    
    # Override model_config to include password field in the example
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "is_active": True,
                "is_superuser": False,
                "team_id": 1,
                "role": "user"
            }
        }
    )
    
    def model_dump(self, **kwargs):
        """Convert model to dictionary."""
        return self.dict(**kwargs)

class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    team_id: Optional[int] = None
    role: Optional[UserRole] = None
    
    model_config = ConfigDict(
        from_attributes=True,

    )
    
    def model_dump(self, **kwargs):
        """Convert model to dictionary."""
        # Exclude unset fields by default
        kwargs.setdefault('exclude_unset', True)
        return self.dict(**kwargs)

class UserInDBBase(UserBase):
    """Base user schema for database models with common fields."""
    id: int = Field(..., description="Unique identifier for the user")
    created_at: datetime = Field(..., description="When the user account was created")
    updated_at: Optional[datetime] = Field(None, description="When the user account was last updated")
    
    model_config = ConfigDict(
        from_attributes=True,

    )
    
    def model_dump(self, **kwargs):
        """Convert model to dictionary."""
        return self.dict(**kwargs)

class User(UserInDBBase):
    """Schema for returning a user with basic information."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )


class UserWithRelations(UserInDBBase):
    """User model with related data."""
    incident_assignments: List[Any] = Field(default_factory=list)
    comments: List[Any] = Field(default_factory=list)
    incidents: List[Any] = Field(default_factory=list)
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False,
                "incident_assignments": [],
                "comments": [],
                "incidents": []
            }
        }
    )
    
    def model_dump(self, **kwargs):
        """Convert model to dictionary."""
        return self.dict(**kwargs)
    


class UserWithToken(User):
    """User schema with authentication token included."""
    access_token: str = Field(..., description="JWT access token for authentication")
    token_type: str = Field("bearer", description="Type of token, typically 'bearer'")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "is_active": True,
                    "is_superuser": False
                }
            }
        }

        orm_mode = True

class Token(BaseModel):
    """Authentication token schema."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Type of token, typically 'bearer'")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )

class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: Optional[int] = Field(None, description="Subject (user ID)")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,

    )

class Msg(BaseModel):
    msg: str
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "msg": "Operation completed successfully"
            }
        }
    )



# Re-export models that might be used by other modules
__all__ = [
    'User', 'UserBase', 'UserCreate', 'UserUpdate', 'UserInDBBase',
    'UserWithRelations', 'UserWithToken',
    'Token', 'TokenPayload', 'Msg'
]
