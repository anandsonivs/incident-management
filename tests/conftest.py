import os
import sys

# Ensure project root is on sys.path for 'app' imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.base import Base
from app.main import app
from app.models.incident import Incident, IncidentStatus
from app.models.user import User
from app.models.escalation import EscalationPolicy, EscalationEvent
from app.db.session import get_db

# Set test environment
os.environ["ENV"] = "test"
os.environ["TESTING"] = "True"

# Create test database
# Get database URL from settings
settings = get_settings()
SQLALCHEMY_DATABASE_URL = getattr(settings, "SQLALCHEMY_DATABASE_URL", "sqlite:///:memory:")
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = Session(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup test database with all tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    """Create a clean database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    """Create a test client that uses the test database."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(db):
    """Create an async test client that uses the test database."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def mock_db():
    """Create a mock database session for unit tests."""
    db = MagicMock(spec=Session)
    
    # Setup default query behavior
    db.query = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.rollback = MagicMock()
    db.execute = MagicMock()
    db.get = MagicMock()
    db.merge = MagicMock(side_effect=lambda x: x)
    db.begin = MagicMock()
    db.begin_nested = MagicMock()
    db.close = MagicMock()
    
    # Setup query chain
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None
    filter_mock.all.return_value = []
    filter_mock.offset.return_value = filter_mock
    filter_mock.limit.return_value = filter_mock
    filter_mock.order_by.return_value = filter_mock
    
    db.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    
    return db

@pytest.fixture
def test_user():
    """Create a test user."""
    return User(
        id=1,
        email="test@example.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # 'secret'
        full_name="Test User",
        is_active=True,
        is_superuser=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def test_token(test_user):
    """Create a valid JWT token for the test user."""
    return create_access_token(
        subject=str(test_user.id)
    )

@pytest.fixture
def auth_headers(test_token):
    """Return authorization headers with a valid JWT token."""
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
def test_incident(test_user):
    """Create a test incident."""
    return Incident(
        id=1,
        title="Test Incident",
        description="Test Description",
        status=IncidentStatus.TRIGGERED,
        severity="high",
        service="api",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        resolved_at=None,
        acknowledged_at=None
    )

@pytest.fixture
def test_incident_list(test_user):
    """Create a list of test incidents."""
    now = datetime.utcnow()
    return [
        Incident(
            id=i,
            title=f"Test Incident {i}",
            description=f"Test Description {i}",
            status=IncidentStatus.TRIGGERED,
            severity=severity,
            service=service,
            created_at=now - timedelta(days=i),
            updated_at=now - timedelta(days=i),
            resolved_at=None,
            acknowledged_at=None
        )
        for i, (severity, service) in enumerate([
            ("high", "api"),
            ("medium", "database"),
            ("low", "frontend"),
            ("critical", "backend")
        ], 1)
    ]

@pytest.fixture
def test_escalation_policy():
    """Create a test escalation policy."""
    return EscalationPolicy(
        id=1,
        name="Test Policy",
        description="Test Description",
        conditions={"severity": ["high"], "service": ["api"]},
        steps=[
            {
                "delay_minutes": 5,
                "actions": [
                    {"type": "notify", "recipients": ["assignees"], "message": "Test notification"}
                ]
            },
            {
                "delay_minutes": 15,
                "actions": [
                    {"type": "notify", "recipients": ["managers"], "message": "Escalation: Incident not resolved"},
                    {"type": "assign", "assignee_id": 2}
                ]
            },
            {
                "delay_minutes": 30,
                "actions": [
                    {"type": "notify", "recipients": ["executives"], "message": "Critical: Immediate attention required"}
                ]
            }
        ],
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def test_escalation_policy_list():
    """Create a list of test escalation policies."""
    now = datetime.utcnow()
    return [
        EscalationPolicy(
            id=i,
            name=f"Test Policy {i}",
            description=f"Test Description {i}",
            conditions={"severity": [severity], "service": [service]},
            steps=[
                {
                    "delay_minutes": 5 * i,
                    "actions": [{"type": "notify", "recipients": [target], "message": f"Test notification {i}"}]
                }
            ],
            is_active=is_active,
            created_at=now - timedelta(days=i),
            updated_at=now - timedelta(days=i)
        )
        for i, (severity, service, target, is_active) in enumerate([
            ("high", "api", "team", True),
            ("critical", "database", "managers", True),
            ("medium", "frontend", "developers", False),
            ("low", "backend", "support", True)
        ], 1)
    ]

@pytest.fixture
def test_escalation_event(test_incident, test_escalation_policy):
    """Create a test escalation event."""
    return EscalationEvent(
        id=1,
        incident_id=test_incident.id,
        policy_id=test_escalation_policy.id,
        step=0,
        status="pending",
        triggered_at=datetime.utcnow(),
        completed_at=None,
        metadata={"test": "data"}
    )

@pytest.fixture
def test_escalation_event_list(test_incident, test_escalation_policy):
    """Create a list of test escalation events."""
    now = datetime.utcnow()
    return [
        EscalationEvent(
            id=i,
            incident_id=test_incident.id,
            policy_id=test_escalation_policy.id,
            step=step,
            status=status,
            triggered_at=now - timedelta(minutes=30 * i),
            completed_at=now - timedelta(minutes=15 * i) if status == "completed" else None,
            metadata={"step": step, "status": status, "test": f"data_{i}"}
        )
        for i, (step, status) in enumerate([
            (0, "completed"),
            (1, "in_progress"),
            (2, "pending")
        ], 1)
    ]

# Mock services
@pytest.fixture
def mock_notification_service():
    """Create a mock notification service."""
    with patch('app.services.notification.NotificationService') as mock:
        mock.return_value = AsyncMock()
        yield mock.return_value

@pytest.fixture
def mock_escalation_service():
    """Create a mock escalation service."""
    with patch('app.services.escalation.EscalationService') as mock:
        mock.return_value = AsyncMock()
        yield mock.return_value

# Test client with authentication
@pytest.fixture
def authenticated_client(client, test_user, test_token):
    """Create an authenticated test client."""
    client.headers.update({"Authorization": f"Bearer {test_token}"})
    return client
