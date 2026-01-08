from datetime import datetime, timezone
from typing import Dict, Any

from pymongo import ASCENDING
from bson import ObjectId
from bson.errors import InvalidId

from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client


class UpsertDocumentService:
    """
    Servicio estilo Firebase: save() que crea o actualiza.
    """
    
    def execute(
        self,
        project: "Project",
        collection: str,
        document_id: str,
        payload: Dict[str, Any],
    ) -> dict:
        # Validar ObjectId
        try:
            obj_id = ObjectId(document_id)
        except InvalidId:
            raise ValueError(f"Invalid document ID format: '{document_id}'. Must be a 24-character hex string.")
        
        db_name = project.database.name
        expires_at = project.expires_at

        client = get_mongo_client()
        db = client[db_name]
        col = db[collection]

        # Crear índice TTL si no existe
        try:
            col.create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_expires_at",
            )
        except Exception:
            pass

        # Preparar documento
        document = {
            **payload,
            "expires_at": expires_at,
            "updated_at": datetime.now(timezone.utc),
        }

        # Upsert: actualizar si existe, crear si no existe
        result = col.update_one(
            {"_id": obj_id},
            {
                "$set": document,
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)}
            },
            upsert=True
        )

        return {
            "id": document_id,
            "upserted": result.upserted_id is not None,
            "modified": result.modified_count > 0,
            "expires_at": expires_at,
        }
