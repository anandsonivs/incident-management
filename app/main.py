import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.worker import start_worker, stop_worker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background worker
    logger.info("Starting application...")
    await start_worker()
    logger.info("Background worker started")
    
    yield
    
    # Shutdown: Stop the background worker
    logger.info("Shutting down application...")
    await stop_worker()
    logger.info("Background worker stopped")

def create_app() -> FastAPI:
    from app.api.v1.api import api_router
    
    # Get settings
    settings = get_settings()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, 'BACKEND_CORS_ORIGINS', ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to the {settings.PROJECT_NAME} API",
            "version": settings.VERSION,
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    return app

# Create the application instance
app = create_app()
