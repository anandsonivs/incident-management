import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.escalation import (
    EscalationPolicyBase,
    EscalationPolicyCreate,
    EscalationPolicyUpdate,
    EscalationPolicyInDBBase,
    EscalationPolicy,
    EscalationEventBase,
    EscalationEventCreate,
    EscalationEventInDBBase,
    EscalationEvent,
    EscalationEventStatus
)

def test_escalation_policy_base_validation():
    # Test valid policy with all fields
    valid_policy = {
        "name": "Test Policy",
        "description": "Test Description",
        "conditions": {"severity": ["high", "critical"], "service": ["api"]},
        "steps": [
            {
                "delay_minutes": 5,
                "actions": [
                    {"type": "notify", "target": "team", "message": "Test notification"}
                ]
            }
        ],
        "is_active": True
    }
    policy = EscalationPolicyBase(**valid_policy)
    assert policy.name == "Test Policy"
    assert policy.description == "Test Description"
    assert policy.conditions == {"severity": ["high", "critical"], "service": ["api"]}
    assert len(policy.steps) == 1
    assert policy.steps[0]["delay_minutes"] == 5
    assert len(policy.steps[0]["actions"]) == 1
    assert policy.is_active is True

def test_escalation_policy_invalid_conditions():
    # Test invalid conditions (not a dict)
    with pytest.raises(ValueError) as excinfo:
        EscalationPolicyBase(
            name="Invalid Policy",
            steps=[{"delay_minutes": 5, "actions": [{"type": "notify"}]}],
            conditions="not a dict"
        )
    error_message = str(excinfo.value)
    assert "validation error" in error_message.lower()
    assert "conditions" in error_message.lower()
    assert "value is not a valid dict" in error_message.lower()
    
    # Test empty conditions (should be allowed)
    policy = EscalationPolicyBase(
        name="Empty Conditions Policy",
        steps=[{"delay_minutes": 5, "actions": [{"type": "notify"}]}],
        conditions={}
    )
    assert policy.conditions == {}

def test_escalation_policy_step_validation():
    # Test missing delay_minutes
    with pytest.raises(ValueError, match="Each step must have a 'delay_minutes' field"):
        EscalationPolicyBase(
            name="Invalid Step Policy",
            steps=[{"actions": [{"type": "notify"}]}]
        )
    
    # Test missing actions
    with pytest.raises(ValueError, match="Each step must have an 'actions' list"):
        EscalationPolicyBase(
            name="Invalid Step Policy",
            steps=[{"delay_minutes": 5}]
        )
    
    # Test empty actions list - should raise an error about having at least one action
    with pytest.raises(ValueError, match="Each step must have at least one action"):
        EscalationPolicyBase(
            name="Empty Actions Policy",
            steps=[{"delay_minutes": 5, "actions": []}]
        )
    
    # Test invalid action (missing type)
    with pytest.raises(ValueError, match="Each action must have a 'type' field"):
        EscalationPolicyBase(
            name="Invalid Action Policy",
            steps=[{"delay_minutes": 5, "actions": [{"target": "team"}]}]
        )
    
    # Test valid steps with multiple actions
    valid_steps = [
        {
            "delay_minutes": 5,
            "actions": [
                {"type": "notify", "target": "team"},
                {"type": "assign", "target": "escalation_team"}
            ]
        },
        {
            "delay_minutes": 15,
            "actions": [
                {"type": "notify", "target": "managers"}
            ]
        }
    ]
    policy = EscalationPolicyBase(
        name="Multi-Step Policy",
        steps=valid_steps
    )
    assert len(policy.steps) == 2
    assert policy.steps[0]["delay_minutes"] == 5
    assert len(policy.steps[0]["actions"]) == 2
    assert policy.steps[1]["delay_minutes"] == 15
    assert len(policy.steps[1]["actions"]) == 1

def test_escalation_policy_action_validation():
    # Test various action types with different parameters
    valid_actions = [
        {"type": "notify", "target": "team"},
        {"type": "notify", "target": "team", "message": "Custom message"},
        {"type": "assign", "target": "user@example.com"},
        {"type": "assign", "target": "team:oncall"},
        {"type": "run_playbook", "playbook_id": "incident_response_v1"},
    ]
    
    policy = EscalationPolicyBase(
        name="Action Validation Policy",
        steps=[{"delay_minutes": 5, "actions": valid_actions}]
    )
    assert len(policy.steps[0]["actions"]) == 5
    
    # Test invalid action type
    with pytest.raises(ValueError, match="Each action must have a 'type' field"):
        EscalationPolicyBase(
            name="Invalid Action Policy",
            steps=[{"delay_minutes": 5, "actions": [{"target": "team"}]}]
        )
    
    # Test action with extra fields (should be allowed)
    policy = EscalationPolicyBase(
        name="Extra Fields Policy",
        steps=[{
            "delay_minutes": 5,
            "actions": [{"type": "notify", "target": "team", "extra": "data"}]
        }]
    )
    assert policy.steps[0]["actions"][0]["extra"] == "data"

def test_escalation_policy_create():
    # Test create schema with all fields
    policy_data = {
        "name": "Create Policy",
        "description": "Test creation",
        "conditions": {"severity": ["high"], "service": ["api"]},
        "steps": [{"delay_minutes": 5, "actions": [{"type": "notify"}]}],
        "is_active": True
    }
    policy = EscalationPolicyCreate(**policy_data)
    assert policy.name == "Create Policy"
    assert policy.description == "Test creation"
    assert policy.conditions == {"severity": ["high"], "service": ["api"]}
    assert len(policy.steps) == 1
    assert policy.is_active is True
    
    # Test create with minimal fields
    minimal_data = {
        "name": "Minimal Policy",
        "steps": [{"delay_minutes": 5, "actions": [{"type": "notify"}]}]
    }
    policy = EscalationPolicyCreate(**minimal_data)
    assert policy.name == "Minimal Policy"
    assert policy.description is None
    assert policy.conditions == {}
    assert policy.is_active is True

def test_escalation_policy_update():
    # Test update with all fields
    policy_data = {
        "name": "Update Policy",
        "description": "Updated description",
        "is_active": False,
        "conditions": {"severity": ["low"], "service": ["api"]},
        "steps": [{"delay_minutes": 10, "actions": [{"type": "assign"}]}]
    }
    policy = EscalationPolicyUpdate(**policy_data)
    assert policy.name == "Update Policy"
    assert policy.description == "Updated description"
    assert policy.is_active is False
    assert policy.conditions == {"severity": ["low"], "service": ["api"]}
    assert len(policy.steps) == 1
    
    # Test partial update (all fields optional)
    partial_data = {"name": "Partial Update"}
    policy = EscalationPolicyUpdate(**partial_data)
    assert policy.name == "Partial Update"
    assert policy.description is None
    assert policy.conditions == {}
    assert policy.steps == []
    assert policy.is_active is None

def test_escalation_policy_db_models():
    # Test DB base model
    db_policy = EscalationPolicyInDBBase(
        id=1,
        name="DB Policy",
        steps=[{"delay_minutes": 5, "actions": [{"type": "notify"}]}],
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 2, 12, 0, 0)
    )
    assert db_policy.id == 1
    assert db_policy.name == "DB Policy"
    assert db_policy.created_at == datetime(2023, 1, 1, 12, 0, 0)
    
    # Test full model
    policy_data = db_policy.dict()
    policy_data['description'] = "DB Test Policy"
    policy = EscalationPolicy(**policy_data)
    assert policy.description == "DB Test Policy"

def test_escalation_event_models():
    # Test base event model
    event = EscalationEventBase(
        policy_id=1,
        incident_id=1,
        step=0,
        status=EscalationEventStatus.PENDING,
        metadata_={"test": "data"}
    )
    assert event.policy_id == 1
    assert event.step == 0
    assert event.status == EscalationEventStatus.PENDING
    assert event.metadata == {"test": "data"}
    
    # Test create model
    create_event = EscalationEventCreate(
        **event.dict()
    )
    assert create_event.incident_id == 1
    
    # Test DB model
    db_event = EscalationEventInDBBase(
        **create_event.dict(),
        id=1,
        triggered_at=datetime(2023, 1, 1, 12, 0, 0),
        completed_at=None
    )
    assert db_event.id == 1
    assert db_event.triggered_at == datetime(2023, 1, 1, 12, 0, 0)
    assert db_event.completed_at is None
    
    # Test full model
    full_event = EscalationEvent(
        **db_event.dict()
    )
    assert full_event.id == 1
    assert full_event.status == EscalationEventStatus.PENDING
