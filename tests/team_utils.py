import random
import string
from typing import Optional

from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.team import Team


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def create_random_team(db: Session) -> Team:
    """Create a random team for testing."""
    team_in = schemas.TeamCreate(
        name=random_lower_string(),
        description=random_lower_string(),
        is_active=True,
    )
    return crud.team.create(db=db, obj_in=team_in)


def create_random_team_data() -> dict:
    """Create random team data for testing."""
    return {
        "name": random_lower_string(),
        "description": random_lower_string(),
        "is_active": True,
    }
