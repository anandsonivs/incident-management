import random
import string
from typing import Optional

from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.user import User, UserRole


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def create_random_user(
    db: Session, 
    *, 
    team_id: Optional[int] = None,
    role: UserRole = UserRole.USER,
    is_superuser: bool = False
) -> User:
    """Create a random user for testing."""
    user_in = schemas.UserCreate(
        email=random_email(),
        password=random_lower_string(),
        full_name=random_lower_string(),
        team_id=team_id,
        role=role,
        is_superuser=is_superuser,
    )
    return crud.user.create(db=db, obj_in=user_in)


def create_random_superuser(db: Session, *, team_id: Optional[int] = None) -> User:
    """Create a random superuser for testing."""
    return create_random_user(db, team_id=team_id, is_superuser=True)


def create_random_user_data(
    *, 
    team_id: Optional[int] = None,
    role: UserRole = UserRole.USER,
    is_superuser: bool = False
) -> dict:
    """Create random user data for testing."""
    return {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team_id,
        "role": role.value,
        "is_superuser": is_superuser,
    }
