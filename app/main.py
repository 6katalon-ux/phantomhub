"""
FastAPI Main Application.
Serves the REST API, Public Subscription endpoints, and the Web Admin Panel.
Includes built-in mobile-first Embedded Admin Panel fallback and SPA static file support.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from app.core.config import config
from app.core.database import sync_engine, Base, get_db
from app.core.logging import logger
from app.web.routes.api import api_router, get_subscription

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "app" / "web" / "static"
DIST_DIR = BASE_DIR / "dist"

def get_web_dir():
    if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
        return STATIC_DIR
    if DIST_DIR.exists() and (DIST_DIR / "index.html").exists():
        return DIST_DIR
    return None

@asynccontextmanager
async def lifespan(app: FastAPI):
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
@app.get("/sub/{token}")
async def root_sub(token: str, db=Depends(get_db)):
    return await get_subscription(token, db)

@app.get("/health")
def health_check():
    return {"status": "ok", "app": "VPN Store", "version": "1.0.0"}

# Mount static assets if directory exists
target_web = get_web_dir()
if target_web and (target_web / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(target_web / "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Exclude system and API routes from SPA catching
    if full_path.startswith("api/") or full_path.startswith("sub/") or full_path in ("health", "docs", "openapi.json", "redoc"):
        raise HTTPException(status_code=404, detail="Not found")

    # 1. Try static compiled React bundle
    target_dir = get_web_dir()
    if target_dir:
        file_path = target_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        index_file = target_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

    # 2. Standalone Embedded Mobile-First Dark-Mode Admin Panel
    # Ensures the admin panel is 100% accessible even before Vite assets are pulled
    return HTMLResponse("""<!DOCTYPE html>
<html lang="fa" dir="rtl" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>VPN Store — پنل مدیریت هوشمند اشتراک VPN</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #09090b;
            --card: #141417;
            --card-border: #27272a;
            --accent: #06b6d4;
            --accent-hover: #0891b2;
            --accent-glow: rgba(6, 182, 212, 0.2);
            --text: #f4f4f5;
            --text-muted: #a1a1aa;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Vazirmatn', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            direction: rtl;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
        }
        .header {
            background: rgba(20, 20, 23, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--card-border);
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 50;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .brand-icon {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            background: linear-gradient(135deg, #06b6d4, #3b82f6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 0 15px var(--accent-glow);
        }
        .brand-title {
            font-size: 16px;
            font-weight: 800;
            color: #fff;
            letter-spacing: -0.5px;
        }
        .brand-subtitle {
            font-size: 11px;
            color: var(--accent);
            font-weight: 500;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
        }
        .badge-success { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-cyan { background: rgba(6, 182, 212, 0.15); color: #38bdf8; border: 1px solid rgba(6, 182, 212, 0.3); }
        .main-container {
            flex: 1;
            padding: 16px;
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
        }
        .nav-tabs {
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding-bottom: 8px;
            margin-bottom: 16px;
            scrollbar-width: none;
        }
        .nav-tabs::-webkit-scrollbar { display: none; }
        .nav-tab {
            background: var(--card);
            border: 1px solid var(--card-border);
            color: var(--text-muted);
            padding: 8px 14px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .nav-tab.active {
            background: rgba(6, 182, 212, 0.15);
            color: var(--accent);
            border-color: var(--accent);
        }
        .card {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.4);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            padding-bottom: 12px;
        }
        .card-title {
            font-size: 15px;
            font-weight: 700;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .form-group {
            margin-bottom: 14px;
        }
        .form-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
        }
        .form-input {
            width: 100%;
            background: #09090b;
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 10px 14px;
            color: #fff;
            font-family: inherit;
            font-size: 13px;
            outline: none;
            transition: border 0.2s;
            direction: ltr;
            text-align: left;
        }
        .form-input.rtl { direction: rtl; text-align: right; }
        .form-input:focus { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: var(--accent);
            color: #09090b;
            font-weight: 700;
            font-size: 13px;
            padding: 10px 18px;
            border-radius: 10px;
            border: none;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
        }
        .btn:hover { background: var(--accent-hover); color: #fff; }
        .btn-secondary {
            background: #27272a;
            color: #f4f4f5;
        }
        .btn-secondary:hover { background: #3f3f46; }
        .btn-outline {
            background: transparent;
            border: 1px solid var(--card-border);
            color: var(--text);
        }
        .btn-outline:hover { background: rgba(255,255,255,0.05); border-color: var(--accent); }
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }
        .stat-card {
            background: rgba(9, 9, 11, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 14px;
        }
        .stat-num {
            font-size: 20px;
            font-weight: 800;
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
            margin-top: 4px;
        }
        .stat-label {
            font-size: 11px;
            color: var(--text-muted);
        }
        .toast {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 10px 18px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 600;
            z-index: 100;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
            display: none;
            text-align: center;
            max-width: 90%;
        }
        .toast-success { background: #065f46; color: #34d399; border: 1px solid #059669; }
        .toast-error { background: #7f1d1d; color: #f87171; border: 1px solid #b91c1c; }
        .code-box {
            background: #09090b;
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 10px 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #38bdf8;
            direction: ltr;
            text-align: left;
            margin-top: 8px;
            overflow-x: auto;
        }
        .login-wrap {
            max-width: 400px;
            margin: 40px auto 0;
        }
        .hidden { display: none !important; }
    </style>
</head>
<body>

    <!-- Header -->
    <header class="header">
        <div class="brand">
            <div class="brand-icon">🛡️</div>
            <div>
                <div class="brand-title">VPN Store</div>
                <div class="brand-subtitle">پنل مدیریت موبایل‌فرست</div>
            </div>
        </div>
        <div id="header-status">
            <span class="badge badge-success">● سرور آنلاین (Port 8000)</span>
        </div>
    </header>

    <!-- Main Content -->
    <main class="main-container">

        <!-- Login Screen -->
        <div id="login-section" class="login-wrap">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">🔐 ورود به پنل مدیریت</span>
                    <span class="badge badge-cyan">ادمین</span>
                </div>
                <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.6;">
                    برای ورود، نام کاربری و رمز عبور تعیین‌شده در مرحله نصب (Setup) را وارد نمایید.
                </p>
                <form id="login-form" onsubmit="handleLogin(event)">
                    <div class="form-group">
                        <label class="form-label">نام کاربری ادمین</label>
                        <input id="login-user" type="text" class="form-input" value="admin" required placeholder="admin">
                    </div>
                    <div class="form-group">
                        <label class="form-label">رمز عبور ادمین</label>
                        <input id="login-pass" type="password" class="form-input" required placeholder="••••••••">
                    </div>
                    <button type="submit" id="login-btn" class="btn" style="margin-top: 8px;">
                        ورود به پنل مدیریت
                    </button>
                </form>

                <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--card-border); font-size: 11px; color: var(--text-muted);">
                    <strong>رمز عبور را فراموش کرده‌اید؟</strong>
                    <div style="margin-top: 4px;">کافیست دستور زیر را یک‌بار در سرور لایت‌سیل/اوبونتو اجرا کنید تا رمز به <code style="color:var(--accent);">admin123</code> ریست شود:</div>
                    <div class="code-box">/opt/vpn_store/.venv/bin/python -c "import sqlite3, bcrypt; c=sqlite3.connect('/opt/vpn_store/data/vpn_store.db'); h=bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode(); c.execute('UPDATE admins SET password_hash=? WHERE username=\'admin\'', (h,)); c.commit(); print('رمز ادمین به admin123 تغییر یافت')"</div>
                </div>
            </div>
        </div>

        <!-- Dashboard App (shown after login) -->
        <div id="app-section" class="hidden">
            <!-- Tabs Navigation -->
            <div class="nav-tabs">
                <button class="nav-tab active" onclick="switchTab('dashboard')">📊 وضعیت کل</button>
                <button class="nav-tab" onclick="switchTab('bot')">🤖 ربات تلگرام</button>
                <button class="nav-tab" onclick="switchTab('xui')">🌐 پنل 3X-UI</button>
                <button class="nav-tab" onclick="switchTab('plans')">📦 پلن‌ها و فروش</button>
                <button class="nav-tab" onclick="switchTab('users')">👥 کاربران</button>
                <button class="nav-tab" onclick="logout()" style="color: var(--danger); margin-right: auto;">🚪 خروج</button>
            </div>

            <!-- Tab 1: Dashboard Stats -->
            <div id="tab-dashboard" class="tab-pane">
                <div class="grid-2">
                    <div class="stat-card">
                        <div class="stat-label">👥 کل کاربران</div>
                        <div id="stat-users" class="stat-num">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">⚡ سرویس‌های فعال</div>
                        <div id="stat-services" class="stat-num">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">💰 مجموع فروش</div>
                        <div id="stat-sales" class="stat-num">0 تومان</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">💳 پرداخت در انتظار</div>
                        <div id="stat-pending" class="stat-num">0</div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">⚙️ وضعیت سرویس‌های اصلی</span>
                        <button onclick="refreshData()" class="btn btn-outline" style="width: auto; padding: 4px 10px; font-size: 11px;">🔄 بروزرسانی</button>
                    </div>
                    <div style="font-size: 12px; line-height: 2;">
                        <div>🟢 <strong>FastAPI Backend:</strong> پورت 8000 فعال و پاسخگو</div>
                        <div>🟢 <strong>SQLite Database:</strong> متصل به /opt/vpn_store/data/vpn_store.db</div>
                        <div id="status-bot-text">⚪ <strong>ربات تلگرام:</strong> بررسی توکن...</div>
                        <div id="status-xui-text">⚪ <strong>اتصال 3X-UI:</strong> بررسی وب‌هوک...</div>
                    </div>
                </div>

                <div class="card" style="border-color: rgba(6, 182, 212, 0.3);">
                    <div class="card-header">
                        <span class="card-title" style="color: var(--accent);">🚀 دریافت رابط کاربری ری‌اکت (نسخه کامل ۱۵ زبانه)</span>
                    </div>
                    <p style="font-size: 12px; color: var(--text-muted); line-height: 1.6; margin-bottom: 12px;">
                        برای بارگذاری داشبورد کامل React با نمودارها، مدیریت جامع هدایا، تراکنش‌ها، لاگ‌ها و اعلان‌ها، دستور زیر را در سرور اجرا نمایید:
                    </p>
                    <div class="code-box">cd /opt/vpn_store && git pull && sudo systemctl restart vpnstore-web</div>
                </div>
            </div>

            <!-- Tab 2: Telegram Bot -->
            <div id="tab-bot" class="tab-pane hidden">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🤖 تنظیمات ربات تلگرام (Aiogram 3)</span>
                        <span class="badge badge-cyan">بدون نیاز به ادیت کد</span>
                    </div>
                    <div class="form-group">
                        <label class="form-label">توکن ربات تلگرام (از @BotFather)</label>
                        <input id="cfg-bot-token" type="text" class="form-input" placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ">
                    </div>
                    <div class="form-group">
                        <label class="form-label">شناسه عددی ادمین تلگرام (از @userinfobot)</label>
                        <input id="cfg-bot-admin-ids" type="text" class="form-input" placeholder="123456789">
                    </div>
                    <div class="form-group">
                        <label class="form-label">آیدی پشتیبانی تلگرام</label>
                        <input id="cfg-bot-support" type="text" class="form-input" placeholder="@support_vpn">
                    </div>
                    <div class="grid-2" style="margin-top: 16px;">
                        <button onclick="saveBotSettings()" class="btn">💾 ذخیره تنظیمات</button>
                        <button onclick="testBotToken()" class="btn btn-secondary">⚡ تست اتصال ربات</button>
                    </div>
                </div>
            </div>

            <!-- Tab 3: 3X-UI Connection -->
            <div id="tab-xui" class="tab-pane hidden">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🌐 اتصال به پنل 3X-UI</span>
                        <span class="badge badge-cyan">REST API</span>
                    </div>
                    <div class="form-group">
                        <label class="form-label">آدرس کامل پنل 3X-UI (همراه با پورت)</label>
                        <input id="cfg-xui-url" type="text" class="form-input" placeholder="http://13.49.78.84:2053">
                    </div>
                    <div class="form-group">
                        <label class="form-label">نام کاربری ادمین 3X-UI</label>
                        <input id="cfg-xui-user" type="text" class="form-input" placeholder="admin">
                    </div>
                    <div class="form-group">
                        <label class="form-label">رمز عبور ادمین 3X-UI</label>
                        <input id="cfg-xui-pass" type="password" class="form-input" placeholder="••••••••">
                    </div>
                    <div class="form-group">
                        <label class="form-label">دامنه یا آی‌پی ساخت لینک اشتراک (Client Host)</label>
                        <input id="cfg-vpn-host" type="text" class="form-input" placeholder="13.49.78.84">
                    </div>
                    <div class="grid-2" style="margin-top: 16px;">
                        <button onclick="saveXuiSettings()" class="btn">💾 ذخیره مشخصات</button>
                        <button onclick="testXuiConnection()" class="btn btn-secondary">⚡ تست اتصال 3X-UI</button>
                    </div>
                </div>
            </div>

            <!-- Tab 4: Plans -->
            <div id="tab-plans" class="tab-pane hidden">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">📦 پلن‌های فروش اشتراک</span>
                        <button onclick="loadPlans()" class="btn btn-outline" style="width:auto; padding:4px 10px; font-size:11px;">بروزرسانی</button>
                    </div>
                    <div id="plans-list" style="font-size: 13px;">
                        در حال بارگذاری پلن‌ها...
                    </div>
                </div>
            </div>

            <!-- Tab 5: Users -->
            <div id="tab-users" class="tab-pane hidden">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">👥 لیست کاربران</span>
                        <button onclick="loadUsers()" class="btn btn-outline" style="width:auto; padding:4px 10px; font-size:11px;">بروزرسانی</button>
                    </div>
                    <div id="users-list" style="font-size: 13px;">
                        در حال بارگذاری کاربران...
                    </div>
                </div>
            </div>

        </div>

    </main>

    <!-- Toast Notice -->
    <div id="toast" class="toast"></div>

    <script>
        let currentToken = localStorage.getItem('vpnstore_token') || '';

        function showToast(msg, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.className = 'toast toast-' + type;
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 3500);
        }

        async function handleLogin(e) {
            e.preventDefault();
            const btn = document.getElementById('login-btn');
            btn.textContent = 'در حال اعتبارسنجی...';
            btn.disabled = true;

            const u = document.getElementById('login-user').value.trim();
            const p = document.getElementById('login-pass').value;

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: u, password: p })
                });
                const data = await res.json();
                if (res.ok && data.token) {
                    currentToken = data.token;
                    localStorage.setItem('vpnstore_token', currentToken);
                    showToast('ورود با موفقیت انجام شد!');
                    initDashboard();
                } else {
                    showToast(data.detail || 'نام کاربری یا رمز عبور اشتباه است', 'error');
                }
            } catch (err) {
                showToast('خطا در برقراری ارتباط با وب‌سرور', 'error');
            } finally {
                btn.textContent = 'ورود به پنل مدیریت';
                btn.disabled = false;
            }
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));

            const target = document.getElementById('tab-' + tabId);
            if (target) target.classList.remove('hidden');

            event.currentTarget.classList.add('active');

            if (tabId === 'plans') loadPlans();
            if (tabId === 'users') loadUsers();
        }

        function logout() {
            localStorage.removeItem('vpnstore_token');
            currentToken = '';
            document.getElementById('login-section').classList.remove('hidden');
            document.getElementById('app-section').classList.add('hidden');
            showToast('از پنل خارج شدید');
        }

        async function initDashboard() {
            document.getElementById('login-section').classList.add('hidden');
            document.getElementById('app-section').classList.remove('hidden');
            refreshData();
            loadSettings();
        }

        async function refreshData() {
            try {
                const res = await fetch('/api/admin/dashboard/stats', {
                    headers: { 'Authorization': 'Bearer ' + currentToken }
                });
                if (res.ok) {
                    const stats = await res.json();
                    document.getElementById('stat-users').textContent = stats.users_count || 0;
                    document.getElementById('stat-services').textContent = stats.active_services || 0;
                    document.getElementById('stat-sales').textContent = (stats.total_sales || 0).toLocaleString('fa-IR') + ' تومان';
                    document.getElementById('stat-pending').textContent = stats.pending_payments || 0;
                }
            } catch (e) {}
        }

        async function loadSettings() {
            try {
                const res = await fetch('/api/admin/settings', {
                    headers: { 'Authorization': 'Bearer ' + currentToken }
                });
                if (res.ok) {
                    const s = await res.json();
                    if (s.bot_token) document.getElementById('cfg-bot-token').value = s.bot_token;
                    if (s.bot_admin_ids) document.getElementById('cfg-bot-admin-ids').value = s.bot_admin_ids;
                    if (s.bot_support_username) document.getElementById('cfg-bot-support').value = s.bot_support_username;
                    if (s.xui_url) document.getElementById('cfg-xui-url').value = s.xui_url;
                    if (s.xui_username) document.getElementById('cfg-xui-user').value = s.xui_username;
                    if (s.vpn_server_host) document.getElementById('cfg-vpn-host').value = s.vpn_server_host;
                }
            } catch (e) {}
        }

        async function saveBotSettings() {
            const body = {
                settings: {
                    bot_token: document.getElementById('cfg-bot-token').value.trim(),
                    bot_admin_ids: document.getElementById('cfg-bot-admin-ids').value.trim(),
                    bot_support_username: document.getElementById('cfg-bot-support').value.trim()
                }
            };
            const res = await fetch('/api/admin/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + currentToken },
                body: JSON.stringify(body)
            });
            if (res.ok) showToast('تنظیمات ربات تلگرام در دیتابیس ذخیره شد');
            else showToast('خطا در ذخیره تنظیمات', 'error');
        }

        async function testBotToken() {
            showToast('در حال بررسی توکن در تلگرام...');
            const res = await fetch('/api/admin/settings/bot/test', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + currentToken }
            });
            const data = await res.json();
            if (res.ok && data.status === 'ok') {
                showToast('اتصال به ربات برقرار شد: @' + (data.bot?.username || 'ok'));
                document.getElementById('status-bot-text').innerHTML = '🟢 <strong>ربات تلگرام:</strong> متصل به @' + (data.bot?.username || 'فعال');
            } else {
                showToast(data.message || 'خطا در اتصال به تلگرام', 'error');
            }
        }

        async function saveXuiSettings() {
            const body = {
                settings: {
                    xui_url: document.getElementById('cfg-xui-url').value.trim(),
                    xui_username: document.getElementById('cfg-xui-user').value.trim(),
                    xui_password: document.getElementById('cfg-xui-pass').value.trim(),
                    vpn_server_host: document.getElementById('cfg-vpn-host').value.trim()
                }
            };
            const res = await fetch('/api/admin/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + currentToken },
                body: JSON.stringify(body)
            });
            if (res.ok) showToast('تنظیمات 3X-UI با موفقیت ذخیره شد');
            else showToast('خطا در ذخیره تنظیمات', 'error');
        }

        async function testXuiConnection() {
            showToast('در حال تست اتصال به 3X-UI...');
            const res = await fetch('/api/admin/settings/3x-ui/test', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + currentToken }
            });
            const data = await res.json();
            if (res.ok && data.status === 'ok') {
                showToast('اتصال به پنل 3X-UI برقرار شد! اینباندها: ' + (data.inbounds_count || 0));
                document.getElementById('status-xui-text').innerHTML = '🟢 <strong>اتصال 3X-UI:</strong> متصل (اینباندها: ' + (data.inbounds_count || 0) + ')';
            } else {
                showToast(data.message || 'خطا در اتصال به 3X-UI', 'error');
            }
        }

        async function loadPlans() {
            const el = document.getElementById('plans-list');
            try {
                const res = await fetch('/api/admin/plans', {
                    headers: { 'Authorization': 'Bearer ' + currentToken }
                });
                const data = await res.json();
                if (data && data.length) {
                    el.innerHTML = data.map(p => `
                        <div style="background:rgba(255,255,255,0.03); border:1px solid var(--card-border); border-radius:10px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <strong>${p.name}</strong>
                                <div style="font-size:11px; color:var(--text-muted);">${p.traffic_gb} گیگابایت | ${p.duration_days} روزه</div>
                            </div>
                            <div style="font-weight:700; color:var(--accent);">
                                ${p.price.toLocaleString('fa-IR')} تومان
                            </div>
                        </div>
                    `).join('');
                } else {
                    el.textContent = 'هیچ پلنی یافت نشد.';
                }
            } catch (e) { el.textContent = 'خطا در بارگذاری پلن‌ها'; }
        }

        async function loadUsers() {
            const el = document.getElementById('users-list');
            try {
                const res = await fetch('/api/admin/users', {
                    headers: { 'Authorization': 'Bearer ' + currentToken }
                });
                const data = await res.json();
                if (data && data.length) {
                    el.innerHTML = data.map(u => `
                        <div style="background:rgba(255,255,255,0.03); border:1px solid var(--card-border); border-radius:10px; padding:12px; margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between;">
                                <strong>${u.first_name || 'کاربر'} (@${u.telegram_username || 'بدون آیدی'})</strong>
                                <span style="font-size:11px; color:var(--accent);">موجودی: ${(u.wallet_balance||0).toLocaleString('fa-IR')} تومان</span>
                            </div>
                            <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">شناسه تلگرام: ${u.telegram_id}</div>
                        </div>
                    `).join('');
                } else {
                    el.textContent = 'هنوز کاربری ثبت نشده است.';
                }
            } catch (e) { el.textContent = 'خطا در بارگذاری کاربران'; }
        }

        // Auto check token on load
        if (currentToken) {
            initDashboard();
        }
    </script>
</body>
</html>
    """)
