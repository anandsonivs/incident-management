from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, teams, incidents, escalation, elastic_webhook, frontend, notification_preferences, notifications

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(escalation.router, prefix="/escalation", tags=["escalation"])
api_router.include_router(elastic_webhook.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(notification_preferences.router, prefix="/notification-preferences", tags=["notifications"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(frontend.router, tags=["frontend"])
