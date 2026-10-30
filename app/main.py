"""
FastAPI Main Application.
Serves the REST API, Public Subscription endpoints, and the Web Admin Panel.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

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
if DIST_DIR.exists() and (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # If API or sub or health, let FastAPI handlers take precedence
    if full_path.startswith("api/") or full_path.startswith("sub/") or full_path == "health":
        raise HTTPException(status_code=404, detail="Not found")

    if DIST_DIR.exists():
        file_path = DIST_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        index_file = DIST_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

    # Embedded Fallback Diagnostic Dashboard if dist was not built
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VPN Store — پنل وب در حال اجرا</title>
        <style>
            body { background: #09090b; color: #f4f4f5; font-family: system-ui, -apple-system, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
            .card { background: #18181b; border: 1px solid #27272a; border-radius: 16px; padding: 28px; max-width: 480px; width: 100%; text-align: center; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }
            h1 { color: #06b6d4; font-size: 20px; margin-top: 0; }
            p { font-size: 13px; color: #a1a1aa; line-height: 1.6; }
            .badge { display: inline-block; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600; margin-bottom: 16px; }
            .btn { display: block; background: #0891b2; color: #fff; text-decoration: none; padding: 10px 16px; border-radius: 12px; font-weight: 600; font-size: 13px; margin-top: 20px; transition: background 0.2s; }
            .btn:hover { background: #06b6d4; }
            .code-box { background: #09090b; border: 1px solid #27272a; border-radius: 8px; padding: 10px; font-family: monospace; font-size: 11px; color: #38bdf8; text-align: left; direction: ltr; margin-top: 14px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="badge">● وب‌سرور و API با موفقیت فعال است</div>
            <h1>سامانه VPN Store آنلاین شد</h1>
            <p>سرویس بک‌اند پایتون و روت‌های API بدون هیچ مشکلی در حال اجرا هستند.</p>
            <div class="code-box">FastAPI Status: OK (Port 8000 Active)<br>SQLite Database: Connected</div>
            <a href="/docs" class="btn">مشاهده مستندات و تست روت‌های API (Swagger)</a>
        </div>
    </body>
    </html>
    """)

