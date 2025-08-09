#!/usr/bin/env python3
"""
AssetDNA - BOM Tracking & Historical Analysis System
Main application entry point
"""

import uvicorn
from app import create_app
from app.core.config import settings

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )