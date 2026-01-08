from datetime import datetime, timezone
from typing import List

from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client
from app.models.responses import DocumentResponse, ListDocumentsResponse


class GetCollectionService:
    def execute(
        self,
        project: "Project",  # Forward reference or import
        collection: str,
        limit: int,
        offset: int,
    ) -> ListDocumentsResponse:
        
        # Database name from Project entity
        db_name = project.database.name
        
        client = get_mongo_client()
        db = client[db_name]

        cursor = (
            db[collection]
            .find({}, {"expires_at": 0})
            .skip(offset)
            .limit(limit)
        )

        items: List[DocumentResponse] = []

        for doc in cursor:
            items.append(
                DocumentResponse(
                    id=str(doc["_id"]),
                    data={
                        k: v
                        for k, v in doc.items()
                        if k not in {"_id"}
                    },
                )
            )

        return ListDocumentsResponse(
            items=items,
            limit=limit,
            offset=offset,
        )
