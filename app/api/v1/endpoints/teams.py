from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps

router = APIRouter()

@router.get("/")
def read_teams(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve teams.
    """
    teams = crud.team.get_all_teams_with_user_count(db, skip=skip, limit=limit)
    return teams

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_team(
    *,
    db: Session = Depends(deps.get_db),
    team_in: schemas.TeamCreate,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new team.
    """
    team = crud.team.get_by_name(db, name=team_in.name)
    if team:
        raise HTTPException(
            status_code=400,
            detail="A team with this name already exists in the system.",
        )
    team = crud.team.create(db, obj_in=team_in)
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "is_active": team.is_active,
        "created_at": team.created_at,
        "updated_at": team.updated_at
    }

@router.put("/{team_id}")
def update_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    team_in: schemas.TeamUpdate,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update team.
    """
    team = crud.team.get(db, id=team_id)
    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found",
        )
    team = crud.team.update(db, db_obj=team, obj_in=team_in)
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "is_active": team.is_active,
        "created_at": team.created_at,
        "updated_at": team.updated_at
    }

@router.get("/{team_id}")
def read_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    current_user: schemas.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get team by ID.
    """
    team = crud.team.get_team_with_user_count(db, team_id=team_id)
    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found",
        )
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "is_active": team.is_active,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
        "user_count": getattr(team, 'user_count', 0)
    }

@router.delete("/{team_id}")
def delete_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete team.
    """
    team = crud.team.get(db, id=team_id)
    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found",
        )
    team = crud.team.remove(db, id=team_id)
    return {"message": "Team deleted successfully"}
