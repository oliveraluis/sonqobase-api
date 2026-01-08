from datetime import datetime, timezone
from typing import Dict, Any

from bson import ObjectId
from bson.errors import InvalidId

from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client


class GetDocumentService:
    """Servicio para obtener un documento por ID"""
    
    def execute(
        self,
        project: "Project",
        collection: str,
        document_id: str,
    ) -> Dict[str, Any]:
        # Validar ObjectId
        try:
            obj_id = ObjectId(document_id)
        except InvalidId:
            raise ValueError(f"Invalid document ID format: '{document_id}'. Must be a 24-character hex string.")
        
        db_name = project.database.name
        # expires checking handled in dependency...

        client = get_mongo_client()
        db = client[db_name]
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
