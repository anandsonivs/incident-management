from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel = Column(String, nullable=False)  # email, sms, whatsapp, push
    enabled = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")
