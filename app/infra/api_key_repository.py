from typing import Optional
import hashlib
import logging

from app.infra.mongo_client import get_mongo_client
from app.config import settings

logger = logging.getLogger(__name__)


def _hash_api_key(api_key: str) -> str:
    """Hash API key usando SHA-256 para comparación segura"""
    return hashlib.sha256(api_key.encode()).hexdigest()


class ApiKeyRepository:
    def get_project_by_key(self, api_key: str) -> Optional[dict]:
        client = get_mongo_client()
        db = client[settings.mongo_meta_db]
        collection = db["projects"]

        try:
            # Buscar por hash de API key, no por texto plano
            api_key_hash = _hash_api_key(api_key)
            project = collection.find_one(
                {"api_key_hash": api_key_hash},
                {"_id": 0}
            )
            if project:
                logger.info(f"Project found for API key hash")
            else:
                logger.warning(f"No project found for provided API key")
            return project
        except Exception as e:
            logger.error(f"Error fetching project by API key: {e}")
            return None

