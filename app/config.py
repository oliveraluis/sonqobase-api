from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str = None
    mongo_meta_db: str = "meta"
    gemini_api_key: str = None
    encryption_key: str = None  # For encrypting API keys (Fernet key)

    class Config:
        env_file = ".env"

settings = Settings()