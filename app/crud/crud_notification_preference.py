from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.notification_preference import NotificationPreference
from app.schemas.notification_preference import (
    NotificationPreferenceCreate, NotificationPreferenceUpdate
)

class CRUDNotificationPreference(CRUDBase[
    NotificationPreference, NotificationPreferenceCreate, NotificationPreferenceUpdate
]):
    def get_for_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[NotificationPreference]:
        """
        Get all notification preferences for a specific user.
        """
        return (
            db.query(self.model)
            .filter(NotificationPreference.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_channel(
        self, db: Session, *, user_id: int, channel: str
    ) -> Optional[NotificationPreference]:
        """
        Get a specific notification preference by user ID and channel.
        """
        return (
            db.query(self.model)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.channel == channel
            )
            .first()
        )
    
    def create_or_update(
        self, db: Session, *, obj_in: NotificationPreferenceCreate
    ) -> NotificationPreference:
        """
        Create or update a notification preference.
        """
        db_obj = self.get_by_channel(
            db, user_id=obj_in.user_id, channel=obj_in.channel
        )
        
        if db_obj:
            return self.update(db, db_obj=db_obj, obj_in=obj_in)
        return self.create(db, obj_in=obj_in)

notification_preference = CRUDNotificationPreference(NotificationPreference)
