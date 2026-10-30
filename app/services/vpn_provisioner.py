"""
VPN Service Provisioner.
Coordinates 3X-UI client creation, link generation, wallet balance deductions,
and automatic rollbacks / refunds if provisioning fails.
"""

import time
import uuid
import secrets
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import User, Plan, Service
from app.services.xui_client import xui_client
from app.services.wallet import wallet_service
from app.core.config import config
from app.core.logging import logger

class VPNProvisioner:
    @staticmethod
    async def purchase_plan(
        session: AsyncSession,
        user_id: int,
        telegram_id: int,
        plan_id: int
    ) -> Tuple[bool, Optional[Service], str]:
        """
        Deducts balance atomically, creates client in 3X-UI, and creates Service record.
        If 3X-UI fails, automatically refunds user balance!
        """
        # 1. Fetch Plan
        res = await session.execute(select(Plan).where(Plan.id == plan_id, Plan.is_active == 1))
        plan = res.scalar_one_or_none()
        if not plan:
            return False, None, "Plan not found or currently unavailable"

        # 2. Check & Deduct Wallet Funds
        plan_desc = f"Purchase {plan.name} ({plan.traffic_gb}GB, {plan.duration_days} days)"
        ok_deduct, _, deduct_msg = await wallet_service.deduct_funds(
            session=session,
            user_id=user_id,
            amount=plan.price,
            description=plan_desc
        )
        if not ok_deduct:
            return False, None, deduct_msg

        # 3. Determine Inbound ID
        inbound_id = plan.inbound_id
        if not inbound_id or inbound_id <= 0:
            inbound_id = config.get_int("xui_default_inbound", 1)

        # 4. Fetch Inbound Details from 3X-UI
        inbound = await xui_client.get_inbound(inbound_id)
        if not inbound:
            # Automatic Refund
            await wallet_service.refund_funds(
                session=session,
                user_id=user_id,
                amount=plan.price,
                reason="Refund: Inbound not found in 3X-UI"
            )
            await session.commit()
            return False, None, f"Selected VPN server inbound (ID {inbound_id}) is not reachable on 3X-UI"

        # 5. Generate Client UUID and Unique Email
        client_uuid = str(uuid.uuid4())
        client_suffix = secrets.token_hex(3)
        client_email = f"u{telegram_id}_{client_suffix}"
        
        # Calculate expiration timestamp (in milliseconds)
        expire_time_ms = int((time.time() + (plan.duration_days * 86400)) * 1000)
        total_traffic_bytes = plan.traffic_gb * 1024 * 1024 * 1024

        # 6. Add Client to 3X-UI
        protocol = inbound.get("protocol", "vless").lower()
        success_xui, xui_msg = await xui_client.add_client(
            inbound_id=inbound_id,
            client_uuid=client_uuid,
            email=client_email,
            total_gb=plan.traffic_gb,
            expire_time_ms=expire_time_ms,
            max_ips=plan.max_ips or 2
        )

        if not success_xui:
            # CRITICAL: Automatic rollback and refund!
            logger.error(f"3X-UI client creation failed for user {telegram_id}: {xui_msg}. Refunding...")
            await wallet_service.refund_funds(
                session=session,
                user_id=user_id,
                amount=plan.price,
                reason=f"Refund: 3X-UI provisioning failed ({xui_msg})"
            )
            await session.commit()
            return False, None, f"VPN Server provisioning error: {xui_msg}. Your balance has been automatically refunded."

        # 7. Generate Real Configuration Link
        site_name = config.get("site_name", "VPNStore")
        remark = f"{site_name}-{telegram_id}-{plan.name}"
        config_link = xui_client.generate_config_link(inbound, client_uuid, remark)
        sub_token = secrets.token_urlsafe(24)

        # 8. Record Service in Database
        service = Service(
            user_id=user_id,
            telegram_id=telegram_id,
            plan_id=plan.id,
            protocol=protocol,
            inbound_id=inbound_id,
            client_uuid=client_uuid,
            client_email=client_email,
            config_link=config_link,
            sub_token=sub_token,
            total_traffic_bytes=total_traffic_bytes,
            used_traffic_bytes=0,
            expire_time_ms=expire_time_ms,
            is_active=1
        )
        session.add(service)
        await session.commit()
        await session.refresh(service)

        logger.info(f"Successfully provisioned service {service.id} for user {telegram_id}")
        return True, service, "Service provisioned successfully"

    @staticmethod
    async def claim_free_trial(
        session: AsyncSession,
        user_id: int,
        telegram_id: int
    ) -> Tuple[bool, Optional[Service], str]:
        """Provision a free test subscription if eligible"""
        if not config.get_bool("trial_enabled", True):
            return False, None, "Free trial is currently disabled"

        # Check user eligibility
        res = await session.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()
        if not user or user.trial_used:
            return False, None, "You have already claimed your one-time free trial"

        traffic_gb = config.get_int("trial_traffic_gb", 1)
        duration_days = config.get_int("trial_duration_days", 3)
        inbound_id = config.get_int("trial_inbound_id", 1)

        inbound = await xui_client.get_inbound(inbound_id)
        if not inbound:
            return False, None, "Trial inbound server is not accessible in 3X-UI"

        client_uuid = str(uuid.uuid4())
        client_email = f"trial_{telegram_id}_{secrets.token_hex(2)}"
        expire_time_ms = int((time.time() + (duration_days * 86400)) * 1000)
        total_bytes = traffic_gb * 1024 * 1024 * 1024

        ok, msg = await xui_client.add_client(
            inbound_id=inbound_id,
            client_uuid=client_uuid,
            email=client_email,
            total_gb=traffic_gb,
            expire_time_ms=expire_time_ms,
            max_ips=1
        )
        if not ok:
            return False, None, f"Failed to provision trial client: {msg}"

        site_name = config.get("site_name", "VPNStore")
        config_link = xui_client.generate_config_link(inbound, client_uuid, f"{site_name}-Trial-{telegram_id}")
        sub_token = secrets.token_urlsafe(24)

        service = Service(
            user_id=user_id,
            telegram_id=telegram_id,
            plan_id=None,
            protocol=inbound.get("protocol", "vless").lower(),
            inbound_id=inbound_id,
            client_uuid=client_uuid,
            client_email=client_email,
            config_link=config_link,
            sub_token=sub_token,
            total_traffic_bytes=total_bytes,
            used_traffic_bytes=0,
            expire_time_ms=expire_time_ms,
            is_active=1
        )
        session.add(service)
        user.trial_used = 1
        await session.commit()
        await session.refresh(service)
        return True, service, "Free trial claimed successfully"

    @staticmethod
    async def toggle_service(
        session: AsyncSession,
        service_id: int,
        enable: bool
    ) -> Tuple[bool, str]:
        """Enable or disable service in DB and 3X-UI"""
        res = await session.execute(select(Service).where(Service.id == service_id))
        srv = res.scalar_one_or_none()
        if not srv:
            return False, "Service not found"

        # Update in 3X-UI
        ok, msg = await xui_client.update_client(
            inbound_id=srv.inbound_id,
            client_uuid=srv.client_uuid,
            email=srv.client_email,
            total_bytes=srv.total_traffic_bytes,
            expire_time_ms=srv.expire_time_ms,
            enable=enable
        )
        if not ok:
            logger.warning(f"Could not update client status in 3X-UI: {msg}")

        srv.is_active = 1 if enable else 0
        await session.commit()
        return True, f"Service {'enabled' if enable else 'disabled'} successfully"

    @staticmethod
    async def delete_service(
        session: AsyncSession,
        service_id: int
    ) -> Tuple[bool, str]:
        """Delete service from DB and 3X-UI"""
        res = await session.execute(select(Service).where(Service.id == service_id))
        srv = res.scalar_one_or_none()
        if not srv:
            return False, "Service not found"

        # Remove from 3X-UI
        await xui_client.delete_client(inbound_id=srv.inbound_id, client_uuid=srv.client_uuid)

        await session.delete(srv)
        await session.commit()
        return True, "Service deleted"

vpn_provisioner = VPNProvisioner()
