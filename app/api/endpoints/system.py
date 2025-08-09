"""
System information endpoints
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

# Store server start time
server_start_time = datetime.now(timezone.utc)


@router.get("/info")
async def get_system_info():
    """Get system information including version and uptime"""
    current_time = datetime.now(timezone.utc)
    uptime_seconds = (current_time - server_start_time).total_seconds()
    
    # Calculate uptime components
    days = int(uptime_seconds // (24 * 3600))
    hours = int((uptime_seconds % (24 * 3600)) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    
    # Format uptime string
    uptime_parts = []
    if days > 0:
        uptime_parts.append(f"{days}d")
    if hours > 0:
        uptime_parts.append(f"{hours}h")
    if minutes > 0:
        uptime_parts.append(f"{minutes}m")
    uptime_parts.append(f"{seconds}s")
    
    uptime_str = " ".join(uptime_parts)
    
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "uptime": uptime_str,
        "uptime_seconds": int(uptime_seconds),
        "server_start_time": server_start_time.isoformat(),
        "current_time": current_time.isoformat()
    }