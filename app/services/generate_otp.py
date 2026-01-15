"""
Service for generating and sending OTP codes.
"""
import logging
import random
import uuid
from typing import Dict

from app.infra.otp_repository import OTPRepository
from app.infra.email_service import get_email_service
from app.infra.user_repository import UserRepository

logger = logging.getLogger(__name__)


class GenerateOTPService:
    """Service to generate OTP and send via email"""
    
    def __init__(
        self,
        otp_repo: OTPRepository,
        user_repo: UserRepository
    ):
        self.otp_repo = otp_repo
        self.user_repo = user_repo
        self.email_service = get_email_service()
    
    async def execute(self, user_id: str) -> Dict[str, any]:
        """
        Generate OTP code and send to user's email.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with success status and message
        
        Raises:
            ValueError: If user not found
        """
        # Get user
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"Usuario no encontrado: {user_id}")
        
        email = user.get("email")
        if not email:
            raise ValueError(f"El usuario {user_id} no tiene email")
        
        # Rate Limiting: Check if there is already a valid pending OTP
        existing_otp = self.otp_repo.get_latest_otp_by_user(user_id, status="pending")
        if existing_otp:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            created_at = existing_otp["created_at"].replace(tzinfo=timezone.utc)
            
            # If OTP is less than 60 seconds old, block new request
            if (now - created_at).total_seconds() < 60:
                wait_seconds = 60 - int((now - created_at).total_seconds())
                raise ValueError(f"Por favor espera {wait_seconds} segundos antes de solicitar un nuevo código.")
        
        # Invalidate any existing pending OTPs for this user
        # We still do this sync to ensure consistency before accepting new request
        self.otp_repo.invalidate_user_otps(user_id)
        
        # Generate OTP code & ID (In-Memory)
        # Check environment for DEV mode or MOCK OTP
        from app.config import settings
        
        is_dev = settings.environment == "development"
        use_mock = settings.mock_otp or is_dev
        
        if use_mock:
            otp_code = "000000"
            should_mail = False
            logger.info(f"🔧 DEV MODE: Generated MOCK OTP '000000' for user {user_id}")
        else:
            otp_code = str(random.randint(100000, 999999))
            should_mail = True
            
        otp_id = f"otp_{uuid.uuid4().hex[:12]}"
        
        # Publish OtpCreatedEvent (Async Persistence & Email)
        from app.infra.event_bus import get_event_bus
        from app.domain.events import OtpCreatedEvent
        
        user_name = user.get("name") or email.split("@")[0]
        event = OtpCreatedEvent(
            otp_id=otp_id,
            user_id=user_id,
            email=email,
            otp_code=otp_code,
            user_name=user_name,
            otp_type="login",
            should_send_email=should_mail
        )
        
        # Fire and forget (persistence + email listeners)
        await get_event_bus().publish(event)
        
        logger.info(f"🚀 OTP event published for user {user_id} (Persistence + Email)")
        
        return {
            "success": True,
            "message": "Código enviado a tu email" if should_mail else "MODO DEV: Usa el código 000000",
            "email": email,
            "otp_id": otp_id,
            "expires_in": 60  # 1 minute
        }
