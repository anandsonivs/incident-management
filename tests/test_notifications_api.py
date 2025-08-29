"""
Tests for Notifications API endpoints.

This module tests the new notifications functionality including:
- GET /v1/notifications/ - Get all notifications
- GET /v1/notifications/history - Get notification history
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.incident import Incident, IncidentStatus
from app.models.user import User, UserRole
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.team import Team
from app.core.security import create_access_token


class TestNotificationsAPI:
    """Test notifications API endpoints."""

    def test_get_all_notifications(self, client: TestClient, db: Session, test_user: User):
        """Test getting all notifications."""
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

        # Create notifications
        notification1 = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Test Notification 1",
            message="Test message 1",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SENT,
            created_at=datetime.utcnow() - timedelta(hours=2),
            sent_at=datetime.utcnow() - timedelta(hours=2)
        )
        notification2 = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Test Notification 2",
            message="Test message 2",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.PENDING,
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        db.add_all([notification1, notification2])
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the endpoint
        response = client.get("/v1/notifications/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return notifications sorted by created_at desc (newest first)
        assert len(data) == 2
        assert data[0]["id"] == notification2.id  # Newer notification first
        assert data[1]["id"] == notification1.id  # Older notification second
        
        # Check notification structure
        notification = data[0]
        assert "id" in notification
        assert "user_id" in notification
        assert "incident_id" in notification
        assert "title" in notification
        assert "message" in notification
        assert "channel" in notification
        assert "status" in notification
        assert "created_at" in notification
        assert "sent_at" in notification
        assert "metadata" in notification

    def test_get_notification_history(self, client: TestClient, db: Session, test_user: User):
        """Test getting notification history."""
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

        # Test the endpoint
        response = client.get("/v1/notifications/history", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        notification_data = data[0]
        assert notification_data["id"] == notification.id
        assert notification_data["user_id"] == test_user.id
        assert notification_data["incident_id"] == incident.id
        assert notification_data["title"] == "Test Notification"
        assert notification_data["channel"] == "email"
        assert notification_data["status"] == "sent"

    def test_notifications_pagination(self, client: TestClient, db: Session, test_user: User):
        """Test pagination for notifications."""
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

        # Create multiple notifications
        notifications = []
        for i in range(15):
            notification = Notification(
                user_id=test_user.id,
                incident_id=incident.id,
            recipient="test@example.com",
                title=f"Test Notification {i}",
                message=f"Test message {i}",
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.SENT,
                created_at=datetime.utcnow() - timedelta(hours=i),
                sent_at=datetime.utcnow() - timedelta(hours=i)
            )
            notifications.append(notification)
        
        db.add_all(notifications)
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test pagination
        response = client.get("/v1/notifications/?skip=0&limit=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

        # Test second page
        response = client.get("/v1/notifications/?skip=10&limit=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # Remaining 5 notifications

    def test_notifications_with_metadata(self, client: TestClient, db: Session, test_user: User):
        """Test notifications with metadata."""
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

        # Create notification with metadata
        metadata = {
            "retry_count": 3,
            "delivery_method": "smtp",
            "template_id": "incident_alert"
        }
        
        notification = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Test Notification",
            message="Test message",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SENT,
            created_at=datetime.utcnow(),
            sent_at=datetime.utcnow(),
            metadata_=metadata
        )
        db.add(notification)
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the endpoint
        response = client.get("/v1/notifications/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        notification_data = data[0]
        assert notification_data["metadata"] == metadata

    def test_notifications_different_channels(self, client: TestClient, db: Session, test_user: User):
        """Test notifications with different channels."""
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

        # Create notifications with different channels
        email_notification = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Email Notification",
            message="Email message",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SENT,
            created_at=datetime.utcnow(),
            sent_at=datetime.utcnow()
        )
        
        sms_notification = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="SMS Notification",
            message="SMS message",
            channel=NotificationChannel.SMS,
            status=NotificationStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        db.add_all([email_notification, sms_notification])
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the endpoint
        response = client.get("/v1/notifications/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        
        # Check that both channels are present
        channels = [n["channel"] for n in data]
        assert "email" in channels
        assert "sms" in channels

    def test_notifications_different_statuses(self, client: TestClient, db: Session, test_user: User):
        """Test notifications with different statuses."""
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

        # Create notifications with different statuses
        sent_notification = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Sent Notification",
            message="Sent message",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SENT,
            created_at=datetime.utcnow(),
            sent_at=datetime.utcnow()
        )
        
        pending_notification = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Pending Notification",
            message="Pending message",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        failed_notification = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Failed Notification",
            message="Failed message",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.FAILED,
            created_at=datetime.utcnow()
        )
        
        db.add_all([sent_notification, pending_notification, failed_notification])
        db.commit()

        # Create access token
        token = create_access_token(subject=str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Test the endpoint
        response = client.get("/v1/notifications/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        
        # Check that all statuses are present
        statuses = [n["status"] for n in data]
        assert "sent" in statuses
        assert "pending" in statuses
        assert "failed" in statuses
