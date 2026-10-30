"""
FastAPI REST API Routes for Web Admin Dashboard and Public Subscription Endpoint.
Supports all 15 administrative sections: Dashboard, Bot Settings, 3X-UI Connection,
Inbounds, Plans, Users, Services, Wallet, Gifts, Trials, Payments, System, Logs, Backups.
"""

import time
import os
import shutil
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update

from app.core.database import get_db, DB_PATH
from app.core.config import config
from app.core.security import (
    verify_password, create_access_token, get_current_admin,
    check_login_rate_limit, reset_login_attempts
)
from app.core.logging import logger, get_recent_logs
from app.models.models import (
    Admin, User, Setting, Plan, Service, Transaction,
    Payment, GiftCode, GiftRedemption, AuditLog, Notification
)
from app.services.xui_client import xui_client
from app.services.vpn_provisioner import vpn_provisioner
from app.services.wallet import wallet_service
from app.services.traffic_sync import traffic_sync_service
from app.workers.scheduler import perform_db_backup, BACKUPS_DIR

api_router = APIRouter()

# --- Request Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]

class PlanCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    price: int
    traffic_gb: int
    duration_days: int
    inbound_id: Optional[int] = 1
    protocol: Optional[str] = "vless"
    max_ips: Optional[int] = 2
    is_active: Optional[bool] = True
    sort_order: Optional[int] = 0

class UserBalanceAdjustRequest(BaseModel):
    amount: int
    description: Optional[str] = "Manual Admin Adjustment"

class GiftCodeCreateRequest(BaseModel):
    code: str
    amount: int
    max_redemptions: Optional[int] = 1
    expire_days: Optional[int] = 30

class PaymentReviewRequest(BaseModel):
    action: str # "approve" or "reject"
    admin_note: Optional[str] = ""

class BroadcastRequest(BaseModel):
    title: str
    message: str

# --- 1. Authentication ---
@api_router.post("/auth/login")
async def login(req: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not check_login_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many failed login attempts. Please wait 5 minutes.")

    res = await db.execute(select(Admin).where(Admin.username == req.username))
    admin = res.scalar_one_or_none()

    if not admin or not verify_password(req.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    reset_login_attempts(client_ip)
    admin.last_login = datetime.utcnow()
    await db.commit()

    token = create_access_token({"sub": admin.username, "id": admin.id, "type": "admin"})
    response.set_cookie(
        key="admin_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400
    )
    return {"token": token, "admin": admin.to_dict()}

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("admin_session")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(admin_data: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Admin).where(Admin.id == admin_data.get("id")))
    admin = res.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin.to_dict()

# --- 2. Dashboard Statistics ---
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    users_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_services = (await db.execute(select(func.count(Service.id)).where(Service.is_active == 1))).scalar() or 0
    expired_services = (await db.execute(select(func.count(Service.id)).where(Service.is_active == 0))).scalar() or 0
    
    # Financial metrics
    total_sales = (await db.execute(
        select(func.sum(Transaction.amount)).where(Transaction.type == "purchase")
    )).scalar() or 0
    total_sales = abs(total_sales)

    wallet_liabilities = (await db.execute(select(func.sum(User.wallet_balance)))).scalar() or 0
    pending_payments = (await db.execute(
        select(func.count(Payment.id)).where(Payment.status == "pending")
    )).scalar() or 0

    return {
        "users_count": users_count,
        "active_services": active_services,
        "expired_services": expired_services,
        "total_sales": total_sales,
        "wallet_liabilities": wallet_liabilities,
        "pending_payments": pending_payments,
        "last_sync": config.get("last_traffic_sync_timestamp", "Not yet synced"),
        "currency": config.get("currency", "تومان"),
        "bot_configured": bool(config.get("bot_token")),
        "bot_enabled": config.get_bool("bot_enabled", True)
    }

# --- 3. Settings Management ---
@api_router.get("/settings")
async def get_all_settings(admin: Dict[str, Any] = Depends(get_current_admin)):
    config.refresh_cache_sync()
    flat = {}
    for k, v in config._cache.items():
        val = v.get("value", "")
        # Cast booleans and ints where appropriate
        if val in ("1", "true", "True", True):
            flat[k] = True
        elif val in ("0", "false", "False", False):
            flat[k] = False
        elif str(val).isdigit() and k in ("trial_traffic_gb", "trial_duration_days", "sync_interval_mins", "backup_retention_days", "xui_timeout", "xui_default_inbound", "trial_inbound_id"):
            flat[k] = int(val)
        else:
            flat[k] = val
    return flat

@api_router.post("/settings")
async def update_settings(req: SettingsUpdateRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    bot_changed = False
    for key, val in req.settings.items():
        # Do not overwrite with masked bullets
        if isinstance(val, str) and "••••" in val:
            continue
        if key in ("bot_token", "bot_enabled"):
            val_str = str(val).strip() if isinstance(val, str) else str(val)
            if key == "bot_token":
                val = val_str
            if str(val) != str(config.get(key)):
                bot_changed = True
        config.set(key, val)

    # If bot token or status changed, restart vpnstore-bot systemd service
    if bot_changed:
        try:
            import subprocess
            subprocess.run(["systemctl", "restart", "vpnstore-bot.service"], timeout=5)
            logger.info("Restarted vpnstore-bot.service following settings update.")
        except Exception as e:
            logger.warning(f"Could not auto-restart vpnstore-bot.service: {e}")

    return {"message": "Settings updated successfully"}

@api_router.post("/settings/test-bot")
async def test_bot(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Directly verify Telegram Bot Token with Telegram API"""
    token = config.get("bot_token", "").strip()
    if not token:
        return {"success": False, "message": "توکن ربات تلگرام در تنظیمات خالی است. ابتدا توکن را ذخیره نمایید."}

    import aiohttp
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("ok"):
                    bot_info = data.get("result", {})
                    # Ensure service is running
                    try:
                        import subprocess
                        subprocess.run(["systemctl", "restart", "vpnstore-bot.service"], timeout=5)
                    except Exception:
                        pass
                    return {
                        "success": True,
                        "message": f"اتصال به تلگرام موفقیت‌آمیز است. ربات: @{bot_info.get('username')} ({bot_info.get('first_name')})",
                        "bot": bot_info
                    }
                else:
                    return {
                        "success": False,
                        "message": f"خطا از تلگرام: {data.get('description', 'توکن نامعتبر است')}"
                    }
    except Exception as e:
        return {"success": False, "message": f"عدم امکان اتصال به سرور تلگرام: {str(e)}"}

@api_router.post("/settings/restart-bot")
async def restart_bot_service(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Restart vpnstore-bot systemd service"""
    try:
        import subprocess
        res = subprocess.run(["systemctl", "restart", "vpnstore-bot.service"], capture_output=True, text=True, timeout=10)
        return {"success": True, "message": "سرویس ربات تلگرام با موفقیت مجدداً راه‌اندازی شد."}
    except Exception as e:
        return {"success": False, "message": f"خطا در ریستارت سرویس ربات: {str(e)}"}

@api_router.post("/settings/test-xui")
async def test_xui(admin: Dict[str, Any] = Depends(get_current_admin)):
    return await xui_client.test_connection()

# --- 4. Inbound Manager ---
@api_router.get("/inbounds")
async def get_inbounds(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Fetch and normalize 3X-UI inbounds into structured InboundItem array"""
    import json
    raw_res = await xui_client.get_inbounds()
    items = []

    if raw_res and raw_res.get("success") and "obj" in raw_res:
        inbounds_list = raw_res.get("obj") or []
        for obj in inbounds_list:
            inbound_id = obj.get("id", 1)
            remark = obj.get("remark") or f"Inbound #{inbound_id}"
            protocol = obj.get("protocol", "vless")
            port = obj.get("port", 443)
            enable = bool(obj.get("enable", True))

            network = "tcp"
            security = "none"
            reality_sni = ""
            total_clients = 0

            # Parse streamSettings
            stream_raw = obj.get("streamSettings", "")
            if isinstance(stream_raw, str) and stream_raw:
                try:
                    s_data = json.loads(stream_raw)
                    network = s_data.get("network", "tcp")
                    security = s_data.get("security", "none")
                    if security == "reality":
                        rs = s_data.get("realitySettings", {})
                        server_names = rs.get("serverNames", [])
                        if server_names:
                            reality_sni = server_names[0]
                except Exception:
                    pass
            elif isinstance(stream_raw, dict):
                network = stream_raw.get("network", "tcp")
                security = stream_raw.get("security", "none")

            # Parse clients count
            settings_raw = obj.get("settings", "")
            if isinstance(settings_raw, str) and settings_raw:
                try:
                    set_data = json.loads(settings_raw)
                    total_clients = len(set_data.get("clients", []))
                except Exception:
                    pass
            elif obj.get("clientStats"):
                total_clients = len(obj.get("clientStats", []))

            items.append({
                "id": inbound_id,
                "inbound_id": inbound_id,
                "remark": remark,
                "protocol": protocol,
                "port": port,
                "network": network,
                "security": security,
                "total_clients": total_clients,
                "is_enabled": enable,
                "reality_sni": reality_sni
            })

    return items

# --- 5. Plans Manager ---
@api_router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Plan).order_by(Plan.sort_order.asc(), Plan.id.asc()))
    plans = res.scalars().all()
    return [p.to_dict() for p in plans]

@api_router.post("/plans")
async def create_plan(req: PlanCreateRequest, admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    plan = Plan(
        name=req.name,
        description=req.description,
        price=req.price,
        traffic_gb=req.traffic_gb,
        duration_days=req.duration_days,
        inbound_id=req.inbound_id,
        protocol=req.protocol,
        max_ips=req.max_ips,
        is_active=1 if req.is_active else 0,
        sort_order=req.sort_order
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan.to_dict()

@api_router.put("/plans/{plan_id}")
async def update_plan(plan_id: int, req: PlanCreateRequest, admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.name = req.name
    plan.description = req.description
    plan.price = req.price
    plan.traffic_gb = req.traffic_gb
    plan.duration_days = req.duration_days
    plan.inbound_id = req.inbound_id
    plan.protocol = req.protocol
    plan.max_ips = req.max_ips
    plan.is_active = 1 if req.is_active else 0
    plan.sort_order = req.sort_order
    await db.commit()
    return plan.to_dict()

@api_router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: int, admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    await db.delete(plan)
    await db.commit()
    return {"message": "Plan deleted"}

# --- 6. Users Manager ---
@api_router.get("/users")
async def list_users(
    query: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    admin: Dict[str, Any] = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).order_by(desc(User.id))
    if query:
        stmt = stmt.where(
            (User.username.ilike(f"%{query}%")) |
            (User.first_name.ilike(f"%{query}%")) |
            (func.cast(User.telegram_id, String).ilike(f"%{query}%"))
        )
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    res = await db.execute(stmt)
    users = res.scalars().all()
    return [u.to_dict() for u in users]

@api_router.post("/users/{user_id}/adjust-balance")
async def adjust_user_balance(
    user_id: int,
    req: UserBalanceAdjustRequest,
    admin: Dict[str, Any] = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    if req.amount >= 0:
        ok, new_bal, msg = await wallet_service.add_funds(
            session=db,
            user_id=user_id,
            amount=req.amount,
            tx_type="admin_adjustment",
            description=req.description
        )
    else:
        ok, new_bal, msg = await wallet_service.deduct_funds(
            session=db,
            user_id=user_id,
            amount=abs(req.amount),
            description=req.description
        )
    await db.commit()
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "new_balance": new_bal}

@api_router.post("/users/{user_id}/toggle-block")
async def toggle_block_user(user_id: int, admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.is_blocked = 0 if u.is_blocked else 1
    await db.commit()
    return {"is_blocked": bool(u.is_blocked)}

@api_router.post("/users/{user_id}/reset-trial")
async def reset_user_trial(user_id: int, admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.trial_used = 0
    await db.commit()
    return {"message": "Free trial eligibility reset"}

# --- 7. Services Manager ---
@api_router.get("/services")
async def list_services(
    page: int = 1,
    limit: int = 30,
    admin: Dict[str, Any] = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Service).order_by(desc(Service.id)).offset((page - 1) * limit).limit(limit)
    res = await db.execute(stmt)
    services = res.scalars().all()
    return [s.to_dict() for s in services]

@api_router.post("/services/{service_id}/toggle")
async def toggle_service_status(service_id: int, admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Service).where(Service.id == service_id))
    srv = res.scalar_one_or_none()
    if not srv:
        raise HTTPException(status_code=404, detail="Service not found")
    new_state = not bool(srv.is_active)
    ok, msg = await vpn_provisioner.toggle_service(db, service_id, new_state)
    return {"success": ok, "message": msg}

@api_router.delete("/services/{service_id}")
async def delete_service_item(service_id: int, admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    ok, msg = await vpn_provisioner.delete_service(db, service_id)
    return {"success": ok, "message": msg}

@api_router.post("/services/sync-traffic")
async def sync_traffic_on_demand(admin: Dict[str, Any] = Depends(get_current_admin)):
    stats = await traffic_sync_service.run_sync_cycle()
    return {"message": "Traffic synchronized successfully", "stats": stats}

# --- 8. Payments Management ---
@api_router.get("/payments")
async def list_payments(status_filter: Optional[str] = None, admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    stmt = select(Payment).order_by(desc(Payment.id))
    if status_filter:
        stmt = stmt.where(Payment.status == status_filter)
    res = await db.execute(stmt)
    payments = res.scalars().all()
    return [p.to_dict() for p in payments]

@api_router.post("/payments/{payment_id}/review")
async def review_payment(payment_id: int, req: PaymentReviewRequest, admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = res.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status != "pending":
        raise HTTPException(status_code=400, detail="Payment has already been processed")

    payment.reviewed_at = datetime.utcnow()
    payment.admin_note = req.admin_note

    if req.action == "approve":
        payment.status = "approved"
        # Atomically credit user's wallet
        await wallet_service.add_funds(
            session=db,
            user_id=payment.user_id,
            amount=payment.amount,
            tx_type="topup",
            description=f"Approved payment #{payment.id}"
        )
    else:
        payment.status = "rejected"

    await db.commit()
    return {"message": f"Payment #{payment.id} {payment.status}"}

# --- 9. Gift Codes ---
@api_router.get("/gift-codes")
async def list_gift_codes(admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(GiftCode).order_by(desc(GiftCode.id)))
    codes = res.scalars().all()
    return [c.to_dict() for c in codes]

@api_router.post("/gift-codes")
async def create_gift_code(req: GiftCodeCreateRequest, admin: Dict[str, Any] = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    expire_at = datetime.utcnow() + timedelta(days=req.expire_days) if req.expire_days else None
    gift = GiftCode(
        code=req.code.strip().upper(),
        amount=req.amount,
        max_redemptions=req.max_redemptions,
        redeemed_count=0,
        expire_at=expire_at,
        is_active=1
    )
    db.add(gift)
    await db.commit()
    await db.refresh(gift)
    return gift.to_dict()

# --- 10. Logs & Backups ---
@api_router.get("/system/logs")
async def fetch_logs(file_type: str = "web", admin: Dict[str, Any] = Depends(get_current_admin)):
    return {"lines": get_recent_logs(file_type=file_type, lines_count=200)}

@api_router.post("/system/backup")
async def trigger_backup(admin: Dict[str, Any] = Depends(get_current_admin)):
    backup_file = perform_db_backup()
    return {"message": "Backup created successfully", "filename": os.path.basename(backup_file)}

@api_router.get("/system/download-backup")
async def download_backup(filename: Optional[str] = None, admin: Dict[str, Any] = Depends(get_current_admin)):
    if not filename:
        # Get latest backup file
        backups = sorted(BACKUPS_DIR.glob("vpn_store_backup_*.db"), key=os.path.getmtime, reverse=True)
        if not backups:
            raise HTTPException(status_code=404, detail="No backup files found")
        target = backups[0]
    else:
        target = BACKUPS_DIR / filename
        if not target.exists():
            raise HTTPException(status_code=404, detail="Specified backup file not found")
    
    return FileResponse(
        path=str(target),
        filename=target.name,
        media_type="application/octet-stream"
    )

# --- 11. Public VPN Subscription Link Endpoint (/sub/{token}) ---
@api_router.get("/sub/{token}")
async def get_subscription(token: str, db: AsyncSession = Depends(get_db)):
    """
    Public subscription link consumed by v2rayNG, Streisand, Shadowrocket, Sing-box, Clash.
    Returns Base64-encoded list of configurations.
    """
    res = await db.execute(select(Service).where(Service.sub_token == token))
    srv = res.scalar_one_or_none()
    if not srv or not srv.is_active:
        raise HTTPException(status_code=404, detail="Subscription link expired or not found")

    content = f"{srv.config_link}\n"
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    # Standard subscription headers for clients to display remaining traffic
    headers = {
        "Profile-Update-Interval": "24",
        "Subscription-Userinfo": f"upload=0; download={srv.used_traffic_bytes}; total={srv.total_traffic_bytes}; expire={int(srv.expire_time_ms / 1000)}"
    }
    return PlainTextResponse(content=encoded, headers=headers)
