from datetime import datetime, timezone
from typing import Dict, Any

from pymongo import ASCENDING

from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client


class InsertCollectionService:
    def __init__(self, api_key_repo: ApiKeyRepository):
        self.api_key_repo = api_key_repo

    def execute(
        self,
        api_key: str,
        collection: str,
        payload: Dict[str, Any],
    ) -> dict:
        project = self.api_key_repo.get_project_by_key(api_key)

        if not project:
            raise ValueError("Invalid API Key")

        db_name = project["database"]
        expires_at = project["expires_at"]

        document = {
            **payload,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
        }

        client = get_mongo_client()
        db = client[db_name]
        col = db[collection]
        
        # Crear índice TTL si no existe (idempotente)
        try:
            col.create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_expires_at",
            )
        except Exception:
            # Índice ya existe, continuar
            pass
        
        result = col.insert_one(document)

        return {
            "inserted_id": str(result.inserted_id),
            "expires_at": expires_at,
        }
