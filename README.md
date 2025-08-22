# Incident Management System

A FastAPI-based microservice for managing incidents, escalations, and notifications with a comprehensive team and role-based management system. Built with a focus on reliability, maintainability, and enterprise-grade features.

## ✨ Features

- **Team & Role Management** 🆕
  - Comprehensive team-based incident management
  - 7 distinct user roles: `user`, `oncall_engineer`, `team_lead`, `manager`, `vp`, `cto`, `admin`
  - Team-based escalation targeting (escalate to team leads, managers of same team)
  - User filtering by team and role
  - Team assignment for incidents and users

- **Incident Management**
  - Create, update, and track incidents with full audit trail
  - Team-based incident assignment and filtering
  - Rich incident metadata and status tracking
  - Support for incident assignments and comments
  - Timeline tracking for all incident activities
  - Incident collaboration features

- **Advanced Escalation System**
  - Define multi-step escalation policies with team-based targeting
  - Team-aware conditional escalation rules
  - Role-based escalation targeting (notify team leads, managers)
  - Actionable steps at each escalation level
  - Background worker for automatic escalation processing
  - Escalation event tracking and audit trail

- **User & Access Control**
  - JWT-based authentication with secure token handling
  - Comprehensive role-based access control with 7 user roles
  - Team-based user management API
  - Password recovery system
  - User filtering and search capabilities

- **Notification System**
  - Multi-channel notifications (Email, SMS, etc.)
  - Configurable notification preferences per user
  - Delivery status tracking
  - Webhook support for external integrations
  - Team-based notification routing

- **Developer Friendly**
  - RESTful API with OpenAPI documentation
  - **100% API endpoint coverage** with comprehensive test suite (60 E2E tests)
  - Containerized deployment (Docker)
  - CI/CD ready
  - Database migrations with Alembic
  - Comprehensive testing framework

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 13+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/incident-management.git
   cd incident-management
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   Copy the example environment file and update it:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   alembic upgrade head
   ```

6. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API documentation will be available at http://localhost:8000/docs

## 🏗️ Project Structure

```
.
├── app/                    # Application code
│   ├── api/               # API endpoints
│   │   └── v1/            # API version 1
│   │       ├── endpoints/ # Individual endpoint modules
│   │       └── api.py     # Main API router
│   ├── core/              # Core functionality
│   │   ├── config.py      # Application configuration
│   │   └── security.py    # Authentication and security
│   ├── crud/              # Database operations
│   ├── db/                # Database configuration
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic models
│   ├── services/          # Business logic
│   └── worker/            # Background worker
├── tests/                 # Test suite
│   ├── conftest.py        # Test fixtures
│   ├── utils.py           # General test utilities
│   ├── user_utils.py      # User-specific test utilities
│   ├── team_utils.py      # Team-specific test utilities
│   ├── test_escalation_api.py
│   ├── test_escalation_schemas.py
│   ├── test_team_api.py
│   ├── test_team_incidents.py
│   ├── test_team_escalation.py
│   ├── test_user_roles.py
│   └── test_escalation_service.py
├── alembic/              # Database migrations
├── run_e2e_tests.py      # Comprehensive E2E test suite
└── docs/                 # Documentation
```

## 🔧 Configuration

Key environment variables (see `.env.example` for all options):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/incident_management

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO

# Notification Services (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Twilio (for SMS/WhatsApp notifications, optional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
```

## Database Setup

1. Create a PostgreSQL database:
   ```bash
   createdb incident_management
   ```

2. Run database migrations:
   ```bash
   alembic upgrade head
   ```

## Running the Application

1. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🧪 Testing

### Comprehensive Test Suite

The project includes a comprehensive end-to-end test suite that covers **100% of all API endpoints**:

```bash
# Run the complete E2E test suite
python run_e2e_tests.py
```

**Expected Output:**
```
📊 COMPREHENSIVE END-TO-END TEST SUMMARY
============================================================
Total Tests: 60
✅ Passed: 60
❌ Failed: 0
⏱️  Duration: ~1.47 seconds

📈 Success Rate: 100.0%
🎉 All tests passed! 100% API coverage achieved!
```

### Test Coverage

The test suite covers all endpoints including the new team and role system:
- ✅ **Health Endpoints** (2/2) - Basic health checks
- ✅ **Authentication** (5/5) - Signup, Login, Token Validation, Password Recovery
- ✅ **User Management** (7/7) - CRUD operations, admin functions, role filtering
- ✅ **Team Management** (6/6) - Team CRUD, duplicate validation, error handling 🆕
- ✅ **User Roles & Teams** (6/6) - Role assignment, team filtering, role validation 🆕
- ✅ **Team-Based Incidents** (5/5) - Team assignment, filtering, collaboration 🆕
- ✅ **Team Escalation Policies** (5/5) - Team-based escalation rules 🆕
- ✅ **Incident Management** (10/10) - Full lifecycle, assignments, comments
- ✅ **Webhook Integration** (1/1) - Elastic APM webhook
- ✅ **Notification Preferences** (4/4) - User and admin management
- ✅ **Escalation System** (7/7) - Policies, events, triggers
- ✅ **Administrative Functions** (2/2) - Admin-only operations

### Unit Tests

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=app --cov-report=html
```

## API Endpoints

### Authentication
- `POST /v1/auth/signup` - Create a new user
- `POST /v1/auth/login/access-token` - Get access token
- `POST /v1/auth/login/test-token` - Validate token
- `POST /v1/auth/password-recovery/{email}` - Request password recovery
- `POST /v1/auth/reset-password/` - Reset password with token

### Teams 🆕
- `GET /v1/teams/` - List all teams (admin only)
- `POST /v1/teams/` - Create a new team (admin only)
- `GET /v1/teams/{team_id}` - Get team details (admin only)
- `PUT /v1/teams/{team_id}` - Update a team (admin only)
- `DELETE /v1/teams/{team_id}` - Delete a team (admin only)

### Users (Enhanced with Team & Role Support)
- `GET /v1/users/me` - Get current user
- `PUT /v1/users/me` - Update current user
- `GET /v1/users/` - List all users with optional team/role filtering (admin only)
  - Query params: `?team_id=1&role=team_lead`
- `POST /v1/users/` - Create a new user with team and role assignment (admin only)
- `GET /v1/users/{user_id}` - Get user by ID (admin only)
- `PUT /v1/users/{user_id}` - Update user including team and role (admin only)
- `DELETE /v1/users/{user_id}` - Delete user (admin only)

### Incidents (Enhanced with Team Support)
- `GET /v1/incidents/` - List all incidents with optional team filtering
  - Query params: `?team_id=1&status=triggered`
- `POST /v1/incidents/` - Create a new incident with team assignment
- `GET /v1/incidents/{incident_id}` - Get incident details
- `PUT /v1/incidents/{incident_id}` - Update an incident
- `POST /v1/incidents/{incident_id}/acknowledge` - Acknowledge an incident
- `POST /v1/incidents/{incident_id}/resolve` - Resolve an incident
- `POST /v1/incidents/{incident_id}/snooze` - Snooze an incident
- `POST /v1/incidents/{incident_id}/assign` - Assign an incident to a user with role
- `POST /v1/incidents/{incident_id}/comments` - Add a comment to an incident
- `GET /v1/incidents/{incident_id}/timeline` - Get incident timeline
- `POST /v1/incidents/{incident_id}/escalate` - Manually trigger escalation
- `GET /v1/incidents/{incident_id}/escalation-events` - Get escalation events

### Escalation Policies (Enhanced with Team Support)
- `GET /v1/escalation/policies/` - List all escalation policies (admin only)
- `POST /v1/escalation/policies/` - Create a new escalation policy with team conditions (admin only)
- `GET /v1/escalation/policies/{policy_id}` - Get escalation policy details (admin only)
- `PUT /v1/escalation/policies/{policy_id}` - Update an escalation policy (admin only)
- `DELETE /v1/escalation/policies/{policy_id}` - Delete an escalation policy (admin only)

### Notification Preferences
- `GET /v1/notification-preferences/me` - Get current user's preferences
- `PUT /v1/notification-preferences/me/{channel}` - Update user preference
- `GET /v1/notification-preferences/{user_id}` - Get user preferences (admin)
- `PUT /v1/notification-preferences/{user_id}/{channel}` - Update user preference (admin)

### Health & Documentation
- `GET /health` - Health check
- `GET /` - Root endpoint
- `GET /docs` - Swagger UI documentation
- `GET /v1/openapi.json` - OpenAPI schema

### Webhooks
- `POST /v1/alerts/elastic` - Webhook for receiving alerts from Elastic APM

## Background Processing

The system includes a background worker that automatically processes escalations:

- Runs every minute to check for pending escalations
- Processes each active incident that matches escalation policy conditions
- Executes the appropriate actions based on the defined steps and delays
- Handles errors gracefully and logs them for review

The worker is automatically started when the application starts and stopped when the application shuts down.

## Database Migrations

The project uses Alembic for database migrations:

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Apply pending migrations
alembic upgrade head

# Create new migration (when models change)
alembic revision --autogenerate -m "description"
```

## Development

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8
```

### Testing Escalations

To test the escalation system:

1. Create an escalation policy using the API
2. Create or update an incident to match the policy conditions
3. The system will automatically process escalations in the background
4. Monitor the logs to see escalation events being processed

## Deployment

### Production

For production deployment, consider using:
- Gunicorn as the ASGI server
- Nginx as a reverse proxy
- Supervisor for process management
- Environment variables for configuration

Example Gunicorn command:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### Docker

```bash
# Build the image
docker build -t incident-management .

# Run the container
docker run -p 8000:8000 incident-management
```

## 🎯 Current Status

- ✅ **100% API Coverage** - All endpoints tested and working (60 E2E tests)
- ✅ **Team & Role System** - Comprehensive team management with 7 user roles 🆕
- ✅ **Enhanced Incident Management** - Team-based assignment and filtering 🆕
- ✅ **Advanced Escalation System** - Team-aware escalation policies 🆕
- ✅ **Database Migrations** - Alembic working with PostgreSQL
- ✅ **Authentication System** - JWT-based with comprehensive role-based access
- ✅ **Background Worker** - Automatic escalation processing
- ✅ **Notification System** - Multi-channel support with team routing
- ✅ **Comprehensive Testing** - E2E tests with 100% success rate
- ✅ **Documentation** - Complete OpenAPI/Swagger documentation
- ✅ **Production Ready** - All core features implemented and tested

### 🆕 Enhanced Features

**Team Management System:**
- ✅ Team CRUD operations for administrators
- ✅ User assignment to teams with role validation
- ✅ Team-based incident filtering and assignment
- ✅ Team-aware escalation policies

**Role-Based Access Control:**
- ✅ 7 distinct user roles with specific privileges
- ✅ Role-based user filtering and management
- ✅ Team lead and manager escalation targeting
- ✅ Comprehensive permission system

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
