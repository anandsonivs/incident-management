from .__about__ import __appname__, __version__, __description__
from fastapi import FastAPI

__all__ = ["__appname__", "__version__", "__description__", "create_app"]

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from fastapi.middleware.cors import CORSMiddleware
    from app.core.config import settings
    
    app = FastAPI(
        title=__appname__,
        description=__description__,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with your frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to the {__appname__} API",
            "version": __version__,
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    return app
