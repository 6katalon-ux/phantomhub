"""
FastAPI Main Application.
Serves the REST API, Public Subscription endpoints, and the Web Admin Panel.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from app.core.config import config
from app.core.database import sync_engine, Base
from app.core.logging import logger
from app.web.routes.api import api_router

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist on startup
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=sync_engine)
    config.refresh_cache_sync()
    logger.info("VPN Store Web Application started successfully.")
    yield
    logger.info("Shutting down VPN Store Web Application...")

app = FastAPI(
    title="VPN Store API",
    version="1.0.0",
    description="VPN Subscription Management & Sales Platform API",
    lifespan=lifespan
)

# Enable CORS for mobile browsers and frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API endpoints under /api
app.include_router(api_router, prefix="/api")

# Mount public subscription also at root level /sub/{token}
from app.web.routes.api import get_subscription
from app.core.database import get_db
from fastapi import Depends
@app.get("/sub/{token}")
async def root_sub(token: str, db=Depends(get_db)):
    return await get_subscription(token, db)

@app.get("/health")
def health_check():
    return {"status": "ok", "app": "VPN Store", "version": "1.0.0"}

# Serve Frontend static assets if built into dist/
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = DIST_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")
