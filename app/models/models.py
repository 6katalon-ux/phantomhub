"""
SQLAlchemy ORM Data Models for VPN Store
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, BigInteger, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), default="superadmin")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(64), nullable=True, index=True)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    wallet_balance = Column(Integer, default=0) # In Currency units (e.g. Toman)
    trial_used = Column(Integer, default=0) # 0 = eligible, 1 = claimed
    is_blocked = Column(Integer, default=0) # 0 = normal, 1 = blocked
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    services = relationship("Service", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "wallet_balance": self.wallet_balance,
            "trial_used": bool(self.trial_used),
            "is_blocked": bool(self.is_blocked),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    category = Column(String(32), default="general")
    is_secret = Column(Integer, default=0)

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "category": self.category,
            "is_secret": bool(self.is_secret)
        }

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)
    traffic_gb = Column(Integer, nullable=False)
    duration_days = Column(Integer, nullable=False)
    inbound_id = Column(Integer, nullable=True)
    protocol = Column(String(32), default="vless")
    max_ips = Column(Integer, default=2)
    is_active = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "traffic_gb": self.traffic_gb,
            "duration_days": self.duration_days,
            "inbound_id": self.inbound_id,
            "protocol": self.protocol,
            "max_ips": self.max_ips,
            "is_active": bool(self.is_active),
            "sort_order": self.sort_order
        }

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_id = Column(BigInteger, nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    protocol = Column(String(32), default="vless")
    inbound_id = Column(Integer, nullable=False)
    client_uuid = Column(String(64), nullable=False, index=True)
    client_email = Column(String(128), unique=True, nullable=False, index=True)
    config_link = Column(Text, nullable=True)
    sub_token = Column(String(64), unique=True, nullable=True, index=True)
    total_traffic_bytes = Column(BigInteger, nullable=False)
    used_traffic_bytes = Column(BigInteger, default=0)
    expire_time_ms = Column(BigInteger, nullable=False) # Unix timestamp in milliseconds
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="services")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "telegram_id": self.telegram_id,
            "plan_id": self.plan_id,
            "protocol": self.protocol,
            "inbound_id": self.inbound_id,
            "client_uuid": self.client_uuid,
            "client_email": self.client_email,
            "config_link": self.config_link,
            "sub_token": self.sub_token,
            "total_traffic_bytes": self.total_traffic_bytes,
            "used_traffic_bytes": self.used_traffic_bytes,
            "expire_time_ms": self.expire_time_ms,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False) # Positive = credit, Negative = debit
    balance_after = Column(Integer, nullable=False)
    type = Column(String(32), nullable=False) # topup, purchase, refund, admin_adjustment
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "type": self.type,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    method = Column(String(32), default="card") # card, crypto, manual
    reference_id = Column(String(128), nullable=True)
    receipt_note = Column(Text, nullable=True)
    status = Column(String(32), default="pending") # pending, approved, rejected
    admin_note = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "method": self.method,
            "reference_id": self.reference_id,
            "receipt_note": self.receipt_note,
            "status": self.status,
            "admin_note": self.admin_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None
        }

class GiftCode(Base):
    __tablename__ = "gift_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    max_redemptions = Column(Integer, default=1)
    redeemed_count = Column(Integer, default=0)
    expire_at = Column(DateTime, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "amount": self.amount,
            "max_redemptions": self.max_redemptions,
            "redeemed_count": self.redeemed_count,
            "expire_at": self.expire_at.isoformat() if self.expire_at else None,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class GiftRedemption(Base):
    __tablename__ = "gift_redemptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gift_id = Column(Integer, ForeignKey("gift_codes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Integer, nullable=False)
    redeemed_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "gift_id": self.gift_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "redeemed_at": self.redeemed_at.isoformat() if self.redeemed_at else None
        }

class InboundCache(Base):
    __tablename__ = "inbounds_cache"

    id = Column(Integer, primary_key=True)
    inbound_id = Column(Integer, unique=True, nullable=False)
    tag = Column(String(128), nullable=True)
    protocol = Column(String(32), nullable=True)
    port = Column(Integer, nullable=True)
    network = Column(String(32), nullable=True)
    security = Column(String(32), nullable=True)
    total_clients = Column(Integer, default=0)
    raw_data = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "inbound_id": self.inbound_id,
            "tag": self.tag,
            "protocol": self.protocol,
            "port": self.port,
            "network": self.network,
            "security": self.security,
            "total_clients": self.total_clients,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, nullable=True)
    action = Column(String(64), nullable=False)
    target = Column(String(128), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "action": self.action,
            "target": self.target,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    target_type = Column(String(32), default="all") # all, user
    target_id = Column(BigInteger, nullable=True)
    is_sent = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "is_sent": bool(self.is_sent),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
