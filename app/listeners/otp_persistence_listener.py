"""
Listener to save OTP to database.
"""
import logging
import asyncio

from app.infra.event_bus import get_event_bus
from app.domain.events import OtpCreatedEvent
from app.infra.otp_repository import OTPRepository

logger = logging.getLogger(__name__)

event_bus = get_event_bus()

@event_bus.subscribe(OtpCreatedEvent, async_handler=True)
async def on_otp_created_persistence(event: OtpCreatedEvent):
    """
    Listener to save OTP to MongoDB.
    """
    logger.info(f"💾 ENTERING OtpPersistenceListener for user {event.user_id}")
    
    try:
        otp_repo = OTPRepository()
        logger.info("💾 OTPRepository instantiated")
        
        # Invalidate old OTPs first
        otp_repo.invalidate_user_otps(event.user_id)
        
        # Create new OTP
        otp_repo.create_otp(
            otp_id=event.otp_id,
            user_id=event.user_id,
            email=event.email,
            code=event.otp_code,
            otp_type=event.otp_type
        )
        logger.info(f"💾 OTP persisted via event for user {event.user_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to persist OTP via event: {e}")
