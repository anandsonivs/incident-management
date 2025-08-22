"""
Shared type definitions and type variables.
"""
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel

# Type variables for generic model types
ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# Type aliases are handled by importing directly in each schema
