import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta

from app.main import app
from app.models.escalation import EscalationPolicy
from app.models.user import User
from app.core.security import create_access_token

@pytest.fixture
def test_user():
    return User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=True
    )

@pytest.fixture
def test_token(test_user):
    return create_access_token(subject=str(test_user.id))

@pytest.fixture
def test_policy():
    return EscalationPolicy(
        id=1,
        name="Test Policy",
        description="Test Description",
        conditions={"severity": ["high"]},
        steps=[{"delay_minutes": 5, "actions": [{"type": "notify"}]}],
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@patch('app.crud.user_crud.is_superuser')
def test_create_escalation_policy(mock_is_superuser, mock_db, client, test_token):
    mock_is_superuser.return_value = True
    policy_data = {"name": "New Policy", "description": "New escalation policy", "conditions": {"severity": ["critical"]}, "steps": [{"delay_minutes": 10, "actions": [{"type": "notify"}]}], "is_active": True}
    response = client.post(
        "/v1/escalation/policies/",
        json=policy_data,
        headers={"Authorization": f"Bearer {test_token}", "Content-Type": "application/json"}
    )
    assert response.status_code in (200, 201), f"Unexpected status code: {response.status_code}, Response: {response.text}"
    data = response.json()
    assert data["name"] == "New Policy"

@patch('app.crud.user_crud.is_superuser')
def test_get_escalation_policy(mock_is_superuser, mock_db, client, test_policy, test_token):
    mock_is_superuser.return_value = True
    # Create a policy first
    policy_data = {"name": "Test Policy", "description": "Test Description", "conditions": {"severity": ["high"]}, "steps": [{"delay_minutes": 5, "actions": [{"type": "notify"}]}], "is_active": True}
    create_resp = client.post(
        "/v1/escalation/policies/",
        json=policy_data,
        headers={"Authorization": f"Bearer {test_token}", "Content-Type": "application/json"}
    )
    assert create_resp.status_code in (200, 201)
    created = create_resp.json()
    response = client.get(
        f"/v1/escalation/policies/{created['id']}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == "Test Policy"

@patch('app.crud.user_crud.is_superuser')
def test_trigger_escalation(mock_is_superuser, mock_db, client, test_incident, test_token):
    mock_is_superuser.return_value = True
    # Create an incident first
    incident_resp = client.post(
        "/v1/incidents/",
        json={"title": "Test Incident", "description": "", "severity": "high", "service": "api"},
        headers={"Authorization": f"Bearer {test_token}", "Content-Type": "application/json"}
    )
    assert incident_resp.status_code in (200, 201)
    incident_id = incident_resp.json()["id"]
    response = client.post(
        f"/v1/escalation/incidents/{incident_id}/escalate/",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    assert response.json().get("id") == incident_id

@patch('app.crud.user_crud.is_superuser')
def test_get_incident_escalation_events(mock_is_superuser, mock_db, client, test_incident, test_policy, test_token):
    mock_is_superuser.return_value = True
    # Create incident
    incident_resp = client.post(
        "/v1/incidents/",
        json={"title": "Test Incident", "description": "", "severity": "high", "service": "api"},
        headers={"Authorization": f"Bearer {test_token}", "Content-Type": "application/json"}
    )
    assert incident_resp.status_code in (200, 201)
    incident_id = incident_resp.json()["id"]
    # Create policy
    policy_resp = client.post(
        "/v1/escalation/policies/",
        json={"name": "Policy A", "steps": [{"delay_minutes": 0, "actions": [{"type": "notify"}]}]},
        headers={"Authorization": f"Bearer {test_token}", "Content-Type": "application/json"}
    )
    assert policy_resp.status_code in (200, 201)
    # Trigger escalation to create events
    client.post(
        f"/v1/escalation/incidents/{incident_id}/escalate/",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    response = client.get(
        f"/v1/escalation/incidents/{incident_id}/escalation-events/",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert isinstance(data, list)
