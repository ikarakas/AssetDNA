"""
AssetDNA Application Factory
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="AssetDNA",
        description="BOM Tracking & Historical Analysis System",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Import routers here to avoid circular imports
    from app.api import api_router
    from app.web import web_router
    
    # Mount static files
    import os
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Include routers
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(web_router)
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize database and load asset types"""
        await init_db()
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "AssetDNA"}
    
    return app