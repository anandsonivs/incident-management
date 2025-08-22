from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db
from app.schemas.notification_preference import (
    NotificationPreference,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate
)

router = APIRouter()

@router.get("/me")
def get_my_notification_preferences(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's notification preferences.
    """
    return crud.notification_preference.get_for_user(db, user_id=current_user.id)

@router.put("/me/{channel}")
def update_my_notification_preference(
    *,
    db: Session = Depends(get_db),
    channel: str,
    preference_in: NotificationPreferenceUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update current user's notification preference for a specific channel.
    """
    # Check if preference exists
    preference = crud.notification_preference.get_by_channel(
        db, user_id=current_user.id, channel=channel
    )
    
    if not preference:
        # Create new preference if it doesn't exist
        preference_in = NotificationPreferenceCreate(
            channel=channel,
            enabled=preference_in.enabled,
            user_id=current_user.id
        )
        return crud.notification_preference.create(db, obj_in=preference_in)
    
    # Update existing preference
    return crud.notification_preference.update(
        db, db_obj=preference, obj_in=preference_in
    )

@router.get("/{user_id}")
def get_user_notification_preferences(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get notification preferences for a specific user (admin only).
    """
    return crud.notification_preference.get_for_user(db, user_id=user_id)

@router.put("/{user_id}/{channel}")
def update_user_notification_preference(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    channel: str,
    preference_in: NotificationPreferenceUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update notification preference for a specific user (admin only).
    """
    # Check if user exists
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if preference exists
    preference = crud.notification_preference.get_by_channel(
        db, user_id=user_id, channel=channel
    )
    
    if not preference:
        # Create new preference if it doesn't exist
        preference_in = NotificationPreferenceCreate(
            channel=channel,
            enabled=preference_in.enabled,
            user_id=user_id
        )
        return crud.notification_preference.create(db, obj_in=preference_in)
    
    # Update existing preference
    return crud.notification_preference.update(
        db, db_obj=preference, obj_in=preference_in
    )
