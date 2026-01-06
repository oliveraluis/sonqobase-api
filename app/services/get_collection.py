from datetime import datetime, timezone
from typing import List

from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client
from app.models.responses import DocumentResponse, ListDocumentsResponse


class GetCollectionService:
    def __init__(self, api_key_repo: ApiKeyRepository):
        self.api_key_repo = api_key_repo

    def execute(
        self,
        api_key: str,
        collection: str,
        limit: int,
        offset: int,
    ) -> ListDocumentsResponse:
        project = self.api_key_repo.get_project_by_key(api_key)

        if not project:
            raise ValueError("Invalid API Key")

        # ⛔ Proyecto expirado
        # MongoDB devuelve datetimes naive, convertir a aware para comparación
        expires_at = project["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < datetime.now(timezone.utc):
            raise RuntimeError("Project expired")

        client = get_mongo_client()
        db = client[project["database"]]

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
