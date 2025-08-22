import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.orm import Session

from app.models.incident import Incident, IncidentStatus
from app.models.escalation import EscalationPolicy, EscalationEvent
from app.schemas.escalation import EscalationPolicyCreate
from app.services.escalation import EscalationService

@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    db.query = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db

@pytest.fixture
def test_incident():
    return Incident(
        id=1,
        title="Test Incident",
        status=IncidentStatus.TRIGGERED,
        severity="high",
        service="api",
        created_at=datetime.utcnow() - timedelta(minutes=30)
    )

@pytest.fixture
def test_policy():
    return EscalationPolicy(
        id=1,
        name="Test Policy",
        conditions={"severity": ["high"], "service": ["api"]},
        steps=[
            {
                "delay_minutes": 5,
                "actions": [
                    {"type": "notify", "target": "assignees", "message": "Test notification"}
                ]
            }
        ]
    )

@pytest.mark.asyncio
async def test_check_and_escalate_incident(mock_db, test_incident, test_policy):
    # Setup mocks
    mock_notification_service = AsyncMock()
    policy_crud = MagicMock()
    policy_crud.get_active_policies.return_value = [test_policy]
    
    # Create service instance
    service = EscalationService(mock_db, crud=policy_crud, notification_service=mock_notification_service)
    
    # Test
    await service.check_and_escalate_incident(test_incident)
    
    # Verify escalation event and notification
    assert mock_notification_service.send_notification.await_count >= 1

@pytest.mark.asyncio
async def test_escalation_conditions_not_met(mock_db, test_incident):
    # Create a policy that won't match the incident
    non_matching_policy = EscalationPolicy(
        id=2,
        name="Non-matching Policy",
        conditions={"severity": ["low"], "service": ["database"]},
        steps=[{"delay_minutes": 5, "actions": [{"type": "notify"}]}]
    )
    
    policy_crud = MagicMock()
    policy_crud.get_active_policies.return_value = [non_matching_policy]
    
    # Create service instance
    service = EscalationService(mock_db, crud=policy_crud, notification_service=AsyncMock())
    
    # Test
    await service.check_and_escalate_incident(test_incident)
    
    # Verify no notifications sent
    # Since notification service is a fresh AsyncMock, its send_notification should not be awaited
    # We check DB.add not called as a proxy (event not created)
    assert not mock_db.add.called

@pytest.mark.asyncio
async def test_escalation_with_multiple_steps(mock_db, test_incident, test_policy):
    # Add multiple steps to the test policy
    test_policy.steps = [
        {"delay_minutes": 5, "actions": [{"type": "notify", "message": "Step 1", "target": "team"}]},
        {"delay_minutes": 10, "actions": [{"type": "notify", "message": "Step 2", "target": "team"}]}
    ]
    
    policy_crud = MagicMock()
    policy_crud.get_active_policies.return_value = [test_policy]
    
    # Create service instance
    mock_notification = AsyncMock()
    service = EscalationService(mock_db, crud=policy_crud, notification_service=mock_notification)
    
    # Test
    await service.check_and_escalate_incident(test_incident)
    
    # Verify both steps were processed (at least two notifications)
    assert mock_notification.send_notification.await_count >= 2
