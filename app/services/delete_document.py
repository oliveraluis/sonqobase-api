from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client


class DeleteDocumentService:
    """Servicio para eliminar documentos por ID"""
    
    def execute(
        self,
        project: "Project",
        collection: str,
        document_id: str,
    ) -> dict:
        # Validar ObjectId
        try:
            obj_id = ObjectId(document_id)
        except InvalidId:
            raise ValueError(f"Invalid document ID format: '{document_id}'. Must be a 24-character hex string.")
        
        db_name = project.database.name
        # expires checking handled in dependency... but could check again? 
        # Dependency check is sufficient.
        
        client = get_mongo_client()
        db = client[db_name]
        col = db[collection]

        # Eliminar documento
        result = col.delete_one({"_id": obj_id})

        if result.deleted_count == 0:
            raise ValueError(f"Document with id '{document_id}' not found")

        return {
            "id": document_id,
            "deleted": True,
        }
