"""
Listener para envío de notificaciones por email.
Escucha OtpRequestedEvent y envía el código por correo.
"""
import logging
import asyncio

from app.infra.event_bus import get_event_bus
from app.domain.events import OtpCreatedEvent
from app.infra.email_service import get_email_service

logger = logging.getLogger(__name__)

# Obtener event bus global
event_bus = get_event_bus()


@event_bus.subscribe(OtpCreatedEvent, async_handler=True)
async def on_otp_created_email(event: OtpCreatedEvent):
    """
    Listener que envía el OTP por correo.
    Ejecuta el envío SMTP en un thread separado para no bloquear.
    """
    logger.info(f"📧 Processing OTP email for user {event.user_id}")
    
    email_service = get_email_service()
    loop = asyncio.get_running_loop()
    
    # Run blocking SMTP call in thread pool
    try:
        success = await loop.run_in_executor(
            None, 
            lambda: email_service.send_otp_email(
                to_email=event.email,
                otp_code=event.otp_code,
                user_name=event.user_name
            )
        )
        
        if success:
            logger.info(f"✅ OTP email sent successfully to {event.email}")
        else:
            logger.error(f"❌ Failed to send OTP email to {event.email}")
            
    except Exception as e:
        logger.error(f"❌ Error sending OTP email (async): {e}")
