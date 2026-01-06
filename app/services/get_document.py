from datetime import datetime, timezone
from typing import Dict, Any

from bson import ObjectId
from bson.errors import InvalidId

from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client


class GetDocumentService:
    """Servicio para obtener un documento por ID"""
    def __init__(self, api_key_repo: ApiKeyRepository):
        self.api_key_repo = api_key_repo

    def execute(
        self,
        api_key: str,
        collection: str,
        document_id: str,
    ) -> Dict[str, Any]:
        # Validar ObjectId
        try:
            obj_id = ObjectId(document_id)
        except InvalidId:
            raise ValueError(f"Invalid document ID format: '{document_id}'. Must be a 24-character hex string.")
        
        project = self.api_key_repo.get_project_by_key(api_key)

        if not project:
            raise ValueError("Invalid API Key")

        # MongoDB devuelve datetimes naive, convertir a aware
        expires_at = project["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < datetime.now(timezone.utc):
            raise RuntimeError("Project expired")

        client = get_mongo_client()
        db = client[project["database"]]
        col = db[collection]

        # Buscar documento
        doc = col.find_one({"_id": obj_id})

        if not doc:
            raise ValueError(f"Document with id '{document_id}' not found")

        # Preparar respuesta
        return {
            "id": str(doc["_id"]),
            "data": {
                k: v
                for k, v in doc.items()
                if k not in {"_id", "expires_at", "created_at", "updated_at"}
            },
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        }
