from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    mongo_uri: str = None
    mongo_meta_db: str = "meta"
    gemini_api_key: str = None
    encryption_key: str = None  # For encrypting API keys (Fernet key)
    
    # SMTP Configuration
    mail_host: str = "smtp.gmail.com"
    mail_port: int = 587
    mail_auth: Optional[str] = None  # SMTP username (email)
    mail_password: Optional[str] = None  # SMTP password or app password
    
    # JWT Configuration
    jwt_secret_key: Optional[str] = None  # Secret key for signing JWTs
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60  # 1 hour
    refresh_token_expire_days: int = 7  # 7 days
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    
    # OTP Configuration
    otp_expire_seconds: int = 60  # 1 minute
    otp_length: int = 6

    class Config:
        env_file = ".env"

settings = Settings()

def get_settings() -> Settings:
    return settings