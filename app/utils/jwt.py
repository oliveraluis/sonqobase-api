"""
JWT utilities for creating and validating tokens.
"""
import jwt
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_access_token(data: Dict) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Payload data (must include sub/user_id)
    
    Returns:
        JWT access token string
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expires,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "access"
    })
    
    if not settings.jwt_secret_key:
        logger.critical("JWT_SECRET_KEY is missing in configuration/env!")
        raise ValueError("Server configuration error: JWT_SECRET_KEY is missing")

    token = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    # logger.info(f"Access token created for user {data.get('sub') or data.get('user_id')}")
    return token


def create_refresh_token(data: Dict) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data: Payload data
    
    Returns:
        JWT refresh token string
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({
        "exp": expires,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh"
    })
    
    token = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    # logger.info(f"Refresh token created for user {data.get('sub') or data.get('user_id')}")
    return token


def decode_token(token: str) -> Dict:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload
    
    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise


def get_token_expiry_seconds(token: str) -> Optional[int]:
    """
    Get remaining seconds until token expires.
    
    Args:
        token: JWT token string
    
    Returns:
        Seconds until expiry, or None if invalid
    """
    try:
        payload = decode_token(token)
        exp = payload.get("exp")
        if not exp:
            return None
        
        now = datetime.now(timezone.utc).timestamp()
        remaining = int(exp - now)
        return max(0, remaining)
    except Exception:
        return None
