from fastapi import APIRouter

api_router = APIRouter()

# Import and include routers
from .endpoints import (
    incidents, 
    users, 
    auth, 
    elastic_webhook, 
    notification_preferences,
    escalation
)

api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(elastic_webhook.router, prefix="/alerts/elastic", tags=["alerts"])
api_router.include_router(
    notification_preferences.router, 
    prefix="/notification-preferences",
    tags=["notification-preferences"]
)
api_router.include_router(
    escalation.router,
    prefix="/escalation",
    tags=["escalation"]
)
