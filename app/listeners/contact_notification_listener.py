"""
Listener para notificaciones de formulario de contacto.
Envía email al admin cuando alguien envía el formulario.
"""
import logging
from app.domain.events import ContactFormSubmittedEvent
from app.infra.event_bus import get_event_bus
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


async def on_contact_form_submitted(event: ContactFormSubmittedEvent):
    """Envía notificación por email cuando se envía el formulario de contacto"""
    try:
        logger.info(f"📧 Enviando notificación de contacto: {event.name} ({event.email})")
        
        email_service = EmailService()
        
        # Email al admin
        subject = f"🚀 Nuevo registro de interés en SonqoBase - {event.plan}"
        
        body = f"""
¡Hola!

Alguien está interesado en usar SonqoBase:

📋 Detalles del Contacto:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Nombre: {event.name}
• Email: {event.email}
• Teléfono: {event.phone or 'No proporcionado'}
• País: {event.country or 'No especificado'}
• Empresa: {event.company or 'No especificada'}
• Plan de interés: {event.plan.upper()}

💡 Qué quiere construir:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{event.interest}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enviado desde SonqoBase Landing Page
Fecha: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        await email_service.send_email(
            to_email="loliverv11@gmail.com",
            subject=subject,
            body=body
        )
        
        logger.info(f"✅ Notificación enviada exitosamente para {event.email}")
        
    except Exception as e:
        logger.error(f"❌ Error enviando notificación de contacto: {e}", exc_info=True)


# Registrar listener
event_bus = get_event_bus()
event_bus.subscribe(ContactFormSubmittedEvent, on_contact_form_submitted)
logger.info("✅ Registered async listener for ContactFormSubmittedEvent")
