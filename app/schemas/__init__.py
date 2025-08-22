"""
Pydantic schemas for the Incident Management System.

This module contains all the Pydantic models used for request/response validation
and serialization.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

# Import base models first
from pydantic import BaseModel, ConfigDict

# Import type variables
from .types import ModelType, CreateSchemaType, UpdateSchemaType

# Import base schema
from .base import BaseSchema

# Import enums first (no dependencies)
from .incident import IncidentStatus, IncidentSeverity

# Import user schemas (they only depend on base schemas)
from .user import (
    UserBase,
    UserCreate,
    UserInDBBase,
    UserUpdate,
    User,
    UserWithRelations,
    Token,
    TokenPayload,
    Msg,
)

# Import incident schemas
from .incident import (
    IncidentBase,
    IncidentCreate,
    IncidentInDBBase,
    Incident,
    IncidentWithRelations,
    AssignmentBase,
    AssignmentCreate,
    Assignment,
    CommentBase,
    CommentCreate,
    Comment,
    TimelineEventBase,
    TimelineEventCreate,
    TimelineEvent,
    TimelineEventType
)

# Import escalation schemas
from .escalation import (
    EscalationPolicy,
    EscalationPolicyBase,
    EscalationPolicyCreate,
    EscalationPolicyUpdate,
    EscalationPolicyInDBBase,
    EscalationEvent,
    EscalationEventBase,
    EscalationEventCreate,
    EscalationEventInDBBase,
    EscalationEventStatus,
)

# Re-export everything for easier imports
__all__ = [
    # Base schemas
    'BaseModel', 'BaseSchema', 'ModelType', 'CreateSchemaType', 'UpdateSchemaType',
    
    # User schemas
    'User', 'UserBase', 'UserCreate', 'UserInDBBase', 'UserUpdate', 'UserWithRelations',
    'Token', 'TokenPayload', 'Msg',
    
    # Incident schemas
    'IncidentBase', 'IncidentCreate', 'IncidentUpdate', 'IncidentInDBBase', 'IncidentWithRelations',
    'IncidentStatus', 'IncidentSeverity',
    'AssignmentBase', 'AssignmentCreate', 'Assignment',
    'CommentBase', 'CommentCreate', 'Comment',
    'TimelineEvent', 'TimelineEventBase', 'TimelineEventCreate', 'TimelineEventType',
    
    # Escalation schemas
    'EscalationPolicy', 'EscalationPolicyCreate', 'EscalationPolicyUpdate',
    'EscalationEvent', 'EscalationEventCreate', 'EscalationEventStatus',
    'EscalationEventBase', 'EscalationEventInDBBase'
]
