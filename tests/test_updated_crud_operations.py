"""
Tests for Updated CRUD Operations.

This module tests the updated CRUD operations including:
- Updated escalation event CRUD operations
- Updated notification CRUD operations
- Sorting and filtering improvements
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.incident import Incident, IncidentStatus
from app.models.user import User, UserRole
from app.models.escalation import EscalationPolicy, EscalationEvent
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.team import Team
from app.crud.crud_escalation import CRUDEscalationEvent
from app.crud.crud_notification import get_all_notifications


class TestUpdatedEscalationEventCRUD:
    """Test updated escalation event CRUD operations."""

    def test_get_by_incident_sorted_by_created_at_desc(self, db: Session, test_user: User):
        """Test that get_by_incident returns events sorted by created_at desc."""
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
        event3 = EscalationEvent(
            incident_id=incident.id,
            recipient="test@example.com",
            policy_id=policy.id,
            step=3,
            status="triggered",
            triggered_at=datetime.utcnow() - timedelta(hours=2),
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        db.add_all([event1, event2, event3])
        db.commit()

        # Test the CRUD operation
        from app.crud.crud_escalation import escalation_event
        events = escalation_event.get_by_incident(db, incident_id=incident.id)
        
        # Should be sorted by created_at desc (newest first)
        assert len(events) == 3
        assert events[0].id == event2.id  # Newest (1 hour ago)
        assert events[1].id == event3.id  # Middle (2 hours ago)
        assert events[2].id == event1.id  # Oldest (3 hours ago)

    def test_get_all_events_sorted_by_created_at_desc(self, db: Session, test_user: User):
        """Test that get_all_events returns events sorted by created_at desc."""
        # Create test data
        team = Team(name="Test Team", description="Test team")
        db.add(team)
        db.commit()
        db.refresh(team)

        incident1 = Incident(
            title="Test Incident 1",
            description="Test description 1",
            severity="high",
            service="test-service-1",
            team_id=team.id
        )
        incident2 = Incident(
            title="Test Incident 2",
            description="Test description 2",
            severity="medium",
            service="test-service-2",
            team_id=team.id
        )
        db.add_all([incident1, incident2])
        db.commit()
        db.refresh(incident1)
        db.refresh(incident2)

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
            incident_id=incident1.id,
            policy_id=policy.id,
            step=1,
            status="triggered",
            triggered_at=datetime.utcnow() - timedelta(hours=3),
            created_at=datetime.utcnow() - timedelta(hours=3)
        )
        event2 = EscalationEvent(
            incident_id=incident2.id,
            policy_id=policy.id,
            step=1,
            status="completed",
            triggered_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow() - timedelta(minutes=30),
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        event3 = EscalationEvent(
            incident_id=incident1.id,
            policy_id=policy.id,
            step=2,
            status="triggered",
            triggered_at=datetime.utcnow() - timedelta(hours=2),
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        db.add_all([event1, event2, event3])
        db.commit()

        # Test the CRUD operation
        from app.crud.crud_escalation import escalation_event
        crud = escalation_event
        events = crud.get_all_events(db)
        
        # Should be sorted by created_at desc (newest first)
        assert len(events) == 3
        assert events[0].id == event2.id  # Newest (1 hour ago)
        assert events[1].id == event3.id  # Middle (2 hours ago)
        assert events[2].id == event1.id  # Oldest (3 hours ago)

    def test_get_all_events_with_relationships(self, db: Session, test_user: User):
        """Test that get_all_events includes incident and policy relationships."""
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

        # Test the CRUD operation
        from app.crud.crud_escalation import escalation_event
        crud = escalation_event
        events = crud.get_all_events(db)
        
        assert len(events) == 1
        event_result = events[0]
        
        # Check that relationships are loaded
        assert event_result.incident is not None
        assert event_result.incident.id == incident.id
        assert event_result.incident.title == incident.title
        assert event_result.incident.team is not None
        assert event_result.incident.team.id == team.id
        
        assert event_result.policy is not None
        assert event_result.policy.id == policy.id
        assert event_result.policy.name == policy.name

    def test_get_all_events_pagination(self, db: Session, test_user: User):
        """Test pagination for get_all_events."""
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
            recipient="test@example.com",
                policy_id=policy.id,
                step=i + 1,
                status="triggered",
                triggered_at=datetime.utcnow() - timedelta(hours=i),
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            events.append(event)
        
        db.add_all(events)
        db.commit()

        # Test pagination
        from app.crud.crud_escalation import escalation_event
        crud = escalation_event
        
        # First page
        events_page1 = crud.get_all_events(db, skip=0, limit=10)
        assert len(events_page1) == 10
        
        # Second page
        events_page2 = crud.get_all_events(db, skip=10, limit=10)
        assert len(events_page2) == 5  # Remaining 5 events


class TestUpdatedNotificationCRUD:
    """Test updated notification CRUD operations."""

    def test_get_all_notifications_sorted_by_created_at_desc(self, db: Session, test_user: User):
        """Test that get_all_notifications returns notifications sorted by created_at desc."""
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
        notification3 = Notification(
            user_id=test_user.id,
            incident_id=incident.id,
            recipient="test@example.com",
            title="Test Notification 3",
            message="Test message 3",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.PENDING,
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        db.add_all([notification1, notification2, notification3])
        db.commit()

        # Test the CRUD operation
        notifications = get_all_notifications(db)
        
        # Should be sorted by created_at desc (newest first)
        assert len(notifications) == 3
        assert notifications[0].id == notification2.id  # Newest (1 hour ago)
        assert notifications[1].id == notification3.id  # Middle (2 hours ago)
        assert notifications[2].id == notification1.id  # Oldest (3 hours ago)

    def test_get_all_notifications_pagination(self, db: Session, test_user: User):
        """Test pagination for get_all_notifications."""
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

        # Test pagination
        # First page
        notifications_page1 = get_all_notifications(db, skip=0, limit=10)
        assert len(notifications_page1) == 10
        
        # Second page
        notifications_page2 = get_all_notifications(db, skip=10, limit=10)
        assert len(notifications_page2) == 5  # Remaining 5 notifications

    def test_get_all_notifications_with_metadata(self, db: Session, test_user: User):
        """Test get_all_notifications with metadata."""
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

        # Test the CRUD operation
        notifications = get_all_notifications(db)
        
        assert len(notifications) == 1
        notification_result = notifications[0]
        assert notification_result.metadata == metadata
