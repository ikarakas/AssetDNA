"""
Web interface router
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

web_router = APIRouter()

@web_router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})