"""
Automatic Traffic Synchronization Service.
Periodically fetches real traffic statistics and expiration status from 3X-UI,
updates SQLite records, and disables exhausted or expired VPN clients.
"""

import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Service
from app.services.xui_client import xui_client
from app.core.config import config
from app.core.database import AsyncSessionLocal
from app.core.logging import logger

class TrafficSyncService:
    @staticmethod
    async def run_sync_cycle() -> dict:
        """Run a single traffic synchronization pass over all active services"""
        logger.info("Starting traffic synchronization cycle with 3X-UI...")
        stats = {
            "services_checked": 0,
            "services_updated": 0,
            "services_expired": 0,
            "timestamp": datetime.utcnow().isoformat()
        }

        # 1. Fetch inbounds from 3X-UI to obtain bulk clientStats if available
        inbounds_res = await xui_client.get_inbounds()
        inbounds_list = inbounds_res.get("obj", []) if inbounds_res.get("success") else []

        # Build client lookup table from inbounds: email -> {up, down, total, expiryTime, enable}
        client_stats_map = {}
        for ib in inbounds_list:
            c_stats = ib.get("clientStats") or []
            for cs in c_stats:
                em = cs.get("email")
                if em:
                    client_stats_map[em] = {
                        "up": cs.get("up", 0),
                        "down": cs.get("down", 0),
                        "total": cs.get("up", 0) + cs.get("down", 0),
                        "enable": cs.get("enable", True),
                        "expiryTime": cs.get("expiryTime", 0)
                    }

        now_ms = int(time.time() * 1000)

        async with AsyncSessionLocal() as session:
            res = await session.execute(select(Service).where(Service.is_active == 1))
            services = res.scalars().all()

            for srv in services:
                stats["services_checked"] += 1
                cdata = client_stats_map.get(srv.client_email)

                # If not found in bulk stats, try individual query
                if not cdata:
                    cdata = await xui_client.get_client_traffic(srv.client_email)
                    if cdata:
                        cdata["total"] = cdata.get("up", 0) + cdata.get("down", 0)

                if cdata:
                    used = cdata.get("total", srv.used_traffic_bytes)
                    srv.used_traffic_bytes = used
                    stats["services_updated"] += 1

                # Check quota exhaustion or expiration
                is_quota_exceeded = srv.total_traffic_bytes > 0 and srv.used_traffic_bytes >= srv.total_traffic_bytes
                is_time_expired = srv.expire_time_ms > 0 and now_ms >= srv.expire_time_ms

                if is_quota_exceeded or is_time_expired:
                    logger.info(f"Service {srv.id} ({srv.client_email}) expired or exceeded limit. Disabling in 3X-UI...")
                    await xui_client.update_client(
                        inbound_id=srv.inbound_id,
                        client_uuid=srv.client_uuid,
                        email=srv.client_email,
                        total_bytes=srv.total_traffic_bytes,
                        expire_time_ms=srv.expire_time_ms,
                        enable=False
                    )
                    srv.is_active = 0
                    stats["services_expired"] += 1

            await session.commit()

        # Update last sync timestamp in settings
        config.set("last_traffic_sync_timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info(f"Traffic synchronization completed: {stats}")
        return stats

traffic_sync_service = TrafficSyncService()
