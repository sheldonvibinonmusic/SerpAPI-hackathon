"""
main.py — BharatPrice Pulse
FastAPI application factory, middleware, routing, and lifecycle hooks.

Entrypoint for:
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config.settings import get_settings
from app.routes.analysis import router as analysis_router
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.history import router as history_router
from app.routes.quota import router as quota_router
from app.storage.database import init_db
from app.utils.logging import setup_logging

settings = get_settings()
setup_logging(debug=settings.debug)
logger = logging.getLogger("bharatprice_pulse")

# Define template directory
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown handler."""
    logger.info("Initializing BharatPrice Pulse database and cache...")
    await init_db()
    logger.info(f"BharatPrice Pulse v{settings.app_version} started. Mock mode: {settings.serpapi_mock_mode}")
    yield
    logger.info("BharatPrice Pulse shutting down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Browser-based market-decision copilot for Indian small sellers (SerpApi Hackathon 2026)",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mounting
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# HTML Page routes
@app.get("/", response_class=HTMLResponse, summary="Main Market Copilot UI")
async def home_page(request: Request):
    """Serve the primary decision copilot dashboard."""
    return templates.TemplateResponse(request=request, name="index.html", context={"app_name": settings.app_name})


@app.get("/history", response_class=HTMLResponse, summary="Past Analyses View")
async def history_page(request: Request):
    """Serve the past analyses history view."""
    return templates.TemplateResponse(request=request, name="history.html", context={"app_name": settings.app_name})


# API Routers
app.include_router(analysis_router)
app.include_router(auth_router)
app.include_router(quota_router)
app.include_router(history_router)
app.include_router(health_router)
