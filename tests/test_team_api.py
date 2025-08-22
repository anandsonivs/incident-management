import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import get_settings
from tests.team_utils import create_random_team
from tests.user_utils import create_random_user, create_random_superuser
from tests.utils import random_lower_string


def test_create_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test creating a new team."""
    settings = get_settings()
    data = {
        "name": random_lower_string(),
        "description": random_lower_string(),
        "is_active": True,
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert content["is_active"] == data["is_active"]
    assert "id" in content


def test_create_team_existing_name(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test creating a team with existing name should fail."""
    settings = get_settings()
    team_in = create_random_team(db)
    data = {
        "name": team_in.name,
        "description": random_lower_string(),
        "is_active": True,
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 400


def test_read_teams(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test reading teams."""
    settings = get_settings()
    team1 = create_random_team(db)
    team2 = create_random_team(db)
    response = client.get(
        f"{settings.API_V1_STR}/teams/", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 2
    for item in content:
        assert "id" in item
        assert "name" in item
        assert "description" in item
        assert "is_active" in item
        assert "user_count" in item


def test_read_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test reading a specific team."""
    settings = get_settings()
    team = create_random_team(db)
    response = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == team.id
    assert content["name"] == team.name
    assert content["description"] == team.description
    assert content["is_active"] == team.is_active


def test_read_team_not_found(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test reading a non-existent team."""
    settings = get_settings()
    response = client.get(
        f"{settings.API_V1_STR}/teams/999999", headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_update_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test updating a team."""
    settings = get_settings()
    team = create_random_team(db)
    data = {
        "name": random_lower_string(),
        "description": random_lower_string(),
        "is_active": False,
    }
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == team.id
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert content["is_active"] == data["is_active"]


def test_update_team_not_found(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test updating a non-existent team."""
    settings = get_settings()
    data = {
        "name": random_lower_string(),
        "description": random_lower_string(),
    }
    response = client.put(
        f"{settings.API_V1_STR}/teams/999999", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 404


def test_delete_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test deleting a team."""
    settings = get_settings()
    team = create_random_team(db)
    response = client.delete(
        f"{settings.API_V1_STR}/teams/{team.id}", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Team deleted successfully"


def test_delete_team_not_found(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test deleting a non-existent team."""
    settings = get_settings()
    response = client.delete(
        f"{settings.API_V1_STR}/teams/999999", headers=superuser_token_headers,
    )
    assert response.status_code == 404


@pytest.mark.skip(reason="Missing normal_user_token_headers fixture")
def test_create_team_normal_user(
    client: TestClient, normal_user_token_headers: dict, db: Session
) -> None:
    """Test that normal users cannot create teams."""
    data = {
        "name": random_lower_string(),
        "description": random_lower_string(),
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/", headers=normal_user_token_headers, json=data,
    )
    assert response.status_code == 403


@pytest.mark.skip(reason="Missing normal_user_token_headers fixture")
def test_read_teams_normal_user(
    client: TestClient, normal_user_token_headers: dict, db: Session
) -> None:
    """Test that normal users cannot read teams."""
    response = client.get(
        f"{settings.API_V1_STR}/teams/", headers=normal_user_token_headers,
    )
    assert response.status_code == 403


@pytest.mark.skip(reason="Missing normal_user_token_headers fixture")
def test_read_team_normal_user(
    client: TestClient, normal_user_token_headers: dict, db: Session
) -> None:
    """Test that normal users can read specific teams."""
    team = create_random_team(db)
    response = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}", headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == team.id
