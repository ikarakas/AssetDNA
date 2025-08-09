"""
API router aggregation
"""

from fastapi import APIRouter
from app.api.endpoints import assets, bom, import_export, reports, system, asset_operations

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    system.router,
    prefix="/system",
    tags=["System"]
)

api_router.include_router(
    assets.router,
    prefix="/assets",
    tags=["Assets"]
)

api_router.include_router(
    bom.router,
    prefix="",
    tags=["BOM"]
)

api_router.include_router(
    import_export.router,
    prefix="/io",
    tags=["Import/Export"]
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"]
)

api_router.include_router(
    asset_operations.router,
    prefix="",
    tags=["Asset Operations"]
)