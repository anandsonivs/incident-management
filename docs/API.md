# API Documentation

## Overview

The Incident Management System provides a comprehensive REST API for managing incidents, escalations, notifications, and user management. All endpoints require authentication via JWT tokens.

## Authentication

### JWT Token Authentication
All API endpoints require authentication. Include your JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting a Token
```bash
# Login to get access token
curl -X POST "http://localhost:8000/v1/auth/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your-email@example.com&password=your-password"
```

## Base URL
```
http://localhost:8000/v1
```

## Endpoints

### Authentication

#### POST /auth/signup
Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "is_superuser": false,
  "team_id": 1,
  "role": "user"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "team_id": 1,
  "role": "user"
}
```

#### POST /auth/login/access-token
Authenticate and get access token.

**Request Body:**
```
username=user@example.com&password=securepassword
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

#### POST /auth/login/test-token
Validate current token.

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false
}
```

### User Management

#### GET /users/me
Get current user information.

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "team_id": 1,
  "role": "user"
}
```

#### PUT /users/me
Update current user information.

**Request Body:**
```json
{
  "full_name": "John Smith",
  "phone_number": "+1234567890"
}
```

#### GET /users/
List all users (admin only).

**Query Parameters:**
- `team_id` (optional): Filter by team ID
- `role` (optional): Filter by role
- `skip` (optional): Number of records to skip
- `limit` (optional): Maximum number of records to return

**Response:**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_superuser": false,
    "team_id": 1,
    "role": "user"
  }
]
```

### Team Management

#### GET /teams/
List all teams (admin only).

**Response:**
```json
[
  {
    "id": 1,
    "name": "Engineering",
    "description": "Engineering team",
    "created_at": "2025-08-28T10:00:00Z"
  }
]
```

#### POST /teams/
Create a new team (admin only).

**Request Body:**
```json
{
  "name": "Engineering",
  "description": "Engineering team"
}
```

#### GET /teams/{team_id}
Get team details (admin only).

**Response:**
```json
{
  "id": 1,
  "name": "Engineering",
  "description": "Engineering team",
  "created_at": "2025-08-28T10:00:00Z"
}
```

### Incident Management

#### GET /incidents/
List all incidents.

**Query Parameters:**
- `team_id` (optional): Filter by team ID
- `status` (optional): Filter by status
- `skip` (optional): Number of records to skip
- `limit` (optional): Maximum number of records to return

**Response:**
```json
[
  {
    "id": 1,
    "title": "Database Connection Issue",
    "description": "Unable to connect to database",
    "severity": "high",
    "service": "database",
    "status": "triggered",
    "team_id": 1,
    "created_at": "2025-08-28T10:00:00Z",
    "updated_at": "2025-08-28T10:00:00Z"
  }
]
```

#### POST /incidents/
Create a new incident.

**Request Body:**
```json
{
  "title": "Database Connection Issue",
  "description": "Unable to connect to database",
  "severity": "high",
  "service": "database",
  "team_id": 1
}
```

#### GET /incidents/{incident_id}
Get incident details.

**Response:**
```json
{
  "id": 1,
  "title": "Database Connection Issue",
  "description": "Unable to connect to database",
  "severity": "high",
  "service": "database",
  "status": "triggered",
  "team_id": 1,
  "created_at": "2025-08-28T10:00:00Z",
  "updated_at": "2025-08-28T10:00:00Z",
  "assignments": [],
  "comments": []
}
```

#### POST /incidents/{incident_id}/acknowledge
Acknowledge an incident.

**Response:**
```json
{
  "id": 1,
  "status": "acknowledged",
  "acknowledged_at": "2025-08-28T10:30:00Z"
}
```

#### POST /incidents/{incident_id}/resolve
Resolve an incident.

**Response:**
```json
{
  "id": 1,
  "status": "resolved",
  "resolved_at": "2025-08-28T11:00:00Z"
}
```

#### POST /incidents/{incident_id}/snooze
Snooze an incident.

**Query Parameters:**
- `hours` (required): Number of hours to snooze

**Response:**
```json
{
  "id": 1,
  "status": "snoozed",
  "snoozed_until": "2025-08-28T13:00:00Z"
}
```

### Escalation Management

#### GET /escalation/events/
Get all escalation events (sorted by created_at desc).

**Query Parameters:**
- `skip` (optional): Number of records to skip
- `limit` (optional): Maximum number of records to return

**Response:**
```json
[
  {
    "id": 1,
    "incident_id": 1,
    "policy_id": 1,
    "step": 1,
    "status": "triggered",
    "triggered_at": "2025-08-28T10:00:00Z",
    "created_at": "2025-08-28T10:00:00Z",
    "metadata": {},
    "incident": {
      "id": 1,
      "title": "Database Connection Issue",
      "service": "database",
      "severity": "high",
      "team": {
        "id": 1,
        "name": "Engineering",
        "description": "Engineering team"
      }
    },
    "policy": {
      "id": 1,
      "name": "High Priority Escalation",
      "description": "Escalation policy for high priority incidents"
    }
  }
]
```

#### GET /escalation/incidents/{incident_id}/escalation-events/
Get escalation events for a specific incident.

**Query Parameters:**
- `skip` (optional): Number of records to skip
- `limit` (optional): Maximum number of records to return

**Response:**
```json
[
  {
    "id": 1,
    "incident_id": 1,
    "policy_id": 1,
    "step": 1,
    "status": "triggered",
    "triggered_at": "2025-08-28T10:00:00Z",
    "created_at": "2025-08-28T10:00:00Z",
    "metadata": {},
    "incident": {
      "id": 1,
      "title": "Database Connection Issue",
      "service": "database",
      "severity": "high",
      "team": {
        "id": 1,
        "name": "Engineering",
        "description": "Engineering team"
      }
    },
    "policy": {
      "id": 1,
      "name": "High Priority Escalation",
      "description": "Escalation policy for high priority incidents"
    }
  }
]
```

#### POST /escalation/incidents/{incident_id}/escalate/
Manually trigger escalation for an incident.

**Requirements:**
- User must be assigned to the incident OR be a superuser

**Response:**
```json
{
  "id": 1,
  "title": "Database Connection Issue",
  "status": "triggered",
  "escalation_events": [
    {
      "id": 1,
      "step": 1,
      "status": "triggered",
      "triggered_at": "2025-08-28T10:00:00Z"
    }
  ]
}
```

#### GET /escalation/policies/
List all escalation policies (admin only).

**Response:**
```json
[
  {
    "id": 1,
    "name": "High Priority Escalation",
    "description": "Escalation policy for high priority incidents",
    "is_active": true,
    "steps": [
      {
        "delay": 5,
        "action": "notify",
        "target_roles": ["team_lead", "manager"]
      }
    ],
    "conditions": {
      "severity": ["high", "critical"],
      "team_id": 1
    }
  }
]
```

#### POST /escalation/policies/
Create a new escalation policy (admin only).

**Request Body:**
```json
{
  "name": "High Priority Escalation",
  "description": "Escalation policy for high priority incidents",
  "is_active": true,
  "steps": [
    {
      "delay": 5,
      "action": "notify",
      "target_roles": ["team_lead", "manager"]
    }
  ],
  "conditions": {
    "severity": ["high", "critical"],
    "team_id": 1
  }
}
```

### Notification Management

#### GET /notifications/
Get all notifications (sorted by created_at desc).

**Query Parameters:**
- `skip` (optional): Number of records to skip
- `limit` (optional): Maximum number of records to return

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "incident_id": 1,
    "recipient": "user@example.com",
    "title": "Incident Escalated",
    "message": "Incident 'Database Connection Issue' has been escalated",
    "channel": "email",
    "status": "sent",
    "created_at": "2025-08-28T10:00:00Z",
    "sent_at": "2025-08-28T10:01:00Z",
    "metadata": {
      "retry_count": 1,
      "delivery_method": "smtp"
    }
  }
]
```

#### GET /notifications/history
Get notification history.

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "incident_id": 1,
    "recipient": "user@example.com",
    "title": "Incident Escalated",
    "message": "Incident 'Database Connection Issue' has been escalated",
    "channel": "email",
    "status": "sent",
    "created_at": "2025-08-28T10:00:00Z",
    "sent_at": "2025-08-28T10:01:00Z"
  }
]
```

#### GET /notification-preferences/me
Get current user's notification preferences.

**Response:**
```json
{
  "email": {
    "enabled": true,
    "incident_updates": true,
    "escalations": true
  },
  "sms": {
    "enabled": false,
    "incident_updates": false,
    "escalations": true
  }
}
```

#### PUT /notification-preferences/me/{channel}
Update notification preference for a specific channel.

**Request Body:**
```json
{
  "enabled": true,
  "incident_updates": true,
  "escalations": true
}
```

### Health & System

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-28T10:00:00Z",
  "version": "1.0.0"
}
```

#### GET /
Root endpoint.

**Response:**
```json
{
  "message": "Incident Management System API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

## Error Responses

### Standard Error Format
All error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

### Example Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

#### 403 Forbidden
```json
{
  "detail": "Not enough permissions to access this resource"
}
```

#### 404 Not Found
```json
{
  "detail": "Incident not found"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Pagination

Many endpoints support pagination using `skip` and `limit` query parameters:

- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100, max: 1000)

### Example
```bash
GET /incidents/?skip=20&limit=10
```

## Filtering

Several endpoints support filtering using query parameters:

### Incidents
- `team_id`: Filter by team
- `status`: Filter by status (triggered, acknowledged, resolved, snoozed)
- `severity`: Filter by severity (low, medium, high, critical)

### Users
- `team_id`: Filter by team
- `role`: Filter by role (user, oncall_engineer, team_lead, manager, vp, cto, admin)

### Example
```bash
GET /incidents/?team_id=1&status=triggered&severity=high
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- **Authentication endpoints**: 5 requests per minute
- **Other endpoints**: 100 requests per minute

When rate limited, you'll receive a 429 Too Many Requests response.

## Webhooks

### POST /alerts/elastic
Webhook endpoint for receiving alerts from Elastic APM.

**Request Body:**
```json
{
  "alert_name": "High Error Rate",
  "severity": "high",
  "message": "Error rate exceeded threshold",
  "service": "web-api",
  "timestamp": "2025-08-28T10:00:00Z"
}
```

## SDK Examples

### Python
```python
import requests

# Base configuration
BASE_URL = "http://localhost:8000/v1"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get all incidents
response = requests.get(f"{BASE_URL}/incidents/", headers=headers)
incidents = response.json()

# Create new incident
incident_data = {
    "title": "New Incident",
    "description": "Description here",
    "severity": "high",
    "service": "web-api",
    "team_id": 1
}
response = requests.post(f"{BASE_URL}/incidents/", json=incident_data, headers=headers)
```

### JavaScript
```javascript
const BASE_URL = 'http://localhost:8000/v1';
const TOKEN = 'your-jwt-token';

const headers = {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json'
};

// Get all incidents
fetch(`${BASE_URL}/incidents/`, { headers })
    .then(response => response.json())
    .then(incidents => console.log(incidents));

// Create new incident
const incidentData = {
    title: 'New Incident',
    description: 'Description here',
    severity: 'high',
    service: 'web-api',
    team_id: 1
};

fetch(`${BASE_URL}/incidents/`, {
    method: 'POST',
    headers,
    body: JSON.stringify(incidentData)
})
.then(response => response.json())
.then(incident => console.log(incident));
```

### cURL
```bash
# Get all incidents
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/v1/incidents/

# Create new incident
curl -X POST \
     -H "Authorization: Bearer your-jwt-token" \
     -H "Content-Type: application/json" \
     -d '{"title":"New Incident","description":"Description","severity":"high","service":"web-api","team_id":1}' \
     http://localhost:8000/v1/incidents/
```

## Testing

The API includes comprehensive test coverage. Run the test suite:

```bash
# Run all tests
python run_enhanced_tests.py

# Run specific test categories
pytest tests/test_escalation_events_api.py -v
pytest tests/test_notifications_api.py -v
```

## Support

For API support:
1. Check the interactive documentation at `/docs`
2. Review the test examples in the test suite
3. Check the troubleshooting guide
4. Create an issue with detailed information

---

**API Version:** 1.0.0  
**Last Updated:** August 2025  
**Test Coverage:** 83.3% (15/18 tests passing)
