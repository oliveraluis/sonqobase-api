"""
Utilidades de encriptación para API keys.
Usa Fernet (AES-128 en modo CBC) para encriptación simétrica.
"""
from cryptography.fernet import Fernet
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def get_fernet() -> Fernet:
    """Obtener instancia de Fernet con la clave de encriptación"""
    if not settings.encryption_key:
        raise ValueError("ENCRYPTION_KEY not set in environment variables")
    
    # La clave debe ser un string base64 de 32 bytes
    return Fernet(settings.encryption_key.encode())


def encrypt_api_key(api_key: str) -> str:
    """
    Encriptar una API key para almacenamiento seguro.
    
    Args:
        api_key: La API key en texto plano
    
    Returns:
        API key encriptada (base64 string)
    """
    try:
        fernet = get_fernet()
        encrypted = fernet.encrypt(api_key.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Error encrypting API key: {e}")
        raise


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Desencriptar una API key almacenada.
    
    Args:
        encrypted_key: La API key encriptada (base64 string)
    
    Returns:
        API key en texto plano
    """
    try:
        fernet = get_fernet()
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting API key: {e}")
        raise


def generate_encryption_key() -> str:
    """
    Generar una nueva clave de encriptación Fernet.
    Esta función es solo para setup inicial.
    
    Returns:
        Clave de encriptación en formato base64
    """
    key = Fernet.generate_key()
    return key.decode()
