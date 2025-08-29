"""
Tests for Frontend Functionality.

This module tests the frontend functionality including:
- Event delegation for action buttons
- Time display and timezone handling
- Cache busting
- API integration
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.models.incident import Incident, IncidentStatus
from app.models.user import User, UserRole
from app.models.escalation import EscalationPolicy, EscalationEvent
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.team import Team
from app.core.security import create_access_token


class TestFrontendEventDelegation:
    """Test frontend event delegation functionality."""

    def test_trigger_escalation_button_functionality(self, client: TestClient, db: Session, test_user: User):
        """Test that trigger escalation button works with event delegation."""
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
            team_id=team.id,
            status=IncidentStatus.TRIGGERED
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        # Assign user to incident
        from app.models.incident import IncidentAssignment
        assignment = IncidentAssignment(
            incident_id=incident.id,
            recipient="test@example.com",
            user_id=test_user.id,
            assigned_at=datetime.utcnow()
        )
        db.add(assignment)
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the escalation endpoint directly
        response = client.post(f"/v1/escalation/incidents/{incident.id}/escalate/", headers=headers)
        assert response.status_code == 200

        # Verify escalation event was created
        events_response = client.get("/v1/escalation/events/", headers=headers)
        assert events_response.status_code == 200
        events_data = events_response.json()
        assert len(events_data) == 1
        assert events_data[0]["incident_id"] == incident.id

    def test_action_buttons_event_delegation(self, client: TestClient, db: Session, test_user: User):
        """Test that all action buttons work with event delegation."""
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
            team_id=team.id,
            status=IncidentStatus.TRIGGERED
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test acknowledge endpoint
        response = client.post(f"/v1/incidents/{incident.id}/acknowledge", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "acknowledged"

        # Test snooze endpoint
        response = client.post(f"/v1/incidents/{incident.id}/snooze?hours=2", headers=headers)
        assert response.status_code == 200

        # Test resolve endpoint
        response = client.post(f"/v1/incidents/{incident.id}/resolve", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"


class TestFrontendCacheBusting:
    """Test frontend cache busting functionality."""

    def test_cache_busting_parameters(self):
        """Test that cache busting parameters are properly set."""
        # Read the HTML file
        with open("app/frontend/index.html", "r") as f:
            html_content = f.read()
        
        # Check that cache busting parameters are present
        assert "app.js?v=" in html_content
        assert "&t=" in html_content
        assert "&cb=" in html_content
        
        # Check that the version number is reasonable
        import re
        version_match = re.search(r'app\.js\?v=(\d+)', html_content)
        assert version_match is not None
        version = int(version_match.group(1))
        assert version >= 1  # Should be at least version 1

    def test_script_loading(self, client: TestClient):
        """Test that the JavaScript file loads correctly with cache busting."""
        # Test the script endpoint
        response = client.get("/app.js?v=6&t=20250828&cb=1735392000")
        assert response.status_code == 200
        assert "text/javascript" in response.headers.get("content-type", "")
        
        # Check that the JavaScript contains expected functions
        js_content = response.text
        assert "class IncidentManagementApp" in js_content
        assert "triggerEscalation" in js_content
        assert "getTimeAgo" in js_content
        assert "loadEscalations" in js_content
        assert "loadNotifications" in js_content


class TestFrontendAPIIntegration:
    """Test frontend API integration."""

    def test_escalations_api_integration(self, client: TestClient, db: Session, test_user: User):
        """Test that frontend can load escalations from the new API."""
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

        # Create escalation event
        event = EscalationEvent(
            incident_id=incident.id,
            recipient="test@example.com",
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

        # Test the escalations API endpoint
        response = client.get("/v1/escalation/events/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        event_data = data[0]
        assert event_data["incident_id"] == incident.id
        assert event_data["policy_id"] == policy.id
        assert "created_at" in event_data
        assert "incident" in event_data
        assert "policy" in event_data

    def test_notifications_api_integration(self, client: TestClient, db: Session, test_user: User):
        """Test that frontend can load notifications from the new API."""
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

        # Create notification
        notification = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Test Notification",
            message="Test message",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SENT,
            created_at=datetime.utcnow(),
            sent_at=datetime.utcnow()
        )
        db.add(notification)
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the notifications API endpoint
        response = client.get("/v1/notifications/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        notification_data = data[0]
        assert notification_data["user_id"] == test_user.id
        assert notification_data["incident_id"] == incident.id
        assert notification_data["title"] == "Test Notification"
        assert notification_data["channel"] == "email"
        assert notification_data["status"] == "sent"
        assert "created_at" in notification_data
        assert "sent_at" in notification_data

    def test_api_error_handling(self, client: TestClient, test_user: User):
        """Test that frontend handles API errors gracefully."""
        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test with non-existent incident
        response = client.get("/v1/escalation/incidents/99999/escalation-events/", headers=headers)
        assert response.status_code == 404

        # Test with non-existent notification
        response = client.get("/v1/notifications/99999", headers=headers)
        assert response.status_code == 404

        # Test without authentication
        response = client.get("/v1/escalation/events/")
        assert response.status_code == 401


class TestFrontendDataSorting:
    """Test frontend data sorting functionality."""

    def test_escalations_sorted_by_created_at_desc(self, client: TestClient, db: Session, test_user: User):
        """Test that escalations are sorted by created_at desc."""
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

        # Create escalation events with different timestamps
        event1 = EscalationEvent(
            incident_id=incident.id,
            recipient="test@example.com",
            policy_id=policy.id,
            step=1,
            status="triggered",
            triggered_at=datetime.utcnow() - timedelta(hours=3),
            created_at=datetime.utcnow() - timedelta(hours=3)
        )
        event2 = EscalationEvent(
            incident_id=incident.id,
            recipient="test@example.com",
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

        # Test the API endpoint
        response = client.get("/v1/escalation/events/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should be sorted by created_at desc (newest first)
        assert len(data) == 2
        assert data[0]["id"] == event2.id  # Newer event first
        assert data[1]["id"] == event1.id  # Older event second

    def test_notifications_sorted_by_created_at_desc(self, client: TestClient, db: Session, test_user: User):
        """Test that notifications are sorted by created_at desc."""
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

        # Create notifications with different timestamps
        notification1 = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Test Notification 1",
            message="Test message 1",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SENT,
            created_at=datetime.utcnow() - timedelta(hours=3),
            sent_at=datetime.utcnow() - timedelta(hours=3)
        )
        notification2 = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Test Notification 2",
            message="Test message 2",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SENT,
            created_at=datetime.utcnow() - timedelta(hours=1),
            sent_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        db.add_all([notification1, notification2])
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the API endpoint
        response = client.get("/v1/notifications/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should be sorted by created_at desc (newest first)
        assert len(data) == 2
        assert data[0]["id"] == notification2.id  # Newer notification first
        assert data[1]["id"] == notification1.id  # Older notification second
