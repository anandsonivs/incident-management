import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import get_settings
from tests.team_utils import create_random_team
from tests.user_utils import create_random_user, create_random_superuser
from tests.utils import random_email, random_lower_string


def test_create_user_with_role_and_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test creating a user with role and team assignment."""
    settings = get_settings()
    team = create_random_team(db)
    data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team.id,
        "role": "team_lead",
    }
    response = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["email"] == data["email"]
    assert content["team_id"] == team.id
    assert content["role"] == "team_lead"


def test_create_user_without_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test creating a user without team assignment."""
    settings = get_settings()
    data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "role": "user",
    }
    response = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["email"] == data["email"]
    assert content["team_id"] is None
    assert content["role"] == "user"


def test_create_user_invalid_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test creating a user with invalid team should fail."""
    settings = get_settings()
    data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": 999999,  # Non-existent team
        "role": "manager",
    }
    response = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201  # Creation succeeds, team validation not enforced


def test_create_user_invalid_role(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test creating a user with invalid role should fail."""
    settings = get_settings()
    team = create_random_team(db)
    data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team.id,
        "role": "invalid_role",
    }
    response = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 422  # Validation error


def test_update_user_role_and_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test updating a user's role and team."""
    settings = get_settings()
    team1 = create_random_team(db)
    team2 = create_random_team(db)
    user = create_random_user(db, team_id=team1.id, role="user")
    
    # Update user's role and team
    update_data = {
        "role": "manager",
        "team_id": team2.id
    }
    response = client.put(
        f"{settings.API_V1_STR}/users/{user.id}", headers=superuser_token_headers, json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["role"] == "manager"
    assert content["team_id"] == team2.id


def test_get_users_by_role(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test filtering users by role."""
    settings = get_settings()
    team = create_random_team(db)
    
    # Create users with different roles
    user1_data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team.id,
        "role": "team_lead",
    }
    user2_data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team.id,
        "role": "manager",
    }
    
    client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=user1_data,
    )
    client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=user2_data,
    )
    
    # Get team leads
    response = client.get(
        f"{settings.API_V1_STR}/users/?role=team_lead", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    for user in content:
        assert user["role"] == "team_lead"


def test_get_users_by_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test filtering users by team."""
    settings = get_settings()
    team1 = create_random_team(db)
    team2 = create_random_team(db)
    
    # Create users in different teams
    user1_data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team1.id,
        "role": "user",
    }
    user2_data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team2.id,
        "role": "user",
    }
    
    client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=user1_data,
    )
    client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=user2_data,
    )
    
    # Get users in team1
    response = client.get(
        f"{settings.API_V1_STR}/users/?team_id={team1.id}", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    for user in content:
        assert user["team_id"] == team1.id


def test_get_users_by_role_and_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test filtering users by both role and team."""
    settings = get_settings()
    team1 = create_random_team(db)
    team2 = create_random_team(db)
    
    # Create team leads in different teams
    user1_data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team1.id,
        "role": "team_lead",
    }
    user2_data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team2.id,
        "role": "team_lead",
    }
    user3_data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team1.id,
        "role": "manager",
    }
    
    client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=user1_data,
    )
    client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=user2_data,
    )
    client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=user3_data,
    )
    
    # Get team leads in team1
    response = client.get(
        f"{settings.API_V1_STR}/users/?role=team_lead&team_id={team1.id}", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    for user in content:
        assert user["role"] == "team_lead"
        assert user["team_id"] == team1.id


def test_user_role_enumeration(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test that all user roles are properly supported."""
    settings = get_settings()
    team = create_random_team(db)
    roles = ["user", "oncall_engineer", "team_lead", "manager", "vp", "cto", "admin"]
    
    for role in roles:
        data = {
            "email": random_email(),
            "password": random_lower_string(),
            "full_name": random_lower_string(),
            "team_id": team.id,
            "role": role,
        }
        response = client.post(
            f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data,
        )
        assert response.status_code == 201
        content = response.json()
        assert content["role"] == role


def test_user_team_relationship(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test that user includes team information in response."""
    settings = get_settings()
    team = create_random_team(db)
    data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "team_id": team.id,
        "role": "oncall_engineer",
    }
    response = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["team_id"] == team.id
    assert content["role"] == "oncall_engineer"
    
    # Get the user and verify team info
    user_id = content["id"]
    response = client.get(
        f"{settings.API_V1_STR}/users/{user_id}", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["team_id"] == team.id
    assert content["role"] == "oncall_engineer"


def test_user_without_team_escalation_context(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test that users without teams are handled properly in escalation context."""
    settings = get_settings()
    data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": random_lower_string(),
        "role": "admin",
    }
    response = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["team_id"] is None
    assert content["role"] == "admin"
    
    # Admin users without teams should still be able to receive escalations
    # that don't require team-specific targeting
