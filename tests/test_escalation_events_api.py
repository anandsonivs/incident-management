"""
Tests for Escalation Events API endpoints.

This module tests the new escalation events functionality including:
- GET /v1/escalation/events/ - Get all escalation events
- GET /v1/escalation/incidents/{id}/escalation-events/ - Get incident escalation events
- POST /v1/escalation/incidents/{id}/escalate/ - Manual escalation trigger
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.incident import Incident, IncidentStatus
from app.models.user import User, UserRole
from app.models.escalation import EscalationPolicy, EscalationEvent
from app.models.team import Team
from app.core.security import create_access_token


class TestEscalationEventsAPI:
    """Test escalation events API endpoints."""

    def test_get_all_escalation_events(self, client: TestClient, db: Session, test_user: User):
        """Test getting all escalation events."""
        # Create test data
        team = Team(name="Test Team", description="Test team")
        db.add(team)
        db.commit()
        db.refresh(team)

        incident = Incident(
            title="Test Incident",
            description="Test description",
            severity="high",
            service="test-service",
            team_id=team.id
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        policy = EscalationPolicy(
            name="Test Policy",
            description="Test policy",
            steps=[{"delay": 5, "action": "notify"}]
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

        # Create escalation events
        event1 = EscalationEvent(
            incident_id=incident.id,
            policy_id=policy.id,
            step=1,
            status="triggered",
            triggered_at=datetime.utcnow() - timedelta(hours=2),
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        event2 = EscalationEvent(
            incident_id=incident.id,
            policy_id=policy.id,
            step=2,
            status="completed",
            triggered_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow() - timedelta(minutes=30),
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        db.add_all([event1, event2])
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the endpoint
        response = client.get("/v1/escalation/events/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return events sorted by created_at desc (newest first)
        assert len(data) == 2
        assert data[0]["id"] == event2.id  # Newer event first
        assert data[1]["id"] == event1.id  # Older event second
        
        # Check event structure
        event = data[0]
        assert "id" in event
        assert "incident_id" in event
        assert "policy_id" in event
        assert "step" in event
        assert "status" in event
        assert "triggered_at" in event
        assert "completed_at" in event
        assert "created_at" in event
        assert "metadata" in event
        
        # Check nested incident data
        assert "incident" in event
        assert event["incident"]["id"] == incident.id
        assert event["incident"]["title"] == incident.title
        assert "team" in event["incident"]
        
        # Check nested policy data
        assert "policy" in event
        assert event["policy"]["id"] == policy.id
        assert event["policy"]["name"] == policy.name

    def test_get_incident_escalation_events(self, client: TestClient, db: Session, test_user: User):
        """Test getting escalation events for a specific incident."""
        # Create test data
        team = Team(name="Test Team", description="Test team")
        db.add(team)
        db.commit()
        db.refresh(team)

        incident = Incident(
            title="Test Incident",
            description="Test description",
            severity="high",
            service="test-service",
            team_id=team.id
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        policy = EscalationPolicy(
            name="Test Policy",
            description="Test policy",
            steps=[{"delay": 5, "action": "notify"}]
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

        # Create escalation events
        event = EscalationEvent(
            incident_id=incident.id,
            policy_id=policy.id,
            step=1,
            status="triggered",
            triggered_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(event)
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the endpoint
        response = client.get(f"/v1/escalation/incidents/{incident.id}/escalation-events/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        event_data = data[0]
        assert event_data["id"] == event.id
        assert event_data["incident_id"] == incident.id
        assert event_data["policy_id"] == policy.id
        assert "created_at" in event_data

    def test_get_incident_escalation_events_permission_denied(self, client: TestClient, db: Session, test_user: User):
        """Test that users without permission cannot access incident escalation events."""
        # Create a non-superuser test user
        non_superuser = User(
            id=999,
            email="nonsuper@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            full_name="Non Super User",
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(non_superuser)
        db.commit()
        db.refresh(non_superuser)
        
        # Create test data with different team
        team = Team(name="Other Team", description="Other team")
        db.add(team)
        db.commit()
        db.refresh(team)

        incident = Incident(
            title="Test Incident",
            description="Test description",
            severity="high",
            service="test-service",
            team_id=team.id
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        # Create access token for non-superuser
        token = create_access_token(subject=str(non_superuser.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the endpoint - should be forbidden
        response = client.get(f"/v1/escalation/incidents/{incident.id}/escalation-events/", headers=headers)
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_manual_escalation_trigger(self, client: TestClient, db: Session, test_user: User):
        """Test manual escalation trigger endpoint."""
        # Create test data
        team = Team(name="Test Team", description="Test team")
        db.add(team)
        db.commit()
        db.refresh(team)

        incident = Incident(
            title="Test Incident",
            description="Test description",
            severity="high",
            service="test-service",
            
            status=IncidentStatus.TRIGGERED
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        # Assign user to incident
        from app.models.incident import IncidentAssignment
        assignment = IncidentAssignment(
            incident_id=incident.id,
            user_id=test_user.id,
            assigned_at=datetime.utcnow()
        )
        db.add(assignment)
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the endpoint
        response = client.post(f"/v1/escalation/incidents/{incident.id}/escalate/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == incident.id

    def test_manual_escalation_trigger_permission_denied(self, client: TestClient, db: Session, test_user: User):
        """Test that users without permission cannot trigger escalations."""
        # Create a non-superuser test user
        non_superuser = User(
            id=998,
            email="nonsuper2@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            full_name="Non Super User 2",
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(non_superuser)
        db.commit()
        db.refresh(non_superuser)
        
        # Create test data with different team
        team = Team(name="Other Team", description="Other team")
        db.add(team)
        db.commit()
        db.refresh(team)

        incident = Incident(
            title="Test Incident",
            description="Test description",
            severity="high",
            service="test-service",
            team_id=team.id,
            status=IncidentStatus.TRIGGERED
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        # Create access token for non-superuser
        token = create_access_token(subject=str(non_superuser.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the endpoint - should be forbidden
        response = client.post(f"/v1/escalation/incidents/{incident.id}/escalate/", headers=headers)
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_escalation_events_pagination(self, client: TestClient, db: Session, test_user: User):
        """Test pagination for escalation events."""
        # Create test data
        team = Team(name="Test Team", description="Test team")
        db.add(team)
        db.commit()
        db.refresh(team)

        incident = Incident(
            title="Test Incident",
            description="Test description",
            severity="high",
            service="test-service",
            team_id=team.id
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        policy = EscalationPolicy(
            name="Test Policy",
            description="Test policy",
            steps=[{"delay": 5, "action": "notify"}]
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

        # Create multiple escalation events
        events = []
        for i in range(15):
            event = EscalationEvent(
                incident_id=incident.id,
                policy_id=policy.id,
                step=i + 1,
                status="triggered",
                triggered_at=datetime.utcnow() - timedelta(hours=i),
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            events.append(event)
        
        db.add_all(events)
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test pagination
        response = client.get("/v1/escalation/events/?skip=0&limit=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10  # Default limit is 100, but we're testing with limit=10

        # Test second page
        response = client.get("/v1/escalation/events/?skip=10&limit=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # Remaining 5 events

    def test_escalation_events_with_metadata(self, client: TestClient, db: Session, test_user: User):
        """Test escalation events with metadata."""
        # Create test data
        team = Team(name="Test Team", description="Test team")
        db.add(team)
        db.commit()
        db.refresh(team)

        incident = Incident(
            title="Test Incident",
            description="Test description",
            severity="high",
            service="test-service",
            team_id=team.id
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        policy = EscalationPolicy(
            name="Test Policy",
            description="Test policy",
            steps=[{"delay": 5, "action": "notify"}]
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

        # Create escalation event with metadata
        metadata = {
            "escalation_reason": "Manual trigger",
            "escalated_by": "test_user",
            "priority": "high"
        }
        
        event = EscalationEvent(
            incident_id=incident.id,
            policy_id=policy.id,
            step=1,
            status="triggered",
            triggered_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            event_metadata=metadata
        )
        db.add(event)
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the endpoint
        response = client.get("/v1/escalation/events/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        event_data = data[0]
        assert event_data["metadata"] == metadata
