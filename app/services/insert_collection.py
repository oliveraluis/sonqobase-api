from datetime import datetime, timezone
from typing import Dict, Any

from pymongo import ASCENDING

from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client


class InsertCollectionService:
    def execute(
        self,
        project: "Project",
        collection: str,
        payload: Dict[str, Any],
    ) -> dict:
        db_name = project.database.name
        expires_at = project.expires_at

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
