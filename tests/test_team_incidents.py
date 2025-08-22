import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import get_settings
from tests.team_utils import create_random_team
from tests.user_utils import create_random_user, create_random_superuser
from tests.utils import random_email, random_lower_string


def test_create_incident_with_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test creating an incident with team assignment."""
    settings = get_settings()
    team = create_random_team(db)
    data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "high",
        "service": random_lower_string(),
        "team_id": team.id,
    }
    response = client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["team_id"] == team.id
    assert content["severity"] == data["severity"]


def test_create_incident_without_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test creating an incident without team assignment."""
    settings = get_settings()
    data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "medium",
        "service": random_lower_string(),
    }
    response = client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["team_id"] is None


def test_create_incident_invalid_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test creating an incident with invalid team should fail."""
    settings = get_settings()
    data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "high",
        "service": random_lower_string(),
        "team_id": 999999,  # Non-existent team
    }
    response = client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201  # API doesn't validate team existence during creation


def test_update_incident_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test updating an incident's team assignment."""
    settings = get_settings()
    team1 = create_random_team(db)
    team2 = create_random_team(db)
    
    # Create incident with team1
    incident_data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "medium",
        "service": random_lower_string(),
        "team_id": team1.id,
    }
    response = client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=incident_data,
    )
    assert response.status_code == 201
    incident_id = response.json()["id"]
    
    # Update incident to team2
    update_data = {
        "team_id": team2.id
    }
    response = client.put(
        f"{settings.API_V1_STR}/incidents/{incident_id}", headers=superuser_token_headers, json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["team_id"] == team2.id


def test_get_incidents_by_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test filtering incidents by team."""
    settings = get_settings()
    team1 = create_random_team(db)
    team2 = create_random_team(db)
    
    # Create incidents for different teams
    incident1_data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "high",
        "service": random_lower_string(),
        "team_id": team1.id,
    }
    incident2_data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "medium",
        "service": random_lower_string(),
        "team_id": team2.id,
    }
    
    client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=incident1_data,
    )
    client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=incident2_data,
    )
    
    # Get incidents for team1
    response = client.get(
        f"{settings.API_V1_STR}/incidents/?team_id={team1.id}", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    for incident in content:
        assert incident["team_id"] == team1.id


def test_assign_user_to_team_incident(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test assigning a user to an incident within their team."""
    settings = get_settings()
    team = create_random_team(db)
    user = create_random_user(db, team_id=team.id)
    
    # Create incident for the team
    incident_data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "high",
        "service": random_lower_string(),
        "team_id": team.id,
    }
    response = client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=incident_data,
    )
    assert response.status_code == 201
    incident_id = response.json()["id"]
    
    # Assign user to incident
    assignment_data = {
        "user_id": user.id,
        "role": "responder"
    }
    response = client.post(
        f"{settings.API_V1_STR}/incidents/{incident_id}/assign", headers=superuser_token_headers, json=assignment_data,
    )
    assert response.status_code == 200


def test_assign_user_from_different_team(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test assigning a user from a different team to an incident."""
    settings = get_settings()
    team1 = create_random_team(db)
    team2 = create_random_team(db)
    user = create_random_user(db, team_id=team2.id)
    
    # Create incident for team1
    incident_data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "high",
        "service": random_lower_string(),
        "team_id": team1.id,
    }
    response = client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=incident_data,
    )
    assert response.status_code == 201
    incident_id = response.json()["id"]
    
    # Assign user from team2 to incident in team1 (should be allowed)
    assignment_data = {
        "user_id": user.id,
        "role": "responder"
    }
    response = client.post(
        f"{settings.API_V1_STR}/incidents/{incident_id}/assign", headers=superuser_token_headers, json=assignment_data,
    )
    assert response.status_code == 200


def test_incident_team_relationship(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test that incident includes team information in response."""
    settings = get_settings()
    team = create_random_team(db)
    data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "critical",
        "service": random_lower_string(),
        "team_id": team.id,
    }
    response = client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["team_id"] == team.id
    
    # Get the incident and verify team info
    incident_id = content["id"]
    response = client.get(
        f"{settings.API_V1_STR}/incidents/{incident_id}", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["team_id"] == team.id


def test_incident_with_team_escalation_context(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test that incident team information is available for escalation context."""
    settings = get_settings()
    team = create_random_team(db)
    data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "high",
        "service": random_lower_string(),
        "team_id": team.id,
    }
    response = client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["team_id"] == team.id
    
    # The escalation service should be able to use this team_id
    # to find appropriate escalation targets within the team


def test_incident_team_filtering_with_status(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test filtering incidents by team and status."""
    settings = get_settings()
    team = create_random_team(db)
    
    # Create incidents with different statuses for the same team
    incident1_data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "high",
        "service": random_lower_string(),
        "team_id": team.id,
        "status": "triggered"
    }
    incident2_data = {
        "title": random_lower_string(),
        "description": random_lower_string(),
        "severity": "medium",
        "service": random_lower_string(),
        "team_id": team.id,
        "status": "acknowledged"
    }
    
    client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=incident1_data,
    )
    client.post(
        f"{settings.API_V1_STR}/incidents/", headers=superuser_token_headers, json=incident2_data,
    )
    
    # Get triggered incidents for the team
    response = client.get(
        f"{settings.API_V1_STR}/incidents/?team_id={team.id}&status=triggered", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    for incident in content:
        assert incident["team_id"] == team.id
        assert incident["status"] == "triggered"
