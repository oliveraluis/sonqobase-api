"""
Service for verifying OTP and issuing JWT tokens.
"""
import logging
from typing import Dict

from app.infra.otp_repository import OTPRepository
from app.infra.user_repository import UserRepository
from app.utils.jwt import create_access_token, create_refresh_token
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VerifyOTPService:
    """Service to verify OTP and issue tokens"""
    
    def __init__(
        self,
        otp_repo: OTPRepository,
        user_repo: UserRepository
    ):
        self.otp_repo = otp_repo
        self.user_repo = user_repo
    
    def execute(self, user_id: str, code: str) -> Dict[str, str]:
        """
        Verify OTP and generate JWT tokens.
        
        Args:
            user_id: User ID
            code: 6-digit OTP code
        
        Returns:
            Dict with access_token, refresh_token, and token_type
        
        Raises:
            ValueError: If OTP is invalid or expired
        """
        # Verify OTP
        otp_doc = self.otp_repo.verify_otp(user_id, code)
        
        if not otp_doc:
            raise ValueError("Invalid or expired OTP code")
        
        # Mark OTP as used
        self.otp_repo.update_otp_status(otp_doc["otp_id"], "used")
        
        # Get user details for token payload
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Create Access Token
        access_token_payload = {
            "sub": str(user.id),
            "email": str(user.email) if user.email else "",
            "plan": str(user.plan_name) if user.plan_name else "free",
            "role": "user",  # Default role
            "type": "access"
        }
        logger.info(f"Generating token for payload: {access_token_payload}")
        access_token = create_access_token(data=access_token_payload)
        
        # Create Refresh Token
        refresh_token_payload = {
            "sub": str(user.id),
            "type": "refresh"
        }
        refresh_token = create_refresh_token(data=refresh_token_payload)
        
        logger.info(f"✅ JWT tokens issued for user {user_id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }
