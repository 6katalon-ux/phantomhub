"""
Security utilities: Password hashing, JWT token authentication, Session verification, and Rate Limiting.
"""

import time
import bcrypt
import jwt
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import config

security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash"""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(days=7))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    secret = config.get_secret("jwt_secret")
    return jwt.encode(to_encode, secret, algorithm="HS256")

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token"""
    secret = config.get_secret("jwt_secret")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except (jwt.PyJWTError, Exception):
        return None

# Simple in-memory rate limiter for failed login attempts to prevent brute force
_login_attempts: Dict[str, list] = {}

def check_login_rate_limit(ip: str, max_attempts: int = 5, window_seconds: int = 300) -> bool:
    """Returns True if within rate limit, False if rate limited"""
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    # Filter attempts within window
    attempts = [t for t in attempts if now - t < window_seconds]
    if len(attempts) >= max_attempts:
        _login_attempts[ip] = attempts
        return False
    attempts.append(now)
    _login_attempts[ip] = attempts
    return True

def reset_login_attempts(ip: str):
    if ip in _login_attempts:
        del _login_attempts[ip]

async def get_current_admin(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> Dict[str, Any]:
    """Dependency for authenticating admin via Bearer token or session cookie"""
    token = None
    if auth_header and auth_header.credentials:
        token = auth_header.credentials
    elif "admin_session" in request.cookies:
        token = request.cookies.get("admin_session")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication session",
        )
    return payload
