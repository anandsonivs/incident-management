"""
Base schemas and common functionality for all Pydantic models.
"""
from pydantic import BaseModel
from typing import Any, Dict, Optional, Type, TypeVar, Generic

# Type variables for generic model types
ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseSchema(BaseModel):
    """Base schema that all other schemas should inherit from.
    
    Provides common configuration and functionality.
    """
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class BaseCreateSchema(BaseSchema):
    """Base schema for creating new records."""
    pass

class BaseUpdateSchema(BaseSchema):
    """Base schema for updating existing records."""
    pass

class BaseInDBBase(BaseSchema):
    """Base schema for database models with common fields."""
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config(BaseSchema.Config):
        pass
