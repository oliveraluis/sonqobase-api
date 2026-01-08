"""
Email service for sending OTP codes and notifications.
Uses SMTP (Gmail) for email delivery.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.mail_host
        self.smtp_port = settings.mail_port
        self.smtp_user = settings.mail_auth
        self.smtp_password = settings.mail_password
        self.from_email = settings.mail_auth
    
    def send_otp_email(self, to_email: str, otp_code: str, user_name: Optional[str] = None) -> bool:
        """
        Send OTP code via email.
        
        Args:
            to_email: Recipient email address
            otp_code: 6-digit OTP code
            user_name: Optional user name for personalization
        
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "🔐 Tu código de verificación - SonqoBase"
        
        # HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 32px; font-weight: bold; background: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                .otp-code {{ font-size: 36px; font-weight: bold; text-align: center; letter-spacing: 8px; color: #00ff88; background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 30px 0; }}
                .message {{ color: #333; line-height: 1.6; margin-bottom: 20px; }}
                .warning {{ color: #ff4444; font-size: 14px; margin-top: 20px; padding: 15px; background-color: #fff3f3; border-left: 4px solid #ff4444; }}
                .footer {{ text-align: center; margin-top: 40px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🗄️ SonqoBase</div>
                </div>
                
                <div class="message">
                    <p>Hola{f" {user_name}" if user_name else ""},</p>
                    <p>Has solicitado acceso a tu cuenta de SonqoBase. Usa el siguiente código de verificación:</p>
                </div>
                
                <div class="otp-code">{otp_code}</div>
                
                <div class="message">
                    <p>Este código expirará en <strong>5 minutos</strong>.</p>
                    <p>Si no solicitaste este código, puedes ignorar este correo de forma segura.</p>
                </div>
                
                <div class="warning">
                    ⚠️ <strong>Nunca compartas este código</strong> con nadie. El equipo de SonqoBase nunca te pedirá tu código de verificación.
                </div>
                
                <div class="footer">
                    <p>© 2026 SonqoBase - Base de Datos Vectorial Efímera</p>
                    <p>Este es un correo automático, por favor no respondas.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_body)
    
    def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """
        Internal method to send email via SMTP.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
        
        Returns:
            True if sent successfully
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject
            
            # Attach HTML body
            html_part = MIMEText(html_body, "html", "utf-8")
            message.attach(html_part)
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get singleton instance of EmailService"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
