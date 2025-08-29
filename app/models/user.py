from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base

class UserRole(str, enum.Enum):
    USER = "user"
    ONCALL_ENGINEER = "oncall_engineer"
    TEAM_LEAD = "team_lead"
    MANAGER = "manager"
    VP = "vp"
    CTO = "cto"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="users")
    incident_assignments = relationship("IncidentAssignment", back_populates="user")
    comments = relationship("IncidentComment", back_populates="user")
    notification_preferences = relationship("NotificationPreference", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
