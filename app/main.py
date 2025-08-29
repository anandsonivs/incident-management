import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

from app.core.config import get_settings
from app.worker import start_worker, stop_worker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the frontend directory path
frontend_dir = Path(__file__).parent / "frontend"

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
    
    # Frontend routes at root level
    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        """Serve the main index.html file."""
        index_path = frontend_dir / "index.html"
        if not index_path.exists():
            return {"message": f"Welcome to the {settings.PROJECT_NAME} API", "version": settings.VERSION}
        
        with open(index_path, 'r') as f:
            return HTMLResponse(content=f.read())

    @app.get("/login.html", response_class=HTMLResponse)
    async def serve_login():
        """Serve the login.html file."""
        login_path = frontend_dir / "login.html"
        if not login_path.exists():
            return {"error": "Login page not found"}
        
        with open(login_path, 'r') as f:
            return HTMLResponse(content=f.read())

    @app.get("/{filename}")
    async def serve_static_file(filename: str):
        """Serve static files (CSS, JS, etc.)."""
        file_path = frontend_dir / filename
        
        if not file_path.exists():
            return {"error": "File not found"}
        
        return FileResponse(file_path)
    
    return app

# Create the application instance
app = create_app()
