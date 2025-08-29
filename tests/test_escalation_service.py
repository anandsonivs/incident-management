import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.orm import Session

from app.models.incident import Incident, IncidentStatus
from app.models.escalation import EscalationPolicy
from app.models.team import Team
from app.models.user import User, UserRole
from app.models.escalation import EscalationEvent
from app.schemas.escalation import EscalationPolicyCreate
from app.services.escalation import EscalationService
from app import crud

@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    db.query = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db

@pytest.fixture
def test_team():
    return Team(
        id=1,
        name="Test Team",
        description="Test team for escalation tests",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def test_team_lead(test_team):
    return User(
        id=1,
        email="teamlead@example.com",
        full_name="Team Lead",
        role=UserRole.TEAM_LEAD,
        team_id=test_team.id,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def test_manager(test_team):
    return User(
        id=2,
        email="manager@example.com",
        full_name="Manager",
        role=UserRole.MANAGER,
        team_id=test_team.id,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def test_incident(test_team):
    from datetime import timezone
    return Incident(
        id=1,
        title="Test Incident",
        status=IncidentStatus.TRIGGERED,
        severity="high",
        service="api",
        team_id=test_team.id,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=30)
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
                    {"type": "notify", "target": "team_lead", "message": "Test notification"}
                ]
            }
        ]
    )

@pytest.mark.asyncio
async def test_check_and_escalate_incident(mock_db, test_incident, test_policy, test_team_lead):
    # Setup mocks
    mock_notification_service = AsyncMock()
    policy_crud = MagicMock()
    policy_crud.get_active_policies.return_value = [test_policy]
    
    # Mock global crud.user
    original_user_crud = crud.user
    mock_user_crud = MagicMock()
    mock_user_crud.get_by_role_and_team.return_value = [test_team_lead]
    crud.user = mock_user_crud
    
    try:
        # Create service instance
        service = EscalationService(mock_db, crud=policy_crud, notification_service=mock_notification_service)
        
        # Test
        await service.check_and_escalate_incident(test_incident)
        
        # Verify escalation event and notification
        assert mock_notification_service.send_notification.await_count >= 1
    finally:
        # Restore original crud.user
        crud.user = original_user_crud

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
async def test_escalation_with_multiple_steps(mock_db, test_incident, test_policy, test_team_lead, test_manager):
    # Add multiple steps to the test policy
    test_policy.steps = [
        {"delay_minutes": 5, "actions": [{"type": "notify", "message": "Step 1", "target": "team_lead"}]},
        {"delay_minutes": 10, "actions": [{"type": "notify", "message": "Step 2", "target": "manager"}]}
    ]
    
    policy_crud = MagicMock()
    policy_crud.get_active_policies.return_value = [test_policy]
    
    # Mock global crud.user
    original_user_crud = crud.user
    mock_user_crud = MagicMock()
    
    def mock_get_by_role_and_team(db, role, team_id):
        return {
            "team_lead": [test_team_lead],
            "manager": [test_manager]
        }.get(role, [])
    
    mock_user_crud.get_by_role_and_team.side_effect = mock_get_by_role_and_team
    crud.user = mock_user_crud
    
    try:
        # Create service instance
        mock_notification = AsyncMock()
        service = EscalationService(mock_db, crud=policy_crud, notification_service=mock_notification)
        
        # Test
        await service.check_and_escalate_incident(test_incident)
        
        # Verify both steps were processed (at least two notifications)
        assert mock_notification.send_notification.await_count >= 2
    finally:
        # Restore original crud.user
        crud.user = original_user_crud
