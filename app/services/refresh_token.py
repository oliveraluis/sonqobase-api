"""
Service to refresh JWT access tokens.
"""
import logging
from typing import Dict

from app.infra.user_repository import UserRepository
from app.utils.jwt import decode_token, create_access_token, get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RefreshTokenService:
    """Service to refresh access tokens using a refresh token"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def execute(self, refresh_token: str) -> Dict[str, str]:
        """
        Validate refresh token and issue new access token.
        
        Args:
            refresh_token: JWT verification token
        
        Returns:
            Dict with new access_token and type
        
        Raises:
            ValueError: If token is invalid, expired, or wrong type
        """
        # Decode and validate signature/expiration
        try:
            payload = decode_token(refresh_token)
        except Exception as e:
            raise ValueError(f"Invalid refresh token: {e}")
        
        # Verify token type
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type. Expected 'refresh'")
        
        # Get user ID
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise ValueError("Token missing subject (user_id)")
        
        # Get user details (to ensure user is active and get fresh data)
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
            
        if user.status != "active":
            raise ValueError(f"User account is {user.status}")
        
        # Create NEW Access Token
        access_token_payload = {
            "sub": user.id,
            "email": user.email,
            "plan": user.plan_name,
            "role": "user",
            "type": "access"
        }
        new_access_token = create_access_token(data=access_token_payload)
        
        logger.info(f"🔄 Access token refreshed for user {user_id}")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }
