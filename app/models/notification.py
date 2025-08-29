from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"

class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Can be null for system notifications
    recipient = Column(String, nullable=False)  # Email, phone, or other identifier
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(Enum(NotificationChannel), default=NotificationChannel.EMAIL, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    action_type = Column(String, nullable=True)  # assignment, escalation, etc.
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    incident = relationship("Incident", back_populates="notifications")
    user = relationship("User", back_populates="notifications")
    
    # Add updated_at property to match SQLAlchemy expectations
    @property
    def updated_at(self):
        return self.created_at
