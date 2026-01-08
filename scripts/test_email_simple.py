"""
Script simple para probar el envío de correos SMTP.
Usa la configuración actual de .env
"""
import sys
import os
import logging

# Añadir directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.infra.email_service import EmailService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email():
    settings = get_settings()
    print(f"📧 Probando configuración SMTP:")
    print(f"Host: {settings.mail_host}")
    print(f"Port: {settings.mail_port}")
    print(f"User: {settings.mail_auth}")
    
    recipient = settings.mail_auth  # Enviar a uno mismo para probar
    
    print(f"\n🚀 Intentando enviar correo de prueba a: {recipient}...")
    
    service = EmailService()
    success = service.send_otp_email(
        to_email=recipient,
        otp_code="123456",
        user_name="Test User"
    )
    
    if success:
        print("\n✅ ¡Correo enviado exitosamente! Revisa tu bandeja de entrada (y spam).")
    else:
        print("\n❌ Falló el envío del correo. Revisa los logs de arriba para ver el error.")

if __name__ == "__main__":
    test_email()
