from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.user import Token, User, UserCreate

router = APIRouter()

@router.post("/login/access-token")
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not crud.user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/login/test-token")
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    # Convert to schema, excluding hashed_password
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone_number": current_user.phone_number,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }
    return user_dict

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def create_user_signup(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    
    user = crud.user.create(db, obj_in=user_in)
    # Convert to schema, excluding hashed_password
    user_dict = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    return user_dict

@router.post("/password-recovery/{email}", response_model=schemas.Msg)
def recover_password(email: str, db: Session = Depends(get_db)) -> Any:
    """
    Password Recovery
    """
    user = crud.user.get_by_email(db, email=email)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    
    # TODO: Implement password recovery logic
    # password_reset_token = generate_password_reset_token(email=email)
    # send_reset_password_email(
    #     email_to=user.email, email=email, token=password_reset_token
    # )
    
    return {"msg": "Password recovery email sent"}

@router.post("/reset-password/", response_model=schemas.Msg)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Reset password
    """
    # TODO: Implement password reset logic
    # email = verify_password_reset_token(token)
    # if not email:
    #     raise HTTPException(status_code=400, detail="Invalid token")
    # 
    # user = crud.user.get_by_email(db, email=email)
    # if not user:
    #     raise HTTPException(
    #         status_code=404,
    #         detail="The user with this username does not exist in the system.",
    #     )
    # elif not crud.user.is_active(user):
    #     raise HTTPException(status_code=400, detail="Inactive user")
    # 
    # user_updated = crud.user.update_password(db, user=user, new_password=new_password)
    
    return {"msg": "Password updated successfully"}
