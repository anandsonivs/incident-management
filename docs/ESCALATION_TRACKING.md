# Escalation Tracking System

This document explains how the escalation system prevents duplicate notifications and ensures each escalation step only happens once per user.

## Overview

The escalation system has two levels of tracking to prevent spam and ensure proper escalation flow:

1. **Step-level tracking**: Prevents the same escalation step from being processed multiple times
2. **User-level tracking**: Prevents the same user from being notified multiple times for the same step

## How It Works

### Step-Level Tracking

The system tracks which escalation steps have already been processed for each incident and policy combination:

```python
def get_processed_escalation_steps(self, incident_id: int, policy_id: int) -> set:
    """Get the escalation steps that have already been processed for an incident."""
    events = self.db.query(EscalationEvent).filter(
        EscalationEvent.incident_id == incident_id,
        EscalationEvent.policy_id == policy_id
    ).all()
    
    return {event.step for event in events}
```

**Example**: If step 0 (10-minute escalation) has already been processed for incident 96, policy 7, it won't be processed again.

### User-Level Tracking

The system tracks which specific users have already been notified for each step:

```python
def get_notified_users_for_step(self, incident_id: int, policy_id: int, step: int) -> Set[int]:
    """Get the user IDs that have already been notified for a specific step."""
    events = self.db.query(EscalationEvent).filter(
        EscalationEvent.incident_id == incident_id,
        EscalationEvent.policy_id == policy_id,
        EscalationEvent.step == step
    ).all()
    
    notified_users = set()
    for event in events:
        if event.event_metadata and "target_users" in event.event_metadata:
            for user_info in event.event_metadata["target_users"]:
                if isinstance(user_info, dict) and "id" in user_info:
                    notified_users.add(user_info["id"])
    
    return notified_users
```

**Example**: If user ID 40 (Platform Team Lead) has already been notified for step 0 of incident 96, they won't receive another notification for that step.

## Escalation Flow

### 1. Initial Incident Creation
- Incident is created and auto-assigned to oncall engineer
- Initial notification is sent to the assigned oncall engineer

### 2. Escalation Processing (Every 5 minutes)
The escalation processor runs and:

1. **Finds active incidents** that need escalation
2. **Matches policies** based on severity, team, and service
3. **Checks step timing** - only processes steps that are due based on incident age
4. **Checks step processing** - skips steps that have already been processed
5. **Checks user notifications** - only notifies users who haven't been notified for this step
6. **Records events** - creates escalation events with detailed metadata

### 3. Example Escalation Timeline

For a critical incident with a 2-step escalation policy:

```
Time 0:00 - Incident created, assigned to oncall engineer
Time 0:10 - Step 0 due: Notify team lead (only if not already notified)
Time 0:40 - Step 1 due: Notify manager (only if not already notified)
Time 1:10 - Step 0 would be due again, but skipped (already processed)
Time 1:40 - Step 1 would be due again, but skipped (already processed)
```

## Database Schema

### EscalationEvent Table

```sql
CREATE TABLE escalation_events (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id),
    policy_id INTEGER REFERENCES escalation_policies(id),
    step INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    event_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Event Metadata Structure

```json
{
    "policy_name": "Platform Team Escalation",
    "policy_description": "Escalation policy for platform team incidents",
    "step": {
        "delay_minutes": 10,
        "actions": [
            {
                "type": "notify",
                "target": "team_lead",
                "message": "Oncall engineer has not responded to incident. Escalating to team lead."
            }
        ]
    },
    "severity": "critical",
    "service": "api-gateway",
    "incident_age_minutes": 15,
    "delay_minutes": 10,
    "triggered_by": "system",
    "triggered_for": ["team_lead"],
    "target_users": [
        {
            "id": 40,
            "name": "Platform Team Lead",
            "email": "platform.lead@company.com",
            "role": "responder"
        }
    ],
    "new_notifications": 1,
    "already_notified_users": []
}
```

## Prevention Mechanisms

### 1. Duplicate Step Processing
- **Problem**: Same escalation step runs multiple times
- **Solution**: Track processed steps in `EscalationEvent` table
- **Result**: Each step only processes once per incident/policy combination

### 2. Duplicate User Notifications
- **Problem**: Same user gets notified multiple times for the same step
- **Solution**: Track notified users in event metadata
- **Result**: Each user only gets notified once per step

### 3. Spam Prevention
- **Problem**: Users receive excessive notifications
- **Solution**: Both step and user-level tracking
- **Result**: Clean, predictable escalation flow

## Testing the System

### Manual Testing

```bash
# Test escalation tracking logic
python test_escalation_tracking.py

# Run escalation processor manually
./scripts/run_escalation_processor.sh

# Check escalation events
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/v1/escalation/incidents/96/escalation-events/"
```

### Verification Commands

```bash
# Check current escalation status
./scripts/monitor_escalation.sh

# View escalation logs
tail -f logs/escalation_processor.log

# Check database directly
python -c "
from app.db.session import SessionLocal
from app.models.escalation import EscalationEvent
db = SessionLocal()
events = db.query(EscalationEvent).filter(EscalationEvent.incident_id == 96).all()
for event in events:
    print(f'Event {event.id}: Step {event.step}, Users: {event.event_metadata.get(\"target_users\", []) if event.event_metadata else []}')
db.close()
"
```

## Configuration

### Escalation Policy Example

```json
{
    "name": "Platform Team Escalation",
    "description": "Escalation policy for platform team incidents",
    "conditions": {
        "severity": ["high", "critical"],
        "team_id": [1]
    },
    "steps": [
        {
            "delay_minutes": 10,
            "actions": [
                {
                    "type": "notify",
                    "target": "team_lead",
                    "message": "Oncall engineer has not responded to incident. Escalating to team lead."
                }
            ]
        },
        {
            "delay_minutes": 30,
            "actions": [
                {
                    "type": "notify",
                    "target": "manager",
                    "message": "Incident still unacknowledged. Escalating to manager."
                }
            ]
        }
    ]
}
```

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Escalation Events Created**: Number of escalation events per time period
2. **Notifications Sent**: Number of actual notifications sent (vs. skipped)
3. **Duplicate Prevention**: Number of notifications skipped due to tracking
4. **Escalation Success Rate**: Percentage of escalations that result in incident acknowledgment

### Log Analysis

```bash
# Count escalation events
grep "Completed escalation event" logs/escalation_processor.log | wc -l

# Count new notifications
grep "new notifications" logs/escalation_processor.log

# Count skipped notifications
grep "Skipping notification" logs/escalation_processor.log | wc -l
```

## Troubleshooting

### Common Issues

1. **No escalations happening**
   - Check if incidents have matching policies
   - Verify incident age vs. escalation delays
   - Check if steps have already been processed

2. **Duplicate notifications**
   - Verify user-level tracking is working
   - Check event metadata for target_users
   - Ensure escalation events are being created properly

3. **Escalations not stopping**
   - Check if incident status is being updated
   - Verify escalation conditions are still met
   - Check if all steps have been processed

### Debug Commands

```bash
# Check escalation processor status
./scripts/monitor_escalation.sh

# Test escalation logic
python test_escalation_tracking.py

# View recent escalation events
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/v1/escalation/events/" | jq

# Check specific incident escalations
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/v1/escalation/incidents/96/escalation-events/" | jq
```

## Best Practices

1. **Test escalation policies** before deploying to production
2. **Monitor escalation logs** regularly to ensure proper functioning
3. **Review escalation timing** to ensure appropriate delays
4. **Update escalation targets** when team structure changes
5. **Document escalation policies** clearly for all stakeholders

## Summary

The escalation tracking system ensures:

- ✅ **No duplicate step processing** - Each escalation step only runs once
- ✅ **No duplicate user notifications** - Each user only gets notified once per step
- ✅ **Proper escalation flow** - Escalations happen at the right time to the right people
- ✅ **Audit trail** - Complete history of all escalation events and notifications
- ✅ **Configurable policies** - Flexible escalation rules based on incident characteristics

This creates a reliable, predictable escalation system that ensures incidents get proper attention without overwhelming responders with duplicate notifications.
